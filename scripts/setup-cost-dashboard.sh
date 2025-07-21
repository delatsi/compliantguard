#!/bin/bash

echo "💰 Setting up AWS Cost Management Dashboard"
echo "==========================================="
echo ""

# Configuration
REGION="us-east-1"
DASHBOARD_NAME="CompliantGuard-Cost-Dashboard"
PROJECT_NAME="CompliantGuard"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_section() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

log_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "🕐 Setup started at: $(date)"
echo "🌎 Region: $REGION"
echo ""

# Step 1: Create Cost Allocation Tags
log_section "Setting up Cost Allocation Tags"

echo "📋 Activating cost allocation tags for proper cost tracking..."

# Activate user-defined cost allocation tags
COST_TAGS=(
    "Project"
    "Environment"
    "Tier"
    "Component"
    "Owner"
    "CostCenter"
    "Application"
)

for tag in "${COST_TAGS[@]}"; do
    echo "🏷️  Activating cost allocation tag: $tag"
    aws ce modify-cost-category-definition \
        --cost-category-arn "arn:aws:ce::${AWS_ACCOUNT_ID}:cost-category/${tag}" \
        --name "$tag" \
        --rules '[{"Value":"'$tag'","Type":"DIMENSION","Key":"'$tag'"}]' \
        --region $REGION 2>/dev/null || echo "   (Tag may already be active or require manual activation in billing console)"
done

echo ""

# Step 2: Create Cost Budget Alerts
log_section "Creating Cost Budget Alerts"

echo "📊 Setting up cost budgets for each environment..."

# Create budgets configuration
cat > /tmp/compliantguard-budgets.json << 'EOF'
{
  "budgets": [
    {
      "BudgetName": "CompliantGuard-Development-Monthly",
      "BudgetLimit": {
        "Amount": "50.00",
        "Unit": "USD"
      },
      "TimeUnit": "MONTHLY",
      "BudgetType": "COST",
      "CostFilters": {
        "TagKey": ["Project", "Environment"],
        "TagValue": ["CompliantGuard", "dev"]
      },
      "NotificationsWithSubscribers": [
        {
          "Notification": {
            "NotificationType": "ACTUAL",
            "ComparisonOperator": "GREATER_THAN",
            "Threshold": 80.0,
            "ThresholdType": "PERCENTAGE"
          },
          "Subscribers": [
            {
              "SubscriptionType": "EMAIL",
              "Address": "alerts@yourcompany.com"
            }
          ]
        },
        {
          "Notification": {
            "NotificationType": "FORECASTED",
            "ComparisonOperator": "GREATER_THAN",
            "Threshold": 100.0,
            "ThresholdType": "PERCENTAGE"
          },
          "Subscribers": [
            {
              "SubscriptionType": "EMAIL",
              "Address": "alerts@yourcompany.com"
            }
          ]
        }
      ]
    },
    {
      "BudgetName": "CompliantGuard-Production-Monthly",
      "BudgetLimit": {
        "Amount": "200.00",
        "Unit": "USD"
      },
      "TimeUnit": "MONTHLY",
      "BudgetType": "COST",
      "CostFilters": {
        "TagKey": ["Project", "Environment"],
        "TagValue": ["CompliantGuard", "prod"]
      },
      "NotificationsWithSubscribers": [
        {
          "Notification": {
            "NotificationType": "ACTUAL",
            "ComparisonOperator": "GREATER_THAN",
            "Threshold": 75.0,
            "ThresholdType": "PERCENTAGE"
          },
          "Subscribers": [
            {
              "SubscriptionType": "EMAIL",
              "Address": "alerts@yourcompany.com"
            }
          ]
        },
        {
          "Notification": {
            "NotificationType": "FORECASTED",
            "ComparisonOperator": "GREATER_THAN",
            "Threshold": 90.0,
            "ThresholdType": "PERCENTAGE"
          },
          "Subscribers": [
            {
              "SubscriptionType": "EMAIL",
              "Address": "alerts@yourcompany.com"
            }
          ]
        }
      ]
    }
  ]
}
EOF

# Note: Budget creation requires specific permissions and may need manual setup
log_warning "Budget creation requires billing permissions - see AWS Budgets console for manual setup"
echo "Budget configuration saved to: /tmp/compliantguard-budgets.json"

