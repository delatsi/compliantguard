# Comprehensive Data Security & Segregation Strategy

## 🛡️ **Executive Summary**

This document outlines industry-leading data protection practices for your HIPAA compliance SaaS, ensuring complete customer data isolation, encryption, and audit trails while maintaining operational efficiency.

---

## 🏗️ **Multi-Layered Data Segregation Architecture**

### **Level 1: Account-Level Isolation**
```
AWS Organization: DELATSI LLC
├── Production Account (Customer Data)
│   ├── Customer A Data (Encrypted)
│   ├── Customer B Data (Encrypted)
│   └── Customer C Data (Encrypted)
├── Development Account (Synthetic Data Only)
└── Security Account (Audit Logs Only)
```

### **Level 2: Service-Level Isolation**
```
Production Account
├── Customer Service (Lambda + DynamoDB)
├── Audit Service (Separate Lambda + DynamoDB)
├── Admin Service (Completely Isolated)
└── Analytics Service (Aggregated Data Only)
```

### **Level 3: Data-Level Isolation**
```
DynamoDB Tables
├── customer-{customer_id}-scans
├── customer-{customer_id}-reports
├── customer-{customer_id}-usage
└── shared-metadata (No PII/PHI)
```

---

## 🔐 **1. Customer Data Isolation Patterns**

### **Pattern A: Customer-Specific Tables (Recommended)**
```python
# Dynamic table names based on customer ID
class CustomerDataService:
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.table_prefix = f"customer-{customer_id}"
        
        # Each customer gets their own tables
        self.scans_table = f"{self.table_prefix}-scans"
        self.reports_table = f"{self.table_prefix}-reports"
        self.usage_table = f"{self.table_prefix}-usage"
        
    def get_customer_table(self, table_type: str) -> str:
        """Get customer-specific table name"""
        return f"customer-{self.customer_id}-{table_type}"
    
    async def store_scan_data(self, scan_data: dict):
        """Store data in customer-specific table"""
        table = self.dynamodb.Table(self.get_customer_table("scans"))
        
        # Add customer context to every record
        scan_data.update({
            'customer_id': self.customer_id,
            'data_classification': 'PHI',
            'created_at': datetime.utcnow().isoformat(),
            'encrypted': True
        })
        
        # Store with customer-specific encryption key
        encrypted_data = self.encrypt_data(scan_data, self.customer_id)
        await table.put_item(Item=encrypted_data)
```

### **Pattern B: Shared Tables with Row-Level Security**
```python
# Alternative: Shared tables with strict access control
class SecureDataService:
    def __init__(self, customer_id: str, user_role: str):
        self.customer_id = customer_id
        self.user_role = user_role
        
    async def query_customer_data(self, table_name: str, **filters):
        """Query data with mandatory customer filter"""
        
        # ALWAYS enforce customer boundary
        mandatory_filter = {
            'customer_id': self.customer_id
        }
        
        # Merge with user filters
        filters.update(mandatory_filter)
        
        # Add additional security checks
        if not self.has_access_to_customer(self.customer_id):
            raise UnauthorizedAccessError(
                f"User not authorized for customer {self.customer_id}"
            )
        
        # Query with customer-specific encryption context
        table = self.dynamodb.Table(table_name)
        response = await table.query(
            KeyConditionExpression=Key('customer_id').eq(self.customer_id),
            FilterExpression=self.build_filter_expression(filters)
        )
        
        # Decrypt data with customer-specific key
        return self.decrypt_customer_data(response['Items'])
```

---

## 🔒 **2. Advanced Encryption Strategy**

