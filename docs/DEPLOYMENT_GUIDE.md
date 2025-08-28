# CompliantGuard Production Deployment Guide

## Overview

This guide provides a systematic approach to deploying CompliantGuard with proper version tracking, security validation, and environment consistency.

## 🚨 Pre-Deployment Security Requirements

**CRITICAL:** Address these security issues before any production deployment:

### 1. Remove Hardcoded Credentials
```bash
# Search and remove all hardcoded credentials
grep -r "SecureAdmin123" . --exclude-dir=docs
grep -r "admin@themisguard.com.*password" . --exclude-dir=docs

# Files to update:
# - frontend/src/contexts/AdminContext.jsx
# - frontend/src/pages/AdminLogin.jsx
```

### 2. Implement Real Authentication
Replace mock authentication in:
- `AdminContext.jsx` - Remove hardcoded login logic
- `AuthContext.jsx` - Ensure all authentication goes through backend
- Backend - Implement proper password hashing and verification

### 3. Secure JWT Configuration
```bash
# Generate secure JWT secret (minimum 256 bits)
openssl rand -base64 32

# Store in AWS Secrets Manager (not environment variables)
aws secretsmanager create-secret \
  --name "compliantguard/jwt-secret" \
  --description "JWT signing secret for CompliantGuard" \
  --secret-string "$(openssl rand -base64 32)"
```

## 🔧 Deployment Tools

### 1. Version Management
```bash
# Generate deployment info before each deployment
./scripts/generate-deployment-info.sh staging
./scripts/generate-deployment-info.sh production

# This creates:
# - frontend/public/deployment-info.json
# - backend/deployment-info.json
```

### 2. Database Migrations
```bash
# Run database migrations
python scripts/database-schema-manager.py migrate staging
python scripts/database-schema-manager.py migrate production

# Check migration status
python scripts/database-schema-manager.py status production
```

### 3. Environment Validation
```bash
# Validate environment before deployment
python scripts/validate-environment.py staging
python scripts/validate-environment.py production

# Must return exit code 0 before proceeding
```

## 📋 Deployment Checklist

### Pre-Deployment (Every Release)

- [ ] **Security Audit Complete**
  - [ ] No hardcoded credentials in code
  - [ ] Authentication endpoints secured
  - [ ] JWT secrets in AWS Secrets Manager
  - [ ] Security headers configured
  
- [ ] **Code Quality**
  - [ ] All tests passing (`npm test`)
  - [ ] Linting clean (`npm run lint`)
  - [ ] Build successful (`npm run build`)
  - [ ] Backend tests passing

- [ ] **Version Management**
  - [ ] Deployment info generated
  - [ ] Git tagged with version
  - [ ] Change log updated

- [ ] **Database**
  - [ ] Migrations tested in staging
  - [ ] Data backup completed (if applicable)
  - [ ] Migration rollback plan ready

### Staging Deployment

- [ ] **Environment Setup**
  ```bash
  # Validate staging environment
  python scripts/validate-environment.py staging
  
  # Run migrations
  python scripts/database-schema-manager.py migrate staging
  
  # Generate deployment info
  ./scripts/generate-deployment-info.sh staging
  ```

- [ ] **Deploy Backend**
  ```bash
  # Using GitHub Actions (recommended)
  git push origin main
  
  # Or manual deployment
  sam build && sam deploy --stack-name compliantguard-staging
  ```

- [ ] **Deploy Frontend**
  ```bash
  # Build with staging config
  VITE_API_URL=https://82orcbhmf6.execute-api.us-east-1.amazonaws.com/Prod npm run build
  
  # Deploy to S3
  aws s3 sync frontend/dist/ s3://compliantguard-frontend-staging/ --delete
  
  # Invalidate CloudFront
  aws cloudfront create-invalidation --distribution-id YOUR_STAGING_ID --paths "/*"
  ```

- [ ] **Post-Deployment Validation**
  ```bash
  # Test deployment endpoints
  curl https://staging.compliantguard.com/health
  curl https://staging.compliantguard.com/deployment-info
  
  # Verify version sync
  # Check frontend and backend git hashes match
  ```

