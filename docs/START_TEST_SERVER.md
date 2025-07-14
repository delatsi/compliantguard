# Start GCP Test Server

## Quick Commands

**Run these commands in your terminal:**

```bash
# Go to backend directory
cd /Users/delatsi/projects/compliantguard/backend

# Install dependencies (if needed)
pip install fastapi uvicorn python-multipart

# Start the test server
python test_gcp_endpoint.py
```

## Expected Output

You should see:
```
🚀 Starting GCP Test API on port 8001...
📝 Test endpoints:
  GET  http://localhost:8001/api/v1/gcp/projects
  POST http://localhost:8001/api/v1/gcp/credentials/upload
  DELETE http://localhost:8001/api/v1/gcp/projects/{project_id}/credentials

💡 Change frontend API URL to http://localhost:8001 to test

INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

## Quick Test

Once running, test in a new terminal:
```bash
curl http://localhost:8001/api/v1/gcp/projects
```

Should return:
```json
[{"project_id":"test-project-1","service_account_email":"test@test-project-1.iam.gserviceaccount.com","status":"active","created_at":"2024-01-01T00:00:00Z","last_used":"2024-01-02T00:00:00Z"}]
```

## If Dependencies Fail

Try these alternatives:
```bash
# Option 1: Use pip3
pip3 install fastapi uvicorn python-multipart

# Option 2: Use the same environment as your main backend
# If your main backend works, activate the same environment first

# Option 3: Check your Python environment
which python
python --version
```

## Frontend Testing

Once the test server is running:
1. Make sure your frontend .env file has: `VITE_API_URL=http://localhost:8001`
2. Restart your frontend: `cd frontend && npm run dev`
3. Visit: http://localhost:5173/app/scan
4. Should see "Connect GCP Project" interface instead of errors

**Copy and paste the commands above to start the test server!**