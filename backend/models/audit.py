"""
Audit Models - Data structures for comprehensive audit logging
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AccessResult(Enum):
    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"
    NOT_FOUND = "not_found"
    PARTIAL = "partial"


class EventType(Enum):
    DATA_ACCESS = "data_access"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ADMIN_ACTION = "admin_action"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    PHI_ACCESS = "phi_access"
    BULK_OPERATION = "bulk_operation"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    ENCRYPTION_EVENT = "encryption_event"
    PERMISSION_CHANGE = "permission_change"


class SecurityEventType(Enum):
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    UNUSUAL_IP_ACCESS = "unusual_ip_access"
    BULK_DATA_OPERATION = "bulk_data_operation"
    MULTIPLE_FAILED_LOGINS = "multiple_failed_logins"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION_ATTEMPT = "data_exfiltration_attempt"
    UNAUTHORIZED_API_ACCESS = "unauthorized_api_access"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Core audit event structure"""

    user_id: str
    customer_id: Optional[str]
    action: str
    resource_type: str
    result: AccessResult
    timestamp: datetime
    event_type: EventType = EventType.DATA_ACCESS
    resource_id: Optional[str] = None
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[int] = None
    data_classification: Optional[str] = None
    compliance_tags: List[str] = None
    additional_context: Dict[str, Any] = None

    def __post_init__(self):
        if self.compliance_tags is None:
            self.compliance_tags = []
        if self.additional_context is None:
            self.additional_context = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "audit_id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "result": self.result.value,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "duration_ms": self.duration_ms,
            "data_classification": self.data_classification,
            "compliance_tags": self.compliance_tags,
            "additional_context": self.additional_context,
            "created_at": datetime.utcnow().isoformat(),
            "ttl": int(
                (datetime.utcnow().timestamp()) + (7 * 365 * 24 * 60 * 60)
            ),  # 7 years
        }


@dataclass
class SecurityEvent:
    """Security-specific event structure"""

    event_type: SecurityEventType
    severity: Severity
    user_id: Optional[str]
    customer_id: Optional[str]
    description: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    source_system: str = "themisguard"
    detection_method: str = "automated"
    false_positive: bool = False
    investigated: bool = False
    resolved: bool = False
    resolution_notes: Optional[str] = None
    related_events: List[str] = None
    threat_indicators: Dict[str, Any] = None
    response_actions: List[str] = None

    def __post_init__(self):
        if self.related_events is None:
            self.related_events = []
        if self.threat_indicators is None:
            self.threat_indicators = {}
        if self.response_actions is None:
            self.response_actions = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "security_event_id": str(uuid.uuid4()),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "source_system": self.source_system,
            "detection_method": self.detection_method,
            "false_positive": self.false_positive,
            "investigated": self.investigated,
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes,
            "related_events": self.related_events,
            "threat_indicators": self.threat_indicators,
            "response_actions": self.response_actions,
            "created_at": datetime.utcnow().isoformat(),
            "ttl": int(
                (datetime.utcnow().timestamp()) + (7 * 365 * 24 * 60 * 60)
            ),  # 7 years
        }


@dataclass
class ComplianceEvent:
    """HIPAA and other compliance-specific events"""

    compliance_type: str  # HIPAA, SOC2, PCI, etc.
    event_category: str
    user_id: str
    customer_id: Optional[str]
    phi_accessed: bool
    minimum_necessary: bool
    authorized_purpose: str
    timestamp: datetime
    duration_ms: Optional[int] = None
    data_elements_accessed: List[str] = None
    business_justification: Optional[str] = None
    approval_required: bool = False
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    audit_trail_id: Optional[str] = None

    def __post_init__(self):
        if self.data_elements_accessed is None:
            self.data_elements_accessed = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "compliance_event_id": str(uuid.uuid4()),
            "compliance_type": self.compliance_type,
            "event_category": self.event_category,
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "phi_accessed": self.phi_accessed,
            "minimum_necessary": self.minimum_necessary,
            "authorized_purpose": self.authorized_purpose,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "data_elements_accessed": self.data_elements_accessed,
            "business_justification": self.business_justification,
            "approval_required": self.approval_required,
            "approved_by": self.approved_by,
            "approval_timestamp": (
                self.approval_timestamp.isoformat() if self.approval_timestamp else None
            ),
            "audit_trail_id": self.audit_trail_id,
            "created_at": datetime.utcnow().isoformat(),
            "ttl": int(
                (datetime.utcnow().timestamp()) + (7 * 365 * 24 * 60 * 60)
            ),  # 7 years
        }


@dataclass
class DataAccessPattern:
    """Pattern analysis for detecting anomalous access"""

    user_id: str
    customer_id: Optional[str]
    pattern_type: str
    frequency: int
    time_window: str
    baseline_frequency: float
    deviation_score: float
    timestamp: datetime
    suspicious: bool = False
    investigated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "pattern_id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "pattern_type": self.pattern_type,
            "frequency": self.frequency,
            "time_window": self.time_window,
            "baseline_frequency": self.baseline_frequency,
            "deviation_score": self.deviation_score,
            "timestamp": self.timestamp.isoformat(),
            "suspicious": self.suspicious,
            "investigated": self.investigated,
            "created_at": datetime.utcnow().isoformat(),
            "ttl": int(
                (datetime.utcnow().timestamp()) + (90 * 24 * 60 * 60)
            ),  # 90 days
        }


# Helper functions for creating common audit events
def create_data_access_event(
    user_id: str,
    customer_id: str,
    action: str,
    resource_type: str,
    result: AccessResult,
    resource_id: str = None,
    error_message: str = None,
    **kwargs
) -> AuditEvent:
    """Create a standard data access audit event"""
    return AuditEvent(
        user_id=user_id,
        customer_id=customer_id,
        action=action,
        resource_type=resource_type,
        result=result,
        resource_id=resource_id,
        error_message=error_message,
        timestamp=datetime.utcnow(),
        event_type=EventType.DATA_ACCESS,
        **kwargs
    )


def create_phi_access_event(
    user_id: str,
    customer_id: str,
    action: str,
    purpose: str,
    minimum_necessary: bool = True,
    **kwargs
) -> ComplianceEvent:
    """Create a HIPAA PHI access compliance event"""
    return ComplianceEvent(
        compliance_type="HIPAA",
        event_category="PHI_ACCESS",
        user_id=user_id,
        customer_id=customer_id,
        phi_accessed=True,
        minimum_necessary=minimum_necessary,
        authorized_purpose=purpose,
        timestamp=datetime.utcnow(),
        **kwargs
    )


def create_security_event(
    event_type: SecurityEventType,
    severity: Severity,
    description: str,
    user_id: str = None,
    customer_id: str = None,
    **kwargs
) -> SecurityEvent:
    """Create a security event"""
    return SecurityEvent(
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        customer_id=customer_id,
        description=description,
        timestamp=datetime.utcnow(),
        **kwargs
    )
