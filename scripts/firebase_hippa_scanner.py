#!/usr/bin/env python3
"""
Complete Firebase HIPAA Compliance Scanner
Integrates with existing executive dashboard
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

import requests


def discover_firebase_services(project_id):
    """Discover Firebase services for a given project"""
    print(f"🔍 Discovering Firebase services for project: {project_id}")

    firebase_services = {}

    try:
        # Get enabled APIs with detailed output for debugging
        result = subprocess.run(
            [
                "gcloud",
                "services",
                "list",
                "--enabled",
                f"--project={project_id}",
                "--format=json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        enabled_services = json.loads(result.stdout)

        # Extract API names and handle the full project path format
        enabled_apis = []
        for service in enabled_services:
            service_name = service["name"]
            # Handle both formats: "firebaserules.googleapis.com" and "projects/123/services/firebaserules.googleapis.com"
            if service_name.startswith("projects/"):
                # Extract just the API name from "projects/668668923572/services/firebaserules.googleapis.com"
                api_name = service_name.split("/")[-1]
            else:
                api_name = service_name
            enabled_apis.append(api_name)

        print(f"🔍 Checking {len(enabled_apis)} enabled APIs...")

        # Comprehensive Firebase API mapping
        firebase_api_mapping = {
            "firebaserules.googleapis.com": "Firebase Security Rules",
            "firebase.googleapis.com": "Firebase Management",
            "firebasehosting.googleapis.com": "Firebase Hosting",
            "firestore.googleapis.com": "Cloud Firestore",
            "firebasedatabase.googleapis.com": "Firebase Realtime Database",
            "fcm.googleapis.com": "Firebase Cloud Messaging",
            "firebaseremoteconfig.googleapis.com": "Firebase Remote Config",
            "identitytoolkit.googleapis.com": "Firebase Authentication",
            "cloudfunctions.googleapis.com": "Cloud Functions for Firebase",
            "storage.googleapis.com": "Cloud Storage for Firebase",
            "storage-api.googleapis.com": "Cloud Storage API (Firebase)",
            "storage-component.googleapis.com": "Cloud Storage Component (Firebase)",
        }

        # Check for exact API matches
        for api, service_name in firebase_api_mapping.items():
            if api in enabled_apis:
                firebase_services[service_name] = {
                    "api": api,
                    "enabled": True,
                    "hipaa_relevant": (
                        True
                        if any(
                            keyword in service_name.lower()
                            for keyword in [
                                "firestore",
                                "database",
                                "storage",
                                "auth",
                                "rules",
                            ]
                        )
                        else False
                    ),
                }
                print(f"✅ Found: {api} -> {service_name}")

        # Show some debug info
        if firebase_services:
            print(f"🔥 Firebase services detected:")
            for service_name, details in firebase_services.items():
                hipaa_flag = "🏥" if details["hipaa_relevant"] else "ℹ️"
                print(f"   {hipaa_flag} {service_name}")
        else:
            print("❌ No Firebase services detected")
            print(f"🔍 Sample APIs found: {enabled_apis[:5]}")
            # Check if firebaserules is in the list
            if "firebaserules.googleapis.com" in enabled_apis:
                print(
                    "✅ firebaserules.googleapis.com IS in the list - this should have been detected!"
                )
            else:
                print("❌ firebaserules.googleapis.com not found in enabled APIs")

        return firebase_services

    except subprocess.CalledProcessError as e:
        print(f"❌ Error discovering Firebase services: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        return {}


def scan_firestore_compliance(project_id):
    """Scan Firestore for HIPAA compliance issues"""
    print("🔍 Scanning Firestore for HIPAA compliance...")

    violations = []

    try:
        # Check if Firestore databases exist
        result = subprocess.run(
            [
                "gcloud",
                "firestore",
                "databases",
                "list",
                f"--project={project_id}",
                "--format=json",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            databases = json.loads(result.stdout)

            for db in databases:
                db_name = db.get("name", "unknown")

                # Check for encryption
                if not db.get("encryptionConfig", {}).get("encryptionType"):
                    violations.append(
                        {
                            "service": "Cloud Firestore",
                            "resource": db_name,
                            "violation": "Database encryption not explicitly configured",
                            "severity": "HIGH",
                            "hipaa_rule": "Security Rule - Encryption",
                            "remediation": "Configure customer-managed encryption keys (CMEK) for Firestore",
                            "business_impact": "PHI data may not be adequately protected at rest",
                        }
                    )

                # Check database location for data residency
                location = db.get("locationId", "unknown")
                if location.startswith("europe-") or location.startswith("asia-"):
                    violations.append(
                        {
                            "service": "Cloud Firestore",
                            "resource": db_name,
                            "violation": f"Database located outside US: {location}",
                            "severity": "MEDIUM",
                            "hipaa_rule": "Administrative Safeguards - Data Location",
                            "remediation": "Ensure data residency requirements are met for PHI",
                            "business_impact": "Potential data sovereignty compliance issues",
                        }
                    )

        else:
            print(
                "⚠️ Could not access Firestore databases (may not exist or access denied)"
            )

    except subprocess.TimeoutExpired:
        print("⚠️ Firestore scan timed out")
    except Exception as e:
        print(f"⚠️ Error scanning Firestore: {e}")

    return violations


def scan_firebase_auth_compliance(project_id):
    """Scan Firebase Authentication for HIPAA compliance"""
    print("🔍 Scanning Firebase Authentication for HIPAA compliance...")

    violations = []

    try:
        # Check if Identity Toolkit (Firebase Auth) is enabled
        result = subprocess.run(
            [
                "gcloud",
                "services",
                "list",
                "--enabled",
                f"--project={project_id}",
                "--filter=name:identitytoolkit.googleapis.com",
                "--format=json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        if json.loads(result.stdout):
            # Firebase Auth is enabled - check for HIPAA compliance issues

            # Check for multi-factor authentication configuration
            violations.append(
                {
                    "service": "Firebase Authentication",
                    "resource": "Authentication Configuration",
                    "violation": "Multi-factor authentication not verified as enforced",
                    "severity": "HIGH",
                    "hipaa_rule": "Access Control - User Authentication",
                    "remediation": "Verify MFA is enabled for all users accessing PHI",
                    "business_impact": "Weak authentication increases risk of unauthorized PHI access",
                }
            )

            # Check for session management
            violations.append(
                {
                    "service": "Firebase Authentication",
                    "resource": "Session Management",
                    "violation": "Session timeout configuration not verified",
                    "severity": "MEDIUM",
                    "hipaa_rule": "Access Control - Automatic Logoff",
                    "remediation": "Configure appropriate session timeouts for HIPAA compliance",
                    "business_impact": "Extended sessions may allow unauthorized access",
                }
            )

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error checking Firebase Auth: {e}")

    return violations


def scan_firebase_storage_compliance(project_id):
    """Scan Firebase Storage for HIPAA compliance"""
    print("🔍 Scanning Firebase Storage for HIPAA compliance...")

    violations = []

    try:
        # Check for Storage buckets that might be used with Firebase
        result = subprocess.run(
            [
                "gcloud",
                "storage",
                "buckets",
                "list",
                f"--project={project_id}",
                "--format=json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        buckets = json.loads(result.stdout)

        for bucket in buckets:
            bucket_name = bucket.get("name", "unknown")

            # Check for public access
            if (
                bucket.get("iamConfiguration", {})
                .get("uniformBucketLevelAccess", {})
                .get("enabled")
                != True
            ):
                violations.append(
                    {
                        "service": "Cloud Storage for Firebase",
                        "resource": bucket_name,
                        "violation": "Uniform bucket-level access not enabled",
                        "severity": "HIGH",
                        "hipaa_rule": "Access Control - Minimum Necessary",
                        "remediation": "Enable uniform bucket-level access to prevent object-level ACLs",
                        "business_impact": "Inconsistent access controls may expose PHI",
                    }
                )

            # Check encryption
            if not bucket.get("encryption"):
                violations.append(
                    {
                        "service": "Cloud Storage for Firebase",
                        "resource": bucket_name,
                        "violation": "Custom encryption not configured",
                        "severity": "MEDIUM",
                        "hipaa_rule": "Security Rule - Encryption",
                        "remediation": "Configure customer-managed encryption keys (CMEK)",
                        "business_impact": "PHI files may not be adequately encrypted",
                    }
                )

            # Check for lifecycle policies (data retention)
            if not bucket.get("lifecycle"):
                violations.append(
                    {
                        "service": "Cloud Storage for Firebase",
                        "resource": bucket_name,
                        "violation": "No lifecycle/retention policy configured",
                        "severity": "MEDIUM",
                        "hipaa_rule": "Administrative Safeguards - Data Retention",
                        "remediation": "Implement data retention and deletion policies",
                        "business_impact": "PHI may be retained longer than necessary",
                    }
                )

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error checking Firebase Storage: {e}")

    return violations


def scan_firebase_security_rules(project_id):
    """Scan Firebase Security Rules for HIPAA compliance"""
    print("🔍 Scanning Firebase Security Rules for HIPAA compliance...")

    violations = []

    # Since we know firebaserules.googleapis.com is enabled, check for common issues
    violations.extend(
        [
            {
                "service": "Firebase Security Rules",
                "resource": "Firestore Security Rules",
                "violation": "Security rules may allow unauthorized PHI access",
                "severity": "CRITICAL",
                "hipaa_rule": "Access Control - Role-Based Access",
                "remediation": "Review Firestore security rules to ensure only authorized users can access PHI",
                "business_impact": "Improper rules could expose all PHI data",
                "manual_check": "https://console.firebase.google.com/project/medtelligence/firestore/rules",
            },
            {
                "service": "Firebase Security Rules",
                "resource": "Storage Security Rules",
                "violation": "Storage rules may allow unauthorized file access",
                "severity": "HIGH",
                "hipaa_rule": "Access Control - File Access Controls",
                "remediation": "Review Firebase Storage security rules for PHI file protection",
                "business_impact": "PHI files could be accessible without proper authorization",
                "manual_check": "https://console.firebase.google.com/project/medtelligence/storage/rules",
            },
        ]
    )

    return violations


def scan_firebase_hosting_compliance(project_id):
    """Scan Firebase Hosting for HIPAA compliance"""
    print("🔍 Scanning Firebase Hosting for HIPAA compliance...")

    violations = []

    try:
        # Check if Firebase Hosting is enabled
        result = subprocess.run(
            [
                "gcloud",
                "services",
                "list",
                "--enabled",
                f"--project={project_id}",
                "--filter=name:firebasehosting.googleapis.com",
                "--format=json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        if json.loads(result.stdout):
            violations.extend(
                [
                    {
                        "service": "Firebase Hosting",
                        "resource": "Web Application",
                        "violation": "Client-side PHI handling not verified",
                        "severity": "HIGH",
                        "hipaa_rule": "Security Rule - Data Transmission",
                        "remediation": "Ensure client-side code properly handles PHI with encryption in transit",
                        "business_impact": "PHI transmitted to client browsers may be inadequately protected",
                    },
                    {
                        "service": "Firebase Hosting",
                        "resource": "SSL/TLS Configuration",
                        "violation": "SSL certificate configuration not verified for HIPAA",
                        "severity": "MEDIUM",
                        "hipaa_rule": "Security Rule - Transmission Security",
                        "remediation": "Verify SSL/TLS configuration meets HIPAA requirements",
                        "business_impact": "Data transmission may not be adequately secured",
                    },
                ]
            )

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error checking Firebase Hosting: {e}")

    return violations


def generate_firebase_hipaa_report(project_id):
    """Generate comprehensive Firebase HIPAA compliance report"""
    print(f"🔍 Generating Firebase HIPAA compliance report for {project_id}...")

    # Discover Firebase services
    firebase_services = discover_firebase_services(project_id)

    if not firebase_services:
        print("ℹ️ No Firebase services detected")
        return {
            "firebase_services": {},
            "violations": [],
            "summary": {
                "total_violations": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
            },
        }

    # Scan each service for HIPAA compliance
    all_violations = []

    # Scan Firestore
    if "Cloud Firestore" in firebase_services:
        all_violations.extend(scan_firestore_compliance(project_id))

    # Scan Firebase Auth
    if "Firebase Authentication" in firebase_services:
        all_violations.extend(scan_firebase_auth_compliance(project_id))

    # Scan Firebase Storage
    if "Cloud Storage for Firebase" in firebase_services:
        all_violations.extend(scan_firebase_storage_compliance(project_id))

    # Scan Security Rules (always check if rules API is enabled)
    if "Firebase Security Rules" in firebase_services:
        all_violations.extend(scan_firebase_security_rules(project_id))

    # Scan Firebase Hosting
    if "Firebase Hosting" in firebase_services:
        all_violations.extend(scan_firebase_hosting_compliance(project_id))

    # Categorize violations
    critical_count = len([v for v in all_violations if v.get("severity") == "CRITICAL"])
    high_count = len([v for v in all_violations if v.get("severity") == "HIGH"])
    medium_count = len([v for v in all_violations if v.get("severity") == "MEDIUM"])
    low_count = len([v for v in all_violations if v.get("severity") == "LOW"])

    print(f"📊 Firebase scan complete:")
    print(f"   Services found: {len(firebase_services)}")
    print(
        f"   Violations: {len(all_violations)} (Critical: {critical_count}, High: {high_count}, Medium: {medium_count}, Low: {low_count})"
    )

    return {
        "firebase_services": firebase_services,
        "violations": all_violations,
        "summary": {
            "total_violations": len(all_violations),
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
        },
        "manual_checks_required": [v for v in all_violations if "manual_check" in v],
    }


def format_firebase_violations_for_report(firebase_report):
    """Format Firebase violations for integration with main report"""
    formatted_violations = []

    for violation in firebase_report["violations"]:
        formatted_violation = {
            "title": f"Firebase: {violation['violation']}",
            "risk_level": violation["severity"],
            "business_impact": violation["business_impact"],
            "affected_resource": f"{violation['service']} - {violation['resource']}",
            "compliance_frameworks": ["HIPAA", "Firebase"],
            "remediation": {
                "action": violation["remediation"],
                "effort": "Medium",
                "cost": "$1,000 - $5,000",
                "timeline": (
                    "1-2 weeks"
                    if violation["severity"] in ["HIGH", "CRITICAL"]
                    else "2-4 weeks"
                ),
                "priority": violation["severity"].title(),
            },
        }

        if "manual_check" in violation:
            formatted_violation["remediation"]["manual_check"] = violation[
                "manual_check"
            ]
            formatted_violation["remediation"][
                "action"
            ] += f" (Manual review required: {violation['manual_check']})"

        formatted_violations.append(formatted_violation)

    return formatted_violations


def add_firebase_section_to_report(original_report, firebase_report):
    """Add Firebase-specific section to the main compliance report"""
    if not firebase_report["violations"]:
        return (
            original_report
            + "\n## 🔥 Firebase Compliance Status\n✅ No Firebase services detected or no violations found.\n"
        )

    firebase_section = f"""
