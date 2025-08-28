#!/usr/bin/env python3
"""
Environment Configuration Validator for CompliantGuard
Validates deployment readiness across environments
"""

import json
import os
import sys
from typing import Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
import requests
from urllib.parse import urlparse


class EnvironmentValidator:
    def __init__(self, environment: str = "local"):
        self.environment = environment
        self.validation_results = []
        self.critical_failures = []
        self.warnings = []

    def log_result(self, category: str, test: str, status: str, message: str, critical: bool = False):
        """Log a validation result"""
        result = {
            "category": category,
            "test": test,
            "status": status,
            "message": message,
            "critical": critical
        }
        self.validation_results.append(result)
        
        if status == "FAIL":
            if critical:
                self.critical_failures.append(result)
            else:
                self.warnings.append(result)

    def validate_aws_credentials(self) -> bool:
        """Validate AWS credentials and permissions"""
        try:
            # Test basic AWS connectivity
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            
            self.log_result("AWS", "Credentials", "PASS", 
                          f"AWS credentials valid. Account: {identity.get('Account')}")
            
            # Test DynamoDB access
            dynamodb = boto3.client('dynamodb')
            tables = dynamodb.list_tables()
            
            self.log_result("AWS", "DynamoDB Access", "PASS", 
                          f"DynamoDB accessible. {len(tables['TableNames'])} tables found")
            
            # Test S3 access
            s3 = boto3.client('s3')
            buckets = s3.list_buckets()
            
            self.log_result("AWS", "S3 Access", "PASS",
                          f"S3 accessible. {len(buckets['Buckets'])} buckets found")
            
            return True
            
        except Exception as e:
            self.log_result("AWS", "Credentials", "FAIL", 
                          f"AWS credentials invalid or insufficient permissions: {str(e)}", 
                          critical=True)
            return False

    def validate_environment_variables(self) -> bool:
        """Validate required environment variables are set"""
        required_vars = {
            "local": [
                "AWS_REGION",
                "JWT_SECRET_KEY"
            ],
            "staging": [
                "AWS_REGION", 
                "JWT_SECRET_KEY",
                "ENVIRONMENT",
                "S3_BUCKET_NAME",
                "DYNAMODB_TABLE_NAME"
            ],
            "production": [
                "AWS_REGION",
                "JWT_SECRET_KEY", 
                "ENVIRONMENT",
                "S3_BUCKET_NAME",
                "DYNAMODB_TABLE_NAME",
                "DOMAIN_NAME",
                "SSL_CERTIFICATE_ARN"
            ]
        }
        
        env_vars = required_vars.get(self.environment, [])
        all_present = True
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Don't log sensitive values
                display_value = "***" if "secret" in var.lower() or "key" in var.lower() else value
                self.log_result("Environment", f"Variable {var}", "PASS",
                              f"{var} is set: {display_value}")
            else:
                self.log_result("Environment", f"Variable {var}", "FAIL",
                              f"Required environment variable {var} is not set",
                              critical=True)
                all_present = False
        
        return all_present

    def validate_database_connectivity(self) -> bool:
        """Validate database/DynamoDB connectivity and table existence"""
        try:
            dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            
            # Core tables that should exist
            required_tables = [
                'themisguard-users',
                'themisguard-scans', 
                'themisguard-compliance-data'
            ]
            
            if self.environment in ['staging', 'production']:
                required_tables.extend([
                    'themisguard-audit-logs',
                    'themisguard-billing-data'
                ])
            
            all_tables_exist = True
            for table_name in required_tables:
                try:
                    table = dynamodb.Table(table_name)
                    table.load()
                    self.log_result("Database", f"Table {table_name}", "PASS",
                                  f"Table exists and is accessible")
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ResourceNotFoundException':
                        self.log_result("Database", f"Table {table_name}", "FAIL",
                                      f"Required table does not exist: {table_name}",
                                      critical=True)
                        all_tables_exist = False
                    else:
                        raise
            
            return all_tables_exist
            
        except Exception as e:
            self.log_result("Database", "Connectivity", "FAIL",
                          f"Database connectivity failed: {str(e)}",
                          critical=True)
            return False

    def validate_security_configuration(self) -> bool:
        """Validate security configuration"""
        security_valid = True
        
        # Check JWT secret strength
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if jwt_secret:
            if len(jwt_secret) < 32:
                self.log_result("Security", "JWT Secret Length", "FAIL",
                              "JWT secret key is too short (minimum 32 characters)",
                              critical=True)
                security_valid = False
            elif jwt_secret.lower() in ['secret', 'password', 'changeme']:
                self.log_result("Security", "JWT Secret Strength", "FAIL",
                              "JWT secret key is too weak/predictable",
                              critical=True)
                security_valid = False
            else:
                self.log_result("Security", "JWT Secret", "PASS",
                              "JWT secret key meets minimum requirements")
        
        # Check for hardcoded credentials in code (basic check)
        dangerous_patterns = [
            "password.*=.*['\"].*['\"]",
            "SecureAdmin123",
            "admin@themisguard.com.*password",
            "123456"  # 2FA code
        ]
        
        # This is a basic check - in production, use proper SAST tools
        self.log_result("Security", "Hardcoded Credentials", "WARNING",
                      "Manual code review required for hardcoded credentials")
        
        # Environment-specific security checks
        if self.environment == "production":
            # Production should have stricter security
            if not os.getenv('SSL_CERTIFICATE_ARN'):
                self.log_result("Security", "SSL Certificate", "FAIL",
                              "SSL certificate ARN not configured for production",
                              critical=True)
                security_valid = False
        
        return security_valid

    def validate_api_endpoints(self) -> bool:
        """Validate API endpoints are responding correctly"""
        # Map environments to API URLs
        api_urls = {
            "local": "http://localhost:8000",
            "staging": "https://82orcbhmf6.execute-api.us-east-1.amazonaws.com/Prod", 
            "production": "https://5fiz077nk8.execute-api.us-east-1.amazonaws.com/Prod"
        }
        
        base_url = api_urls.get(self.environment)
        if not base_url:
            self.log_result("API", "Configuration", "FAIL",
                          f"No API URL configured for environment: {self.environment}",
                          critical=True)
            return False
        
        endpoints_to_test = [
            ("/health", "Health Check"),
            ("/deployment-info", "Deployment Info")
        ]
        
        all_endpoints_healthy = True
        
        for endpoint, name in endpoints_to_test:
            try:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    self.log_result("API", f"Endpoint {endpoint}", "PASS",
                                  f"{name} endpoint responding correctly")
                else:
                    self.log_result("API", f"Endpoint {endpoint}", "FAIL",
                                  f"{name} endpoint returned {response.status_code}",
                                  critical=True)
                    all_endpoints_healthy = False
                    
            except Exception as e:
                self.log_result("API", f"Endpoint {endpoint}", "FAIL",
                              f"{name} endpoint unreachable: {str(e)}",
                              critical=True)
                all_endpoints_healthy = False
        
        return all_endpoints_healthy

    def validate_deployment_sync(self) -> bool:
        """Validate frontend and backend deployment sync"""
        try:
            # Check if deployment-info.json exists
            frontend_info_path = "frontend/public/deployment-info.json"
            backend_info_path = "backend/deployment-info.json"
            
            frontend_info = None
            backend_info = None
            
            if os.path.exists(frontend_info_path):
                with open(frontend_info_path) as f:
                    frontend_info = json.load(f)
                self.log_result("Deployment", "Frontend Info", "PASS",
                              f"Frontend deployment info available")
            else:
                self.log_result("Deployment", "Frontend Info", "WARNING",
                              "Frontend deployment info not generated")
            
            if os.path.exists(backend_info_path):
                with open(backend_info_path) as f:
                    backend_info = json.load(f)
                self.log_result("Deployment", "Backend Info", "PASS", 
                              f"Backend deployment info available")
            else:
                self.log_result("Deployment", "Backend Info", "WARNING",
                              "Backend deployment info not generated")
            
            # Check git hash sync
            if frontend_info and backend_info:
                fe_hash = frontend_info.get('git', {}).get('shortHash')
                be_hash = backend_info.get('git', {}).get('shortHash')
                
                if fe_hash == be_hash:
                    self.log_result("Deployment", "Version Sync", "PASS",
                                  f"Frontend and backend are in sync: {fe_hash}")
                else:
                    self.log_result("Deployment", "Version Sync", "WARNING",
                                  f"Version mismatch - FE: {fe_hash}, BE: {be_hash}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_result("Deployment", "Sync Check", "FAIL",
                          f"Failed to validate deployment sync: {str(e)}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations and return results"""
        print(f"🔍 Starting environment validation for: {self.environment}")
        print("=" * 60)
        
        validations = [
            ("AWS Credentials & Permissions", self.validate_aws_credentials),
            ("Environment Variables", self.validate_environment_variables),
            ("Database Connectivity", self.validate_database_connectivity),
            ("Security Configuration", self.validate_security_configuration),
            ("API Endpoints", self.validate_api_endpoints),
            ("Deployment Sync", self.validate_deployment_sync)
        ]
        
        overall_success = True
        
        for name, validator_func in validations:
            print(f"\n📋 {name}")
            print("-" * 40)
            try:
                result = validator_func()
                if not result:
                    overall_success = False
            except Exception as e:
                self.log_result("System", name, "FAIL",
                              f"Validation failed with exception: {str(e)}",
                              critical=True)
                overall_success = False
        
        # Print results
        print(f"\n🎯 VALIDATION SUMMARY")
        print("=" * 60)
        
        if self.critical_failures:
            print(f"🔴 CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"   ❌ {failure['category']}: {failure['test']} - {failure['message']}")
        
        if self.warnings:
            print(f"🟡 WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   ⚠️  {warning['category']}: {warning['test']} - {warning['message']}")
        
        passed_tests = len([r for r in self.validation_results if r['status'] == 'PASS'])
        total_tests = len(self.validation_results)
        
        print(f"\n📊 RESULTS: {passed_tests}/{total_tests} tests passed")
        
        if overall_success:
            print(f"✅ Environment {self.environment} is ready for deployment!")
        else:
            print(f"❌ Environment {self.environment} has issues that must be resolved")
            if self.critical_failures:
                print("🚨 CRITICAL issues must be fixed before deployment!")
        
        return overall_success, {
            "environment": self.environment,
            "overall_success": overall_success,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "critical_failures": len(self.critical_failures),
            "warnings": len(self.warnings),
            "results": self.validation_results
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate-environment.py <environment> [--json]")
        print("Environments: local, staging, production")
        sys.exit(1)
    
    environment = sys.argv[1]
    output_json = "--json" in sys.argv
    
    validator = EnvironmentValidator(environment)
    success, results = validator.run_all_validations()
    
    if output_json:
        print("\n" + json.dumps(results, indent=2))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()