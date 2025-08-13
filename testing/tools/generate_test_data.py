#!/usr/bin/env python3
"""
Test Data Generator - Create sample data for testing
"""
import json
import random
import uuid
from datetime import datetime, timedelta


def generate_service_account(project_id=None, email_domain=None):
    """Generate a realistic test service account structure"""
    if not project_id:
        project_id = f"test-project-{random.randint(100, 999)}"

    if not email_domain:
        email_domain = f"{project_id}.iam.gserviceaccount.com"

    sa_name = f"test-sa-{random.randint(1000, 9999)}"

    return {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": f"test-key-{uuid.uuid4().hex[:10]}",
        "private_key": f"-----BEGIN PRIVATE KEY-----\nTEST-PRIVATE-KEY-CONTENT-{uuid.uuid4().hex}\n-----END PRIVATE KEY-----\n",
        "client_email": f"{sa_name}@{email_domain}",
        "client_id": f"{random.randint(100000000000000000000, 999999999999999999999)}",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{sa_name}%40{project_id}.iam.gserviceaccount.com",
    }


def generate_user_data():
    """Generate realistic test user data"""
    first_names = ["Alice", "Bob", "Carol", "David", "Eva", "Frank", "Grace", "Henry"]
    last_names = [
        "Johnson",
        "Smith",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
    ]
    companies = [
        "Acme Corp",
        "Tech Solutions",
        "Data Systems",
        "Cloud Innovations",
        "Security First",
    ]

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(['company.com', 'test.org', 'example.net'])}"

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": "testpass123",
        "company": random.choice(companies),
    }


def generate_compliance_violations():
    """Generate sample compliance violations for testing"""
    violation_types = [
        "encryption_at_rest_disabled",
        "public_bucket_access",
        "weak_iam_policies",
        "unencrypted_database",
        "missing_audit_logs",
        "insecure_network_config",
    ]

    severity_levels = ["high", "medium", "low"]

    violations = []
    for _ in range(random.randint(3, 8)):
        violations.append(
            {
                "id": str(uuid.uuid4()),
                "type": random.choice(violation_types),
                "severity": random.choice(severity_levels),
                "resource": f"projects/test-project/resources/{uuid.uuid4().hex[:8]}",
                "description": f"Test violation for {random.choice(violation_types)}",
                "detected_at": (
                    datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                ).isoformat(),
                "status": random.choice(["open", "resolved", "acknowledged"]),
            }
        )

    return violations


def generate_test_scenarios():
    """Generate complete test scenarios"""
    scenarios = []

    # Scenario 1: New user with single project
    user1 = generate_user_data()
    sa1 = generate_service_account("healthcare-prod-001")
    scenarios.append(
        {
            "name": "New User - Single Project",
            "user": user1,
            "gcp_projects": [
                {
                    "project_id": sa1["project_id"],
                    "service_account": sa1,
                    "violations": generate_compliance_violations(),
                }
            ],
        }
    )

    # Scenario 2: Existing user with multiple projects
    user2 = generate_user_data()
    projects = []
    for i in range(3):
        sa = generate_service_account(f"multi-env-{i+1:03d}")
        projects.append(
            {
                "project_id": sa["project_id"],
                "service_account": sa,
                "violations": generate_compliance_violations(),
            }
        )

    scenarios.append(
        {"name": "Multi-Project User", "user": user2, "gcp_projects": projects}
    )

    # Scenario 3: Edge case - Empty project
    user3 = generate_user_data()
    scenarios.append(
        {"name": "Edge Case - No Projects", "user": user3, "gcp_projects": []}
    )

    return scenarios


def save_test_data(filename="test_data.json"):
    """Generate and save test data to file"""
    test_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "scenarios": generate_test_scenarios(),
        "sample_service_accounts": [generate_service_account() for _ in range(5)],
        "sample_users": [generate_user_data() for _ in range(10)],
        "sample_violations": generate_compliance_violations(),
    }

    with open(filename, "w") as f:
        json.dump(test_data, f, indent=2)

    return test_data


def main():
    """Generate test data"""
    print("🔧 Generating Test Data")
    print("=" * 25)

    # Generate test data
    data = save_test_data()

    print(f"✅ Generated test data:")
    print(f"   Scenarios: {len(data['scenarios'])}")
    print(f"   Service Accounts: {len(data['sample_service_accounts'])}")
    print(f"   Users: {len(data['sample_users'])}")
    print(f"   Violations: {len(data['sample_violations'])}")
    print(f"   Saved to: test_data.json")

    # Show sample data
    print(f"\n📋 Sample Service Account:")
    sample_sa = data["sample_service_accounts"][0]
    print(f"   Project: {sample_sa['project_id']}")
    print(f"   Email: {sample_sa['client_email']}")

    print(f"\n👤 Sample User:")
    sample_user = data["sample_users"][0]
    print(f"   Name: {sample_user['first_name']} {sample_user['last_name']}")
    print(f"   Email: {sample_user['email']}")
    print(f"   Company: {sample_user['company']}")

    print(f"\n🚨 Sample Violation:")
    sample_violation = data["sample_violations"][0]
    print(f"   Type: {sample_violation['type']}")
    print(f"   Severity: {sample_violation['severity']}")
    print(f"   Resource: {sample_violation['resource']}")


if __name__ == "__main__":
    main()
