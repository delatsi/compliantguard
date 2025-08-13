#!/usr/bin/env python3
"""
Minimal Backend Test Server for GCP Integration
"""
import json
import os
import sys
from pathlib import Path

# Set environment variables for testing
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['DYNAMODB_TABLE_NAME'] = 'compliantguard-gcp-credentials'
os.environ['KMS_KEY_ALIAS'] = 'alias/compliantguard-gcp-credentials'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-local-development'
os.environ['ENVIRONMENT'] = 'test'

try:
    import base64
    import uuid
    from datetime import datetime
    from typing import Dict, List, Optional

    import boto3
    import uvicorn
    from botocore.exceptions import ClientError
    from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please install: pip install fastapi uvicorn boto3 pydantic")
    sys.exit(1)

app = FastAPI(title="CompliantGuard GCP Test Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock authentication for testing
def get_current_user():
    """Mock authentication - returns test user"""
    return {"user_id": "test-user-123", "email": "test@example.com"}

# Pydantic models
class GCPCredentialUpload(BaseModel):
    project_id: str
    service_account_json: Dict

class GCPProjectInfo(BaseModel):
    project_id: str
    service_account_email: str
    created_at: str
    last_used: Optional[str]
    status: str

# Initialize AWS clients
try:
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    kms_client = boto3.client('kms', region_name='us-east-1')
    creds_table = dynamodb.Table('compliantguard-gcp-credentials')
    print("✅ AWS clients initialized successfully")
except Exception as e:
    print(f"⚠️  AWS client initialization failed: {e}")
    dynamodb = None
    kms_client = None
    creds_table = None

@app.get("/")
async def root():
    return {
        "message": "CompliantGuard GCP Test Server",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth (mocked)",
            "gcp": "/api/v1/gcp"
        },
        "aws_status": {
            "dynamodb": "connected" if creds_table else "error",
            "kms": "connected" if kms_client else "error"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "GCP test server running",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "dynamodb": "ok" if creds_table else "error",
            "kms": "ok" if kms_client else "error"
        }
    }

@app.post("/api/v1/gcp/credentials")
async def upload_gcp_credentials(
    credential_data: GCPCredentialUpload,
    current_user: dict = Depends(get_current_user)
):
    """Upload and store GCP service account credentials (test version)"""
    try:
        # Validate service account structure
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                          'client_email', 'client_id', 'auth_uri', 'token_uri']
        
        missing_fields = [field for field in required_fields 
                         if field not in credential_data.service_account_json]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service account file. Missing fields: {missing_fields}"
            )
        
        if credential_data.service_account_json['type'] != 'service_account':
            raise HTTPException(
                status_code=400,
                detail="File must be a service account key"
            )
        
        # Simulate credential storage (without actual encryption for testing)
        if creds_table:
            item = {
                'user_id': current_user["user_id"],
                'project_id': credential_data.project_id,
                'credential_id': str(uuid.uuid4()),
                'encrypted_credentials': base64.b64encode(
                    json.dumps(credential_data.service_account_json).encode()
                ).decode(),
                'service_account_email': credential_data.service_account_json['client_email'],
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active',
                'test_mode': True
            }
            
            creds_table.put_item(Item=item)
            
            return {
                "message": "GCP credentials stored successfully (test mode)",
                "project_id": credential_data.project_id,
                "service_account_email": credential_data.service_account_json['client_email'],
                "test_mode": True
            }
        else:
            return {
                "message": "GCP credentials validated (simulation mode - no storage)",
                "project_id": credential_data.project_id,
                "service_account_email": credential_data.service_account_json['client_email'],
                "simulation_mode": True
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store GCP credentials: {str(e)}"
        )

@app.post("/api/v1/gcp/credentials/upload")
async def upload_gcp_credentials_file(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload GCP service account JSON file"""
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(
                status_code=400,
                detail="Only JSON files are allowed"
            )
        
        # Read and parse JSON
        content = await file.read()
        try:
            service_account_json = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON file format"
            )
        
        # Use the same validation logic as the other endpoint
        credential_data = GCPCredentialUpload(
            project_id=project_id,
            service_account_json=service_account_json
        )
        
        return await upload_gcp_credentials(credential_data, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload GCP credentials: {str(e)}"
        )

@app.get("/api/v1/gcp/projects", response_model=List[GCPProjectInfo])
async def list_gcp_projects(
    current_user: dict = Depends(get_current_user)
):
    """List all GCP projects configured for the current user"""
    try:
        if not creds_table:
            return []
        
        response = creds_table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': current_user["user_id"]},
        )
        
        projects = []
        for item in response.get('Items', []):
            projects.append({
                'project_id': item['project_id'],
                'service_account_email': item['service_account_email'],
                'created_at': item['created_at'],
                'last_used': item.get('last_used'),
                'status': item.get('status', 'unknown')
            })
        
        return projects
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list GCP projects: {str(e)}"
        )

@app.delete("/api/v1/gcp/projects/{project_id}/credentials")
async def revoke_gcp_credentials(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke GCP credentials for a specific project"""
    try:
        if creds_table:
            creds_table.update_item(
                Key={'user_id': current_user["user_id"], 'project_id': project_id},
                UpdateExpression='SET #status = :status, revoked_at = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'revoked',
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
        
        return {
            "message": f"GCP credentials revoked for project {project_id}",
            "project_id": project_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke GCP credentials: {str(e)}"
        )

@app.get("/api/v1/gcp/test/validate-structure")
async def validate_service_account_structure():
    """Test endpoint to validate service account JSON structure"""
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
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-sa%40test-project-456.iam.gserviceaccount.com"
    }
    
    required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                      'client_email', 'client_id', 'auth_uri', 'token_uri']
    
    missing_fields = [field for field in required_fields if field not in sample_sa]
    
    return {
        "sample_structure": sample_sa,
        "required_fields": required_fields,
        "missing_fields": missing_fields,
        "valid": len(missing_fields) == 0 and sample_sa.get('type') == 'service_account'
    }

if __name__ == "__main__":
    print("🚀 Starting CompliantGuard GCP Test Server")
    print("==========================================")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("GCP Endpoints: http://localhost:8000/api/v1/gcp")
    print("")
    print("🧪 Test Mode Features:")
    print("- Mock authentication (no real JWT required)")
    print("- Service account validation")
    print("- DynamoDB integration (if available)")
    print("- File upload testing")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)