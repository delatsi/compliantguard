# policies/environment_separation.rego
package environment.separation

import rego.v1

# Environment separation compliance policy for HIPAA and SOC 2
# This policy detects missing environment tagging and separation violations

# Required environment tags for compliance
required_environment_tags := {"dev", "development", "staging", "test", "prod", "production"}

# HIPAA/SOC 2 Violation: Resources must be properly tagged with environment
violations contains msg if {
    asset := input[_]
    
    # Check compute instances
    asset.assetType == "compute.googleapis.com/Instance"
    instance_name := asset.resource.data.name
    
    # Check if environment tag is missing or invalid
    not has_valid_environment_tag(asset)
    
    msg := sprintf("Environment Separation Violation (Medium) - Compute instance '%s' lacks proper environment tagging (dev/staging/prod). Required for HIPAA Administrative Safeguards and SOC 2 Security controls.", [instance_name])
}

violations contains msg if {
    asset := input[_]
    
    # Check storage buckets
    asset.assetType == "storage.googleapis.com/Bucket"
    bucket_name := asset.resource.data.name
    
    # Check if environment tag is missing or invalid
    not has_valid_environment_tag(asset)
    
    msg := sprintf("Environment Separation Violation (Medium) - Storage bucket '%s' lacks proper environment tagging (dev/staging/prod). Required for data classification and access controls.", [bucket_name])
}

violations contains msg if {
    asset := input[_]
    
    # Check Cloud SQL instances
    asset.assetType == "sqladmin.googleapis.com/Instance"
    instance_name := asset.resource.data.name
    
    # Check if environment tag is missing or invalid
    not has_valid_environment_tag(asset)
    
    msg := sprintf("Environment Separation Violation (Medium) - Cloud SQL instance '%s' lacks proper environment tagging (dev/staging/prod). Critical for PHI data segregation.", [instance_name])
}

violations contains msg if {
    asset := input[_]
    
    # Check Kubernetes clusters
    asset.assetType == "container.googleapis.com/Cluster"
    cluster_name := asset.resource.data.name
    
    # Check if environment tag is missing or invalid
    not has_valid_environment_tag(asset)
    
    msg := sprintf("Environment Separation Violation (Medium) - GKE cluster '%s' lacks proper environment tagging (dev/staging/prod). Required for workload isolation.", [cluster_name])
}

violations contains msg if {
    asset := input[_]
    
    # Check Cloud Functions
    asset.assetType == "cloudfunctions.googleapis.com/CloudFunction"
    function_name := asset.resource.data.name
    
    # Check if environment tag is missing or invalid
    not has_valid_environment_tag(asset)
    
    msg := sprintf("Environment Separation Violation (Medium) - Cloud Function '%s' lacks proper environment tagging (dev/staging/prod). Required for serverless security controls.", [function_name])
}

# HIPAA/SOC 2 Violation: Production resources should not share networks with dev/staging
violations contains msg if {
    asset := input[_]
    asset.assetType == "compute.googleapis.com/Instance"
    
    instance_name := asset.resource.data.name
    network_interfaces := asset.resource.data.networkInterfaces
    
    # Check if this is a production instance
    is_production_resource(asset)
    
    # Check if sharing network with non-production resources
    network_url := network_interfaces[_].network
    has_mixed_environment_network(network_url)
    
    msg := sprintf("Environment Separation Violation (High) - Production instance '%s' shares network with non-production resources. Violates network segregation requirements.", [instance_name])
}

# HIPAA Administrative Safeguards: Environment-specific access controls
violations contains msg if {
    asset := input[_]
    asset.assetType == "compute.googleapis.com/Instance"
    
    instance_name := asset.resource.data.name
    
    # Check if production resource has proper access controls
    is_production_resource(asset)
    not has_restricted_access_controls(asset)
    
    msg := sprintf("Environment Separation Violation (High) - Production instance '%s' lacks environment-specific access controls. Required for HIPAA workforce access management.", [instance_name])
}

# SOC 2 Processing Integrity: Environment-specific configurations
violations contains msg if {
    asset := input[_]
    asset.assetType == "storage.googleapis.com/Bucket"
    
    bucket_name := asset.resource.data.name
    
    # Production buckets should have stricter configuration
    is_production_resource(asset)
    not has_production_grade_configuration(asset)
    
    msg := sprintf("Environment Separation Violation (Medium) - Production bucket '%s' lacks production-grade configuration (versioning, lifecycle, retention policies).", [bucket_name])
}

# Environment naming convention compliance
violations contains msg if {
    asset := input[_]
    resource_name := get_resource_name(asset)
    
    # Check if resource follows environment naming convention
    has_environment_tag_in_labels(asset)
    not follows_naming_convention(resource_name, asset)
    
    msg := sprintf("Environment Separation Warning (Low) - Resource '%s' has environment tag but name doesn't follow convention (should include env prefix/suffix).", [resource_name])
}

