# Custom Domain Setup for CompliantGuard

This guide walks through setting up `compliantguard.datfunc.com` as the custom domain for the frontend.

## Prerequisites

- Access to datfunc.com DNS management (Route 53 or your DNS provider)
- AWS CLI configured with appropriate permissions
- GitHub repository with secrets access

## Step 1: Create SSL Certificate

Run the setup script to create an SSL certificate:

```bash
chmod +x setup-ssl-cert.sh
./setup-ssl-cert.sh
```

This will:
1. Request an SSL certificate for `compliantguard.datfunc.com` in us-east-1
2. Return a Certificate ARN
3. Provide DNS validation records

## Step 2: Add DNS Validation Records

1. Get the validation records:
```bash
aws acm describe-certificate --certificate-arn <CERT_ARN> --region us-east-1 --query 'Certificate.DomainValidationOptions[0]'
```

2. Add the CNAME record to your datfunc.com DNS zone:
   - **Name**: `_xxxxxxxxxxxx.compliantguard.datfunc.com`
   - **Value**: `_yyyyyyyyyyyy.acm-validations.aws.`
   - **Type**: CNAME

3. Wait for validation (5-30 minutes):
```bash
aws acm wait certificate-validated --certificate-arn <CERT_ARN> --region us-east-1
```

## Step 3: Add GitHub Secrets

Add these secrets to your GitHub repository:

1. Go to: Settings → Secrets and variables → Actions
2. Add repository secrets:
   - **CUSTOM_DOMAIN_NAME**: `compliantguard.datfunc.com`
   - **SSL_CERT_ARN**: `arn:aws:acm:us-east-1:xxxxxxxxxxxx:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

## Step 4: Deploy with Custom Domain

Once the GitHub secrets are set, the next deployment will automatically:
1. Configure CloudFront with your custom domain
2. Attach the SSL certificate
3. Output the custom domain URL

## Step 5: Add DNS Record for the Domain

After deployment, get the CloudFront distribution domain:

```bash
aws cloudformation describe-stacks \
  --stack-name compliantguard-frontend-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomainName`].OutputValue' \
  --output text
```

Then add a CNAME record to your DNS:
- **Name**: `compliantguard.datfunc.com`
- **Value**: `dxxxxxxxxxxxxx.cloudfront.net` (from above command)
- **Type**: CNAME

## Verification

After DNS propagation (5-15 minutes), your site should be accessible at:
- ✅ `https://compliantguard.datfunc.com`
- 🔒 SSL certificate should be valid
- 🚀 Served via CloudFront CDN

## Troubleshooting

### Certificate Validation Stuck
- Verify DNS record was added correctly
- Check DNS propagation: `dig TXT _validation.compliantguard.datfunc.com`
- Certificate validation can take up to 72 hours but usually completes in 30 minutes

### DNS Not Resolving
- Check CNAME record points to CloudFront distribution
- Verify DNS propagation: `dig compliantguard.datfunc.com`
- Clear browser cache and try incognito mode

### SSL Certificate Errors
- Ensure certificate is in us-east-1 region
- Verify certificate status is "ISSUED" in ACM console
- Check that domain names match exactly

## Cost Impact

Custom domain adds minimal cost:
- **Route 53 hosted zone**: ~$0.50/month (if using Route 53)
- **ACM certificate**: Free
- **CloudFront**: No additional cost for custom domain