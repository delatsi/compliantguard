# ThemisGuard Deployment Best Practices & Security Guide

## 🚀 **Deployment Strategy Overview**

This guide provides secure, production-ready deployment practices for ThemisGuard across multiple AWS environments within your DELATSI LLC organization structure.

---

## 🏗️ **Environment-Specific Deployment**

### **Development Environment**
```bash
# Deploy to development account
sam deploy --config-env dev --parameter-overrides \
  "StripeSecretKey=${STRIPE_TEST_SECRET_KEY}" \
  "StripePublishableKey=${STRIPE_TEST_PUB_KEY}" \
  "StripeWebhookSecret=${STRIPE_TEST_WEBHOOK_SECRET}" \
  "GoogleClientId=${GOOGLE_CLIENT_ID}" \
  "GCPProjectId=${GCP_PROJECT_ID}"

# Verify deployment
aws cloudformation describe-stacks --stack-name themisguard-api-dev
```

### **Staging Environment**
```bash
# Deploy to staging account (switch AWS profile)
aws configure set profile themisguard-staging
sam deploy --config-env staging --parameter-overrides \
  "StripeSecretKey=${STRIPE_TEST_SECRET_KEY}" \
  "StripePublishableKey=${STRIPE_TEST_PUB_KEY}" \
  "StripeWebhookSecret=${STRIPE_TEST_WEBHOOK_SECRET}" \
  "GoogleClientId=${GOOGLE_CLIENT_ID}" \
  "GCPProjectId=${GCP_PROJECT_ID}"
```

### **Production Environment**
```bash
# Deploy to production account (requires live Stripe keys)
aws configure set profile themisguard-prod
sam deploy --config-env prod --parameter-overrides \
  "StripeSecretKey=${STRIPE_LIVE_SECRET_KEY}" \
  "StripePublishableKey=${STRIPE_LIVE_PUB_KEY}" \
  "StripeWebhookSecret=${STRIPE_LIVE_WEBHOOK_SECRET}" \
  "GoogleClientId=${GOOGLE_CLIENT_ID}" \
  "GCPProjectId=${GCP_PROJECT_ID}" \
  "CustomDomainName=api.themisguard.com" \
  "SSLCertificateArn=${SSL_CERT_ARN}"
```

---

## 🔐 **Security Best Practices**

### **1. Secrets Management**

#### Environment Variables Setup
```bash
# Create .env files for each environment (NEVER commit these)
cat > backend/.env.dev << EOF
ENVIRONMENT=dev
STRIPE_SECRET_KEY=sk_test_your_dev_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_dev_key
STRIPE_WEBHOOK_SECRET=whsec_your_dev_secret
JWT_SECRET_KEY=$(openssl rand -base64 32)
GOOGLE_CLIENT_ID=your_google_client_id
GCP_PROJECT_ID=your_gcp_project_id
EOF

cat > backend/.env.prod << EOF
ENVIRONMENT=prod
STRIPE_SECRET_KEY=sk_live_your_live_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key
STRIPE_WEBHOOK_SECRET=whsec_your_live_secret
JWT_SECRET_KEY=$(openssl rand -base64 32)
GOOGLE_CLIENT_ID=your_google_client_id
GCP_PROJECT_ID=your_gcp_project_id
EOF
```

#### AWS Secrets Manager Integration
```bash
# Store sensitive secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "themisguard/prod/stripe" \
  --description "Production Stripe API keys" \
  --secret-string '{
    "secret_key": "sk_live_...",
    "publishable_key": "pk_live_...",
    "webhook_secret": "whsec_..."
  }'

aws secretsmanager create-secret \
  --name "themisguard/prod/jwt" \
  --description "Production JWT secret key" \
  --secret-string '{"jwt_secret": "your_strong_jwt_secret"}'
```

### **2. IAM Security**

#### Cross-Account Deployment Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::MASTER_ACCOUNT:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "themisguard-deployment"
        },
        "IpAddress": {
          "aws:SourceIp": ["YOUR_OFFICE_IP/32", "YOUR_CI_IP_RANGE"]
        }
      }
    }
  ]
}
```

#### Least Privilege IAM Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:ValidateTemplate"
      ],
      "Resource": "arn:aws:cloudformation:*:*:stack/themisguard-api-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:GetBucketLocation",
        "s3:ListBucket",
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::themisguard-*",
        "arn:aws:s3:::themisguard-*/*"
      ]
    }
  ]
}
```

