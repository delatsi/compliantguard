#!/usr/bin/env python3
"""
Simple Test Server - Minimal Dependencies
"""
import base64
import hashlib
import hmac
import json
import urllib.parse
import uuid
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# Simple in-memory storage for testing
users_db = {}
gcp_projects_db = {}

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password"""
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def create_jwt(user_id, email):
    """Create a simple JWT-like token"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    token_data = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"simple.{token_data}.test"

def verify_jwt(token):
    """Verify and decode token"""
    try:
        if not token.startswith("simple."):
            return None
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = json.loads(base64.b64decode(parts[1]).decode())
        return payload
    except:
        return None

class TestServerHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def send_json_response(self, data, status=200):
        """Send JSON response with CORS headers"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def get_auth_user(self):
        """Extract user from Authorization header"""
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        token = auth_header[7:]
        return verify_jwt(token)

    def read_json_body(self):
        """Read and parse JSON request body"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return {}
            body = self.rfile.read(content_length)
            return json.loads(body.decode())
        except:
            return {}

    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        if path == '/':
            self.send_json_response({
                "message": "CompliantGuard Simple Test Server",
                "version": "1.0.0",
                "endpoints": {
                    "auth": {
                        "register": "POST /api/v1/auth/register",
                        "login": "POST /api/v1/auth/login",
                        "verify": "GET /api/v1/auth/verify"
                    },
                    "gcp": {
                        "projects": "GET /api/v1/gcp/projects",
                        "upload": "POST /api/v1/gcp/credentials"
                    }
                },
                "test_user": {
                    "email": "test@example.com",
                    "password": "testpass123"
                }
            })
            
        elif path == '/health':
            self.send_json_response({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})
            
        elif path == '/api/v1/auth/verify':
            user = self.get_auth_user()
            if not user:
                self.send_json_response({"detail": "Invalid token"}, 401)
                return
            
            self.send_json_response({
                "user": {
                    "user_id": user["user_id"],
                    "email": user["email"],
                    "profile": users_db.get(user["user_id"], {}).get("profile", {}),
                    "plan_tier": "free"
                }
            })
            
        elif path == '/api/v1/gcp/projects':
            user = self.get_auth_user()
            if not user:
                self.send_json_response({"detail": "Authentication required"}, 401)
                return
            
            user_projects = [p for p in gcp_projects_db.values() if p["user_id"] == user["user_id"]]
            self.send_json_response(user_projects)
            
        elif path.startswith('/api/v1/gcp/projects/') and path.endswith('/status'):
            user = self.get_auth_user()
            if not user:
                self.send_json_response({"detail": "Authentication required"}, 401)
                return
            
            project_id = path.split('/')[-2]
            project = gcp_projects_db.get(f"{user['user_id']}-{project_id}")
            
            if project:
                self.send_json_response({
                    "project_id": project_id,
                    "status": project["status"],
                    "service_account_email": project["service_account_email"],
                    "connection_status": "connected" if project["status"] == "active" else "disconnected"
                })
            else:
                self.send_json_response({
                    "project_id": project_id,
                    "status": "not_found",
                    "connection_status": "disconnected"
                }, 404)
        else:
            self.send_json_response({"detail": "Not found"}, 404)

    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path
        data = self.read_json_body()
        
        if path == '/api/v1/auth/register':
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name', 'Test')
            last_name = data.get('last_name', 'User')
            
            if not email or not password:
                self.send_json_response({"detail": "Email and password required"}, 400)
                return
            
            # Check if user exists
            existing = next((u for u in users_db.values() if u["email"] == email), None)
            if existing:
                self.send_json_response({"detail": "User with this email already exists"}, 400)
                return
            
            # Create user
            user_id = str(uuid.uuid4())
            user = {
                "user_id": user_id,
                "email": email,
                "password_hash": hash_password(password),
                "profile": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "name": f"{first_name} {last_name}",
                    "company": data.get('company')
                },
                "created_at": datetime.utcnow().isoformat(),
                "plan_tier": "free",
                "status": "active"
            }
            users_db[user_id] = user
            
            token = create_jwt(user_id, email)
            self.send_json_response({
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "user_id": user_id,
                    "email": email,
                    "profile": user["profile"],
                    "plan_tier": "free"
                }
            })
            
        elif path == '/api/v1/auth/login':
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                self.send_json_response({"detail": "Email and password required"}, 400)
                return
            
            # Find user
            user = next((u for u in users_db.values() if u["email"] == email), None)
            if not user or not verify_password(password, user["password_hash"]):
                self.send_json_response({"detail": "Invalid email or password"}, 401)
                return
            
            token = create_jwt(user["user_id"], email)
            self.send_json_response({
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "user_id": user["user_id"],
                    "email": user["email"],
                    "profile": user["profile"],
                    "plan_tier": user["plan_tier"]
                }
            })
            
        elif path == '/api/v1/gcp/credentials':
            user = self.get_auth_user()
            if not user:
                self.send_json_response({"detail": "Authentication required"}, 401)
                return
            
            project_id = data.get('project_id')
            service_account_json = data.get('service_account_json')
            
            if not project_id or not service_account_json:
                self.send_json_response({"detail": "project_id and service_account_json required"}, 400)
                return
            
            # Validate service account structure
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                             'client_email', 'client_id', 'auth_uri', 'token_uri']
            
            missing_fields = [field for field in required_fields if field not in service_account_json]
            if missing_fields:
                self.send_json_response({
                    "detail": f"Invalid service account. Missing fields: {missing_fields}"
                }, 400)
                return
            
            if service_account_json.get('type') != 'service_account':
                self.send_json_response({"detail": "Must be a service account key"}, 400)
                return
            
            # Store project (simulated)
            project_key = f"{user['user_id']}-{project_id}"
            gcp_projects_db[project_key] = {
                "user_id": user["user_id"],
                "project_id": project_id,
                "service_account_email": service_account_json["client_email"],
                "created_at": datetime.utcnow().isoformat(),
                "last_used": None,
                "status": "active"
            }
            
            self.send_json_response({
                "message": "GCP credentials stored successfully",
                "project_id": project_id,
                "service_account_email": service_account_json["client_email"]
            })
            
        else:
            self.send_json_response({"detail": "Not found"}, 404)

    def do_DELETE(self):
        """Handle DELETE requests"""
        path = urlparse(self.path).path
        
        if path.startswith('/api/v1/gcp/projects/') and path.endswith('/credentials'):
            user = self.get_auth_user()
            if not user:
                self.send_json_response({"detail": "Authentication required"}, 401)
                return
            
            project_id = path.split('/')[-2]
            project_key = f"{user['user_id']}-{project_id}"
            
            if project_key in gcp_projects_db:
                gcp_projects_db[project_key]["status"] = "revoked"
                self.send_json_response({
                    "message": f"GCP credentials revoked for project {project_id}",
                    "project_id": project_id
                })
            else:
                self.send_json_response({"detail": "Project not found"}, 404)
        else:
            self.send_json_response({"detail": "Not found"}, 404)

    def log_message(self, format, *args):
        """Override to reduce log spam"""
        return

def run_server():
    """Start the test server"""
    port = 8000
    server = HTTPServer(('localhost', port), TestServerHandler)
    
    print("🚀 CompliantGuard Simple Test Server")
    print("=" * 40)
    print(f"Server: http://localhost:{port}")
    print("Health: http://localhost:{port}/health")
    print("")
    print("🔑 Authentication:")
    print("   Register: POST /api/v1/auth/register")
    print("   Login:    POST /api/v1/auth/login")
    print("   Verify:   GET /api/v1/auth/verify")
    print("")
    print("🔧 GCP Integration:")
    print("   Upload:   POST /api/v1/gcp/credentials")
    print("   Projects: GET /api/v1/gcp/projects")
    print("   Status:   GET /api/v1/gcp/projects/{id}/status")
    print("   Revoke:   DELETE /api/v1/gcp/projects/{id}/credentials")
    print("")
    print("📝 Test User:")
    print("   Email: test@example.com")
    print("   Password: testpass123")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")
        server.shutdown()

if __name__ == "__main__":
    run_server()