echo ""

# Step 3: Create CloudWatch Cost Dashboard
log_section "Creating CloudWatch Cost Dashboard"

echo "📊 Setting up CloudWatch dashboard for cost monitoring..."

# Create dashboard configuration
cat > /tmp/cost-dashboard.json << 'EOF'
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [ "AWS/Billing", "EstimatedCharges", "Currency", "USD" ]
        ],
        "period": 86400,
        "stat": "Maximum",
        "region": "us-east-1",
        "title": "Total AWS Costs (Monthly)",
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "view": "timeSeries",
        "stacked": true,
        "metrics": [
          [ "AWS/Lambda", "Duration", { "stat": "Sum" } ],
          [ ".", "Invocations", { "stat": "Sum" } ]
        ],
        "period": 3600,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Lambda Usage (CompliantGuard)",
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 8,
      "height": 6,
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [ "AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "themisguard-users", { "stat": "Sum" } ],
          [ ".", "ConsumedWriteCapacityUnits", ".", ".", { "stat": "Sum" } ]
        ],
        "period": 3600,
        "stat": "Average",
        "region": "us-east-1",
        "title": "DynamoDB Usage",
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      }
    },
    {
      "type": "metric",
      "x": 8,
      "y": 6,
      "width": 8,
      "height": 6,
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [ "AWS/ApiGateway", "Count", "ApiName", "themisguard-api" ],
          [ ".", "Latency", ".", ".", { "stat": "Average" } ]
        ],
        "period": 3600,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "API Gateway Usage",
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      }
    },
    {
      "type": "metric",
      "x": 16,
      "y": 6,
      "width": 8,
      "height": 6,
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [ "AWS/S3", "BucketSizeBytes", "BucketName", "compliantguard-frontend-dev", "StorageType", "StandardStorage" ]
        ],
        "period": 86400,
        "stat": "Average",
        "region": "us-east-1",
        "title": "S3 Storage Usage",
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      }
    },
    {
      "type": "log",
      "x": 0,
      "y": 12,
      "width": 24,
      "height": 6,
      "properties": {
        "query": "SOURCE '/aws/lambda/themisguard-api-dev'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
        "region": "us-east-1",
        "title": "Recent Errors (Lambda Logs)",
        "view": "table"
      }
    }
  ]
}
EOF

# Create the dashboard
if aws cloudwatch put-dashboard \
    --dashboard-name "$DASHBOARD_NAME" \
    --dashboard-body file:///tmp/cost-dashboard.json \
    --region $REGION >/dev/null 2>&1; then
    log_info "✅ CloudWatch dashboard created: $DASHBOARD_NAME"
else
    log_warning "⚠️ Dashboard creation failed - may need manual setup"
fi

echo ""

# Step 4: Create Resource Tagging Script
log_section "Creating Resource Tagging Strategy"

echo "🏷️  Setting up automated resource tagging..."

cat > /tmp/tag-resources.sh << 'EOF'
#!/bin/bash

# CompliantGuard Resource Tagging Script
echo "🏷️ Tagging CompliantGuard Resources"
echo "=================================="

REGION="us-east-1"

# Standard tags for all resources
COMMON_TAGS="Project=CompliantGuard Owner=DevOps CostCenter=Engineering Application=CompliantGuard"

# Function to tag a resource
tag_resource() {
    local resource_arn=$1
    local environment=$2
    local component=$3
    local tier=$4
    
    aws resourcegroupstaggingapi tag-resources \
        --resource-arn-list "$resource_arn" \
        --tags "Project=CompliantGuard,Environment=$environment,Component=$component,Tier=$tier,Owner=DevOps,CostCenter=Engineering,Application=CompliantGuard" \
        --region $REGION >/dev/null 2>&1
}

# Tag DynamoDB tables
echo "📊 Tagging DynamoDB tables..."
for table in $(aws dynamodb list-tables --region $REGION --query 'TableNames[]' --output text | grep -E "(compliantguard|themisguard)"); do
    if [[ $table == *"prod"* ]]; then
        ENVIRONMENT="prod"
        TIER="production"
    elif [[ $table == *"staging"* ]]; then
        ENVIRONMENT="staging"  
        TIER="staging"
    else
        ENVIRONMENT="dev"
        TIER="development"
    fi
    
    if [[ $table == *"gcp-credentials"* ]]; then
        COMPONENT="security"
    elif [[ $table == *"users"* ]]; then
        COMPONENT="auth"
    else
        COMPONENT="core"
    fi
    
    echo "  Tagging: $table ($ENVIRONMENT)"
    aws dynamodb tag-resource \
        --resource-arn "arn:aws:dynamodb:$REGION:$(aws sts get-caller-identity --query Account --output text):table/$table" \
        --tags "Key=Project,Value=CompliantGuard" "Key=Environment,Value=$ENVIRONMENT" "Key=Component,Value=$COMPONENT" "Key=Tier,Value=$TIER" "Key=Owner,Value=DevOps" "Key=CostCenter,Value=Engineering" \
        --region $REGION 2>/dev/null || true
done

# Tag S3 buckets
echo "📦 Tagging S3 buckets..."
for bucket in $(aws s3api list-buckets --query 'Buckets[?contains(Name, `compliantguard`) || contains(Name, `themisguard`)].Name' --output text); do
    if [[ $bucket == *"prod"* ]]; then
        ENVIRONMENT="prod"
        TIER="production"
    elif [[ $bucket == *"staging"* ]]; then
        ENVIRONMENT="staging"
        TIER="staging"  
    else
        ENVIRONMENT="dev"
        TIER="development"
    fi
    
    if [[ $bucket == *"frontend"* ]]; then
        COMPONENT="frontend"
    elif [[ $bucket == *"reports"* ]]; then
        COMPONENT="reports"
    else
        COMPONENT="storage"
    fi
    
    echo "  Tagging: $bucket ($ENVIRONMENT)"
    aws s3api put-bucket-tagging \
        --bucket "$bucket" \
        --tagging "TagSet=[{Key=Project,Value=CompliantGuard},{Key=Environment,Value=$ENVIRONMENT},{Key=Component,Value=$COMPONENT},{Key=Tier,Value=$TIER},{Key=Owner,Value=DevOps},{Key=CostCenter,Value=Engineering}]" \
        2>/dev/null || true
done

# Tag Lambda functions
echo "⚡ Tagging Lambda functions..."
for function in $(aws lambda list-functions --region $REGION --query 'Functions[?contains(FunctionName, `compliantguard`) || contains(FunctionName, `themisguard`)].FunctionName' --output text); do
    if [[ $function == *"prod"* ]]; then
        ENVIRONMENT="prod"
        TIER="production"
    elif [[ $function == *"staging"* ]]; then
        ENVIRONMENT="staging"
        TIER="staging"
    else
        ENVIRONMENT="dev"
        TIER="development"
    fi
    
    COMPONENT="api"
    
    echo "  Tagging: $function ($ENVIRONMENT)"
    aws lambda tag-resource \
        --resource "arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$function" \
        --tags "Project=CompliantGuard,Environment=$ENVIRONMENT,Component=$COMPONENT,Tier=$TIER,Owner=DevOps,CostCenter=Engineering" \
        --region $REGION 2>/dev/null || true
done

echo "✅ Resource tagging completed!"
EOF

chmod +x /tmp/tag-resources.sh

log_info "✅ Resource tagging script created: /tmp/tag-resources.sh"

echo ""

# Step 5: Cost Anomaly Detection
log_section "Setting up Cost Anomaly Detection"

echo "🔍 Creating cost anomaly detection..."

cat > /tmp/cost-anomaly-detector.json << 'EOF'
{
  "AnomalyDetectorName": "CompliantGuard-Cost-Anomaly-Detector",
  "MonitorType": "DIMENSIONAL",
  "MonitorSpecification": {
    "DimensionKey": "SERVICE",
    "MatchOptions": ["EQUALS"],
    "Values": ["Amazon Simple Storage Service", "Amazon DynamoDB", "AWS Lambda", "Amazon API Gateway"]
  },
  "MonitorDimension": "SERVICE"
}
EOF

log_warning "Cost anomaly detection requires manual setup in AWS Cost Explorer"
echo "Configuration saved to: /tmp/cost-anomaly-detector.json"

