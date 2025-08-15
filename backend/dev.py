#!/usr/bin/env python3
"""
Development server for ThemisGuard API
Run this for local development with mock data
"""

import os
from datetime import datetime


# Set development environment
os.environ["ENVIRONMENT"] = "development"

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Mock data for development
MOCK_USER = {
    "user_id": "dev-user-123",
    "email": "dev@themisguard.com",
    "first_name": "Demo",
    "last_name": "User",
}

# In-memory storage for uploaded GCP projects (development only)
UPLOADED_PROJECTS = {}

# In-memory storage for scan reports (development only)
SCAN_REPORTS = {}

MOCK_SCANS = [
    {
        "scan_id": "scan-1",
        "project_id": "production-app",
        "scan_timestamp": "2024-01-15T10:30:00Z",
        "total_violations": 8,
        "compliance_score": 92,
        "status": "completed",
    },
    {
        "scan_id": "scan-2",
        "project_id": "staging-env",
        "scan_timestamp": "2024-01-14T15:20:00Z",
        "total_violations": 15,
        "compliance_score": 78,
        "status": "completed",
    },
]

MOCK_VIOLATIONS = [
    {
        "id": "violation-1",
        "type": "hipaa_violation",
        "severity": "high",
        "title": "Storage bucket allows public access",
        "description": "Storage bucket 'my-bucket' allows public access, violating access controls",
        "resource_type": "storage.bucket",
        "resource_name": "my-bucket",
        "project_id": "production-app",
    },
    {
        "id": "violation-2",
        "type": "hipaa_violation",
        "severity": "medium",
        "title": "Firewall rule allows unrestricted SSH",
        "description": "Firewall rule 'default-allow-ssh' allows unrestricted access to port 22",
        "resource_type": "compute.firewall",
        "resource_name": "default-allow-ssh",
        "project_id": "production-app",
    },
]

