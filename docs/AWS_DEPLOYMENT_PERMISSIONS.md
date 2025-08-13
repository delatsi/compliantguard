# AWS Deployment Permissions Issue

## Problem
```
An error occurred (AccessDenied) when calling the DescribeStacks operation: 
User: arn:aws:iam::148535712339:user/complianceguard-deploy-prod is not authorized 
to perform: cloudformation:DescribeStacks
```

## Solution: Add Missing IAM Permissions

The `complianceguard-deploy-prod` user needs the following IAM policy attached:

### Required IAM Policy - CloudFormation Deployment

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CloudFormationFullAccess",
            "Effect": "Allow",
            "Action": [
                "cloudformation:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "S3DeploymentBuckets", 
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": [
                "arn:aws:s3:::aws-sam-cli-*",
                "arn:aws:s3:::aws-sam-cli-*/*",
                "arn:aws:s3:::compliantguard-frontend-*",
                "arn:aws:s3:::compliantguard-frontend-*/*"
            ]
        },
        {
            "Sid": "IAMRoleCreation",
            "Effect": "Allow", 
            "Action": [
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:GetRole",
                "iam:PutRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:PassRole"
            ],
            "Resource": "arn:aws:iam::148535712339:role/themisguard-*"
        },
        {
            "Sid": "LambdaDeployment",
            "Effect": "Allow",
            "Action": [
                "lambda:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "APIGatewayDeployment", 
            "Effect": "Allow",
            "Action": [
                "apigateway:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudFrontAccess",
            "Effect": "Allow",
            "Action": [
                "cloudfront:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "LogsAccess",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream", 
                "logs:PutLogEvents",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams"
            ],
            "Resource": "*"
        }
    ]
}
```

## How to Apply the Fix

### Option 1: AWS Console
1. Go to IAM → Users → `complianceguard-deploy-prod`
2. Click "Add permissions" → "Attach policies directly"
3. Create new policy with JSON above
4. Name it: `CompliantGuardDeploymentPolicy`

### Option 2: AWS CLI (if you have admin access)
```bash
# Create the policy
aws iam create-policy \
  --policy-name CompliantGuardDeploymentPolicy \
  --policy-document file://deployment-policy.json

# Attach to user  
aws iam attach-user-policy \
  --user-name complianceguard-deploy-prod \
  --policy-arn arn:aws:iam::148535712339:policy/CompliantGuardDeploymentPolicy
```

## Environment-Specific Considerations

Your workflow uses different credentials per environment:
- **DEV**: `AWS_ACCESS_KEY_ID_DEV` / `AWS_SECRET_ACCESS_KEY_DEV`
- **STAGING**: `AWS_ACCESS_KEY_ID_STAGING` / `AWS_SECRET_ACCESS_KEY_STAGING`  
- **PROD**: `AWS_ACCESS_KEY_ID_PROD` / `AWS_SECRET_ACCESS_KEY_PROD`

**Ensure each deployment user has the same policy attached.**

## Verification
After applying permissions, test with:
```bash
aws cloudformation describe-stacks --stack-name compliantguard-frontend-staging
```

## Security Note
These are deployment permissions - they're broad by necessity. Consider:
1. Using separate deployment accounts per environment
2. Implementing least-privilege principles where possible
3. Regular audit of deployment permissions