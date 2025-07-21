#!/bin/bash
echo "📋 Current DynamoDB Tables:"
echo "=========================="
aws dynamodb list-tables --region us-east-1 --output table

echo ""
echo "📊 Table Details:"
echo "=================="
for table in $(aws dynamodb list-tables --region us-east-1 --output text --query 'TableNames[]'); do
    echo "Table: $table"
    aws dynamodb describe-table --table-name "$table" --region us-east-1 \
        --query 'Table.{Name:TableName,Status:TableStatus,Items:ItemCount,Size:TableSizeBytes}' \
        --output table
    echo ""
done
