# Google Auth Setup for Staging - Quick Summary

## 🎯 What You Need to Do

### 1. **Google Cloud Console (5 minutes)**
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID → Web application
3. Add authorized origins: `https://your-staging-domain.com`
4. Copy Client ID and Client Secret

### 2. **GitHub Secrets (2 minutes)**
Add these to Repository → Settings → Secrets:
```
GOOGLE_CLIENT_ID_STAGING=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET_STAGING=GOCSPX-your-secret
```

### 3. **Frontend Configuration (1 minute)**
Create `frontend/.env.staging`:
```bash
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
VITE_API_URL=https://your-staging-api.com
```

### 4. **Deploy (Automatic)**
```bash
git commit -am "Add Google Auth staging config"
git push
# GitHub Actions will deploy automatically
```

## ✅ What's Already Done

- ✅ **GoogleSSO React component** - Ready to use
- ✅ **Backend `/auth/google-sso` endpoint** - Handles JWT verification
- ✅ **SAM template configuration** - Accepts GoogleClientId parameter
- ✅ **GitHub workflow** - Passes Google Client ID during deployment
- ✅ **User registration flow** - Creates users from Google data
- ✅ **JWT token handling** - Full authentication flow

## 🚀 Quick Setup Script

Run this to get started:
```bash
./scripts/setup-google-auth.sh
```

## 📋 Testing

1. Deploy to staging
2. Visit `https://your-staging-domain.com/login`
3. Click "Continue with Google"
4. Complete OAuth flow
5. Verify user is logged in

## 🔧 Troubleshooting

**"Invalid client ID"** → Check `VITE_GOOGLE_CLIENT_ID` matches Google Console  
**"Unauthorized redirect"** → Add your domain to Google Console authorized origins  
**"SSO login failed"** → Check backend logs in CloudWatch

## 📚 Full Documentation

- **Complete guide:** `docs/GOOGLE_AUTH_SETUP.md`
- **Setup script:** `scripts/setup-google-auth.sh`

**Total setup time: ~10 minutes** 🎉