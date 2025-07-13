# Secure GCP Authentication Architecture for CompliantGuard

## Security Requirements for HIPAA Compliance

1. **Encryption at rest** - All GCP credentials encrypted with AWS KMS
2. **Least privilege** - Service accounts with minimal required permissions
3. **Audit trail** - All credential access logged
4. **Rotation** - Support for credential rotation
5. **Customer isolation** - Each customer's credentials isolated

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Setup    │    │   CompliantGuard │    │   GCP Project   │
│   Instructions  │───▶│   Backend        │───▶│   (Customer)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   AWS KMS +      │
                       │   DynamoDB       │
                       │   (Encrypted)    │
                       └──────────────────┘
```

## Option 1: Service Account JSON (Recommended)

### Customer Setup Process
1. **Create service account** in their GCP project
2. **Assign minimal permissions** for compliance scanning
3. **Download JSON key** securely
4. **Upload to CompliantGuard** (encrypted immediately)

### Permissions Required
```json
{
  "roles": [
    "roles/cloudasset.viewer",
    "roles/compute.viewer",
    "roles/storage.legacyBucketReader",
    "roles/sql.viewer",
    "roles/iam.securityReviewer"
  ]
}
```

## Option 2: Workload Identity (Advanced)

### For customers using GKE/Cloud Run
- Cross-cloud identity federation
- No long-lived keys
- More complex setup

## Implementation Plan

### 1. KMS Key Setup
```bash
# Create KMS key for GCP credentials
aws kms create-key \
  --description "CompliantGuard GCP Credentials Encryption" \
  --key-usage ENCRYPT_DECRYPT \
  --key-spec SYMMETRIC_DEFAULT

# Create alias
aws kms create-alias \
  --alias-name alias/compliantguard-gcp-credentials \
  --target-key-id $KEY_ID
```

### 2. DynamoDB Schema
```json
{
  "TableName": "compliantguard-gcp-credentials",
  "KeySchema": [
    {"AttributeName": "user_id", "KeyType": "HASH"},
    {"AttributeName": "project_id", "KeyType": "RANGE"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "user_id", "AttributeType": "S"},
    {"AttributeName": "project_id", "AttributeType": "S"}
  ],
  "Item": {
    "user_id": "uuid",
    "project_id": "gcp-project-id",
    "encrypted_credentials": "KMS_ENCRYPTED_BLOB",
    "service_account_email": "scanner@project.iam.gserviceaccount.com",
    "created_at": "2024-01-15T10:30:00Z",
    "last_used": "2024-01-15T10:30:00Z",
    "status": "active|revoked"
  }
}
```

### 3. Backend Implementation
```python
import boto3
import json
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GCPCredentialManager:
    def __init__(self):
        self.kms_client = boto3.client('kms')
        self.dynamodb = boto3.resource('dynamodb')
        self.creds_table = self.dynamodb.Table('compliantguard-gcp-credentials')
        self.kms_key_id = 'alias/compliantguard-gcp-credentials'
    
    async def store_credentials(self, user_id: str, project_id: str, 
                              service_account_json: dict):
        """Encrypt and store GCP service account credentials"""
        try:
            # Validate the service account
            await self._validate_service_account(service_account_json, project_id)
            
            # Encrypt credentials with KMS
            credentials_str = json.dumps(service_account_json)
            encrypted_response = self.kms_client.encrypt(
                KeyId=self.kms_key_id,
                Plaintext=credentials_str.encode('utf-8')
            )
            
            encrypted_blob = base64.b64encode(
                encrypted_response['CiphertextBlob']
            ).decode('utf-8')
            
            # Store in DynamoDB
            self.creds_table.put_item(
                Item={
                    'user_id': user_id,
                    'project_id': project_id,
                    'encrypted_credentials': encrypted_blob,
                    'service_account_email': service_account_json['client_email'],
                    'created_at': datetime.utcnow().isoformat(),
                    'last_used': datetime.utcnow().isoformat(),
                    'status': 'active'
                }
            )
            
            return {"success": True, "project_id": project_id}
            
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            raise HTTPException(status_code=500, detail="Failed to store credentials")
    
    async def get_credentials(self, user_id: str, project_id: str) -> dict:
        """Decrypt and return GCP credentials for scanning"""
        try:
            # Get encrypted credentials from DynamoDB
            response = self.creds_table.get_item(
                Key={'user_id': user_id, 'project_id': project_id}
            )
            
            if 'Item' not in response:
                raise HTTPException(status_code=404, detail="Credentials not found")
            
            item = response['Item']
            if item['status'] != 'active':
                raise HTTPException(status_code=403, detail="Credentials revoked")
            
            # Decrypt with KMS
            encrypted_blob = base64.b64decode(item['encrypted_credentials'])
            decrypted_response = self.kms_client.decrypt(
                CiphertextBlob=encrypted_blob
            )
            
            credentials_json = json.loads(
                decrypted_response['Plaintext'].decode('utf-8')
            )
            
            # Update last used timestamp
            self.creds_table.update_item(
                Key={'user_id': user_id, 'project_id': project_id},
                UpdateExpression='SET last_used = :timestamp',
                ExpressionAttributeValues={':timestamp': datetime.utcnow().isoformat()}
            )
            
            return credentials_json
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve credentials")
    
    async def _validate_service_account(self, creds: dict, project_id: str):
        """Validate service account has required permissions"""
        try:
            # Create credentials object
            credentials = service_account.Credentials.from_service_account_info(creds)
            
            # Test basic access
            service = build('cloudasset', 'v1', credentials=credentials)
            
            # Verify project access
            parent = f"projects/{project_id}"
            request = service.assets().list(parent=parent, pageSize=1)
            response = request.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Service account validation failed: {e}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid service account or insufficient permissions"
            )
