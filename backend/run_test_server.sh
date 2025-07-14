#!/bin/bash

echo "🚀 Starting GCP Test Server..."
echo "================================"

# Check if we're in the right directory
if [ ! -f "test_gcp_endpoint.py" ]; then
    echo "❌ Error: Please run this from the backend directory"
    echo "   cd backend && ./run_test_server.sh"
    exit 1
fi

# Check if FastAPI is available
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ FastAPI not found. Installing dependencies..."
    pip install fastapi uvicorn python-multipart
fi

echo "📝 Test endpoints will be available at:"
echo "  GET  http://localhost:8001/api/v1/gcp/projects"
echo "  POST http://localhost:8001/api/v1/gcp/credentials/upload"
echo ""
echo "💡 Update your frontend API URL to: http://localhost:8001"
echo ""
echo "🔄 Starting server..."
echo ""

python test_gcp_endpoint.py