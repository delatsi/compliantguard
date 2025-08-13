from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    VIEWER = "viewer"


class AdminPermission(str, Enum):
    VIEW_CUSTOMERS = "view_customers"
    VIEW_REVENUE = "view_revenue"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_SUBSCRIPTIONS = "manage_subscriptions"
    VIEW_SYSTEM_HEALTH = "view_system_health"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOGS = "view_audit_logs"


class AdminUser(BaseModel):
    admin_id: str
    email: str
    name: str
    role: AdminRole
    permissions: List[AdminPermission]
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 2FA Settings
    two_factor_enabled: bool = True
    two_factor_secret: Optional[str] = None  # Encrypted TOTP secret
    backup_codes: Optional[List[str]] = None  # Encrypted backup codes


class ChurnAnalytics(BaseModel):
    """Comprehensive churn analytics"""

    # Current churn metrics
    monthly_churn_rate: float
    quarterly_churn_rate: float
    annual_churn_rate: float
    gross_churn_rate: float
    net_churn_rate: float  # Includes expansion revenue

    # Churn trends
    churn_trend_6_months: List[
        Dict[str, Any]
    ]  # [{"month": "Jan", "churn_rate": 3.2, "churned_customers": 12}]
    churn_by_plan: Dict[
        str, float
    ]  # {"starter": 5.2, "professional": 2.8, "enterprise": 1.1}
    churn_by_industry: Dict[str, float]
    churn_by_customer_age: Dict[
        str, float
    ]  # {"0-3_months": 15.5, "3-6_months": 8.2, etc.}

    # Churn reasons and patterns
    churn_reasons: List[
        Dict[str, Any]
    ]  # [{"reason": "Price", "percentage": 35.2, "count": 23}]
    voluntary_vs_involuntary: Dict[
        str, float
    ]  # {"voluntary": 78.5, "involuntary": 21.5}

    # Early warning indicators
    at_risk_customers: Dict[
        str, int
    ]  # {"high_risk": 45, "medium_risk": 123, "low_risk": 234}
    engagement_decline_alerts: int
    payment_failure_alerts: int
    support_escalation_alerts: int

    # Cohort analysis
    cohort_retention_rates: List[Dict[str, Any]]  # Monthly cohort retention
    ltv_by_cohort: Dict[str, float]

    # Predictive analytics
    predicted_churn_next_30_days: int
    predicted_churn_next_90_days: int
    churn_risk_score_distribution: Dict[str, int]  # {"0-20": 800, "20-40": 200, etc.}

    # Financial impact
    lost_revenue_this_month: float
    potential_lost_revenue_next_quarter: float
    saved_revenue_from_retention_efforts: float


class CustomerMetrics(BaseModel):
    """Aggregated customer metrics - no PII data"""

    total_customers: int
    active_customers: int
    new_customers_this_month: int
    churn_rate: float
    customers_by_plan: Dict[str, int]
    customers_by_industry: Dict[str, int]
    customer_retention_rate: float
    average_customer_lifetime: float  # in months

    # Enhanced customer analytics
    customer_acquisition_cost: float
    customer_lifetime_value: float
    monthly_active_users: int
    weekly_active_users: int
    expansion_revenue_rate: (
        float  # Percentage of revenue from existing customers upgrading
    )
    contraction_revenue_rate: float  # Percentage of revenue lost from downgrades

    # Customer engagement metrics
    average_login_frequency: float  # Logins per month
    feature_adoption_rates: Dict[str, float]
    time_to_first_value: float  # Days to first successful scan
    product_qualified_leads: int

    # Customer health scores
    healthy_customers: int  # High engagement, regular usage
    at_risk_customers: int  # Declining usage, support issues
    critical_customers: int  # Payment issues, low engagement


class RevenueMetrics(BaseModel):
    """Aggregated revenue metrics"""

    monthly_recurring_revenue: float
    annual_recurring_revenue: float
    revenue_growth_rate: float
    average_revenue_per_user: float
    monthly_revenue: List[Dict[str, Any]]  # [{"month": "Jan", "revenue": 1000}]
    revenue_by_plan: Dict[str, float]
    revenue_by_region: Dict[str, float]
    total_revenue: float
    projected_revenue: float


