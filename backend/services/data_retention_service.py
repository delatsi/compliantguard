"""
Data Retention and Deletion Service - HIPAA compliant data lifecycle management
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict

import boto3

from ..core.config import settings
from ..models.audit import AccessResult, AuditEvent, EventType
from .audit_service import AuditService
from .encryption_service import CustomerEncryptionService


class RetentionPolicy(Enum):
    HIPAA_MINIMUM = "hipaa_minimum"  # 6 years
    EXTENDED = "extended"  # 10 years
    INDEFINITE = "indefinite"  # Until customer deletes
    SHORT_TERM = "short_term"  # 1 year


class DataCategory(Enum):
    PHI = "phi"  # Protected Health Information
    AUDIT_LOGS = "audit_logs"  # Audit and compliance logs
    SYSTEM_LOGS = "system_logs"  # System operation logs
    BILLING_DATA = "billing_data"  # Billing and payment data
    USER_DATA = "user_data"  # User account data
    ANALYTICS = "analytics"  # Usage analytics (anonymized)


class DeletionMethod(Enum):
    SOFT_DELETE = "soft_delete"  # Mark as deleted, keep encrypted
    HARD_DELETE = "hard_delete"  # Permanently remove data
    CRYPTOGRAPHIC_ERASURE = "crypto_erasure"  # Delete encryption keys


class DataRetentionService:
    """
    Comprehensive data retention and deletion service for HIPAA compliance
    """

    # HIPAA-compliant retention policies
    RETENTION_POLICIES = {
        DataCategory.PHI: {
            "policy": RetentionPolicy.HIPAA_MINIMUM,
            "retention_days": 2190,  # 6 years
            "deletion_method": DeletionMethod.CRYPTOGRAPHIC_ERASURE,
            "requires_approval": True,
            "audit_level": "comprehensive",
        },
        DataCategory.AUDIT_LOGS: {
            "policy": RetentionPolicy.EXTENDED,
            "retention_days": 3650,  # 10 years
            "deletion_method": DeletionMethod.HARD_DELETE,
            "requires_approval": True,
            "audit_level": "comprehensive",
        },
        DataCategory.SYSTEM_LOGS: {
            "policy": RetentionPolicy.SHORT_TERM,
            "retention_days": 365,  # 1 year
            "deletion_method": DeletionMethod.HARD_DELETE,
            "requires_approval": False,
            "audit_level": "standard",
        },
        DataCategory.BILLING_DATA: {
            "policy": RetentionPolicy.EXTENDED,
            "retention_days": 3650,  # 10 years (tax requirements)
            "deletion_method": DeletionMethod.SOFT_DELETE,
            "requires_approval": True,
            "audit_level": "comprehensive",
        },
        DataCategory.USER_DATA: {
            "policy": RetentionPolicy.INDEFINITE,
            "retention_days": None,  # Until customer requests deletion
            "deletion_method": DeletionMethod.HARD_DELETE,
            "requires_approval": False,
            "audit_level": "standard",
        },
        DataCategory.ANALYTICS: {
            "policy": RetentionPolicy.SHORT_TERM,
            "retention_days": 730,  # 2 years
            "deletion_method": DeletionMethod.HARD_DELETE,
            "requires_approval": False,
            "audit_level": "minimal",
        },
    }

    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        self.audit_service = AuditService()

        # Retention tracking table
        self.retention_table_name = "data-retention-tracker"
        self.deletion_queue_table_name = "deletion-queue"

    async def schedule_data_for_retention(
        self,
        customer_id: str,
        data_category: DataCategory,
        resource_type: str,
        resource_id: str,
        created_at: datetime,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Schedule data for retention tracking

        Args:
            customer_id: Customer ID
            data_category: Category of data (PHI, audit_logs, etc.)
            resource_type: Type of resource (scan_data, report, etc.)
            resource_id: Unique resource identifier
            created_at: When the data was created
            metadata: Additional metadata about the data

        Returns:
            Retention tracking ID
        """

        try:
            policy = self.RETENTION_POLICIES[data_category]

            # Calculate retention expiry
            if policy["retention_days"]:
                expiry_date = created_at + timedelta(days=policy["retention_days"])
            else:
                expiry_date = None  # Indefinite retention

            # Create retention record
            retention_record = {
                "retention_id": f"{customer_id}#{resource_type}#{resource_id}",
                "customer_id": customer_id,
                "data_category": data_category.value,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "created_at": created_at.isoformat(),
                "expiry_date": expiry_date.isoformat() if expiry_date else None,
                "retention_policy": policy["policy"].value,
                "deletion_method": policy["deletion_method"].value,
                "requires_approval": policy["requires_approval"],
                "audit_level": policy["audit_level"],
                "status": "active",
                "metadata": metadata or {},
                "scheduled_at": datetime.utcnow().isoformat(),
                "last_reviewed": datetime.utcnow().isoformat(),
            }

            # Store retention record
            retention_table = self.dynamodb.Table(self.retention_table_name)
            await retention_table.put_item(Item=retention_record)

            # Audit the retention scheduling
            await self.audit_service.log_access(
                AuditEvent(
                    user_id="system",
                    customer_id=customer_id,
                    action="schedule_retention",
                    resource_type=resource_type,
                    resource_id=resource_id,
                    result=AccessResult.SUCCESS,
                    timestamp=datetime.utcnow(),
                    event_type=EventType.SYSTEM_EVENT,
                    additional_context={
                        "data_category": data_category.value,
                        "expiry_date": expiry_date.isoformat() if expiry_date else None,
                        "retention_policy": policy["policy"].value,
                    },
                )
            )

            return retention_record["retention_id"]

        except Exception as e:
            await self.audit_service.log_access(
                AuditEvent(
                    user_id="system",
                    customer_id=customer_id,
                    action="schedule_retention",
                    resource_type=resource_type,
                    resource_id=resource_id,
                    result=AccessResult.ERROR,
                    timestamp=datetime.utcnow(),
                    event_type=EventType.SYSTEM_EVENT,
                    error_message=str(e),
                )
            )
            raise

    async def process_expired_data(self) -> Dict[str, int]:
        """
        Process all expired data according to retention policies

        Returns:
            Summary of processing results
        """

        try:
            current_time = datetime.utcnow()
            processing_summary = {
                "items_reviewed": 0,
                "items_queued_for_deletion": 0,
                "items_deleted": 0,
                "items_requiring_approval": 0,
                "errors": 0,
            }

            # Get all retention records
            retention_table = self.dynamodb.Table(self.retention_table_name)

            # Scan for expired items
            response = retention_table.scan(
                FilterExpression="expiry_date <= :current_time AND #status = :active_status",
                ExpressionAttributeValues={
                    ":current_time": current_time.isoformat(),
                    ":active_status": "active",
                },
                ExpressionAttributeNames={"#status": "status"},
            )

            expired_items = response.get("Items", [])
            processing_summary["items_reviewed"] = len(expired_items)

            for item in expired_items:
                try:
                    if item["requires_approval"]:
                        # Queue for manual approval
                        await self._queue_for_approval(item)
                        processing_summary["items_requiring_approval"] += 1
                    else:
                        # Process automatic deletion
                        success = await self._process_automatic_deletion(item)
                        if success:
                            processing_summary["items_deleted"] += 1
                        else:
                            # Queue for retry
                            await self._queue_for_retry(item)
                            processing_summary["items_queued_for_deletion"] += 1

                except Exception as e:
                    processing_summary["errors"] += 1
                    await self._handle_processing_error(item, str(e))

            # Audit the processing run
            await self.audit_service.log_access(
                AuditEvent(
                    user_id="system",
                    customer_id=None,
                    action="process_expired_data",
                    resource_type="retention_system",
                    result=AccessResult.SUCCESS,
                    timestamp=current_time,
                    event_type=EventType.SYSTEM_EVENT,
                    additional_context=processing_summary,
                )
            )

            return processing_summary

        except Exception as e:
            await self.audit_service.log_access(
                AuditEvent(
                    user_id="system",
                    customer_id=None,
                    action="process_expired_data",
                    resource_type="retention_system",
                    result=AccessResult.ERROR,
                    timestamp=datetime.utcnow(),
                    event_type=EventType.SYSTEM_EVENT,
                    error_message=str(e),
                )
            )
            raise

    async def delete_customer_data_by_request(
        self,
        customer_id: str,
        requested_by: str,
        deletion_reason: str = "customer_request",
    ) -> Dict[str, Any]:
        """
        Delete all customer data by explicit request (GDPR right to be forgotten)

        Args:
            customer_id: Customer ID
            requested_by: User who requested the deletion
            deletion_reason: Reason for deletion

        Returns:
            Deletion summary
        """

        try:
            deletion_summary = {
                "deletion_id": f"customer-deletion-{customer_id}-{int(datetime.utcnow().timestamp())}",
                "customer_id": customer_id,
                "requested_by": requested_by,
                "deletion_reason": deletion_reason,
                "started_at": datetime.utcnow().isoformat(),
                "status": "in_progress",
                "items_deleted": {},
                "errors": [],
            }

            # Get all retention records for this customer
            retention_table = self.dynamodb.Table(self.retention_table_name)
            response = retention_table.query(
                IndexName="customer-id-index",
                KeyConditionExpression="customer_id = :customer_id",
                ExpressionAttributeValues={":customer_id": customer_id},
            )

            customer_items = response.get("Items", [])

            # Process each item
            for item in customer_items:
                try:
                    data_category = DataCategory(item["data_category"])

                    # Skip audit logs (required for compliance)
                    if data_category == DataCategory.AUDIT_LOGS:
                        continue

                    # Determine deletion method
                    deletion_method = DeletionMethod(item["deletion_method"])

                    success = await self._execute_deletion(
                        item,
                        deletion_method,
                        reason=f"Customer request: {deletion_reason}",
                    )

                    if success:
                        category_key = data_category.value
                        deletion_summary["items_deleted"][category_key] = (
                            deletion_summary["items_deleted"].get(category_key, 0) + 1
                        )
                    else:
                        deletion_summary["errors"].append(
                            f"Failed to delete {item['resource_type']}:{item['resource_id']}"
                        )

                except Exception as e:
                    deletion_summary["errors"].append(
                        f"Error processing {item.get('resource_id', 'unknown')}: {str(e)}"
                    )

            # Delete customer-specific encryption keys
            try:
                encryption_service = CustomerEncryptionService(customer_id)
                await encryption_service.delete_customer_key()
                deletion_summary["items_deleted"]["encryption_keys"] = 1
            except Exception as e:
                deletion_summary["errors"].append(
                    f"Failed to delete encryption keys: {str(e)}"
                )

            # Update status
            deletion_summary["completed_at"] = datetime.utcnow().isoformat()
            deletion_summary["status"] = (
                "completed"
                if not deletion_summary["errors"]
                else "completed_with_errors"
            )

            # Audit the deletion
            await self.audit_service.log_access(
                AuditEvent(
                    user_id=requested_by,
                    customer_id=customer_id,
                    action="delete_customer_data",
                    resource_type="customer_data",
                    result=(
                        AccessResult.SUCCESS
                        if not deletion_summary["errors"]
                        else AccessResult.PARTIAL
                    ),
                    timestamp=datetime.utcnow(),
                    event_type=EventType.DATA_DELETION,
                    additional_context=deletion_summary,
                )
            )

            return deletion_summary

        except Exception as e:
            await self.audit_service.log_access(
                AuditEvent(
                    user_id=requested_by,
                    customer_id=customer_id,
                    action="delete_customer_data",
                    resource_type="customer_data",
                    result=AccessResult.ERROR,
                    timestamp=datetime.utcnow(),
                    event_type=EventType.DATA_DELETION,
                    error_message=str(e),
                )
            )
            raise

    async def extend_retention_period(
        self,
        retention_id: str,
        new_expiry_date: datetime,
        extended_by: str,
        reason: str,
    ) -> bool:
        """
        Extend the retention period for specific data

        Args:
            retention_id: Retention tracking ID
            new_expiry_date: New expiry date
            extended_by: User who extended the retention
            reason: Reason for extension

        Returns:
            Success status
        """

        try:
            retention_table = self.dynamodb.Table(self.retention_table_name)

            # Update the retention record
            response = retention_table.update_item(
                Key={"retention_id": retention_id},
                UpdateExpression="SET expiry_date = :new_expiry, last_reviewed = :reviewed, extension_history = list_append(if_not_exists(extension_history, :empty_list), :extension)",
                ExpressionAttributeValues={
                    ":new_expiry": new_expiry_date.isoformat(),
                    ":reviewed": datetime.utcnow().isoformat(),
                    ":empty_list": [],
                    ":extension": [
                        {
                            "extended_by": extended_by,
                            "extended_at": datetime.utcnow().isoformat(),
                            "reason": reason,
                            "new_expiry_date": new_expiry_date.isoformat(),
                        }
                    ],
                },
                ReturnValues="ALL_NEW",
            )

            # Audit the extension
            item = response.get("Attributes", {})
            await self.audit_service.log_access(
                AuditEvent(
                    user_id=extended_by,
                    customer_id=item.get("customer_id"),
                    action="extend_retention",
                    resource_type=item.get("resource_type"),
                    resource_id=item.get("resource_id"),
                    result=AccessResult.SUCCESS,
                    timestamp=datetime.utcnow(),
                    event_type=EventType.ADMIN_ACTION,
                    additional_context={
                        "retention_id": retention_id,
                        "new_expiry_date": new_expiry_date.isoformat(),
                        "reason": reason,
                    },
                )
            )

            return True

        except Exception as e:
            await self.audit_service.log_access(
                AuditEvent(
                    user_id=extended_by,
                    customer_id=None,
                    action="extend_retention",
                    resource_type="retention_record",
                    resource_id=retention_id,
                    result=AccessResult.ERROR,
                    timestamp=datetime.utcnow(),
                    event_type=EventType.ADMIN_ACTION,
                    error_message=str(e),
                )
            )
            return False

    async def get_retention_status(self, customer_id: str) -> Dict[str, Any]:
        """
        Get retention status summary for a customer

        Args:
            customer_id: Customer ID

        Returns:
            Retention status summary
        """

        try:
            retention_table = self.dynamodb.Table(self.retention_table_name)
            response = retention_table.query(
                IndexName="customer-id-index",
                KeyConditionExpression="customer_id = :customer_id",
                ExpressionAttributeValues={":customer_id": customer_id},
            )

            items = response.get("Items", [])
            current_time = datetime.utcnow()

            summary = {
                "customer_id": customer_id,
                "total_items": len(items),
                "by_category": {},
                "expiring_soon": [],  # Within 30 days
                "expired": [],
                "indefinite_retention": [],
                "generated_at": current_time.isoformat(),
            }

            for item in items:
                category = item["data_category"]

                # Count by category
                if category not in summary["by_category"]:
                    summary["by_category"][category] = {
                        "count": 0,
                        "active": 0,
                        "expired": 0,
                    }

                summary["by_category"][category]["count"] += 1

                # Check status
                if item.get("expiry_date"):
                    expiry_date = datetime.fromisoformat(item["expiry_date"])

                    if expiry_date <= current_time:
                        summary["expired"].append(
                            {
                                "retention_id": item["retention_id"],
                                "resource_type": item["resource_type"],
                                "expiry_date": item["expiry_date"],
                                "requires_approval": item["requires_approval"],
                            }
                        )
                        summary["by_category"][category]["expired"] += 1
                    elif expiry_date <= current_time + timedelta(days=30):
                        summary["expiring_soon"].append(
                            {
                                "retention_id": item["retention_id"],
                                "resource_type": item["resource_type"],
                                "expiry_date": item["expiry_date"],
                                "days_until_expiry": (expiry_date - current_time).days,
                            }
                        )
                        summary["by_category"][category]["active"] += 1
                    else:
                        summary["by_category"][category]["active"] += 1
                else:
                    summary["indefinite_retention"].append(
                        {
                            "retention_id": item["retention_id"],
                            "resource_type": item["resource_type"],
                            "created_at": item["created_at"],
                        }
                    )
                    summary["by_category"][category]["active"] += 1

            return summary

        except Exception as e:
            print(f"Failed to get retention status: {e}")
            return {}

    # Internal helper methods

    async def _queue_for_approval(self, item: Dict[str, Any]):
        """Queue item for manual approval before deletion"""
        deletion_queue_table = self.dynamodb.Table(self.deletion_queue_table_name)

        queue_item = {
            "queue_id": f"approval-{item['retention_id']}-{int(datetime.utcnow().timestamp())}",
            "retention_id": item["retention_id"],
            "customer_id": item["customer_id"],
            "resource_type": item["resource_type"],
            "resource_id": item["resource_id"],
            "data_category": item["data_category"],
            "expiry_date": item["expiry_date"],
            "queued_at": datetime.utcnow().isoformat(),
            "status": "pending_approval",
            "requires_approval": True,
            "deletion_method": item["deletion_method"],
        }

        await deletion_queue_table.put_item(Item=queue_item)

    async def _process_automatic_deletion(self, item: Dict[str, Any]) -> bool:
        """Process automatic deletion for items that don't require approval"""
        try:
            deletion_method = DeletionMethod(item["deletion_method"])
            return await self._execute_deletion(
                item, deletion_method, reason="automatic_retention_policy"
            )
        except Exception as e:
            print(f"Failed automatic deletion for {item['retention_id']}: {e}")
            return False

    async def _execute_deletion(
        self, item: Dict[str, Any], deletion_method: DeletionMethod, reason: str
    ) -> bool:
        """Execute the actual deletion based on method"""

        try:
            customer_id = item["customer_id"]
            resource_type = item["resource_type"]
            resource_id = item["resource_id"]

            if deletion_method == DeletionMethod.CRYPTOGRAPHIC_ERASURE:
                # Delete encryption keys (makes data unrecoverable)
                encryption_service = CustomerEncryptionService(customer_id)
                await encryption_service.delete_customer_key()

            elif deletion_method == DeletionMethod.HARD_DELETE:
                # Permanently delete data
                await self._hard_delete_resource(
                    customer_id, resource_type, resource_id
                )

            elif deletion_method == DeletionMethod.SOFT_DELETE:
                # Mark as deleted but keep encrypted
                await self._soft_delete_resource(
                    customer_id, resource_type, resource_id
                )

            # Update retention record
            retention_table = self.dynamodb.Table(self.retention_table_name)
            retention_table.update_item(
                Key={"retention_id": item["retention_id"]},
                UpdateExpression="SET #status = :deleted, deleted_at = :deleted_at, deletion_method = :method, deletion_reason = :reason",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":deleted": "deleted",
                    ":deleted_at": datetime.utcnow().isoformat(),
                    ":method": deletion_method.value,
                    ":reason": reason,
                },
            )

            return True

        except Exception as e:
            print(f"Failed to execute deletion: {e}")
            return False

    async def _hard_delete_resource(
        self, customer_id: str, resource_type: str, resource_id: str
    ):
        """Permanently delete a resource"""

        # Delete from DynamoDB
        if resource_type in ["scan_data", "reports", "usage"]:
            table_name = f"customer-{customer_id}-{resource_type}"
            table = self.dynamodb.Table(table_name)
            table.delete_item(Key={f"{resource_type[:-1]}_id": resource_id})

        # Delete from S3
        s3_prefix = f"customers/{customer_id}/{resource_type}/{resource_id}/"
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=settings.S3_BUCKET_NAME, Prefix=s3_prefix)

            for page in pages:
                if "Contents" in page:
                    delete_objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                    if delete_objects:
                        self.s3.delete_objects(
                            Bucket=settings.S3_BUCKET_NAME,
                            Delete={"Objects": delete_objects},
                        )
        except Exception as e:
            print(f"Failed to delete S3 objects: {e}")

    async def _soft_delete_resource(
        self, customer_id: str, resource_type: str, resource_id: str
    ):
        """Mark resource as deleted without removing data"""

        if resource_type in ["scan_data", "reports", "usage"]:
            table_name = f"customer-{customer_id}-{resource_type}"
            table = self.dynamodb.Table(table_name)

            table.update_item(
                Key={f"{resource_type[:-1]}_id": resource_id},
                UpdateExpression="SET deleted = :true, deleted_at = :deleted_at",
                ExpressionAttributeValues={
                    ":true": True,
                    ":deleted_at": datetime.utcnow().isoformat(),
                },
            )

    async def _queue_for_retry(self, item: Dict[str, Any]):
        """Queue failed deletion for retry"""
        deletion_queue_table = self.dynamodb.Table(self.deletion_queue_table_name)

        queue_item = {
            "queue_id": f"retry-{item['retention_id']}-{int(datetime.utcnow().timestamp())}",
            "retention_id": item["retention_id"],
            "customer_id": item["customer_id"],
            "resource_type": item["resource_type"],
            "resource_id": item["resource_id"],
            "queued_at": datetime.utcnow().isoformat(),
            "status": "retry_needed",
            "retry_count": 1,
            "deletion_method": item["deletion_method"],
        }

        await deletion_queue_table.put_item(Item=queue_item)

    async def _handle_processing_error(self, item: Dict[str, Any], error: str):
        """Handle errors during retention processing"""
        await self.audit_service.log_access(
            AuditEvent(
                user_id="system",
                customer_id=item.get("customer_id"),
                action="retention_processing_error",
                resource_type=item.get("resource_type"),
                resource_id=item.get("resource_id"),
                result=AccessResult.ERROR,
                timestamp=datetime.utcnow(),
                event_type=EventType.SYSTEM_EVENT,
                error_message=error,
                additional_context={"retention_id": item.get("retention_id")},
            )
        )
