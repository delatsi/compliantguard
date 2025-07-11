# Product Rename Strategy & Implementation Guide

## 🎯 **Comprehensive Product Rename Process**

This guide covers everything you need to rename your product from "ThemisGuard" to any new name while maintaining functionality and minimizing disruption.

---

## 🚀 **Quick Start: Rename in 3 Steps**

### **Step 1: Preview Changes (Dry Run)**
```bash
# Test the rename process without making changes
python scripts/rename-product.py \
  --old-name "ThemisGuard" \
  --new-name "YourNewProductName" \
  --dry-run
```

### **Step 2: Execute Rename**
```bash
# Perform the actual rename (creates automatic backup)
python scripts/rename-product.py \
  --old-name "ThemisGuard" \
  --new-name "YourNewProductName"
```

### **Step 3: Verify & Test**
```bash
# Test the application
cd frontend && npm run dev
cd ../backend && sam local start-api

# Check for any missed references
grep -r "themisguard" . --exclude-dir=backups --exclude-dir=.git
```

---

## 📋 **What Gets Renamed Automatically**

### **Code & Configuration Files**
- ✅ **All Python files** (.py)
- ✅ **All JavaScript/React files** (.js, .jsx, .ts, .tsx)
- ✅ **Configuration files** (.yaml, .yml, .json, .toml)
- ✅ **Documentation** (.md, .txt)
- ✅ **Environment files** (.env templates)
- ✅ **Docker files** (Dockerfile, docker-compose.yml)

### **Case Variations Handled**
- ✅ **themisguard** → **yournewproductname**
- ✅ **ThemisGuard** → **YourNewProductName**
- ✅ **THEMISGUARD** → **YOURNEWPRODUCTNAME**
- ✅ **themis-guard** → **your-new-product-name**
- ✅ **themis_guard** → **your_new_product_name**

### **Special Files & Configurations**
- ✅ **package.json** name field
- ✅ **SAM config** stack names
- ✅ **CloudFormation** stack names
- ✅ **README.md** main title
- ✅ **File and directory names**
- ✅ **URL patterns** and domain references

---

## 🔍 **Files That Need Manual Review**

### **External References**
These require manual updates after the automated rename:

#### **1. Domain Names & URLs**
```bash
# Current references that need manual update:
- Custom domain configurations
- SSL certificate references
- DNS records
- External documentation links
```

#### **2. Third-Party Service Names**
```bash
# Services that may need manual renaming:
- Stripe product names
- Google OAuth application name
- GCP project references
- AWS resource tags (some)
```

#### **3. Legal & Business Documents**
```bash
# Documents outside the codebase:
- Trademark applications
- Business licenses
- Marketing materials
- Customer communications
```

---

## 🛡️ **Safety Features**

### **Automatic Backup**
The script automatically creates a complete backup before making changes:
```
backups/
└── rename-20241211-143022/
    ├── backend/
    ├── frontend/
    ├── docs/
    └── [all project files]
```

### **Rollback Script**
A rollback script is automatically generated:
```bash
# Rollback if needed
./scripts/rollback-rename.sh
```

### **Dry Run Mode**
Always test first with `--dry-run`:
```bash
python scripts/rename-product.py \
  --old-name "ThemisGuard" \
  --new-name "TestName" \
  --dry-run
```

---

## 📝 **Example Rename Process**

### **Scenario: Renaming to "ComplianceShield"**

```bash
# 1. Preview the changes
python scripts/rename-product.py \
  --old-name "ThemisGuard" \
  --new-name "ComplianceShield" \
  --dry-run

# 2. Execute the rename
python scripts/rename-product.py \
  --old-name "ThemisGuard" \
  --new-name "ComplianceShield"

# 3. Verify key files were updated
grep -n "ComplianceShield" frontend/package.json
grep -n "complianceshield" samconfig.toml
grep -n "Compliance Shield" README.md
```

### **Expected Output**
```
🔄 Renaming product from 'ThemisGuard' to 'ComplianceShield'
📁 Project root: /Users/delatsi/projects/themisguard

💾 Creating backup at: backups/rename-20241211-143022
✅ Backup created successfully

🔍 Finding files to process...
📄 Found 127 files to process

✏️  backend/main.py (15 replacements)
  - Replaced 'ThemisGuard' → 'ComplianceShield' (8 times)
  - Replaced 'themisguard' → 'complianceshield' (7 times)

✏️  frontend/package.json (2 replacements)
📝 Renaming file: themisguard-api.py → complianceshield-api.py

🔧 Updating special configuration files...
📦 Updated package.json name: themisguard → complianceshield
📋 Updated SAM stack names: themisguard-api → complianceshield-api
📖 Updated README title: ThemisGuard → ComplianceShield

✅ RENAMING COMPLETE
📊 Files processed: 45
🔄 Total replacements: 312
💾 Backup location: backups/rename-20241211-143022
📜 Rollback script created: scripts/rollback-rename.sh
```

---

## 🎨 **Naming Best Practices**

