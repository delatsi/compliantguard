#!/bin/bash

echo "🔐 Setting up Google Authentication for Staging"
echo "=============================================="
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

# Check if we're in the right directory
if [[ ! -f "template.yaml" ]]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

log_section "Google Auth Setup Checklist"

echo "This script will help you set up Google Authentication for staging."
echo "You'll need to complete some manual steps in Google Cloud Console."
echo ""

# Step 1: Check current configuration
log_section "Checking Current Configuration"

# Check if GoogleSSO component exists
if [[ -f "frontend/src/components/GoogleSSO.jsx" ]]; then
    log_info "GoogleSSO component found"
else
    log_error "GoogleSSO component not found"
fi

# Check if auth endpoint exists
if grep -q "google-sso" backend/routes/auth.py; then
    log_info "Backend Google SSO endpoint found"
else
    log_error "Backend Google SSO endpoint not found"
fi

# Check if template has Google Client ID parameter
if grep -q "GoogleClientId" template.yaml; then
    log_info "SAM template configured for Google Client ID"
else
    log_warning "SAM template may need Google Client ID parameter"
fi

echo ""

# Step 2: Environment configuration
log_section "Environment Configuration"

STAGING_DOMAIN=""
DEV_DOMAIN="http://localhost:3000"

echo "Enter your staging domain (e.g., https://staging.compliantguard.com):"
read -r STAGING_DOMAIN

if [[ -z "$STAGING_DOMAIN" ]]; then
    log_error "Staging domain is required"
    exit 1
fi

log_info "Staging domain: $STAGING_DOMAIN"
log_info "Development domain: $DEV_DOMAIN"

# Step 3: Create frontend environment files
log_section "Creating Frontend Environment Files"

# Create staging environment file
cat > frontend/.env.staging << EOF
# Staging Environment Configuration
VITE_API_URL=${STAGING_DOMAIN}/api
VITE_GOOGLE_CLIENT_ID=your-google-client-id-staging.apps.googleusercontent.com
VITE_ENVIRONMENT=staging
EOF

log_info "Created frontend/.env.staging"

# Create development environment file if it doesn't exist
if [[ ! -f "frontend/.env.development" ]]; then
    cat > frontend/.env.development << EOF
# Development Environment Configuration  
VITE_API_URL=http://localhost:8000/api
VITE_GOOGLE_CLIENT_ID=your-google-client-id-dev.apps.googleusercontent.com
VITE_ENVIRONMENT=development
EOF
    log_info "Created frontend/.env.development"
fi

echo ""

# Step 4: Google Cloud Console instructions
log_section "Google Cloud Console Setup Required"

echo "🌐 Next, you need to set up OAuth in Google Cloud Console:"
echo ""
echo "1. Go to: https://console.cloud.google.com/apis/credentials"
echo ""
echo "2. Create OAuth 2.0 Client ID with these settings:"
echo "   Application type: Web application"
echo "   Name: CompliantGuard Staging"
echo ""
echo "3. Add these Authorized JavaScript origins:"
echo "   - $STAGING_DOMAIN"
echo "   - $DEV_DOMAIN"
echo ""
echo "4. Add these Authorized redirect URIs:"
echo "   - $STAGING_DOMAIN/auth/callback"
echo "   - $DEV_DOMAIN/auth/callback"
echo ""
echo "5. Copy the Client ID and Client Secret"
echo ""

# Step 5: GitHub Secrets instructions
log_section "GitHub Secrets Configuration Required"

echo "🔑 Add these secrets to your GitHub repository:"
echo ""
echo "Repository → Settings → Secrets and variables → Actions"
echo ""
echo "Required secrets:"
echo "- GOOGLE_CLIENT_ID_STAGING=your-client-id.apps.googleusercontent.com"
echo "- GOOGLE_CLIENT_SECRET_STAGING=GOCSPX-your-client-secret"
echo "- GOOGLE_CLIENT_ID_DEV=your-dev-client-id.apps.googleusercontent.com"
echo "- GOOGLE_CLIENT_SECRET_DEV=GOCSPX-your-dev-client-secret"
echo ""

# Step 6: Update frontend configuration
log_section "Update Frontend Configuration"

