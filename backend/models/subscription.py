from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"

class PlanTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class BillingInterval(str, Enum):
    MONTHLY = "month"
    ANNUAL = "year"

class PricingPlan(BaseModel):
    """ThemisGuard subscription plans"""
    plan_id: str
    tier: PlanTier
    name: str
    description: str
    price_monthly: float
    price_annual: float
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_annual: Optional[str] = None
    features: List[str]
    scan_limit: Optional[int] = None  # None = unlimited
    project_limit: Optional[int] = None
    user_limit: Optional[int] = None
    api_access: bool = False
    priority_support: bool = False
    sso_enabled: bool = False
    custom_policies: bool = False

class CustomerSubscription(BaseModel):
    """Customer subscription details"""
    subscription_id: str
    customer_id: str  # Our internal customer ID
    stripe_customer_id: str
    stripe_subscription_id: str
    plan: PricingPlan
    status: SubscriptionStatus
    billing_interval: BillingInterval
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class UsageRecord(BaseModel):
    """Track usage for billing purposes"""
    usage_id: str
    customer_id: str
    subscription_id: str
    usage_date: datetime
    scans_count: int
    projects_scanned: int
    api_calls: int = 0
    violations_found: int = 0
    month_year: str  # Format: "2024-01" for aggregation

class PaymentIntent(BaseModel):
    """Payment intent for one-time payments or setup"""
    payment_intent_id: str
    customer_id: str
    stripe_payment_intent_id: str
    amount: float
    currency: str = "usd"
    status: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class Invoice(BaseModel):
    """Invoice tracking"""
    invoice_id: str
    customer_id: str
    subscription_id: str
    stripe_invoice_id: str
    amount_due: float
    amount_paid: float
    status: str
    invoice_date: datetime
    due_date: datetime
    paid_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

class WebhookEvent(BaseModel):
    """Stripe webhook event tracking"""
    event_id: str
    stripe_event_id: str
    event_type: str
    processed: bool = False
    processed_at: Optional[datetime] = None
    data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)

# Pre-defined pricing plans for ThemisGuard
THEMISGUARD_PLANS = {
    PlanTier.STARTER: PricingPlan(
        plan_id="starter",
        tier=PlanTier.STARTER,
        name="Starter",
        description="Perfect for small teams getting started with HIPAA compliance",
        price_monthly=49.00,
        price_annual=490.00,  # 2 months free
        features=[
            "Up to 100 scans per month",
            "HIPAA compliance scanning",
            "Environment separation detection",
            "Basic reporting dashboard",
            "Email support",
            "Up to 3 projects"
        ],
        scan_limit=100,
        project_limit=3,
        user_limit=5,
        api_access=False,
        priority_support=False,
        sso_enabled=False,
        custom_policies=False
    ),
    
    PlanTier.PROFESSIONAL: PricingPlan(
        plan_id="professional",
        tier=PlanTier.PROFESSIONAL,
        name="Professional", 
        description="For growing companies with regular compliance needs",
        price_monthly=99.00,
        price_annual=990.00,  # 2 months free
        features=[
            "Up to 500 scans per month",
            "HIPAA compliance scanning",
            "Environment separation detection", 
            "SOC 2 readiness reports",
            "Advanced analytics dashboard",
            "Priority email support",
            "Up to 10 projects",
            "API access",
            "Custom policy templates"
        ],
        scan_limit=500,
        project_limit=10,
        user_limit=15,
        api_access=True,
        priority_support=True,
        sso_enabled=False,
        custom_policies=True
    ),
    
    PlanTier.ENTERPRISE: PricingPlan(
        plan_id="enterprise",
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        description="For large organizations with comprehensive compliance requirements",
        price_monthly=199.00,
        price_annual=1990.00,  # 2 months free
        features=[
            "Unlimited scans",
            "HIPAA compliance scanning",
            "Environment separation detection",
            "SOC 2 readiness reports", 
            "Custom compliance frameworks",
            "Advanced analytics & churn prediction",
            "Priority phone & email support",
            "Unlimited projects",
            "Full API access",
            "SSO integration",
            "Custom policy creation",
            "Dedicated customer success manager"
        ],
        scan_limit=None,  # Unlimited
        project_limit=None,  # Unlimited
        user_limit=None,  # Unlimited
        api_access=True,
        priority_support=True,
        sso_enabled=True,
        custom_policies=True
    )
}

class SubscriptionChangeRequest(BaseModel):
    """Request to change subscription"""
    customer_id: str
    new_plan_tier: PlanTier
    new_billing_interval: BillingInterval
    effective_date: Optional[datetime] = None
    prorate: bool = True

class BillingPortalSession(BaseModel):
    """Stripe customer portal session"""
    session_id: str
    customer_id: str
    stripe_session_id: str
    return_url: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime