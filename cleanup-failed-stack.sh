#!/bin/bash

# Cleanup script for failed CloudFormation stack
# This script will disable deletion protection and delete the failed stack

STACK_NAME="themisguard-api-staging"
AWS_REGION="us-east-1"

echo "🧹 Cleaning up failed CloudFormation stack: $STACK_NAME"

# Function to disable deletion protection for a DynamoDB table
disable_table_deletion_protection() {
    local table_name=$1
    echo "  🔓 Disabling deletion protection for table: $table_name"
    
    aws dynamodb update-table \
        --table-name "$table_name" \
        --no-deletion-protection-enabled \
        --region "$AWS_REGION" \
        2>/dev/null || echo "    ⚠️ Table $table_name may not exist or already unprotected"
}

# Function to check if table exists
table_exists() {
    local table_name=$1
    aws dynamodb describe-table --table-name "$table_name" --region "$AWS_REGION" >/dev/null 2>&1
}

echo "📋 Step 1: Disabling deletion protection on remaining tables..."

# Check and disable deletion protection for tables that might still exist
TABLES_TO_CHECK=(
    "themisguard-staging-admin-users"
    "themisguard-staging-admin-audit"
)

for table in "${TABLES_TO_CHECK[@]}"; do
    if table_exists "$table"; then
        disable_table_deletion_protection "$table"
    else
        echo "    ✅ Table $table does not exist or is already cleaned up"
    fi
done

echo "📋 Step 2: Continuing stack deletion..."

# Continue the stack deletion process
aws cloudformation continue-update-rollback \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    2>/dev/null || echo "  ⚠️ Continue update rollback not needed or failed"

# Wait for stack deletion to complete or try manual deletion
echo "📋 Step 3: Monitoring stack deletion..."
aws cloudformation wait stack-delete-complete \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --cli-read-timeout 300 \
    --cli-connect-timeout 60 \
    2>/dev/null || {
    echo "  ⚠️ Stack deletion didn't complete automatically"
    echo "  🔥 Attempting to delete stack manually..."
    
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
    
    echo "  ⏳ Waiting for manual deletion to complete..."
    aws cloudformation wait stack-delete-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --cli-read-timeout 600 \
        2>/dev/null || echo "  ❌ Manual deletion also failed - may need AWS Console intervention"
}

# Check final stack status
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "DELETED")

if [ "$STACK_STATUS" = "DELETED" ]; then
    echo "✅ Stack cleanup completed successfully!"
    echo "🚀 Ready to retry deployment"
else
    echo "❌ Stack status: $STACK_STATUS"
    echo "🔧 You may need to manually clean up resources in AWS Console"
    echo "   - Check DynamoDB tables with deletion protection"
    echo "   - Check CloudFormation stack events for details"
fi

echo ""
echo "💡 After cleanup, you can retry deployment with:"
echo "   sam deploy --config-env staging"