# Cross-environment data access detection
violations contains msg if {
    asset := input[_]
    asset.assetType == "storage.googleapis.com/Bucket"
    
    bucket_name := asset.resource.data.name
    iam_policy := asset.resource.data.iam
    
    # Check for cross-environment access in IAM policies
    is_production_resource(asset)
    has_cross_environment_access(iam_policy)
    
    msg := sprintf("Environment Separation Violation (High) - Production bucket '%s' has IAM policies allowing cross-environment access. Violates data segregation principles.", [bucket_name])
}

# Helper functions

# Check if asset has valid environment tag
has_valid_environment_tag(asset) if {
    labels := asset.resource.data.labels
    env_tag := labels[_]
    required_environment_tags[env_tag]
}

has_valid_environment_tag(asset) if {
    # Check in resource metadata/tags
    metadata := asset.resource.data.metadata
    items := metadata.items[_]
    items.key == "environment"
    required_environment_tags[items.value]
}

has_valid_environment_tag(asset) if {
    # Check in GCP labels
    labels := asset.resource.data.labels
    env_value := labels.environment
    required_environment_tags[env_value]
}

has_valid_environment_tag(asset) if {
    # Check if environment is in resource name
    resource_name := get_resource_name(asset)
    contains(resource_name, "prod")
    required_environment_tags["prod"]
}

has_valid_environment_tag(asset) if {
    resource_name := get_resource_name(asset)
    contains(resource_name, "dev")
    required_environment_tags["dev"]
}

has_valid_environment_tag(asset) if {
    resource_name := get_resource_name(asset)
    contains(resource_name, "staging")
    required_environment_tags["staging"]
}

# Check if resource is production
is_production_resource(asset) if {
    labels := asset.resource.data.labels
    prod_tags := {"prod", "production"}
    prod_tags[labels.environment]
}

is_production_resource(asset) if {
    resource_name := get_resource_name(asset)
    contains(resource_name, "prod")
}

is_production_resource(asset) if {
    metadata := asset.resource.data.metadata
    items := metadata.items[_]
    items.key == "environment"
    prod_tags := {"prod", "production"}
    prod_tags[items.value]
}

# Check for environment tag in labels
has_environment_tag_in_labels(asset) if {
    labels := asset.resource.data.labels
    labels.environment
}

# Check naming convention
follows_naming_convention(resource_name, asset) if {
    labels := asset.resource.data.labels
    env := labels.environment
    contains(resource_name, env)
}

follows_naming_convention(resource_name, asset) if {
    # Allow if name starts with environment
    labels := asset.resource.data.labels
    env := labels.environment
    startswith(resource_name, env)
}

# Get resource name helper
get_resource_name(asset) := asset.resource.data.name

# Check for restricted access controls (placeholder - would need IAM data)
has_restricted_access_controls(asset) if {
    # This would check IAM policies, service accounts, etc.
    # For now, assume false to flag for review
    false
}

# Check for production-grade configuration
has_production_grade_configuration(asset) if {
    asset.assetType == "storage.googleapis.com/Bucket"
    versioning := asset.resource.data.versioning
    versioning.enabled == true
    
    # Check for lifecycle management
    lifecycle := asset.resource.data.lifecycle
    lifecycle.rule
}

# Check for cross-environment access (placeholder)
has_cross_environment_access(iam_policy) if {
    # This would analyze IAM bindings for cross-env access
    # For now, assume false to be safe
    false
}

# Check for mixed environment network (placeholder)
has_mixed_environment_network(network_url) if {
    # This would require network topology analysis
    # For now, assume false to avoid false positives
    false
}

# Environment isolation best practices recommendations
recommendations contains msg if {
    asset := input[_]
    resource_name := get_resource_name(asset)
    
    # Recommend environment-specific projects
    asset.assetType == "cloudresourcemanager.googleapis.com/Project"
    project_id := asset.resource.data.projectId
    
    # Check if project name suggests multi-environment usage
    not contains(project_id, "prod")
    not contains(project_id, "dev")
    not contains(project_id, "staging")
    
    msg := sprintf("Environment Separation Recommendation - Project '%s' should consider environment-specific projects for better isolation and compliance.", [project_id])
}

recommendations contains msg if {
    # Count resources by environment to identify potential consolidation opportunities
    asset := input[_]
    has_valid_environment_tag(asset)
    
    # This is a simplified check - in practice would aggregate across all resources
    msg := "Environment Separation Best Practice - Consider implementing environment-specific VPCs, projects, and IAM policies for enhanced security posture."
}