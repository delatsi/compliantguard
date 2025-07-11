#!/bin/bash

# ThemisGuard Frontend Deployment Script
# Deploys React frontend to S3 + CloudFront

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
SKIP_BUILD=false
SKIP_INVALIDATION=false
DRY_RUN=false
VERBOSE=false

# Help function
show_help() {
    cat << EOF
ThemisGuard Frontend Deployment Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Target environment (dev|staging|prod) [default: dev]
    -s, --skip-build        Skip the build step (use existing dist/)
    -i, --skip-invalidation Skip CloudFront cache invalidation
    -d, --dry-run          Show what would be done without executing
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

EXAMPLES:
    $0 -e dev                          # Deploy to development
    $0 -e prod --verbose               # Deploy to production with verbose output
    $0 -e staging --skip-build         # Deploy to staging without rebuilding
    $0 --dry-run                       # Preview what would happen

PREREQUISITES:
    - AWS CLI configured with appropriate credentials
    - Node.js and npm installed
    - Frontend infrastructure deployed (CloudFormation stack)

EOF
}

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${NC}🔍 $1${NC}"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -i|--skip-invalidation)
            SKIP_INVALIDATION=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod."
    exit 1
fi

# Set stack name based on environment
STACK_NAME="themisguard-frontend-${ENVIRONMENT}"

log_info "Starting frontend deployment to ${ENVIRONMENT} environment"
log_verbose "Stack name: $STACK_NAME"

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

log_verbose "Project root: $PROJECT_ROOT"
log_verbose "Frontend directory: $FRONTEND_DIR"

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Change to frontend directory
cd "$FRONTEND_DIR"

# Function to get CloudFormation output
get_cf_output() {
    local stack_name=$1
    local output_key=$2
    
    aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue" \
        --output text 2>/dev/null || echo ""
}

# Function to check if stack exists
stack_exists() {
    local stack_name=$1
    aws cloudformation describe-stacks --stack-name "$stack_name" >/dev/null 2>&1
}

# Check if frontend infrastructure exists
log_info "Checking frontend infrastructure..."
if ! stack_exists "$STACK_NAME"; then
    log_error "Frontend infrastructure stack '$STACK_NAME' not found."
    log_info "Please deploy the frontend infrastructure first:"
    log_info "  sam deploy --template-file frontend-template.yaml --stack-name $STACK_NAME --parameter-overrides Environment=$ENVIRONMENT"
    exit 1
fi

# Get infrastructure details
S3_BUCKET=$(get_cf_output "$STACK_NAME" "FrontendBucketName")
DISTRIBUTION_ID=$(get_cf_output "$STACK_NAME" "CloudFrontDistributionId")
FRONTEND_URL=$(get_cf_output "$STACK_NAME" "FrontendURL")

if [ -z "$S3_BUCKET" ] || [ -z "$DISTRIBUTION_ID" ]; then
    log_error "Could not retrieve infrastructure details from CloudFormation stack"
    exit 1
fi

log_success "Infrastructure found:"
log_verbose "S3 Bucket: $S3_BUCKET"
log_verbose "CloudFront Distribution: $DISTRIBUTION_ID"
log_verbose "Frontend URL: $FRONTEND_URL"

# Set environment variables for build
export VITE_ENVIRONMENT="$ENVIRONMENT"
export VITE_API_URL=$(get_cf_output "themisguard-api-${ENVIRONMENT}" "ApiGatewayUrl" || echo "")

log_verbose "Build environment variables:"
log_verbose "VITE_ENVIRONMENT: $VITE_ENVIRONMENT"
log_verbose "VITE_API_URL: $VITE_API_URL"

# Build the frontend
if [ "$SKIP_BUILD" = false ]; then
    log_info "Building frontend for $ENVIRONMENT environment..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would run: npm ci && npm run build"
    else
        # Install dependencies if node_modules doesn't exist or package-lock.json is newer
        if [ ! -d "node_modules" ] || [ "package-lock.json" -nt "node_modules" ]; then
            log_info "Installing dependencies..."
            npm ci
        fi
        
        # Build the application
        npm run build
        
        # Check if build was successful
        if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
            log_error "Build failed or dist directory is empty"
            exit 1
        fi
        
        log_success "Build completed successfully"
    fi
