#!/usr/bin/env python3
"""
Standalone test script to verify GCP endpoints work
Run this to test the GCP functionality independently
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import json
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GCP Test API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "GCP Test API", "status": "running"}

@app.post("/api/v1/gcp/credentials/upload")
async def upload_gcp_credentials_file(
    project_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload GCP service account JSON file"""
    try:
        print(f"Received upload request for project: {project_id}")
        print(f"File: {file.filename}, Content-Type: {file.content_type}")
        
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(
                status_code=400,
                detail="Only JSON files are allowed"
            )
        
        # Read and parse JSON
        content = await file.read()
        print(f"File size: {len(content)} bytes")
        
        try:
            service_account_json = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON file format: {str(e)}"
            )
        
        # Basic validation of required fields
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                          'client_email', 'client_id', 'auth_uri', 'token_uri']
        
        missing_fields = [field for field in required_fields 
                         if field not in service_account_json]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service account file. Missing fields: {missing_fields}"
            )
        
        if service_account_json['type'] != 'service_account':
            raise HTTPException(
                status_code=400,
                detail="File must be a service account key"
            )
        
        print(f"✅ Valid service account for: {service_account_json.get('client_email')}")
        
        # Return success
        return {
            "message": "GCP credentials uploaded and stored successfully",
            "project_id": project_id,
            "service_account_email": service_account_json.get('client_email', 'unknown'),
            "file_project_id": service_account_json.get('project_id'),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload GCP credentials: {str(e)}"
        )

@app.get("/api/v1/gcp/projects")
async def list_gcp_projects():
    """List all GCP projects configured for the current user"""
    print("📋 Listing GCP projects")
    # Return some test data to verify the endpoint works
    return [
        {
            "project_id": "test-project-1", 
            "service_account_email": "test@test-project-1.iam.gserviceaccount.com",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "last_used": "2024-01-02T00:00:00Z"
        }
    ]

@app.delete("/api/v1/gcp/projects/{project_id}/credentials")
async def revoke_gcp_credentials(project_id: str):
    """Revoke GCP credentials for a specific project"""
    print(f"🗑️ Revoking credentials for project: {project_id}")
    return {
        "message": f"GCP credentials revoked for project {project_id}",
        "project_id": project_id,
        "status": "revoked"
    }

if __name__ == "__main__":
    print("🚀 Starting GCP Test API on port 8002...")
    print("📝 Test endpoints:")
    print("  GET  http://localhost:8002/api/v1/gcp/projects")
    print("  POST http://localhost:8002/api/v1/gcp/credentials/upload") 
    print("  DELETE http://localhost:8002/api/v1/gcp/projects/{project_id}/credentials")
    print("\n💡 Change frontend API URL to http://localhost:8002 to test")
    
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=False)
