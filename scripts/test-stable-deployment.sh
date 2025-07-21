#!/bin/bash

echo "🚀 Testing SAM Deployment with Stable Resource Names"
echo "===================================================="
echo ""

# Configuration
REGION="us-east-1"
STACK_NAME="themisguard-api-dev"  # Fixed name, no timestamps!
ENVIRONMENT="dev"
PROJECT_NAME="themisguard"

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

echo "🕐 Test deployment started at: $(date)"
echo "🌎 Region: $REGION"
echo "📋 Stack Name: $STACK_NAME (STABLE - no timestamps)"
echo "🏷️  Environment: $ENVIRONMENT"
echo ""

# Show expected resource names
log_info "Expected stable resource names:"
echo "================================"
echo "Lambda Function: ${PROJECT_NAME}-${ENVIRONMENT}-api"
echo "DynamoDB Tables:"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-scans"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-users"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-admin-users"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-admin-sessions"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-admin-audit"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-admin-metrics"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-subscriptions"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-usage"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-invoices"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-webhook-events"
echo "  - ${PROJECT_NAME}-${ENVIRONMENT}-gcp-credentials"
echo "S3 Bucket: ${PROJECT_NAME}-${ENVIRONMENT}-reports-\${AWS_ACCOUNT_ID}"
echo "Cognito Pool: ${PROJECT_NAME}-${ENVIRONMENT}-users"
echo ""

# Validate template
log_info "Validating SAM template..."
if sam validate --region $REGION; then
    log_info "✅ Template validation successful"
else
    log_error "Template validation failed"
    exit 1
fi

echo ""

# Build the application
log_info "Building SAM application..."
if sam build --region $REGION; then
    log_info "✅ Build successful"
else
    log_error "Build failed"
    exit 1
fi

echo ""

# Check if stack already exists
STACK_EXISTS=false
if aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region $REGION >/dev/null 2>&1; then
    STACK_EXISTS=true
    log_info "Stack already exists - will update"
    
    # Show current resource names (for comparison)
    log_info "Current stack resources:"
    aws cloudformation list-stack-resources \
        --stack-name "$STACK_NAME" \
        --region $REGION \
        --query 'StackResourceSummaries[?ResourceType==`AWS::DynamoDB::Table`].{Type:ResourceType,LogicalId:LogicalResourceId,PhysicalId:PhysicalResourceId}' \
        --output table 2>/dev/null || echo "  (Unable to list current resources)"
else
    log_info "Stack does not exist - will create"
fi

echo ""

# Ask for confirmation
read -p "🤔 Do you want to proceed with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

# Deploy with stable configuration
log_info "Deploying with stable resource names..."

# Use samconfig.toml dev environment for stable deployment
if sam deploy --config-env dev --region $REGION; then
    log_info "✅ Deployment successful!"
else
    log_error "Deployment failed"
    exit 1
fi

echo ""

# Verify stable resource names
log_info "Verifying stable resource names..."

# Check Lambda function
LAMBDA_NAME=$(aws lambda get-function \
    --function-name "${PROJECT_NAME}-${ENVIRONMENT}-api" \
    --region $REGION \
    --query 'Configuration.FunctionName' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$LAMBDA_NAME" = "${PROJECT_NAME}-${ENVIRONMENT}-api" ]; then
    log_info "✅ Lambda function has stable name: $LAMBDA_NAME"
else
    log_warning "⚠️ Lambda function name mismatch: $LAMBDA_NAME"
fi

# Check DynamoDB tables
log_info "Checking DynamoDB table names..."
EXPECTED_TABLES=(
    "${PROJECT_NAME}-${ENVIRONMENT}-scans"
    "${PROJECT_NAME}-${ENVIRONMENT}-users"
    "${PROJECT_NAME}-${ENVIRONMENT}-admin-users"
    "${PROJECT_NAME}-${ENVIRONMENT}-gcp-credentials"
)

for table in "${EXPECTED_TABLES[@]}"; do
    if aws dynamodb describe-table \
        --table-name "$table" \
        --region $REGION >/dev/null 2>&1; then
        log_info "✅ Table exists with stable name: $table"
    else
        log_warning "⚠️ Table not found: $table"
    fi
done

# Check S3 bucket
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
EXPECTED_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-reports-${ACCOUNT_ID}"
if aws s3api head-bucket --bucket "$EXPECTED_BUCKET" 2>/dev/null; then
    log_info "✅ S3 bucket exists with stable name: $EXPECTED_BUCKET"
else
    log_warning "⚠️ S3 bucket not found: $EXPECTED_BUCKET"
fi

echo ""

# Get stack outputs
log_info "Stack outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region $REGION \
    --query 'Stacks[0].Outputs[]' \
    --output table 2>/dev/null || echo "  (Unable to retrieve outputs)"

echo ""

# Cost tracking verification
log_info "Verifying cost management tags..."
# Check Lambda function tags
LAMBDA_TAGS=$(aws lambda list-tags \
    --resource "arn:aws:lambda:$REGION:$ACCOUNT_ID:function:${PROJECT_NAME}-${ENVIRONMENT}-api" \
    --region $REGION \
    --query 'Tags' \
    --output json 2>/dev/null || echo "{}")

echo "Lambda function tags:"
echo "$LAMBDA_TAGS" | jq -r 'to_entries[] | "  \(.key): \(.value)"' 2>/dev/null || echo "  (Unable to retrieve tags)"

echo ""

log_info "🎉 Stable deployment test completed!"
echo ""
echo "✅ Benefits of stable naming:"
echo "  • No more timestamped resources"
echo "  • Predictable resource names"
echo "  • Environment separation (dev/staging/prod)"
echo "  • Proper cost allocation with tags"
echo "  • No duplicate resources on redeployment"
echo ""

echo "🏷️  Cost Management Tags Applied:"
echo "  • Project: $PROJECT_NAME"
echo "  • Environment: $ENVIRONMENT"
echo "  • Component: [api|core|auth|admin|storage]"
echo "  • Tier: development"
echo "  • Owner: DevOps"
echo "  • CostCenter: Engineering"
echo ""

echo "🚀 Next Steps:"
echo "=============="
echo "1. Clean up old timestamped resources: ./scripts/comprehensive-cleanup.sh --execute"
echo "2. Test staging deployment: sam deploy --config-env staging"
echo "3. Test production deployment: sam deploy --config-env prod"
echo "4. Monitor costs in dashboard: https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=CompliantGuard-Cost-Dashboard"

echo ""
echo "✅ Test completed at: $(date)"