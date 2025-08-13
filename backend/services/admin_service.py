import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import boto3
import pyotp
from botocore.exceptions import ClientError

from ..core.config import settings
from ..models.admin import (
    AdminAuditLog,
    AdminDashboardData,
    AdminPermission,
    AdminRole,
    AdminSession,
    AdminUser,
    ChurnAnalytics,
    CustomerMetrics,
    RevenueMetrics,
    SecurityMetrics,
    SupportMetrics,
    SystemHealthMetrics,
    UsageMetrics,
)


class AdminService:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.s3 = boto3.client("s3", region_name=settings.AWS_REGION)

        # Admin-specific tables (separate from customer data)
        self.admin_users_table = self.dynamodb.Table("themisguard-admin-users")
        self.admin_sessions_table = self.dynamodb.Table("themisguard-admin-sessions")
        self.admin_audit_table = self.dynamodb.Table("themisguard-admin-audit")
        self.admin_metrics_table = self.dynamodb.Table("themisguard-admin-metrics")

    async def authenticate_admin(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate admin user (step 1 - before 2FA)"""
        try:
            # Get admin user from secure table
            response = self.admin_users_table.get_item(Key={"email": email})

            if "Item" not in response:
                await self.log_admin_action(
                    admin_id="unknown",
                    admin_email=email,
                    action="login_failed",
                    resource_type="authentication",
                    details={"reason": "user_not_found"},
                    ip_address="0.0.0.0",  # Would be passed from request
                    success=False,
                )
                return {"success": False, "error": "Invalid credentials"}

            admin_user = response["Item"]

            # Verify password (in production, use proper password hashing)
            stored_password_hash = admin_user.get("password_hash")
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            if stored_password_hash != password_hash:
                await self.log_admin_action(
                    admin_id=admin_user["admin_id"],
                    admin_email=email,
                    action="login_failed",
                    resource_type="authentication",
                    details={"reason": "invalid_password"},
                    ip_address="0.0.0.0",
                    success=False,
                )
                return {"success": False, "error": "Invalid credentials"}

            # Check if admin is active
            if not admin_user.get("is_active", False):
                return {"success": False, "error": "Account disabled"}

            # Generate temporary token for 2FA
            temp_token = secrets.token_urlsafe(32)

            # Store temp token with expiration (5 minutes)
            self.admin_sessions_table.put_item(
                Item={
                    "session_id": f"temp_{temp_token}",
                    "admin_id": admin_user["admin_id"],
                    "session_type": "temp_2fa",
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat(),
                    "is_active": True,
                }
            )

            return {"success": True, "requires_2fa": True, "temp_token": temp_token}

        except Exception as e:
            print(f"Admin authentication error: {e}")
            return {"success": False, "error": "Authentication failed"}

    async def verify_2fa(
        self, temp_token: str, totp_code: str, ip_address: str, user_agent: str
    ) -> Dict[str, Any]:
        """Verify 2FA and create admin session"""
        try:
            # Get temp session
            temp_session_response = self.admin_sessions_table.get_item(
                Key={"session_id": f"temp_{temp_token}"}
            )

            if "Item" not in temp_session_response:
                return {"success": False, "error": "Invalid or expired token"}

            temp_session = temp_session_response["Item"]
            admin_id = temp_session["admin_id"]

            # Check if temp session is expired
            expires_at = datetime.fromisoformat(temp_session["expires_at"])
            if datetime.now() > expires_at:
                return {"success": False, "error": "Token expired"}

            # Get admin user for 2FA secret
            admin_response = self.admin_users_table.get_item(
                Key={"admin_id": admin_id},
                ProjectionExpression="admin_id, email, two_factor_secret, #name, #role, permissions",
                ExpressionAttributeNames={"#name": "name", "#role": "role"},
            )

            if "Item" not in admin_response:
                return {"success": False, "error": "Admin user not found"}

            admin_user = admin_response["Item"]

            # Verify TOTP code
            totp_secret = admin_user.get("two_factor_secret")
            if not totp_secret:
                return {"success": False, "error": "2FA not configured"}

            totp = pyotp.TOTP(totp_secret)
            if not totp.verify(totp_code, valid_window=1):
                await self.log_admin_action(
                    admin_id=admin_id,
                    admin_email=admin_user["email"],
                    action="2fa_failed",
                    resource_type="authentication",
                    details={"ip_address": ip_address},
                    ip_address=ip_address,
                    success=False,
                )
                return {"success": False, "error": "Invalid 2FA code"}

            # Create admin session
            session_token = secrets.token_urlsafe(64)
            session_id = f"admin_{secrets.token_urlsafe(16)}"

            admin_session = AdminSession(
                session_id=session_id,
                admin_id=admin_id,
                ip_address=ip_address,
                user_agent=user_agent,
                login_time=datetime.now(),
                last_activity=datetime.now(),
                is_active=True,
                two_factor_verified=True,
                session_token=session_token,
            )

            # Store session
            self.admin_sessions_table.put_item(Item=admin_session.dict())

            # Update last login
            self.admin_users_table.update_item(
                Key={"admin_id": admin_id},
                UpdateExpression="SET last_login = :login_time",
                ExpressionAttributeValues={":login_time": datetime.now().isoformat()},
            )

            # Clean up temp session
            self.admin_sessions_table.delete_item(
                Key={"session_id": f"temp_{temp_token}"}
            )

            # Log successful login
            await self.log_admin_action(
                admin_id=admin_id,
                admin_email=admin_user["email"],
                action="login_success",
                resource_type="authentication",
                details={"ip_address": ip_address, "user_agent": user_agent},
                ip_address=ip_address,
                success=True,
            )

            return {
                "success": True,
                "session_token": session_token,
                "admin_user": {
                    "admin_id": admin_id,
                    "email": admin_user["email"],
                    "name": admin_user["name"],
                    "role": admin_user["role"],
                    "permissions": admin_user.get("permissions", []),
                },
            }

        except Exception as e:
            print(f"2FA verification error: {e}")
            return {"success": False, "error": "2FA verification failed"}

    async def validate_admin_session(self, session_token: str) -> Optional[AdminUser]:
        """Validate admin session token"""
        try:
            # Query sessions table for active session
            response = self.admin_sessions_table.scan(
                FilterExpression="session_token = :token AND is_active = :active",
                ExpressionAttributeValues={":token": session_token, ":active": True},
            )

            if not response.get("Items"):
                return None

            session = response["Items"][0]

            # Check session expiration (24 hours)
            login_time = datetime.fromisoformat(session["login_time"])
            if datetime.now() - login_time > timedelta(hours=24):
                # Expire session
                self.admin_sessions_table.update_item(
                    Key={"session_id": session["session_id"]},
                    UpdateExpression="SET is_active = :inactive",
                    ExpressionAttributeValues={":inactive": False},
                )
                return None

            # Update last activity
            self.admin_sessions_table.update_item(
                Key={"session_id": session["session_id"]},
                UpdateExpression="SET last_activity = :activity",
                ExpressionAttributeValues={":activity": datetime.now().isoformat()},
            )

            # Get admin user details
            admin_response = self.admin_users_table.get_item(
                Key={"admin_id": session["admin_id"]}
            )

            if "Item" in admin_response:
                return AdminUser(**admin_response["Item"])

            return None

        except Exception as e:
            print(f"Session validation error: {e}")
            return None

    async def get_admin_dashboard_data(self, admin_id: str) -> AdminDashboardData:
        """Get aggregated dashboard data for admin - NO CUSTOMER PII"""
        try:
            # This would aggregate data from various sources
            # All data is anonymized and aggregated

            # Get cached metrics (updated periodically by background job)
            cached_metrics = await self.get_cached_admin_metrics()

            if cached_metrics:
                return cached_metrics

            # Generate fresh metrics if cache miss
            return await self.generate_admin_metrics()

        except Exception as e:
            print(f"Error getting admin dashboard data: {e}")
            # Return default/empty metrics
            return self.get_default_admin_metrics()

    async def get_cached_admin_metrics(self) -> Optional[AdminDashboardData]:
        """Get cached admin metrics from DynamoDB"""
        try:
            response = self.admin_metrics_table.get_item(
                Key={"metric_type": "dashboard_summary"}
            )

            if "Item" in response:
                # Check if data is fresh (updated within last hour)
                last_updated = datetime.fromisoformat(response["Item"]["last_updated"])
                if datetime.now() - last_updated < timedelta(hours=1):
                    return AdminDashboardData(**response["Item"]["data"])

            return None

        except Exception as e:
            print(f"Error getting cached metrics: {e}")
            return None

    async def generate_admin_metrics(self) -> AdminDashboardData:
        """Generate fresh admin metrics (this would query actual data sources)"""
        # In production, this would aggregate from:
        # - Customer database (count only, no PII)
        # - Billing system
        # - Usage analytics
        # - System monitoring

        # For demo, return realistic sample data
        # Comprehensive churn analytics
        churn_analytics = ChurnAnalytics(
            # Current churn metrics
            monthly_churn_rate=3.2,
            quarterly_churn_rate=9.1,
            annual_churn_rate=32.4,
            gross_churn_rate=3.8,
            net_churn_rate=1.9,  # Lower due to expansion revenue
            # Churn trends over 6 months
            churn_trend_6_months=[
                {
                    "month": "Jan",
                    "churn_rate": 4.1,
                    "churned_customers": 18,
                    "expansion_revenue": 12400,
                },
                {
                    "month": "Feb",
                    "churn_rate": 3.8,
                    "churned_customers": 16,
                    "expansion_revenue": 15200,
                },
                {
                    "month": "Mar",
                    "churn_rate": 3.5,
                    "churned_customers": 15,
                    "expansion_revenue": 18900,
                },
                {
                    "month": "Apr",
                    "churn_rate": 3.2,
                    "churned_customers": 14,
                    "expansion_revenue": 21300,
                },
                {
                    "month": "May",
                    "churn_rate": 2.9,
                    "churned_customers": 13,
                    "expansion_revenue": 23800,
                },
                {
                    "month": "Jun",
                    "churn_rate": 3.2,
                    "churned_customers": 15,
                    "expansion_revenue": 25100,
                },
            ],
            # Churn by customer segments
            churn_by_plan={
                "starter": 5.8,  # Higher churn for lower-tier plans
                "professional": 2.4,  # Mid-tier plans more stable
                "enterprise": 0.9,  # Enterprise customers very sticky
            },
            churn_by_industry={
                "healthcare": 2.1,  # Lower churn in healthcare (compliance critical)
                "finance": 2.8,  # Moderate churn in finance
                "technology": 4.2,  # Higher churn in tech (more options)
                "other": 4.8,
            },
            churn_by_customer_age={
                "0-3_months": 15.2,  # High early churn
                "3-6_months": 8.7,  # Onboarding complete, more stable
                "6-12_months": 4.1,  # Getting value, lower churn
                "12-24_months": 2.3,  # Established customers
                "24+_months": 1.2,  # Long-term loyal customers
            },
            # Churn reasons and patterns
            churn_reasons=[
                {"reason": "Price/Budget Constraints", "percentage": 28.3, "count": 17},
                {"reason": "Lack of Product Adoption", "percentage": 22.1, "count": 13},
                {"reason": "Competitive Solution", "percentage": 18.5, "count": 11},
                {"reason": "Internal Tool Development", "percentage": 12.4, "count": 7},
                {"reason": "Business Change/Closure", "percentage": 8.9, "count": 5},
                {"reason": "Technical Issues", "percentage": 6.2, "count": 4},
                {"reason": "Poor Support Experience", "percentage": 3.6, "count": 2},
            ],
            voluntary_vs_involuntary={
                "voluntary": 78.5,  # Customer chose to leave
                "involuntary": 21.5,  # Payment failures, etc.
            },
            # Early warning indicators
            at_risk_customers={
                "high_risk": 45,  # >70% churn probability
                "medium_risk": 123,  # 40-70% churn probability
                "low_risk": 234,  # 20-40% churn probability
            },
            engagement_decline_alerts=28,  # Customers with declining usage
            payment_failure_alerts=12,  # Failed payment attempts
            support_escalation_alerts=8,  # Escalated support tickets
            # Cohort retention analysis
            cohort_retention_rates=[
                {
                    "cohort": "Jan_2023",
                    "month_1": 95.2,
                    "month_3": 87.1,
                    "month_6": 78.9,
                    "month_12": 68.2,
                },
                {
                    "cohort": "Feb_2023",
                    "month_1": 96.1,
                    "month_3": 88.3,
                    "month_6": 81.2,
                    "month_12": 72.1,
                },
                {
                    "cohort": "Mar_2023",
                    "month_1": 94.8,
                    "month_3": 86.9,
                    "month_6": 79.4,
                    "month_12": 70.8,
                },
                {
                    "cohort": "Apr_2023",
                    "month_1": 95.7,
                    "month_3": 89.1,
                    "month_6": 82.3,
                    "month_12": 74.2,
                },
                {
                    "cohort": "May_2023",
                    "month_1": 96.3,
                    "month_3": 90.2,
                    "month_6": 84.1,
                    "month_12": 76.5,
                },
                {
                    "cohort": "Jun_2023",
                    "month_1": 97.1,
                    "month_3": 91.4,
                    "month_6": 85.7,
                    "month_12": 78.3,
                },
            ],
            ltv_by_cohort={
                "Q1_2023": 2847.50,
                "Q2_2023": 3124.80,
                "Q3_2023": 3356.20,
                "Q4_2023": 3598.90,
            },
            # Predictive analytics
            predicted_churn_next_30_days=23,
            predicted_churn_next_90_days=67,
            churn_risk_score_distribution={
                "0-20": 832,  # Very low risk
                "20-40": 234,  # Low risk
                "40-60": 123,  # Medium risk
                "60-80": 45,  # High risk
                "80-100": 13,  # Very high risk
            },
            # Financial impact of churn
            lost_revenue_this_month=47800.00,
            potential_lost_revenue_next_quarter=142400.00,
            saved_revenue_from_retention_efforts=89300.00,
        )

        customer_metrics = CustomerMetrics(
            total_customers=1247,
            active_customers=1103,
            new_customers_this_month=89,
            churn_rate=3.2,
            customers_by_plan={"starter": 456, "professional": 623, "enterprise": 168},
            customers_by_industry={
                "healthcare": 489,
                "finance": 312,
                "technology": 287,
                "other": 159,
            },
            customer_retention_rate=96.8,
            average_customer_lifetime=28.5,
            # Enhanced customer analytics
            customer_acquisition_cost=245.80,
            customer_lifetime_value=2847.50,
            monthly_active_users=1089,
            weekly_active_users=892,
            expansion_revenue_rate=18.7,
            contraction_revenue_rate=4.3,
            # Customer engagement metrics
            average_login_frequency=12.4,  # Logins per month
            feature_adoption_rates={
                "hipaa_scanning": 89.2,
                "soc2_reports": 67.1,
                "environment_separation": 54.3,
                "custom_policies": 43.8,
                "api_integration": 31.2,
            },
            time_to_first_value=3.2,  # Days to first successful scan
            product_qualified_leads=156,
            # Customer health scores
            healthy_customers=834,  # 75% of active customers
            at_risk_customers=189,  # 17% need attention
            critical_customers=80,  # 8% in critical state
        )

        revenue_metrics = RevenueMetrics(
            monthly_recurring_revenue=187420.00,
            annual_recurring_revenue=2249040.00,
            revenue_growth_rate=23.4,
            average_revenue_per_user=169.89,
            monthly_revenue=[
                {"month": "Jan", "revenue": 156890},
                {"month": "Feb", "revenue": 163420},
                {"month": "Mar", "revenue": 171230},
                {"month": "Apr", "revenue": 178910},
                {"month": "May", "revenue": 184560},
                {"month": "Jun", "revenue": 187420},
            ],
            revenue_by_plan={
                "starter": 22800,
                "professional": 124600,
                "enterprise": 40320,
            },
            revenue_by_region={
                "north_america": 112452,
                "europe": 48931,
                "asia_pacific": 26037,
            },
            total_revenue=2249040.00,
            projected_revenue=2750000.00,
        )

        usage_metrics = UsageMetrics(
            total_scans=45789,
            scans_this_month=8934,
            average_scans_per_customer=36.7,
            total_violations_found=123456,
            average_compliance_score=84.3,
            popular_features=[
                {"feature": "HIPAA Compliance Scanning", "usage": 89},
                {"feature": "SOC 2 Reports", "usage": 67},
                {"feature": "Environment Separation", "usage": 54},
                {"feature": "Custom Policies", "usage": 43},
            ],
            scan_frequency_trends=[
                {"date": "2024-01-01", "scans": 1200},
                {"date": "2024-01-02", "scans": 1350},
                {"date": "2024-01-03", "scans": 1180},
            ],
            resource_utilization={"cpu": 67.2, "memory": 74.8, "storage": 45.3},
        )

        system_health = SystemHealthMetrics(
            api_uptime=99.97,
            average_response_time=245,
            error_rate=0.12,
            active_scans=23,
            queued_scans=7,
            system_alerts=2,
            storage_usage={"used_gb": 2340, "total_gb": 5000},
            compute_usage={"cpu_percent": 67.2, "memory_percent": 74.8},
            database_performance={"query_time_avg": 45, "connections": 234},
        )

        support_metrics = SupportMetrics(
            open_tickets=34,
            average_resolution_time=4.2,
            customer_satisfaction_score=4.6,
            escalated_tickets=3,
            tickets_by_category={
                "technical": 18,
                "billing": 8,
                "feature_request": 5,
                "other": 3,
            },
            support_response_time=2.1,
        )

        security_metrics = SecurityMetrics(
            failed_login_attempts=23,
            suspicious_activities=2,
            security_alerts=1,
            compliance_violations=0,
            data_breaches=0,
            vulnerability_score=92.5,
            security_incidents=[],
        )

        dashboard_data = AdminDashboardData(
            customer_metrics=customer_metrics,
            churn_analytics=churn_analytics,
            revenue_metrics=revenue_metrics,
            usage_metrics=usage_metrics,
            system_health=system_health,
            support_metrics=support_metrics,
            security_metrics=security_metrics,
        )

        # Cache the metrics
        await self.cache_admin_metrics(dashboard_data)

        return dashboard_data

    async def cache_admin_metrics(self, data: AdminDashboardData):
        """Cache admin metrics in DynamoDB"""
        try:
            self.admin_metrics_table.put_item(
                Item={
                    "metric_type": "dashboard_summary",
                    "data": data.dict(),
                    "last_updated": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(hours=2)).isoformat(),
                }
            )
        except Exception as e:
            print(f"Error caching metrics: {e}")

    def get_default_admin_metrics(self) -> AdminDashboardData:
        """Return default metrics in case of errors"""
        return AdminDashboardData(
            customer_metrics=CustomerMetrics(
                total_customers=0,
                active_customers=0,
                new_customers_this_month=0,
                churn_rate=0.0,
                customers_by_plan={},
                customers_by_industry={},
                customer_retention_rate=0.0,
                average_customer_lifetime=0.0,
                customer_acquisition_cost=0.0,
                customer_lifetime_value=0.0,
                monthly_active_users=0,
                weekly_active_users=0,
                expansion_revenue_rate=0.0,
                contraction_revenue_rate=0.0,
                average_login_frequency=0.0,
                feature_adoption_rates={},
                time_to_first_value=0.0,
                product_qualified_leads=0,
                healthy_customers=0,
                at_risk_customers=0,
                critical_customers=0,
            ),
            churn_analytics=ChurnAnalytics(
                monthly_churn_rate=0.0,
                quarterly_churn_rate=0.0,
                annual_churn_rate=0.0,
                gross_churn_rate=0.0,
                net_churn_rate=0.0,
                churn_trend_6_months=[],
                churn_by_plan={},
                churn_by_industry={},
                churn_by_customer_age={},
                churn_reasons=[],
                voluntary_vs_involuntary={},
                at_risk_customers={},
                engagement_decline_alerts=0,
                payment_failure_alerts=0,
                support_escalation_alerts=0,
                cohort_retention_rates=[],
                ltv_by_cohort={},
                predicted_churn_next_30_days=0,
                predicted_churn_next_90_days=0,
                churn_risk_score_distribution={},
                lost_revenue_this_month=0.0,
                potential_lost_revenue_next_quarter=0.0,
                saved_revenue_from_retention_efforts=0.0,
            ),
            revenue_metrics=RevenueMetrics(
                monthly_recurring_revenue=0.0,
                annual_recurring_revenue=0.0,
                revenue_growth_rate=0.0,
                average_revenue_per_user=0.0,
                monthly_revenue=[],
                revenue_by_plan={},
                revenue_by_region={},
                total_revenue=0.0,
                projected_revenue=0.0,
            ),
            usage_metrics=UsageMetrics(
                total_scans=0,
                scans_this_month=0,
                average_scans_per_customer=0.0,
                total_violations_found=0,
                average_compliance_score=0.0,
                popular_features=[],
                scan_frequency_trends=[],
                resource_utilization={},
            ),
            system_health=SystemHealthMetrics(
                api_uptime=0.0,
                average_response_time=0,
                error_rate=0.0,
                active_scans=0,
                queued_scans=0,
                system_alerts=0,
                storage_usage={},
                compute_usage={},
                database_performance={},
            ),
            support_metrics=SupportMetrics(
                open_tickets=0,
                average_resolution_time=0.0,
                customer_satisfaction_score=0.0,
                escalated_tickets=0,
                tickets_by_category={},
                support_response_time=0.0,
            ),
            security_metrics=SecurityMetrics(
                failed_login_attempts=0,
                suspicious_activities=0,
                security_alerts=0,
                compliance_violations=0,
                data_breaches=0,
                vulnerability_score=0.0,
                security_incidents=[],
            ),
        )

    async def log_admin_action(
        self,
        admin_id: str,
        admin_email: str,
        action: str,
        resource_type: str,
        details: Dict[str, Any],
        ip_address: str,
        success: bool = True,
        resource_id: Optional[str] = None,
        user_agent: str = "",
    ):
        """Log admin actions for audit trail"""
        try:
            audit_log = AdminAuditLog(
                log_id=f"audit_{secrets.token_urlsafe(16)}",
                admin_id=admin_id,
                admin_email=admin_email,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
            )

            self.admin_audit_table.put_item(Item=audit_log.dict())

        except Exception as e:
            print(f"Error logging admin action: {e}")

    async def logout_admin(self, session_token: str, admin_id: str):
        """Logout admin and invalidate session"""
        try:
            # Find and deactivate session
            response = self.admin_sessions_table.scan(
                FilterExpression="session_token = :token",
                ExpressionAttributeValues={":token": session_token},
            )

            if response.get("Items"):
                session = response["Items"][0]
                self.admin_sessions_table.update_item(
                    Key={"session_id": session["session_id"]},
                    UpdateExpression="SET is_active = :inactive",
                    ExpressionAttributeValues={":inactive": False},
                )

            # Log logout
            await self.log_admin_action(
                admin_id=admin_id,
                admin_email="",  # Would get from session
                action="logout",
                resource_type="authentication",
                details={},
                ip_address="0.0.0.0",
                success=True,
            )

        except Exception as e:
            print(f"Error logging out admin: {e}")

    async def get_admin_audit_logs(
        self, admin_id: str, limit: int = 50
    ) -> List[AdminAuditLog]:
        """Get audit logs for admin actions"""
        try:
            response = self.admin_audit_table.query(
                IndexName="admin-id-index",
                KeyConditionExpression="admin_id = :admin_id",
                ExpressionAttributeValues={":admin_id": admin_id},
                Limit=limit,
                ScanIndexForward=False,  # Get newest first
            )

            return [AdminAuditLog(**item) for item in response.get("Items", [])]

        except Exception as e:
            print(f"Error getting audit logs: {e}")
            return []
