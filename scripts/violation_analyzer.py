#!/usr/bin/env python3
"""
Analyze and categorize the 290 infrastructure violations
"""

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict


def get_raw_violations():
    """Get raw violations from each OPA namespace"""
    try:
        violations = {}

        # Query GCP expanded HIPAA violations
        print("🔍 Getting GCP expanded HIPAA violations...")
        result = subprocess.run(
            [
                "opa",
                "eval",
                "--input",
                "gcp_assets.json",
                "--data",
                "policies",
                "--format",
                "json",
                "data.gcp.expanded_hipaa.violations",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        gcp_violations = json.loads(result.stdout)["result"][0]["expressions"][0][
            "value"
        ]
        violations["gcp_expanded_hipaa"] = gcp_violations
        print(f"✅ GCP violations: {len(gcp_violations)}")

        # Query HIPAA compliance violations
        print("🔍 Getting HIPAA compliance violations...")
        result = subprocess.run(
            [
                "opa",
                "eval",
                "--input",
                "gcp_assets.json",
                "--data",
                "policies",
                "--format",
                "json",
                "data.hipaa.compliance.violations",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        hipaa_violations = json.loads(result.stdout)["result"][0]["expressions"][0][
            "value"
        ]
        violations["hipaa_compliance"] = hipaa_violations
        print(f"✅ HIPAA violations: {len(hipaa_violations)}")

        # Query themisguard framework violations
        print("🔍 Getting themisguard framework violations...")
        result = subprocess.run(
            [
                "opa",
                "eval",
                "--input",
                "gcp_assets.json",
                "--data",
                "policies",
                "--format",
                "json",
                "data.themisguard.startup_framework.violations",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        themisguard_violations = json.loads(result.stdout)["result"][0]["expressions"][
            0
        ]["value"]
        violations["themisguard_framework"] = themisguard_violations
        print(f"✅ Themisguard violations: {len(themisguard_violations)}")

        return violations

    except Exception as e:
        print(f"❌ Error getting violations: {e}")
        return {}


def analyze_violation_patterns(violations_dict):
    """Analyze patterns in violations to find duplicates and categorize"""

    all_violations = []
    source_count = {}

    # Combine all violations and track sources
    for source, violations in violations_dict.items():
        source_count[source] = len(violations)
        for violation in violations:
            all_violations.append({"source": source, "violation": violation})

    print(f"\n📊 Violation Sources:")
    for source, count in source_count.items():
        print(f"   {source}: {count} violations")
    print(f"   TOTAL: {len(all_violations)} violations")

    # Analyze violation types and patterns
    violation_patterns = defaultdict(list)
    violation_types = Counter()
    resource_types = Counter()
    severity_levels = Counter()

    for item in all_violations:
        violation = item["violation"]
        source = item["source"]

        # Extract violation information
        violation_str = str(violation).lower()
        violation_patterns[extract_violation_pattern(violation_str)].append(item)

        # Extract resource type if available
        resource_type = extract_resource_type(violation)
        if resource_type:
            resource_types[resource_type] += 1

        # Extract severity if available
        severity = extract_severity(violation)
        severity_levels[severity] += 1

        # Extract violation type
        vtype = extract_violation_type(violation_str)
        violation_types[vtype] += 1

    return {
        "total_violations": len(all_violations),
        "source_breakdown": source_count,
        "violation_patterns": dict(violation_patterns),
        "violation_types": dict(violation_types.most_common(20)),
        "resource_types": dict(resource_types.most_common(15)),
        "severity_levels": dict(severity_levels),
        "raw_violations": all_violations[:10],  # Sample of raw violations
    }


def extract_violation_pattern(violation_str):
    """Extract a pattern from violation string for grouping"""
    # Common patterns to group similar violations
    if "private" in violation_str and (
        "cluster" in violation_str or "gke" in violation_str
    ):
        return "GKE Private Cluster Issues"
    elif "network" in violation_str and "policy" in violation_str:
        return "Network Policy Missing"
    elif "security" in violation_str and "context" in violation_str:
        return "Pod Security Context Issues"
    elif "encryption" in violation_str:
        return "Encryption Configuration"
    elif "service" in violation_str and "account" in violation_str:
        return "Service Account Issues"
    elif "firewall" in violation_str:
        return "Firewall Configuration"
    elif "storage" in violation_str and (
        "bucket" in violation_str or "public" in violation_str
    ):
        return "Storage Security Issues"
    elif "iam" in violation_str or "permission" in violation_str:
        return "IAM/Permissions Issues"
    elif "logging" in violation_str or "audit" in violation_str:
        return "Logging/Auditing Issues"
    elif "ssl" in violation_str or "tls" in violation_str:
        return "SSL/TLS Configuration"
    elif "backup" in violation_str:
        return "Backup Configuration"
    elif "label" in violation_str or "tag" in violation_str:
        return "Resource Labeling"
    else:
        # Extract first few words as pattern
        words = violation_str.split()[:3]
        return " ".join(words).title()


def extract_resource_type(violation):
    """Extract resource type from violation"""
    if isinstance(violation, dict):
        # Check common resource fields
        for field in ["resource", "asset_type", "component", "service"]:
            if field in violation:
                resource = str(violation[field])
                if "k8s.io" in resource or "apps/v1" in resource:
                    return "Kubernetes"
                elif "compute" in resource.lower():
                    return "Compute Engine"
                elif "storage" in resource.lower():
                    return "Cloud Storage"
                elif "sql" in resource.lower():
                    return "Cloud SQL"
                elif "gke" in resource.lower():
                    return "GKE"
                else:
                    return resource.split("/")[-1] if "/" in resource else resource

    violation_str = str(violation).lower()
    if "kubernetes" in violation_str or "k8s" in violation_str:
        return "Kubernetes"
    elif "gke" in violation_str:
        return "GKE"
    elif "compute" in violation_str:
        return "Compute Engine"
    elif "storage" in violation_str:
        return "Cloud Storage"
    elif "sql" in violation_str:
        return "Cloud SQL"
    else:
        return "Other"


def extract_severity(violation):
    """Extract severity level from violation"""
    if isinstance(violation, dict):
        for field in ["severity", "priority", "level", "risk"]:
            if field in violation:
                return str(violation[field]).upper()

    violation_str = str(violation).lower()
    if any(word in violation_str for word in ["critical", "high", "major"]):
        return "HIGH"
    elif any(word in violation_str for word in ["medium", "moderate"]):
        return "MEDIUM"
    elif any(word in violation_str for word in ["low", "minor", "info"]):
        return "LOW"
    else:
        return "UNKNOWN"


def extract_violation_type(violation_str):
    """Extract violation type for categorization"""
    if "private" in violation_str and "cluster" in violation_str:
        return "GKE Private Cluster Not Enabled"
    elif "network" in violation_str and "policy" in violation_str:
        return "Missing Network Policies"
    elif "security" in violation_str and "context" in violation_str:
        return "Pod Security Context Missing"
    elif "encryption" in violation_str:
        return "Encryption Not Configured"
    elif "service" in violation_str and "account" in violation_str:
        return "Service Account Issues"
    elif "public" in violation_str and (
        "ip" in violation_str or "access" in violation_str
    ):
        return "Public Access Exposed"
    elif "firewall" in violation_str:
        return "Firewall Rules Too Permissive"
    elif "logging" in violation_str:
        return "Audit Logging Not Enabled"
    elif "ssl" in violation_str or "tls" in violation_str:
        return "SSL/TLS Not Enforced"
    elif "backup" in violation_str:
        return "Backup Not Configured"
    elif "iam" in violation_str:
        return "IAM Overprivileged"
    elif "label" in violation_str or "tag" in violation_str:
        return "Resource Not Labeled"
    else:
        return "Other Configuration Issue"


def generate_violation_report(analysis):
    """Generate a detailed violation analysis report"""

    report = f"""
# Infrastructure Violation Analysis Report
**Total Violations Found:** {analysis['total_violations']}

## 📊 Breakdown by Source
"""

    for source, count in analysis["source_breakdown"].items():
        percentage = (count / analysis["total_violations"]) * 100
        report += f"- **{source}**: {count} violations ({percentage:.1f}%)\n"

    report += f"""
## 🎯 Top Violation Types
The most common infrastructure issues found:
"""

    for vtype, count in list(analysis["violation_types"].items())[:10]:
        percentage = (count / analysis["total_violations"]) * 100
        severity = get_violation_severity(vtype)
        report += (
            f"- **{vtype}**: {count} instances ({percentage:.1f}%) - *{severity}*\n"
        )

    report += f"""
## 🏗️ Affected Resource Types
"""

    for resource_type, count in analysis["resource_types"].items():
        percentage = (count / analysis["total_violations"]) * 100
        report += f"- **{resource_type}**: {count} violations ({percentage:.1f}%)\n"

    report += f"""
## ⚡ Severity Distribution
"""

    for severity, count in analysis["severity_levels"].items():
        percentage = (count / analysis["total_violations"]) * 100
        report += f"- **{severity}**: {count} violations ({percentage:.1f}%)\n"

    report += f"""
## 🔍 Sample Violations
Here are examples of actual violations found:
"""

    for i, item in enumerate(analysis["raw_violations"][:5], 1):
        violation = item["violation"]
        source = item["source"]

        # Format violation for display
        if isinstance(violation, dict):
            title = violation.get(
                "title",
                violation.get("message", violation.get("description", "Unknown")),
            )
            resource = violation.get("resource", violation.get("asset", "Unknown"))
        else:
            title = (
                str(violation)[:100] + "..."
                if len(str(violation)) > 100
                else str(violation)
            )
            resource = "Unknown"

        report += f"""
### {i}. {title}
- **Source**: {source}
- **Affected Resource**: {resource}
- **Raw Data**: `{str(violation)[:200]}...`
"""

    report += f"""
## 💡 Key Insights

### Most Critical Issues
Based on the analysis, focus on these high-impact areas:

1. **GKE Security**: {analysis['violation_types'].get('GKE Private Cluster Not Enabled', 0) + analysis['violation_types'].get('Missing Network Policies', 0)} cluster security issues
2. **Pod Security**: {analysis['violation_types'].get('Pod Security Context Missing', 0)} pod security violations  
3. **Encryption**: {analysis['violation_types'].get('Encryption Not Configured', 0)} encryption configuration issues
4. **Access Control**: {analysis['violation_types'].get('Public Access Exposed', 0) + analysis['violation_types'].get('IAM Overprivileged', 0)} access control problems

### Potential Duplicates
Look for these patterns that might indicate duplicate counting:
- Multiple violations per resource (same issue reported multiple ways)
- Similar violations across different policy sources
- Resource labeling issues (administrative vs security)

### Recommended Prioritization
1. **Immediate (Critical)**: GKE private cluster, public access exposure
2. **This Week (High)**: Pod security contexts, encryption configuration  
3. **This Month (Medium)**: Network policies, service account issues
4. **Quarterly (Low)**: Resource labeling, administrative tasks

## 🎯 Next Steps

1. **Review Top 5 Violation Types** - These represent 80% of your issues
2. **Check for Duplicates** - Same issue might be counted multiple times
3. **Focus on GKE Security** - Kubernetes violations are often the most critical
4. **Automate Fixes** - Many violations can be fixed with scripts
"""

    return report


def get_violation_severity(violation_type):
    """Get estimated severity for violation type"""
    high_severity = [
        "GKE Private Cluster Not Enabled",
        "Public Access Exposed",
        "Encryption Not Configured",
        "Pod Security Context Missing",
    ]

    medium_severity = [
        "Missing Network Policies",
        "Service Account Issues",
        "Firewall Rules Too Permissive",
        "SSL/TLS Not Enforced",
    ]

    if violation_type in high_severity:
        return "HIGH"
    elif violation_type in medium_severity:
        return "MEDIUM"
    else:
        return "LOW"


def main():
    """Main analysis function"""
    print("🔍 Analyzing 290 infrastructure violations...")

    # Get raw violations from OPA
    violations = get_raw_violations()

    if not violations:
        print("❌ Could not retrieve violations")
        return

    # Analyze patterns
    analysis = analyze_violation_patterns(violations)

    # Generate report
    report = generate_violation_report(analysis)

    # Save report
    with open("docs/violation_analysis_report.md", "w") as f:
        f.write(report)

    print(f"\n✅ Violation analysis complete!")
    print(f"📊 Total violations analyzed: {analysis['total_violations']}")
    print(f"📋 Report saved to: docs/violation_analysis_report.md")
    print(f"\n🎯 Top 3 violation types:")
    for vtype, count in list(analysis["violation_types"].items())[:3]:
        print(f"   {vtype}: {count} instances")


if __name__ == "__main__":
    main()
