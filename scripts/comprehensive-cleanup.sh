#!/bin/bash

echo "🧹 Comprehensive AWS Resource Cleanup"
echo "====================================="
echo ""

# Configuration
REGION="us-east-1"
DRY_RUN=true

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

log_dry_run() {
    echo -e "${YELLOW}[DRY RUN] $1${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --execute)
            DRY_RUN=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--execute|--dry-run]"
            echo "  --execute   Actually delete resources (dangerous!)"
            echo "  --dry-run   Show what would be deleted (default)"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ "$DRY_RUN" = true ]; then
    log_warning "Running in DRY RUN mode - no resources will be deleted"
    log_info "Use --execute to actually delete resources"
else
    log_error "LIVE MODE - Resources will be permanently deleted!"
    echo ""
    read -p "⚠️  Are you absolutely sure? Type 'DELETE EVERYTHING' to confirm: " -r
    echo
    if [[ $REPLY != "DELETE EVERYTHING" ]]; then
        echo "❌ Cleanup cancelled"
        exit 1
    fi
fi

echo ""
echo "🕐 Cleanup started at: $(date)"
echo "🌎 Region: $REGION"
echo ""

# Resources to keep (safe list)
SAFE_RESOURCES=(
    "compliantguard-gcp-credentials"
    "compliantguard-frontend-dev"
    "compliantguard-frontend-dev-fallback"
    "Music"
    "courses"
    "locations"
    "users-swagyu-dev"
)

echo "✅ Resources that will be KEPT:"
printf '  %s\n' "${SAFE_RESOURCES[@]}"
echo ""

# 1. Cleanup S3 Buckets
log_section "S3 Buckets Cleanup"

echo "🔍 Finding timestamped S3 buckets..."
TIMESTAMPED_BUCKETS=$(aws s3api list-buckets --query 'Buckets[?contains(Name, `themisguard-api-dev-20`)].Name' --output text 2>/dev/null || echo "")

if [ ! -z "$TIMESTAMPED_BUCKETS" ]; then
    BUCKET_COUNT=$(echo "$TIMESTAMPED_BUCKETS" | tr ' ' '\n' | wc -l)
    log_warning "Found $BUCKET_COUNT timestamped S3 buckets to delete:"
    
    for bucket in $TIMESTAMPED_BUCKETS; do
        echo "  🗑️  $bucket"
        
        if [ "$DRY_RUN" = true ]; then
            log_dry_run "Would delete bucket: $bucket"
        else
            echo "    Emptying bucket contents..."
            aws s3 rm "s3://$bucket" --recursive --region $REGION 2>/dev/null || true
            
            echo "    Deleting bucket..."
            if aws s3api delete-bucket --bucket "$bucket" --region $REGION 2>/dev/null; then
                log_info "✅ Deleted bucket: $bucket"
            else
                log_error "❌ Failed to delete bucket: $bucket"
            fi
        fi
    done
    
    # Estimate savings
    if [ "$DRY_RUN" = true ]; then
        BUCKET_COST=$(echo "scale=2; $BUCKET_COUNT * 0.50" | bc 2>/dev/null || echo "~")
        echo "💰 Estimated monthly savings: \$${BUCKET_COST}"
    fi
else
    log_info "No timestamped S3 buckets found"
fi

echo ""

# 2. Cleanup Lambda Functions
log_section "Lambda Functions Cleanup"

echo "🔍 Finding timestamped Lambda functions..."
TIMESTAMPED_FUNCTIONS=$(aws lambda list-functions --region $REGION --query 'Functions[?contains(FunctionName, `themisguard-api-dev-20`)].FunctionName' --output text 2>/dev/null || echo "")

if [ ! -z "$TIMESTAMPED_FUNCTIONS" ]; then
    FUNCTION_COUNT=$(echo "$TIMESTAMPED_FUNCTIONS" | tr ' ' '\n' | wc -l)
    log_warning "Found $FUNCTION_COUNT timestamped Lambda functions to delete:"
    
    for function in $TIMESTAMPED_FUNCTIONS; do
        echo "  🗑️  $function"
        
        if [ "$DRY_RUN" = true ]; then
            log_dry_run "Would delete function: $function"
        else
            if aws lambda delete-function --function-name "$function" --region $REGION 2>/dev/null; then
                log_info "✅ Deleted function: $function"
            else
                log_error "❌ Failed to delete function: $function"
            fi
        fi
    done
    
    # Estimate savings (Lambda is mostly pay-per-use, but there might be reserved concurrency costs)
    if [ "$DRY_RUN" = true ]; then
        echo "💰 Lambda functions: Mostly pay-per-use (minimal ongoing cost)"
    fi
