# Backend GCP Endpoint Debug Guide

## Issue: GCP endpoints returning 404

The backend server is not picking up the GCP route changes. Here are the steps to fix this:

## 🔍 **Diagnosis**

The server at `localhost:8000` is returning different responses than expected, indicating it's running a cached or different version of the code.

## 🛠 **Solution Options**

### Option 1: Force Restart Backend (Recommended)

1. **Stop the backend completely:**
   ```bash
   # Find and kill all uvicorn processes
   pkill -f uvicorn
   pkill -f "python.*main"
   
   # Or if running in terminal, use Ctrl+C
   ```

2. **Install missing dependencies:**
   ```bash
   cd backend
   pip install google-auth==2.23.0 google-api-python-client==2.108.0 structlog==23.2.0
   ```

3. **Restart with explicit path:**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option 2: Use Test Server (Immediate Solution)

Run the standalone test server I created:

1. **Start test server:**
   ```bash
   cd backend
   python test_gcp_endpoint.py
   ```
   This will start a server on port 8001 with working GCP endpoints.

2. **Update frontend to use test server:**
   In `frontend/src/services/api.js`, temporarily change:
   ```javascript
   const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
   ```

### Option 3: Check for Multiple Servers

```bash
# Check what's running on port 8000
lsof -i :8000

# Check all Python processes
ps aux | grep python

# Check for uvicorn processes
ps aux | grep uvicorn
```

## 🧪 **Verification Tests**

After fixing, test these endpoints:

```bash
# Should return project list (empty array is fine)
curl -X GET http://localhost:8000/api/v1/gcp/projects

# Should return 422 (validation error, not 404)
curl -X POST http://localhost:8000/api/v1/gcp/credentials/upload

# Root endpoint should return updated message
curl -X GET http://localhost:8000/
```

## 🎯 **Expected Results**

- `GET /api/v1/gcp/projects` → `[]` (not 404)
- `POST /api/v1/gcp/credentials/upload` → 422 validation error (not 404)
- `GET /` → `{"message":"ThemisGuard HIPAA Compliance API","version":"1.0.0"}`

## 🚀 **Quick Test with Frontend**

Once endpoints work:
1. Go to the Scan page in the frontend
2. You should see "No connected projects" instead of an error
3. Click "Connect GCP Project" to test the onboarding modal
4. Upload a test JSON file to verify the upload endpoint

## 📝 **Common Issues**

1. **Virtual Environment**: Make sure you're in the right Python environment
2. **Working Directory**: Ensure you're running from the `backend` directory
3. **Port Conflicts**: Another service might be using port 8000
4. **File Changes**: The server might not be detecting file changes

## 🔧 **Nuclear Option: Clean Restart**

If all else fails:
1. Kill all Python processes: `pkill python`
2. Change to a different port: `uvicorn main:app --port 8002`
3. Update frontend API URL to match the new port

The GCP integration is ready to work - we just need to get the backend serving the correct endpoints!