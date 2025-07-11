import stripe
import boto3
import json
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError

from ..models.subscription import (
    CustomerSubscription, PricingPlan, UsageRecord, PaymentIntent,
    Invoice, WebhookEvent, SubscriptionStatus, PlanTier, BillingInterval,
    THEMISGUARD_PLANS, SubscriptionChangeRequest, BillingPortalSession
)
from ..core.config import settings

class StripeService:
    def __init__(self):
        # Set Stripe API key (will be set via environment variables)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # DynamoDB for subscription data
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        self.subscriptions_table = self.dynamodb.Table('themisguard-subscriptions')
        self.usage_table = self.dynamodb.Table('themisguard-usage')
        self.invoices_table = self.dynamodb.Table('themisguard-invoices')
        self.webhook_events_table = self.dynamodb.Table('themisguard-webhook-events')
        
        # Stripe webhook endpoint secret
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    async def create_customer(self, user_id: str, email: str, name: str, company: Optional[str] = None) -> str:
        """Create a Stripe customer"""
        try:
            customer_data = {
                'email': email,
                'name': name,
                'metadata': {
                    'user_id': user_id,
                    'company': 'DELATSI LLC'  # Your LLC
                }
            }
            
            if company:
                customer_data['description'] = f"Customer from {company}"
                customer_data['metadata']['customer_company'] = company
            
            stripe_customer = stripe.Customer.create(**customer_data)
            
            return stripe_customer.id
            
        except stripe.error.StripeError as e:
            print(f"Stripe error creating customer: {e}")
            raise Exception(f"Failed to create customer: {str(e)}")

    async def create_subscription(
        self, 
        user_id: str, 
        stripe_customer_id: str, 
        plan_tier: PlanTier, 
        billing_interval: BillingInterval,
        trial_days: int = 14
    ) -> CustomerSubscription:
        """Create a new subscription"""
        try:
            plan = THEMISGUARD_PLANS[plan_tier]
            
            # Get the appropriate Stripe price ID
            price_id = (plan.stripe_price_id_annual if billing_interval == BillingInterval.ANNUAL 
                       else plan.stripe_price_id_monthly)
            
            if not price_id:
                raise Exception(f"Stripe price ID not configured for {plan_tier} {billing_interval}")
            
            # Create subscription in Stripe
            subscription_data = {
                'customer': stripe_customer_id,
                'items': [{'price': price_id}],
                'trial_period_days': trial_days,
                'collection_method': 'charge_automatically',
                'metadata': {
                    'user_id': user_id,
                    'plan_tier': plan_tier.value,
                    'billing_interval': billing_interval.value
                }
            }
            
            stripe_subscription = stripe.Subscription.create(**subscription_data)
            
            # Create our internal subscription record
            subscription = CustomerSubscription(
                subscription_id=f"sub_{secrets.token_urlsafe(16)}",
                customer_id=user_id,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription.id,
                plan=plan,
                status=SubscriptionStatus(stripe_subscription.status),
                billing_interval=billing_interval,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None
            )
            
            # Store in DynamoDB
            self.subscriptions_table.put_item(Item=subscription.dict())
            
            return subscription
            
        except stripe.error.StripeError as e:
            print(f"Stripe error creating subscription: {e}")
            raise Exception(f"Failed to create subscription: {str(e)}")

    async def get_customer_subscription(self, user_id: str) -> Optional[CustomerSubscription]:
        """Get customer's current subscription"""
        try:
            response = self.subscriptions_table.query(
                IndexName='customer-id-index',
                KeyConditionExpression='customer_id = :customer_id',
                ExpressionAttributeValues={':customer_id': user_id},
                ScanIndexForward=False,  # Get latest first
                Limit=1
            )
            
            if response.get('Items'):
                return CustomerSubscription(**response['Items'][0])
            
            return None
            
        except Exception as e:
            print(f"Error getting customer subscription: {e}")
            return None

    async def change_subscription(self, request: SubscriptionChangeRequest) -> CustomerSubscription:
        """Change customer subscription plan or billing interval"""
        try:
            current_subscription = await self.get_customer_subscription(request.customer_id)
            if not current_subscription:
                raise Exception("No active subscription found")
            
            new_plan = THEMISGUARD_PLANS[request.new_plan_tier]
            price_id = (new_plan.stripe_price_id_annual if request.new_billing_interval == BillingInterval.ANNUAL 
                       else new_plan.stripe_price_id_monthly)
            
            # Update subscription in Stripe
            stripe_subscription = stripe.Subscription.modify(
                current_subscription.stripe_subscription_id,
                items=[{
                    'id': stripe.Subscription.retrieve(current_subscription.stripe_subscription_id).items.data[0].id,
                    'price': price_id
                }],
                proration_behavior='create_prorations' if request.prorate else 'none'
            )
            
            # Update our internal record
            current_subscription.plan = new_plan
            current_subscription.billing_interval = request.new_billing_interval
            current_subscription.status = SubscriptionStatus(stripe_subscription.status)
            current_subscription.updated_at = datetime.now()
            
            # Save updated subscription
            self.subscriptions_table.put_item(Item=current_subscription.dict())
            
            return current_subscription
            
        except stripe.error.StripeError as e:
            print(f"Stripe error changing subscription: {e}")
            raise Exception(f"Failed to change subscription: {str(e)}")

    async def cancel_subscription(self, user_id: str, cancel_immediately: bool = False) -> CustomerSubscription:
        """Cancel customer subscription"""
        try:
            subscription = await self.get_customer_subscription(user_id)
            if not subscription:
                raise Exception("No active subscription found")
            
            if cancel_immediately:
                # Cancel immediately
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = SubscriptionStatus.CANCELED
                subscription.canceled_at = datetime.now()
            else:
                # Cancel at period end
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True
            
            subscription.updated_at = datetime.now()
            self.subscriptions_table.put_item(Item=subscription.dict())
            
            return subscription
            
        except stripe.error.StripeError as e:
            print(f"Stripe error canceling subscription: {e}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")

    async def record_usage(self, user_id: str, scans_count: int, projects_scanned: int, api_calls: int = 0):
        """Record usage for billing purposes"""
        try:
            subscription = await self.get_customer_subscription(user_id)
            if not subscription:
                return  # No subscription, no usage tracking needed
            
            current_date = datetime.now()
            month_year = current_date.strftime("%Y-%m")
            
            usage_record = UsageRecord(
                usage_id=f"usage_{secrets.token_urlsafe(16)}",
                customer_id=user_id,
                subscription_id=subscription.subscription_id,
                usage_date=current_date,
                scans_count=scans_count,
                projects_scanned=projects_scanned,
                api_calls=api_calls,
                month_year=month_year
            )
            
            self.usage_table.put_item(Item=usage_record.dict())
            
        except Exception as e:
            print(f"Error recording usage: {e}")

    async def get_monthly_usage(self, user_id: str, month_year: Optional[str] = None) -> Dict[str, int]:
        """Get customer's usage for a specific month"""
        try:
            if not month_year:
                month_year = datetime.now().strftime("%Y-%m")
            
            response = self.usage_table.query(
                IndexName='customer-month-index',
                KeyConditionExpression='customer_id = :customer_id AND month_year = :month_year',
                ExpressionAttributeValues={
                    ':customer_id': user_id,
                    ':month_year': month_year
                }
            )
            
            # Aggregate usage
            total_scans = sum(item.get('scans_count', 0) for item in response.get('Items', []))
            total_projects = len(set(item.get('projects_scanned', []) for item in response.get('Items', [])))
            total_api_calls = sum(item.get('api_calls', 0) for item in response.get('Items', []))
            
            return {
                'scans_count': total_scans,
                'projects_scanned': total_projects,
                'api_calls': total_api_calls,
                'month_year': month_year
            }
            
        except Exception as e:
            print(f"Error getting monthly usage: {e}")
            return {'scans_count': 0, 'projects_scanned': 0, 'api_calls': 0, 'month_year': month_year}

    async def check_usage_limits(self, user_id: str) -> Dict[str, Any]:
        """Check if customer is within their usage limits"""
        try:
            subscription = await self.get_customer_subscription(user_id)
            if not subscription:
                return {'within_limits': False, 'reason': 'No active subscription'}
            
            if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]:
                return {'within_limits': False, 'reason': f'Subscription status: {subscription.status}'}
            
            usage = await self.get_monthly_usage(user_id)
            plan = subscription.plan
            
            # Check scan limit
            if plan.scan_limit and usage['scans_count'] >= plan.scan_limit:
                return {
                    'within_limits': False, 
                    'reason': f'Monthly scan limit exceeded ({usage["scans_count"]}/{plan.scan_limit})',
                    'usage': usage,
                    'limits': {'scans': plan.scan_limit, 'projects': plan.project_limit}
                }
            
            # Check project limit
            if plan.project_limit and usage['projects_scanned'] >= plan.project_limit:
                return {
                    'within_limits': False,
                    'reason': f'Project limit exceeded ({usage["projects_scanned"]}/{plan.project_limit})',
                    'usage': usage,
                    'limits': {'scans': plan.scan_limit, 'projects': plan.project_limit}
                }
            
            return {
                'within_limits': True,
                'usage': usage,
                'limits': {'scans': plan.scan_limit, 'projects': plan.project_limit}
            }
            
        except Exception as e:
            print(f"Error checking usage limits: {e}")
            return {'within_limits': False, 'reason': 'Error checking limits'}

    async def create_billing_portal_session(self, user_id: str, return_url: str) -> str:
        """Create Stripe customer portal session for self-service billing"""
        try:
            subscription = await self.get_customer_subscription(user_id)
            if not subscription:
                raise Exception("No subscription found")
            
            session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=return_url
            )
            
            # Store session info
            portal_session = BillingPortalSession(
                session_id=f"portal_{secrets.token_urlsafe(16)}",
                customer_id=user_id,
                stripe_session_id=session.id,
                return_url=return_url,
                expires_at=datetime.now() + timedelta(hours=1)
            )
            
            return session.url
            
        except stripe.error.StripeError as e:
            print(f"Stripe error creating portal session: {e}")
            raise Exception(f"Failed to create billing portal session: {str(e)}")

    async def handle_webhook(self, payload: str, sig_header: str) -> bool:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
            
            # Store webhook event for processing
            webhook_event = WebhookEvent(
                event_id=f"webhook_{secrets.token_urlsafe(16)}",
                stripe_event_id=event['id'],
                event_type=event['type'],
                data=event['data']
            )
            
            self.webhook_events_table.put_item(Item=webhook_event.dict())
            
            # Process specific events
            if event['type'] == 'customer.subscription.updated':
                await self._handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                await self._handle_subscription_deleted(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                await self._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                await self._handle_payment_failed(event['data']['object'])
            
            # Mark as processed
            webhook_event.processed = True
            webhook_event.processed_at = datetime.now()
            self.webhook_events_table.put_item(Item=webhook_event.dict())
            
            return True
            
        except stripe.error.SignatureVerificationError:
            print("Invalid webhook signature")
            return False
        except Exception as e:
            print(f"Error handling webhook: {e}")
            return False

    async def _handle_subscription_updated(self, stripe_subscription: Dict[str, Any]):
        """Handle subscription update webhook"""
        try:
            # Find our subscription record
            response = self.subscriptions_table.scan(
                FilterExpression='stripe_subscription_id = :sub_id',
                ExpressionAttributeValues={':sub_id': stripe_subscription['id']}
            )
            
            if response.get('Items'):
                subscription_data = response['Items'][0]
                subscription_data['status'] = stripe_subscription['status']
                subscription_data['current_period_start'] = datetime.fromtimestamp(
                    stripe_subscription['current_period_start']
                ).isoformat()
                subscription_data['current_period_end'] = datetime.fromtimestamp(
                    stripe_subscription['current_period_end']
                ).isoformat()
                subscription_data['updated_at'] = datetime.now().isoformat()
                
                self.subscriptions_table.put_item(Item=subscription_data)
                
        except Exception as e:
            print(f"Error handling subscription update: {e}")

    async def _handle_subscription_deleted(self, stripe_subscription: Dict[str, Any]):
        """Handle subscription deletion webhook"""
        try:
            response = self.subscriptions_table.scan(
                FilterExpression='stripe_subscription_id = :sub_id',
                ExpressionAttributeValues={':sub_id': stripe_subscription['id']}
            )
            
            if response.get('Items'):
                subscription_data = response['Items'][0]
                subscription_data['status'] = 'canceled'
                subscription_data['canceled_at'] = datetime.now().isoformat()
                subscription_data['updated_at'] = datetime.now().isoformat()
                
                self.subscriptions_table.put_item(Item=subscription_data)
                
        except Exception as e:
            print(f"Error handling subscription deletion: {e}")

    async def _handle_payment_succeeded(self, stripe_invoice: Dict[str, Any]):
        """Handle successful payment webhook"""
        # Log successful payment, update customer status, etc.
        print(f"Payment succeeded for invoice: {stripe_invoice['id']}")

    async def _handle_payment_failed(self, stripe_invoice: Dict[str, Any]):
        """Handle failed payment webhook"""
        # Log failed payment, notify customer, etc.
        print(f"Payment failed for invoice: {stripe_invoice['id']}")

    def get_available_plans(self) -> Dict[str, PricingPlan]:
        """Get all available pricing plans"""
        return THEMISGUARD_PLANS