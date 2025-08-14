# Fix DynamoDB Table Naming Conflict

## The Problem
The staging deployment is failing because it's trying to create a DynamoDB table named `themisguard-minimal-users` that already exists in another CloudFormation stack called `themisguard-minimal-debug`.

## Root Cause Analysis
There are two possible causes:
1. **Conflicting stack**: The `themisguard-minimal-debug` stack contains tables that conflict with our staging deployment
2. **Wrong template**: SAM might be accidentally using `template-minimal.yaml` instead of `template.yaml`

## Solution Options

### Option 1: Delete the Conflicting Stack (Recommended)
```bash
# Delete the debug stack that's causing the conflict
aws cloudformation delete-stack \
    --stack-name themisguard-minimal-debug \
    --region us-east-1

# Wait for deletion
aws cloudformation wait stack-delete-complete \
    --stack-name themisguard-minimal-debug \
    --region us-east-1

# Then retry the staging deployment
sam deploy --config-env staging
```

### Option 2: Delete Conflicting Tables Manually
```bash
# List and delete conflicting tables
aws dynamodb delete-table --table-name themisguard-minimal-users --region us-east-1
aws dynamodb delete-table --table-name themisguard-minimal-scans --region us-east-1
aws dynamodb delete-table --table-name themisguard-minimal-gcp-credentials --region us-east-1

# Then retry deployment
sam deploy --config-env staging
```

### Option 3: Clear SAM Build Cache
```bash
# Clear any cached builds
rm -rf .aws-sam
sam build --config-env staging
sam deploy --config-env staging
```

## Verification Steps

1. **Check which stacks exist:**
```bash
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --region us-east-1 | grep themisguard
```

2. **Check which tables exist:**
```bash
aws dynamodb list-tables --region us-east-1 | grep themisguard
```

3. **Verify correct template is being used:**
```bash
# The main template.yaml should have environment-specific naming:
grep -A 2 "TableName:" template.yaml
# Should show: !Sub "${ProjectName}-${Environment}-users"
```

## Expected Result
After cleanup, the deployment should succeed because:
- No conflicting table names
- Proper environment-specific naming
- Clean SAM build process

## Prevention
To prevent this in the future:
- Use consistent naming conventions
- Clean up debug/test stacks regularly
- Use environment-specific resource names