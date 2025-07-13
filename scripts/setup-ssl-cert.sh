#!/bin/bash

# Create SSL certificate for compliantguard.delatsi.com
# Must be run in us-east-1 region for CloudFront

echo "🔐 Creating SSL certificate for compliantguard.datfunc.com"

# Request certificate
CERT_ARN=$(aws acm request-certificate \
    --domain-name "compliantguard.datfunc.com" \
    --validation-method DNS \
    --region us-east-1 \
    --query 'CertificateArn' \
    --output text)

echo "Certificate ARN: $CERT_ARN"
echo ""
echo "📋 Next steps:"
echo "1. Get DNS validation records:"
echo "   aws acm describe-certificate --certificate-arn $CERT_ARN --region us-east-1"
echo ""
echo "2. Add the CNAME records to your datfunc.com DNS zone"
echo ""
echo "3. Wait for certificate validation (can take 5-30 minutes)"
echo "   aws acm wait certificate-validated --certificate-arn $CERT_ARN --region us-east-1"
echo ""
echo "4. Add this ARN to your GitHub secrets as SSL_CERT_ARN:"
echo "   $CERT_ARN"