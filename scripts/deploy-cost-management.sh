#!/bin/bash

echo "💰 Deploying CompliantGuard Cost Management Infrastructure"
echo "========================================================="
echo ""

# Configuration
REGION="us-east-1"
STACK_NAME="compliantguard-cost-management"
TEMPLATE_FILE="infrastructure/cost-management-template.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Parse command line arguments
ALERT_EMAIL=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --email)
            ALERT_EMAIL="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 --email <alert-email> [--dry-run]"
            echo "  --email       Email address for cost alerts (required)"
            echo "  --dry-run     Show what would be deployed without executing"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$ALERT_EMAIL" ]; then
    log_error "Alert email is required. Use --email <email-address>"
    exit 1
fi

echo "🕐 Deployment started at: $(date)"
echo "🌎 Region: $REGION"
echo "📧 Alert Email: $ALERT_EMAIL"
echo "📋 Stack Name: $STACK_NAME"
echo ""

if [ "$DRY_RUN" = true ]; then
    log_warning "Running in DRY RUN mode - no resources will be deployed"
    echo ""
fi

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    log_error "Template file not found: $TEMPLATE_FILE"
    exit 1
fi

# Validate CloudFormation template
log_info "Validating CloudFormation template..."
if aws cloudformation validate-template \
    --template-body file://$TEMPLATE_FILE \
    --region $REGION >/dev/null 2>&1; then
    log_info "✅ Template validation successful"
else
    log_error "Template validation failed"
    exit 1
fi

# Check if stack already exists
STACK_EXISTS=false
if aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region $REGION >/dev/null 2>&1; then
    STACK_EXISTS=true
    log_info "Stack already exists - will update"
else
    log_info "Stack does not exist - will create"
fi

if [ "$DRY_RUN" = true ]; then
    echo ""
    log_warning "DRY RUN - Would deploy the following resources:"
    echo "=============================================="
    echo "✅ SNS Topic for cost alerts"
    echo "✅ CloudWatch Dashboard with cost metrics"
    echo "✅ Cost Anomaly Detector"
    echo "✅ CloudWatch Alarms for high costs"
    echo "✅ Lambda function for daily cost reports"
    echo "✅ EventBridge rule for scheduled reports"
    echo "✅ IAM roles and policies"
    echo ""
    echo "Parameters:"
    echo "  ProjectName: CompliantGuard"
    echo "  Environment: shared"
    echo "  AlertEmail: $ALERT_EMAIL"
    echo "  DevBudgetLimit: 50"
    echo "  StagingBudgetLimit: 100"
    echo "  ProdBudgetLimit: 200"
    echo ""
    echo "To execute: $0 --email $ALERT_EMAIL"
    exit 0
fi

# Deploy the stack
log_info "Deploying cost management infrastructure..."

OPERATION="create"
if [ "$STACK_EXISTS" = true ]; then
    OPERATION="update"
fi

# Create/Update stack
if aws cloudformation ${OPERATION}-stack \
    --stack-name "$STACK_NAME" \
    --template-body file://$TEMPLATE_FILE \
    --parameters \
        ParameterKey=ProjectName,ParameterValue=CompliantGuard \
        ParameterKey=Environment,ParameterValue=shared \
        ParameterKey=AlertEmail,ParameterValue="$ALERT_EMAIL" \
        ParameterKey=DevBudgetLimit,ParameterValue=50 \
        ParameterKey=StagingBudgetLimit,ParameterValue=100 \
        ParameterKey=ProdBudgetLimit,ParameterValue=200 \
    --capabilities CAPABILITY_NAMED_IAM \
    --tags \
        Key=Project,Value=CompliantGuard \
        Key=Environment,Value=shared \
        Key=Component,Value=cost-management \
        Key=Owner,Value=DevOps \
        Key=CostCenter,Value=Engineering \
    --region $REGION >/dev/null 2>&1; then
    
    log_info "✅ Stack $OPERATION initiated successfully"
    log_info "⏳ Waiting for stack $OPERATION to complete..."
    
    # Wait for stack operation to complete
    if aws cloudformation wait stack-${OPERATION}-complete \
        --stack-name "$STACK_NAME" \
        --region $REGION; then
        log_info "✅ Stack $OPERATION completed successfully"
    else
        log_error "Stack $OPERATION failed"
        exit 1
    fi
else
    log_error "Failed to initiate stack $OPERATION"
    exit 1
fi

# Get stack outputs
log_info "Retrieving stack outputs..."

DASHBOARD_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
    --output text 2>/dev/null || echo "")

SNS_TOPIC_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`SNSTopicArn`].OutputValue' \
    --output text 2>/dev/null || echo "")

LAMBDA_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`CostReportingFunctionArn`].OutputValue' \
    --output text 2>/dev/null || echo "")

echo ""
echo "🎉 Cost Management Infrastructure Deployed Successfully!"
echo "======================================================="
echo ""
echo "📊 Dashboard URL:"
echo "   $DASHBOARD_URL"
echo ""
echo "📧 Cost Alerts Topic:"
echo "   $SNS_TOPIC_ARN"
echo ""
echo "⚡ Cost Reporting Function:"
echo "   $LAMBDA_ARN"
echo ""

echo "🚀 Next Steps:"
echo "=============="
echo "1. ✅ Confirm email subscription in your inbox"
echo "2. 🏷️  Run resource tagging: ./scripts/setup-cost-dashboard.sh"
echo "3. 📋 Set up AWS Budgets (requires manual configuration):"
echo "   https://console.aws.amazon.com/billing/home#/budgets"
echo "4. 📊 View your cost dashboard:"
echo "   $DASHBOARD_URL"
echo "5. 🔍 Test the cost reporting function:"
echo "   aws lambda invoke --function-name compliantguard-cost-reporting output.json"
echo ""

echo "💡 Tagging Strategy Applied:"
echo "==========================="
echo "All resources are tagged with:"
echo "• Project: CompliantGuard"
echo "• Environment: shared"
echo "• Component: cost-management"  
echo "• Owner: DevOps"
echo "• CostCenter: Engineering"
echo ""

echo "🔔 Alerts Configured:"
echo "===================="
echo "• Daily cost reports at 9 AM UTC"
echo "• High cost alerts when daily spend > $200"
echo "• Anomaly detection for unusual cost patterns"
echo "• Email notifications to: $ALERT_EMAIL"
echo ""

echo "💰 Budget Recommendations:"
echo "=========================="
echo "• Development: $50/month"
echo "• Staging: $100/month"
echo "• Production: $200/month"
echo "• Total Project: $350/month"

echo ""
echo "✅ Deployment completed at: $(date)"