"""
Comprehensive Audit Service - Complete audit logging and monitoring system
"""

import boto3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
import hashlib
import asyncio

from ..core.config import settings
from ..models.audit import (
    AuditEvent, SecurityEvent, ComplianceEvent, DataAccessPattern,
    AccessResult, EventType, SecurityEventType, Severity
)


class AuditService:
    """
    Comprehensive audit logging service with real-time monitoring and anomaly detection
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        self.kinesis = boto3.client('kinesis', region_name=settings.AWS_REGION)
        self.sns = boto3.client('sns', region_name=settings.AWS_REGION)
        
        # Audit table names
        self.audit_table_name = 'audit-logs'
        self.security_events_table_name = 'security-events'
        self.compliance_events_table_name = 'compliance-events'
        self.patterns_table_name = 'access-patterns'
        
        # Initialize tables
        self.audit_table = self.dynamodb.Table(self.audit_table_name)
        
        # Real-time monitoring configuration
        self.kinesis_stream_name = 'audit-stream'
        self.security_alerts_topic = settings.SNS_SECURITY_ALERTS_TOPIC
        
        # Anomaly detection thresholds
        self.anomaly_thresholds = {
            'failed_logins_per_hour': 5,
            'bulk_operations_per_day': 3,
            'unusual_ip_threshold': 0.95,  # 95% confidence
            'rapid_access_threshold': 100,  # requests per minute
            'off_hours_access_weight': 2.0,  # multiplier for suspicious activity
            'data_volume_threshold': 1000   # MB
        }
    
    async def log_access(self, event: AuditEvent) -> str:
        """
        Log an access event with comprehensive audit trail
        
        Args:
            event: The audit event to log
            
        Returns:
            The audit record ID
        """
        
        try:
            # Convert to storage format
            audit_record = event.to_dict()
            audit_id = audit_record['audit_id']
            
            # Enrich with additional metadata
            audit_record.update({
                'hash': self._calculate_event_hash(audit_record),
                'sequence_number': await self._get_next_sequence_number(),
                'source_service': 'themisguard-api',
                'api_version': '1.0',
                'environment': settings.ENVIRONMENT
            })
            
            # Store in DynamoDB
            await self._store_audit_record(audit_record)
            
            # Stream to Kinesis for real-time processing
            await self._stream_to_kinesis(audit_record)
            
            # Check for anomalous patterns
            await self._check_access_patterns(event)
            
            # Handle specific event types
            if event.result == AccessResult.DENIED:
                await self._handle_access_denied(event)
            elif event.event_type == EventType.PHI_ACCESS:
                await self._handle_phi_access(event)
            elif event.event_type == EventType.BULK_OPERATION:
                await self._handle_bulk_operation(event)
            
            return audit_id
            
        except Exception as e:
            # Critical: audit failures must be logged elsewhere
            await self._handle_audit_failure(event, str(e))
            raise
    
    async def log_security_event(self, event: SecurityEvent) -> str:
        """Log a security event with immediate alerting"""
        
        try:
            security_record = event.to_dict()
            security_id = security_record['security_event_id']
            
            # Store security event
            security_table = self.dynamodb.Table(self.security_events_table_name)
            await security_table.put_item(Item=security_record)
            
            # Trigger immediate alerts for high/critical severity
            if event.severity in [Severity.HIGH, Severity.CRITICAL]:
                await self._trigger_security_alert(event)
            
            # Update threat intelligence
            await self._update_threat_indicators(event)
            
            return security_id
            
        except Exception as e:
            await self._handle_audit_failure(event, str(e))
            raise
    
    async def log_compliance_event(self, event: ComplianceEvent) -> str:
        """Log compliance-specific events (HIPAA, SOC2, etc.)"""
        
        try:
            compliance_record = event.to_dict()
            compliance_id = compliance_record['compliance_event_id']
            
            # Store compliance event
            compliance_table = self.dynamodb.Table(self.compliance_events_table_name)
            await compliance_table.put_item(Item=compliance_record)
            
            # Check for compliance violations
            if event.phi_accessed and not event.minimum_necessary:
                await self._flag_compliance_violation(event, "PHI accessed without minimum necessary check")
            
            if event.approval_required and not event.approved_by:
                await self._flag_compliance_violation(event, "Required approval not obtained")
            
            return compliance_id
            
        except Exception as e:
            await self._handle_audit_failure(event, str(e))
            raise
    
    async def get_audit_trail(
        self, 
        customer_id: str = None,
        user_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        event_type: EventType = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve audit trail with filtering"""
        
        try:
            # Build query parameters
            query_params = {
                'Limit': limit,
                'ScanIndexForward': False  # Most recent first
            }
            
            # Add filters
            filter_expressions = []
            expression_values = {}
            
            if customer_id:
                filter_expressions.append('customer_id = :customer_id')
                expression_values[':customer_id'] = customer_id
            
            if user_id:
                filter_expressions.append('user_id = :user_id')
                expression_values[':user_id'] = user_id
            
            if start_time:
                filter_expressions.append('#ts >= :start_time')
                expression_values[':start_time'] = start_time.isoformat()
                query_params['ExpressionAttributeNames'] = {'#ts': 'timestamp'}
            
            if end_time:
                filter_expressions.append('#ts <= :end_time')
                expression_values[':end_time'] = end_time.isoformat()
                query_params['ExpressionAttributeNames'] = {'#ts': 'timestamp'}
            
            if event_type:
                filter_expressions.append('event_type = :event_type')
                expression_values[':event_type'] = event_type.value
            
            if filter_expressions:
                query_params['FilterExpression'] = ' AND '.join(filter_expressions)
                query_params['ExpressionAttributeValues'] = expression_values
            
            # Execute query
            response = self.audit_table.scan(**query_params)
            
            # Return audit records
            return response.get('Items', [])
            
        except Exception as e:
            print(f"Failed to retrieve audit trail: {e}")
            return []
    
    async def detect_anomalous_patterns(self, user_id: str, hours: int = 24) -> List[DataAccessPattern]:
        """Detect anomalous access patterns for a user"""
        
        try:
            # Get recent access history
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            recent_events = await self.get_audit_trail(
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                limit=1000
            )
            
            patterns = []
            
            # Analyze failed login attempts
            failed_logins = [e for e in recent_events if 
                           e.get('action') == 'login' and e.get('result') == AccessResult.DENIED.value]
            
            if len(failed_logins) > self.anomaly_thresholds['failed_logins_per_hour']:
                pattern = DataAccessPattern(
                    user_id=user_id,
                    customer_id=failed_logins[0].get('customer_id'),
                    pattern_type='excessive_failed_logins',
                    frequency=len(failed_logins),
                    time_window=f'{hours}h',
                    baseline_frequency=2.0,
                    deviation_score=(len(failed_logins) - 2.0) / 2.0,
                    timestamp=datetime.utcnow(),
                    suspicious=True
                )
                patterns.append(pattern)
            
            # Analyze IP address diversity
            unique_ips = set(e.get('ip_address') for e in recent_events if e.get('ip_address'))
            if len(unique_ips) > 3:  # Multiple IPs in short time
                pattern = DataAccessPattern(
                    user_id=user_id,
                    customer_id=recent_events[0].get('customer_id') if recent_events else None,
                    pattern_type='multiple_ip_addresses',
                    frequency=len(unique_ips),
                    time_window=f'{hours}h',
                    baseline_frequency=1.0,
                    deviation_score=len(unique_ips) - 1.0,
                    timestamp=datetime.utcnow(),
                    suspicious=len(unique_ips) > 5
                )
                patterns.append(pattern)
            
            # Analyze access volume
            total_requests = len(recent_events)
            baseline_requests = 50  # Expected baseline
            
            if total_requests > baseline_requests * 3:
                pattern = DataAccessPattern(
                    user_id=user_id,
                    customer_id=recent_events[0].get('customer_id') if recent_events else None,
                    pattern_type='high_volume_access',
                    frequency=total_requests,
                    time_window=f'{hours}h',
                    baseline_frequency=baseline_requests,
                    deviation_score=(total_requests - baseline_requests) / baseline_requests,
                    timestamp=datetime.utcnow(),
                    suspicious=total_requests > baseline_requests * 5
                )
                patterns.append(pattern)
            
            # Store detected patterns
            for pattern in patterns:
                if pattern.suspicious:
                    await self._store_access_pattern(pattern)
                    await self._trigger_pattern_alert(pattern)
            
            return patterns
            
        except Exception as e:
            print(f"Failed to detect anomalous patterns: {e}")
            return []
    
    async def generate_compliance_report(
        self, 
        customer_id: str,
        start_date: datetime,
        end_date: datetime,
        compliance_type: str = "HIPAA"
    ) -> Dict[str, Any]:
        """Generate compliance audit report"""
        
        try:
            # Get compliance events
            compliance_events = await self.get_audit_trail(
                customer_id=customer_id,
                start_time=start_date,
                end_time=end_date,
                event_type=EventType.PHI_ACCESS
            )
            
            # Get all access events
            all_events = await self.get_audit_trail(
                customer_id=customer_id,
                start_time=start_date,
                end_time=end_date
            )
            
            # Calculate compliance metrics
            phi_accesses = len([e for e in all_events if e.get('data_classification') == 'PHI'])
            unauthorized_attempts = len([e for e in all_events if e.get('result') == AccessResult.DENIED.value])
            unique_users = len(set(e.get('user_id') for e in all_events if e.get('user_id')))
            
            # Generate report
            report = {
                'report_id': str(uuid.uuid4()),
                'customer_id': customer_id,
                'compliance_type': compliance_type,
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_access_events': len(all_events),
                    'phi_access_events': phi_accesses,
                    'unauthorized_attempts': unauthorized_attempts,
                    'unique_users_accessed': unique_users,
                    'compliance_violations': 0  # TODO: Calculate violations
                },
                'access_patterns': {
                    'by_user': Counter(e.get('user_id') for e in all_events),
                    'by_action': Counter(e.get('action') for e in all_events),
                    'by_result': Counter(e.get('result') for e in all_events)
                },
                'phi_access_details': [
                    {
                        'timestamp': e.get('timestamp'),
                        'user_id': e.get('user_id'),
                        'action': e.get('action'),
                        'resource_type': e.get('resource_type'),
                        'purpose': e.get('additional_context', {}).get('purpose')
                    }
                    for e in all_events if e.get('data_classification') == 'PHI'
                ],
                'generated_at': datetime.utcnow().isoformat(),
                'generated_by': 'audit_service'
            }
            
            return report
            
        except Exception as e:
            print(f"Failed to generate compliance report: {e}")
            return {}
    
    # Internal helper methods
    
    async def _store_audit_record(self, record: Dict[str, Any]):
        """Store audit record in DynamoDB"""
        await self.audit_table.put_item(Item=record)
    
    async def _stream_to_kinesis(self, record: Dict[str, Any]):
        """Stream audit event to Kinesis for real-time processing"""
        try:
            self.kinesis.put_record(
                StreamName=self.kinesis_stream_name,
                Data=json.dumps(record, default=str),
                PartitionKey=record.get('customer_id', 'system')
            )
        except Exception as e:
            print(f"Failed to stream to Kinesis: {e}")
    
    async def _check_access_patterns(self, event: AuditEvent):
        """Check for anomalous access patterns"""
        # Run pattern detection for the user
        patterns = await self.detect_anomalous_patterns(event.user_id, hours=1)
        
        # Check for immediate red flags
        if event.result == AccessResult.DENIED:
            # Check for brute force patterns
            recent_failures = await self._count_recent_failures(event.user_id, minutes=60)
            if recent_failures >= self.anomaly_thresholds['failed_logins_per_hour']:
                await self._create_security_event(
                    SecurityEventType.BRUTE_FORCE_ATTEMPT,
                    Severity.HIGH,
                    f"User {event.user_id} had {recent_failures} failed attempts in 1 hour",
                    event.user_id,
                    event.customer_id,
                    ip_address=event.ip_address
                )
    
    async def _handle_access_denied(self, event: AuditEvent):
        """Handle access denied events"""
        # Log security event for denied access
        await self._create_security_event(
            SecurityEventType.UNAUTHORIZED_API_ACCESS,
            Severity.MEDIUM,
            f"Access denied for user {event.user_id} on {event.resource_type}",
            event.user_id,
            event.customer_id,
            ip_address=event.ip_address
        )
    
    async def _handle_phi_access(self, event: AuditEvent):
        """Handle PHI access events with additional compliance logging"""
        # Create compliance event
        compliance_event = ComplianceEvent(
            compliance_type="HIPAA",
            event_category="PHI_ACCESS",
            user_id=event.user_id,
            customer_id=event.customer_id,
            phi_accessed=True,
            minimum_necessary=event.additional_context.get('minimum_necessary', False),
            authorized_purpose=event.additional_context.get('purpose', 'unspecified'),
            timestamp=event.timestamp,
            duration_ms=event.duration_ms
        )
        
        await self.log_compliance_event(compliance_event)
    
    async def _handle_bulk_operation(self, event: AuditEvent):
        """Handle bulk operations with enhanced monitoring"""
        await self._create_security_event(
            SecurityEventType.BULK_DATA_OPERATION,
            Severity.MEDIUM,
            f"Bulk operation {event.action} performed by {event.user_id}",
            event.user_id,
            event.customer_id,
            ip_address=event.ip_address
        )
    
    async def _create_security_event(
        self, 
        event_type: SecurityEventType, 
        severity: Severity, 
        description: str,
        user_id: str = None,
        customer_id: str = None,
        **kwargs
    ):
        """Create and log a security event"""
        security_event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            customer_id=customer_id,
            description=description,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        
        await self.log_security_event(security_event)
    
    async def _trigger_security_alert(self, event: SecurityEvent):
        """Trigger immediate security alerts"""
        try:
            if self.security_alerts_topic:
                message = {
                    'event_type': event.event_type.value,
                    'severity': event.severity.value,
                    'description': event.description,
                    'user_id': event.user_id,
                    'customer_id': event.customer_id,
                    'timestamp': event.timestamp.isoformat(),
                    'requires_immediate_attention': event.severity in [Severity.HIGH, Severity.CRITICAL]
                }
                
                self.sns.publish(
                    TopicArn=self.security_alerts_topic,
                    Message=json.dumps(message),
                    Subject=f"Security Alert: {event.event_type.value} ({event.severity.value})"
                )
        except Exception as e:
            print(f"Failed to send security alert: {e}")
    
    async def _store_access_pattern(self, pattern: DataAccessPattern):
        """Store detected access pattern"""
        try:
            patterns_table = self.dynamodb.Table(self.patterns_table_name)
            await patterns_table.put_item(Item=pattern.to_dict())
        except Exception as e:
            print(f"Failed to store access pattern: {e}")
    
    async def _trigger_pattern_alert(self, pattern: DataAccessPattern):
        """Trigger alert for suspicious access pattern"""
        await self._create_security_event(
            SecurityEventType.SUSPICIOUS_USER_AGENT if 'user_agent' in pattern.pattern_type else SecurityEventType.UNUSUAL_IP_ACCESS,
            Severity.MEDIUM,
            f"Suspicious access pattern detected: {pattern.pattern_type} (score: {pattern.deviation_score:.2f})",
            pattern.user_id,
            pattern.customer_id
        )
    
    async def _count_recent_failures(self, user_id: str, minutes: int) -> int:
        """Count recent failed access attempts for a user"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        recent_events = await self.get_audit_trail(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=100
        )
        
        return len([e for e in recent_events if e.get('result') == AccessResult.DENIED.value])
    
    def _calculate_event_hash(self, event: Dict[str, Any]) -> str:
        """Calculate hash of audit event for integrity"""
        # Create a deterministic string representation
        hash_string = json.dumps(event, sort_keys=True, separators=(',', ':'), default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    async def _get_next_sequence_number(self) -> int:
        """Get next sequence number for audit events"""
        # Simple implementation - in production, use atomic counters
        return int(datetime.utcnow().timestamp() * 1000000)
    
    async def _update_threat_indicators(self, event: SecurityEvent):
        """Update threat intelligence indicators"""
        # Extract and store threat indicators
        if event.ip_address:
            # Track suspicious IPs
            pass
        
        if event.user_agent:
            # Track suspicious user agents
            pass
    
    async def _flag_compliance_violation(self, event: ComplianceEvent, violation_description: str):
        """Flag a compliance violation"""
        await self._create_security_event(
            SecurityEventType.UNAUTHORIZED_API_ACCESS,
            Severity.HIGH,
            f"Compliance violation: {violation_description}",
            event.user_id,
            event.customer_id
        )
    
    async def _handle_audit_failure(self, event: Any, error: str):
        """Handle audit system failures"""
        # Critical: Log to separate system
        failure_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'error': error,
            'event_summary': str(event)[:500],
            'severity': 'CRITICAL'
        }
        
        # Log to CloudWatch or separate audit system
        print(f"AUDIT FAILURE: {json.dumps(failure_record)}")