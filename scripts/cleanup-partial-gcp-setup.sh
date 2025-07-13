#!/bin/bash

echo "🧹 Cleaning up partial GCP credential infrastructure setup..."

CREDENTIALS_TABLE="compliantguard-gcp-credentials" 
REGION="us-east-1"

echo "🗑️ Checking for partially created resources..."

# Check if table exists in a bad state
if aws dynamodb describe-table --table-name "$CREDENTIALS_TABLE" --region $REGION 2>/dev/null; then
    TABLE_STATUS=$(aws dynamodb describe-table --table-name "$CREDENTIALS_TABLE" --region $REGION --query 'Table.TableStatus' --output text)
    echo "📋 Table status: $TABLE_STATUS"
    
    if [[ "$TABLE_STATUS" == "CREATING" || "$TABLE_STATUS" == "DELETING" ]]; then
        echo "⏳ Table is in transitional state, waiting..."
        aws dynamodb wait table-exists --table-name "$CREDENTIALS_TABLE" --region $REGION 2>/dev/null || true
    fi
    
    echo "🗑️ Deleting existing table..."
    aws dynamodb delete-table --table-name "$CREDENTIALS_TABLE" --region $REGION
    
    echo "⏳ Waiting for table deletion..."
    aws dynamodb wait table-not-exists --table-name "$CREDENTIALS_TABLE" --region $REGION
    
    echo "✅ Table deleted successfully"
else
    echo "ℹ️ No existing table found"
fi

echo ""
echo "✅ Cleanup complete! You can now run the setup script again:"
echo "   ./scripts/setup-gcp-security.sh"