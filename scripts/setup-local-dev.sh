#!/bin/bash

echo "🚀 Setting up CompliantGuard local development environment..."

# Create DynamoDB table locally (if using DynamoDB Local) or use AWS
echo "1. Setting up DynamoDB table: themisguard-users"

# Check if table exists
if aws dynamodb describe-table --table-name themisguard-users 2>/dev/null; then
    echo "✅ DynamoDB table 'themisguard-users' already exists"
else
    echo "📦 Creating DynamoDB table: themisguard-users"
    aws dynamodb create-table \
        --table-name themisguard-users \
        --attribute-definitions \
            AttributeName=user_id,AttributeType=S \
        --key-schema \
            AttributeName=user_id,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --tags Key=Environment,Value=development Key=Project,Value=CompliantGuard
    
    echo "⏳ Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name themisguard-users
    echo "✅ Table created successfully"
fi

echo ""
echo "2. Creating .env file for local development"

# Create backend .env file
cat > backend/.env << EOF
# Environment
ENVIRONMENT=development

# AWS Configuration
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=themisguard-scans
S3_BUCKET_NAME=themisguard-reports

# JWT Configuration (change in production)
JWT_SECRET_KEY=dev-secret-key-change-in-production-$(date +%s)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# GCP Configuration (optional for local dev)
# GCP_PROJECT_ID=your-project-id
# GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Stripe Configuration (use test keys)
STRIPE_SECRET_KEY=sk_test_your_test_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
EOF

echo "✅ Backend .env file created"

# Create frontend .env file
cat > frontend/.env.development << EOF
# API URL for local development
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development

# Google OAuth (optional)
# VITE_GOOGLE_CLIENT_ID=your-google-client-id
EOF

echo "✅ Frontend .env.development file created"

echo ""
echo "3. Installing Python dependencies"
cd backend
pip install -r requirements.txt
pip install uvicorn  # For local development server
cd ..

echo ""
echo "4. Installing Node.js dependencies"
cd frontend
npm install
cd ..

echo ""
echo "📋 Next steps:"
echo ""
echo "🔧 Start the backend (in backend/ directory):"
echo "   cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🎨 Start the frontend (in frontend/ directory):"
echo "   cd frontend && npm run dev"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🐛 Monitor logs:"
echo "   Backend: Check terminal output from uvicorn"
echo "   Frontend: Check browser developer tools console"
echo "   DynamoDB: AWS CloudWatch logs (if using AWS DynamoDB)"
echo ""
echo "✅ Local development environment setup complete!"