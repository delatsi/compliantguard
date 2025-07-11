# GitHub Actions CI/CD Setup Guide

## 🚀 **Quick Setup Checklist**

### **Required GitHub Secrets**

Add these secrets in your GitHub repository settings (`Settings` → `Secrets and variables` → `Actions`):

#### **Development Environment**
```bash
AWS_ACCESS_KEY_ID_DEV=AKIA...
AWS_SECRET_ACCESS_KEY_DEV=...
```

#### **Production Environment**  
```bash
AWS_ACCESS_KEY_ID_PROD=AKIA...
AWS_SECRET_ACCESS_KEY_PROD=...
```

### **Optional Secrets (for enhanced features)**
```bash
CODECOV_TOKEN=...           # For code coverage reporting
SLACK_WEBHOOK_URL=...       # For deployment notifications
```

---

## 🔧 **AWS IAM Setup**

### **Development IAM Policy**
Create an IAM user with this policy for development deployments:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:*",
                "lambda:*",
                "apigateway:*",
                "dynamodb:*",
                "s3:*",
                "iam:*",
                "logs:*",
                "events:*",
                "cognito-identity:*",
                "cognito-idp:*",
                "kms:*",
                "ssm:*",
                "cloudfront:*",
                "route53:*"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:RequestedRegion": "us-east-1"
                }
            }
        }
    ]
}
```

### **Production IAM Policy (More Restrictive)**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStackResource",
                "cloudformation:DescribeStackResources",
                "cloudformation:GetTemplate",
                "cloudformation:List*",
                "cloudformation:UpdateStack",
                "cloudformation:CreateStack",
                "cloudformation:DeleteStack"
            ],
            "Resource": [
                "arn:aws:cloudformation:us-east-1:*:stack/themisguard-*/*",
                "arn:aws:cloudformation:us-east-1:*:stack/sam-*/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "lambda:GetFunction",
                "lambda:CreateFunction",
                "lambda:DeleteFunction",
                "lambda:ListFunctions",
                "lambda:GetFunctionConfiguration",
                "lambda:AddPermission",
                "lambda:RemovePermission",
                "lambda:CreateAlias",
                "lambda:UpdateAlias",
                "lambda:GetAlias",
                "lambda:ListAliases"
            ],
            "Resource": "arn:aws:lambda:us-east-1:*:function:themisguard-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:PutObjectAcl",
                "s3:GetBucketLocation"
            ],
            "Resource": [
                "arn:aws:s3:::themisguard-*",
                "arn:aws:s3:::themisguard-*/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudfront:CreateInvalidation",
                "cloudfront:GetInvalidation",
                "cloudfront:ListInvalidations",
                "cloudfront:GetDistribution",
                "cloudfront:GetDistributionConfig"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateBackup",
                "dynamodb:DescribeBackup",
                "dynamodb:ListBackups",
                "dynamodb:DescribeTable",
                "dynamodb:ListTables"
            ],
            "Resource": "arn:aws:dynamodb:us-east-1:*:table/themisguard-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:PutParameter",
                "ssm:GetParameters"
            ],
            "Resource": "arn:aws:ssm:us-east-1:*:parameter/themisguard/*"
        }
    ]
}
```

---

## 📋 **Pipeline Overview**

### **Development Pipeline** (`.github/workflows/dev-deploy.yml`)

**Triggers:**
- Push to `develop` or `main` branches
- Pull requests to `develop`

**Workflow:**
1. **Test Backend** - Python linting, tests, coverage
2. **Test Frontend** - Node.js linting, tests, build
3. **Security Scan** - Trivy vulnerability scan, secret detection
4. **Deploy Backend** - SAM build and deploy to dev
5. **Deploy Frontend** - Build and deploy to S3/CloudFront
6. **Integration Tests** - End-to-end testing with Playwright
7. **Notification** - Deployment summary and status

### **Production Pipeline** (`.github/workflows/prod-deploy.yml`)

**Triggers:**
- GitHub releases (automatic)
- Manual workflow dispatch (with approval)

**Workflow:**
1. **Pre-deployment Checks** - Version validation, readiness checks
2. **Comprehensive Testing** - Full test suite, security scans
3. **Backup Production** - Create backups before deployment
4. **Deploy Backend** - Staged production deployment
5. **Deploy Frontend** - Production frontend deployment
6. **Smoke Tests** - Critical functionality verification
7. **Post-deployment** - Success tracking, rollback on failure

---

## 🛠️ **Required Repository Structure**

Ensure your repository has these files for the pipelines to work:

```
themisguard/
├── .github/
│   └── workflows/
│       ├── dev-deploy.yml
│       └── prod-deploy.yml
├── backend/
│   ├── template.yaml
│   ├── samconfig.toml
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   └── playwright.config.js
└── docs/
    └── deployment-setup.md
```

---

## ⚙️ **Pipeline Configuration**

### **SAM Configuration** (`backend/samconfig.toml`)
```toml
version = 0.1

[default.global.parameters]
stack_name = "themisguard-api"
region = "us-east-1"
confirm_changeset = true
fail_on_empty_changeset = false

[default.build.parameters]
cached = true
parallel = true

[default.deploy.parameters]
capabilities = "CAPABILITY_IAM"
parameter_overrides = [
    "Environment=dev"
]

[dev.deploy.parameters]
stack_name = "themisguard-api-dev"
parameter_overrides = [
    "Environment=dev"
]

[prod.deploy.parameters]
stack_name = "themisguard-api-prod"
parameter_overrides = [
    "Environment=prod"
]
```

### **Frontend Package.json Scripts**
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest",
    "test:ci": "vitest run --coverage",
    "lint": "eslint . --ext js,jsx,ts,tsx",
    "lint:fix": "eslint . --ext js,jsx,ts,tsx --fix"
  }
}
```

---

## 🚦 **Environment Protection Rules**

### **Production Environment Setup**
1. Go to repository `Settings` → `Environments`
2. Create `production` environment
3. Add protection rules:
   - **Required reviewers**: Add team members who can approve prod deployments
   - **Wait timer**: 5 minutes (optional delay)
   - **Deployment branches**: Only `main` branch

### **Branch Protection Rules**
1. Go to `Settings` → `Branches`
2. Add rule for `main` branch:
   - Require pull request reviews
   - Require status checks (all CI tests must pass)
   - Require up-to-date branches
   - Restrict pushes to admins only

---

## 🔍 **Monitoring & Alerting**

### **AWS Resources to Monitor**
```bash
# CloudWatch Alarms
- Lambda function errors
- API Gateway 4xx/5xx errors  
- DynamoDB throttling
- S3 upload failures

# Custom Metrics
- Deployment success/failure rates
- Application response times
- User authentication failures
```

### **GitHub Notifications**
The pipelines automatically create:
- Deployment summaries in GitHub
- Failed deployment alerts
- Security scan results
- Test coverage reports

---

## 🔧 **Troubleshooting Common Issues**

### **Permission Errors**
```bash
# Check IAM policies
aws sts get-caller-identity
aws iam get-user

# Verify S3 bucket access
aws s3 ls s3://themisguard-frontend-dev
```

### **SAM Build Failures**
```bash
# Clear SAM cache
rm -rf backend/.aws-sam
cd backend && sam build --config-env dev
```

### **Frontend Build Issues**
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### **CloudFormation Stack Issues**
```bash
# Check stack events
aws cloudformation describe-stack-events --stack-name themisguard-api-dev

# View stack outputs
aws cloudformation describe-stacks --stack-name themisguard-api-dev \
  --query 'Stacks[0].Outputs'
```

---

## 📊 **Deployment Metrics**

### **Key Performance Indicators**
- **Deployment Frequency**: How often you deploy
- **Lead Time**: Time from commit to production
- **Mean Time to Recovery**: How quickly you fix issues
- **Change Failure Rate**: Percentage of deployments causing issues

### **Monitoring Commands**
```bash
# Check recent deployments
aws ssm get-parameter --name "/themisguard/prod/last-successful-deployment"

# View deployment history
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
```

---

## 🎯 **Next Steps After Setup**

1. **Test the pipelines** with a small change to `develop` branch
2. **Create a test release** to verify production pipeline
3. **Set up monitoring dashboards** in AWS CloudWatch
4. **Configure alerts** for failed deployments
5. **Document rollback procedures** for your team
6. **Schedule regular security scans** and dependency updates

---

## 🔒 **Security Best Practices**

### **Secrets Management**
- Use GitHub secrets for sensitive data
- Rotate AWS access keys regularly
- Use least-privilege IAM policies
- Enable AWS CloudTrail for audit logging

### **Code Security**
- Enable Dependabot for dependency updates
- Use CodeQL for static analysis
- Scan container images for vulnerabilities
- Implement branch protection rules

**Ready to deploy!** 🚀 Your CI/CD pipelines are configured for reliable, secure deployments from development to production.