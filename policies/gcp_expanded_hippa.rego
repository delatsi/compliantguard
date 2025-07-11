# policies/gcp_expanded_hipaa.rego
package gcp.expanded_hipaa

import rego.v1

# CRITICAL: Check for non-HIPAA eligible services
violations contains msg if {
    asset := input[_]
    
    # Services that are explicitly NOT HIPAA eligible and problematic for PHI
    non_hipaa_services := {
        "firebase.googleapis.com/DatabaseInstance",  # Realtime Database
        "crashlytics.googleapis.com/Application",
        "analytics.googleapis.com/Application", 
        "firebase.googleapis.com/WebApp",
        "firebase.googleapis.com/AndroidApp",
        "firebase.googleapis.com/IosApp",
        "cloudtrace.googleapis.com/Trace",
        "clouddebugger.googleapis.com/Debuggee",
        "cloudprofiler.googleapis.com/Profile",
        "firebase.googleapis.com/RemoteConfig",
        "firebase.googleapis.com/DynamicLinks",
        "firebase.googleapis.com/Hosting",
        "firebase.googleapis.com/TestLab"
    }
    
    asset_type := asset.assetType
    
    # Check if service is explicitly non-HIPAA eligible
    non_hipaa_services[asset_type]
    
    msg := sprintf("CRITICAL HIPAA Violation - Service '%s' (%s) is NOT HIPAA eligible and cannot be used with PHI data", [asset.name, asset_type])
}