### **Customer-Specific Encryption Keys**
```python
import boto3
from cryptography.fernet import Fernet
import base64

class CustomerEncryptionService:
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.kms = boto3.client('kms')
        self.customer_key_id = f"customer-{customer_id}"
        
    async def get_customer_key(self) -> str:
        """Get or create customer-specific encryption key"""
        try:
            # Try to get existing key
            key_response = self.kms.describe_key(
                KeyId=f"alias/{self.customer_key_id}"
            )
            return key_response['KeyMetadata']['KeyId']
            
        except self.kms.exceptions.NotFoundException:
            # Create new customer-specific key
            key_response = self.kms.create_key(
                Description=f"Customer encryption key for {self.customer_id}",
                KeyUsage='ENCRYPT_DECRYPT',
                Tags=[
                    {'TagKey': 'Customer', 'TagValue': self.customer_id},
                    {'TagKey': 'Purpose', 'TagValue': 'PHI_Encryption'},
                    {'TagKey': 'Project', 'TagValue': 'themisguard'}
                ]
            )
            
            # Create alias for easy reference
            self.kms.create_alias(
                AliasName=f"alias/{self.customer_key_id}",
                TargetKeyId=key_response['KeyMetadata']['KeyId']
            )
            
            return key_response['KeyMetadata']['KeyId']
    
    async def encrypt_data(self, data: dict) -> dict:
        """Encrypt data with customer-specific key"""
        key_id = await self.get_customer_key()
        
        # Generate data encryption key
        dek_response = self.kms.generate_data_key(
            KeyId=key_id,
            KeySpec='AES_256',
            EncryptionContext={
                'customer_id': self.customer_id,
                'purpose': 'PHI_protection'
            }
        )
        
        # Encrypt data with DEK
        fernet = Fernet(base64.urlsafe_b64encode(dek_response['Plaintext'][:32]))
        encrypted_data = fernet.encrypt(json.dumps(data).encode())
        
        return {
            'encrypted_data': base64.b64encode(encrypted_data).decode(),
            'encrypted_key': base64.b64encode(dek_response['CiphertextBlob']).decode(),
            'customer_id': self.customer_id,
            'encryption_context': {
                'customer_id': self.customer_id,
                'purpose': 'PHI_protection'
            }
        }
    
    async def decrypt_data(self, encrypted_record: dict) -> dict:
        """Decrypt data with customer-specific key"""
        # Decrypt the data encryption key
        dek_response = self.kms.decrypt(
            CiphertextBlob=base64.b64decode(encrypted_record['encrypted_key']),
            EncryptionContext=encrypted_record['encryption_context']
        )
        
        # Decrypt the actual data
        fernet = Fernet(base64.urlsafe_b64encode(dek_response['Plaintext'][:32]))
        decrypted_data = fernet.decrypt(
            base64.b64decode(encrypted_record['encrypted_data'])
        )
        
        return json.loads(decrypted_data.decode())
```

### **Field-Level Encryption for Sensitive Data**
```python
class FieldLevelEncryption:
    """Encrypt specific fields within records"""
    
    SENSITIVE_FIELDS = {
        'email', 'phone', 'ssn', 'patient_id', 'medical_record_number',
        'ip_address', 'user_agent', 'location_data'
    }
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.encryption_service = CustomerEncryptionService(customer_id)
    
    async def encrypt_sensitive_fields(self, record: dict) -> dict:
        """Encrypt only sensitive fields in a record"""
        encrypted_record = record.copy()
        
        for field, value in record.items():
            if field in self.SENSITIVE_FIELDS and value:
                # Encrypt this field
                encrypted_field = await self.encryption_service.encrypt_data({
                    'field': field,
                    'value': value,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Replace with encrypted version
                encrypted_record[f"{field}_encrypted"] = encrypted_field
                encrypted_record[f"{field}_hash"] = hashlib.sha256(
                    str(value).encode()
                ).hexdigest()[:8]  # For searching
                
                # Remove plaintext
                del encrypted_record[field]
        
        return encrypted_record
```

---

## 🎯 **3. Access Control & Authorization**