### **Choose a Strong Product Name**
```yaml
Good Examples:
  - "ComplianceShield" (clear purpose, brandable)
  - "SecureGuard" (simple, memorable)
  - "HIPAAFlow" (descriptive, industry-specific)

Avoid:
  - Special characters (!@#$%)
  - Numbers at the start (123Guard)
  - Too long (VeryLongProductNameThatIsHard)
  - Generic terms (Guard, System, App)
```

### **Technical Considerations**
```yaml
Name Requirements:
  - Start with a letter
  - Alphanumeric characters only
  - 3-20 characters ideal
  - Available domain name
  - Unique trademark
```

---

## 🔄 **Post-Rename Checklist**

### **Immediate Tasks (Same Day)**
- [ ] Test application locally
- [ ] Run all automated tests
- [ ] Check for any compilation errors
- [ ] Verify frontend builds successfully
- [ ] Test API endpoints
- [ ] Review git status for unexpected changes

### **Short Term (Within Week)**
- [ ] Update external documentation
- [ ] Register new domain name
- [ ] Update Stripe product names
- [ ] Modify Google OAuth settings
- [ ] Update AWS resource tags
- [ ] Test deployment pipeline

### **Medium Term (Within Month)**
- [ ] Update marketing materials
- [ ] Notify existing users (if any)
- [ ] Update legal documents
- [ ] File trademark application
- [ ] Update business cards/materials
- [ ] Search engine optimization

---

## 🚨 **Troubleshooting Common Issues**

### **Build Errors After Rename**
```bash
# 1. Clear build caches
rm -rf frontend/node_modules frontend/dist
rm -rf backend/.aws-sam

# 2. Reinstall dependencies
cd frontend && npm install
cd ../backend && sam build

# 3. Check for missed references
grep -r "themisguard" . --exclude-dir=backups --exclude-dir=.git
```

### **Deployment Issues**
```bash
# 1. Update stack names in deployment scripts
grep -r "themisguard-api" scripts/

# 2. Check CloudFormation stack names
aws cloudformation list-stacks --query 'StackSummaries[?contains(StackName, `themisguard`)]'

# 3. May need to deploy with new stack names
sam deploy --stack-name complianceshield-api-dev
```

### **Database/State Issues**
```bash
# The rename doesn't affect existing data:
# - DynamoDB data remains unchanged
# - S3 objects remain unchanged  
# - Stripe subscriptions remain unchanged
# Only configuration and code are updated
```

---

## 🔒 **Security Considerations**

### **Secrets and Credentials**
```bash
# After rename, verify these still work:
- AWS IAM roles and policies
- Stripe webhook endpoints
- Google OAuth redirect URIs
- Environment variables in CI/CD
```

### **Domain and SSL Certificates**
```bash
# Plan for new domains:
1. Register new domain
2. Request new SSL certificates
3. Update DNS records
4. Update CDN configurations
5. Redirect old URLs (if public)
```

---

## 💰 **Cost Implications**

### **One-Time Costs**
```yaml
Domain Registration: $12-50/year
SSL Certificates: $0 (Let's Encrypt) or $50-200/year
Legal Review: $500-2000 (if needed)
Marketing Updates: $200-1000
```

### **Ongoing Considerations**
```yaml
No Additional Infrastructure Costs:
- Same AWS resources
- Same Stripe account
- Same deployment pipeline
- Same monitoring setup
```

---

## 📊 **Testing Strategy**

### **Automated Testing**
```bash
# 1. Unit tests should still pass
cd backend && python -m pytest
cd frontend && npm test

# 2. Integration tests
sam local start-api &
cd frontend && npm run test:integration

# 3. Build tests
sam build
cd frontend && npm run build
```

### **Manual Testing Checklist**
- [ ] Frontend loads correctly
- [ ] Authentication works (Google SSO)
- [ ] API endpoints respond
- [ ] Database operations work
- [ ] Billing/Stripe integration works
- [ ] Admin dashboard accessible
- [ ] File uploads/downloads work

---

## 🎯 **Example: Full Rename to "SecureFlow"**

```bash
# Complete example workflow
cd /Users/delatsi/projects/themisguard

# 1. Preview
python scripts/rename-product.py \
  --old-name "ThemisGuard" \
  --new-name "SecureFlow" \
  --dry-run

# 2. Execute rename
python scripts/rename-product.py \
  --old-name "ThemisGuard" \
  --new-name "SecureFlow"

# 3. Test locally
cd frontend && npm install && npm run dev &
cd backend && sam build && sam local start-api &

# 4. Check for issues
curl http://localhost:3000
curl http://localhost:3001/health

# 5. Deploy to dev environment
sam deploy --config-env dev --stack-name secureflow-api-dev

# 6. Commit changes
git add .
git commit -m "Rename product from ThemisGuard to SecureFlow"
```

---

## 🎊 **Success Metrics**

### **Technical Success**
- ✅ All tests pass
- ✅ Application builds without errors
- ✅ Deployment pipeline works
- ✅ No broken references found

### **Business Success**
- ✅ Domain registered and configured
- ✅ Branding updated consistently
- ✅ Legal documents updated
- ✅ Customer communication plan ready

---

**Ready to rename?** The automated script handles 95% of the work, leaving you to focus on the strategic aspects of your rebrand!