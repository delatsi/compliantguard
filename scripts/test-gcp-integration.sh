#!/bin/bash

echo "🔧 Testing GCP Integration Locally"
echo "=================================="
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

# Check if we're in the right directory
if [[ ! -f "backend/main.py" ]]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

# Step 1: Check prerequisites
log_section "Checking Prerequisites"

# Check Python environment
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "✅ Python $PYTHON_VERSION found"
else
    log_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check if backend dependencies are installed
if [[ ! -d "backend/venv" ]]; then
    log_warning "Virtual environment not found. Creating one..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    log_info "✅ Virtual environment found"
fi

# Check AWS CLI and credentials (use configured environment)
log_info "Checking AWS CLI using configured environment..."
source /opt/env/garmin/bin/activate

if command -v aws &> /dev/null; then
    log_info "✅ AWS CLI found"
    
    # Check AWS credentials
    if aws sts get-caller-identity &> /dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
        log_info "✅ AWS credentials configured (Account: $ACCOUNT_ID)"
    else
        log_error "AWS credentials not configured. Please run 'aws configure'"
        exit 1
    fi
else
    log_error "AWS CLI not found. Please install AWS CLI"
    exit 1
fi

echo ""

# Step 2: Check/Create DynamoDB table
log_section "Setting up DynamoDB Table"

TABLE_NAME="compliantguard-gcp-credentials"
REGION="us-east-1"

if aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" &> /dev/null; then
    log_info "✅ DynamoDB table '$TABLE_NAME' exists"
else
    log_warning "DynamoDB table '$TABLE_NAME' not found. Creating..."
    
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions \
            AttributeName=user_id,AttributeType=S \
            AttributeName=project_id,AttributeType=S \
        --key-schema \
            AttributeName=user_id,KeyType=HASH \
            AttributeName=project_id,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    
    log_info "⏳ Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
    log_info "✅ DynamoDB table created successfully"
fi

# Step 3: Check/Create KMS key
log_section "Setting up KMS Key"

KMS_KEY_ALIAS="alias/compliantguard-gcp-credentials"

if aws kms describe-key --key-id "$KMS_KEY_ALIAS" --region "$REGION" &> /dev/null; then
    log_info "✅ KMS key '$KMS_KEY_ALIAS' exists"
else
    log_warning "KMS key '$KMS_KEY_ALIAS' not found. Creating..."
    
    KEY_ID=$(aws kms create-key \
        --description "CompliantGuard GCP Credentials Encryption Key (Local Testing)" \
        --key-usage ENCRYPT_DECRYPT \
        --key-spec SYMMETRIC_DEFAULT \
        --region "$REGION" \
        --query 'KeyMetadata.KeyId' \
        --output text)
    
    aws kms create-alias \
        --alias-name "$KMS_KEY_ALIAS" \
        --target-key-id "$KEY_ID" \
        --region "$REGION"
    
    log_info "✅ KMS key created successfully"
fi

echo ""

# Step 4: Create test environment file
log_section "Creating Test Environment"

cat > backend/.env.test << EOF
# Test Environment for GCP Integration
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=compliantguard-gcp-credentials
KMS_KEY_ALIAS=alias/compliantguard-gcp-credentials
JWT_SECRET_KEY=test-secret-key-for-local-development
ENVIRONMENT=test
EOF

log_info "✅ Test environment file created: backend/.env.test"

# Step 5: Create sample service account for testing
log_section "Creating Sample Test Data"

cat > test-service-account-sample.json << 'EOF'
{
  "type": "service_account",
  "project_id": "your-gcp-project-id",
  "private_key_id": "sample-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nSAMPLE-PRIVATE-KEY-CONTENT\n-----END PRIVATE KEY-----\n",
  "client_email": "test-sa@your-gcp-project-id.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-sa%40your-gcp-project-id.iam.gserviceaccount.com"
}
EOF

log_info "✅ Sample service account file created: test-service-account-sample.json"
log_warning "⚠️  This is a sample file. Replace with your actual service account key for testing."

echo ""

# Step 6: Create test script
log_section "Creating Test Script"

