# AWS Deployment Testing Guide

Test the deployed CompliantGuard system with real GCP credentials for compliance scanning.

## 🎯 Overview

This guide helps you:
1. **Create test users** in the deployed AWS environment
2. **Authenticate** with the live API
3. **Upload real GCP credentials** for scanning
4. **Run compliance scans** on actual GCP projects
5. **View scan results** and violations

## 🚀 Quick Start

```bash
# Run the interactive test suite
./scripts/aws-deployment-test.sh
```

## 📋 Step-by-Step Process

### 1. Create Test User

```bash
# Interactive user creation
python3 scripts/create-test-user.py
```

**What it does:**
- Creates user in deployed DynamoDB table
- Generates secure password hash
- Saves credentials for testing
- Creates test login script

**Example:**
```
Email: test@compliantguard.com
Password: testpass123
Environment: dev (or staging/prod)
```

### 2. Test Authentication

```bash
# Test login with deployed API
python3 test-login-dev.py  # Auto-generated script
```

**Verifies:**
- Login endpoint works
- JWT token generation
- Token verification
- Protected endpoint access

### 3. Upload Real GCP Credentials

```bash
# Interactive GCP testing
python3 scripts/test-gcp-scanning.py
```

**Process:**
1. Login with test user
2. Upload GCP service account JSON
3. Verify credential storage
4. List configured projects

### 4. Run Compliance Scan

**Triggers real scan:**
- Connects to your GCP project
- Analyzes resources for HIPAA compliance
- Generates violation report
- Saves results to DynamoDB

### 5. View Results

**Scan output includes:**
- Violation count by severity
- Resource-specific issues
- Compliance recommendations
- Detailed JSON report

## 🔧 Prerequisites

### AWS Setup
- AWS CLI configured
- Access to deployed environment
- DynamoDB tables exist
- Lambda functions deployed

### GCP Setup
- GCP service account JSON file
- Cloud Asset API enabled
- Appropriate IAM permissions

### Dependencies
```bash
pip install requests boto3
```

## 🌐 Environment URLs

**Development:**
```
API: https://your-dev-api.execute-api.us-east-1.amazonaws.com
DynamoDB: themisguard-dev-*
```

**Staging:**
```
API: https://api-staging.compliantguard.com
DynamoDB: themisguard-staging-*
```

**Production:**
```
API: https://api.compliantguard.com
DynamoDB: themisguard-prod-*
```

## 📊 Test Scenarios

### Scenario 1: First-Time User
1. Create test user
2. Upload GCP credentials
3. Run initial scan
4. Review violations

### Scenario 2: Existing User
1. Login with existing credentials
2. Add additional GCP project
3. Compare scan results
4. Track improvements

### Scenario 3: Multiple Projects
1. Upload multiple GCP projects
2. Run scans on each
3. Compare compliance scores
4. Generate summary reports

## 🧪 Sample Test Flow

```bash
# 1. Create user
python3 scripts/create-test-user.py
# Input: test@example.com, testpass123, dev

# 2. Test login
python3 test-login-dev.py
# Verifies: Authentication works

# 3. Run GCP scan
python3 scripts/test-gcp-scanning.py
# Input: path/to/service-account.json
# Output: Compliance report

# 4. Check results
cat compliance-report-project-12345678.json
```

## 🔍 Debugging

### Common Issues

**"Table not found":**
- Verify deployment completed
- Check environment name
- Ensure AWS credentials have access

**"Login failed":**
- Check API Gateway URL
- Verify user exists in DynamoDB
- Check password hash

**"GCP upload failed":**
- Validate service account JSON
- Check required permissions
- Verify project ID matches

**"Scan failed":**
- Ensure GCP API access
- Check service account permissions
- Verify network connectivity

### Debug Commands

```bash
# Check deployment status
aws cloudformation describe-stacks --stack-name themisguard-api-dev

# List DynamoDB tables
aws dynamodb list-tables --query "TableNames[?contains(@, 'themisguard')]"

# Check Lambda functions
aws lambda list-functions --query "Functions[?contains(FunctionName, 'themisguard')]"

# View CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/themisguard"
```

## 📈 Monitoring

### Metrics to Track
- Authentication success rate
- GCP credential upload success
- Scan completion rate
- Violation detection accuracy

### CloudWatch Dashboards
- API response times
- Error rates by endpoint
- DynamoDB read/write metrics
- Lambda execution duration

## 🔒 Security Notes

### Test User Security
- Use strong passwords
- Delete test users after testing
- Don't commit credentials to git
- Use least-privilege AWS access

### GCP Credentials
- Use dedicated test projects
- Limit service account permissions
- Don't share service account keys
- Rotate credentials regularly

## 🎯 Success Criteria

**Authentication:**
- ✅ User creation works
- ✅ Login returns valid JWT
- ✅ Protected endpoints accessible

**GCP Integration:**
- ✅ Credentials upload successfully
- ✅ Projects listed correctly
- ✅ Scans complete without errors

**Compliance Scanning:**
- ✅ Real violations detected
- ✅ Reports generated correctly
- ✅ Results saved to database

## 🚀 Production Readiness

After successful testing:
1. **Clean up test data** from DynamoDB
2. **Document scan accuracy** and performance
3. **Set up monitoring** and alerting
4. **Create user onboarding** documentation
5. **Deploy to production** environment

This testing approach ensures the deployed system works correctly with real GCP environments and can detect actual compliance violations!