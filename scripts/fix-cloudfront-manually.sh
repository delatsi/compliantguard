#!/bin/bash

# Script to check and fix common CloudFront issues for manually created distribution
DISTRIBUTION_ID="E35NIWANRWM2P8"
BUCKET_NAME="compliantguard-frontend-dev-fallback"  # Update if different

echo "🔍 Checking CloudFront distribution: $DISTRIBUTION_ID"

# 1. Get current distribution config
echo "1. Current distribution configuration:"
aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DistributionConfig.{Origins:Origins[0].DomainName,DefaultRootObject:DefaultRootObject,Comment:Comment}' --output table

echo ""
echo "2. Checking S3 bucket website configuration:"
aws s3api get-bucket-website --bucket $BUCKET_NAME 2>/dev/null || echo "❌ Static website hosting not enabled"

echo ""
echo "3. Expected S3 website endpoint should be:"
echo "   $BUCKET_NAME.s3-website-us-east-1.amazonaws.com"

echo ""
echo "4. Checking if CloudFront origin matches S3 website endpoint:"
ORIGIN_DOMAIN=$(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DistributionConfig.Origins[0].DomainName' --output text)
echo "   Current origin: $ORIGIN_DOMAIN"

if [[ "$ORIGIN_DOMAIN" == *"s3-website"* ]]; then
    echo "   ✅ Using S3 website endpoint (good)"
else
    echo "   ❌ Using S3 REST endpoint (should be website endpoint)"
    echo "   Fix: Change origin to: $BUCKET_NAME.s3-website-us-east-1.amazonaws.com"
fi

echo ""
echo "5. Checking default root object:"
ROOT_OBJECT=$(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DistributionConfig.DefaultRootObject' --output text)
if [[ "$ROOT_OBJECT" == "index.html" ]]; then
    echo "   ✅ Default root object is index.html"
else
    echo "   ❌ Default root object: '$ROOT_OBJECT' (should be 'index.html')"
fi

echo ""
echo "6. To enable S3 static website hosting:"
echo "   aws s3 website s3://$BUCKET_NAME --index-document index.html --error-document index.html"

echo ""
echo "7. To invalidate CloudFront cache:"
echo "   aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths '/*'"

echo ""
echo "8. Test URLs:"
echo "   Direct S3: http://$BUCKET_NAME.s3-website-us-east-1.amazonaws.com"
echo "   CloudFront: https://compliantguard.datfunc.com"