### **Role-Based Access Control (RBAC)**
```python
from enum import Enum
from typing import Set, Dict

class Permission(Enum):
    READ_OWN_DATA = "read_own_data"
    WRITE_OWN_DATA = "write_own_data"
    READ_CUSTOMER_DATA = "read_customer_data"
    WRITE_CUSTOMER_DATA = "write_customer_data"
    DELETE_CUSTOMER_DATA = "delete_customer_data"
    ACCESS_AUDIT_LOGS = "access_audit_logs"
    ADMIN_FUNCTIONS = "admin_functions"

class Role(Enum):
    CUSTOMER_USER = "customer_user"
    CUSTOMER_ADMIN = "customer_admin"
    SYSTEM_ADMIN = "system_admin"
    AUDITOR = "auditor"
    READONLY_ANALYST = "readonly_analyst"

class AccessControlService:
    
    ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
        Role.CUSTOMER_USER: {
            Permission.READ_OWN_DATA,
            Permission.WRITE_OWN_DATA
        },
        Role.CUSTOMER_ADMIN: {
            Permission.READ_OWN_DATA,
            Permission.WRITE_OWN_DATA,
            Permission.READ_CUSTOMER_DATA,
            Permission.WRITE_CUSTOMER_DATA,
            Permission.DELETE_CUSTOMER_DATA
        },
        Role.SYSTEM_ADMIN: {
            Permission.ADMIN_FUNCTIONS,
            Permission.ACCESS_AUDIT_LOGS
        },
        Role.AUDITOR: {
            Permission.ACCESS_AUDIT_LOGS
        },
        Role.READONLY_ANALYST: {
            # No customer data access - only aggregated metrics
        }
    }
    
    def __init__(self, user_id: str, customer_id: str, role: Role):
        self.user_id = user_id
        self.customer_id = customer_id
        self.role = role
        self.permissions = self.ROLE_PERMISSIONS.get(role, set())
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions
    
    def can_access_customer_data(self, target_customer_id: str) -> bool:
        """Check if user can access specific customer's data"""
        
        # System admins cannot access customer data
        if self.role == Role.SYSTEM_ADMIN:
            return False
        
        # Users can only access their own customer's data
        if self.customer_id != target_customer_id:
            return False
        
        # Check specific permission
        return self.has_permission(Permission.READ_CUSTOMER_DATA)
    
    async def audit_access_attempt(self, resource: str, action: str, success: bool):
        """Log all access attempts for audit"""
        audit_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': self.user_id,
            'customer_id': self.customer_id,
            'role': self.role.value,
            'resource': resource,
            'action': action,
            'success': success,
            'ip_address': self.get_request_ip(),
            'user_agent': self.get_user_agent()
        }
        
        # Store in audit-specific table (separate from customer data)
        await self.store_audit_log(audit_log)

# Decorator for automatic access control
def require_permission(permission: Permission, customer_field: str = 'customer_id'):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract access control context
            access_control = kwargs.get('access_control')
            if not access_control:
                raise AuthenticationError("Access control context required")
            
            # Check permission
            if not access_control.has_permission(permission):
                await access_control.audit_access_attempt(
                    resource=func.__name__,
                    action=permission.value,
                    success=False
                )
                raise AuthorizationError(f"Permission {permission.value} required")
            
            # Check customer boundary
            target_customer = kwargs.get(customer_field)
            if target_customer and not access_control.can_access_customer_data(target_customer):
                await access_control.audit_access_attempt(
                    resource=func.__name__,
                    action=f"access_customer_{target_customer}",
                    success=False
                )
                raise AuthorizationError("Cannot access data for this customer")
            
            # Log successful access
            await access_control.audit_access_attempt(
                resource=func.__name__,
                action=permission.value,
                success=True
            )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage example
@require_permission(Permission.READ_CUSTOMER_DATA, 'customer_id')
async def get_customer_scans(customer_id: str, access_control: AccessControlService):
    """Get scans for a specific customer"""
    data_service = CustomerDataService(customer_id)
    return await data_service.get_scans()
```

---

## 📊 **4. Comprehensive Audit Logging**

