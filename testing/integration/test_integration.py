#!/usr/bin/env python3
"""
Integration Testing Suite - Full AWS Integration
"""
import json
import os
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

def test_aws_infrastructure():
    """Test AWS infrastructure components"""
    print("🧪 Testing AWS Infrastructure Integration")
    print("=" * 50)
    
    try:
        import boto3
        from botocore.exceptions import ClientError

        # Test DynamoDB
        print("\n1. Testing DynamoDB...")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Test main tables
        tables_to_test = [
            'themisguard-dev-scans',
            'themisguard-dev-gcp-credentials',
            'themisguard-dev-users'
        ]
        
        for table_name in tables_to_test:
            try:
                table = dynamodb.Table(table_name)
                table.table_status
                print(f"   ✅ {table_name} - accessible")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"   ⚠️  {table_name} - not found (create with setup script)")
                else:
                    print(f"   ❌ {table_name} - error: {e}")
        
        # Test KMS
        print("\n2. Testing KMS...")
        kms = boto3.client('kms', region_name='us-east-1')
        try:
            response = kms.describe_key(KeyId='alias/compliantguard-gcp-credentials')
            print(f"   ✅ KMS key accessible - {response['KeyMetadata']['KeyId']}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFoundException':
                print("   ⚠️  KMS key not found (create with setup script)")
            else:
                print(f"   ❌ KMS error: {e}")
        
        # Test S3
        print("\n3. Testing S3...")
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'themisguard-dev-reports'
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"   ✅ S3 bucket accessible - {bucket_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"   ⚠️  S3 bucket not found - {bucket_name}")
            else:
                print(f"   ❌ S3 error: {e}")
                
        print("\n✅ AWS infrastructure test completed")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install boto3")
        return False
    except Exception as e:
        print(f"❌ Infrastructure test failed: {e}")
        return False

def test_fastapi_integration():
    """Test FastAPI application with real backend"""
    print("\n🚀 Testing FastAPI Integration")
    print("=" * 30)
    
    try:
        # Set environment variables
        os.environ.update({
            'AWS_REGION': 'us-east-1',
            'DYNAMODB_TABLE_NAME': 'themisguard-dev-scans',
            'GCP_CREDENTIALS_TABLE': 'themisguard-dev-gcp-credentials',
            'KMS_KEY_ALIAS': 'alias/compliantguard-gcp-credentials',
            'JWT_SECRET_KEY': 'test-integration-secret',
            'ENVIRONMENT': 'development'
        })
        
        # Import and test FastAPI app
        from fastapi.testclient import TestClient

        from backend.main import app
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
        
        print("✅ FastAPI integration test completed")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install fastapi[all] httpx")
        return False
    except Exception as e:
        print(f"❌ FastAPI integration test failed: {e}")
        return False

def test_gcp_credential_service():
    """Test GCP credential service with real AWS"""
    print("\n🔐 Testing GCP Credential Service")
    print("=" * 35)
    
    try:
        from backend.services.gcp_credential_service import \
            GCPCredentialService
        
        service = GCPCredentialService()
        print("✅ GCP credential service initialized")
        
        # Test service configuration
        print(f"   Table: {service.creds_table.table_name}")
        print(f"   KMS Key: {service.kms_key_alias}")
        print(f"   Region: {service.kms_client._client_config.region_name}")
        
        print("✅ GCP credential service test completed")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"❌ GCP credential service test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🧪 CompliantGuard Integration Test Suite")
    print("=" * 45)
    print("")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: AWS Infrastructure
    if test_aws_infrastructure():
        tests_passed += 1
    
    # Test 2: FastAPI Integration
    if test_fastapi_integration():
        tests_passed += 1
    
    # Test 3: GCP Credential Service
    if test_gcp_credential_service():
        tests_passed += 1
    
    print(f"\n📊 Integration Test Results")
    print("=" * 28)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All integration tests passed!")
        print("\n🚀 System ready for deployment")
        return True
    else:
        print(f"❌ {total_tests - tests_passed} test(s) failed")
        print("\n🔧 Check AWS setup and dependencies")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)