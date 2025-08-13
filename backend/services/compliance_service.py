import json
import subprocess
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from ..core.config import settings
from ..models.compliance import (
    ComplianceReport,
    DashboardData,
    Violation,
    ViolationSeverity,
    ViolationType,
)


class ComplianceService:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        self.scans_table = self.dynamodb.Table(settings.DYNAMODB_TABLE_NAME)

    async def analyze_violations(self, assets: Dict[str, Any]) -> List[Violation]:
        """Analyze GCP assets for HIPAA violations using existing OPA policies"""
        violations = []

        # Save assets to temporary file for OPA evaluation
        temp_assets_file = f"/tmp/assets_{uuid.uuid4()}.json"
        with open(temp_assets_file, "w") as f:
            json.dump(assets, f)

        try:
            # Run OPA evaluations using existing policies
            policy_evaluations = [
                {
                    "name": "gcp_expanded_hipaa",
                    "query": "data.gcp.expanded_hipaa.violations",
                    "type": ViolationType.HIPAA_VIOLATION,
                },
                {
                    "name": "hipaa_compliance",
                    "query": "data.hipaa.compliance.violations",
                    "type": ViolationType.HIPAA_VIOLATION,
                },
                {
                    "name": "themisguard_framework",
                    "query": "data.themisguard.startup_framework.violations",
                    "type": ViolationType.COMPLIANCE_GAP,
                },
                {
                    "name": "environment_separation",
                    "query": "data.environment.separation.violations",
                    "type": ViolationType.COMPLIANCE_GAP,
                },
            ]

            for policy in policy_evaluations:
                try:
                    result = subprocess.run(
                        [
                            "opa",
                            "eval",
                            "--input",
                            temp_assets_file,
                            "--data",
                            "/Users/delatsi/projects/themisguard/policies",
                            "--format",
                            "json",
                            policy["query"],
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                    policy_violations = json.loads(result.stdout)["result"][0][
                        "expressions"
                    ][0]["value"]

                    for i, violation_text in enumerate(policy_violations):
                        violation = self._parse_violation(
                            violation_text, policy["type"], i
                        )
                        violations.append(violation)

                except subprocess.CalledProcessError as e:
                    print(f"Error running OPA evaluation for {policy['name']}: {e}")
                    continue

        finally:
            # Clean up temporary file
            import os

            if os.path.exists(temp_assets_file):
                os.remove(temp_assets_file)

        return violations

    def _parse_violation(
        self, violation_text: str, violation_type: ViolationType, index: int
    ) -> Violation:
        """Parse violation text into structured Violation object"""

        # Determine severity based on violation text
        severity = ViolationSeverity.MEDIUM
        if "Critical" in violation_text or "critical" in violation_text:
            severity = ViolationSeverity.CRITICAL
        elif (
            "High" in violation_text
            or "unrestricted access" in violation_text
            or "Violation (High)" in violation_text
        ):
            severity = ViolationSeverity.HIGH
        elif (
            "Violation (Medium)" in violation_text
            or "Environment Separation Violation (Medium)" in violation_text
        ):
            severity = ViolationSeverity.MEDIUM
        elif (
            "Review Required" in violation_text
            or "Violation (Low)" in violation_text
            or "Warning" in violation_text
        ):
            severity = ViolationSeverity.LOW

        # Extract resource information
        resource_name = "Unknown"
        resource_type = "Unknown"

        # Simple parsing - could be enhanced with regex
        if "Storage bucket" in violation_text:
            resource_type = "storage.bucket"
            start = violation_text.find("'") + 1
            end = violation_text.find("'", start)
            if start > 0 and end > start:
                resource_name = violation_text[start:end]
        elif "Firewall rule" in violation_text:
            resource_type = "compute.firewall"
            start = violation_text.find("'") + 1
            end = violation_text.find("'", start)
            if start > 0 and end > start:
                resource_name = violation_text[start:end]
        elif "Compute instance" in violation_text:
            resource_type = "compute.instance"
            start = violation_text.find("'") + 1
            end = violation_text.find("'", start)
            if start > 0 and end > start:
                resource_name = violation_text[start:end]
        elif "Cloud SQL instance" in violation_text:
            resource_type = "sql.instance"
            start = violation_text.find("'") + 1
            end = violation_text.find("'", start)
            if start > 0 and end > start:
                resource_name = violation_text[start:end]
        elif "GKE cluster" in violation_text:
            resource_type = "container.cluster"
            start = violation_text.find("'") + 1
            end = violation_text.find("'", start)
            if start > 0 and end > start:
                resource_name = violation_text[start:end]
        elif "Cloud Function" in violation_text:
            resource_type = "cloudfunctions.function"
            start = violation_text.find("'") + 1
            end = violation_text.find("'", start)
            if start > 0 and end > start:
                resource_name = violation_text[start:end]

        return Violation(
            id=str(uuid.uuid4()),
            type=violation_type,
            severity=severity,
            title=(
                violation_text.split(" - ")[0]
                if " - " in violation_text
                else violation_text[:50]
            ),
            description=violation_text,
            resource_type=resource_type,
            resource_name=resource_name,
            project_id=settings.GCP_PROJECT_ID or "unknown",
            hipaa_section=self._extract_hipaa_section(violation_text),
            remediation_steps=self._get_remediation_steps(violation_text),
        )

    def _extract_hipaa_section(self, violation_text: str) -> Optional[str]:
        """Extract HIPAA section from violation text"""
        hipaa_sections = {
            "Technical Safeguards": "§164.312",
            "Admin Safeguards": "§164.308",
            "Administrative Safeguards": "§164.308",
            "Physical Safeguards": "§164.310",
            "Network Security": "§164.312(e)",
            "Breach Notification": "§164.400",
            "Minimum Necessary": "§164.502(b)",
            "Environment Separation": "§164.308(a)(3)",
            "SOC 2 Security": "SOC 2 CC6.1",
            "Processing Integrity": "SOC 2 CC7.1",
        }

        for section_name, section_code in hipaa_sections.items():
            if section_name in violation_text:
                return section_code

        return None

    def _get_remediation_steps(self, violation_text: str) -> List[str]:
        """Get remediation steps based on violation type"""
        steps = []

        if "Storage bucket" in violation_text and "public access" in violation_text:
            steps = [
                "Review bucket IAM policies",
                "Remove public access permissions",
                "Implement least privilege access",
                "Enable uniform bucket-level access",
            ]
        elif (
            "Firewall rule" in violation_text
            and "unrestricted access" in violation_text
        ):
            steps = [
                "Review firewall rule configuration",
                "Restrict source IP ranges",
                "Implement network segmentation",
                "Enable VPC flow logs",
            ]
        elif "service account" in violation_text:
            steps = [
                "Create custom service account",
                "Assign minimal required permissions",
                "Remove default service account usage",
                "Implement service account keys rotation",
            ]
        elif "Environment Separation" in violation_text and "tagging" in violation_text:
            steps = [
                "Implement environment tagging strategy (dev/staging/prod)",
                "Create environment-specific resource naming conventions",
                "Apply consistent labels to all cloud resources",
                "Set up automated tagging policies and compliance monitoring",
                "Document environment classification procedures",
            ]
        elif "Environment Separation" in violation_text and "network" in violation_text:
            steps = [
                "Create environment-specific VPCs or networks",
                "Implement network segmentation between environments",
                "Configure environment-specific security groups and firewall rules",
                "Enable network monitoring and flow logs",
                "Document network architecture and separation controls",
            ]
        elif (
            "Environment Separation" in violation_text
            and "access controls" in violation_text
        ):
            steps = [
                "Implement environment-specific IAM roles and policies",
                "Create separate service accounts for each environment",
                "Configure conditional access based on environment",
                "Enable audit logging for cross-environment access attempts",
                "Regular review of environment access permissions",
            ]
        elif "production-grade configuration" in violation_text:
            steps = [
                "Enable versioning and lifecycle policies for production storage",
                "Implement backup and disaster recovery procedures",
                "Configure monitoring and alerting for production resources",
                "Apply security hardening specific to production environments",
                "Document production environment standards and procedures",
            ]
        else:
            steps = [
                "Review the identified resource configuration",
                "Implement HIPAA-compliant security controls",
                "Document remediation actions",
                "Schedule regular compliance reviews",
            ]

        return steps

    async def store_scan_results(
        self, user_id: str, project_id: str, violations: List[Violation]
    ) -> str:
        """Store scan results in DynamoDB and S3"""
        scan_id = str(uuid.uuid4())

        # Calculate compliance metrics
        violation_counts = {
            ViolationSeverity.CRITICAL: sum(
                1 for v in violations if v.severity == ViolationSeverity.CRITICAL
            ),
            ViolationSeverity.HIGH: sum(
                1 for v in violations if v.severity == ViolationSeverity.HIGH
            ),
            ViolationSeverity.MEDIUM: sum(
                1 for v in violations if v.severity == ViolationSeverity.MEDIUM
            ),
            ViolationSeverity.LOW: sum(
                1 for v in violations if v.severity == ViolationSeverity.LOW
            ),
        }

        # Calculate compliance score (simple formula)
        total_violations = len(violations)
        compliance_score = max(
            0,
            100
            - (
                violation_counts[ViolationSeverity.CRITICAL] * 20
                + violation_counts[ViolationSeverity.HIGH] * 10
                + violation_counts[ViolationSeverity.MEDIUM] * 5
                + violation_counts[ViolationSeverity.LOW] * 2
            ),
        )

        # Create compliance report
        report = ComplianceReport(
            scan_id=scan_id,
            user_id=user_id,
            project_id=project_id,
            violations=violations,
            total_violations=total_violations,
            critical_violations=violation_counts[ViolationSeverity.CRITICAL],
            high_violations=violation_counts[ViolationSeverity.HIGH],
            medium_violations=violation_counts[ViolationSeverity.MEDIUM],
            low_violations=violation_counts[ViolationSeverity.LOW],
            compliance_score=compliance_score,
        )

        # Store in DynamoDB
        try:
            self.scans_table.put_item(
                Item={
                    "scan_id": scan_id,
                    "user_id": user_id,
                    "project_id": project_id,
                    "scan_timestamp": report.scan_timestamp.isoformat(),
                    "total_violations": total_violations,
                    "compliance_score": compliance_score,
                    "status": "completed",
                }
            )

            # Store detailed report in S3
            s3_key = f"reports/{user_id}/{scan_id}.json"
            self.s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=s3_key,
                Body=report.model_dump_json(),
                ContentType="application/json",
            )

        except ClientError as e:
            raise Exception(f"Failed to store scan results: {e}")

        # Record usage for billing (async, don't block scan completion)
        try:
            from .stripe_service import StripeService

            stripe_service = StripeService()
            await stripe_service.record_usage(
                user_id=user_id, scans_count=1, projects_scanned=1, api_calls=0
            )
        except Exception as e:
            # Log error but don't fail the scan
            print(f"Failed to record usage for billing: {e}")

        return scan_id

    async def get_scan_report(self, scan_id: str, user_id: str) -> ComplianceReport:
        """Retrieve scan report from S3"""
        try:
            s3_key = f"reports/{user_id}/{scan_id}.json"
            response = self.s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
            report_data = json.loads(response["Body"].read())
            return ComplianceReport(**report_data)

        except ClientError as e:
            raise Exception(f"Failed to retrieve scan report: {e}")

    async def list_user_reports(
        self, user_id: str, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all reports for a user"""
        try:
            response = self.scans_table.query(
                IndexName="user-index",
                KeyConditionExpression="user_id = :user_id",
                ExpressionAttributeValues={":user_id": user_id},
                Limit=limit,
                ScanIndexForward=False,  # Get newest first
            )

            return response.get("Items", [])

        except ClientError as e:
            raise Exception(f"Failed to list reports: {e}")

    async def get_dashboard_summary(self, user_id: str) -> DashboardData:
        """Get dashboard summary for a user"""
        try:
            # Get recent scans
            recent_scans_response = self.scans_table.query(
                IndexName="user-index",
                KeyConditionExpression="user_id = :user_id",
                ExpressionAttributeValues={":user_id": user_id},
                Limit=5,
                ScanIndexForward=False,
            )

            scans = recent_scans_response.get("Items", [])

            # Calculate summary metrics
            total_scans = len(scans)
            projects = set(scan.get("project_id") for scan in scans)
            total_projects = len(projects)

            overall_compliance_score = 0
            if scans:
                overall_compliance_score = sum(
                    scan.get("compliance_score", 0) for scan in scans
                ) / len(scans)

            last_scan_date = None
            if scans:
                last_scan_date = datetime.fromisoformat(scans[0]["scan_timestamp"])

            return DashboardData(
                user_id=user_id,
                total_scans=total_scans,
                total_projects=total_projects,
                overall_compliance_score=overall_compliance_score,
                last_scan_date=last_scan_date,
            )

        except ClientError as e:
            raise Exception(f"Failed to get dashboard data: {e}")