### **Audit Service Implementation**
```python
class AuditService:
    """Comprehensive audit logging for all data access"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.audit_table = self.dynamodb.Table('audit-logs')
        self.kinesis = boto3.client('kinesis')
        
    async def log_data_access(self, event: Dict[str, Any]):
        """Log all data access events"""
        
        audit_record = {
            'audit_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event['type'],
            'user_id': event['user_id'],
            'customer_id': event.get('customer_id'),
            'resource_type': event['resource_type'],
            'resource_id': event.get('resource_id'),
            'action': event['action'],
            'result': event['result'],
            'ip_address': event.get('ip_address'),
            'user_agent': event.get('user_agent'),
            'session_id': event.get('session_id'),
            'data_classification': event.get('data_classification', 'unknown'),
            'compliance_tags': event.get('compliance_tags', []),
            'ttl': int((datetime.utcnow() + timedelta(days=2555)).timestamp())  # 7 years retention
        }
        
        # Store in DynamoDB
        await self.audit_table.put_item(Item=audit_record)
        
        # Stream to Kinesis for real-time monitoring
        await self.kinesis.put_record(
            StreamName='audit-stream',
            Data=json.dumps(audit_record),
            PartitionKey=event['customer_id'] or 'system'
        )
        
        # Check for suspicious patterns
        await self.check_anomalous_access(audit_record)
    
    async def check_anomalous_access(self, audit_record: Dict[str, Any]):
        """Detect anomalous access patterns"""
        
        # Check for unusual access patterns
        recent_access = await self.get_recent_access(
            user_id=audit_record['user_id'],
            hours=1
        )
        
        # Multiple failed attempts
        failed_attempts = [r for r in recent_access if r['result'] == 'FAILED']
        if len(failed_attempts) > 5:
            await self.trigger_security_alert(
                type='BRUTE_FORCE_ATTEMPT',
                user_id=audit_record['user_id'],
                details=f"{len(failed_attempts)} failed attempts in 1 hour"
            )
        
        # Access from unusual IP
        user_ips = await self.get_user_ip_history(audit_record['user_id'])
        if audit_record['ip_address'] not in user_ips:
            await self.trigger_security_alert(
                type='UNUSUAL_IP_ACCESS',
                user_id=audit_record['user_id'],
                details=f"Access from new IP: {audit_record['ip_address']}"
            )
        
        # Bulk data access
        if audit_record['action'] in ['BULK_EXPORT', 'BULK_DELETE']:
            await self.trigger_security_alert(
                type='BULK_DATA_OPERATION',
                user_id=audit_record['user_id'],
                details=f"Bulk operation: {audit_record['action']}"
            )

# Audit decorator for automatic logging
def audit_data_access(resource_type: str, action: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            result = 'SUCCESS'
            error = None
            
            try:
                response = await func(*args, **kwargs)
                return response
            except Exception as e:
                result = 'FAILED'
                error = str(e)
                raise
            finally:
                # Log the access attempt
                audit_event = {
                    'type': 'DATA_ACCESS',
                    'user_id': kwargs.get('user_id'),
                    'customer_id': kwargs.get('customer_id'),
                    'resource_type': resource_type,
                    'resource_id': kwargs.get('resource_id'),
                    'action': action,
                    'result': result,
                    'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                    'error': error,
                    'ip_address': kwargs.get('ip_address'),
                    'user_agent': kwargs.get('user_agent'),
                    'session_id': kwargs.get('session_id')
                }
                
                audit_service = AuditService()
                await audit_service.log_data_access(audit_event)
        
        return wrapper
    return decorator
```

---

## 🔐 **5. Data Loss Prevention (DLP)**

### **Sensitive Data Detection**
```python
import re
from typing import List, Dict, Any

class DataLossPreventionService:
    """Detect and protect sensitive data"""
    
    # Patterns for detecting sensitive information
    PATTERNS = {
        'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
        'credit_card': re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b\d{3}-?\d{3}-?\d{4}\b'),
        'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
        'medical_record': re.compile(r'\bMRN[:\s]*\d+\b', re.IGNORECASE),
        'patient_id': re.compile(r'\bPID[:\s]*\d+\b', re.IGNORECASE)
    }
    
    def scan_for_sensitive_data(self, text: str) -> Dict[str, List[str]]:
        """Scan text for sensitive data patterns"""
        findings = {}
        
        for pattern_name, pattern in self.PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                findings[pattern_name] = matches
        
        return findings
    
    def redact_sensitive_data(self, text: str) -> tuple[str, Dict[str, int]]:
        """Redact sensitive data from text"""
        redacted_text = text
        redaction_count = {}
        
        for pattern_name, pattern in self.PATTERNS.items():
            matches = pattern.findall(redacted_text)
            if matches:
                redaction_count[pattern_name] = len(matches)
                redacted_text = pattern.sub('[REDACTED]', redacted_text)
        
        return redacted_text, redaction_count
    
    async def validate_data_before_storage(self, data: Dict[str, Any], customer_id: str):
        """Validate data before storing"""
        
        # Convert data to string for scanning
        data_str = json.dumps(data)
        
        # Scan for sensitive patterns
        findings = self.scan_for_sensitive_data(data_str)
        
        if findings:
            # Log the detection
            await self.log_sensitive_data_detection(
                customer_id=customer_id,
                findings=findings,
                data_hash=hashlib.sha256(data_str.encode()).hexdigest()
            )
            
            # Apply appropriate handling based on findings
            for pattern_type, matches in findings.items():
                if pattern_type in ['ssn', 'credit_card']:
                    # High-risk data - requires special handling
                    await self.trigger_high_risk_data_alert(
                        customer_id=customer_id,
                        pattern_type=pattern_type,
                        count=len(matches)
                    )
        
        return findings
```

---

## 🏥 **6. HIPAA-Specific Protections**

