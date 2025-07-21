#!/bin/bash

echo "🔍 AWS Account Resource Audit - Timestamped Items"
echo "================================================="
echo ""

# Configuration
REGION="us-east-1"
PROJECT_PREFIX="themisguard"
COMPLIANT_PREFIX="compliantguard"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_section() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to estimate costs
estimate_cost() {
    local resource_type=$1
    local count=$2
    local unit_cost=$3
    
    if [ $count -gt 0 ]; then
        cost=$(echo "scale=2; $count * $unit_cost" | bc)
        echo -e "${YELLOW}💰 Estimated monthly cost: \$$cost${NC}"
    fi
}

echo "🕐 Audit started at: $(date)"
echo "🌎 Region: $REGION"
echo ""

# 1. CloudFormation Stacks
log_section "CloudFormation Stacks"

echo "🔍 Searching for timestamped stacks..."
TIMESTAMPED_STACKS=$(aws cloudformation list-stacks \
    --region $REGION \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
    --query 'StackSummaries[?contains(StackName, `20`) && (contains(StackName, `themisguard`) || contains(StackName, `compliantguard`))].{Name:StackName,Status:StackStatus,Created:CreationTime}' \
    --output table 2>/dev/null || echo "")

if [ ! -z "$TIMESTAMPED_STACKS" ]; then
    echo "$TIMESTAMPED_STACKS"
    STACK_COUNT=$(aws cloudformation list-stacks --region $REGION --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[?contains(StackName, `20`) && (contains(StackName, `themisguard`) || contains(StackName, `compliantguard`))]' --output text | wc -l)
    log_warning "Found $STACK_COUNT timestamped CloudFormation stacks"
else
    log_info "No timestamped CloudFormation stacks found"
fi

echo ""

# 2. DynamoDB Tables
log_section "DynamoDB Tables"

echo "🔍 Searching for timestamped tables..."
ALL_TABLES=$(aws dynamodb list-tables --region $REGION --query 'TableNames[]' --output text 2>/dev/null || echo "")

if [ ! -z "$ALL_TABLES" ]; then
    THEMIS_TABLES=$(echo "$ALL_TABLES" | tr ' ' '\n' | grep -E "(themisguard|compliantguard)" | sort)
    TIMESTAMPED_TABLES=$(echo "$THEMIS_TABLES" | grep -E "20[0-9]{6}-[0-9]{6}" || echo "")
    
    echo "📊 All project tables:"
    echo "$THEMIS_TABLES" | sed 's/^/  /'
    echo ""
    
    if [ ! -z "$TIMESTAMPED_TABLES" ]; then
        TIMESTAMP_COUNT=$(echo "$TIMESTAMPED_TABLES" | wc -l)
        log_warning "Found $TIMESTAMP_COUNT timestamped DynamoDB tables:"
        echo "$TIMESTAMPED_TABLES" | sed 's/^/  🗑️  /'
        estimate_cost "DynamoDB tables" $TIMESTAMP_COUNT 0.25
    else
        log_info "No timestamped DynamoDB tables found"
    fi
    
    # Show table details for cost estimation
    echo ""
    echo "📋 Table details for cost estimation:"
    for table in $THEMIS_TABLES; do
        TABLE_INFO=$(aws dynamodb describe-table --table-name "$table" --region $REGION \
            --query 'Table.{Name:TableName,Status:TableStatus,ItemCount:ItemCount,SizeBytes:TableSizeBytes,BillingMode:BillingModeSummary.BillingMode}' \
            --output json 2>/dev/null)
        
        if [ ! -z "$TABLE_INFO" ]; then
            echo "  Table: $table"
            echo "$TABLE_INFO" | jq -r '  "    Status: \(.Status), Items: \(.ItemCount // 0), Size: \(.SizeBytes // 0) bytes, Billing: \(.BillingMode)"'
        fi
    done
else
    log_info "No DynamoDB tables found"
fi

echo ""

# 3. S3 Buckets
log_section "S3 Buckets"

echo "🔍 Searching for timestamped buckets..."
ALL_BUCKETS=$(aws s3api list-buckets --query 'Buckets[].Name' --output text 2>/dev/null || echo "")

if [ ! -z "$ALL_BUCKETS" ]; then
    PROJECT_BUCKETS=$(echo "$ALL_BUCKETS" | tr ' ' '\n' | grep -E "(themisguard|compliantguard)" | sort)
    TIMESTAMPED_BUCKETS=$(echo "$PROJECT_BUCKETS" | grep -E "20[0-9]{6}-[0-9]{6}" || echo "")
    
    echo "📊 All project buckets:"
    echo "$PROJECT_BUCKETS" | sed 's/^/  /'
    echo ""
    
    if [ ! -z "$TIMESTAMPED_BUCKETS" ]; then
        BUCKET_COUNT=$(echo "$TIMESTAMPED_BUCKETS" | wc -l)
        log_warning "Found $BUCKET_COUNT timestamped S3 buckets:"
        echo "$TIMESTAMPED_BUCKETS" | sed 's/^/  🗑️  /'
        
        # Check bucket sizes
        echo ""
        echo "📋 Bucket sizes:"
        for bucket in $TIMESTAMPED_BUCKETS; do
            SIZE=$(aws s3 ls s3://$bucket --recursive --summarize 2>/dev/null | grep "Total Size:" | awk '{print $3}' || echo "0")
            if [ "$SIZE" -gt 0 ]; then
                SIZE_MB=$(echo "scale=2; $SIZE / 1024 / 1024" | bc)
                echo "  $bucket: ${SIZE_MB} MB"
            else
                echo "  $bucket: Empty"
            fi
        done
    else
        log_info "No timestamped S3 buckets found"
    fi
else
    log_info "No S3 buckets found"
fi

echo ""

# 4. Lambda Functions
log_section "Lambda Functions"

echo "🔍 Searching for timestamped Lambda functions..."
ALL_FUNCTIONS=$(aws lambda list-functions --region $REGION --query 'Functions[].FunctionName' --output text 2>/dev/null || echo "")

if [ ! -z "$ALL_FUNCTIONS" ]; then
    PROJECT_FUNCTIONS=$(echo "$ALL_FUNCTIONS" | tr ' ' '\n' | grep -E "(themisguard|compliantguard)" | sort)
    TIMESTAMPED_FUNCTIONS=$(echo "$PROJECT_FUNCTIONS" | grep -E "20[0-9]{6}-[0-9]{6}" || echo "")
    
    echo "📊 All project functions:"
    echo "$PROJECT_FUNCTIONS" | sed 's/^/  /'
    echo ""
    
    if [ ! -z "$TIMESTAMPED_FUNCTIONS" ]; then
        FUNCTION_COUNT=$(echo "$TIMESTAMPED_FUNCTIONS" | wc -l)
        log_warning "Found $FUNCTION_COUNT timestamped Lambda functions:"
        echo "$TIMESTAMPED_FUNCTIONS" | sed 's/^/  🗑️  /'
    else
        log_info "No timestamped Lambda functions found"
    fi
else
    log_info "No Lambda functions found"
fi

echo ""

# 5. API Gateway APIs
log_section "API Gateway REST APIs"

echo "🔍 Searching for timestamped API Gateway APIs..."
ALL_APIS=$(aws apigateway get-rest-apis --region $REGION --query 'items[].{Name:name,Id:id}' --output json 2>/dev/null || echo "[]")

if [ "$ALL_APIS" != "[]" ]; then
    PROJECT_APIS=$(echo "$ALL_APIS" | jq -r '.[] | select(.Name | test("themisguard|compliantguard")) | .Name')
    TIMESTAMPED_APIS=$(echo "$PROJECT_APIS" | grep -E "20[0-9]{6}-[0-9]{6}" || echo "")
    
    echo "📊 All project APIs:"
    echo "$PROJECT_APIS" | sed 's/^/  /'
    echo ""
    
    if [ ! -z "$TIMESTAMPED_APIS" ]; then
        API_COUNT=$(echo "$TIMESTAMPED_APIS" | wc -l)
        log_warning "Found $API_COUNT timestamped API Gateway APIs:"
        echo "$TIMESTAMPED_APIS" | sed 's/^/  🗑️  /'
    else
        log_info "No timestamped API Gateway APIs found"
    fi
else
    log_info "No API Gateway APIs found"
fi

echo ""

# 6. CloudWatch Log Groups
log_section "CloudWatch Log Groups"

echo "🔍 Searching for timestamped log groups..."
ALL_LOG_GROUPS=$(aws logs describe-log-groups --region $REGION --query 'logGroups[].logGroupName' --output text 2>/dev/null || echo "")

if [ ! -z "$ALL_LOG_GROUPS" ]; then
    PROJECT_LOG_GROUPS=$(echo "$ALL_LOG_GROUPS" | tr ' ' '\n' | grep -E "(themisguard|compliantguard)" | sort)
    TIMESTAMPED_LOG_GROUPS=$(echo "$PROJECT_LOG_GROUPS" | grep -E "20[0-9]{6}-[0-9]{6}" || echo "")
    
    echo "📊 All project log groups:"
    echo "$PROJECT_LOG_GROUPS" | sed 's/^/  /'
    echo ""
    
    if [ ! -z "$TIMESTAMPED_LOG_GROUPS" ]; then
        LOG_GROUP_COUNT=$(echo "$TIMESTAMPED_LOG_GROUPS" | wc -l)
        log_warning "Found $LOG_GROUP_COUNT timestamped CloudWatch log groups:"
        echo "$TIMESTAMPED_LOG_GROUPS" | sed 's/^/  🗑️  /'
    else
        log_info "No timestamped CloudWatch log groups found"
    fi
else
    log_info "No CloudWatch log groups found"
fi

echo ""

# 7. IAM Roles
log_section "IAM Roles"

echo "🔍 Searching for timestamped IAM roles..."
ALL_ROLES=$(aws iam list-roles --query 'Roles[].RoleName' --output text 2>/dev/null || echo "")

if [ ! -z "$ALL_ROLES" ]; then
    PROJECT_ROLES=$(echo "$ALL_ROLES" | tr ' ' '\n' | grep -E "(themisguard|compliantguard)" | sort)
    TIMESTAMPED_ROLES=$(echo "$PROJECT_ROLES" | grep -E "20[0-9]{6}-[0-9]{6}" || echo "")
    
    echo "📊 All project roles:"
    echo "$PROJECT_ROLES" | sed 's/^/  /'
    echo ""
    
    if [ ! -z "$TIMESTAMPED_ROLES" ]; then
        ROLE_COUNT=$(echo "$TIMESTAMPED_ROLES" | wc -l)
        log_warning "Found $ROLE_COUNT timestamped IAM roles:"
        echo "$TIMESTAMPED_ROLES" | sed 's/^/  🗑️  /'
    else
        log_info "No timestamped IAM roles found"
    fi
else
    log_info "No IAM roles found"
fi

echo ""

# 8. Summary and Recommendations
log_section "Audit Summary"

echo "🕐 Audit completed at: $(date)"
echo ""

echo "📊 Resources Found:"
echo "==================="
TOTAL_STACKS=$(echo "$TIMESTAMPED_STACKS" | grep -c "themisguard" 2>/dev/null || echo 0)
TOTAL_TABLES=$(echo "$TIMESTAMPED_TABLES" | wc -l 2>/dev/null || echo 0)
TOTAL_BUCKETS=$(echo "$TIMESTAMPED_BUCKETS" | wc -l 2>/dev/null || echo 0)
TOTAL_FUNCTIONS=$(echo "$TIMESTAMPED_FUNCTIONS" | wc -l 2>/dev/null || echo 0)
TOTAL_APIS=$(echo "$TIMESTAMPED_APIS" | wc -l 2>/dev/null || echo 0)
TOTAL_LOG_GROUPS=$(echo "$TIMESTAMPED_LOG_GROUPS" | wc -l 2>/dev/null || echo 0)
TOTAL_ROLES=$(echo "$TIMESTAMPED_ROLES" | wc -l 2>/dev/null || echo 0)

echo "🗑️  CloudFormation Stacks: $TOTAL_STACKS"
echo "🗑️  DynamoDB Tables: $TOTAL_TABLES"
echo "🗑️  S3 Buckets: $TOTAL_BUCKETS"
echo "🗑️  Lambda Functions: $TOTAL_FUNCTIONS"
echo "🗑️  API Gateway APIs: $TOTAL_APIS"
echo "🗑️  CloudWatch Log Groups: $TOTAL_LOG_GROUPS"
echo "🗑️  IAM Roles: $TOTAL_ROLES"

TOTAL_RESOURCES=$((TOTAL_STACKS + TOTAL_TABLES + TOTAL_BUCKETS + TOTAL_FUNCTIONS + TOTAL_APIS + TOTAL_LOG_GROUPS + TOTAL_ROLES))
echo ""
echo "📈 Total timestamped resources: $TOTAL_RESOURCES"

if [ $TOTAL_RESOURCES -gt 0 ]; then
    echo ""
    log_warning "💰 Estimated monthly cost for cleanup-able resources:"
    ESTIMATED_TABLE_COST=$(echo "scale=2; $TOTAL_TABLES * 0.25" | bc 2>/dev/null || echo "0.00")
    echo "   DynamoDB tables: \$$ESTIMATED_TABLE_COST"
    echo "   Other resources: Variable (CloudFormation stacks incur costs for contained resources)"
    echo ""
    
    echo "🧹 Cleanup Recommendations:"
    echo "=========================="
    echo "1. Review the emergency DynamoDB cleanup script: ./scripts/emergency-dynamodb-cleanup.sh"
    echo "2. Delete timestamped CloudFormation stacks (this will clean up associated resources)"
    echo "3. Clean up unused S3 buckets and their contents"
    echo "4. Remove orphaned Lambda functions and API Gateway APIs"
    echo "5. Delete old CloudWatch log groups to reduce log storage costs"
    echo "6. Clean up orphaned IAM roles"
    echo ""
    
    echo "⚡ Quick cleanup commands:"
    echo "========================"
    echo "# Delete timestamped DynamoDB tables:"
    echo "./scripts/emergency-dynamodb-cleanup.sh"
    echo ""
    echo "# Delete timestamped CloudFormation stacks:"
    if [ ! -z "$TIMESTAMPED_STACKS" ]; then
        echo "$TIMESTAMPED_STACKS" | grep -o "themisguard-api-dev-20[0-9]*-[0-9]*" | head -5 | while read stack; do
            echo "aws cloudformation delete-stack --stack-name $stack --region $REGION"
        done
        if [ $(echo "$TIMESTAMPED_STACKS" | wc -l) -gt 5 ]; then
            echo "# ... and $(( $(echo "$TIMESTAMPED_STACKS" | wc -l) - 5 )) more stacks"
        fi
    fi
else
    log_info "✅ No timestamped resources found - your AWS account is clean!"
fi

echo ""
echo "🔒 Security Note:"
echo "================"
echo "⚠️  Always review resources before deletion"
echo "⚠️  Backup any important data before cleanup"
echo "⚠️  Some resources may have dependencies"
echo "⚠️  Consider using AWS Config for ongoing resource governance"