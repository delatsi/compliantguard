# Google Authentication Setup for Staging

This guide walks through setting up Google OAuth authentication for the CompliantGuard staging environment.

## 🎯 Overview

Google Auth requires several components to work properly:
1. **Google Cloud Console** - OAuth client configuration
2. **Frontend Environment** - Client ID configuration  
3. **Backend Integration** - JWT token verification
4. **Domain Configuration** - Authorized redirect URIs
5. **GitHub Secrets** - Secure credential storage

## 📋 Prerequisites

- Google Cloud Console access
- Staging domain URL (e.g., `https://staging.compliantguard.com`)
- GitHub repository admin access
- AWS deployment pipeline working

## 🔧 Step-by-Step Setup

### 1. Google Cloud Console Setup

#### Create OAuth 2.0 Client ID

1. **Navigate to Google Cloud Console:**
   ```
   https://console.cloud.google.com/apis/credentials
   ```

2. **Select or Create Project:**
   - Use existing project or create new one
   - Project name: `compliantguard-auth` (or similar)

3. **Configure OAuth Consent Screen:**
   ```
   APIs & Services → OAuth consent screen
   
   User Type: External
   App name: CompliantGuard
   User support email: your-email@company.com
   Developer contact: your-email@company.com
   
   Scopes:
   - openid
   - email  
   - profile
   
   Test users (for development):
   - Add your email and team emails
   ```

4. **Create OAuth 2.0 Client ID:**
   ```
   APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
   
   Application type: Web application
   Name: CompliantGuard Staging
   
   Authorized JavaScript origins:
   - https://staging.compliantguard.com
   - https://compliantguard-staging.herokuapp.com (if using Heroku)
   - http://localhost:3000 (for local development)
   
   Authorized redirect URIs:
   - https://staging.compliantguard.com/auth/callback
   - http://localhost:3000/auth/callback
   ```

5. **Copy Credentials:**
   ```
   Client ID: 123456789-abcdef.apps.googleusercontent.com
   Client Secret: GOCSPX-abcdef123456789
   ```

### 2. GitHub Secrets Configuration

Add these secrets to your GitHub repository:

```bash
# Navigate to: GitHub Repository → Settings → Secrets and variables → Actions

# Staging secrets
GOOGLE_CLIENT_ID_STAGING=123456789-abcdef.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET_STAGING=GOCSPX-abcdef123456789

# Development secrets (optional)
GOOGLE_CLIENT_ID_DEV=123456789-devtest.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET_DEV=GOCSPX-devtest123456789

# Production secrets (when ready)
GOOGLE_CLIENT_ID_PROD=123456789-prod.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET_PROD=GOCSPX-prod123456789
```

### 3. Update SAM Template

The template is already configured to use Google Client ID, but ensure it's properly referenced:

```yaml
# template.yaml - Already configured
Parameters:
  GoogleClientId:
    Type: String
    Default: ""
    Description: Google OAuth Client ID for SSO
    
Environment:
  Variables:
    GOOGLE_CLIENT_ID: !Ref GoogleClientId
```

### 4. Update Frontend Environment Variables

The frontend needs the client ID at build time:

```javascript
// frontend/.env.staging (create this file)
VITE_API_URL=https://api-staging.compliantguard.com
VITE_GOOGLE_CLIENT_ID=123456789-abcdef.apps.googleusercontent.com
```

### 5. Update GitHub Workflow

Ensure the smart-deploy workflow passes the Google Client ID:

```yaml
# .github/workflows/smart-deploy.yml - Already configured
- name: Deploy backend
  run: |
    sam deploy \
      --config-env ${{ needs.detect-changes.outputs.environment }} \
      --parameter-overrides \
        GoogleClientId=${{ needs.detect-changes.outputs.environment == 'dev' && secrets.GOOGLE_CLIENT_ID_DEV || needs.detect-changes.outputs.environment == 'staging' && secrets.GOOGLE_CLIENT_ID_STAGING || secrets.GOOGLE_CLIENT_ID_PROD }}
```

### 6. Update Frontend GoogleSSO Component

The component is ready but may need environment-specific configuration:

```javascript
// frontend/src/components/GoogleSSO.jsx - Already implemented
window.google.accounts.id.initialize({
  client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID, // Uses environment variable
  callback: handleCredentialResponse,
});
```

### 7. Backend Google SSO Endpoint

The backend already has the `/api/v1/auth/google-sso` endpoint implemented.

## 🚀 Deployment Process

### Deploy to Staging

1. **Commit any final changes:**
   ```bash
   git add .
   git commit -m "Configure Google Auth for staging"
   git push origin main
   ```

2. **Deploy via GitHub Actions:**
   - The smart-deploy workflow will automatically deploy
   - Or manually trigger: Repository → Actions → smart-deploy → Run workflow

3. **Deploy frontend with environment variables:**
   ```bash
   # Frontend deployment will include VITE_GOOGLE_CLIENT_ID
   ```

## 🧪 Testing Google Auth

### 1. Test Authentication Flow

1. **Navigate to staging URL:**
   ```
   https://staging.compliantguard.com/login
   ```

2. **Click "Continue with Google" button**

3. **Verify OAuth flow:**
   - Redirects to Google
   - Shows consent screen (if first time)
   - Redirects back to app
   - Creates user account automatically

### 2. Test Backend Integration

```bash
# Test the Google SSO endpoint directly
curl -X POST https://api-staging.compliantguard.com/api/v1/auth/google-sso \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@gmail.com",
    "name": "Test User",
    "google_id": "google-user-123",
    "picture": "https://example.com/photo.jpg"
  }'
```

### 3. Verify User Creation

Check that users are properly created in DynamoDB with Google ID fields.

## 🔒 Security Considerations

### Domain Restrictions
- Only authorize your actual staging domain
- Remove localhost from production client
- Use separate OAuth clients for each environment

### Token Verification
```javascript
// Backend already implements proper JWT verification
const userInfo = JSON.parse(atob(response.credential.split('.')[1]));
```

### HTTPS Required
- Google OAuth requires HTTPS in production
- Ensure staging environment uses SSL certificate

## 🐛 Troubleshooting

### Common Issues

**"Invalid client ID":**
- Check VITE_GOOGLE_CLIENT_ID matches Google Console
- Verify client ID is for correct environment

**"Unauthorized redirect URI":**
- Add staging domain to authorized origins in Google Console
- Check for typos in domain name

**"SSO login failed":**
- Check backend logs for Google SSO endpoint errors
- Verify DynamoDB users table exists and is accessible

**CORS errors:**
- Ensure staging domain is in authorized JavaScript origins
- Check frontend CORS configuration

### Debug Steps

1. **Check browser console** for JavaScript errors
2. **Verify network requests** in DevTools
3. **Check backend logs** in CloudWatch
4. **Test with different Google accounts**

## 📊 Monitoring

### Metrics to Track
- Google auth success/failure rates
- User registration via Google SSO
- Token verification errors
- OAuth consent screen completion

### CloudWatch Alarms
- High authentication failure rates
- Google API rate limit errors
- JWT token verification failures

## 🎯 Production Checklist

Before moving to production:

- [ ] Create production OAuth client in Google Console
- [ ] Configure production domain in authorized origins
- [ ] Add production secrets to GitHub
- [ ] Test with multiple Google accounts
- [ ] Verify user data handling complies with privacy policies
- [ ] Set up monitoring and alerting
- [ ] Document user onboarding flow

## 🔗 Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Identity Services](https://developers.google.com/identity/gsi/web)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)