```

### 4. Frontend Integration
```javascript
// GCP Credentials Upload Component
import React, { useState } from 'react';

const GCPCredentialsSetup = ({ projectId, onSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [credentials, setCredentials] = useState(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const json = JSON.parse(e.target.result);
          setCredentials(json);
        } catch (error) {
          alert('Invalid JSON file');
        }
      };
      reader.readAsText(file);
    }
  };

  const uploadCredentials = async () => {
    setUploading(true);
    try {
      const response = await fetch('/api/v1/gcp/credentials', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          project_id: projectId,
          service_account_json: credentials
        })
      });

      if (response.ok) {
        onSuccess();
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      alert('Failed to upload credentials');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="gcp-credentials-setup">
      <h3>Add GCP Project Credentials</h3>
      <p>Upload your service account JSON key to enable scanning.</p>
      
      <input
        type="file"
        accept=".json"
        onChange={handleFileUpload}
        className="file-input"
      />
      
      {credentials && (
        <div className="credentials-preview">
          <p>Service Account: {credentials.client_email}</p>
          <p>Project: {credentials.project_id}</p>
          <button
            onClick={uploadCredentials}
            disabled={uploading}
            className="upload-button"
          >
            {uploading ? 'Uploading...' : 'Upload Credentials'}
          </button>
        </div>
      )}
    </div>
  );
};
```

## Security Considerations

### Encryption
- **KMS encryption** for all stored credentials
- **Envelope encryption** for large payloads
- **Key rotation** support

### Access Control
- **IAM policies** restrict KMS key access
- **VPC endpoints** for internal AWS communication
- **CloudTrail logging** for all key operations

### Audit & Compliance
- **All credential access logged**
- **Usage tracking** per project
- **Automatic credential expiry** warnings
- **Emergency revocation** capability

### Network Security
- **TLS 1.3** for all data in transit
- **Certificate pinning** for GCP API calls
- **WAF protection** for upload endpoints

## Customer Setup Instructions

### Step 1: Create Service Account
```bash
# In customer's GCP project
gcloud iam service-accounts create compliantguard-scanner \
  --description="CompliantGuard HIPAA Scanner" \
  --display-name="CompliantGuard Scanner"
```

### Step 2: Assign Permissions
```bash
# Minimum required permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:compliantguard-scanner@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudasset.viewer"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:compliantguard-scanner@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.viewer"
```

### Step 3: Create Key
```bash
gcloud iam service-accounts keys create compliantguard-key.json \
  --iam-account=compliantguard-scanner@PROJECT_ID.iam.gserviceaccount.com
```

### Step 4: Upload to CompliantGuard
- Securely upload JSON key via web interface
- Delete local copy after upload
- Credentials encrypted immediately upon receipt

This architecture provides enterprise-grade security for GCP credentials while maintaining usability for customers.