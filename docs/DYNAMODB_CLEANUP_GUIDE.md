# DynamoDB Tables Cleanup & Deployment Fix

## 🚨 **Current Problem**

You're right - every deployment is creating new tables with stack-specific names, which would cause data loss in production. Here's what's happening:

### **Table Naming Pattern:**
```
${AWS::StackName}-tablename

Examples:
- themisguard-api-scans
- themisguard-api-dev-scans  
- themisguard-api-staging-scans
- themisguard-api-prod-scans
```

### **Multiple Stack Deployments:**
- **Default:** `themisguard-api`
- **Dev:** `themisguard-api-dev`
- **Staging:** `themisguard-api-staging`
- **Prod:** `themisguard-api-prod`

Each stack creates its own set of tables!

## 🧹 **Cleanup Steps**

### **Step 1: List All DynamoDB Tables**
```bash
aws dynamodb list-tables --region us-east-1
```

### **Step 2: Identify Tables to Keep vs Delete**

**Keep (Production Data):**
- `themisguard-api-prod-*` (if exists)
- `compliantguard-gcp-credentials` (from our setup script)
- `themisguard-users` (from local dev script)

**Delete (Development/Duplicate Tables):**
- `themisguard-api-scans`
- `themisguard-api-dev-*`
- `themisguard-api-staging-*`
- Any other `themisguard-api-*` variants

### **Step 3: Safe Cleanup Commands**

**⚠️ BACKUP FIRST if there's any important data:**
```bash
# Backup before deletion (if needed)
aws dynamodb create-backup \
  --table-name <table-name> \
  --backup-name "cleanup-backup-$(date +%Y%m%d)"
```

**Delete duplicate tables:**
```bash
# List tables and identify duplicates
aws dynamodb list-tables --region us-east-1 | grep themisguard

# Delete specific tables (example)
aws dynamodb delete-table --table-name themisguard-api-scans --region us-east-1
aws dynamodb delete-table --table-name themisguard-api-dev-scans --region us-east-1
# ... repeat for other duplicates
```

## 🔧 **Long-term Fix: Stable Table Names**

### **Option 1: Fixed Table Names (Recommended)**

Update `template.yaml` to use fixed table names instead of stack-based names:

```yaml
# OLD (creates new tables per stack):
TableName: !Sub "${AWS::StackName}-scans"

# NEW (stable table names):
TableName: !Sub "themisguard-${Environment}-scans"
```

### **Option 2: Shared Tables Across Environments**

```yaml
# Use same table names across all environments
TableName: "themisguard-scans"
TableName: "themisguard-users"
```

## 🏗 **Recommended Production Architecture**

### **Table Naming Strategy:**
```
Production: themisguard-prod-scans
Staging:    themisguard-staging-scans  
Dev:        themisguard-dev-scans
Local:      themisguard-local-scans
```

### **Benefits:**
- ✅ Environment separation
- ✅ No data loss on deployment
- ✅ Predictable table names
- ✅ Easy backup/restore between environments

## 📋 **Immediate Action Plan**

### **Step 1: Audit Current Tables**
```bash
# Create a script to list all tables
cat > scripts/audit-dynamodb-tables.sh << 'EOF'
#!/bin/bash
echo "📋 Current DynamoDB Tables:"
echo "=========================="
aws dynamodb list-tables --region us-east-1 --output table

echo ""
echo "📊 Table Details:"
echo "=================="
for table in $(aws dynamodb list-tables --region us-east-1 --output text --query 'TableNames[]'); do
    echo "Table: $table"
    aws dynamodb describe-table --table-name "$table" --region us-east-1 \
        --query 'Table.{Name:TableName,Status:TableStatus,Items:ItemCount,Size:TableSizeBytes}' \
        --output table
    echo ""
done
EOF

chmod +x scripts/audit-dynamodb-tables.sh
./scripts/audit-dynamodb-tables.sh
```

### **Step 2: Create Cleanup Script**
```bash
cat > scripts/cleanup-duplicate-tables.sh << 'EOF'
#!/bin/bash

echo "🧹 DynamoDB Tables Cleanup"
echo "=========================="

# List tables to review
echo "📋 Current tables:"
aws dynamodb list-tables --region us-east-1 --output table

echo ""
echo "⚠️  Tables that will be DELETED:"
echo "- themisguard-api-scans"
echo "- themisguard-api-dev-scans" 
echo "- themisguard-api-staging-scans"
echo "- (any other themisguard-api-* variants)"

echo ""
echo "✅ Tables that will be KEPT:"
echo "- themisguard-api-prod-* (production data)"
echo "- compliantguard-gcp-credentials"
echo "- themisguard-users"

echo ""
read -p "Continue with cleanup? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️ Starting cleanup..."
    
    # Delete development/duplicate tables
    for table in $(aws dynamodb list-tables --region us-east-1 --output text --query 'TableNames[]' | grep -E '^themisguard-api-(scans|users|admin|subscriptions|usage|invoices|webhook)'); do
        echo "Deleting: $table"
        aws dynamodb delete-table --table-name "$table" --region us-east-1
    done
    
    echo "✅ Cleanup complete!"
else
    echo "❌ Cleanup cancelled"
fi
EOF

chmod +x scripts/cleanup-duplicate-tables.sh
```

### **Step 3: Fix SAM Template**

Update the table names in `template.yaml`:

```yaml
# Replace all occurrences of:
TableName: !Sub "${AWS::StackName}-scans"
# With:
TableName: !Sub "themisguard-${Environment}-scans"
```

## 🎯 **Missing: GCP Credentials Table**

I notice the SAM template is missing the GCP credentials table! Add this:

```yaml
# Add to template.yaml after other tables
GCPCredentialsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub "themisguard-${Environment}-gcp-credentials"
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: user_id
        AttributeType: S
      - AttributeName: project_id
        AttributeType: S
    KeySchema:
      - AttributeName: user_id
        KeyType: HASH
      - AttributeName: project_id
        KeyType: RANGE
    PointInTimeRecoverySpecification:
      PointInTimeRecoveryEnabled: true
    SSESpecification:
      SSEEnabled: true
    DeletionProtectionEnabled: !If [IsProduction, true, false]
```

## 🚀 **Next Steps**

1. **Run audit script** to see current state
2. **Review tables** and identify what can be safely deleted
3. **Run cleanup script** to remove duplicates
4. **Update SAM template** with stable naming
5. **Add GCP credentials table** to template
6. **Test deployment** to ensure no new duplicates are created

This will prevent future data loss and clean up the current mess! 🎯