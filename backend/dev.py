#!/usr/bin/env python3
"""
Development server for ThemisGuard API
Run this for local development with mock data
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Set development environment
os.environ["ENVIRONMENT"] = "development"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Mock data for development
MOCK_USER = {
    "user_id": "dev-user-123",
    "email": "dev@themisguard.com",
    "first_name": "Demo",
    "last_name": "User"
}

MOCK_SCANS = [
    {
        "scan_id": "scan-1",
        "project_id": "production-app", 
        "scan_timestamp": "2024-01-15T10:30:00Z",
        "total_violations": 8,
        "compliance_score": 92,
        "status": "completed"
    },
    {
        "scan_id": "scan-2", 
        "project_id": "staging-env",
        "scan_timestamp": "2024-01-14T15:20:00Z", 
        "total_violations": 15,
        "compliance_score": 78,
        "status": "completed"
    }
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
        "project_id": "production-app"
    },
    {
        "id": "violation-2",
        "type": "hipaa_violation", 
        "severity": "medium",
        "title": "Firewall rule allows unrestricted SSH",
        "description": "Firewall rule 'default-allow-ssh' allows unrestricted access to port 22",
        "resource_type": "compute.firewall",
        "resource_name": "default-allow-ssh", 
        "project_id": "production-app"
    }
]

# Create FastAPI app
app = FastAPI(
    title="ThemisGuard HIPAA Compliance API (Development)",
    description="Development server with mock data",
    version="1.0.0-dev"
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
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "mode": "development"
    }

@app.post("/api/v1/auth/login")
async def login(request: AuthRequest):
    # Mock login - always succeeds
    return {
        "user": MOCK_USER,
        "token": "mock-jwt-token-for-development",
        "message": "Login successful (development mode)"
    }

@app.post("/api/v1/auth/register") 
async def register(request: RegisterRequest):
    # Mock registration - always succeeds
    user = {
        "user_id": "dev-user-new",
        "email": request.email,
        "first_name": request.first_name,
        "last_name": request.last_name
    }
    return {
        "user": user,
        "token": "mock-jwt-token-for-development",
        "message": "Registration successful (development mode)"
    }

@app.get("/api/v1/auth/verify")
async def verify_token():
    return {"user": MOCK_USER}

@app.post("/api/v1/scan")
async def trigger_scan(request: ScanRequest):
    # Mock scan trigger
    scan_id = f"scan-{datetime.now().timestamp()}"
    return {
        "scan_id": scan_id,
        "project_id": request.project_id,
        "violations_count": 5,
        "status": "completed",
        "message": "Mock scan completed (development mode)"
    }

@app.get("/api/v1/reports/{scan_id}")
async def get_report(scan_id: str):
    # Return mock report
    return {
        "scan_id": scan_id,
        "user_id": MOCK_USER["user_id"],
        "project_id": "mock-project",
        "scan_timestamp": datetime.utcnow().isoformat(),
        "violations": MOCK_VIOLATIONS,
        "total_violations": len(MOCK_VIOLATIONS),
        "compliance_score": 85,
        "status": "completed"
    }

@app.get("/api/v1/reports")
async def list_reports(limit: int = 10, offset: int = 0):
    return {
        "reports": MOCK_SCANS[offset:offset+limit],
        "total": len(MOCK_SCANS),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/dashboard")
async def get_dashboard():
    return {
        "user_id": MOCK_USER["user_id"],
        "total_scans": len(MOCK_SCANS),
        "total_projects": 3,
        "overall_compliance_score": 85.5,
        "recent_scans": MOCK_SCANS[:3],
        "last_scan_date": "2024-01-15T10:30:00Z",
        "violation_summary": {
            "total_violations": 23,
            "critical_violations": 2,
            "high_violations": 8,
            "medium_violations": 10,
            "low_violations": 3
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ThemisGuard Development Server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print("🔧 This is a development server with mock data")
    
    uvicorn.run(
        "dev:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )