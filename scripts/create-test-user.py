#!/usr/bin/env python3
"""
Create Test User for AWS Deployment Testing
"""
import hashlib
import json
import os
import uuid
from datetime import datetime

import boto3


def hash_password(password):
    """Simple password hashing using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_test_user():
    """Create a test user in the deployed DynamoDB table"""
    print("🔧 Creating Test User for AWS Deployment")
    print("=" * 45)
    
    # Get environment info
    environment = input("Enter environment (dev/staging/prod) [dev]: ").strip() or "dev"
    table_name = f"themisguard-{environment}-users"
    
    print(f"📋 Using table: {table_name}")
    
    # Get user details
    email = input("Enter email address [test@compliantguard.com]: ").strip() or "test@compliantguard.com"
    password = input("Enter password [testpass123]: ").strip() or "testpass123"
    first_name = input("Enter first name [Test]: ").strip() or "Test"
    last_name = input("Enter last name [User]: ").strip() or "User"
    company = input("Enter company [CompliantGuard]: ").strip() or "CompliantGuard"
    
    try:
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table(table_name)
        
        # Check if user already exists
        print(f"\n🔍 Checking if user {email} exists...")
        response = table.scan(
            FilterExpression="email = :email",
            ExpressionAttributeValues={":email": email}
        )
        
        if response.get('Items'):
            print("⚠️  User already exists!")
            overwrite = input("Overwrite existing user? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("❌ Cancelled")
                return False
            
            # Delete existing user
            existing_user = response['Items'][0]
            table.delete_item(Key={'user_id': existing_user['user_id']})
            print("🗑️ Deleted existing user")
        
        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        
        user_item = {
            "user_id": user_id,
            "email": email,
            "password_hash": password_hash,
            "profile": {
                "first_name": first_name,
                "last_name": last_name,
                "name": f"{first_name} {last_name}",
                "company": company
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "email_verified": True,
            "plan_tier": "free",
            "status": "active",
            "test_user": True  # Mark as test user
        }
        
        # Store in DynamoDB
        table.put_item(Item=user_item)
        
        print("✅ Test user created successfully!")
        print(f"   User ID: {user_id}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   Name: {first_name} {last_name}")
        print(f"   Company: {company}")
        
        # Create credentials file for easy testing
        creds_file = f"test-user-{environment}.json"
        with open(creds_file, 'w') as f:
            json.dump({
                "environment": environment,
                "user_id": user_id,
                "email": email,
                "password": password,
                "api_url": f"https://api-{environment}.compliantguard.com" if environment != "dev" else "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com",
                "table_name": table_name,
                "created_at": datetime.utcnow().isoformat()
            }, indent=2)
        
        print(f"📄 Credentials saved to: {creds_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        print("💡 Make sure:")
        print("   - AWS credentials are configured")
        print("   - You have access to the DynamoDB table")
        print("   - The table exists in the specified environment")
        return False

def test_login():
    """Test login with the created user"""
    print("\n🧪 Testing Login")
    print("=" * 20)
    
    # Find credentials file
    environment = input("Enter environment to test [dev]: ").strip() or "dev"
    creds_file = f"test-user-{environment}.json"
    
    if not os.path.exists(creds_file):
        print(f"❌ Credentials file {creds_file} not found")
        print("Run the create user option first")
        return False
    
    with open(creds_file, 'r') as f:
        creds = json.load(f)
    
    print(f"📋 Testing login for: {creds['email']}")
    print(f"🌐 API URL: {creds['api_url']}")
    
    # Create a simple test script
    test_script = f"""#!/usr/bin/env python3
import requests
import json

# Test credentials
email = "{creds['email']}"
password = "{creds['password']}"
api_url = "{creds['api_url']}"

print("🧪 Testing AWS Deployment Login")
print("==============================")

# Test 1: Login
print("\\n1. Testing login...")
login_data = {{
    "email": email,
    "password": password
}}

try:
    response = requests.post(f"{{api_url}}/api/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        access_token = data['access_token']
        print("✅ Login successful!")
        print(f"   Token: {{access_token[:20]}}...")
        
        # Test 2: Verify token
        print("\\n2. Testing token verification...")
        headers = {{"Authorization": f"Bearer {{access_token}}"}}
        
        verify_response = requests.get(f"{{api_url}}/api/v1/auth/verify", headers=headers)
        if verify_response.status_code == 200:
            user_data = verify_response.json()
            print("✅ Token verification successful!")
            print(f"   User: {{user_data['user']['email']}}")
            
            # Test 3: List GCP projects
            print("\\n3. Testing GCP projects endpoint...")
            projects_response = requests.get(f"{{api_url}}/api/v1/gcp/projects", headers=headers)
            if projects_response.status_code == 200:
                projects = projects_response.json()
                print(f"✅ GCP projects endpoint accessible!")
                print(f"   Projects found: {{len(projects)}}")
                
                print("\\n🎉 All tests passed! Ready for GCP scanning.")
                print("\\n📋 Your authentication token:")
                print(f"Authorization: Bearer {{access_token}}")
                print("\\n🚀 You can now:")
                print("1. Upload GCP service account credentials")
                print("2. Run compliance scans")
                print("3. View scan results")
                
            else:
                print(f"❌ GCP projects endpoint failed: {{projects_response.status_code}}")
        else:
            print(f"❌ Token verification failed: {{verify_response.status_code}}")
    else:
        print(f"❌ Login failed: {{response.status_code}}")
        print(f"   Response: {{response.text}}")
        
except Exception as e:
    print(f"❌ Test failed: {{e}}")
    print("💡 Make sure the API is deployed and accessible")
"""
    
    test_file = f"test-login-{environment}.py"
    with open(test_file, 'w') as f:
        f.write(test_script)
    
    os.chmod(test_file, 0o755)
    print(f"📄 Test script created: {test_file}")
    
    # Run the test
    run_test = input("Run the test now? (Y/n): ").strip().lower()
    if run_test != 'n':
        print("\n" + "="*50)
        os.system(f"python3 {test_file}")
    
    return True

def main():
    """Main function"""
    print("🔐 AWS Deployment Test User Setup")
    print("=" * 35)
    print("")
    print("This tool helps you create test users for the deployed AWS environment")
    print("so you can test GCP scanning with real credentials.")
    print("")
    
    while True:
        print("Options:")
        print("1. Create test user in AWS DynamoDB")
        print("2. Test login with existing user")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            create_test_user()
        elif choice == "2":
            test_login()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()