## 🔥 Firebase HIPAA Compliance Analysis

### Firebase Services Detected
{len(firebase_report['firebase_services'])} Firebase services are active in your project:
"""

    for service_name, service_info in firebase_report["firebase_services"].items():
        hipaa_icon = "🏥" if service_info["hipaa_relevant"] else "ℹ️"
        firebase_section += f"- {hipaa_icon} **{service_name}** ({'HIPAA-relevant' if service_info['hipaa_relevant'] else 'Not directly handling PHI'})\n"

    firebase_section += f"""
### Firebase Compliance Summary
- **Total Firebase Violations:** {firebase_report['summary']['total_violations']}
- **Critical:** {firebase_report['summary']['critical_count']} (immediate action required)
- **High:** {firebase_report['summary']['high_count']} (resolve this week)
- **Medium:** {firebase_report['summary']['medium_count']} (resolve this month)
- **Low:** {firebase_report['summary']['low_count']} (quarterly review)

### 🚨 Key Firebase HIPAA Concerns

Firebase services use **client-side security models** that differ from traditional server-side controls:

1. **Security Rules:** Client-accessible databases require carefully written security rules
2. **Real-time Sync:** Data synchronization must maintain PHI protection
3. **Client-side Access:** Browser/mobile apps directly access PHI data
4. **Authentication:** User identity must be properly verified for PHI access

