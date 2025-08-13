#!/usr/bin/env python3
"""
Start Local Development Server with Mock Authentication
"""
import os
import sys
from pathlib import Path

# Set environment variables for local development
os.environ["AWS_REGION"] = "us-east-1"
os.environ["DYNAMODB_TABLE_NAME"] = "themisguard-dev-scans"
os.environ["GCP_CREDENTIALS_TABLE"] = "themisguard-dev-gcp-credentials"
os.environ["KMS_KEY_ALIAS"] = "alias/compliantguard-gcp-credentials"
os.environ["JWT_SECRET_KEY"] = "local-dev-secret-key-not-for-production"
os.environ["ENVIRONMENT"] = "development"
os.environ["S3_BUCKET_NAME"] = "themisguard-dev-reports"

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    # Import your backend app
    from backend.main import app

    # Add development-friendly middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add a development info endpoint
    @app.get("/dev/info")
    async def dev_info():
        return {
            "environment": "development",
            "aws_region": os.environ.get("AWS_REGION"),
            "dynamodb_table": os.environ.get("DYNAMODB_TABLE_NAME"),
            "gcp_table": os.environ.get("GCP_CREDENTIALS_TABLE"),
            "kms_key": os.environ.get("KMS_KEY_ALIAS"),
            "s3_bucket": os.environ.get("S3_BUCKET_NAME"),
            "endpoints": {
                "auth": {
                    "register": "POST /api/v1/auth/register",
                    "login": "POST /api/v1/auth/login",
                    "verify": "GET /api/v1/auth/verify",
                },
                "gcp": {
                    "upload_file": "POST /api/v1/gcp/credentials/upload",
                    "upload_json": "POST /api/v1/gcp/credentials",
                    "list_projects": "GET /api/v1/gcp/projects",
                    "project_status": "GET /api/v1/gcp/projects/{id}/status",
                    "revoke": "DELETE /api/v1/gcp/projects/{id}/credentials",
                },
            },
            "test_credentials": {
                "email": "test@example.com",
                "password": "testpass123",
                "note": "Use these to login or register a new account",
            },
        }

    if __name__ == "__main__":
        print("🚀 Starting CompliantGuard Local Development Server")
        print("=" * 55)
        print("Server will be available at: http://localhost:8000")
        print("API Documentation: http://localhost:8000/docs")
        print("Development Info: http://localhost:8000/dev/info")
        print("")
        print("🔑 Authentication Endpoints:")
        print("   Register: POST /api/v1/auth/register")
        print("   Login:    POST /api/v1/auth/login")
        print("   Verify:   GET /api/v1/auth/verify")
        print("")
        print("🔧 GCP Integration Endpoints:")
        print("   Upload:   POST /api/v1/gcp/credentials/upload")
        print("   Projects: GET /api/v1/gcp/projects")
        print("   Status:   GET /api/v1/gcp/projects/{id}/status")
        print("")
        print("📝 Test Credentials:")
        print("   Email: test@example.com")
        print("   Password: testpass123")
        print("")
        print("🧪 To test authentication:")
        print("   python3 test_local_auth.py")
        print("")
        print("Press Ctrl+C to stop the server")
        print("=" * 55)

        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("\nTo install required dependencies:")
    print("pip install fastapi uvicorn python-multipart")
    print("\nOr use a virtual environment:")
    print("cd backend")
    print("python3 -m venv venv")
    print("source venv/bin/activate")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Server startup failed: {e}")
    sys.exit(1)
