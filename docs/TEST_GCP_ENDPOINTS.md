# GCP Endpoints Test Guide

## 🚀 Step 1: Start the Test Server

Run this command from the `backend` directory:

```bash
cd backend
python test_gcp_endpoint.py
```

**Expected output:**
```
🚀 Starting GCP Test API on port 8001...
📝 Test endpoints:
  GET  http://localhost:8001/api/v1/gcp/projects
  POST http://localhost:8001/api/v1/gcp/credentials/upload
  DELETE http://localhost:8001/api/v1/gcp/projects/{project_id}/credentials

💡 Change frontend API URL to http://localhost:8001 to test

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

If you get a `ModuleNotFoundError`, install the dependencies:
```bash
pip install fastapi uvicorn python-multipart
```

## 🧪 Step 2: Test the Endpoints

Once the server is running, test these in a new terminal:

### Test 1: List Projects
```bash
curl -X GET http://localhost:8001/api/v1/gcp/projects
```
**Expected:** `[{"project_id":"test-project-1","service_account_email":"test@test-project-1.iam.gserviceaccount.com","status":"active","created_at":"2024-01-01T00:00:00Z","last_used":"2024-01-02T00:00:00Z"}]`

### Test 2: Root Endpoint
```bash
curl -X GET http://localhost:8001/
```
**Expected:** `{"message":"GCP Test API","status":"running"}`

### Test 3: Upload Endpoint (should fail with validation error, not 404)
```bash
curl -X POST http://localhost:8001/api/v1/gcp/credentials/upload
```
**Expected:** `422 Unprocessable Entity` (validation error - this is good!)

## 🎨 Step 3: Test with Frontend

1. **Restart the frontend** (if running):
   ```bash
   cd frontend
   npm run dev
   ```

2. **Visit the Scan page:** http://localhost:5173/app/scan

3. **Expected behavior:**
   - Should show "No connected projects" instead of an error
   - "Connect GCP Project" button should be visible
   - Clicking it opens the onboarding modal

4. **Test the onboarding:**
   - Go through the 3-step modal
   - In Step 3, try uploading a JSON file
   - Should show success message

## 🔧 Step 4: Create Test JSON File

Create a test service account file for upload testing:

```bash
cat > test-service-account.json << 'EOF'
{
  "type": "service_account",
  "project_id": "test-project-123",
  "private_key_id": "test-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----\n",
  "client_email": "test@test-project-123.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
EOF
```

## ✅ Success Indicators

**Test Server Working:**
- Server starts without errors on port 8001
- Curl tests return expected responses (not 404s)
- Frontend loads without API errors

**Frontend Integration Working:**
- Scan page shows project connection interface
- Onboarding modal opens and progresses through steps
- File upload in Step 3 shows success (even with test data)
- Settings page shows GCP Projects tab

## 🐛 Troubleshooting

**Port 8001 already in use:**
```bash
# Change port in test_gcp_endpoint.py line 110:
uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)

# Update frontend .env:
VITE_API_URL=http://localhost:8002
```

**Dependencies missing:**
```bash
pip install fastapi uvicorn python-multipart google-auth google-api-python-client
```

**Frontend not updating:**
- Restart the frontend dev server
- Clear browser cache (hard refresh)
- Check browser console for errors

Once this test server is working, we'll know the frontend integration is perfect and can focus on fixing the main backend caching issue!