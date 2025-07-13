# GCP Project Setup Guide for CompliantGuard

## Overview
This guide helps you securely connect your GCP project to CompliantGuard for HIPAA compliance scanning.

## Prerequisites
- GCP project with billing enabled
- Project owner or security admin permissions
- Google Cloud SDK installed (optional)

## Step 1: Create a Service Account

### Option A: Using Google Cloud Console (Recommended)

1. **Go to the IAM & Admin section**
   - Open [Google Cloud Console](https://console.cloud.google.com)
   - Select your project
   - Navigate to **IAM & Admin** → **Service Accounts**

2. **Create Service Account**
   - Click **"Create Service Account"**
   - **Name**: `compliantguard-scanner`
   - **Description**: `CompliantGuard HIPAA compliance scanner`
   - Click **"Create and Continue"**

3. **Grant Required Permissions**
   Add these roles to the service account:
   - ✅ **Cloud Asset Viewer** (`roles/cloudasset.viewer`)
   - ✅ **Compute Viewer** (`roles/compute.viewer`)
   - ✅ **Storage Legacy Bucket Reader** (`roles/storage.legacyBucketReader`)
   - ✅ **Cloud SQL Viewer** (`roles/sql.viewer`)
   - ✅ **Security Reviewer** (`roles/iam.securityReviewer`)

4. **Create and Download Key**
   - Click on the created service account
   - Go to **"Keys"** tab
   - Click **"Add Key"** → **"Create new key"**
   - Select **JSON** format
   - Click **"Create"** - the key file will download automatically

### Option B: Using gcloud CLI

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Create service account
gcloud iam service-accounts create compliantguard-scanner \
  --project=$PROJECT_ID \
  --description="CompliantGuard HIPAA compliance scanner" \
  --display-name="CompliantGuard Scanner"

# Assign required roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:compliantguard-scanner@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudasset.viewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:compliantguard-scanner@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.viewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:compliantguard-scanner@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.legacyBucketReader"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:compliantguard-scanner@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/sql.viewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:compliantguard-scanner@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.securityReviewer"

# Create and download key
gcloud iam service-accounts keys create compliantguard-key.json \
  --iam-account=compliantguard-scanner@$PROJECT_ID.iam.gserviceaccount.com
```

## Step 2: Upload Credentials to CompliantGuard

1. **Log in to CompliantGuard**
   - Go to [compliantguard.datfunc.com](https://compliantguard.datfunc.com)
   - Sign in to your account

2. **Navigate to Scan Page**
   - Click **"New Scan"** or **"Scan"** in the navigation

3. **Add GCP Project**
   - Enter your **GCP Project ID**
   - Click **"Add Credentials"**

4. **Upload Service Account Key**
   - Click **"Choose File"** or drag and drop
   - Select the downloaded JSON key file
   - Click **"Upload Credentials"**

5. **Verify Connection**
   - CompliantGuard will test the connection
   - You should see a ✅ "Connected" status

## Step 3: Run Your First Scan

1. **Start Compliance Scan**
   - Click **"Start Scan"**
   - Wait for the scan to complete (typically 2-5 minutes)

2. **Review Results**
   - View compliance score and violations
   - Download detailed reports
   - Track progress over time

## Security Features

### 🔒 **Enterprise-Grade Security**
- **Encrypted Storage**: All credentials encrypted with AWS KMS
- **Zero Trust**: Credentials never stored in plaintext
- **Audit Logging**: All access logged and monitored
- **Least Privilege**: Minimal required permissions only

### 🔑 **Credential Management**
- **Automatic Rotation**: Supports credential rotation
- **Revocation**: Instantly revoke access if needed
- **Usage Tracking**: Monitor when credentials are used
- **Expiry Alerts**: Notifications before keys expire

## Required Permissions Explained

| Permission | Why It's Needed | What It Accesses |
|------------|-----------------|------------------|
| **Cloud Asset Viewer** | Discover all resources in your project | Resource inventory and metadata |
| **Compute Viewer** | Check VM configurations and security | Virtual machines, networks, firewalls |
| **Storage Bucket Reader** | Scan storage bucket policies | Cloud Storage bucket permissions |
| **Cloud SQL Viewer** | Review database configurations | Database instances and settings |
| **Security Reviewer** | Analyze IAM policies and access | Identity and access management |

## Troubleshooting

### Common Issues

**❌ "Invalid service account"**
- Verify the JSON key file is valid
- Check that the service account exists in the correct project
- Ensure the project ID matches

**❌ "Insufficient permissions"**
- Verify all required roles are assigned
- Check that APIs are enabled in your GCP project
- Confirm the service account is active

**❌ "Project not found"**
- Double-check the project ID spelling
- Ensure the project exists and is active
- Verify billing is enabled on the project

### Enable Required APIs

Some GCP projects may need these APIs enabled:
```bash
gcloud services enable cloudasset.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable iam.googleapis.com
```

### Security Best Practices

1. **Store Keys Securely**
   - Delete the downloaded JSON file after uploading to CompliantGuard
   - Don't commit keys to version control
   - Don't share keys via email or chat

2. **Regular Rotation**
   - Rotate service account keys every 90 days
   - Monitor key usage in GCP IAM console
   - Remove unused keys immediately

3. **Monitor Access**
   - Review audit logs regularly
   - Set up alerts for unusual activity
   - Use GCP Security Command Center for monitoring

## Support

Need help? Contact us:
- 📧 **Email**: support@datfunc.com
- 💬 **Chat**: Available in the CompliantGuard dashboard
- 📖 **Documentation**: [docs.compliantguard.com](https://docs.compliantguard.com)

---

**Security Note**: CompliantGuard uses bank-level encryption and follows SOC 2 Type II standards. Your GCP credentials are encrypted with AWS KMS and never stored in plaintext.