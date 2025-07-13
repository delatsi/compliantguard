# Debugging Blank Page Issue

Your S3 bucket has the correct files:
- ✅ `index.html` (main HTML file)
- ✅ `assets/` folder (JS/CSS bundles)

## Likely Causes & Solutions:

### 1. JavaScript/CSS Loading Issues

Check browser developer tools (F12):

**Console Tab:**
- Look for 404 errors loading `/assets/index-*.js` or `/assets/index-*.css`
- Look for CORS errors
- Look for any JavaScript errors

**Network Tab:**
- Check if assets are loading with 200 status
- Look for failed requests

### 2. CloudFront Configuration Issues

Since you manually created CloudFront (E35NIWANRWM2P8), verify these settings:

**Origin Settings:**
- Origin Domain: Should be your S3 bucket's **website endpoint** (e.g., `bucket-name.s3-website-us-east-1.amazonaws.com`)
- NOT the REST endpoint (e.g., `bucket-name.s3.amazonaws.com`)

**Behavior Settings:**
- Default Root Object: `index.html`
- Error Pages: 403 → `/index.html` (for SPA routing)
- Error Pages: 404 → `/index.html` (for SPA routing)

### 3. S3 Bucket Configuration

Your S3 bucket needs static website hosting enabled:

```bash
# Check current website configuration
aws s3api get-bucket-website --bucket YOUR_BUCKET_NAME

# If not configured, enable it:
aws s3 website s3://YOUR_BUCKET_NAME --index-document index.html --error-document index.html
```

### 4. Environment Variables

The app might be failing due to missing API URL. Check if it's trying to connect to localhost:

**In browser console, look for:**
- Failed API calls to localhost
- Environment variable errors

**Current API URL setting:**
The build process should create `.env.production` with `VITE_API_URL` set to your backend URL.

## Quick Debug Commands:

```bash
# 1. Run the debug script
./scripts/debug-frontend-stack.sh

# 2. Check CloudFront configuration
./scripts/fix-cloudfront-manually.sh

# 3. Manual checks:
# Check what's actually in your S3 bucket
aws s3 ls s3://YOUR_BUCKET_NAME --recursive

# Check S3 website configuration
aws s3api get-bucket-website --bucket YOUR_BUCKET_NAME

# Test direct S3 website access (not through CloudFront)
# URL format: http://YOUR_BUCKET_NAME.s3-website-REGION.amazonaws.com

# Check CloudFront distribution settings
aws cloudfront get-distribution --id E35NIWANRWM2P8
```

## Common Fixes:

### Fix 1: Update CloudFront Origin
If using S3 REST endpoint, change to website endpoint:
- **Wrong**: `mybucket.s3.amazonaws.com`
- **Right**: `mybucket.s3-website-us-east-1.amazonaws.com`

### Fix 2: Add Error Pages to CloudFront
For React SPA routing:
- 403 → `/index.html` (Response Code: 200)
- 404 → `/index.html` (Response Code: 200)

### Fix 3: Check Cache
Clear CloudFront cache:
```bash
aws cloudfront create-invalidation --distribution-id E35NIWANRWM2P8 --paths "/*"
```

## Test URLs:

1. **Direct S3 website** (should work): `http://YOUR_BUCKET_NAME.s3-website-us-east-1.amazonaws.com`
2. **CloudFront** (if configured correctly): `https://compliantguard.datfunc.com`

Let me know what you see in the browser developer tools console!