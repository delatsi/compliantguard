#!/bin/bash

echo "🔧 Fixing SAM Deployment Configuration"
echo "====================================="

echo "🔍 Current SAM configuration issues:"
echo "- Stack names are being generated with timestamps"
echo "- Each deployment creates new DynamoDB tables"
echo "- Old tables are never cleaned up"
echo ""

echo "✅ Solutions to implement:"
echo "1. Fix stack naming in deployment commands"
echo "2. Use stable table names instead of stack-based names"
echo "3. Add table deletion protection for production"
echo ""

echo "🎯 Immediate fixes:"
echo ""

echo "1. Update deployment commands to use fixed stack names:"
echo "   Instead of: sam deploy --stack-name themisguard-api-dev-\$(date +%Y%m%d-%H%M%S)"
echo "   Use:        sam deploy --config-env dev"
echo ""

echo "2. Fix template.yaml table naming:"
echo "   Replace: TableName: !Sub \"\${AWS::StackName}-scans\""
echo "   With:    TableName: !Sub \"themisguard-\${Environment}-scans\""
echo ""

echo "3. Deploy with environment-specific configs:"
echo "   Development: sam deploy --config-env dev"
echo "   Staging:     sam deploy --config-env staging"
echo "   Production:  sam deploy --config-env prod"
echo ""

echo "4. Set table deletion protection:"
echo "   DeletionProtectionEnabled: !If [IsProduction, true, false]"
echo ""

echo "⚠️  Next steps:"
echo "1. Clean up duplicate tables with emergency-dynamodb-cleanup.sh"
echo "2. Update template.yaml with stable table names"
echo "3. Update deployment scripts to use --config-env"
echo "4. Test deployment to ensure no new duplicates are created"