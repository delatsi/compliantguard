#!/bin/bash

echo "Checking CloudFormation stack status..."

# Wait for stack to complete
while true; do
    STACK_STATUS=$(aws cloudformation describe-stacks --stack-name compliantguard-frontend --region us-east-1 --query 'Stacks[0].StackStatus' --output text 2>/dev/null)
    
    if [ "$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
        echo "✅ Stack deployment complete!"
        break
    elif [ "$STACK_STATUS" = "CREATE_FAILED" ] || [ "$STACK_STATUS" = "ROLLBACK_COMPLETE" ]; then
        echo "❌ Stack deployment failed!"
        exit 1
    else
        echo "⏳ Stack status: $STACK_STATUS - waiting..."
        sleep 30
    fi
done

# Get bucket name from stack outputs
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name compliantguard-frontend --region us-east-1 --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' --output text)
CLOUDFRONT_DOMAIN=$(aws cloudformation describe-stacks --stack-name compliantguard-frontend --region us-east-1 --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomainName`].OutputValue' --output text)
DISTRIBUTION_ID=$(aws cloudformation describe-stacks --stack-name compliantguard-frontend --region us-east-1 --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' --output text)

echo "📦 Bucket: $BUCKET_NAME"
echo "🌐 CloudFront: $CLOUDFRONT_DOMAIN"
echo "🆔 Distribution ID: $DISTRIBUTION_ID"

# Upload frontend files to S3
echo "📤 Uploading frontend files to S3..."
aws s3 sync frontend/dist/ s3://$BUCKET_NAME/ --delete --region us-east-1

# Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"

echo "🚀 Frontend deployed successfully!"
echo "📱 Website URL: https://$CLOUDFRONT_DOMAIN"