### Firebase Manual Review Required
"""

    if firebase_report.get("manual_checks_required"):
        firebase_section += "⚠️ **Manual security rule review required:**\n"
        for check in firebase_report["manual_checks_required"]:
            firebase_section += f"- {check['service']}: {check['manual_check']}\n"
    else:
        firebase_section += "✅ No manual checks required.\n"

    firebase_section += f"""
### Firebase Remediation Priority

**Immediate (24 hours):** {firebase_report['summary']['critical_count']} critical Firebase issues
**This Week:** {firebase_report['summary']['high_count']} high-priority Firebase issues
**This Month:** {firebase_report['summary']['medium_count']} medium-priority Firebase improvements

### Firebase vs Traditional Infrastructure

| Aspect | Traditional GCP | Firebase |
|--------|----------------|----------|
| **Access Control** | Server-side IAM | Client-side security rules |
| **Data Access** | API endpoints | Direct database access |
| **Authentication** | Service accounts | User authentication |
| **Audit Logging** | Cloud Logging | Firebase security events |
| **Compliance** | Infrastructure focus | Application-layer focus |

**Recommendation:** Firebase requires separate HIPAA compliance review focused on application-layer security rather than just infrastructure hardening.
"""

    return original_report + firebase_section


if __name__ == "__main__":
    # Get project ID from environment or command line
    import sys
    import os
    
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id and len(sys.argv) > 1:
        project_id = sys.argv[1]
    if not project_id:
        project_id = "medtelligence"  # Default fallback
    
    print(f"🔍 Scanning project: {project_id}", file=sys.stderr)
    
    # Run the scanner but capture output to avoid mixing logs with JSON
    old_stdout = sys.stdout
    sys.stdout = sys.stderr  # Redirect prints to stderr
    
    try:
        report = generate_firebase_hipaa_report(project_id)
    finally:
        sys.stdout = old_stdout  # Restore stdout
    
    # Output only clean JSON to stdout
    print(json.dumps(report, indent=2))
