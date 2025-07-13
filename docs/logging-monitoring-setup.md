# AWS Logging & Monitoring Setup for CompliantGuard

## Overview
Set up comprehensive logging and monitoring using AWS native services for both development and production environments.

## 1. CloudWatch Logs Setup

### Backend Lambda Logs
- **Automatic**: Lambda functions automatically send logs to CloudWatch
- **Log Group**: `/aws/lambda/themisguard-api-dev`
- **Retention**: 30 days (dev), 90 days (prod)

### Frontend CloudFront Logs
- **Access Logs**: Delivered to S3 bucket
- **Real-time Logs**: Optional for detailed monitoring

### DynamoDB Logs
- **CloudTrail**: API calls and data access patterns
- **Contributor Insights**: Top accessed items

## 2. CloudWatch Alarms

### Critical Alarms
```bash
# API Error Rate > 5%
aws cloudwatch put-metric-alarm \
  --alarm-name "CompliantGuard-API-ErrorRate" \
  --alarm-description "API error rate is high" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# DynamoDB Throttles
aws cloudwatch put-metric-alarm \
  --alarm-name "CompliantGuard-DynamoDB-Throttles" \
  --alarm-description "DynamoDB is being throttled" \
  --metric-name UserErrors \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold

# High Response Time
aws cloudwatch put-metric-alarm \
  --alarm-name "CompliantGuard-API-LatencyHigh" \
  --alarm-description "API response time is high" \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 5000 \
  --comparison-operator GreaterThanThreshold
```

## 3. X-Ray Distributed Tracing

### Enable X-Ray for Lambda
```yaml
# In SAM template.yaml
Globals:
  Function:
    Tracing: Active
    Environment:
      Variables:
        _X_AMZN_TRACE_ID: !Ref AWS::NoValue
```

### Add to Python code
```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Patch AWS SDK calls
patch_all()

@xray_recorder.capture('registration_flow')
async def register_user(user_data):
    # Your registration code
    pass
```

## 4. Custom Metrics

### Business Metrics
```python
import boto3
cloudwatch = boto3.client('cloudwatch')

# Track registrations
cloudwatch.put_metric_data(
    Namespace='CompliantGuard/Business',
    MetricData=[
        {
            'MetricName': 'UserRegistrations',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Environment', 'Value': 'dev'},
                {'Name': 'Source', 'Value': 'email'}  # or 'google-sso'
            ]
        }
    ]
)

# Track scan usage
cloudwatch.put_metric_data(
    Namespace='CompliantGuard/Usage',
    MetricData=[
        {
            'MetricName': 'ScansPerformed',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'PlanTier', 'Value': user_plan},
                {'Name': 'ProjectType', 'Value': 'gcp'}
            ]
        }
    ]
)
```

## 5. Error Tracking & Alerting

### CloudWatch Insights Queries
```sql
-- Registration errors
fields @timestamp, @message
| filter @message like /registration/
| filter @message like /error/
| sort @timestamp desc

-- Authentication failures
fields @timestamp, @message, email
| filter @message like /authentication failed/
| stats count() by email
| sort count desc

-- API performance
fields @timestamp, @duration, @requestId
| filter @type = "REPORT"
| stats avg(@duration), max(@duration), min(@duration) by bin(5m)
```

### SNS for Alerts
```bash
# Create SNS topic for alerts
aws sns create-topic --name compliantguard-alerts

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT:compliantguard-alerts \
  --protocol email \
  --notification-endpoint admin@datfunc.com
```

## 6. Dashboard Setup

### CloudWatch Dashboard
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", "FunctionName", "themisguard-api"],
          [".", "Errors", ".", "."],
          [".", "Duration", ".", "."]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "API Metrics"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/lambda/themisguard-api-dev'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
        "region": "us-east-1",
        "title": "Recent Errors",
        "view": "table"
      }
    }
  ]
}
```

## 7. Local Development Logging

### Enhanced Backend Logging
```python
import logging
import structlog
from datetime import datetime

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage in auth routes
@router.post("/register")
async def register_user(user_data: UserRegistration):
    logger.info("user_registration_started", email=user_data.email, has_company=bool(user_data.company))
    
    try:
        # Registration logic
        logger.info("user_registration_successful", user_id=user_id, email=user_data.email)
        return result
    except Exception as e:
        logger.error("user_registration_failed", email=user_data.email, error=str(e))
        raise
```

## 8. Production Monitoring Commands

### Check API Health
```bash
# Lambda function metrics
aws logs filter-log-events \
  --log-group-name "/aws/lambda/themisguard-api-dev" \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"

# DynamoDB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=themisguard-users \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# API Gateway metrics (if using)
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=themisguard-api \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## 9. Cost Monitoring

### Budget Alerts
```bash
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget '{
    "BudgetName": "CompliantGuard-Monthly",
    "BudgetLimit": {
      "Amount": "100",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[
    {
      "Notification": {
        "NotificationType": "ACTUAL",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 80
      },
      "Subscribers": [
        {
          "SubscriptionType": "EMAIL",
          "Address": "admin@datfunc.com"
        }
      ]
    }
  ]'
```

This setup provides comprehensive monitoring for both development debugging and production operations, all using AWS-native services.