else
    log_warning "Skipping build step (using existing dist/)"
    
    if [ ! -d "dist" ] && [ "$DRY_RUN" = false ]; then
        log_error "dist/ directory not found. Cannot skip build."
        exit 1
    fi
fi

# Sync files to S3
log_info "Syncing files to S3..."

if [ "$DRY_RUN" = true ]; then
    log_info "[DRY RUN] Would sync files to s3://$S3_BUCKET/"
    if [ -d "dist" ]; then
        log_verbose "Files that would be synced:"
        find dist -type f | head -20
        if [ $(find dist -type f | wc -l) -gt 20 ]; then
            log_verbose "... and $(expr $(find dist -type f | wc -l) - 20) more files"
        fi
    fi
else
    # Sync with appropriate cache headers
    aws s3 sync dist/ "s3://$S3_BUCKET/" \
        --delete \
        --cache-control "public, max-age=31536000" \
        --exclude "*.html" \
        --exclude "sw.js" \
        --exclude "manifest.json"
    
    # Upload HTML files with shorter cache duration
    aws s3 sync dist/ "s3://$S3_BUCKET/" \
        --cache-control "public, max-age=0, must-revalidate" \
        --include "*.html" \
        --include "sw.js" \
        --include "manifest.json"
    
    log_success "Files synced to S3"
fi

# Invalidate CloudFront cache
if [ "$SKIP_INVALIDATION" = false ]; then
    log_info "Invalidating CloudFront cache..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would invalidate CloudFront distribution $DISTRIBUTION_ID"
    else
        INVALIDATION_ID=$(aws cloudfront create-invalidation \
            --distribution-id "$DISTRIBUTION_ID" \
            --paths "/*" \
            --query 'Invalidation.Id' \
            --output text)
        
        log_success "CloudFront invalidation started (ID: $INVALIDATION_ID)"
        
        if [ "$VERBOSE" = true ]; then
            log_info "Waiting for invalidation to complete..."
            aws cloudfront wait invalidation-completed \
                --distribution-id "$DISTRIBUTION_ID" \
                --id "$INVALIDATION_ID"
            log_success "CloudFront invalidation completed"
        else
            log_info "Invalidation is in progress. Check AWS Console for status."
        fi
    fi
else
    log_warning "Skipping CloudFront cache invalidation"
fi

# Deployment verification
if [ "$DRY_RUN" = false ]; then
    log_info "Performing deployment verification..."
    
    # Wait a moment for changes to propagate
    sleep 5
    
    # Test frontend URL
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" || echo "000")
    
    if [ "$HTTP_STATUS" = "200" ]; then
        log_success "Frontend is responding successfully"
    else
        log_warning "Frontend returned HTTP status: $HTTP_STATUS"
        log_warning "It may take a few minutes for changes to propagate"
    fi
    
    # Check if main bundle exists
    if aws s3 ls "s3://$S3_BUCKET/index.html" >/dev/null 2>&1; then
        log_success "Main files deployed successfully"
    else
        log_error "Main files not found in S3 bucket"
        exit 1
    fi
fi

# Deployment summary
echo
log_success "🚀 Frontend deployment completed!"
echo
echo "📊 Deployment Summary:"
echo "   Environment: $ENVIRONMENT"
echo "   S3 Bucket: $S3_BUCKET"
echo "   CloudFront: $DISTRIBUTION_ID"
echo "   Frontend URL: $FRONTEND_URL"
echo

if [ "$ENVIRONMENT" = "prod" ]; then
    echo "🎯 Production Deployment Checklist:"
    echo "   □ Test the application thoroughly"
    echo "   □ Monitor CloudWatch metrics"
    echo "   □ Check error rates and performance"
    echo "   □ Verify custom domain (if applicable)"
    echo "   □ Update DNS if needed"
    echo
fi

log_info "Deployment logs available in CloudWatch:"
log_info "  aws logs tail /aws/s3/$STACK_NAME-frontend --follow"

exit 0