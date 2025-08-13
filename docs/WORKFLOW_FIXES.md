# GitHub Workflow Fixes

## ❌ Issue Fixed
```
Unrecognized function: 'upper'. Located at position 41 within expression: 
secrets[format('AWS_ACCESS_KEY_ID_{0}', upper(needs.detect-changes.outputs.environment))]
```

## ✅ Solution Applied

**Problem:** GitHub Actions doesn't have an `upper()` function for string manipulation.

**Fix:** Replaced dynamic secret selection using `upper()` with explicit conditional logic.

### Before (Invalid):
```yaml
aws-access-key-id: ${{ secrets[format('AWS_ACCESS_KEY_ID_{0}', upper(needs.detect-changes.outputs.environment))] }}
aws-secret-access-key: ${{ secrets[format('AWS_SECRET_ACCESS_KEY_{0}', upper(needs.detect-changes.outputs.environment))] }}
```

### After (Valid):
```yaml
aws-access-key-id: ${{ needs.detect-changes.outputs.environment == 'dev' && secrets.AWS_ACCESS_KEY_ID_DEV || needs.detect-changes.outputs.environment == 'staging' && secrets.AWS_ACCESS_KEY_ID_STAGING || secrets.AWS_ACCESS_KEY_ID_PROD }}
aws-secret-access-key: ${{ needs.detect-changes.outputs.environment == 'dev' && secrets.AWS_SECRET_ACCESS_KEY_DEV || needs.detect-changes.outputs.environment == 'staging' && secrets.AWS_SECRET_ACCESS_KEY_STAGING || secrets.AWS_SECRET_ACCESS_KEY_PROD }}
```

## 📁 Files Fixed

1. **`.github/workflows/smart-deploy.yml`**
   - Fixed 4 instances in different jobs
   - Lines: 275, 276, 385, 386, 553, 554, 625, 626

2. **`.github/workflows/infrastructure-drift-check.yml`**
   - Fixed 2 instances in matrix strategy
   - Lines: 45, 46

## 🎯 How It Works

The new conditional logic works as follows:

```yaml
environment == 'dev' && secrets.AWS_ACCESS_KEY_ID_DEV ||     # If dev, use DEV secrets
environment == 'staging' && secrets.AWS_ACCESS_KEY_ID_STAGING ||  # If staging, use STAGING secrets  
secrets.AWS_ACCESS_KEY_ID_PROD                              # Otherwise, use PROD secrets (default)
```

This provides the same dynamic secret selection without using unsupported functions.

## 🔧 Required GitHub Secrets

Ensure these secrets are configured in your repository:

**Development:**
- `AWS_ACCESS_KEY_ID_DEV`
- `AWS_SECRET_ACCESS_KEY_DEV`

**Staging:**
- `AWS_ACCESS_KEY_ID_STAGING`
- `AWS_SECRET_ACCESS_KEY_STAGING`

**Production:**
- `AWS_ACCESS_KEY_ID_PROD`
- `AWS_SECRET_ACCESS_KEY_PROD`

## ✅ Validation

- ✅ No more `upper()` function calls in any workflow
- ✅ Valid GitHub Actions expression syntax
- ✅ Maintains same environment-specific credential selection
- ✅ Backward compatible with existing secret naming

## 🚀 Result

The workflows are now valid and ready for deployment!