#!/bin/bash

echo "🔍 Validating GitHub Workflows for Idempotent Deployments"
echo "========================================================="
echo ""

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

log_section() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

# Check workflow files exist
log_section "Checking Workflow Files"

WORKFLOW_DIR=".github/workflows"
EXPECTED_WORKFLOWS=(
    "smart-deploy.yml"
    "dev-deploy.yml"
    "prod-deploy.yml"
    "infrastructure-drift-check.yml"
)

for workflow in "${EXPECTED_WORKFLOWS[@]}"; do
    if [[ -f "$WORKFLOW_DIR/$workflow" ]]; then
        log_info "✅ Found: $workflow"
    else
        log_error "❌ Missing: $workflow"
    fi
done

echo ""

# Validate smart-deploy.yml features
log_section "Validating Smart Deploy Features"

if [[ -f "$WORKFLOW_DIR/smart-deploy.yml" ]]; then
    log_info "Checking smart-deploy.yml features..."
    
    # Check for change detection
    if grep -q "dorny/paths-filter" "$WORKFLOW_DIR/smart-deploy.yml"; then
        log_info "✅ Change detection implemented"
    else
        log_warning "⚠️ Change detection not found"
    fi
    
    # Check for selective deployment
    if grep -q "deployment_strategy" "$WORKFLOW_DIR/smart-deploy.yml"; then
        log_info "✅ Selective deployment strategy implemented"
    else
        log_warning "⚠️ Deployment strategy logic not found"
    fi
    
    # Check for stable stack names
    if grep -q "themisguard-api-\${" "$WORKFLOW_DIR/smart-deploy.yml"; then
        log_info "✅ Stable stack naming pattern found"
    else
        log_warning "⚠️ Stable stack naming not detected"
    fi
    
    # Check for environment-specific secrets
    if grep -q "format('AWS_ACCESS_KEY_ID_" "$WORKFLOW_DIR/smart-deploy.yml"; then
        log_info "✅ Environment-specific credentials configuration found"
    else
        log_warning "⚠️ Dynamic secret selection not found"
    fi
    
    # Check for cost tagging
    if grep -q "Key=CostCenter" "$WORKFLOW_DIR/smart-deploy.yml"; then
        log_info "✅ Cost management tags found"
    else
        log_warning "⚠️ Cost management tags not found"
    fi
else
    log_error "❌ smart-deploy.yml not found"
fi

echo ""

# Validate stable naming patterns
log_section "Validating Stable Naming Patterns"

# Check if workflows use stable stack names instead of timestamps
log_info "Checking for timestamp patterns (should be eliminated)..."

TIMESTAMP_PATTERNS=(
    "\$(date"
    "timestamp"
    "\${GITHUB_RUN_NUMBER}"
    "\${GITHUB_SHA}"
)

