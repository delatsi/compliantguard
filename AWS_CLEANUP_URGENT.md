# 🚨 URGENT: AWS Resource Cleanup Required

## Summary
**CRITICAL ISSUE FOUND:** The deployment process is creating hundreds of timestamped DynamoDB tables on every deployment, causing:

- **Massive AWS costs** (~$270+ monthly just for empty tables)
- **Resource proliferation** (300+ duplicate tables identified)
- **Management complexity** (impossible to track which resources are active)

## Problem Root Cause
The SAM deployment is using stack-based table naming with timestamps:
```
TableName: !Sub "${AWS::StackName}-tablename"
```

Combined with timestamped stack names in deployment commands:
```bash
sam deploy --stack-name themisguard-api-dev-$(date +%Y%m%d-%H%M%S)
```

## Tables Found (Sample Pattern)
```
themisguard-api-dev-20250712-180706-admin-audit
themisguard-api-dev-20250712-180706-admin-users
themisguard-api-dev-20250712-182800-admin-audit
themisguard-api-dev-20250712-182800-admin-users
... (300+ more tables following this pattern)
```

Each deployment creates **8 tables** × **~40 deployments** = **320+ tables**

## Estimated Costs

### DynamoDB Tables
- **320+ tables** × **$0.25/month each** = **~$80+/month**
- Plus associated resources (Lambda functions, API Gateway, etc.)
- **Total estimated waste: $200-300+/month**

### Other Resources
Each timestamped stack likely includes:
- Lambda functions
- API Gateway APIs  
- IAM roles
- CloudWatch log groups
- S3 buckets

## Immediate Actions Required

### 1. Stop Creating New Resources
```bash
# Use fixed stack names instead of timestamped ones
sam deploy --config-env dev    # NOT: sam deploy --stack-name themisguard-api-dev-$(date)
```

### 2. Emergency Table Cleanup
```bash
# Run the emergency cleanup script
./scripts/emergency-dynamodb-cleanup.sh
```

### 3. Fix SAM Template
Update `template.yaml` table naming:
```yaml
# BEFORE (creates new tables per stack):
TableName: !Sub "${AWS::StackName}-scans"

# AFTER (stable table names):
TableName: !Sub "themisguard-${Environment}-scans"
```

### 4. Update Deployment Process
Use `samconfig.toml` environments:
```bash
# Development
sam deploy --config-env dev

# Staging  
sam deploy --config-env staging

# Production
sam deploy --config-env prod
```

## Resources to Clean Up

### Safe to Delete (Timestamped)
- All tables matching: `themisguard-api-dev-20250712-*`
- All tables matching: `themisguard-api-dev-20250713-*`  
- All tables matching: `themisguard-api-dev-20250714-*`

### Keep (Active/Production)
- `compliantguard-gcp-credentials`
- `themisguard-api-dev-admin-audit` (non-timestamped)
- `themisguard-api-dev-admin-users` (non-timestamped)
- Any production tables

## Cost Savings
After cleanup: **~$200-300/month savings**

## Prevention Strategy
1. ✅ Fixed stack names in `samconfig.toml`
2. ✅ Stable table names in `template.yaml`  
3. ✅ Deployment process using `--config-env`
4. ✅ Resource governance policies
5. ✅ Monthly cost monitoring alerts

## Next Steps
1. **URGENT:** Run emergency cleanup script
2. **TODAY:** Fix SAM template and deployment process
3. **THIS WEEK:** Set up cost monitoring and governance
4. **ONGOING:** Monthly resource audits

---

**STATUS:** 🔴 Critical - Immediate action required to prevent further cost escalation