### **3. Network Security**

#### VPC Configuration (Production)
```yaml
# Add to template.yaml for production
VPC:
  Type: AWS::EC2::VPC
  Properties:
    CidrBlock: 10.0.0.0/16
    EnableDnsHostnames: true
    EnableDnsSupport: true
    Tags:
      - Key: Name
        Value: !Sub "${AWS::StackName}-vpc"

PrivateSubnet1:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref VPC
    CidrBlock: 10.0.1.0/24
    AvailabilityZone: !Select [0, !GetAZs ""]

PrivateSubnet2:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref VPC
    CidrBlock: 10.0.2.0/24
    AvailabilityZone: !Select [1, !GetAZs ""]

NATGateway:
  Type: AWS::EC2::NatGateway
  Properties:
    AllocationId: !GetAtt EIPForNAT.AllocationId
    SubnetId: !Ref PublicSubnet
```

### **4. Monitoring & Alerting**

#### CloudWatch Alarms
```yaml
HighErrorRateAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${AWS::StackName}-high-error-rate"
    AlarmDescription: "High error rate in ThemisGuard API"
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 2
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
    Dimensions:
      - Name: FunctionName
        Value: !Ref ThemisGuardAPI
    AlarmActions:
      - !Ref SNSAlarmTopic

DatabaseWriteErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${AWS::StackName}-dynamodb-write-errors"
    MetricName: UserErrors
    Namespace: AWS/DynamoDB
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanOrEqualToThreshold
```

---

## 🔄 **CI/CD Pipeline Implementation**

### **GitHub Actions Workflow**
```yaml
# .github/workflows/deploy.yml
name: Deploy ThemisGuard

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          cd backend
          python -m pytest tests/ -v --cov=. --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Bandit Security Scan
        run: |
          pip install bandit
          bandit -r backend/ -f json -o bandit-report.json
      
      - name: Run Safety Check
        run: |
          pip install safety
          safety check -r backend/requirements.txt

  deploy-dev:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: development
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_DEV }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_DEV }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: SAM Build and Deploy
        run: |
          sam build
          sam deploy --config-env dev --parameter-overrides \
            "StripeSecretKey=${{ secrets.STRIPE_TEST_SECRET_KEY }}" \
            "StripePublishableKey=${{ secrets.STRIPE_TEST_PUB_KEY }}" \
            "GoogleClientId=${{ secrets.GOOGLE_CLIENT_ID }}"

  deploy-staging:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_STAGING }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_STAGING }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: SAM Build and Deploy
        run: |
          sam build
          sam deploy --config-env staging

  deploy-prod:
    needs: [deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v3
      
      - name: Manual Approval
        uses: trstringer/manual-approval@v1
        with:
          secret: ${{ github.TOKEN }}
          approvers: your-github-username
          minimum-approvals: 1
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_PROD }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_PROD }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: SAM Build and Deploy
        run: |
          sam build
          sam deploy --config-env prod
```

---

## 📊 **Infrastructure Monitoring**

### **Essential CloudWatch Dashboards**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Duration", "FunctionName", "themisguard-api-prod-ThemisGuardAPI"],
          ["AWS/Lambda", "Errors", "FunctionName", "themisguard-api-prod-ThemisGuardAPI"],
          ["AWS/Lambda", "Invocations", "FunctionName", "themisguard-api-prod-ThemisGuardAPI"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Lambda Performance"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "themisguard-api-prod-scans"],
          ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", "themisguard-api-prod-scans"],
          ["AWS/DynamoDB", "ThrottledRequests", "TableName", "themisguard-api-prod-scans"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "DynamoDB Usage"
      }
    }
  ]
}
```

### **Cost Monitoring**
```yaml
BudgetAlert:
  Type: AWS::Budgets::Budget
  Properties:
    Budget:
      BudgetName: !Sub "${AWS::StackName}-monthly-budget"
      BudgetLimit:
        Amount: !If [IsProduction, 1000, 200]
        Unit: USD
      TimeUnit: MONTHLY
      BudgetType: COST
      CostFilters:
        TagKey:
          - Project
        TagValue:
          - !Ref ProjectName
    NotificationsWithSubscribers:
      - Notification:
          NotificationType: ACTUAL
          ComparisonOperator: GREATER_THAN
          Threshold: 80
        Subscribers:
          - SubscriptionType: EMAIL
            Address: billing@delatsi-llc.com
      - Notification:
          NotificationType: FORECASTED
          ComparisonOperator: GREATER_THAN
          Threshold: 100
        Subscribers:
          - SubscriptionType: EMAIL
            Address: billing@delatsi-llc.com
