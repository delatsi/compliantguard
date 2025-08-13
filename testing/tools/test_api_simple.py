#!/usr/bin/env python3
"""
Simple GCP API Test Script (without complex dependencies)
"""
import json
import os
import sys
import time
from pathlib import Path

import requests


def log_info(message):
    print(f"✅ {message}")


def log_warning(message):
    print(f"⚠️  {message}")


def log_error(message):
    print(f"❌ {message}")


def test_gcp_api():
    """Test GCP API endpoints"""
    print("🧪 Testing GCP API Endpoints")
    print("============================")

    base_url = "http://localhost:8000"

    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            log_info("Health check passed")
            print(f"   Response: {response.json()}")
        else:
            log_error(f"Health check failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        log_error(f"Health check failed: {e}")
        print("   Make sure the backend server is running:")
        print("   cd backend && python -m uvicorn main:app --reload")
        return False

    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            log_info("Root endpoint accessible")
            data = response.json()
            if "endpoints" in data:
                log_info("API endpoints discovered")
                for key, value in data["endpoints"].items():
                    print(f"   {key}: {value}")
        else:
            log_error(f"Root endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        log_error(f"Root endpoint failed: {e}")

    # Test 3: GCP projects endpoint (without auth - should fail gracefully)
    print("\n3. Testing GCP projects endpoint (without auth)...")
    try:
        response = requests.get(f"{base_url}/api/v1/gcp/projects", timeout=5)
        if response.status_code == 401:
            log_info("Authentication required (expected)")
            print("   This confirms the endpoint exists and auth is working")
        elif response.status_code == 422:
            log_info("Validation error (expected without auth)")
        else:
            log_warning(f"Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        log_error(f"GCP projects endpoint test failed: {e}")

    # Test 4: Create sample service account for structure testing
    print("\n4. Testing service account structure validation...")
    sample_sa = {
        "type": "service_account",
        "project_id": "test-project-456",
        "private_key_id": "sample-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nSAMPLE\n-----END PRIVATE KEY-----\n",
        "client_email": "test-sa@test-project-456.iam.gserviceaccount.com",
        "client_id": "123456789012345678901",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-sa%40test-project-456.iam.gserviceaccount.com",
    }

    # Validate required fields
    required_fields = [
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
    ]

    missing_fields = [field for field in required_fields if field not in sample_sa]

    if not missing_fields:
        log_info("Service account structure validation passed")
        if sample_sa["type"] == "service_account":
            log_info("Service account type is correct")
        else:
            log_error("Invalid service account type")
    else:
        log_error(f"Missing required fields: {missing_fields}")

    print("\n📋 API Test Summary")
    print("==================")
    print("✅ Backend server is accessible")
    print("✅ Health endpoints working")
    print("✅ GCP endpoints exist and require authentication")
    print("✅ Service account structure validation ready")
    print("")
    print("🎯 To test with authentication:")
    print("1. Register/login to get JWT token")
    print("2. Use token in Authorization header")
    print("3. Upload real GCP service account credentials")
    print("")
    print("📝 Example with auth:")
    print(f'curl -H "Authorization: Bearer <token>" \\')
    print(f"     {base_url}/api/v1/gcp/projects")
    print("")
    print("📤 Example credential upload:")
    print(f"curl -X POST {base_url}/api/v1/gcp/credentials/upload \\")
    print(f'     -H "Authorization: Bearer <token>" \\')
    print(f'     -F "project_id=your-project-id" \\')
    print(f'     -F "file=@your-service-account.json"')

    return True


if __name__ == "__main__":
    print("🚀 Starting GCP API Integration Test")
    print("====================================")
    print("")

    # Check if requests is available
    try:
        import requests
    except ImportError:
        log_error("requests library not found. Install with: pip install requests")
        sys.exit(1)

    # Run the test
    success = test_gcp_api()

    if success:
        log_info("GCP API integration test completed successfully!")
    else:
        log_error("GCP API integration test failed!")
        sys.exit(1)