class UsageMetrics(BaseModel):
    """Aggregated usage analytics"""

    total_scans: int
    scans_this_month: int
    average_scans_per_customer: float
    total_violations_found: int
    average_compliance_score: float
    popular_features: List[Dict[str, Any]]  # [{"feature": "name", "usage": 80}]
    scan_frequency_trends: List[Dict[str, Any]]
    resource_utilization: Dict[str, float]


class SystemHealthMetrics(BaseModel):
    """System operational metrics"""

    api_uptime: float
    average_response_time: int  # milliseconds
    error_rate: float
    active_scans: int
    queued_scans: int
    system_alerts: int
    storage_usage: Dict[str, float]  # {"used_gb": 500, "total_gb": 1000}
    compute_usage: Dict[str, float]
    database_performance: Dict[str, Any]


class SupportMetrics(BaseModel):
    """Customer support metrics"""

    open_tickets: int
    average_resolution_time: float  # hours
    customer_satisfaction_score: float
    escalated_tickets: int
    tickets_by_category: Dict[str, int]
    support_response_time: float


class SecurityMetrics(BaseModel):
    """Security and compliance metrics"""

    failed_login_attempts: int
    suspicious_activities: int
    security_alerts: int
    compliance_violations: int
    data_breaches: int
    vulnerability_score: float
    security_incidents: List[Dict[str, Any]]


class AdminDashboardData(BaseModel):
    """Complete admin dashboard data - aggregated and anonymized"""

    customer_metrics: CustomerMetrics
    churn_analytics: ChurnAnalytics
    revenue_metrics: RevenueMetrics
    usage_metrics: UsageMetrics
    system_health: SystemHealthMetrics
    support_metrics: SupportMetrics
    security_metrics: SecurityMetrics
    last_updated: datetime = Field(default_factory=datetime.now)


class AdminAuditLog(BaseModel):
    """Audit log for admin actions"""

    log_id: str
    admin_id: str
    admin_email: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True


class AdminSession(BaseModel):
    """Admin session tracking"""

    session_id: str
    admin_id: str
    ip_address: str
    user_agent: str
    login_time: datetime
    last_activity: datetime
    is_active: bool = True
    two_factor_verified: bool = False
    session_token: str


# Data aggregation models for privacy protection
class CustomerSummary(BaseModel):
    """Non-PII customer summary for admin dashboard"""

    customer_count: int
    plan_distribution: Dict[str, int]
    industry_distribution: Dict[str, int]
    geographic_distribution: Dict[str, int]
    signup_trends: List[Dict[str, Any]]
    churn_analysis: Dict[str, Any]


class RevenueSummary(BaseModel):
    """Revenue summary for admin dashboard"""

    current_mrr: float
    mrr_growth: float
    revenue_by_segment: Dict[str, float]
    revenue_trends: List[Dict[str, Any]]
    forecast: Dict[str, float]


class ComplianceMetrics(BaseModel):
    """Compliance-related metrics for admin oversight"""

    total_scans_performed: int
    violations_detected: int
    compliance_score_average: float
    hipaa_violations: int
    soc2_violations: int
    environment_separation_violations: int
    remediation_rate: float
    compliance_trends: List[Dict[str, Any]]


# Admin configuration models
class AdminConfiguration(BaseModel):
    """System-wide admin configuration"""

    config_id: str
    setting_name: str
    setting_value: Any
    description: str
    is_sensitive: bool = False
    last_modified_by: str
    last_modified_at: datetime = Field(default_factory=datetime.now)


class AdminNotification(BaseModel):
    """Admin notifications and alerts"""

    notification_id: str
    type: str  # "alert", "warning", "info"
    title: str
    message: str
    severity: str  # "low", "medium", "high", "critical"
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    action_required: bool = False
    action_url: Optional[str] = None