else
    log_info "No timestamped Lambda functions found"
fi

echo ""

# 3. Cleanup API Gateway APIs
log_section "API Gateway APIs Cleanup"

echo "🔍 Finding timestamped API Gateway APIs..."
TIMESTAMPED_APIS=$(aws apigateway get-rest-apis --region $REGION --query 'items[?contains(name, `themisguard-api-dev-20`)].id' --output text 2>/dev/null || echo "")

if [ ! -z "$TIMESTAMPED_APIS" ]; then
    API_COUNT=$(echo "$TIMESTAMPED_APIS" | tr ' ' '\n' | wc -l)
    log_warning "Found $API_COUNT timestamped API Gateway APIs to delete:"
    
    # Get names for display
    API_NAMES=$(aws apigateway get-rest-apis --region $REGION --query 'items[?contains(name, `themisguard-api-dev-20`)].name' --output text 2>/dev/null || echo "")
    
    echo "$API_NAMES" | tr '\t' '\n' | while read api_name; do
        echo "  🗑️  $api_name"
    done
    
    if [ "$DRY_RUN" = true ]; then
        echo "$TIMESTAMPED_APIS" | tr '\t' '\n' | while read api_id; do
            log_dry_run "Would delete API Gateway: $api_id"
        done
    else
        echo "$TIMESTAMPED_APIS" | tr '\t' '\n' | while read api_id; do
            if aws apigateway delete-rest-api --rest-api-id "$api_id" --region $REGION 2>/dev/null; then
                log_info "✅ Deleted API Gateway: $api_id"
            else
                log_error "❌ Failed to delete API Gateway: $api_id"
            fi
        done
    fi
    
    # Estimate savings
    if [ "$DRY_RUN" = true ]; then
        API_COST=$(echo "scale=2; $API_COUNT * 3.50" | bc 2>/dev/null || echo "~")
        echo "💰 Estimated monthly savings: \$${API_COST}"
    fi
else
    log_info "No timestamped API Gateway APIs found"
fi

echo ""

# 4. Cleanup CloudWatch Log Groups
log_section "CloudWatch Log Groups Cleanup"

echo "🔍 Finding timestamped CloudWatch log groups..."
TIMESTAMPED_LOG_GROUPS=$(aws logs describe-log-groups --region $REGION --query 'logGroups[?contains(logGroupName, `themisguard-api-dev-20`)].logGroupName' --output text 2>/dev/null || echo "")

if [ ! -z "$TIMESTAMPED_LOG_GROUPS" ]; then
    LOG_GROUP_COUNT=$(echo "$TIMESTAMPED_LOG_GROUPS" | tr '\t' '\n' | wc -l)
    log_warning "Found $LOG_GROUP_COUNT timestamped CloudWatch log groups to delete:"
    
    echo "$TIMESTAMPED_LOG_GROUPS" | tr '\t' '\n' | while read log_group; do
        echo "  🗑️  $log_group"
        
        if [ "$DRY_RUN" = true ]; then
            log_dry_run "Would delete log group: $log_group"
        else
            if aws logs delete-log-group --log-group-name "$log_group" --region $REGION 2>/dev/null; then
                log_info "✅ Deleted log group: $log_group"
            else
                log_error "❌ Failed to delete log group: $log_group"
            fi
        fi
    done
    
    # Estimate savings
    if [ "$DRY_RUN" = true ]; then
        echo "💰 CloudWatch logs: Variable based on log volume"
    fi
else
    log_info "No timestamped CloudWatch log groups found"
fi

echo ""

# 5. Cleanup IAM Roles (be very careful here)
log_section "IAM Roles Cleanup"

echo "🔍 Finding timestamped IAM roles..."
TIMESTAMPED_ROLES=$(aws iam list-roles --query 'Roles[?contains(RoleName, `themisguard-api-dev-20`)].RoleName' --output text 2>/dev/null || echo "")

