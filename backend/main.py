from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import os
import json
from datetime import datetime
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError

from .core.config import settings
from .core.auth import verify_token, get_current_user
from .routes.auth import router as auth_router
from .routes.gcp import router as gcp_router
from .models.compliance import ComplianceReport, ViolationSummary
from .models.admin import AdminDashboardData
from .models.subscription import (
    CustomerSubscription, SubscriptionChangeRequest, PlanTier, BillingInterval
)
from .services.compliance_service import ComplianceService
from .services.gcp_service import GCPAssetService
from .services.admin_service import AdminService
from .services.stripe_service import StripeService

app = FastAPI(
    title="ThemisGuard HIPAA Compliance API",
    description="Serverless HIPAA compliance monitoring for GCP infrastructure",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(gcp_router, prefix="/api/v1/gcp", tags=["gcp"])

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Initialize services
compliance_service = ComplianceService()
gcp_service = GCPAssetService()
admin_service = AdminService()
stripe_service = StripeService()

@app.get("/")
async def root():
    return {"message": "ThemisGuard HIPAA Compliance API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/scan")
async def trigger_compliance_scan(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Trigger a new compliance scan for a GCP project"""
    try:
        # Check usage limits before running scan
        limits_check = await stripe_service.check_usage_limits(current_user["user_id"])
        if not limits_check.get("within_limits", True):
            raise HTTPException(
                status_code=429, 
                detail=f"Usage limit exceeded: {limits_check.get('reason', 'Unknown limit exceeded')}"
            )
        
        # Get GCP assets
        assets = await gcp_service.get_project_assets(project_id)
        
        # Run compliance analysis
        violations = await compliance_service.analyze_violations(assets)
        
        # Store results (includes usage tracking)
        scan_id = await compliance_service.store_scan_results(
            user_id=current_user["user_id"],
            project_id=project_id,
            violations=violations
        )
        
        return {
            "scan_id": scan_id,
            "project_id": project_id,
            "violations_count": len(violations),
            "status": "completed"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/reports/{scan_id}")
async def get_compliance_report(
    scan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get compliance report for a specific scan"""
    try:
        report = await compliance_service.get_scan_report(scan_id, current_user["user_id"])
        return report
    except Exception as e:
        raise HTTPException(status_code=404, detail="Report not found")

@app.get("/api/v1/reports")
async def list_reports(
    current_user: dict = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    """List all compliance reports for the current user"""
    try:
        reports = await compliance_service.list_user_reports(
            current_user["user_id"], limit, offset
        )
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard")
async def get_dashboard_data(
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard summary data"""
    try:
        dashboard_data = await compliance_service.get_dashboard_summary(current_user["user_id"])
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin-only endpoints with enhanced security
async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify admin authentication token"""
    token = credentials.credentials
    admin_user = await admin_service.validate_admin_session(token)
    if not admin_user:
        raise HTTPException(status_code=401, detail="Invalid admin session")
    return admin_user

@app.post("/api/admin/v1/login")
async def admin_login(email: str, password: str):
    """Admin login - step 1 (before 2FA)"""
    try:
        result = await admin_service.authenticate_admin(email, password)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.post("/api/admin/v1/verify-2fa")
async def admin_verify_2fa(
    temp_token: str, 
    totp_code: str,
    request_info: dict = {}  # Would include IP, user agent from request
):
    """Admin 2FA verification - step 2"""
    try:
        ip_address = request_info.get("ip_address", "0.0.0.0")
        user_agent = request_info.get("user_agent", "")
        
        result = await admin_service.verify_2fa(temp_token, totp_code, ip_address, user_agent)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="2FA verification failed")

@app.get("/api/admin/v1/dashboard")
async def get_admin_dashboard(
    admin_user = Depends(verify_admin_token)
):
    """Get admin dashboard data - aggregated metrics only, NO customer PII"""
    try:
        if not admin_user or "view_analytics" not in admin_user.permissions:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        dashboard_data = await admin_service.get_admin_dashboard_data(admin_user.admin_id)
        
        # Log admin access
        await admin_service.log_admin_action(
            admin_id=admin_user.admin_id,
            admin_email=admin_user.email,
            action="view_dashboard",
            resource_type="admin_dashboard",
            details={"timestamp": datetime.utcnow().isoformat()},
            ip_address="0.0.0.0",  # Would get from request
            success=True
        )
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/v1/logout")
async def admin_logout(
    admin_user = Depends(verify_admin_token),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Admin logout"""
    try:
        session_token = credentials.credentials
        await admin_service.logout_admin(session_token, admin_user.admin_id)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Logout failed")

@app.get("/api/admin/v1/audit-logs")
async def get_admin_audit_logs(
    admin_user = Depends(verify_admin_token),
    limit: int = 50
):
    """Get admin audit logs"""
    try:
        if not admin_user or "view_audit_logs" not in admin_user.permissions:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        logs = await admin_service.get_admin_audit_logs(admin_user.admin_id, limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stripe/Billing endpoints
@app.get("/api/v1/billing/plans")
async def get_pricing_plans():
    """Get available pricing plans"""
    try:
        plans = stripe_service.get_available_plans()
        return {"plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/billing/create-customer")
async def create_stripe_customer(
    current_user: dict = Depends(get_current_user)
):
    """Create a Stripe customer for the authenticated user"""
    try:
        user_profile = current_user.get("profile", {})
        stripe_customer_id = await stripe_service.create_customer(
            user_id=current_user["user_id"],
            email=current_user["email"],
            name=user_profile.get("name", current_user["email"]),
            company=user_profile.get("company")
        )
        return {"stripe_customer_id": stripe_customer_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/billing/subscribe")
async def create_subscription(
    plan_tier: PlanTier,
    billing_interval: BillingInterval,
    trial_days: int = 14,
    current_user: dict = Depends(get_current_user)
):
    """Create a new subscription for the user"""
    try:
        # First ensure user has a Stripe customer ID
        user_profile = current_user.get("profile", {})
        stripe_customer_id = await stripe_service.create_customer(
            user_id=current_user["user_id"],
            email=current_user["email"],
            name=user_profile.get("name", current_user["email"]),
            company=user_profile.get("company")
        )
        
        subscription = await stripe_service.create_subscription(
            user_id=current_user["user_id"],
            stripe_customer_id=stripe_customer_id,
            plan_tier=plan_tier,
            billing_interval=billing_interval,
            trial_days=trial_days
        )
        
        return subscription
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")

@app.get("/api/v1/billing/subscription")
async def get_user_subscription(
    current_user: dict = Depends(get_current_user)
):
    """Get current user's subscription"""
    try:
        subscription = await stripe_service.get_customer_subscription(current_user["user_id"])
        if not subscription:
            return {"subscription": None}
        return {"subscription": subscription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/billing/change-subscription")
async def change_subscription(
    request: SubscriptionChangeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change user's subscription plan"""
    try:
        # Ensure the request is for the current user
        if request.customer_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        subscription = await stripe_service.change_subscription(request)
        return subscription
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/billing/cancel-subscription")
async def cancel_subscription(
    cancel_immediately: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Cancel user's subscription"""
    try:
        subscription = await stripe_service.cancel_subscription(
            current_user["user_id"], 
            cancel_immediately
        )
        return subscription
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/billing/usage")
async def get_billing_usage(
    month_year: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get user's usage for billing"""
    try:
        usage = await stripe_service.get_monthly_usage(current_user["user_id"], month_year)
        limits_check = await stripe_service.check_usage_limits(current_user["user_id"])
        
        return {
            "usage": usage,
            "limits_check": limits_check
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/billing/portal")
async def create_billing_portal(
    return_url: str,
    current_user: dict = Depends(get_current_user)
):
    """Create Stripe customer portal session"""
    try:
        portal_url = await stripe_service.create_billing_portal_session(
            current_user["user_id"],
            return_url
        )
        return {"portal_url": portal_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/billing/record-usage")
async def record_usage(
    scans_count: int,
    projects_scanned: int,
    api_calls: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Record usage for billing (internal endpoint)"""
    try:
        await stripe_service.record_usage(
            current_user["user_id"],
            scans_count,
            projects_scanned,
            api_calls
        )
        return {"message": "Usage recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: dict):
    """Handle Stripe webhooks"""
    try:
        # In a real implementation, you'd extract the payload and signature from the raw request
        payload = json.dumps(request)
        sig_header = "mock_signature"  # This would come from request headers
        
        success = await stripe_service.handle_webhook(payload, sig_header)
        
        if success:
            return {"received": True}
        else:
            raise HTTPException(status_code=400, detail="Webhook processing failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Lambda handler for AWS deployment
handler = Mangum(app)