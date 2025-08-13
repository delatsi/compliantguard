from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ViolationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationType(str, Enum):
    HIPAA_VIOLATION = "hipaa_violation"
    HIPAA_REVIEW_REQUIRED = "hipaa_review_required"
    SECURITY_RISK = "security_risk"
    COMPLIANCE_GAP = "compliance_gap"


class Violation(BaseModel):
    id: str = Field(..., description="Unique violation identifier")
    type: ViolationType = Field(..., description="Type of violation")
    severity: ViolationSeverity = Field(..., description="Violation severity level")
    title: str = Field(..., description="Violation title")
    description: str = Field(..., description="Detailed violation description")
    resource_type: str = Field(..., description="GCP resource type")
    resource_name: str = Field(..., description="GCP resource name")
    project_id: str = Field(..., description="GCP project ID")
    hipaa_section: Optional[str] = Field(None, description="Related HIPAA section")
    remediation_steps: List[str] = Field(default=[], description="Steps to remediate")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ComplianceReport(BaseModel):
    scan_id: str = Field(..., description="Unique scan identifier")
    user_id: str = Field(..., description="User who initiated the scan")
    project_id: str = Field(..., description="GCP project ID")
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow)
    violations: List[Violation] = Field(
        default=[], description="List of violations found"
    )
    total_violations: int = Field(0, description="Total number of violations")
    critical_violations: int = Field(0, description="Number of critical violations")
    high_violations: int = Field(0, description="Number of high severity violations")
    medium_violations: int = Field(
        0, description="Number of medium severity violations"
    )
    low_violations: int = Field(0, description="Number of low severity violations")
    compliance_score: float = Field(0.0, description="Overall compliance score (0-100)")
    status: str = Field("completed", description="Scan status")


class ViolationSummary(BaseModel):
    total_violations: int = Field(0, description="Total violations")
    violations_by_severity: Dict[ViolationSeverity, int] = Field(
        default={}, description="Violations grouped by severity"
    )
    violations_by_type: Dict[ViolationType, int] = Field(
        default={}, description="Violations grouped by type"
    )
    compliance_score: float = Field(0.0, description="Overall compliance score")


class DashboardData(BaseModel):
    user_id: str = Field(..., description="User ID")
    total_scans: int = Field(0, description="Total number of scans")
    total_projects: int = Field(0, description="Total number of projects scanned")
    recent_scans: List[ComplianceReport] = Field(default=[], description="Recent scans")
    overall_compliance_score: float = Field(
        0.0, description="Overall compliance score across all projects"
    )
    violation_summary: ViolationSummary = Field(
        default=ViolationSummary(), description="Summary of violations"
    )
    last_scan_date: Optional[datetime] = Field(None, description="Date of last scan")


class ScanRequest(BaseModel):
    project_id: str = Field(..., description="GCP project ID to scan")
    scan_type: str = Field("full", description="Type of scan (full, quick, custom)")
    include_policies: List[str] = Field(
        default=[], description="Specific policies to include"
    )
    exclude_policies: List[str] = Field(
        default=[], description="Specific policies to exclude"
    )
