# Fix ROLLBACK_FAILED CloudFormation Stack

The stack `themisguard-api-staging` is in ROLLBACK_FAILED state and needs manual cleanup.

## Step 1: Check and Disable Deletion Protection

First, let's check if there are any DynamoDB tables with deletion protection that are preventing cleanup:

```bash
# Check for remaining tables with deletion protection
aws dynamodb list-tables --region us-east-1 | grep -E "(themisguard.*staging|staging.*themisguard)"

# If any tables exist, disable deletion protection:
aws dynamodb update-table \
    --table-name themisguard-staging-admin-users \
    --no-deletion-protection-enabled \
    --region us-east-1

aws dynamodb update-table \
    --table-name themisguard-staging-admin-audit \
    --no-deletion-protection-enabled \
    --region us-east-1
```

## Step 2: Delete the Failed Stack

```bash
# Delete the stack that's in ROLLBACK_FAILED state
aws cloudformation delete-stack \
    --stack-name themisguard-api-staging \
    --region us-east-1

# Wait for deletion to complete (this may take a few minutes)
aws cloudformation wait stack-delete-complete \
    --stack-name themisguard-api-staging \
    --region us-east-1
```

## Step 3: Verify Stack is Gone

```bash
# Verify the stack no longer exists
aws cloudformation describe-stacks \
    --stack-name themisguard-api-staging \
    --region us-east-1
# This should return an error saying the stack doesn't exist
```

## Step 4: Retry Deployment

After the stack is successfully deleted, retry the deployment:

```bash
# From your project directory
sam deploy --config-env staging
```

## Alternative: Use AWS Console

If the CLI commands don't work, you can also:

1. Go to **AWS Console** → **CloudFormation**
2. Find the `themisguard-api-staging` stack
3. **Delete** it (you may need to disable deletion protection on tables first)
4. Go to **DynamoDB** → **Tables** and manually delete any remaining staging tables
5. Retry the deployment

## Why This Happened

The ROLLBACK_FAILED state occurs when CloudFormation cannot clean up resources during a failed deployment. This is usually because:

- Tables have deletion protection enabled
- Resources have dependencies that prevent deletion
- IAM permissions issues

Our template fixes should prevent this from happening again by making deletion protection conditional for non-production environments.