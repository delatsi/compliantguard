# Stripe Integration Setup for ThemisGuard

This document outlines how to set up Stripe payment processing for the ThemisGuard micro SaaS platform.

## Prerequisites

1. **Stripe Account**: Create a Stripe account at https://stripe.com
2. **Business Entity**: Have DELATSI LLC registered and ready for business banking

## Stripe Dashboard Setup

### 1. Get API Keys

1. Log into your Stripe Dashboard
2. Navigate to **Developers** > **API Keys**
3. Copy your **Publishable key** and **Secret key**
4. For testing, use the test keys (starting with `pk_test_` and `sk_test_`)

### 2. Create Products and Prices

Create the following products in your Stripe Dashboard:

#### Starter Plan
- **Product Name**: ThemisGuard Starter
- **Description**: Perfect for small teams getting started with HIPAA compliance
- **Monthly Price**: $49.00 USD
- **Annual Price**: $490.00 USD (17% discount)

#### Professional Plan  
- **Product Name**: ThemisGuard Professional
- **Description**: For growing companies with regular compliance needs
- **Monthly Price**: $99.00 USD
- **Annual Price**: $990.00 USD (17% discount)

#### Enterprise Plan
- **Product Name**: ThemisGuard Enterprise  
- **Description**: For large organizations with comprehensive compliance requirements
- **Monthly Price**: $199.00 USD
- **Annual Price**: $1,990.00 USD (17% discount)

### 3. Configure Webhooks

1. Go to **Developers** > **Webhooks**
2. Click **Add endpoint**
3. **Endpoint URL**: `https://your-domain.com/api/v1/webhooks/stripe`
4. **Events to send**:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.created`
   - `customer.updated`

5. Copy the **Signing secret** (starts with `whsec_`)

### 4. Enable Customer Portal

1. Go to **Settings** > **Billing** > **Customer portal**
2. Enable the customer portal
3. Configure allowed actions:
   - ✅ Update payment method
   - ✅ View billing history
   - ✅ Download invoices
   - ✅ Cancel subscription
   - ✅ Change subscription (if desired)

## Environment Configuration

1. Copy the environment template:
   ```bash
   cp backend/.env.template backend/.env
   ```

2. Update the Stripe configuration in `backend/.env`:
   ```env
   STRIPE_SECRET_KEY=sk_test_your_secret_key_here
   STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
   ```

## Backend Configuration

### 1. Update Subscription Models

Edit `backend/models/subscription.py` to include your actual Stripe Price IDs:

```python
THEMISGUARD_PLANS = {
    PlanTier.STARTER: PricingPlan(
        # ... other fields ...
        stripe_price_id_monthly="price_starter_monthly_id_from_stripe",
        stripe_price_id_annual="price_starter_annual_id_from_stripe",
    ),
    PlanTier.PROFESSIONAL: PricingPlan(
        # ... other fields ...
        stripe_price_id_monthly="price_professional_monthly_id_from_stripe", 
        stripe_price_id_annual="price_professional_annual_id_from_stripe",
    ),
    PlanTier.ENTERPRISE: PricingPlan(
        # ... other fields ...
        stripe_price_id_monthly="price_enterprise_monthly_id_from_stripe",
        stripe_price_id_annual="price_enterprise_annual_id_from_stripe",
    )
}
```

### 2. DynamoDB Tables

The following DynamoDB tables need to be created for subscription management:

- `themisguard-subscriptions` - Customer subscription data
- `themisguard-usage` - Usage tracking for billing  
- `themisguard-invoices` - Invoice records
- `themisguard-webhook-events` - Stripe webhook event processing

## Frontend Configuration

1. The pricing page is accessible at `/pricing`
2. Authenticated users can manage subscriptions at `/app/subscription`
3. The billing portal integration allows customers to self-manage their billing

## Testing

### 1. Test Cards

Use Stripe's test cards for testing:

- **Successful payment**: `4242 4242 4242 4242`
- **Payment requires authentication**: `4000 0025 0000 3155`
- **Payment is declined**: `4000 0000 0000 9995`

### 2. Test Workflows

1. **Subscription Creation**:
   - Visit `/pricing`
   - Select a plan
   - Complete signup flow
   - Verify subscription in Stripe Dashboard

2. **Usage Tracking**:
   - Perform a compliance scan
   - Check that usage is recorded in DynamoDB
   - Verify usage limits are enforced

3. **Billing Portal**:
   - Navigate to `/app/subscription`
   - Click "Manage Billing"
   - Test payment method updates

## Production Deployment

### 1. Switch to Live Keys

Replace test keys with live keys in production environment:

```env
STRIPE_SECRET_KEY=sk_live_your_live_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_live_webhook_secret
```

### 2. SSL Certificate

Ensure your production domain has a valid SSL certificate for Stripe webhooks.

### 3. Webhook URL

Update webhook endpoint URL to your production domain in Stripe Dashboard.

## Security Considerations

1. **Never commit API keys** to version control
2. **Use environment variables** for all sensitive configuration
3. **Validate webhook signatures** to ensure requests are from Stripe
4. **Implement proper error handling** for payment failures
5. **Log security events** for audit purposes

## DELATSI LLC Banking Setup

Once your business bank account is ready:

1. **Update Stripe Account**: Connect your business bank account to Stripe
2. **Tax Information**: Ensure tax forms (W-9, etc.) are completed
3. **Payout Schedule**: Configure automatic payouts to your business account
4. **Invoice Settings**: Update business information in Stripe for customer invoices

## Support and Monitoring

1. **Stripe Dashboard**: Monitor payments, failed charges, and disputes
2. **Usage Analytics**: Track customer usage patterns and billing efficiency
3. **Churn Monitoring**: Use the admin dashboard to monitor subscription cancellations
4. **Financial Reporting**: Generate monthly revenue reports for business tracking

## Next Steps

1. Test the complete billing flow in development
2. Set up monitoring and alerting for payment failures
3. Create customer communication templates for billing issues
4. Implement dunning management for failed payments
5. Plan for handling subscription upgrades and downgrades
6. Consider implementing usage-based billing for enterprise customers

---

**Note**: This integration provides a complete billing foundation for your micro SaaS. Start with the basic implementation and iterate based on customer feedback and business needs.