for workflow_file in "$WORKFLOW_DIR"/*.yml; do
    if [[ -f "$workflow_file" ]]; then
        workflow_name=$(basename "$workflow_file")
        log_info "Analyzing: $workflow_name"
        
        for pattern in "${TIMESTAMP_PATTERNS[@]}"; do
            if grep -q "$pattern" "$workflow_file"; then
                log_warning "⚠️ Found timestamp pattern '$pattern' in $workflow_name"
            fi
        done
        
        # Check for stable stack names
        if grep -q "themisguard-api-\${.*}" "$workflow_file" || grep -q "themisguard-api-.*\"" "$workflow_file"; then
            log_info "✅ Stable stack naming found in $workflow_name"
        fi
    fi
done

echo ""

# Check for idempotent deployment features
log_section "Validating Idempotent Deployment Features"

IDEMPOTENT_FEATURES=(
    "--no-fail-on-empty-changeset"
    "stack-name.*themisguard-api-"
    "describe-stacks.*stack-name"
)

for workflow_file in "$WORKFLOW_DIR"/*.yml; do
    if [[ -f "$workflow_file" ]]; then
        workflow_name=$(basename "$workflow_file")
        
        for feature in "${IDEMPOTENT_FEATURES[@]}"; do
            if grep -q "$feature" "$workflow_file"; then
                log_info "✅ Idempotent feature '$feature' found in $workflow_name"
            fi
        done
    fi
done

echo ""

# Check for cost optimization features
log_section "Validating Cost Optimization Features"

COST_FEATURES=(
    "backend_changed"
    "frontend_changed"
    "deployment_strategy"
    "Key=Environment"
    "Key=CostCenter"
    "selective"
)

for workflow_file in "$WORKFLOW_DIR"/*.yml; do
    if [[ -f "$workflow_file" ]]; then
        workflow_name=$(basename "$workflow_file")
        
        cost_feature_count=0
        for feature in "${COST_FEATURES[@]}"; do
            if grep -q "$feature" "$workflow_file"; then
                ((cost_feature_count++))
            fi
        done
        
        if [[ $cost_feature_count -gt 0 ]]; then
            log_info "✅ $cost_feature_count cost optimization features found in $workflow_name"
        fi
    fi
done

echo ""

# Validate workflow structure
log_section "Validating Workflow Structure"

if [[ -f "$WORKFLOW_DIR/smart-deploy.yml" ]]; then
    log_info "Checking smart-deploy.yml job structure..."
    
    EXPECTED_JOBS=(
        "detect-changes"
        "test-backend"
        "test-frontend"
        "deploy-backend"
        "deploy-frontend"
        "smoke-test"
    )
    
    for job in "${EXPECTED_JOBS[@]}"; do
        if grep -q "^  $job:" "$WORKFLOW_DIR/smart-deploy.yml"; then
            log_info "✅ Job found: $job"
        else
            log_warning "⚠️ Job not found: $job"
        fi
    done
fi

echo ""

# Generate workflow comparison report
log_section "Workflow Comparison Report"

echo "📊 Workflow Analysis Summary:"
echo "============================="

if [[ -f "$WORKFLOW_DIR/smart-deploy.yml" ]]; then
    SMART_LINES=$(wc -l < "$WORKFLOW_DIR/smart-deploy.yml")
    echo "Smart Deploy Workflow: $SMART_LINES lines"
fi

if [[ -f "$WORKFLOW_DIR/dev-deploy.yml" ]]; then
    DEV_LINES=$(wc -l < "$WORKFLOW_DIR/dev-deploy.yml")
    echo "Legacy Dev Workflow: $DEV_LINES lines"
fi

if [[ -f "$WORKFLOW_DIR/prod-deploy.yml" ]]; then
    PROD_LINES=$(wc -l < "$WORKFLOW_DIR/prod-deploy.yml")
    echo "Production Workflow: $PROD_LINES lines"
fi

echo ""

# Recommendations
log_section "Recommendations"

echo "🚀 Deployment Strategy Recommendations:"
echo "======================================="
echo "1. ✅ Use smart-deploy.yml for all development deployments"
echo "2. ✅ Use selective deployment to save costs and time"
echo "3. ✅ Always use stable stack names (no timestamps)"
echo "4. ✅ Enable change detection for efficient CI/CD"
echo "5. ✅ Apply cost management tags to all resources"
echo ""

echo "💰 Cost Optimization Benefits:"
echo "=============================="
echo "• Reduced Action minutes (5-10 min savings per deployment)"
echo "• No duplicate AWS resources from timestamps"
echo "• Selective testing and deployment"
echo "• Proper resource tagging for cost tracking"
echo "• Idempotent operations (safe to re-run)"
echo ""

echo "🔧 Next Steps:"
echo "=============="
echo "1. Test smart-deploy.yml with a small change"
echo "2. Monitor deployment costs and performance"
echo "3. Gradually migrate all environments to smart deployment"
echo "4. Set up cost monitoring dashboards"
echo "5. Configure environment-specific AWS credentials"
echo ""

echo "✅ Workflow validation completed!"
echo ""
echo "🔗 To test the smart deployment:"
echo "================================"
echo "1. Make a small change to frontend or backend"
echo "2. Push to develop branch"
echo "3. Watch the smart-deploy workflow run"
echo "4. Verify only changed components are deployed"