#!/bin/bash

echo "🚀 AWS Deployment Testing Suite"
echo "==============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_section() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

# Check prerequisites
log_section "Checking Prerequisites"

# Check Python
if command -v python3 &> /dev/null; then
    log_info "Python 3 found"
else
    log_error "Python 3 not found. Please install Python 3"
    exit 1
fi

# Check pip packages
python3 -c "import requests" 2>/dev/null && log_info "requests library available" || log_warning "requests library missing (pip install requests)"
python3 -c "import boto3" 2>/dev/null && log_info "boto3 library available" || log_warning "boto3 library missing (pip install boto3)"

# Check AWS CLI
if command -v aws &> /dev/null; then
    log_info "AWS CLI found"
    
    # Check AWS credentials
    if aws sts get-caller-identity &> /dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
        log_info "AWS credentials configured (Account: $ACCOUNT_ID)"
    else
        log_error "AWS credentials not configured"
        echo "   Run: aws configure"
        exit 1
    fi
else
    log_error "AWS CLI not found. Please install AWS CLI"
    exit 1
fi

echo ""

# Main menu
while true; do
    log_section "AWS Deployment Testing Options"
    echo ""
    echo "1. Create test user in AWS DynamoDB"
    echo "2. Test authentication with deployed API"
    echo "3. Test GCP scanning with real credentials"
    echo "4. Check deployment status"
    echo "5. View AWS resources"
    echo "6. Exit"
    echo ""
    
    read -p "Select option (1-6): " choice
    
    case $choice in
        1)
            log_section "Creating Test User"
            python3 scripts/create-test-user.py
            ;;
        2)
            log_section "Testing Authentication"
            if [[ -f "test-login-dev.py" ]]; then
                python3 test-login-dev.py
            else
                log_warning "No test login script found. Create a test user first."
            fi
            ;;
        3)
            log_section "Testing GCP Scanning"
            python3 scripts/test-gcp-scanning.py
            ;;
        4)
            log_section "Checking Deployment Status"
            
            ENVIRONMENT=${1:-dev}
            STACK_NAME="themisguard-api-$ENVIRONMENT"
            
            echo "Checking stack: $STACK_NAME"
            
            if aws cloudformation describe-stacks --stack-name "$STACK_NAME" &> /dev/null; then
                STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].StackStatus' --output text)
                log_info "Stack status: $STATUS"
                
                # Get API Gateway URL
                API_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text)
                if [[ -n "$API_URL" ]]; then
                    log_info "API URL: $API_URL"
                else
                    log_warning "API URL not found in stack outputs"
                fi
                
                # Get DynamoDB tables
                echo ""
                echo "DynamoDB tables:"
                aws dynamodb list-tables --query "TableNames[?contains(@, 'themisguard-$ENVIRONMENT')]" --output table
                
            else
                log_error "Stack $STACK_NAME not found"
                echo "Available stacks:"
                aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[?contains(StackName, `themisguard`)].{Name:StackName,Status:StackStatus}' --output table
            fi
            ;;
        5)
            log_section "AWS Resources Overview"
            
            ENVIRONMENT=${1:-dev}
            
            echo "🗄️ DynamoDB Tables:"
            aws dynamodb list-tables --query "TableNames[?contains(@, 'themisguard')]" --output table
            
            echo ""
            echo "🗂️ S3 Buckets:"
            aws s3 ls | grep themisguard || echo "No themisguard buckets found"
            
            echo ""
            echo "⚡ Lambda Functions:"
            aws lambda list-functions --query "Functions[?contains(FunctionName, 'themisguard')].{Name:FunctionName,Runtime:Runtime,LastModified:LastModified}" --output table
            
            echo ""
            echo "🔑 KMS Keys:"
            aws kms list-aliases --query "Aliases[?contains(AliasName, 'compliantguard')].{Alias:AliasName,KeyId:TargetKeyId}" --output table
            
            echo ""
            echo "🌐 CloudFormation Stacks:"
            aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[?contains(StackName, `themisguard`)].{Name:StackName,Status:StackStatus,Created:CreationTime}' --output table
            ;;
        6)
            log_info "Goodbye!"
            exit 0
            ;;
        *)
            log_error "Invalid option. Please select 1-6."
            ;;
    esac
    
    echo ""
    echo "Press Enter to continue..."
    read
    echo ""
done