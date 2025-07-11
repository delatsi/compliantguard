#!/bin/bash

# ThemisGuard Development Startup Script
echo "🚀 Starting ThemisGuard Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites found${NC}"

# Setup backend
echo -e "${BLUE}🐍 Setting up backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating backend .env file..."
    cat > .env << EOF
ENVIRONMENT=development
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=themisguard-dev-scans
S3_BUCKET_NAME=themisguard-dev-reports
JWT_SECRET_KEY=development-secret-key-change-in-production
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=../themisguard-key.json
EOF
fi

cd ..

# Setup frontend
echo -e "${BLUE}⚛️  Setting up frontend...${NC}"
cd frontend

# Install npm dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating frontend .env file..."
    cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_APP_ENV=development
EOF
fi

cd ..

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}🚀 Starting servers...${NC}"
echo ""
echo -e "${BLUE}Backend will be available at: http://localhost:8000${NC}"
echo -e "${BLUE}Frontend will be available at: http://localhost:5173${NC}"
echo -e "${BLUE}API docs will be available at: http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Start backend in background
cd backend
source venv/bin/activate
python dev.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend in background
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID