import base64
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timedelta

import boto3

# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb")

# JWT secret key from environment
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "debug-secret-key-minimal")


def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_jwt_token(user_data):
    """Create a simple JWT token"""
    try:
        # Simple JWT implementation
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "role": user_data.get("role", "user"),
            "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),
        }

        # Encode header and payload
        header_encoded = (
            base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        )
        payload_encoded = (
            base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        )

        # Create signature
        message = f"{header_encoded}.{payload_encoded}"
        signature = hmac.new(
            JWT_SECRET.encode(), message.encode(), hashlib.sha256
        ).digest()
        signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip("=")

        return f"{message}.{signature_encoded}"
    except Exception as e:
        print(f"❌ Error creating JWT: {e}")
        return None


def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        if not token:
            return None

        # Remove Bearer prefix if present
        if token.startswith("Bearer "):
            token = token[7:]

        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_encoded, payload_encoded, signature_encoded = parts

        # Verify signature
        message = f"{header_encoded}.{payload_encoded}"
        expected_signature = hmac.new(
            JWT_SECRET.encode(), message.encode(), hashlib.sha256
        ).digest()
        expected_signature_encoded = (
            base64.urlsafe_b64encode(expected_signature).decode().rstrip("=")
        )

        if signature_encoded != expected_signature_encoded:
            print("❌ JWT signature verification failed")
            return None

        # Decode payload
        # Add padding if needed
        payload_encoded += "=" * (4 - len(payload_encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_encoded).decode())

        # Check expiration
        if payload.get("exp", 0) < datetime.utcnow().timestamp():
            print("❌ JWT token expired")
            return None

        return payload
    except Exception as e:
        print(f"❌ Error verifying JWT: {e}")
        return None


def get_auth_user(event):
    """Extract and verify user from Authorization header"""
    headers = event.get("headers", {})
    auth_header = headers.get("Authorization") or headers.get("authorization")

    if not auth_header:
        print("❌ No Authorization header found")
        return None

    user_data = verify_jwt_token(auth_header)
    if user_data:
        print(f"✅ Authenticated user: {user_data['email']}")
        return user_data
    else:
        print("❌ Authentication failed")
        return None


def create_test_user():
    """Create a test user account"""
    try:
        users_table = dynamodb.Table("themisguard-minimal-users")

        test_user = {
            "user_id": "test-user-001",
            "email": "test@compliantguard.com",
            "password_hash": hash_password("password123"),
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "role": "user",
        }

        users_table.put_item(Item=test_user)
        print(f"✅ Test user created: {test_user['email']}")
        return test_user

    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None


def login_user(email, password):
    """Simple user login"""
    try:
        users_table = dynamodb.Table("themisguard-minimal-users")

        response = users_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr("email").eq(email)
        )

        if not response["Items"]:
            return None

        user = response["Items"][0]
        password_hash = hash_password(password)

        if user["password_hash"] == password_hash:
            return user
        return None

    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None


