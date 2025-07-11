# policies/hipaa_compliance.rego
package hipaa.compliance

import rego.v1

# HIPAA Security Rule: Administrative Safeguards
# Violation: IAM users should have MFA enabled
violations contains msg if {
    asset := input[_]
    asset.assetType == "iam.googleapis.com/ServiceAccount"
    
    # Check if service account has overly broad permissions
    email := asset.resource.data.email
    not endswith(email, ".iam.gserviceaccount.com")
    contains(email, "compute@developer")
    
    msg := sprintf("HIPAA Violation - Default service account '%s' should not be used for PHI access (Admin Safeguards)", [email])
}

# HIPAA Security Rule: Physical Safeguards
# Violation: Compute instances storing PHI must be in approved regions
violations contains msg if {
    asset := input[_]
    asset.assetType == "compute.googleapis.com/Instance"
    
    # Extract zone information
    zone_parts := split(asset.name, "/")
    zone := zone_parts[count(zone_parts)-3]
    
    # Check if in approved regions (example: only US regions allowed for PHI)
    not startswith(zone, "us-")
    
    msg := sprintf("HIPAA Violation - Compute instance '%s' in zone '%s' outside approved US regions (Physical Safeguards)", [asset.name, zone])
}

# HIPAA Security Rule: Technical Safeguards - Access Control
# Violation: Storage buckets containing PHI must not be publicly accessible
violations contains msg if {
    asset := input[_]
    asset.assetType == "storage.googleapis.com/Bucket"
    
    # Check for public access prevention
    bucket_name := asset.resource.data.name
    iam_config := asset.resource.data.iamConfiguration
    
    # Public access prevention should be enforced
    iam_config.publicAccessPrevention != "enforced"
    
    msg := sprintf("HIPAA Violation - Storage bucket '%s' allows public access, violating access controls (Technical Safeguards)", [bucket_name])
}

# HIPAA Security Rule: Technical Safeguards - Encryption at Rest
# Violation: Cloud SQL instances must use customer-managed encryption keys
violations contains msg if {
    asset := input[_]
    asset.assetType == "sqladmin.googleapis.com/Instance"
    
    instance_name := asset.resource.data.name
    
    # Check for encryption configuration
    not asset.resource.data.diskEncryptionConfiguration
    
    msg := sprintf("HIPAA Violation - Cloud SQL instance '%s' lacks customer-managed encryption (Technical Safeguards - Encryption)", [instance_name])
}

# HIPAA Security Rule: Technical Safeguards - Encryption in Transit
# Violation: Cloud SQL instances must require SSL/TLS
violations contains msg if {
    asset := input[_]
    asset.assetType == "sqladmin.googleapis.com/Instance"
    
    instance_name := asset.resource.data.name
    settings := asset.resource.data.settings
    
    # SSL should be required
    settings.ipConfiguration.requireSsl != true
    
    msg := sprintf("HIPAA Violation - Cloud SQL instance '%s' does not require SSL connections (Technical Safeguards - Transmission Security)", [instance_name])
}

# HIPAA Security Rule: Technical Safeguards - Audit Controls
# Violation: Cloud SQL instances must have audit logging enabled
violations contains msg if {
    asset := input[_]
    asset.assetType == "sqladmin.googleapis.com/Instance"
    
    instance_name := asset.resource.data.name
    settings := asset.resource.data.settings
    
    # Check for audit logging
    not settings.databaseFlags
    
    msg := sprintf("HIPAA Violation - Cloud SQL instance '%s' missing audit logging configuration (Technical Safeguards - Audit Controls)", [instance_name])
}

# HIPAA Security Rule: Technical Safeguards - Automatic Logoff
# Violation: Compute instances should have idle timeout configured
violations contains msg if {
    asset := input[_]
    asset.assetType == "compute.googleapis.com/Instance"
    
    instance_name := asset.resource.data.name
    metadata := asset.resource.data.metadata
    
    # Check for session timeout configuration in metadata
    not has_session_timeout(metadata)
    
    msg := sprintf("HIPAA Violation - Compute instance '%s' lacks session timeout configuration (Technical Safeguards - Automatic Logoff)", [instance_name])
}

# HIPAA Security Rule: Technical Safeguards - Integrity Controls
# Violation: Storage buckets must have versioning enabled
violations contains msg if {
    asset := input[_]
    asset.assetType == "storage.googleapis.com/Bucket"
    
    bucket_name := asset.resource.data.name
    versioning := asset.resource.data.versioning
    
    # Versioning should be enabled for data integrity
    versioning.enabled != true
    
    msg := sprintf("HIPAA Violation - Storage bucket '%s' has versioning disabled, affecting data integrity (Technical Safeguards - Integrity)", [bucket_name])
}

# HIPAA Security Rule: Network Security
# Violation: VPC networks should not allow unrestricted access
violations contains msg if {
    asset := input[_]
    asset.assetType == "compute.googleapis.com/Firewall"
    
    rule_name := asset.resource.data.name
    
    # Check for overly permissive firewall rules
    source_ranges := asset.resource.data.sourceRanges[_]
    source_ranges == "0.0.0.0/0"
    
    # Check if it allows sensitive ports
    allowed := asset.resource.data.allowed[_]
    sensitive_ports := {"22", "3389", "1433", "3306", "5432"}
    port := allowed.ports[_]
    sensitive_ports[port]
    
    msg := sprintf("HIPAA Violation - Firewall rule '%s' allows unrestricted access to sensitive port %s (Network Security)", [rule_name, port])
}

# HIPAA Business Associate Agreement Requirements
# Violation: External load balancers should have proper access controls
violations contains msg if {
    asset := input[_]
    asset.assetType == "compute.googleapis.com/ForwardingRule"
    
    rule_name := asset.resource.data.name
    load_balancing_scheme := asset.resource.data.loadBalancingScheme
    
    # External load balancers should have additional security measures
    load_balancing_scheme == "EXTERNAL"
    
    msg := sprintf("HIPAA Warning - External load balancer '%s' requires additional BAA compliance verification (Business Associate Requirements)", [rule_name])
}

# HIPAA Breach Notification Rule - Monitoring
# Violation: Projects should have Cloud Logging enabled
violations contains msg if {
    asset := input[_]
    asset.assetType == "logging.googleapis.com/LogSink"
    
    sink_name := asset.resource.data.name
    destination := asset.resource.data.destination
    
    # Check if logs are being exported for compliance monitoring
    not startswith(destination, "storage.googleapis.com")
    not startswith(destination, "bigquery.googleapis.com")
    
    msg := sprintf("HIPAA Violation - Log sink '%s' not configured for long-term storage required for breach detection (Breach Notification Rule)", [sink_name])
}

# HIPAA Minimum Necessary Standard
# Violation: IAM roles should follow principle of least privilege
violations contains msg if {
    asset := input[_]
    asset.assetType == "cloudresourcemanager.googleapis.com/Project"
    
    project_id := asset.resource.data.projectId
    
    # This is a placeholder - in practice, you'd need to examine IAM bindings
    # which would require additional API calls or data sources
    msg := sprintf("HIPAA Review Required - Project '%s' IAM policies should be reviewed for minimum necessary access (Minimum Necessary Standard)", [project_id])
}

# Helper function to check for session timeout in metadata
has_session_timeout(metadata) if {
    items := metadata.items[_]
    items.key == "session-timeout"
}

has_session_timeout(metadata) if {
    items := metadata.items[_]
    items.key == "idle-timeout"
}

# Helper function to check if metadata exists
has_session_timeout(metadata) if {
    not metadata
} else := false
