#!/usr/bin/env python3
"""
Test Local Authentication and GCP Integration
"""
import json
import urllib.request
import urllib.parse
import urllib.error
import base64

def make_request(url, data=None, headers=None, method='GET'):
    """Make HTTP request with proper error handling"""
    if headers is None:
        headers = {}
    
    if data:
        if isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        headers['Content-Length'] = str(len(data))
    
    req = urllib.request.Request(url, data=data, headers=headers)
    req.get_method = lambda: method
    
    try:
        with urllib.request.urlopen(req) as response:
            return {
                'status': response.status,
                'data': json.loads(response.read().decode())
            }
    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read().decode())
        except:
            error_data = {'detail': str(e)}
        return {
            'status': e.code,
            'error': error_data
        }
    except Exception as e:
        return {
            'status': 0,
            'error': {'detail': str(e)}
        }

def test_local_auth():
    """Test local authentication flow"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Local Authentication & GCP Integration")
    print("=" * 50)
    
    # Test 1: Register a test user
    print("\n1. Registering test user...")
    register_data = {
        "first_name": "Test",
        "last_name": "User", 
        "email": "test@example.com",
        "password": "testpass123",
        "company": "Test Company"
    }
    
    response = make_request(f"{base_url}/api/v1/auth/register", register_data, method='POST')
    
    if response['status'] == 200:
        print("✅ Registration successful!")
        access_token = response['data']['access_token']
        user_info = response['data']['user']
        print(f"   User ID: {user_info['user_id']}")
        print(f"   Email: {user_info['email']}")
        print(f"   Name: {user_info['profile']['name']}")
    elif response['status'] == 400 and 'already exists' in response['error']['detail']:
        print("⚠️  User already exists, trying to login...")
        
        # Test 2: Login with existing user
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = make_request(f"{base_url}/api/v1/auth/login", login_data, method='POST')
        
        if response['status'] == 200:
            print("✅ Login successful!")
            access_token = response['data']['access_token']
            user_info = response['data']['user']
            print(f"   User ID: {user_info['user_id']}")
            print(f"   Email: {user_info['email']}")
        else:
            print(f"❌ Login failed: {response['error']['detail']}")
            return
    else:
        print(f"❌ Registration failed: {response['error']['detail']}")
        return
    
    # Test 3: Verify token
    print("\n2. Verifying authentication token...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = make_request(f"{base_url}/api/v1/auth/verify", headers=headers)
    if response['status'] == 200:
        print("✅ Token verification successful!")
        print(f"   Authenticated as: {response['data']['user']['email']}")
    else:
        print(f"❌ Token verification failed: {response['error']['detail']}")
        return
    
    # Test 4: Test GCP endpoints with authentication
    print("\n3. Testing GCP endpoints with authentication...")
    
    # List projects (should be empty initially)
    response = make_request(f"{base_url}/api/v1/gcp/projects", headers=headers)
    if response['status'] == 200:
        projects = response['data']
        print(f"✅ GCP projects retrieved: {len(projects)} projects found")
        for project in projects:
            print(f"   - {project['project_id']}: {project['service_account_email']}")
    else:
        print(f"❌ GCP projects failed: {response['error']['detail']}")
    
    # Test 5: Test credential upload (simulation)
    print("\n4. Testing credential upload simulation...")
    
    # Create a test service account structure
    test_service_account = {
        "type": "service_account",
        "project_id": "test-project-123",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nTEST-KEY-CONTENT\n-----END PRIVATE KEY-----\n",
        "client_email": "test-sa@test-project-123.iam.gserviceaccount.com",
        "client_id": "123456789012345678901",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-sa%40test-project-123.iam.gserviceaccount.com"
    }
    
    credential_data = {
        "project_id": "test-project-123",
        "service_account_json": test_service_account
    }
    
    response = make_request(f"{base_url}/api/v1/gcp/credentials", credential_data, headers=headers, method='POST')
    if response['status'] == 200:
        print("✅ GCP credential upload successful!")
        print(f"   Project: {response['data']['project_id']}")
        print(f"   Service Account: {response['data']['service_account_email']}")
    else:
        print(f"❌ GCP credential upload failed: {response['error']['detail']}")
    
    # Test 6: List projects again (should show the test project)
    print("\n5. Listing projects after credential upload...")
    response = make_request(f"{base_url}/api/v1/gcp/projects", headers=headers)
    if response['status'] == 200:
        projects = response['data']
        print(f"✅ GCP projects retrieved: {len(projects)} projects found")
        for project in projects:
            print(f"   - {project['project_id']}: {project['service_account_email']}")
    else:
        print(f"❌ GCP projects failed: {response['error']['detail']}")
    
    print(f"\n🎉 Authentication & GCP Integration Test Complete!")
    print("=" * 50)
    print(f"📝 Your credentials:")
    print(f"   Email: test@example.com")
    print(f"   Password: testpass123")
    print(f"   Access Token: {access_token[:20]}...")
    print("")
    print("🚀 You can now use these credentials to:")
    print("   1. Login to the frontend")
    print("   2. Test GCP credential uploads")
    print("   3. Access all authenticated endpoints")
    print("")
    print("💡 API Usage Examples:")
    print(f'   curl -H "Authorization: Bearer {access_token}" \\')
    print(f'        {base_url}/api/v1/gcp/projects')
    print("")
    print(f'   curl -X POST {base_url}/api/v1/gcp/credentials \\')
    print(f'        -H "Authorization: Bearer {access_token}" \\')
    print(f'        -H "Content-Type: application/json" \\')
    print(f'        -d \'{{...credential_data...}}\'')

if __name__ == "__main__":
    test_local_auth()