### **HIPAA Compliance Service**
```python
class HIPAAComplianceService:
    """HIPAA-specific data protection measures"""
    
    PHI_FIELDS = {
        'names', 'addresses', 'dates', 'phone_numbers', 'fax_numbers',
        'email_addresses', 'ssn', 'medical_record_numbers', 'health_plan_numbers',
        'account_numbers', 'certificate_numbers', 'vehicle_identifiers',
        'device_identifiers', 'web_urls', 'ip_addresses', 'biometric_identifiers',
        'full_face_photos', 'other_identifying_numbers'
    }
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.encryption_service = CustomerEncryptionService(customer_id)
        self.audit_service = AuditService()
    
    async def handle_phi_data(self, data: Dict[str, Any], context: Dict[str, Any]):
        """Handle PHI data according to HIPAA requirements"""
        
        # 1. Encrypt all PHI data
        encrypted_data = await self.encryption_service.encrypt_data(data)
        
        # 2. Add HIPAA-specific metadata
        hipaa_metadata = {
            'data_classification': 'PHI',
            'hipaa_compliant': True,
            'encryption_algorithm': 'AES-256',
            'access_logged': True,
            'minimum_necessary': context.get('minimum_necessary', False),
            'authorized_purpose': context.get('purpose'),
            'retention_date': self.calculate_retention_date(),
            'customer_id': self.customer_id
        }
        
        encrypted_data.update(hipaa_metadata)
        
        # 3. Log PHI access
        await self.audit_service.log_data_access({
            'type': 'PHI_ACCESS',
            'user_id': context.get('user_id'),
            'customer_id': self.customer_id,
            'resource_type': 'PHI_DATA',
            'action': context.get('action', 'STORE'),
            'result': 'SUCCESS',
            'data_classification': 'PHI',
            'compliance_tags': ['HIPAA', 'PHI'],
            'purpose': context.get('purpose'),
            'ip_address': context.get('ip_address'),
            'user_agent': context.get('user_agent')
        })
        
        return encrypted_data
    
    def calculate_retention_date(self) -> str:
        """Calculate data retention date per HIPAA requirements"""
        # HIPAA requires minimum 6 years retention
        retention_date = datetime.utcnow() + timedelta(days=2190)  # 6 years
        return retention_date.isoformat()
    
    async def minimum_necessary_check(self, requested_fields: List[str], purpose: str) -> List[str]:
        """Implement HIPAA minimum necessary standard"""
        
        # Define what fields are necessary for different purposes
        purpose_field_mapping = {
            'compliance_scan': ['scan_results', 'violation_data', 'timestamps'],
            'billing': ['usage_data', 'scan_counts', 'subscription_info'],
            'support': ['error_logs', 'system_metadata', 'non_phi_identifiers'],
            'audit': ['access_logs', 'system_events', 'compliance_data']
        }
        
        necessary_fields = purpose_field_mapping.get(purpose, [])
        
        # Filter requested fields to only necessary ones
        filtered_fields = [field for field in requested_fields if field in necessary_fields]
        
        # Log the minimum necessary decision
        await self.audit_service.log_data_access({
            'type': 'MINIMUM_NECESSARY_CHECK',
            'customer_id': self.customer_id,
            'purpose': purpose,
            'requested_fields': requested_fields,
            'approved_fields': filtered_fields,
            'result': 'FILTERED'
        })
        
        return filtered_fields
```

---

## 📋 **7. Implementation Checklist**

### **Infrastructure Security**
- [ ] Customer-specific KMS keys for encryption
- [ ] Separate DynamoDB tables per customer
- [ ] VPC with private subnets for production
- [ ] WAF rules for DDoS protection
- [ ] CloudTrail logging enabled
- [ ] GuardDuty threat detection enabled

### **Application Security**
- [ ] Field-level encryption for sensitive data
- [ ] Role-based access control (RBAC)
- [ ] Audit logging for all data access
- [ ] Data loss prevention (DLP) scanning
- [ ] HIPAA compliance validation
- [ ] Minimum necessary access controls

### **Operational Security**
- [ ] Regular security assessments
- [ ] Incident response procedures
- [ ] Data breach notification process
- [ ] Employee security training
- [ ] Vendor security reviews
- [ ] Business associate agreements (BAAs)

### **Monitoring & Alerting**
- [ ] Real-time access monitoring
- [ ] Anomaly detection for unusual access
- [ ] Failed login attempt monitoring
- [ ] Bulk data operation alerts
- [ ] Security event correlation
- [ ] Automated incident response

---

This comprehensive strategy ensures your customers' data is protected with multiple layers of security, meeting and exceeding HIPAA requirements while maintaining operational efficiency.