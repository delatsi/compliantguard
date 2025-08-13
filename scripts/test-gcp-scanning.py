#!/usr/bin/env python3
"""
Test GCP Scanning with Real Credentials on AWS Deployment
"""
import json
import os
import sys
from pathlib import Path

import requests


def load_test_credentials():
    """Load test user credentials"""
    environment = input("Enter environment [dev]: ").strip() or "dev"
    creds_file = f"test-user-{environment}.json"
    
    if not os.path.exists(creds_file):
        print(f"❌ Credentials file {creds_file} not found")
        print("Run: python3 scripts/create-test-user.py")
        return None
    
    with open(creds_file, 'r') as f:
        return json.load(f)

def login_and_get_token(creds):
    """Login and get authentication token"""
    print("🔐 Logging in...")
    
    login_data = {
        "email": creds["email"],
        "password": creds["password"]
    }
    
    try:
        response = requests.post(f"{creds['api_url']}/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            return data["access_token"]
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def upload_gcp_credentials(api_url, token, gcp_creds_file):
    """Upload GCP service account credentials"""
    print("📤 Uploading GCP credentials...")
    
    if not os.path.exists(gcp_creds_file):
        print(f"❌ GCP credentials file not found: {gcp_creds_file}")
        return None
    
    try:
        with open(gcp_creds_file, 'r') as f:
            service_account = json.load(f)
        
        # Extract project ID
        project_id = service_account.get('project_id')
        if not project_id:
            print("❌ No project_id found in service account file")
            return None
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload via JSON endpoint
        upload_data = {
            "project_id": project_id,
            "service_account_json": service_account
        }
        
        response = requests.post(
            f"{api_url}/api/v1/gcp/credentials",
            json=upload_data,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ GCP credentials uploaded successfully!")
            print(f"   Project: {data['project_id']}")
            print(f"   Service Account: {data['service_account_email']}")
            return project_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def list_gcp_projects(api_url, token):
    """List configured GCP projects"""
    print("📋 Listing GCP projects...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{api_url}/api/v1/gcp/projects", headers=headers)
        
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Found {len(projects)} GCP projects:")
            
            for project in projects:
                print(f"   - {project['project_id']}: {project['service_account_email']}")
                print(f"     Status: {project['status']}, Created: {project['created_at']}")
            
            return projects
        else:
            print(f"❌ Failed to list projects: {response.status_code}")
            print(f"   Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ List projects error: {e}")
        return []

def trigger_compliance_scan(api_url, token, project_id):
    """Trigger a compliance scan for a GCP project"""
    print(f"🔍 Triggering compliance scan for {project_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Note: The scan endpoint expects project_id as a form parameter or JSON body
        scan_data = {"project_id": project_id}
        
        response = requests.post(
            f"{api_url}/api/v1/scan",
            json=scan_data,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Compliance scan completed!")
            print(f"   Scan ID: {data['scan_id']}")
            print(f"   Violations found: {data['violations_count']}")
            print(f"   Status: {data['status']}")
            return data['scan_id']
        else:
            print(f"❌ Scan failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Scan error: {e}")
        return None

def get_scan_report(api_url, token, scan_id):
    """Get the compliance scan report"""
    print(f"📊 Retrieving scan report {scan_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{api_url}/api/v1/reports/{scan_id}", headers=headers)
        
        if response.status_code == 200:
            report = response.json()
            print("✅ Scan report retrieved!")
            
            # Display summary
            if 'violations' in report:
                violations = report['violations']
                print(f"\n📋 Compliance Report Summary:")
                print(f"   Total violations: {len(violations)}")
                
                # Group by severity
                severity_counts = {}
                for violation in violations:
                    severity = violation.get('severity', 'unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                for severity, count in severity_counts.items():
                    print(f"   {severity.title()}: {count}")
                
                # Show first few violations
                print(f"\n🚨 Sample Violations:")
                for i, violation in enumerate(violations[:3]):
                    print(f"   {i+1}. {violation.get('type', 'Unknown')}")
                    print(f"      Resource: {violation.get('resource', 'N/A')}")
                    print(f"      Severity: {violation.get('severity', 'N/A')}")
                    print(f"      Description: {violation.get('description', 'N/A')}")
                
                if len(violations) > 3:
                    print(f"   ... and {len(violations) - 3} more violations")
            
            return report
        else:
            print(f"❌ Failed to get report: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Report error: {e}")
        return None

def main():
    """Main testing function"""
    print("🔍 GCP Scanning Test with Real AWS Deployment")
    print("=" * 50)
    print("")
    
    # Step 1: Load test credentials
    creds = load_test_credentials()
    if not creds:
        return
    
    print(f"📋 Testing environment: {creds['environment']}")
    print(f"🌐 API URL: {creds['api_url']}")
    print(f"👤 User: {creds['email']}")
    
    # Step 2: Login
    token = login_and_get_token(creds)
    if not token:
        return
    
    # Step 3: Check existing projects
    existing_projects = list_gcp_projects(creds['api_url'], token)
    
    # Step 4: Upload GCP credentials (if needed)
    project_id = None
    
    if not existing_projects:
        print("\n📁 No GCP projects found. Let's upload service account credentials.")
        gcp_creds_path = input("Enter path to GCP service account JSON file: ").strip()
        
        if not gcp_creds_path:
            print("❌ No credentials file specified")
            return
        
        project_id = upload_gcp_credentials(creds['api_url'], token, gcp_creds_path)
        if not project_id:
            return
    else:
        # Use existing project
        project_id = existing_projects[0]['project_id']
        print(f"\n✅ Using existing project: {project_id}")
    
    # Step 5: Trigger compliance scan
    print(f"\n🔍 Starting compliance scan...")
    scan_id = trigger_compliance_scan(creds['api_url'], token, project_id)
    if not scan_id:
        return
    
    # Step 6: Get scan report
    print(f"\n📊 Retrieving scan results...")
    report = get_scan_report(creds['api_url'], token, scan_id)
    
    if report:
        # Save report to file
        report_file = f"compliance-report-{project_id}-{scan_id[:8]}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Full report saved to: {report_file}")
        
        print(f"\n🎉 GCP scanning test completed successfully!")
        print(f"📋 Summary:")
        print(f"   Project: {project_id}")
        print(f"   Scan ID: {scan_id}")
        print(f"   Report: {report_file}")
        
        # Show next steps
        print(f"\n🚀 Next steps:")
        print(f"1. Review the compliance report: {report_file}")
        print(f"2. Address any violations found")
        print(f"3. Run additional scans as needed")
        print(f"4. Check the web dashboard for visual reports")
    
    print(f"\n✅ Testing complete!")

if __name__ == "__main__":
    main()