cat > test_gcp_local.py << 'EOF'
#!/usr/bin/env python3
"""
Local GCP Integration Test Script
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.services.gcp_credential_service import GCPCredentialService
from backend.core.config import Settings

# Mock settings for testing
class TestSettings:
    AWS_REGION = "us-east-1"
    DYNAMODB_TABLE_NAME = "compliantguard-gcp-credentials"
    KMS_KEY_ALIAS = "alias/compliantguard-gcp-credentials"

# Override settings
import backend.core.config
backend.core.config.settings = TestSettings()

async def test_gcp_integration():
    """Test GCP credential storage and retrieval"""
    print("🧪 Testing GCP Integration")
    print("==========================")
    
    # Initialize service
    service = GCPCredentialService()
    
    # Test user ID
    test_user_id = "test-user-123"
    test_project_id = "test-project-456"
    
    # Sample service account (you can replace with real one)
    sample_service_account = {
        "type": "service_account",
        "project_id": test_project_id,
        "private_key_id": "sample-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nSAMPLE\n-----END PRIVATE KEY-----\n",
        "client_email": f"test-sa@{test_project_id}.iam.gserviceaccount.com",
        "client_id": "123456789012345678901",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/test-sa%40{test_project_id}.iam.gserviceaccount.com"
    }
    
    try:
        print("\n1. Testing credential storage...")
        
        # Note: This will fail validation because it's a sample key
        # For real testing, use an actual service account key
        try:
            result = await service.store_credentials(
                user_id=test_user_id,
                project_id=test_project_id,
                service_account_json=sample_service_account
            )
            print(f"✅ Credentials stored successfully: {result}")
        except Exception as e:
            print(f"⚠️  Credential storage failed (expected for sample key): {e}")
            print("   This is normal for the sample key. Use a real service account key to test fully.")
        
        print("\n2. Testing project listing...")
        projects = await service.list_user_projects(test_user_id)
        print(f"✅ Found {len(projects)} projects for user")
        
        for project in projects:
            print(f"   - {project['project_id']}: {project['service_account_email']}")
        
        if projects:
            print("\n3. Testing credential retrieval...")
            first_project = projects[0]
            try:
                creds = await service.get_credentials(
                    user_id=test_user_id,
                    project_id=first_project['project_id']
                )
                print(f"✅ Retrieved credentials for {first_project['project_id']}")
                print(f"   Service account: {creds.get('client_email')}")
            except Exception as e:
                print(f"⚠️  Credential retrieval failed: {e}")
        
        print("\n🎉 GCP integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gcp_integration())
EOF

chmod +x test_gcp_local.py
log_info "✅ Test script created: test_gcp_local.py"

echo ""

# Step 7: Create FastAPI test server
log_section "Creating Test Server"

cat > run_test_server.py << 'EOF'
#!/usr/bin/env python3
"""
Local FastAPI Test Server for GCP Integration
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Set environment variables
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['DYNAMODB_TABLE_NAME'] = 'compliantguard-gcp-credentials'
os.environ['KMS_KEY_ALIAS'] = 'alias/compliantguard-gcp-credentials'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-local-development'
os.environ['ENVIRONMENT'] = 'test'

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your backend modules
from backend.routes.gcp import router as gcp_router
from backend.routes.auth import router as auth_router

app = FastAPI(title="CompliantGuard GCP Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(gcp_router, prefix="/api/v1/gcp", tags=["gcp"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "GCP test server running"}

@app.get("/")
async def root():
    return {
        "message": "CompliantGuard GCP Test Server",
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth",
            "gcp": "/api/v1/gcp"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting CompliantGuard GCP Test Server")
    print("==========================================")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("GCP Endpoints: http://localhost:8000/api/v1/gcp")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
EOF

chmod +x run_test_server.py
log_info "✅ Test server created: run_test_server.py"

echo ""

# Step 8: Create test curl commands
log_section "Creating Test Commands"

cat > test_gcp_api.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing GCP API Endpoints"
echo "============================"

BASE_URL="http://localhost:8000"

# Test 1: Health check
echo "1. Testing health check..."
curl -s "$BASE_URL/health" | jq '.'

echo -e "\n2. Testing root endpoint..."
curl -s "$BASE_URL/" | jq '.'

echo -e "\n3. Testing GCP projects list (will fail without auth)..."
curl -s "$BASE_URL/api/v1/gcp/projects" | jq '.'

echo -e "\n4. To test with authentication, you need to:"
echo "   a) First register/login to get a JWT token"
echo "   b) Then use the token in the Authorization header"
echo "   c) Example: curl -H 'Authorization: Bearer <token>' $BASE_URL/api/v1/gcp/projects"

echo -e "\n5. Sample credential upload (with auth token):"
echo "   curl -X POST $BASE_URL/api/v1/gcp/credentials/upload \\"
echo "        -H 'Authorization: Bearer <token>' \\"
echo "        -F 'project_id=your-project-id' \\"
echo "        -F 'file=@your-service-account.json'"

echo -e "\n✅ Test commands ready!"
EOF

chmod +x test_gcp_api.sh
log_info "✅ Test commands created: test_gcp_api.sh"

echo ""

# Step 9: Instructions
log_section "Testing Instructions"

echo "🎯 How to test GCP integration locally:"
echo "======================================"
echo ""
echo "1. 📋 Prerequisites Setup:"
echo "   ✅ DynamoDB table: $TABLE_NAME"
echo "   ✅ KMS key: $KMS_KEY_ALIAS"
echo "   ✅ AWS credentials configured"
echo ""
echo "2. 🔑 Get a real GCP service account key:"
echo "   - Go to GCP Console → IAM & Admin → Service Accounts"
echo "   - Create a new service account or use existing one"
echo "   - Add 'Cloud Asset Viewer' role"
echo "   - Download JSON key file"
echo ""
echo "3. 🧪 Test the integration:"
echo "   # Test basic integration"
echo "   python3 test_gcp_local.py"
echo ""
echo "   # Start test server"
echo "   python3 run_test_server.py"
echo ""
echo "   # Test API endpoints (in another terminal)"
echo "   ./test_gcp_api.sh"
echo ""
echo "4. 📤 Upload real credentials:"
echo "   curl -X POST http://localhost:8000/api/v1/gcp/credentials/upload \\"
echo "        -H 'Authorization: Bearer <jwt-token>' \\"
echo "        -F 'project_id=your-actual-project-id' \\"
echo "        -F 'file=@your-real-service-account.json'"
echo ""
echo "5. 🔍 Check what was stored:"
echo "   curl -H 'Authorization: Bearer <jwt-token>' \\"
echo "        http://localhost:8000/api/v1/gcp/projects"
echo ""

log_warning "⚠️  Security Notes:"
echo "- Never commit real service account keys to git"
echo "- Use test/sandbox GCP projects for testing"
echo "- The sample key will fail validation (this is expected)"
echo "- Real keys will be encrypted with KMS before storage"
echo ""

log_info "✅ Local GCP integration test setup complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Get a real GCP service account key"
echo "2. Run: python3 run_test_server.py"
echo "3. Test the endpoints with your real credentials"
echo "4. Check the encrypted storage in DynamoDB"
EOF