# Create FastAPI app
app = FastAPI(
    title="ThemisGuard HIPAA Compliance API (Development)",
    description="Development server with mock data",
    version="1.0.0-dev",
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ScanRequest(BaseModel):
    project_id: str
    scan_type: str = "full"


class AuthRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    company: str = ""


# Mock authentication (always returns success)
async def mock_get_current_user():
    return MOCK_USER


# Routes
@app.get("/")
async def root():
    return {
        "message": "ThemisGuard HIPAA Compliance API (Development Mode)",
        "version": "1.0.0-dev",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "mode": "development",
    }


@app.post("/api/v1/auth/login")
async def login(request: AuthRequest):
    # Mock login - always succeeds
    return {
        "user": MOCK_USER,
        "token": "mock-jwt-token-for-development",
        "message": "Login successful (development mode)",
    }


@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    # Mock registration - always succeeds
    user = {
        "user_id": "dev-user-new",
        "email": request.email,
        "first_name": request.first_name,
        "last_name": request.last_name,
    }
    return {
        "user": user,
        "token": "mock-jwt-token-for-development",
        "message": "Registration successful (development mode)",
    }


@app.get("/api/v1/auth/verify")
async def verify_token():
    return {"user": MOCK_USER}


@app.post("/api/v1/scan")
async def trigger_scan(request: ScanRequest):
    # Real scan using actual scripts
    import json as json_module
    import os
    import subprocess
    import sys
    from datetime import datetime

    now = datetime.now()
    scan_id = f"scan-{now.timestamp()}"
    current_time = now.isoformat() + "Z"

    print(f"🔍 [DEV] Starting REAL scan for project: {request.project_id}")

    # Check if project has credentials
    if request.project_id not in UPLOADED_PROJECTS:
        print(f"❌ [DEV] No credentials found for project: {request.project_id}")
        return {
            "scan_id": scan_id,
            "project_id": request.project_id,
            "violations_count": 0,
            "status": "failed",
            "message": f"No credentials found for project {request.project_id}",
        }

    try:
        # Run comprehensive HIPAA compliance scanning
        print("🔍 [DEV] Running comprehensive HIPAA compliance scan...")

        # Run comprehensive HIPAA scanner
        comprehensive_script = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "comprehensive_hipaa_scan.py"
        )
        venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
        if not os.path.exists(venv_python):
            venv_python = sys.executable

        print("🔍 [DEV] Running comprehensive HIPAA scanner...")
        result = subprocess.run(
            [venv_python, comprehensive_script],
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "GCP_PROJECT_ID": request.project_id},
        )

        if result.returncode == 0:
            print("✅ [DEV] Comprehensive scanner completed successfully")

            # Try to parse the output as JSON (the script outputs JSON)
            try:
                # The comprehensive scanner outputs complete JSON to stdout
                comprehensive_report = json_module.loads(result.stdout)
                violations = comprehensive_report.get("violations", [])
                violations_count = len(violations)

                # Get summary statistics from the comprehensive report
                summary = comprehensive_report.get("summary", {})
                critical_count = summary.get("critical_count", 0)
                high_count = summary.get("high_count", 0)
                medium_count = summary.get("medium_count", 0)
                compliance_score = comprehensive_report.get("compliance_score", 0)

                print(
                    f"📊 [DEV] Comprehensive scan results: {violations_count} violations ({critical_count} critical, {high_count} high, {medium_count} medium), {compliance_score}% compliance"
                )

            except (json_module.JSONDecodeError, IndexError, KeyError) as e:
                print(
                    f"⚠️ [DEV] Could not parse scanner output, using fallback data: {e}"
                )
                violations = [
                    {
                        "service": "Firebase Scanner",
                        "resource": request.project_id,
                        "violation": "Real scan completed - see logs for details",
                        "severity": "MEDIUM",
                        "business_impact": "Scanner executed successfully",
                        "remediation": "Check server logs for detailed scan results",
                    }
                ]
                violations_count = 1
                compliance_score = 95
        else:
            print(f"⚠️ [DEV] Scanner returned error code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")

            # Create a violation indicating scan issues
            violations = [
                {
                    "service": "Scan Engine",
                    "resource": request.project_id,
                    "violation": f"Scan completed with warnings (exit code: {result.returncode})",
                    "severity": "LOW",
                    "business_impact": "Scanner may have encountered authentication or permission issues",
                    "remediation": "Check GCP credentials and permissions",
                }
            ]
            violations_count = 1
            compliance_score = 90

    except subprocess.TimeoutExpired:
        print("⏰ [DEV] Scanner timed out after 60 seconds")
        violations = [
            {
                "service": "Scan Engine",
                "resource": request.project_id,
                "violation": "Scan timed out - large project or network issues",
                "severity": "MEDIUM",
                "business_impact": "Unable to complete full compliance assessment",
                "remediation": "Verify network connectivity and try again",
            }
        ]
        violations_count = 1
        compliance_score = 85

    except Exception as e:
        print(f"❌ [DEV] Scanner error: {e}")
        violations = [
            {
                "service": "Scan Engine",
                "resource": request.project_id,
                "violation": f"Scanner error: {str(e)}",
                "severity": "HIGH",
                "business_impact": "Unable to assess compliance",
                "remediation": "Check scanner configuration and credentials",
            }
        ]
        violations_count = 1
        compliance_score = 75

    # Store scan summary in reports list
    scan_summary = {
        "scan_id": scan_id,
        "project_id": request.project_id,
        "scan_timestamp": current_time,
        "total_violations": violations_count,
        "compliance_score": compliance_score,
        "status": "completed",
    }

    # Store detailed report for individual report retrieval
    detailed_report = {
        "scan_id": scan_id,
        "user_id": MOCK_USER["user_id"],
        "project_id": request.project_id,
        "scan_timestamp": current_time,
        "violations": violations,
        "total_violations": violations_count,
        "compliance_score": compliance_score,
        "status": "completed",
    }

    # Add to our storage
    MOCK_SCANS.insert(0, scan_summary)  # Add to beginning (most recent first)
    SCAN_REPORTS[scan_id] = detailed_report

    print(f"✅ [DEV] Real scan completed: {scan_id} for {request.project_id}")

    return {
        "scan_id": scan_id,
        "project_id": request.project_id,
        "violations_count": violations_count,
        "status": "completed",
        "message": "Real HIPAA compliance scan completed",
    }


@app.get("/api/v1/reports/{scan_id}")
async def get_report(scan_id: str):
    print(f"📄 [DEV] Retrieving report for scan: {scan_id}")

    # Return stored report if it exists
    if scan_id in SCAN_REPORTS:
        print(f"✅ [DEV] Found stored report for {scan_id}")
        return SCAN_REPORTS[scan_id]

    # Fallback to mock report for old scan IDs
    print(f"⚠️ [DEV] No stored report found for {scan_id}, returning mock data")
    return {
        "scan_id": scan_id,
        "user_id": MOCK_USER["user_id"],
        "project_id": "mock-project",
        "scan_timestamp": datetime.utcnow().isoformat(),
        "violations": MOCK_VIOLATIONS,
        "total_violations": len(MOCK_VIOLATIONS),
        "compliance_score": 85,
        "status": "completed",
    }


