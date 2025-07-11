"""
Customer-Specific Encryption Service
Provides customer-isolated encryption keys and data protection
"""

import boto3
import json
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..core.config import settings


class CustomerEncryptionService:
    """
    Customer-specific encryption service using AWS KMS and envelope encryption
    Each customer gets their own KMS key for complete data isolation
    """
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.kms = boto3.client('kms', region_name=settings.AWS_REGION)
        self.customer_key_alias = f"alias/customer-{customer_id}-key"
        self._customer_key_id = None  # Cached key ID
    
    async def get_customer_key_id(self) -> str:
        """Get or create customer-specific KMS key"""
        if self._customer_key_id:
            return self._customer_key_id
        
        try:
            # Try to get existing key
            response = self.kms.describe_key(KeyId=self.customer_key_alias)
            self._customer_key_id = response['KeyMetadata']['KeyId']
            return self._customer_key_id
            
        except self.kms.exceptions.NotFoundException:
            # Create new customer-specific key
            return await self._create_customer_key()
    
    async def _create_customer_key(self) -> str:
        """Create a new customer-specific KMS key"""
        
        # Create the key
        key_response = self.kms.create_key(
            Description=f"Customer-specific encryption key for {self.customer_id}",
            KeyUsage='ENCRYPT_DECRYPT',
            KeySpec='SYMMETRIC_DEFAULT',
            Policy=json.dumps(self._get_customer_key_policy()),
            Tags=[
                {'TagKey': 'Customer', 'TagValue': self.customer_id},
                {'TagKey': 'Purpose', 'TagValue': 'CustomerDataEncryption'},
                {'TagKey': 'Project', 'TagValue': 'themisguard'},
                {'TagKey': 'Environment', 'TagValue': settings.ENVIRONMENT},
                {'TagKey': 'DataClassification', 'TagValue': 'PHI'},
                {'TagKey': 'RetentionPeriod', 'TagValue': '7years'}
            ]
        )
        
        key_id = key_response['KeyMetadata']['KeyId']
        
        # Create alias for easy reference
        self.kms.create_alias(
            AliasName=self.customer_key_alias,
            TargetKeyId=key_id
        )
        
        self._customer_key_id = key_id
        return key_id
    
    def _get_customer_key_policy(self) -> Dict[str, Any]:
        """Get IAM policy for customer-specific key"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{boto3.Session().get_credentials().access_key}:root"
                    },
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow Lambda Service Access",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "kms:ViaService": f"dynamodb.{settings.AWS_REGION}.amazonaws.com"
                        }
                    }
                }
            ]
        }
    
    async def encrypt_customer_data(self, data: Dict[str, Any], context: Dict[str, str]) -> Dict[str, Any]:
        """
        Encrypt customer data using envelope encryption
        
        Args:
            data: The data to encrypt
            context: Encryption context for additional security
            
        Returns:
            Dictionary containing encrypted data and metadata
        """
        
        # Validate encryption context
        required_context = {
            'customer_id': self.customer_id,
            'purpose': context.get('purpose', 'data_protection'),
            'timestamp': datetime.utcnow().isoformat()
        }
        required_context.update(context)
        
        # Get customer key
        key_id = await self.get_customer_key_id()
        
        # Generate data encryption key (DEK)
        dek_response = self.kms.generate_data_key(
            KeyId=key_id,
            KeySpec='AES_256',
            EncryptionContext=required_context
        )
        
        # Encrypt the data with the DEK
        plaintext_data = json.dumps(data, separators=(',', ':'), sort_keys=True)
        fernet = Fernet(base64.urlsafe_b64encode(dek_response['Plaintext'][:32]))
        encrypted_data = fernet.encrypt(plaintext_data.encode('utf-8'))
        
        # Create the encrypted record
        encrypted_record = {
            'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
            'encrypted_dek': base64.b64encode(dek_response['CiphertextBlob']).decode('utf-8'),
            'encryption_context': required_context,
            'key_id': key_id,
            'algorithm': 'AES-256-GCM',
            'customer_id': self.customer_id,
            'encrypted_at': datetime.utcnow().isoformat(),
            'data_hash': hashlib.sha256(plaintext_data.encode('utf-8')).hexdigest(),
            'format_version': '1.0'
        }
        
        return encrypted_record
    
    async def decrypt_customer_data(self, encrypted_record: Dict[str, Any], context: Dict[str, str]) -> Dict[str, Any]:
        """
        Decrypt customer data using envelope encryption
        
        Args:
            encrypted_record: The encrypted record from storage
            context: Decryption context for validation
            
        Returns:
            The decrypted data as a dictionary
        """
        
        # Validate the record format
        required_fields = ['encrypted_data', 'encrypted_dek', 'encryption_context', 'customer_id']
        for field in required_fields:
            if field not in encrypted_record:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate customer boundary
        if encrypted_record['customer_id'] != self.customer_id:
            raise PermissionError(f"Cannot decrypt data for different customer: {encrypted_record['customer_id']}")
        
        # Decrypt the data encryption key
        try:
            dek_response = self.kms.decrypt(
                CiphertextBlob=base64.b64decode(encrypted_record['encrypted_dek']),
                EncryptionContext=encrypted_record['encryption_context']
            )
        except Exception as e:
            raise PermissionError(f"Failed to decrypt DEK: {str(e)}")
        
        # Decrypt the actual data
        try:
            fernet = Fernet(base64.urlsafe_b64encode(dek_response['Plaintext'][:32]))
            decrypted_bytes = fernet.decrypt(
                base64.b64decode(encrypted_record['encrypted_data'])
            )
            decrypted_text = decrypted_bytes.decode('utf-8')
            
            # Verify data integrity
            if 'data_hash' in encrypted_record:
                expected_hash = encrypted_record['data_hash']
                actual_hash = hashlib.sha256(decrypted_text.encode('utf-8')).hexdigest()
                if actual_hash != expected_hash:
                    raise ValueError("Data integrity check failed")
            
            return json.loads(decrypted_text)
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    async def encrypt_field(self, field_value: str, field_name: str) -> Dict[str, str]:
        """
        Encrypt a specific field value for field-level encryption
        
        Args:
            field_value: The value to encrypt
            field_name: The name of the field (for context)
            
        Returns:
            Dictionary with encrypted value and metadata
        """
        
        context = {
            'customer_id': self.customer_id,
            'field_name': field_name,
            'purpose': 'field_encryption',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        encrypted_data = await self.encrypt_customer_data(
            {'field_value': field_value},
            context
        )
        
        return {
            'encrypted_value': encrypted_data['encrypted_data'],
            'encrypted_dek': encrypted_data['encrypted_dek'],
            'encryption_context': encrypted_data['encryption_context'],
            'field_hash': hashlib.sha256(field_value.encode('utf-8')).hexdigest()[:16],  # For searching
            'encrypted_at': encrypted_data['encrypted_at']
        }
    
    async def decrypt_field(self, encrypted_field: Dict[str, str]) -> str:
        """
        Decrypt a field value from field-level encryption
        
        Args:
            encrypted_field: The encrypted field dictionary
            
        Returns:
            The decrypted field value
        """
        
        # Reconstruct the encrypted record format
        encrypted_record = {
            'encrypted_data': encrypted_field['encrypted_value'],
            'encrypted_dek': encrypted_field['encrypted_dek'],
            'encryption_context': encrypted_field['encryption_context'],
            'customer_id': self.customer_id
        }
        
        decrypted_data = await self.decrypt_customer_data(encrypted_record, {})
        return decrypted_data['field_value']
    
    async def rotate_customer_key(self) -> str:
        """
        Rotate the customer's encryption key
        
        Returns:
            New key ID
        """
        
        current_key_id = await self.get_customer_key_id()
        
        # Create new key version
        response = self.kms.create_key(
            Description=f"Rotated customer encryption key for {self.customer_id}",
            KeyUsage='ENCRYPT_DECRYPT',
            KeySpec='SYMMETRIC_DEFAULT',
            Policy=json.dumps(self._get_customer_key_policy()),
            Tags=[
                {'TagKey': 'Customer', 'TagValue': self.customer_id},
                {'TagKey': 'Purpose', 'TagValue': 'CustomerDataEncryption'},
                {'TagKey': 'Project', 'TagValue': 'themisguard'},
                {'TagKey': 'Environment', 'TagValue': settings.ENVIRONMENT},
                {'TagKey': 'RotatedFrom', 'TagValue': current_key_id},
                {'TagKey': 'RotatedAt', 'TagValue': datetime.utcnow().isoformat()}
            ]
        )
        
        new_key_id = response['KeyMetadata']['KeyId']
        
        # Update alias to point to new key
        self.kms.update_alias(
            AliasName=self.customer_key_alias,
            TargetKeyId=new_key_id
        )
        
        # Schedule deletion of old key (after retention period)
        self.kms.schedule_key_deletion(
            KeyId=current_key_id,
            PendingWindowInDays=30  # Minimum waiting period
        )
        
        self._customer_key_id = new_key_id
        return new_key_id
    
    async def delete_customer_key(self) -> bool:
        """
        Schedule deletion of customer's encryption key
        WARNING: This will make all encrypted data unrecoverable
        
        Returns:
            True if deletion was scheduled successfully
        """
        
        try:
            key_id = await self.get_customer_key_id()
            
            # Schedule key deletion (minimum 7 days)
            self.kms.schedule_key_deletion(
                KeyId=key_id,
                PendingWindowInDays=7
            )
            
            # Delete the alias
            self.kms.delete_alias(AliasName=self.customer_key_alias)
            
            return True
            
        except Exception as e:
            print(f"Failed to delete customer key: {e}")
            return False
    
    async def get_key_metadata(self) -> Dict[str, Any]:
        """Get metadata about the customer's encryption key"""
        
        try:
            key_id = await self.get_customer_key_id()
            response = self.kms.describe_key(KeyId=key_id)
            
            return {
                'key_id': response['KeyMetadata']['KeyId'],
                'arn': response['KeyMetadata']['Arn'],
                'creation_date': response['KeyMetadata']['CreationDate'].isoformat(),
                'enabled': response['KeyMetadata']['Enabled'],
                'key_state': response['KeyMetadata']['KeyState'],
                'key_usage': response['KeyMetadata']['KeyUsage'],
                'key_spec': response['KeyMetadata']['KeySpec'],
                'customer_id': self.customer_id
            }
            
        except Exception as e:
            return {'error': str(e), 'customer_id': self.customer_id}