def handler(event, context):
    """Enhanced Lambda handler with user authentication"""

    print(f"🏠 Enhanced API accessed")
    print(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
    print(f"🕐 Timestamp: {datetime.utcnow().isoformat()}")
    print(f"📍 Region: {os.getenv('AWS_DEFAULT_REGION', 'unknown')}")
    print(f"🔍 Event: {json.dumps(event, indent=2)}")

    # Extract request info
    http_method = event.get("httpMethod", "UNKNOWN")
    path = event.get("path", "/")
    body = event.get("body", "{}")

    print(f"🌐 Request: {http_method} {path}")
    print(f"📊 Headers: {event.get('headers', {})}")
    print(f"📝 Body: {body}")

    try:
        # Parse JSON body if present
        request_data = {}
        if body and body != "{}":
            try:
                request_data = json.loads(body)
            except:
                pass

        # Route handling
        if path == "/health":
            print(f"❤️ Health check endpoint accessed")
            response_body = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                "debug": "debugging_working",
            }

        elif path == "/create-test-user" and http_method == "POST":
            print(f"👤 Creating test user...")
            user = create_test_user()
            if user:
                response_body = {
                    "message": "Test user created successfully",
                    "email": user["email"],
                    "password": "password123",
                    "user_id": user["user_id"],
                }
            else:
                response_body = {"error": "Failed to create test user"}

        elif path == "/login" and http_method == "POST":
            print(f"🔑 Login attempt...")
            email = request_data.get("email", "")
            password = request_data.get("password", "")

            print(f"📧 Email: {email}")

            user = login_user(email, password)
            if user:
                # Generate JWT token
                token = create_jwt_token(user)
                if token:
                    response_body = {
                        "message": "Login successful",
                        "user_id": user["user_id"],
                        "email": user["email"],
                        "role": user["role"],
                        "access_token": token,
                        "token_type": "Bearer",
                        "expires_in": 86400,  # 24 hours
                    }
                else:
                    response_body = {"error": "Failed to generate access token"}
            else:
                response_body = {"error": "Invalid credentials"}

        elif path == "/users" and http_method == "GET":
            print(f"👥 Listing users...")
            # Require authentication
            auth_user = get_auth_user(event)
            if not auth_user:
                return {
                    "statusCode": 401,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    "body": json.dumps({"error": "Authentication required"}),
                }

            try:
                users_table = dynamodb.Table("themisguard-minimal-users")
                response = users_table.scan()
                users = [
                    {
                        "user_id": item["user_id"],
                        "email": item["email"],
                        "created_at": item.get("created_at"),
                        "is_active": item.get("is_active"),
                    }
                    for item in response["Items"]
                ]
                response_body = {"users": users}
            except Exception as e:
                response_body = {"error": f"Failed to list users: {str(e)}"}

        elif path == "/gcp/credentials" and http_method == "POST":
            print(f"🔑 GCP credential upload request...")
            # Require authentication
            auth_user = get_auth_user(event)
            if not auth_user:
                return {
                    "statusCode": 401,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    "body": json.dumps({"error": "Authentication required"}),
                }

            # Use authenticated user's ID instead of trusting the request
            user_id = auth_user["user_id"]
            project_id = request_data.get("project_id", "")
            service_account_json = request_data.get("service_account_json", {})

            print(f"👤 Authenticated User ID: {user_id}")
            print(f"🎯 Project ID: {project_id}")
            print(
                f"📝 Service Account Keys: {list(service_account_json.keys()) if service_account_json else 'None'}"
            )

            if not project_id or not service_account_json:
                response_body = {
                    "error": "Missing required fields: project_id, service_account_json"
                }
            else:
                try:
                    # Store GCP credentials (simplified for testing)
                    credential_id = f"gcp-{user_id}-{project_id}"

                    # In a real implementation, you'd encrypt the service account JSON
                    # For testing, we'll just store it directly
                    gcp_credential = {
                        "credential_id": credential_id,
                        "user_id": user_id,
                        "project_id": project_id,
                        "service_account_json": json.dumps(service_account_json),
                        "created_at": datetime.utcnow().isoformat(),
                        "is_active": True,
                    }

                    # Note: In production, you'd create a separate GCP credentials table
                    # For this test, we'll just return success
                    print(
                        f"✅ GCP credentials would be stored for project: {project_id}"
                    )

                    response_body = {
                        "message": "GCP credentials uploaded successfully (test mode)",
                        "credential_id": credential_id,
                        "project_id": project_id,
                        "user_id": user_id,
                        "note": "In production, credentials would be encrypted and stored securely",
                    }

                except Exception as e:
                    print(f"❌ Error storing GCP credentials: {e}")
                    response_body = {
                        "error": f"Failed to store GCP credentials: {str(e)}"
                    }

        else:
            print(f"🏠 Root/default endpoint accessed")
            response_body = {
                "message": "ThemisGuard HIPAA Compliance API - Enhanced Debug Version",
                "version": "debug-2.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "path": path,
                "method": http_method,
                "endpoints": {
                    "/health": "Health check",
                    "/create-test-user": "POST - Create test user account",
                    "/login": "POST - Login with email/password",
                    "/users": "GET - List all users",
                    "/gcp/credentials": "POST - Upload GCP service account credentials",
                },
                "test_credentials": {
                    "email": "test@compliantguard.com",
                    "password": "password123",
                    "note": "Call /create-test-user first to create this account",
                },
            }

        print(f"✅ Response prepared successfully")
        print(f"📦 Response body: {json.dumps(response_body, indent=2)}")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            "body": json.dumps(response_body),
        }

    except Exception as e:
        print(f"❌ Error in handler: {type(e).__name__}: {str(e)}")
        print(f"🔍 Exception details: {repr(e)}")

        error_response = {
            "error": str(e),
            "type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(error_response),
        }