violations contains msg if {
    asset := input[_]
    
    # Focus only on high-risk unknown services (not infrastructure)
    hipaa_eligible_services := {
        "aiplatform.googleapis.com/Dataset",
        "aiplatform.googleapis.com/Endpoint", 
        "aiplatform.googleapis.com/Model",
        "aiplatform.googleapis.com/MetadataStore",  # Added this
        "bigquery.googleapis.com/Dataset",
        "bigquery.googleapis.com/Table",
        "bigtable.googleapis.com/Cluster",
        "bigtable.googleapis.com/Instance",
        "cloudfunctions.googleapis.com/CloudFunction",
        "cloudkms.googleapis.com/CryptoKey",
        "cloudkms.googleapis.com/KeyRing",
        "cloudsql.googleapis.com/Instance",
        "sqladmin.googleapis.com/Instance",
        "compute.googleapis.com/Instance",
        "compute.googleapis.com/Disk",
        "compute.googleapis.com/Firewall",
        "compute.googleapis.com/ForwardingRule",
        "compute.googleapis.com/UrlMap",
        "container.googleapis.com/Cluster",
        "container.googleapis.com/NodePool",
        "dataflow.googleapis.com/Job",
        "dataproc.googleapis.com/Cluster",
        "firestore.googleapis.com/Database",
        "healthcare.googleapis.com/Dataset",
        "healthcare.googleapis.com/FhirStore",
        "healthcare.googleapis.com/Hl7V2Store",
        "healthcare.googleapis.com/DicomStore",
        "iam.googleapis.com/ServiceAccount",
        "logging.googleapis.com/LogSink",
        "monitoring.googleapis.com/AlertPolicy",
        "pubsub.googleapis.com/Topic",
        "pubsub.googleapis.com/Subscription",
        "run.googleapis.com/Service",
        "secretmanager.googleapis.com/Secret",
        "storage.googleapis.com/Bucket",
        "cloudresourcemanager.googleapis.com/Project"
    }
    
    non_hipaa_services := {
        "firebase.googleapis.com/DatabaseInstance",
        "crashlytics.googleapis.com/Application",
        "analytics.googleapis.com/Application", 
        "firebase.googleapis.com/WebApp",
        "firebase.googleapis.com/AndroidApp",
        "firebase.googleapis.com/IosApp",
        "cloudtrace.googleapis.com/Trace",
        "clouddebugger.googleapis.com/Debuggee",
        "cloudprofiler.googleapis.com/Profile",
        "firebase.googleapis.com/RemoteConfig",
        "firebase.googleapis.com/DynamicLinks",
        "firebase.googleapis.com/Hosting",
        "firebase.googleapis.com/TestLab"
    }
    
    # Safe infrastructure services that we shouldn't warn about
    safe_infrastructure_services := {
        "compute.googleapis.com/Network",
        "compute.googleapis.com/Subnetwork", 
        "compute.googleapis.com/Route",
        "compute.googleapis.com/Snapshot",
        "compute.googleapis.com/Address",
        "compute.googleapis.com/InstanceTemplate",
        "compute.googleapis.com/ResourcePolicy",
        "compute.googleapis.com/InstanceSettings",
        "compute.googleapis.com/Project",
        "compute.googleapis.com/FirewallPolicy",
        "artifactregistry.googleapis.com/Repository",
        "artifactregistry.googleapis.com/DockerImage",
        "cloudbuild.googleapis.com/Build",
        "cloudbilling.googleapis.com/ProjectBillingInfo",
        "apikeys.googleapis.com/Key",
        "dns.googleapis.com/ManagedZone",
        "servicenetworking.googleapis.com/Connection",
        "deploymentmanager.googleapis.com/Deployment"
    }
    
    # Kubernetes resources are generally safe infrastructure
    k8s_resources := {
        "k8s.io/Namespace",
        "k8s.io/Pod", 
        "k8s.io/Service",
        "k8s.io/ServiceAccount",
        "k8s.io/Endpoints",
        "k8s.io/Secret",
        "k8s.io/ResourceQuota",
        "apps.k8s.io/Deployment",
        "apps.k8s.io/ReplicaSet",
        "apps.k8s.io/StatefulSet",
        "apps.k8s.io/DaemonSet",
        "rbac.authorization.k8s.io/Role",
        "rbac.authorization.k8s.io/RoleBinding",
        "autoscaling.k8s.io/HorizontalPodAutoscaler",
        "admissionregistration.k8s.io/MutatingWebhookConfiguration",
        "admissionregistration.k8s.io/ValidatingWebhookConfiguration"
    }
    
    asset_type := asset.assetType
    
    # Only flag services that are genuinely concerning
    not hipaa_eligible_services[asset_type]
    not non_hipaa_services[asset_type]
    not safe_infrastructure_services[asset_type]
    not k8s_resources[asset_type]
    
    # Focus on services that might actually process data
    data_processing_indicators := {
        "ml", "ai", "data", "analytics", "processing", "api", "function", "app"
    }
    
    # Check if service name suggests data processing
    some indicator
    data_processing_indicators[indicator]
    contains(lower(asset_type), indicator)
    
    msg := sprintf("HIPAA Review Required - Service '%s' (%s) is not on the official HIPAA-eligible list and may process data. Verify HIPAA compliance before using with PHI", [asset.name, asset_type])
}

# CRITICAL: Firebase Realtime Database is NOT HIPAA compliant
violations contains msg if {
    asset := input[_]
    asset.assetType == "firebase.googleapis.com/DatabaseInstance"
    
    # Realtime Database is not covered by BAA
    not contains(asset.resource.data.databaseUrl, "firestore")
    
    msg := sprintf("CRITICAL HIPAA Violation - Firebase Realtime Database '%s' is NOT HIPAA compliant (Use Firestore instead)", [asset.resource.data.databaseUrl])
}

# Firebase Analytics and Crashlytics violations
violations contains msg if {
    asset := input[_]
    startswith(asset.assetType, "firebase.googleapis.com")
    contains(asset.assetType, "Analytics")
    
    msg := sprintf("CRITICAL HIPAA Violation - Firebase Analytics service '%s' is NOT HIPAA compliant and cannot process PHI", [asset.assetType])
}

violations contains msg if {
    asset := input[_]
    startswith(asset.assetType, "firebase.googleapis.com")
    contains(asset.assetType, "Crashlytics")
    
    msg := sprintf("CRITICAL HIPAA Violation - Firebase Crashlytics service '%s' is NOT HIPAA compliant and cannot process PHI", [asset.assetType])
}