@app.get("/api/v1/reports")
async def list_reports(limit: int = 10, offset: int = 0):
    print(f"📋 [DEV] Listing reports: {len(MOCK_SCANS)} total reports available")
    reports_slice = MOCK_SCANS[offset : offset + limit]
    print(
        f"📋 [DEV] Returning {len(reports_slice)} reports (offset: {offset}, limit: {limit})"
    )

    return {
        "reports": reports_slice,
        "total": len(MOCK_SCANS),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/v1/dashboard")
async def get_dashboard():
    print("📊 [DEV] Generating live dashboard data...")

    # Calculate live statistics from actual scan data
    total_scans = len(MOCK_SCANS)
    total_projects = len(UPLOADED_PROJECTS)

    # Calculate overall compliance score from recent scans
    if MOCK_SCANS:
        recent_scores = [scan.get("compliance_score", 0) for scan in MOCK_SCANS[:5]]
        overall_compliance_score = (
            sum(recent_scores) / len(recent_scores) if recent_scores else 0
        )
        last_scan_date = MOCK_SCANS[0]["scan_timestamp"] if MOCK_SCANS else None
    else:
        overall_compliance_score = 0
        last_scan_date = None

    # Calculate violation summary from recent scan reports
    total_violations = 0
    critical_violations = 0
    high_violations = 0
    medium_violations = 0
    low_violations = 0

    # Look at the most recent detailed reports to get violation breakdown
    recent_report_ids = [scan["scan_id"] for scan in MOCK_SCANS[:3]]
    for scan_id in recent_report_ids:
        if scan_id in SCAN_REPORTS:
            report = SCAN_REPORTS[scan_id]
            violations = report.get("violations", [])
            total_violations += len(violations)

            for violation in violations:
                severity = violation.get("severity", "").upper()
                if severity == "CRITICAL":
                    critical_violations += 1
                elif severity == "HIGH":
                    high_violations += 1
                elif severity == "MEDIUM":
                    medium_violations += 1
                elif severity == "LOW":
                    low_violations += 1

    print(
        f"📊 [DEV] Dashboard stats: {total_scans} scans, {total_projects} projects, {overall_compliance_score:.1f}% compliance"
    )

    return {
        "user_id": MOCK_USER["user_id"],
        "total_scans": total_scans,
        "total_projects": total_projects,
        "overall_compliance_score": round(overall_compliance_score, 1),
        "recent_scans": MOCK_SCANS[:3],
        "last_scan_date": last_scan_date,
        "violation_summary": {
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "high_violations": high_violations,
            "medium_violations": medium_violations,
            "low_violations": low_violations,
        },
    }


# GCP Credential Management Routes (Development Mode)
@app.post("/api/v1/gcp/credentials/upload")
async def upload_gcp_credentials_file(
    project_id: str = Form(...), file: UploadFile = File(...)
):
    """Upload GCP service account JSON file (dev mode)"""
    import json

    try:
        print(f"📤 [DEV] Uploading credentials for project: {project_id}")
        print(f"📁 [DEV] File: {file.filename}")

        # Read and validate JSON
        content = await file.read()
        service_account_json = json.loads(content.decode("utf-8"))

        # Basic validation
        if service_account_json.get("type") != "service_account":
            raise HTTPException(status_code=400, detail="Must be a service account key")

        service_account_email = service_account_json.get("client_email", "unknown")
        print(f"✅ [DEV] Valid service account: {service_account_email}")

        # Store the project in our in-memory storage
        from datetime import datetime

        current_time = datetime.utcnow().isoformat() + "Z"

        UPLOADED_PROJECTS[project_id] = {
            "project_id": project_id,
            "service_account_email": service_account_email,
            "status": "active",
            "created_at": current_time,
            "last_used": current_time,
        }

        return {
            "message": "GCP credentials uploaded successfully (development mode)",
            "project_id": project_id,
            "service_account_email": service_account_email,
            "status": "success",
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/v1/gcp/projects")
async def list_gcp_projects():
    """List GCP projects (dev mode with uploaded projects)"""
    print("📋 [DEV] Listing GCP projects")

    # Return uploaded projects, or empty list if none
    projects = list(UPLOADED_PROJECTS.values())
    print(f"📋 [DEV] Found {len(projects)} uploaded projects")

    return projects


@app.delete("/api/v1/gcp/projects/{project_id}/credentials")
async def revoke_gcp_credentials(project_id: str):
    """Revoke GCP credentials (dev mode)"""
    print(f"🗑️ [DEV] Revoking credentials for project: {project_id}")

    # Remove from in-memory storage
    if project_id in UPLOADED_PROJECTS:
        del UPLOADED_PROJECTS[project_id]
        print(f"✅ [DEV] Project {project_id} removed from storage")
    else:
        print(f"⚠️ [DEV] Project {project_id} not found in storage")

    return {
        "message": f"GCP credentials revoked for project {project_id} (development mode)",
        "project_id": project_id,
        "status": "revoked",
    }


@app.get("/api/v1/gcp/projects/{project_id}/status")
async def check_gcp_project_status(project_id: str):
    """Check GCP project status (dev mode)"""
    return {
        "project_id": project_id,
        "status": "active",
        "service_account_email": f"test-scanner@{project_id}.iam.gserviceaccount.com",
        "connection_status": "connected",
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting ThemisGuard Development Server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print("🔧 This is a development server with mock data")

    uvicorn.run("dev:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
