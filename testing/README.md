# CompliantGuard Testing Suite

This directory contains all testing tools and utilities for CompliantGuard development and integration testing.

## 📁 Directory Structure

```
testing/
├── local/           # Local development testing (no dependencies)
├── integration/     # Full integration testing (requires AWS/dependencies)
├── tools/          # Testing utilities and helpers
└── README.md       # This file
```

## 🚀 Quick Start

### Local Testing (Recommended - No Dependencies)
```bash
# Start simple test server
cd testing/local
python3 server.py

# Run complete test suite
python3 test_all.py
```

### Integration Testing (Requires AWS Setup)
```bash
# Set up AWS infrastructure
cd testing/integration
./setup_infrastructure.sh

# Run integration tests
python3 test_integration.py
```

## 🧪 Test Categories

### Local Testing
- **Zero dependencies** - Only uses Python standard library
- **In-memory storage** - No AWS required
- **Complete API coverage** - All endpoints tested
- **Authentication flow** - Registration, login, JWT verification
- **GCP integration** - Credential upload, project management

### Integration Testing  
- **Real AWS services** - DynamoDB, KMS, S3
- **End-to-end flows** - Full production-like testing
- **Infrastructure validation** - CloudFormation/SAM testing
- **Performance testing** - Load and stress testing

### Tools
- **Test data generators** - Create sample GCP credentials
- **Mock services** - Simulate external APIs
- **Validation utilities** - Schema and data validation
- **Development helpers** - Quick setup and teardown

## 📋 Test Credentials

**Local Testing:**
- Email: `test@example.com`
- Password: `testpass123`

**Integration Testing:**
- Uses real AWS accounts
- Configured via environment variables

## 🔧 Available Scripts

| Script | Purpose | Dependencies |
|--------|---------|--------------|
| `local/server.py` | Simple test server | None |
| `local/test_all.py` | Complete local test suite | None |
| `integration/setup_infrastructure.sh` | AWS infrastructure setup | AWS CLI |
| `integration/test_integration.py` | Full integration tests | FastAPI, boto3 |
| `tools/generate_test_data.py` | Generate test data | None |

## 🎯 Testing Strategy

1. **Start with local testing** - Validate core logic without dependencies
2. **Move to integration testing** - Test with real AWS services
3. **Use tools as needed** - Generate data, validate schemas, etc.

## 📊 Test Coverage

- ✅ Authentication (registration, login, JWT)
- ✅ GCP credential management (upload, list, revoke)
- ✅ Project status checking
- ✅ Error handling and validation
- ✅ CORS and security headers
- ✅ API documentation compliance

## 🛠️ Maintenance

- Keep test files organized by category
- Update tests when API changes
- Maintain backward compatibility
- Document any new testing approaches