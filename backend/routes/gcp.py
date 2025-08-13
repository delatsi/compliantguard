import json
from typing import Dict, List, Optional

from core.auth import get_current_user
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from services.gcp_credential_service import gcp_credential_service


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
    credential_data: GCPCredentialUpload, current_user: dict = Depends(get_current_user)
):
    """
    Upload and securely store GCP service account credentials
    """
    print(f"🔑 GCP credential upload request for user: {current_user.get('user_id')}")
    print(f"🎯 Project ID: {credential_data.project_id}")
    print(
        f"📝 Service account JSON keys: {list(credential_data.service_account_json.keys())}"
    )

    # Extract some info for debugging (without logging sensitive data)
    service_account_email = credential_data.service_account_json.get(
        "client_email", "unknown"
    )
    print(f"📧 Service account email: {service_account_email}")

    try:
        print("💾 Storing credentials via service...")
        result = await gcp_credential_service.store_credentials(
            user_id=current_user["user_id"],
            project_id=credential_data.project_id,
            service_account_json=credential_data.service_account_json,
        )

        print("✅ GCP credentials stored successfully")
        print(f"📊 Result keys: {list(result.keys())}")

        response_data = {
            "message": "GCP credentials stored successfully",
            "project_id": result["project_id"],
            "service_account_email": result["service_account_email"],
        }

        print(f"👤 Returning response for project: {result['project_id']}")
        return response_data

    except HTTPException as http_ex:
        print(f"❌ HTTP Exception in GCP upload: {http_ex.detail}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error in GCP upload: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
        raise HTTPException(status_code=500, detail="Failed to store GCP credentials")


@router.post("/credentials/upload")
async def upload_gcp_credentials_file(
    project_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload GCP service account JSON file
    """
    print(f"📁 GCP file upload request for user: {current_user.get('user_id')}")
    print(f"🎯 Project ID: {project_id}")
    print(f"📎 Filename: {file.filename}")
    print(f"📊 Content type: {file.content_type}")

    try:
        # Validate file type
        print("🔍 Validating file type...")
        if not file.filename.endswith(".json"):
            print(f"❌ Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only JSON files are allowed")

        print("✅ File type validation passed")

        # Read and parse JSON
        print("📄 Reading file content...")
        content = await file.read()
        print(f"📊 Content size: {len(content)} bytes")

        try:
            service_account_json = json.loads(content.decode("utf-8"))
            print("✅ JSON parsed successfully")
            print(f"📝 JSON keys: {list(service_account_json.keys())}")
        except json.JSONDecodeError as json_err:
            print(f"❌ JSON decode error: {json_err}")
            raise HTTPException(status_code=400, detail="Invalid JSON file format")

        # Validate required fields
        print("🔍 Validating required fields...")
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

        missing_fields = [
            field for field in required_fields if field not in service_account_json
        ]

        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service account file. Missing fields: {missing_fields}",
            )

        if service_account_json["type"] != "service_account":
            print(f"❌ Invalid type: {service_account_json.get('type')}")
            raise HTTPException(
                status_code=400, detail="File must be a service account key"
            )

        print("✅ Service account validation passed")
        service_account_email = service_account_json.get("client_email", "unknown")
        json_project_id = service_account_json.get("project_id", "unknown")
        print(f"📧 Service account email: {service_account_email}")
        print(f"🎯 JSON project ID: {json_project_id}")

        # Store credentials
        print("💾 Storing credentials via service...")
        result = await gcp_credential_service.store_credentials(
            user_id=current_user["user_id"],
            project_id=project_id,
            service_account_json=service_account_json,
        )

        print("✅ GCP credentials file uploaded and stored successfully")
        print(f"📊 Result keys: {list(result.keys())}")

        response_data = {
            "message": "GCP credentials uploaded and stored successfully",
            "project_id": result["project_id"],
            "service_account_email": result["service_account_email"],
        }

        print(f"👤 Returning response for project: {result['project_id']}")
        return response_data

    except HTTPException as http_ex:
        print(f"❌ HTTP Exception in GCP file upload: {http_ex.detail}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error in GCP file upload: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload GCP credentials")


@router.get("/projects", response_model=List[GCPProjectInfo])
async def list_gcp_projects(current_user: dict = Depends(get_current_user)):
    """
    List all GCP projects configured for the current user
    """
    print(f"📋 List GCP projects request for user: {current_user.get('user_id')}")

    try:
        print("🔍 Querying user projects via service...")
        projects = await gcp_credential_service.list_user_projects(
            current_user["user_id"]
        )

        print(f"✅ Found {len(projects)} GCP projects")
        if projects:
            for i, project in enumerate(projects):
                print(
                    f"🎯 Project {i + 1}: {project.get('project_id')} ({project.get('status')})"
                )
        else:
            print("📎 No GCP projects configured for user")

        print(f"👤 Returning {len(projects)} projects")
        return projects

    except Exception as e:
        print(f"❌ Error listing GCP projects: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
        raise HTTPException(status_code=500, detail="Failed to list GCP projects")


@router.delete("/projects/{project_id}/credentials")
async def revoke_gcp_credentials(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Revoke GCP credentials for a specific project
    """
    print("🗑️ GCP credential revocation request")
    print(f"👤 User: {current_user.get('user_id')}")
    print(f"🎯 Project ID: {project_id}")

    try:
        print("🔄 Revoking credentials via service...")
        result = await gcp_credential_service.revoke_credentials(
            user_id=current_user["user_id"], project_id=project_id
        )

        print("✅ GCP credentials revoked successfully")
        print(f"📊 Revocation result: {result}")

        response_data = {
            "message": f"GCP credentials revoked for project {project_id}",
            "project_id": project_id,
        }

        print("👤 Returning revocation confirmation")
        return response_data

    except HTTPException as http_ex:
        print(f"❌ HTTP Exception in GCP revocation: {http_ex.detail}")
        raise
    except Exception as e:
        print(f"❌ Error revoking GCP credentials: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
        raise HTTPException(status_code=500, detail="Failed to revoke GCP credentials")


@router.get("/projects/{project_id}/status")
async def check_gcp_project_status(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Check the status of GCP credentials for a project
    """
    print("🔍 GCP project status check")
    print(f"👤 User: {current_user.get('user_id')}")
    print(f"🎯 Project ID: {project_id}")

    try:
        print("📋 Fetching user projects...")
        projects = await gcp_credential_service.list_user_projects(
            current_user["user_id"]
        )

        print(f"🔍 Searching for project {project_id} in {len(projects)} projects")
        project = next((p for p in projects if p["project_id"] == project_id), None)

        if not project:
            print(f"❌ GCP project {project_id} not found")
            raise HTTPException(status_code=404, detail="GCP project not found")

        print(f"✅ Project found: {project.get('service_account_email')}")
        print(f"📊 Project status: {project.get('status')}")
        print(f"🕰️ Last used: {project.get('last_used', 'Never')}")

        connection_status = (
            "connected" if project["status"] == "active" else "disconnected"
        )

        response_data = {
            "project_id": project_id,
            "status": project["status"],
            "service_account_email": project["service_account_email"],
            "last_used": project.get("last_used"),
            "connection_status": connection_status,
        }

        print(f"👤 Returning project status: {connection_status}")
        return response_data

    except HTTPException as http_ex:
        print(f"❌ HTTP Exception in project status: {http_ex.detail}")
        raise
    except Exception as e:
        print(f"❌ Error checking project status: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
        raise HTTPException(status_code=500, detail="Failed to check project status")