### Production Deployment

- [ ] **Additional Production Checks**
  - [ ] Staging thoroughly tested
  - [ ] Security scan completed
  - [ ] Business stakeholder approval
  - [ ] Maintenance window scheduled
  - [ ] Rollback plan documented

- [ ] **Production Deploy**
  ```bash
  # Final validation
  python scripts/validate-environment.py production
  
  # Database migrations (if needed)
  python scripts/database-schema-manager.py migrate production
  
  # Generate production deployment info
  ./scripts/generate-deployment-info.sh production
  
  # Deploy (same process as staging)
  ```

- [ ] **Post-Production Validation**
  - [ ] Health checks passing
  - [ ] Version sync confirmed
  - [ ] User authentication working
  - [ ] Key functionality tested
  - [ ] Monitoring alerts active

## 🔍 Deployment Verification

### Automated Verification
```bash
# Check deployment sync status
curl -s https://your-domain.com/deployment-info | jq '.git.shortHash'

# Compare with expected git hash
git rev-parse --short HEAD
```

### Manual Verification Checklist
- [ ] Login functionality works
- [ ] Admin dashboard accessible (with proper credentials)
- [ ] GCP scanning functional
- [ ] Reports generation working
- [ ] All navigation links functional

## 🚨 Rollback Procedures

### Frontend Rollback
```bash
# Get previous deployment from S3 versioning
aws s3api list-object-versions --bucket compliantguard-frontend-prod

# Restore previous version
aws s3 sync s3://compliantguard-frontend-prod-backup/v1.2.0/ s3://compliantguard-frontend-prod/ --delete

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id PROD_DISTRIBUTION_ID --paths "/*"
```

### Backend Rollback
```bash
# Use AWS Lambda versioning
aws lambda update-alias --function-name compliantguard-prod --name LIVE --function-version PREVIOUS_VERSION

# Or redeploy previous SAM stack
sam deploy --stack-name compliantguard-prod --parameter-overrides Version=1.2.0
```

### Database Rollback
```bash
# Only if migration rollback is available
python scripts/database-schema-manager.py rollback production --migration-id XXX
```

## 🔐 Security Hardening for Production

### 1. AWS Security
- [ ] IAM roles follow principle of least privilege
- [ ] S3 buckets have proper access policies
- [ ] CloudFront configured with security headers
- [ ] WAF rules configured (if applicable)

### 2. Application Security
- [ ] All secrets in AWS Secrets Manager
- [ ] Rate limiting configured
- [ ] CORS policies restrictive
- [ ] Error messages sanitized

### 3. Monitoring & Logging
- [ ] CloudWatch alarms configured
- [ ] Security audit logging enabled
- [ ] Failed login attempt monitoring
- [ ] Performance monitoring active

## 📊 Monitoring Production Health

### Key Metrics to Monitor
- [ ] API response times
- [ ] Error rates
- [ ] Authentication success/failure rates
- [ ] Database connection health
- [ ] Frontend load times

### Alerting Thresholds
- [ ] API error rate > 1%
- [ ] Response time > 2 seconds
- [ ] Failed authentication > 5/minute
- [ ] Database connection failures

## 🔄 CI/CD Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    tags: [ 'v*' ]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Validate Environment
        run: python scripts/validate-environment.py production
        
  deploy:
    needs: validate
    if: success()
    runs-on: ubuntu-latest
    steps:
      - name: Generate Deployment Info
        run: ./scripts/generate-deployment-info.sh production
      # ... deployment steps
```

## 📞 Emergency Contacts

- **Technical Lead:** [Your contact]
- **AWS Support:** [Support case link]
- **Security Team:** [Security contact]

## 📚 Related Documentation

- [Security Audit Report](SECURITY_AUDIT_REPORT.md)
- [Database Schema Documentation](database-schema.md)
- [API Documentation](api-docs.md)
- [Incident Response Plan](incident-response.md)

---

**Last Updated:** 2025-08-28  
**Next Review:** 2025-09-28