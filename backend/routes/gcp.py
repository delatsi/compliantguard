from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, List
import json

from ..core.auth import get_current_user
from ..services.gcp_credential_service import gcp_credential_service

router = APIRouter()

class GCPCredentialUpload(BaseModel):
    project_id: str
    service_account_json: Dict

class GCPProjectInfo(BaseModel):
    project_id: str
    service_account_email: str
    created_at: str
    last_used: Optional[str]
    status: str

@router.post("/credentials")
async def upload_gcp_credentials(
    credential_data: GCPCredentialUpload,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and securely store GCP service account credentials
    """
    try:
        result = await gcp_credential_service.store_credentials(
            user_id=current_user["user_id"],
            project_id=credential_data.project_id,
            service_account_json=credential_data.service_account_json
        )
        
        return {
            "message": "GCP credentials stored successfully",
            "project_id": result["project_id"],
            "service_account_email": result["service_account_email"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to store GCP credentials"
        )

@router.post("/credentials/upload")
async def upload_gcp_credentials_file(
    project_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload GCP service account JSON file
    """
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
        
        # Validate required fields
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
        
        # Store credentials
        result = await gcp_credential_service.store_credentials(
            user_id=current_user["user_id"],
            project_id=project_id,
            service_account_json=service_account_json
        )
        
        return {
            "message": "GCP credentials uploaded and stored successfully",
            "project_id": result["project_id"],
            "service_account_email": result["service_account_email"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload GCP credentials"
        )

@router.get("/projects", response_model=List[GCPProjectInfo])
async def list_gcp_projects(
    current_user: dict = Depends(get_current_user)
):
    """
    List all GCP projects configured for the current user
    """
    try:
        projects = await gcp_credential_service.list_user_projects(
            current_user["user_id"]
        )
        return projects
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to list GCP projects"
        )

@router.delete("/projects/{project_id}/credentials")
async def revoke_gcp_credentials(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke GCP credentials for a specific project
    """
    try:
        result = await gcp_credential_service.revoke_credentials(
            user_id=current_user["user_id"],
            project_id=project_id
        )
        
        return {
            "message": f"GCP credentials revoked for project {project_id}",
            "project_id": project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke GCP credentials"
        )

@router.get("/projects/{project_id}/status")
async def check_gcp_project_status(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check the status of GCP credentials for a project
    """
    try:
        projects = await gcp_credential_service.list_user_projects(
            current_user["user_id"]
        )
        
        project = next((p for p in projects if p['project_id'] == project_id), None)
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail="GCP project not found"
            )
        
        return {
            "project_id": project_id,
            "status": project['status'],
            "service_account_email": project['service_account_email'],
            "last_used": project.get('last_used'),
            "connection_status": "connected" if project['status'] == 'active' else "disconnected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to check project status"
        )