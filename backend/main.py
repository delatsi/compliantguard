from fastapi import FastAPI, HTTPException, Depends, Security, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import os
import json
import sys
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
    print("🏠 Root endpoint accessed")
    print(f"🌍 Environment: {settings.ENVIRONMENT}")
    print(f"📍 Region: {settings.AWS_REGION}")
    return {"message": "ThemisGuard HIPAA Compliance API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    print("❤️ Health check endpoint accessed")
    print(f"🕐 Timestamp: {datetime.utcnow().isoformat()}")
    
    # Test AWS connectivity
    health_details = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "region": settings.AWS_REGION,
        "services": {}
    }
    
    try:
        # Test DynamoDB
        print("🗄️ Testing DynamoDB connectivity...")
        dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        test_table = dynamodb.Table(settings.DYNAMODB_TABLE_NAME)
        test_table.table_status  # This will raise exception if table doesn't exist
        health_details["services"]["dynamodb"] = "connected"
        print(f"✅ DynamoDB table accessible: {settings.DYNAMODB_TABLE_NAME}")
    except Exception as e:
        print(f"❌ DynamoDB error: {str(e)}")
        health_details["services"]["dynamodb"] = f"error: {str(e)}"
    
    try:
        # Test S3
        print("🗂️ Testing S3 connectivity...")
        s3 = boto3.client('s3', region_name=settings.AWS_REGION)
        s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        health_details["services"]["s3"] = "connected"
        print(f"✅ S3 bucket accessible: {settings.S3_BUCKET_NAME}")
    except Exception as e:
        print(f"❌ S3 error: {str(e)}")
        health_details["services"]["s3"] = f"error: {str(e)}"
    
    return health_details

@app.get("/debug")
async def debug_info():
    """Debug endpoint to show environment and configuration"""
    print("🔍 Debug endpoint accessed")
    
    debug_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": {
            "ENVIRONMENT": settings.ENVIRONMENT,
            "AWS_REGION": settings.AWS_REGION,
            "DYNAMODB_TABLE_NAME": settings.DYNAMODB_TABLE_NAME,
            "S3_BUCKET_NAME": settings.S3_BUCKET_NAME,
        },
        "aws_connectivity": {},
        "tables": {},
        "versions": {
            "python": sys.version,
            "boto3": boto3.__version__
        }
    }
    
    # Test each AWS service
    try:
        import sys
        print("🐍 Python version:", sys.version)
        print("📦 Boto3 version:", boto3.__version__)
        
        # Test DynamoDB tables
        dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        
        tables_to_check = [
            settings.DYNAMODB_TABLE_NAME,
            settings.DYNAMODB_TABLE_NAME.replace('-scans', '-users'),
            settings.DYNAMODB_TABLE_NAME.replace('-scans', '-gcp-credentials')
        ]
        
        for table_name in tables_to_check:
            try:
                table = dynamodb.Table(table_name)
                status = table.table_status
                debug_info["tables"][table_name] = {"status": status, "accessible": True}
                print(f"✅ Table {table_name}: {status}")
            except Exception as e:
                debug_info["tables"][table_name] = {"status": "error", "error": str(e), "accessible": False}
                print(f"❌ Table {table_name}: {str(e)}")
        
        debug_info["aws_connectivity"]["dynamodb"] = "ok"
        
    except Exception as e:
        debug_info["aws_connectivity"]["dynamodb"] = f"error: {str(e)}"
        print(f"❌ DynamoDB connectivity error: {str(e)}")
    
    return debug_info


