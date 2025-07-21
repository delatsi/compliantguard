# Local Testing Suite

**Zero-dependency testing for CompliantGuard**

## 🚀 Quick Start

```bash
# Start the test server (Terminal 1)
python3 server.py

# Run all tests (Terminal 2)  
python3 test_all.py
```

## 📋 What's Included

- **server.py** - Simple HTTP server with all API endpoints
- **test_all.py** - Complete test suite for authentication & GCP integration

## ✅ Test Coverage

- User registration and login
- JWT token authentication
- GCP credential upload and validation
- Project listing and management
- Credential revocation
- Error handling and edge cases

## 🔑 Test Credentials

- **Email:** `test@example.com`
- **Password:** `testpass123`

## 🎯 Features

- **Zero dependencies** - Uses only Python standard library
- **In-memory storage** - No database required
- **CORS enabled** - Works with frontend development
- **Complete API** - All endpoints implemented
- **Proper error handling** - Realistic error responses

## 📊 Expected Output

When tests pass, you'll see:
```
✅ All authentication and GCP integration features working
✅ User registration and login
✅ JWT token authentication  
✅ GCP credential upload and validation
✅ Project listing and status checking
✅ Credential revocation
```

Perfect for rapid development and CI/CD pipelines!