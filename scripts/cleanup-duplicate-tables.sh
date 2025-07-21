#!/bin/bash

echo "🧹 DynamoDB Tables Cleanup"
echo "=========================="

# List tables to review
echo "📋 Current tables:"
aws dynamodb list-tables --region us-east-1 --output table

echo ""
echo "⚠️  Tables that will be DELETED:"
echo "- themisguard-api-scans"
echo "- themisguard-api-dev-scans"
echo "- themisguard-api-staging-scans"
echo "- (any other themisguard-api-* variants)"

echo ""
echo "✅ Tables that will be KEPT:"
echo "- themisguard-api-prod-* (production data)"
echo "- compliantguard-gcp-credentials"
echo "- themisguard-users"

echo ""
read -p "Continue with cleanup? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Starting cleanup..."

    # Delete development/duplicate tables
    for table in $(aws dynamodb list-tables --region us-east-1 --output text --query 'TableNames[]' | grep -E '^themisguard-api-(scans|users|admin|subscriptions|usage|invoices|webhook)'); do
        echo "Deleting: $table"
        aws dynamodb delete-table --table-name "$table" --region us-east-1
    done

    echo "✅ Cleanup complete!"
else
    echo "❌ Cleanup cancelled"
fi