@app.post("/api/v1/scan")
async def trigger_compliance_scan(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Trigger a new compliance scan for a GCP project"""
    print(f"🔍 Compliance scan request initiated")
    print(f"👤 User: {current_user.get('user_id')}")
    print(f"🎯 Project ID: {project_id}")
    print(f"🕰️ Timestamp: {datetime.utcnow().isoformat()}")
    
    try:
        # Check usage limits before running scan
        print(f"📈 Checking usage limits...")
        limits_check = await stripe_service.check_usage_limits(current_user["user_id"])
        print(f"📊 Limits check result: {limits_check}")
        
        if not limits_check.get("within_limits", True):
            reason = limits_check.get('reason', 'Unknown limit exceeded')
            print(f"❌ Usage limit exceeded: {reason}")
            raise HTTPException(
                status_code=429, 
                detail=f"Usage limit exceeded: {reason}"
            )
        
        print(f"✅ Usage limits check passed")
        
        # Get GCP assets
        print(f"🌐 Fetching GCP assets for project {project_id}...")
        assets = await gcp_service.get_project_assets(project_id)
        print(f"📊 Retrieved {len(assets) if assets else 0} assets")
        
        if assets:
            asset_types = {}
            for asset in assets:
                asset_type = asset.get('assetType', 'unknown')
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
            print(f"📊 Asset types: {asset_types}")
        
        # Run compliance analysis
        print(f"🔍 Running compliance analysis...")
        violations = await compliance_service.analyze_violations(assets)
        print(f"⚠️ Found {len(violations) if violations else 0} violations")
        
        if violations:
            # Group violations by severity for debugging
            severity_counts = {}
            for violation in violations:
                severity = violation.get('severity', 'unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            print(f"📊 Violations by severity: {severity_counts}")
        
        # Store results (includes usage tracking)
        print(f"💾 Storing scan results...")
        scan_id = await compliance_service.store_scan_results(
            user_id=current_user["user_id"],
            project_id=project_id,
            violations=violations
        )
        print(f"✅ Scan results stored with ID: {scan_id}")
        
        response_data = {
            "scan_id": scan_id,
            "project_id": project_id,
            "violations_count": len(violations) if violations else 0,
            "status": "completed"
        }
        
        print(f"🎉 Compliance scan completed successfully")
        print(f"📊 Final response: {response_data}")
        
        return response_data
    
    except HTTPException as http_ex:
        print(f"❌ HTTP Exception in compliance scan: {http_ex.detail}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error in compliance scan: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/reports/{scan_id}")
async def get_compliance_report(
    scan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get compliance report for a specific scan"""
    print(f"📄 Compliance report request")
    print(f"👤 User: {current_user.get('user_id')}")
    print(f"🆔 Scan ID: {scan_id}")
    
    try:
        print(f"🔍 Fetching scan report via service...")
        report = await compliance_service.get_scan_report(scan_id, current_user["user_id"])
        
        if report:
            print(f"✅ Report found")
            print(f"📊 Report keys: {list(report.keys()) if isinstance(report, dict) else 'Not a dict'}")
            
            # Log some summary info without sensitive details
            if isinstance(report, dict):
                if 'violations' in report:
                    violations_count = len(report['violations']) if report['violations'] else 0
                    print(f"⚠️ Violations in report: {violations_count}")
                if 'project_id' in report:
                    print(f"🎯 Report project: {report['project_id']}")
                if 'scan_timestamp' in report:
                    print(f"🕰️ Scan timestamp: {report['scan_timestamp']}")
        else:
            print(f"❌ No report found for scan ID: {scan_id}")
        
        print(f"👤 Returning compliance report")
        return report
        
    except Exception as e:
        print(f"❌ Error fetching compliance report: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
        raise HTTPException(status_code=404, detail="Report not found")

@app.get("/api/v1/reports")
async def list_reports(
    current_user: dict = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    """List all compliance reports for the current user"""
    print(f"📋 List reports request")
    print(f"👤 User: {current_user.get('user_id')}")
    print(f"📊 Limit: {limit}, Offset: {offset}")
    
    try:
        print(f"🔍 Fetching user reports via service...")
        reports = await compliance_service.list_user_reports(
            current_user["user_id"], limit, offset
        )
        
        print(f"✅ Found {len(reports) if reports else 0} reports")
        
        if reports and len(reports) > 0:
            print(f"📊 First report keys: {list(reports[0].keys()) if isinstance(reports[0], dict) else 'Not a dict'}")
            # Log summary without sensitive details
            for i, report in enumerate(reports[:3]):  # Show first 3
                if isinstance(report, dict):
                    project_id = report.get('project_id', 'unknown')
                    scan_id = report.get('scan_id', 'unknown')
                    violations_count = len(report.get('violations', [])) if report.get('violations') else 0
                    print(f"📊 Report {i+1}: {project_id} (scan: {scan_id[:8]}...) - {violations_count} violations")
        
        print(f"👤 Returning {len(reports) if reports else 0} reports")
        return reports
        
    except Exception as e:
        print(f"❌ Error listing reports: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard")
async def get_dashboard_data(
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard summary data"""
    print(f"📊 Dashboard data request")
    print(f"👤 User: {current_user.get('user_id')}")
    
    try:
        print(f"🔍 Fetching dashboard summary via service...")
        dashboard_data = await compliance_service.get_dashboard_summary(current_user["user_id"])
        
        if dashboard_data:
            print(f"✅ Dashboard data retrieved")
            print(f"📊 Dashboard keys: {list(dashboard_data.keys()) if isinstance(dashboard_data, dict) else 'Not a dict'}")
            
            # Log summary info without sensitive details
            if isinstance(dashboard_data, dict):
                total_scans = dashboard_data.get('total_scans', 0)
                total_violations = dashboard_data.get('total_violations', 0)
                active_projects = dashboard_data.get('active_projects', 0)
                print(f"📊 Summary: {total_scans} scans, {total_violations} violations, {active_projects} projects")
        else:
            print(f"⚠️ No dashboard data returned")
        
        print(f"👤 Returning dashboard data")
        return dashboard_data
        
    except Exception as e:
        print(f"❌ Error fetching dashboard data: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
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
    print(f"🔑 Admin login attempt")
    print(f"📧 Admin email: {email}")
    print(f"🔐 Has password: {bool(password)}")
    
    try:
        print(f"🔍 Authenticating admin via service...")
        result = await admin_service.authenticate_admin(email, password)
        
        print(f"✅ Admin authentication step 1 completed")
        print(f"📊 Auth result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        return result
    except Exception as e:
        print(f"❌ Admin authentication failed: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
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
    print(f"💳 Pricing plans request")
    
    try:
        print(f"🔍 Fetching available plans via Stripe service...")
        plans = stripe_service.get_available_plans()
        
        print(f"✅ Found {len(plans) if plans else 0} pricing plans")
        if plans:
            for plan in plans:
                if isinstance(plan, dict):
                    plan_name = plan.get('name', 'unknown')
                    plan_price = plan.get('price', 'unknown')
                    print(f"📊 Plan: {plan_name} - ${plan_price}")
        
        response_data = {"plans": plans}
        print(f"👤 Returning {len(plans) if plans else 0} plans")
        return response_data
        
    except Exception as e:
        print(f"❌ Error fetching pricing plans: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
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