if [ ! -z "$TIMESTAMPED_ROLES" ]; then
    ROLE_COUNT=$(echo "$TIMESTAMPED_ROLES" | tr '\t' '\n' | wc -l)
    log_warning "Found $ROLE_COUNT timestamped IAM roles:"
    
    echo "$TIMESTAMPED_ROLES" | tr '\t' '\n' | while read role; do
        echo "  🗑️  $role"
        
        if [ "$DRY_RUN" = true ]; then
            log_dry_run "Would delete IAM role: $role (and associated policies)"
        else
            # First detach managed policies
            ATTACHED_POLICIES=$(aws iam list-attached-role-policies --role-name "$role" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null || echo "")
            if [ ! -z "$ATTACHED_POLICIES" ]; then
                echo "$ATTACHED_POLICIES" | tr '\t' '\n' | while read policy_arn; do
                    aws iam detach-role-policy --role-name "$role" --policy-arn "$policy_arn" 2>/dev/null || true
                done
            fi
            
            # Delete inline policies
            INLINE_POLICIES=$(aws iam list-role-policies --role-name "$role" --query 'PolicyNames[]' --output text 2>/dev/null || echo "")
            if [ ! -z "$INLINE_POLICIES" ]; then
                echo "$INLINE_POLICIES" | tr '\t' '\n' | while read policy_name; do
                    aws iam delete-role-policy --role-name "$role" --policy-name "$policy_name" 2>/dev/null || true
                done
            fi
            
            # Finally delete the role
            if aws iam delete-role --role-name "$role" 2>/dev/null; then
                log_info "✅ Deleted IAM role: $role"
            else
                log_error "❌ Failed to delete IAM role: $role"
            fi
        fi
    done
else
    log_info "No timestamped IAM roles found"
fi

echo ""

# 6. Summary
log_section "Cleanup Summary"

echo "🕐 Cleanup completed at: $(date)"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "📊 Resources that WOULD be deleted:"
    echo "=================================="
    S3_COUNT=$(echo "$TIMESTAMPED_BUCKETS" | tr ' ' '\n' | wc -l 2>/dev/null || echo 0)
    LAMBDA_COUNT=$(echo "$TIMESTAMPED_FUNCTIONS" | tr ' ' '\n' | wc -l 2>/dev/null || echo 0)
    API_COUNT=$(echo "$TIMESTAMPED_APIS" | tr '\t' '\n' | wc -l 2>/dev/null || echo 0)
    LOG_COUNT=$(echo "$TIMESTAMPED_LOG_GROUPS" | tr '\t' '\n' | wc -l 2>/dev/null || echo 0)
    ROLE_COUNT=$(echo "$TIMESTAMPED_ROLES" | tr '\t' '\n' | wc -l 2>/dev/null || echo 0)
    
    echo "🗑️  S3 Buckets: $S3_COUNT"
    echo "🗑️  Lambda Functions: $LAMBDA_COUNT"
    echo "🗑️  API Gateway APIs: $API_COUNT"
    echo "🗑️  CloudWatch Log Groups: $LOG_COUNT"
    echo "🗑️  IAM Roles: $ROLE_COUNT"
    
    TOTAL_RESOURCES=$((S3_COUNT + LAMBDA_COUNT + API_COUNT + LOG_COUNT + ROLE_COUNT))
    echo ""
    echo "📈 Total timestamped resources: $TOTAL_RESOURCES"
    
    if [ $TOTAL_RESOURCES -gt 0 ]; then
        echo ""
        log_warning "💰 Estimated monthly savings after cleanup:"
        S3_SAVINGS=$(echo "scale=2; $S3_COUNT * 0.50" | bc 2>/dev/null || echo "0")
        API_SAVINGS=$(echo "scale=2; $API_COUNT * 3.50" | bc 2>/dev/null || echo "0")
        TOTAL_SAVINGS=$(echo "scale=2; $S3_SAVINGS + $API_SAVINGS" | bc 2>/dev/null || echo "Unknown")
        echo "   S3 Storage: \$$S3_SAVINGS"
        echo "   API Gateway: \$$API_SAVINGS"
        echo "   Lambda: Minimal (pay-per-use)"
        echo "   CloudWatch: Variable"
        echo "   Total: ~\$$TOTAL_SAVINGS+"
        echo ""
        
        echo "🚀 To execute cleanup:"
        echo "====================="
        echo "$0 --execute"
    else
        log_info "✅ No timestamped resources found - account is clean!"
    fi
else
    log_info "✅ Cleanup execution completed!"
    echo "Check the output above for any failed deletions."
fi

echo ""
echo "🔒 Next Steps:"
echo "=============="
echo "1. Fix SAM template to use stable resource names"
echo "2. Update deployment process to use --config-env"
echo "3. Set up cost monitoring and governance"
echo "4. Schedule monthly resource audits"