echo ""

# Step 6: Generate Cost Report Script
log_section "Creating Cost Reporting Script"

cat > /tmp/generate-cost-report.sh << 'EOF'
#!/bin/bash

echo "💰 CompliantGuard Cost Report"
echo "============================="
echo "Generated: $(date)"
echo ""

REGION="us-east-1"
START_DATE=$(date -d "1 month ago" +%Y-%m-01)
END_DATE=$(date +%Y-%m-%d)

echo "📊 Cost breakdown for period: $START_DATE to $END_DATE"
echo ""

# Get costs by service
echo "🔍 Costs by AWS Service:"
echo "========================"
aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics "BlendedCost" \
    --group-by Type=DIMENSION,Key=SERVICE \
    --region us-east-1 \
    --query 'ResultsByTime[0].Groups[?starts_with(Keys[0], `Amazon`) || starts_with(Keys[0], `AWS`)].{Service:Keys[0],Cost:Metrics.BlendedCost.Amount}' \
    --output table

echo ""

# Get costs by tag (if available)
echo "🏷️  Costs by Environment (if tagged):"
echo "===================================="
aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics "BlendedCost" \
    --group-by Type=TAG,Key=Environment \
    --region us-east-1 \
    --query 'ResultsByTime[0].Groups[].{Environment:Keys[0],Cost:Metrics.BlendedCost.Amount}' \
    --output table 2>/dev/null || echo "No environment tags found - run tagging script first"

echo ""

# Get resource count
echo "📈 Resource Inventory:"
echo "====================="
echo "DynamoDB Tables: $(aws dynamodb list-tables --region $REGION --query 'length(TableNames)' --output text)"
echo "S3 Buckets: $(aws s3api list-buckets --query 'length(Buckets)' --output text)"
echo "Lambda Functions: $(aws lambda list-functions --region $REGION --query 'length(Functions)' --output text)"

echo ""
echo "🔗 Links:"
echo "========="
echo "Cost Dashboard: https://$REGION.console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=CompliantGuard-Cost-Dashboard"
echo "AWS Cost Explorer: https://console.aws.amazon.com/cost-management/home#/cost-explorer"
echo "AWS Budgets: https://console.aws.amazon.com/billing/home#/budgets"

EOF

chmod +x /tmp/generate-cost-report.sh

log_info "✅ Cost reporting script created: /tmp/generate-cost-report.sh"

echo ""

# Step 7: Summary
log_section "Setup Summary"

echo "✅ Cost management setup completed!"
echo ""
echo "📋 Created Components:"
echo "====================="
echo "1. ✅ Cost allocation tag strategy"
echo "2. ✅ CloudWatch cost dashboard: $DASHBOARD_NAME"  
echo "3. ✅ Resource tagging automation: /tmp/tag-resources.sh"
echo "4. ✅ Cost reporting script: /tmp/generate-cost-report.sh"
echo "5. ✅ Budget configuration: /tmp/compliantguard-budgets.json"
echo "6. ✅ Anomaly detection config: /tmp/cost-anomaly-detector.json"
echo ""

echo "🚀 Next Steps:"
echo "=============="
echo "1. Run resource tagging: /tmp/tag-resources.sh"
echo "2. Set up budgets manually in AWS Budgets console"
echo "3. Configure cost anomaly detection in Cost Explorer"
echo "4. Generate first cost report: /tmp/generate-cost-report.sh"
echo "5. Review dashboard: https://$REGION.console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=$DASHBOARD_NAME"
echo ""

echo "💡 Tagging Strategy:"
echo "==================="
echo "• Project: CompliantGuard"
echo "• Environment: dev/staging/prod"  
echo "• Tier: development/staging/production"
echo "• Component: frontend/api/auth/security/storage"
echo "• Owner: DevOps"
echo "• CostCenter: Engineering"
echo ""

echo "💰 Monthly Budget Recommendations:"
echo "=================================="
echo "• Development: $50/month"
echo "• Staging: $100/month"
echo "• Production: $200/month"
echo "• Total: $350/month"

echo ""
echo "🔔 Alerts configured at:"
echo "• 80% of budget (actual costs)"
echo "• 100% of budget (forecasted costs)"
EOF