```

---

## 🎯 **Pre-Deployment Checklist**

### **Security Validation**
- [ ] All secrets stored in AWS Secrets Manager or environment variables
- [ ] No hardcoded credentials in source code
- [ ] IAM roles follow least privilege principle
- [ ] All S3 buckets have public access blocked
- [ ] DynamoDB tables have encryption at rest enabled
- [ ] Lambda functions have appropriate timeout and memory settings
- [ ] CloudTrail logging enabled for all environments
- [ ] VPC configuration for production environment

### **Functionality Testing**
- [ ] All unit tests passing
- [ ] Integration tests completed
- [ ] Load testing performed on staging
- [ ] Stripe webhook testing completed
- [ ] Google SSO integration verified
- [ ] HIPAA compliance scan functionality tested
- [ ] Admin dashboard security verified

### **Infrastructure Validation**
- [ ] CloudFormation template validates successfully
- [ ] All required parameters provided
- [ ] Resource naming follows conventions
- [ ] Tags applied consistently across all resources
- [ ] Backup and retention policies configured
- [ ] Monitoring and alerting set up
- [ ] Cost budgets and alerts configured

### **Deployment Validation**
- [ ] Smoke tests pass after deployment
- [ ] Health checks return 200 status
- [ ] Database connections successful
- [ ] External API integrations working
- [ ] Frontend can connect to API
- [ ] SSL certificates valid and properly configured

---

## 🚨 **Incident Response**

### **Rollback Procedures**
```bash
# Emergency rollback to previous version
aws cloudformation cancel-update-stack --stack-name themisguard-api-prod

# Or deploy specific previous version
sam deploy --config-env prod --parameter-overrides \
  "Environment=prod" \
  --s3-bucket your-artifacts-bucket \
  --s3-prefix rollback-$(date +%Y%m%d)
```

### **Emergency Contacts**
- **Technical Lead**: your-email@delatsi-llc.com
- **AWS Support**: Enterprise Support Case
- **Stripe Support**: Stripe Dashboard Support

### **Monitoring Dashboards**
- **CloudWatch**: https://console.aws.amazon.com/cloudwatch/
- **Stripe Dashboard**: https://dashboard.stripe.com/
- **Application Insights**: Custom ThemisGuard Dashboard

---

## 📈 **Performance Optimization**

### **Lambda Optimization**
```yaml
# Optimized Lambda configuration
ThemisGuardAPI:
  Type: AWS::Serverless::Function
  Properties:
    MemorySize: !If [IsProduction, 1024, 512]
    Timeout: !If [IsProduction, 30, 15]
    ReservedConcurrencyLimit: !If [IsProduction, 100, 10]
    ProvisionedConcurrencyConfig:
      ProvisionedConcurrencyUnits: !If [IsProduction, 5, 0]
    Environment:
      Variables:
        PYTHONDONTWRITEBYTECODE: 1
        LAMBDA_INSIGHTS_LOG_LEVEL: INFO
    Layers:
      - arn:aws:lambda:us-east-1:580247275435:layer:LambdaInsightsExtension:14
```

### **DynamoDB Optimization**
```yaml
# Auto Scaling for production
ScansTableWriteCapacityScalableTarget:
  Type: AWS::ApplicationAutoScaling::ScalableTarget
  Condition: IsProduction
  Properties:
    MaxCapacity: 100
    MinCapacity: 5
    ResourceId: !Sub "table/${ScansTable}"
    RoleARN: !Sub "arn:aws:iam::${AWS::AccountId}:role/aws-service-role/dynamodb.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_DynamoDBTable"
    ScalableDimension: dynamodb:table:WriteCapacityUnits
    ServiceNamespace: dynamodb
```

---

**Remember**: Always test deployments in development and staging before production. Follow the principle of least privilege and monitor all changes closely through CloudWatch and your alerting systems.