# Firestore compliance checks (this IS HIPAA eligible)
violations contains msg if {
    asset := input[_]
    asset.assetType == "firestore.googleapis.com/Database"
    
    # Check for proper backup configuration
    not asset.resource.data.pointInTimeRecoveryEnablement == "POINT_IN_TIME_RECOVERY_ENABLED"
    
    msg := sprintf("HIPAA Violation - Firestore database '%s' should have point-in-time recovery enabled (Security Rule - Data Backup)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "firestore.googleapis.com/Database"
    
    # Check for proper region (should be in US for PHI)
    location := asset.resource.data.locationId
    not startswith(location, "us-")
    
    msg := sprintf("HIPAA Violation - Firestore database '%s' in region '%s' should be in US region for PHI data (Physical Safeguards)", [asset.resource.data.name, location])
}

# Cloud Run HIPAA violations
violations contains msg if {
    asset := input[_]
    asset.assetType == "run.googleapis.com/Service"
    
    # Check for HTTPS enforcement
    traffic := asset.resource.data.spec.traffic[_]
    not traffic.percent == 100
    
    msg := sprintf("HIPAA Violation - Cloud Run service '%s' must route 100%% traffic to latest revision for consistent security (Technical Safeguards)", [asset.resource.data.metadata.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "run.googleapis.com/Service"
    
    # Check for proper authentication
    spec := asset.resource.data.spec.template.metadata
    not spec.annotations["run.googleapis.com/ingress"] == "all"
    
    # Should require authentication for PHI processing services
    annotations := spec.annotations
    annotations["run.googleapis.com/ingress"] == "all"
    not annotations["run.googleapis.com/invoker"]
    
    msg := sprintf("HIPAA Violation - Cloud Run service '%s' allows unauthenticated access but may process PHI (Access Control)", [asset.resource.data.metadata.name])
}

# Check for environment variables with secrets
violations contains msg if {
    asset := input[_]
    asset.assetType == "run.googleapis.com/Service"
    
    containers := asset.resource.data.spec.template.spec.containers[_]
    env_vars := containers.env[_]
    
    # Check for hardcoded secrets (bad practice)
    contains(lower(env_vars.name), "password")
    
    # Should use Secret Manager, not hardcoded values
    not env_vars.valueFrom.secretKeyRef
    
    msg := sprintf("HIPAA Violation - Cloud Run service '%s' has hardcoded password in environment variables (Technical Safeguards - Secret Management)", [asset.resource.data.metadata.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "run.googleapis.com/Service"
    
    containers := asset.resource.data.spec.template.spec.containers[_]
    env_vars := containers.env[_]
    
    # Check for hardcoded secrets (bad practice)
    contains(lower(env_vars.name), "secret")
    
    # Should use Secret Manager, not hardcoded values
    not env_vars.valueFrom.secretKeyRef
    
    msg := sprintf("HIPAA Violation - Cloud Run service '%s' has hardcoded secret in environment variables (Technical Safeguards - Secret Management)", [asset.resource.data.metadata.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "run.googleapis.com/Service"
    
    containers := asset.resource.data.spec.template.spec.containers[_]
    env_vars := containers.env[_]
    
    # Check for hardcoded secrets (bad practice)
    contains(lower(env_vars.name), "key")
    
    # Should use Secret Manager, not hardcoded values
    not env_vars.valueFrom.secretKeyRef
    
    msg := sprintf("HIPAA Violation - Cloud Run service '%s' has hardcoded key in environment variables (Technical Safeguards - Secret Management)", [asset.resource.data.metadata.name])
}

# Google Kubernetes Engine (GKE) HIPAA violations
violations contains msg if {
    asset := input[_]
    asset.assetType == "container.googleapis.com/Cluster"
    
    # Check for private cluster configuration
    not asset.resource.data.privateClusterConfig.enablePrivateNodes
    
    msg := sprintf("HIPAA Violation - GKE cluster '%s' should use private nodes for PHI workloads (Physical Safeguards)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "container.googleapis.com/Cluster"
    
    # Check for network policy enforcement
    not asset.resource.data.networkPolicy.enabled
    
    msg := sprintf("HIPAA Violation - GKE cluster '%s' should enable network policies for micro-segmentation (Technical Safeguards - Access Control)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "container.googleapis.com/Cluster"
    
    # Check for audit logging
    not asset.resource.data.loggingConfig.enableComponents
    
    msg := sprintf("HIPAA Violation - GKE cluster '%s' should enable audit logging (Technical Safeguards - Audit Controls)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "container.googleapis.com/Cluster"
    
    # Check for workload identity (secure way to access other GCP services)
    not asset.resource.data.workloadIdentityConfig.workloadPool
    
    msg := sprintf("HIPAA Violation - GKE cluster '%s' should enable Workload Identity for secure service authentication (Technical Safeguards - Authentication)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "container.googleapis.com/Cluster"
    
    # Check for binary authorization (ensures only trusted container images)
    not asset.resource.data.binaryAuthorization.enabled
    
    msg := sprintf("HIPAA Violation - GKE cluster '%s' should enable Binary Authorization to prevent unauthorized container images (Technical Safeguards - Integrity)", [asset.resource.data.name])
}

# Cloud Functions violations (Cloud Functions IS HIPAA eligible)
violations contains msg if {
    asset := input[_]
    asset.assetType == "cloudfunctions.googleapis.com/CloudFunction"
    
    # Check for VPC connector (should not be public)
    not asset.resource.data.vpcConnector
    
    msg := sprintf("HIPAA Violation - Cloud Function '%s' should use VPC connector for private networking when processing PHI (Technical Safeguards - Network Security)", [asset.resource.data.name])
}

# Check for environment variables with secrets
violations contains msg if {
    asset := input[_]
    asset.assetType == "cloudfunctions.googleapis.com/CloudFunction"
    
    env_vars := asset.resource.data.environmentVariables
    
    # Look for suspicious environment variable names - password
    some key
    env_vars[key]
    contains(lower(key), "password")
    
    msg := sprintf("HIPAA Violation - Cloud Function '%s' may have password in environment variables, use Secret Manager instead (Technical Safeguards - Secret Management)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "cloudfunctions.googleapis.com/CloudFunction"
    
    env_vars := asset.resource.data.environmentVariables
    
    # Look for suspicious environment variable names - secret
    some key
    env_vars[key]
    contains(lower(key), "secret")
    
    msg := sprintf("HIPAA Violation - Cloud Function '%s' may have secret in environment variables, use Secret Manager instead (Technical Safeguards - Secret Management)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "cloudfunctions.googleapis.com/CloudFunction"
    
    env_vars := asset.resource.data.environmentVariables
    
    # Look for suspicious environment variable names - api_key
    some key
    env_vars[key]
    contains(lower(key), "api_key")
    
    msg := sprintf("HIPAA Violation - Cloud Function '%s' may have API key in environment variables, use Secret Manager instead (Technical Safeguards - Secret Management)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "cloudfunctions.googleapis.com/CloudFunction"
    
    # Check for proper region
    location := asset.resource.location
    not startswith(location, "us-")
    
    msg := sprintf("HIPAA Violation - Cloud Function '%s' in region '%s' should be in US region for PHI processing (Physical Safeguards)", [asset.resource.data.name, location])
}

# Cloud KMS violations (Key Management Service)
violations contains msg if {
    asset := input[_]
    asset.assetType == "cloudkms.googleapis.com/CryptoKey"
    
    # Check for key rotation
    not asset.resource.data.rotationPeriod
    
    msg := sprintf("HIPAA Violation - KMS key '%s' should have automatic rotation enabled (Technical Safeguards - Encryption Key Management)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "cloudkms.googleapis.com/KeyRing"
    
    # Check for location (should be in US for PHI)
    location := asset.resource.location
    not startswith(location, "us-")
    
    msg := sprintf("HIPAA Violation - KMS KeyRing '%s' in location '%s' should be in US region for PHI encryption keys (Physical Safeguards)", [asset.resource.data.name, location])
}

# Pub/Sub violations
violations contains msg if {
    asset := input[_]
    asset.assetType == "pubsub.googleapis.com/Topic"
    
    # Check for encryption with customer-managed keys
    not asset.resource.data.kmsKeyName
    
    msg := sprintf("HIPAA Violation - Pub/Sub topic '%s' should use customer-managed encryption keys for PHI data (Technical Safeguards - Encryption)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "pubsub.googleapis.com/Subscription"
    
    # Check for dead letter policy (important for PHI message handling)
    not asset.resource.data.deadLetterPolicy
    
    msg := sprintf("HIPAA Violation - Pub/Sub subscription '%s' should have dead letter policy for reliable PHI message processing (Technical Safeguards - Data Integrity)", [asset.resource.data.name])
}

# Identity and Access Management (IAM) deeper checks
violations contains msg if {
    asset := input[_]
    asset.assetType == "iam.googleapis.com/ServiceAccount"
    
    # Check for overly broad roles - editor
    email := asset.resource.data.email
    contains(email, "editor")
    
    msg := sprintf("HIPAA Violation - Service account '%s' name suggests editor permissions, use principle of least privilege (Administrative Safeguards - Access Management)", [email])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "iam.googleapis.com/ServiceAccount"
    
    # Check for overly broad roles - owner
    email := asset.resource.data.email
    contains(email, "owner")
    
    msg := sprintf("HIPAA Violation - Service account '%s' name suggests owner permissions, use principle of least privilege (Administrative Safeguards - Access Management)", [email])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "iam.googleapis.com/ServiceAccount"
    
    # Check for overly broad roles - admin
    email := asset.resource.data.email
    contains(email, "admin")
    
    msg := sprintf("HIPAA Violation - Service account '%s' name suggests admin permissions, use principle of least privilege (Administrative Safeguards - Access Management)", [email])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "cloudresourcemanager.googleapis.com/Project"
    
    # Check for project-level IAM policies (this is a simplified check)
    # In practice, you'd need the IAM policy data
    project_id := asset.resource.data.projectId
    
    msg := sprintf("HIPAA Review Required - Project '%s' IAM policies should be audited for least privilege access to PHI resources (Administrative Safeguards)", [project_id])
}

# App Engine violations (if used)
violations contains msg if {
    asset := input[_]
    asset.assetType == "appengine.googleapis.com/Application"
    
    # Check for location
    location := asset.resource.data.locationId
    not startswith(location, "us-")
    
    msg := sprintf("HIPAA Violation - App Engine application '%s' in region '%s' should be in US region for PHI processing (Physical Safeguards)", [asset.resource.data.id, location])
}

# Secret Manager violations
violations contains msg if {
    asset := input[_]
    asset.assetType == "secretmanager.googleapis.com/Secret"
    
    # Check for automatic replication (should use customer-managed locations for PHI)
    replication := asset.resource.data.replication
    replication.automatic
    
    msg := sprintf("HIPAA Violation - Secret '%s' uses automatic replication, should use user-managed locations in US for PHI-related secrets (Physical Safeguards)", [asset.resource.data.name])
}

# Load Balancer violations
violations contains msg if {
    asset := input[_]
    asset.assetType == "compute.googleapis.com/UrlMap"
    
    # Check for HTTPS redirect
    default_service := asset.resource.data.defaultService
    not contains(default_service, "https")
    
    msg := sprintf("HIPAA Violation - Load balancer '%s' should enforce HTTPS for PHI data transmission (Technical Safeguards - Transmission Security)", [asset.resource.data.name])
}

# Cloud SQL enhanced checks
violations contains msg if {
    asset := input[_]
    asset.assetType == "sqladmin.googleapis.com/Instance"
    
    # Check for automated backups
    settings := asset.resource.data.settings
    not settings.backupConfiguration.enabled
    
    msg := sprintf("HIPAA Violation - Cloud SQL instance '%s' should have automated backups enabled (Security Rule - Data Backup)", [asset.resource.data.name])
}

violations contains msg if {
    asset := input[_]
    asset.assetType == "sqladmin.googleapis.com/Instance"
    
    # Check for deletion protection
    settings := asset.resource.data.settings
    not settings.deletionProtectionEnabled
    
    msg := sprintf("HIPAA Violation - Cloud SQL instance '%s' should have deletion protection enabled for PHI data (Security Rule - Data Integrity)", [asset.resource.data.name])
}