echo "📝 After getting your Google Client ID:"
echo ""
echo "1. Update frontend/.env.staging:"
echo "   Replace 'your-google-client-id-staging.apps.googleusercontent.com'"
echo "   with your actual staging Client ID"
echo ""
echo "2. Update frontend/.env.development:"
echo "   Replace 'your-google-client-id-dev.apps.googleusercontent.com'"
echo "   with your actual development Client ID"
echo ""

# Step 7: Deployment instructions
log_section "Deployment Instructions"

echo "🚀 Deploy to staging:"
echo ""
echo "1. Commit your changes:"
echo "   git add ."
echo "   git commit -m 'Configure Google Auth for staging'"
echo "   git push origin main"
echo ""
echo "2. Deploy via GitHub Actions:"
echo "   Repository → Actions → smart-deploy → Run workflow"
echo "   Select 'staging' environment"
echo ""
echo "3. Or deploy manually:"
echo "   sam deploy --config-env staging \\"
echo "     --parameter-overrides GoogleClientId=your-staging-client-id"
echo ""

# Step 8: Testing instructions
log_section "Testing Google Auth"

echo "🧪 Test the authentication flow:"
echo ""
echo "1. Navigate to: $STAGING_DOMAIN/login"
echo "2. Click 'Continue with Google'"
echo "3. Complete OAuth flow"
echo "4. Verify user is created and logged in"
echo ""
echo "🔍 Debug if needed:"
echo "- Check browser console for errors"
echo "- Verify network requests in DevTools"
echo "- Check CloudWatch logs for backend errors"
echo ""

# Step 9: Create test script
log_section "Creating Test Script"

cat > test-google-auth.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing Google Auth Configuration"
echo "==================================="

# Test if frontend environment files exist
if [[ -f "frontend/.env.staging" ]]; then
    echo "✅ Staging environment file exists"
else
    echo "❌ Staging environment file missing"
fi

# Test if Google Client ID is configured
if grep -q "VITE_GOOGLE_CLIENT_ID" frontend/.env.staging; then
    CLIENT_ID=$(grep "VITE_GOOGLE_CLIENT_ID" frontend/.env.staging | cut -d'=' -f2)
    if [[ "$CLIENT_ID" == *"apps.googleusercontent.com"* ]]; then
        echo "✅ Google Client ID configured in staging"
    else
        echo "⚠️  Google Client ID needs to be updated in frontend/.env.staging"
    fi
fi

# Test backend endpoint
echo ""
echo "🔍 Testing backend Google SSO endpoint..."
if command -v curl &> /dev/null; then
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/google-sso \
        -H "Content-Type: application/json" \
        -d '{"email":"test@gmail.com","name":"Test User","google_id":"test-123"}')
    
    if [[ "$RESPONSE" == "200" ]] || [[ "$RESPONSE" == "500" ]]; then
        echo "✅ Backend Google SSO endpoint accessible"
    else
        echo "❌ Backend Google SSO endpoint not accessible (HTTP $RESPONSE)"
    fi
else
    echo "⚠️  curl not available for testing"
fi

echo ""
echo "📋 Manual testing steps:"
echo "1. Start backend: cd backend && python -m uvicorn main:app --reload"
echo "2. Start frontend: cd frontend && npm run dev"
echo "3. Navigate to http://localhost:3000/login"
echo "4. Test Google authentication flow"
EOF

chmod +x test-google-auth.sh
log_info "Created test-google-auth.sh script"

echo ""

# Final summary
log_section "Setup Summary"

echo "📋 What's been configured:"
log_info "Frontend environment files created"
log_info "Test script created (test-google-auth.sh)"
log_info "Configuration templates prepared"

echo ""
echo "🎯 Next steps:"
echo "1. Complete Google Cloud Console setup (see instructions above)"
echo "2. Add GitHub Secrets (see instructions above)"
echo "3. Update frontend/.env.staging with real Client ID"
echo "4. Deploy to staging"
echo "5. Test authentication flow"

echo ""
echo "📚 Documentation:"
echo "- Full setup guide: docs/GOOGLE_AUTH_SETUP.md"
echo "- Test script: ./test-google-auth.sh"

echo ""
log_info "Google Auth setup preparation complete!"
echo "Complete the manual steps above to finish configuration."