class FieldEncryptionMixin:
    """
    Mixin class to add field-level encryption to data models
    """
    
    ENCRYPTED_FIELDS = set()  # Override in subclasses
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.encryption_service = CustomerEncryptionService(customer_id)
    
    async def encrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in a data dictionary"""
        
        encrypted_data = data.copy()
        
        for field_name, field_value in data.items():
            if field_name in self.ENCRYPTED_FIELDS and field_value is not None:
                # Encrypt this field
                encrypted_field = await self.encryption_service.encrypt_field(
                    str(field_value), field_name
                )
                
                # Replace with encrypted version
                encrypted_data[f"{field_name}_encrypted"] = encrypted_field
                encrypted_data[f"{field_name}_hash"] = encrypted_field['field_hash']
                
                # Remove plaintext
                del encrypted_data[field_name]
        
        return encrypted_data
    
    async def decrypt_sensitive_fields(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in a data dictionary"""
        
        decrypted_data = encrypted_data.copy()
        
        # Find encrypted fields
        encrypted_field_names = [
            field.replace('_encrypted', '') 
            for field in encrypted_data.keys() 
            if field.endswith('_encrypted')
        ]
        
        for field_name in encrypted_field_names:
            encrypted_field_key = f"{field_name}_encrypted"
            
            if encrypted_field_key in encrypted_data:
                try:
                    # Decrypt the field
                    decrypted_value = await self.encryption_service.decrypt_field(
                        encrypted_data[encrypted_field_key]
                    )
                    
                    # Add decrypted value
                    decrypted_data[field_name] = decrypted_value
                    
                    # Remove encrypted version
                    del decrypted_data[encrypted_field_key]
                    if f"{field_name}_hash" in decrypted_data:
                        del decrypted_data[f"{field_name}_hash"]
                        
                except Exception as e:
                    print(f"Failed to decrypt field {field_name}: {e}")
                    # Keep encrypted version if decryption fails
        
        return decrypted_data


# Example usage for compliance scan data
class ComplianceScanData(FieldEncryptionMixin):
    """
    Compliance scan data with field-level encryption
    """
    
    ENCRYPTED_FIELDS = {
        'customer_email', 'customer_phone', 'ip_addresses', 
        'server_names', 'database_connections', 'api_keys',
        'user_data', 'system_logs'
    }
    
    def __init__(self, customer_id: str):
        super().__init__(customer_id)
    
    async def prepare_for_storage(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare scan data for secure storage"""
        
        # Encrypt sensitive fields
        encrypted_data = await self.encrypt_sensitive_fields(scan_data)
        
        # Add metadata
        encrypted_data.update({
            'customer_id': self.customer_id,
            'encrypted_at': datetime.utcnow().isoformat(),
            'encryption_version': '1.0',
            'data_classification': 'PHI'
        })
        
        return encrypted_data