"""
Customer Data Service - Implements comprehensive data segregation and security
"""

import boto3
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from cryptography.fernet import Fernet
import base64
from enum import Enum

from ..core.config import settings
from ..models.audit import AuditEvent, AccessResult
from .audit_service import AuditService
from .encryption_service import CustomerEncryptionService


class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PHI = "phi"  # Protected Health Information


class Permission(Enum):
    READ_OWN_DATA = "read_own_data"
    WRITE_OWN_DATA = "write_own_data"
    READ_CUSTOMER_DATA = "read_customer_data"
    WRITE_CUSTOMER_DATA = "write_customer_data"
    DELETE_CUSTOMER_DATA = "delete_customer_data"
    EXPORT_CUSTOMER_DATA = "export_customer_data"


class Role(Enum):
    CUSTOMER_USER = "customer_user"
    CUSTOMER_ADMIN = "customer_admin"
    SYSTEM_ADMIN = "system_admin"
    READONLY_ANALYST = "readonly_analyst"


class CustomerDataService:
    """
    Secure customer data service with complete isolation and encryption
    """

    # Role-based permissions mapping
    ROLE_PERMISSIONS = {
        Role.CUSTOMER_USER: {Permission.READ_OWN_DATA, Permission.WRITE_OWN_DATA},
        Role.CUSTOMER_ADMIN: {
            Permission.READ_OWN_DATA,
            Permission.WRITE_OWN_DATA,
            Permission.READ_CUSTOMER_DATA,
            Permission.WRITE_CUSTOMER_DATA,
            Permission.DELETE_CUSTOMER_DATA,
            Permission.EXPORT_CUSTOMER_DATA,
        },
        Role.SYSTEM_ADMIN: {
            # System admins cannot access customer data directly
        },
        Role.READONLY_ANALYST: {
            # Analysts only get aggregated, anonymized data
        },
    }

    def __init__(
        self,
        customer_id: str,
        user_id: str,
        user_role: Role,
        request_context: Dict[str, Any] = None,
    ):
        """Initialize with customer context and security controls"""
        self.customer_id = customer_id
        self.user_id = user_id
        self.user_role = user_role
        self.request_context = request_context or {}

        # Initialize AWS services
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.s3 = boto3.client("s3", region_name=settings.AWS_REGION)

        # Initialize security services
        self.encryption_service = CustomerEncryptionService(customer_id)
        self.audit_service = AuditService()

        # Customer-specific table names
        self.table_prefix = f"customer-{customer_id}"
        self.scans_table_name = f"{self.table_prefix}-scans"
        self.reports_table_name = f"{self.table_prefix}-reports"
        self.usage_table_name = f"{self.table_prefix}-usage"

        # Customer-specific S3 prefix
        self.s3_prefix = f"customers/{customer_id}/"

        # Validate access on initialization
        self._validate_customer_access()

    def _validate_customer_access(self):
        """Validate user has access to this customer's data"""
        if self.user_role == Role.SYSTEM_ADMIN:
            # System admins cannot access customer data
            raise PermissionError("System admins cannot access customer data directly")

        # Additional customer boundary checks would go here
        # (e.g., verify user belongs to this customer organization)

    def _has_permission(self, permission: Permission) -> bool:
        """Check if current user has specific permission"""
        user_permissions = self.ROLE_PERMISSIONS.get(self.user_role, set())
        return permission in user_permissions

    async def _audit_access(
        self,
        action: str,
        resource_type: str,
        resource_id: str = None,
        result: AccessResult = AccessResult.SUCCESS,
        error: str = None,
    ):
        """Audit all data access attempts"""
        await self.audit_service.log_access(
            AuditEvent(
                user_id=self.user_id,
                customer_id=self.customer_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                result=result,
                error_message=error,
                ip_address=self.request_context.get("ip_address"),
                user_agent=self.request_context.get("user_agent"),
                session_id=self.request_context.get("session_id"),
                timestamp=datetime.utcnow(),
            )
        )

    async def _ensure_customer_table_exists(self, table_type: str) -> str:
        """Ensure customer-specific table exists"""
        table_name = f"{self.table_prefix}-{table_type}"

        try:
            # Check if table exists
            table = self.dynamodb.Table(table_name)
            table.load()
            return table_name
        except Exception:
            # Table doesn't exist, create it
            await self._create_customer_table(table_type)
            return table_name

    async def _create_customer_table(self, table_type: str):
        """Create customer-specific DynamoDB table"""
        table_name = f"{self.table_prefix}-{table_type}"

        # Define table schemas based on type
        table_schemas = {
            "scans": {
                "KeySchema": [
                    {"AttributeName": "scan_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "scan_id", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "S"},
                ],
            },
            "reports": {
                "KeySchema": [{"AttributeName": "report_id", "KeyType": "HASH"}],
                "AttributeDefinitions": [
                    {"AttributeName": "report_id", "AttributeType": "S"}
                ],
            },
            "usage": {
                "KeySchema": [
                    {"AttributeName": "usage_id", "KeyType": "HASH"},
                    {"AttributeName": "date", "KeyType": "RANGE"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "usage_id", "AttributeType": "S"},
                    {"AttributeName": "date", "AttributeType": "S"},
                ],
            },
        }

        schema = table_schemas.get(table_type, table_schemas["scans"])

        # Create table with customer-specific encryption
        table = self.dynamodb.create_table(
            TableName=table_name,
            KeySchema=schema["KeySchema"],
            AttributeDefinitions=schema["AttributeDefinitions"],
            BillingMode="PAY_PER_REQUEST",
            SSESpecification={
                "Enabled": True,
                "SSEType": "KMS",
                "KMSMasterKeyId": await self.encryption_service.get_customer_key_id(),
            },
            PointInTimeRecoverySpecification={"PointInTimeRecoveryEnabled": True},
            Tags=[
                {"Key": "Customer", "Value": self.customer_id},
                {"Key": "DataClassification", "Value": DataClassification.PHI.value},
                {"Key": "Project", "Value": "themisguard"},
                {"Key": "Environment", "Value": settings.ENVIRONMENT},
            ],
        )

        # Wait for table to be created
        table.wait_until_exists()

    async def store_scan_data(self, scan_data: Dict[str, Any]) -> str:
        """Store scan data with full encryption and audit logging"""

        # Check permissions
        if not self._has_permission(Permission.WRITE_CUSTOMER_DATA):
            await self._audit_access(
                "store_scan_data", "scan_data", result=AccessResult.DENIED
            )
            raise PermissionError("Insufficient permissions to store scan data")

        try:
            # Generate unique scan ID
            scan_id = str(uuid.uuid4())

            # Add metadata
            enriched_data = {
                **scan_data,
                "scan_id": scan_id,
                "customer_id": self.customer_id,
                "created_by": self.user_id,
                "created_at": datetime.utcnow().isoformat(),
                "data_classification": DataClassification.PHI.value,
                "version": "1.0",
            }

            # Encrypt sensitive data
            encrypted_data = await self.encryption_service.encrypt_customer_data(
                data=enriched_data,
                context={
                    "customer_id": self.customer_id,
                    "purpose": "compliance_scan",
                    "user_id": self.user_id,
                },
            )

            # Ensure table exists
            table_name = await self._ensure_customer_table_exists("scans")
            table = self.dynamodb.Table(table_name)

            # Store in customer-specific table
            await table.put_item(Item=encrypted_data)

            # Audit successful storage
            await self._audit_access(
                "store_scan_data", "scan_data", scan_id, AccessResult.SUCCESS
            )

            return scan_id

        except Exception as e:
            await self._audit_access(
                "store_scan_data", "scan_data", result=AccessResult.ERROR, error=str(e)
            )
            raise

    async def get_scan_data(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt scan data"""

        # Check permissions
        if not self._has_permission(Permission.READ_CUSTOMER_DATA):
            await self._audit_access(
                "get_scan_data", "scan_data", scan_id, AccessResult.DENIED
            )
            raise PermissionError("Insufficient permissions to read scan data")

        try:
            table_name = await self._ensure_customer_table_exists("scans")
            table = self.dynamodb.Table(table_name)

            # Query encrypted data
            response = table.get_item(Key={"scan_id": scan_id})

            if "Item" not in response:
                await self._audit_access(
                    "get_scan_data", "scan_data", scan_id, AccessResult.NOT_FOUND
                )
                return None

            # Decrypt data
            decrypted_data = await self.encryption_service.decrypt_customer_data(
                encrypted_data=response["Item"],
                context={
                    "customer_id": self.customer_id,
                    "purpose": "data_retrieval",
                    "user_id": self.user_id,
                },
            )

            # Audit successful access
            await self._audit_access(
                "get_scan_data", "scan_data", scan_id, AccessResult.SUCCESS
            )

            return decrypted_data

        except Exception as e:
            await self._audit_access(
                "get_scan_data", "scan_data", scan_id, AccessResult.ERROR, error=str(e)
            )
            raise

    async def list_customer_scans(
        self, limit: int = 50, start_key: str = None
    ) -> Dict[str, Any]:
        """List scans for customer with pagination"""

        # Check permissions
        if not self._has_permission(Permission.READ_CUSTOMER_DATA):
            await self._audit_access(
                "list_customer_scans", "scan_data", result=AccessResult.DENIED
            )
            raise PermissionError("Insufficient permissions to list scan data")

        try:
            table_name = await self._ensure_customer_table_exists("scans")
            table = self.dynamodb.Table(table_name)

            # Query parameters
            query_params = {
                "IndexName": "customer-id-index",
                "KeyConditionExpression": "customer_id = :customer_id",
                "ExpressionAttributeValues": {":customer_id": self.customer_id},
                "Limit": limit,
                "ScanIndexForward": False,  # Most recent first
            }

            if start_key:
                query_params["ExclusiveStartKey"] = {"scan_id": start_key}

            response = table.query(**query_params)

            # Decrypt results
            decrypted_items = []
            for item in response.get("Items", []):
                try:
                    decrypted_item = (
                        await self.encryption_service.decrypt_customer_data(
                            encrypted_data=item,
                            context={
                                "customer_id": self.customer_id,
                                "purpose": "data_listing",
                                "user_id": self.user_id,
                            },
                        )
                    )
                    # Remove sensitive fields for listing (apply minimum necessary principle)
                    safe_item = {
                        "scan_id": decrypted_item.get("scan_id"),
                        "created_at": decrypted_item.get("created_at"),
                        "scan_type": decrypted_item.get("scan_type"),
                        "status": decrypted_item.get("status"),
                        "violation_count": decrypted_item.get("violation_count", 0),
                    }
                    decrypted_items.append(safe_item)
                except Exception as e:
                    # Log decryption error but continue
                    print(
                        f"Failed to decrypt item {item.get('scan_id', 'unknown')}: {e}"
                    )
                    continue

            result = {
                "items": decrypted_items,
                "count": len(decrypted_items),
                "last_key": response.get("LastEvaluatedKey", {}).get("scan_id"),
            }

            # Audit successful access
            await self._audit_access(
                "list_customer_scans", "scan_data", result=AccessResult.SUCCESS
            )

            return result

        except Exception as e:
            await self._audit_access(
                "list_customer_scans",
                "scan_data",
                result=AccessResult.ERROR,
                error=str(e),
            )
            raise

    async def delete_scan_data(self, scan_id: str) -> bool:
        """Securely delete scan data"""

        # Check permissions
        if not self._has_permission(Permission.DELETE_CUSTOMER_DATA):
            await self._audit_access(
                "delete_scan_data", "scan_data", scan_id, AccessResult.DENIED
            )
            raise PermissionError("Insufficient permissions to delete scan data")

        try:
            table_name = await self._ensure_customer_table_exists("scans")
            table = self.dynamodb.Table(table_name)

            # First, verify the scan exists and belongs to this customer
            existing_item = await self.get_scan_data(scan_id)
            if not existing_item:
                await self._audit_access(
                    "delete_scan_data", "scan_data", scan_id, AccessResult.NOT_FOUND
                )
                return False

            if existing_item.get("customer_id") != self.customer_id:
                await self._audit_access(
                    "delete_scan_data", "scan_data", scan_id, AccessResult.DENIED
                )
                raise PermissionError(
                    "Cannot delete scan data belonging to different customer"
                )

            # Delete the item
            table.delete_item(Key={"scan_id": scan_id})

            # Also delete associated S3 objects if any
            s3_key = f"{self.s3_prefix}scans/{scan_id}/"
            try:
                objects = self.s3.list_objects_v2(
                    Bucket=settings.S3_BUCKET_NAME, Prefix=s3_key
                )

                if "Contents" in objects:
                    delete_objects = [
                        {"Key": obj["Key"]} for obj in objects["Contents"]
                    ]
                    self.s3.delete_objects(
                        Bucket=settings.S3_BUCKET_NAME,
                        Delete={"Objects": delete_objects},
                    )
            except Exception as s3_error:
                print(f"Failed to delete S3 objects for scan {scan_id}: {s3_error}")

            # Audit successful deletion
            await self._audit_access(
                "delete_scan_data", "scan_data", scan_id, AccessResult.SUCCESS
            )

            return True

        except Exception as e:
            await self._audit_access(
                "delete_scan_data",
                "scan_data",
                scan_id,
                AccessResult.ERROR,
                error=str(e),
            )
            raise

    async def export_customer_data(self, export_format: str = "json") -> str:
        """Export all customer data (for data portability/GDPR compliance)"""

        # Check permissions
        if not self._has_permission(Permission.EXPORT_CUSTOMER_DATA):
            await self._audit_access(
                "export_customer_data", "customer_data", result=AccessResult.DENIED
            )
            raise PermissionError("Insufficient permissions to export customer data")

        try:
            export_id = str(uuid.uuid4())

            # Get all customer data
            all_scans = await self.list_customer_scans(
                limit=1000
            )  # Adjust based on needs

            # Prepare export data
            export_data = {
                "customer_id": self.customer_id,
                "export_id": export_id,
                "exported_at": datetime.utcnow().isoformat(),
                "exported_by": self.user_id,
                "format": export_format,
                "data": {"scans": all_scans["items"]},
            }

            # Encrypt export data
            encrypted_export = await self.encryption_service.encrypt_customer_data(
                data=export_data,
                context={
                    "customer_id": self.customer_id,
                    "purpose": "data_export",
                    "user_id": self.user_id,
                },
            )

            # Store encrypted export in S3 with temporary access
            export_key = (
                f"{self.s3_prefix}exports/{export_id}.{export_format}.encrypted"
            )

            self.s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=export_key,
                Body=json.dumps(encrypted_export),
                ContentType="application/json",
                ServerSideEncryption="aws:kms",
                SSEKMSKeyId=await self.encryption_service.get_customer_key_id(),
                Metadata={
                    "customer_id": self.customer_id,
                    "export_id": export_id,
                    "exported_by": self.user_id,
                },
                # Auto-delete after 7 days
                Expires=datetime.utcnow() + timedelta(days=7),
            )

            # Generate presigned URL for download (valid for 1 hour)
            download_url = self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": export_key},
                ExpiresIn=3600,  # 1 hour
            )

            # Audit the export
            await self._audit_access(
                "export_customer_data", "customer_data", export_id, AccessResult.SUCCESS
            )

            return download_url

        except Exception as e:
            await self._audit_access(
                "export_customer_data",
                "customer_data",
                result=AccessResult.ERROR,
                error=str(e),
            )
            raise

    async def purge_customer_data(self) -> Dict[str, int]:
        """Permanently delete all customer data (GDPR right to be forgotten)"""

        # This should require special authorization (e.g., customer admin + support approval)
        if not self._has_permission(Permission.DELETE_CUSTOMER_DATA):
            await self._audit_access(
                "purge_customer_data", "customer_data", result=AccessResult.DENIED
            )
            raise PermissionError("Insufficient permissions to purge customer data")

        try:
            deletion_counts = {
                "scans_deleted": 0,
                "s3_objects_deleted": 0,
                "tables_deleted": 0,
            }

            # Delete all DynamoDB tables for this customer
            customer_tables = [
                f"{self.table_prefix}-scans",
                f"{self.table_prefix}-reports",
                f"{self.table_prefix}-usage",
            ]

            for table_name in customer_tables:
                try:
                    table = self.dynamodb.Table(table_name)
                    table.delete()
                    deletion_counts["tables_deleted"] += 1
                except Exception as e:
                    print(f"Failed to delete table {table_name}: {e}")

            # Delete all S3 objects for this customer
            try:
                paginator = self.s3.get_paginator("list_objects_v2")
                pages = paginator.paginate(
                    Bucket=settings.S3_BUCKET_NAME, Prefix=self.s3_prefix
                )

                for page in pages:
                    if "Contents" in page:
                        delete_objects = [
                            {"Key": obj["Key"]} for obj in page["Contents"]
                        ]
                        if delete_objects:
                            self.s3.delete_objects(
                                Bucket=settings.S3_BUCKET_NAME,
                                Delete={"Objects": delete_objects},
                            )
                            deletion_counts["s3_objects_deleted"] += len(delete_objects)

            except Exception as e:
                print(f"Failed to delete S3 objects: {e}")

            # Delete customer-specific KMS key
            try:
                await self.encryption_service.delete_customer_key()
            except Exception as e:
                print(f"Failed to delete customer KMS key: {e}")

            # Audit the purge operation
            await self._audit_access(
                "purge_customer_data", "customer_data", result=AccessResult.SUCCESS
            )

            return deletion_counts

        except Exception as e:
            await self._audit_access(
                "purge_customer_data",
                "customer_data",
                result=AccessResult.ERROR,
                error=str(e),
            )
            raise


# Decorator for automatic access control and auditing
def secure_customer_access(permission: Permission):
    """Decorator to enforce access control and auditing"""

    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Check if this is a CustomerDataService method
            if not isinstance(self, CustomerDataService):
                raise TypeError(
                    "secure_customer_access can only be used on CustomerDataService methods"
                )

            # Check permissions
            if not self._has_permission(permission):
                await self._audit_access(
                    func.__name__, "customer_data", result=AccessResult.DENIED
                )
                raise PermissionError(
                    f"Permission {permission.value} required for {func.__name__}"
                )

            # Execute the function with audit logging
            try:
                result = await func(self, *args, **kwargs)
                await self._audit_access(
                    func.__name__, "customer_data", result=AccessResult.SUCCESS
                )
                return result
            except Exception as e:
                await self._audit_access(
                    func.__name__,
                    "customer_data",
                    result=AccessResult.ERROR,
                    error=str(e),
                )
                raise

        return wrapper

    return decorator
