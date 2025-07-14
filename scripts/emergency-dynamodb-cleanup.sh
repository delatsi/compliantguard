#!/bin/bash

echo "🚨 EMERGENCY DynamoDB Cleanup"
echo "=============================="
echo ""
echo "📊 Analysis of current tables:"
echo "- Found ~270 DynamoDB tables"
echo "- ~260+ are timestamped duplicates"
echo "- Estimated cost: ~$67.50/month for empty tables alone"
echo ""

# Tables to keep (safe list)
SAFE_TABLES=(
    "Music"
    "compliantguard-gcp-credentials"
    "courses"
    "locations"
    "themisguard-api-dev-admin-audit"
    "themisguard-api-dev-admin-users"
    "users-swagyu-dev"
)

echo "✅ Tables that will be KEPT:"
printf '%s\n' "${SAFE_TABLES[@]}"
echo ""

echo "🗑️  Tables that will be DELETED:"
echo "- All tables matching: themisguard-api-dev-2025*"
echo "- Estimated: ~260 tables"
echo ""

# Count tables to delete
DELETE_COUNT=$(aws dynamodb list-tables --region us-east-1 --output text --query 'TableNames[]' | grep -c "themisguard-api-dev-2025")
echo "📈 Exact count of tables to delete: $DELETE_COUNT"
echo ""

read -p "⚠️  Are you sure you want to delete $DELETE_COUNT tables? (type 'DELETE' to confirm): " -r
echo

if [[ $REPLY == "DELETE" ]]; then
    echo "🗑️  Starting cleanup..."
    echo ""
    
    DELETED=0
    FAILED=0
    
    # Get all timestamped tables and delete them
    for table in $(aws dynamodb list-tables --region us-east-1 --output text --query 'TableNames[]' | grep "themisguard-api-dev-2025"); do
        echo "Deleting: $table"
        
        if aws dynamodb delete-table --table-name "$table" --region us-east-1 >/dev/null 2>&1; then
            echo "  ✅ Deleted successfully"
            ((DELETED++))
        else
            echo "  ❌ Failed to delete"
            ((FAILED++))
        fi
        
        # Small delay to avoid rate limiting
        sleep 0.1
    done
    
    echo ""
    echo "📊 Cleanup Results:"
    echo "==================="
    echo "✅ Tables deleted: $DELETED"
    echo "❌ Failed deletions: $FAILED"
    echo "💰 Estimated monthly savings: \$$(echo "$DELETED * 0.25" | bc)"
    echo ""
    
    echo "📋 Remaining tables:"
    aws dynamodb list-tables --region us-east-1 --output table
    
else
    echo "❌ Cleanup cancelled - no tables were deleted"
fi

echo ""
echo "🔧 Next Steps:"
echo "=============="
echo "1. Fix SAM template to prevent future duplicates"
echo "2. Use stable table names instead of timestamped ones"
echo "3. Set up proper environment separation"
echo "4. Monitor DynamoDB costs"