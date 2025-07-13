#!/bin/bash

echo "🔍 Debugging frontend CloudFormation stack deployment..."
echo ""

STACK_NAME="compliantguard-frontend-dev"

echo "1. Checking if stack exists:"
aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].[StackName,StackStatus,CreationTime]' --output table 2>/dev/null || echo "❌ Stack does not exist"

echo ""
echo "2. Listing all frontend-related stacks:"
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[?contains(StackName, `frontend`)].{Name:StackName,Status:StackStatus,Created:CreationTime}' --output table

echo ""
echo "3. If stack exists, checking outputs:"
aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].Outputs' --output table 2>/dev/null || echo "No outputs or stack doesn't exist"

echo ""
echo "4. If stack exists, checking resources:"
aws cloudformation list-stack-resources --stack-name "$STACK_NAME" --query 'StackResourceSummaries[?ResourceType==`AWS::CloudFront::Distribution`].{Type:ResourceType,Status:ResourceStatus,LogicalId:LogicalResourceId}' --output table 2>/dev/null || echo "No CloudFront resources or stack doesn't exist"

echo ""
echo "5. Checking for any stack events (last 10):"
aws cloudformation describe-stack-events --stack-name "$STACK_NAME" --query 'StackEvents[0:9].{Time:Timestamp,Status:ResourceStatus,Type:ResourceType,Reason:ResourceStatusReason}' --output table 2>/dev/null || echo "No events or stack doesn't exist"

echo ""
echo "6. Checking if template file exists:"
if [ -f "frontend-template.yaml" ]; then
    echo "✅ frontend-template.yaml exists"
    echo "   CloudFront resource defined: $(grep -c "AWS::CloudFront::Distribution" frontend-template.yaml) times"
else
    echo "❌ frontend-template.yaml not found"
fi