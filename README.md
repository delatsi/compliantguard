# ThemisGuard - HIPAA Compliance Scanner

A modern micro SaaS application for automated HIPAA compliance scanning of Google Cloud Platform infrastructure.

## 🏗️ Architecture

- **Backend**: FastAPI + AWS Lambda (Serverless)
- **Frontend**: React + Vite + TailwindCSS
- **Database**: DynamoDB + S3
- **Infrastructure**: AWS SAM CLI
- **Documentation**: Markdown

## 🚀 Local Development

### Prerequisites

- Python 3.9+
- Node.js 18+
- AWS CLI configured
- SAM CLI installed
- Docker (for SAM local testing)

### Backend Setup

1. **Create Python virtual environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables:**
```bash
# Create .env file in backend directory
cat > .env << EOF
ENVIRONMENT=development
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=themisguard-dev-scans
S3_BUCKET_NAME=themisguard-dev-reports
JWT_SECRET_KEY=your-secret-key-for-development
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=../themisguard-key.json
EOF
```

4. **Run FastAPI locally:**
```bash
# From backend directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000
- API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Create environment file:**
```bash
# Create .env file in frontend directory
cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_APP_ENV=development
EOF
```

3. **Start development server:**
```bash
npm run dev
```

The frontend will be available at: http://localhost:5173

## 🧪 Testing Locally

### 1. Backend API Testing

Test the health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 2. Mock Data for Development

Since the app requires AWS services, here's how to test without full AWS setup:

**Option A: Mock AWS Services**
Create a mock data file for testing:

```bash
# In backend directory
cat > mock_data.py << 'EOF'
# Mock data for development
MOCK_USER = {
    "user_id": "dev-user-123",
    "email": "dev@example.com",
    "first_name": "Dev",
    "last_name": "User"
}

MOCK_SCAN_RESULT = {
    "scan_id": "dev-scan-123",
    "project_id": "test-project",
    "violations_count": 5,
    "status": "completed"
}
EOF
```

**Option B: Use SAM Local**
```bash
# From project root
sam build
sam local start-api --port 3000
```

### 3. Frontend Testing

1. **Start both servers:**
   - Backend: `uvicorn main:app --reload --port 8000`
   - Frontend: `npm run dev`

2. **Test the flow:**
   - Visit http://localhost:5173
   - Navigate through landing page
   - Try login/register (will show errors without backend auth)
   - Access dashboard at http://localhost:5173/app

## 🔧 Development Configuration

### Backend Development Mode

For easier local development, modify the FastAPI app to skip authentication:

```python
# In backend/main.py, add this for development
import os

if os.getenv("ENVIRONMENT") == "development":
    # Skip auth for development
    async def mock_get_current_user():
        return {"user_id": "dev-user", "email": "dev@example.com"}
    
    # Replace the dependency in your routes
    app.dependency_overrides[get_current_user] = mock_get_current_user
```

### Database Setup (Optional for local testing)

If you want to test with real AWS services locally:

1. **Create DynamoDB tables locally:**
```bash
# Install DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local

# Create tables (in another terminal)
aws dynamodb create-table \
    --table-name themisguard-dev-scans \
    --attribute-definitions AttributeName=scan_id,AttributeType=S \
    --key-schema AttributeName=scan_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000
```

2. **Create S3 bucket locally:**
```bash
# Using LocalStack
docker run -p 4566:4566 localstack/localstack
```

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/api/v1/scan` | Trigger compliance scan |
| GET | `/api/v1/reports/{scan_id}` | Get specific report |
| GET | `/api/v1/reports` | List user reports |
| GET | `/api/v1/dashboard` | Dashboard data |

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors:**
   - Make sure backend is running on port 8000
   - Check CORS settings in FastAPI

2. **Import Errors:**
   - Ensure you're in the correct directory
   - Activate Python virtual environment
   - Install all requirements

3. **AWS Errors:**
   - Check AWS credentials
   - Verify region settings
   - Use mock data for development

4. **GCP Errors:**
   - Ensure service account key is in the right location
   - Check GCP project permissions

### Debug Mode

Enable debug logging:
```bash
# Backend
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug

# Frontend
export VITE_DEBUG=true
npm run dev
```

## 🚀 Deployment

### AWS Deployment
```bash
# Deploy backend
sam build
sam deploy --guided

# Deploy frontend (after backend is deployed)
npm run build
# Upload dist/ to S3 or Vercel/Netlify
```

### Environment Variables for Production

Set these in your deployment:
- `JWT_SECRET_KEY`: Strong secret key
- `GCP_PROJECT_ID`: Your GCP project
- `GOOGLE_APPLICATION_CREDENTIALS`: Service account key
- `AWS_REGION`: Your AWS region

## 📚 Next Steps

1. Implement user authentication endpoints
2. Add comprehensive error handling
3. Create detailed compliance reports
4. Add email notifications
5. Implement billing/subscription system
6. Add comprehensive testing suite
