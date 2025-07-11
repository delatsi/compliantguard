# policies/themisguard_startup_framework.rego
package themisguard.startup_framework

import rego.v1

# Startup-specific risk scoring and prioritization
violations contains violation if {
    # For now, create a simple base violation structure
    # In production, this would come from your actual violation detection logic
    asset := input[_]
    
    # Calculate startup-specific risk factors
    company_stage := input.company_metadata.stage  # "pre-revenue", "early", "growth", "scale"
    team_size := input.company_metadata.team_size
    phi_volume := input.company_metadata.phi_volume  # "low", "medium", "high"
    funding_stage := input.company_metadata.funding_stage
    
    # Create a sample violation for demonstration
    base_violation := {
        "id": "sample_violation",
        "message": "Sample compliance violation detected",
        "category": "technical",
        "type": "missing_encryption",
        "base_risk_score": 7.0
    }
    
    risk_score := calculate_startup_risk_score(base_violation, company_stage, team_size, phi_volume)
    priority := determine_startup_priority(risk_score, funding_stage)
    remediation := get_startup_remediation_guidance(base_violation, company_stage)
    
    violation := {
        "id": base_violation.id,
        "message": base_violation.message,
        "category": base_violation.category,
        "risk_score": risk_score,
        "priority": priority,
        "startup_priority": get_startup_specific_priority(base_violation, company_stage),
        "remediation_effort": estimate_effort_for_startup(base_violation, team_size),
        "cost_estimate": estimate_cost_for_startup(base_violation, funding_stage),
        "compliance_impact": assess_compliance_impact(base_violation),
        "quick_wins": identify_quick_wins(base_violation),
        "remediation_guidance": remediation,
        "business_impact": assess_business_impact(base_violation, company_stage)
    }
}

# Critical violations that block customer acquisition
blocking_violations contains violation if {
    violation := violations[_]
    violation.startup_priority == "customer_blocking"
}

# Quick wins for resource-constrained startups
quick_wins contains violation if {
    violation := violations[_]
    violation.remediation_effort == "low"
    violation.compliance_impact >= "medium"
}

# Minimum Viable Compliance (MVC) framework
mvc_requirements contains requirement if {
    requirement := {
        "category": "administrative",
        "control": "privacy_officer_designation",
        "description": "Designate a privacy officer (can be founder/CTO)",
        "effort": "low",
        "cost": "$0",
        "blocking": true
    }
}

mvc_requirements contains requirement if {
    requirement := {
        "category": "technical",
        "control": "basic_encryption",
        "description": "Implement encryption at rest and in transit",
        "effort": "medium",
        "cost": "$100-500/month",
        "blocking": true
    }
}

mvc_requirements contains requirement if {
    requirement := {
        "category": "administrative",
        "control": "basic_policies",
        "description": "Implement core HIPAA policies and procedures",
        "effort": "medium",
        "cost": "$0-2000",
        "blocking": true
    }
}

# Telemedicine-specific startup violations
telemedicine_violations contains msg if {
    asset := input[_]
    asset.assetType == "communication_platform"
    
    # Check for common startup mistakes in telemedicine
    not has_baa(asset)
    asset.usage == "patient_consultation"
    
    msg := sprintf("Telemedicine Violation - Platform '%s' requires BAA for patient consultations", [asset.name])
}

telemedicine_violations contains msg if {
    asset := input[_]
    asset.assetType == "video_platform"
    
    # Check for consumer-grade platforms
    consumer_platforms := {"zoom_basic", "google_meet_free", "skype", "facetime"}
    consumer_platforms[asset.platform_type]
    asset.phi_exposure == true
    
    msg := sprintf("Telemedicine Violation - Consumer platform '%s' not suitable for PHI", [asset.platform_type])
}

# AI/ML specific violations for health tech startups
ai_ml_violations contains msg if {
    asset := input[_]
    asset.assetType == "ml_model"
    
    # Check for proper de-identification in training data
    not asset.training_data.deidentified
    asset.training_data.contains_phi == true
    
    msg := sprintf("AI/ML Violation - Model '%s' trained on non-de-identified PHI", [asset.name])
}

ai_ml_violations contains msg if {
    asset := input[_]
    asset.assetType == "ai_service"
    
    # Check for third-party AI services handling PHI
    not has_baa(asset)
    asset.processes_phi == true
    
    msg := sprintf("AI/ML Violation - Third-party AI service '%s' lacks BAA for PHI processing", [asset.name])
}

# Cloud-native startup violations
cloud_native_violations contains msg if {
    asset := input[_]
    asset.assetType == "container_image"
    
    # Check for secrets in container images
    has_embedded_secrets(asset)
    
    msg := sprintf("DevOps Violation - Container '%s' contains embedded secrets", [asset.name])
}

cloud_native_violations contains msg if {
    asset := input[_]
    asset.assetType == "api_gateway"
    
    # Check for proper authentication on APIs handling PHI
    not asset.authentication.required
    asset.handles_phi == true
    
    msg := sprintf("API Violation - Gateway '%s' lacks authentication for PHI endpoints", [asset.name])
}

# Incident response for startups
incident_response_violations contains msg if {
    org := input.organization[_]
    
    # Check for basic incident response plan
    not org.incident_response_plan
    org.handles_phi == true
    
    msg := "Incident Response Violation - No documented incident response plan for PHI breaches"
}

incident_response_violations contains msg if {
    org := input.organization[_]
    
    # Check for breach notification procedures
    not org.breach_notification_procedures
    org.handles_phi == true
    
    msg := "Incident Response Violation - No breach notification procedures documented"
}

# Business Associate Management for startups
ba_management_violations contains msg if {
    vendor := input.vendors[_]
    
    # Check for missing BAAs with critical vendors
    not has_signed_baa(vendor)
    vendor.accesses_phi == true
    vendor.criticality == "high"
    
    msg := sprintf("BA Management Violation - Critical vendor '%s' lacks signed BAA", [vendor.name])
}

ba_management_violations contains msg if {
    vendor := input.vendors[_]
    
    # Check for BAA review dates
    is_baa_expired(vendor.baa_signed_date)
    vendor.accesses_phi == true
    
    msg := sprintf("BA Management Violation - BAA with '%s' requires annual review", [vendor.name])
}

# Data minimization for startups
data_minimization_violations contains msg if {
    dataset := input.datasets[_]
    
    # Check for excessive PHI collection
    dataset.phi_fields_count > dataset.required_phi_fields_count
    
    excess_fields := dataset.phi_fields_count - dataset.required_phi_fields_count
    msg := sprintf("Data Minimization Violation - Dataset '%s' collects %d unnecessary PHI fields", [dataset.name, excess_fields])
}

# Employee training violations
training_violations contains msg if {
    employee := input.employees[_]
    
    # Check for HIPAA training completion
    not employee.hipaa_training_completed
    employee.accesses_phi == true
    
    msg := sprintf("Training Violation - Employee '%s' lacks required HIPAA training", [employee.name])
}

training_violations contains msg if {
    employee := input.employees[_]
    
    # Check for training currency (annual requirement)
    is_training_expired(employee.last_training_date)
    employee.accesses_phi == true
    
    msg := sprintf("Training Violation - Employee '%s' requires annual HIPAA training update", [employee.name])
}

# Helper functions
calculate_startup_risk_score(violation, stage, team_size, phi_volume) := score if {
    base_score := violation.base_risk_score
    
    stage_multiplier := stage_risk_multipliers[stage]
    team_multiplier := team_size_risk_multipliers[team_size]
    phi_multiplier := phi_volume_risk_multipliers[phi_volume]
    
    score := base_score * stage_multiplier * team_multiplier * phi_multiplier
}

determine_startup_priority(risk_score, funding_stage) := "critical" if {
    risk_score >= 8.0
}

determine_startup_priority(risk_score, funding_stage) := "high" if {
    risk_score >= 6.0
}

determine_startup_priority(risk_score, funding_stage) := "medium" if {
    risk_score >= 4.0
}

determine_startup_priority(risk_score, funding_stage) := "low" if {
    true
}

get_startup_specific_priority(violation, stage) := "customer_blocking" if {
    customer_blocking_violations := {
        "missing_baa_critical_vendor",
        "no_encryption_at_rest",
        "no_access_controls",
        "no_incident_response_plan"
    }
    customer_blocking_violations[violation.type]
    stage != "pre-revenue"
}

get_startup_specific_priority(violation, stage) := "fundraising_critical" if {
    fundraising_violations := {
        "inadequate_policies",
        "missing_privacy_officer",
        "no_risk_assessment",
        "incomplete_documentation"
    }
    fundraising_violations[violation.type]
    stage == "growth"
}

get_startup_specific_priority(violation, stage) := "nice_to_have" if {
    true  # default
}

estimate_effort_for_startup(violation, team_size) := "low" if {
    low_effort_fixes := {
        "designate_privacy_officer",
        "basic_policy_creation",
        "enable_logging"
    }
    low_effort_fixes[violation.type]
}

estimate_effort_for_startup(violation, team_size) := "medium" if {
    team_size >= 5
    medium_effort_fixes := {
        "implement_encryption",
        "access_control_setup",
        "training_program"
    }
    medium_effort_fixes[violation.type]
}

estimate_effort_for_startup(violation, team_size) := "high" if {
    true  # default
}

estimate_cost_for_startup(violation, funding_stage) := cost if {
    base_cost := violation_base_costs[violation.type]
    funding_multiplier := funding_cost_multipliers[funding_stage]
    cost := base_cost * funding_multiplier
}

# Missing helper functions
get_startup_remediation_guidance(violation, stage) := guidance if {
    remediation_guides := {
        "missing_encryption": "Implement AWS KMS or similar encryption service",
        "no_access_controls": "Set up IAM roles and policies",
        "missing_baa": "Contact vendor for Business Associate Agreement",
        "no_policies": "Use HIPAA policy templates and customize for your startup"
    }
    guidance := remediation_guides[violation.type]
}

get_startup_remediation_guidance(violation, stage) := "Contact HIPAA compliance consultant" if {
    true  # default
}

assess_compliance_impact(violation) := "high" if {
    high_impact_types := {
        "missing_encryption",
        "no_access_controls", 
        "missing_baa",
        "no_incident_response_plan"
    }
    high_impact_types[violation.type]
}

assess_compliance_impact(violation) := "medium" if {
    medium_impact_types := {
        "missing_policies",
        "no_training",
        "inadequate_logging"
    }
    medium_impact_types[violation.type]
}

assess_compliance_impact(violation) := "low" if {
    true  # default
}

identify_quick_wins(violation) := true if {
    quick_win_types := {
        "designate_privacy_officer",
        "enable_logging",
        "basic_policy_creation"
    }
    quick_win_types[violation.type]
}

identify_quick_wins(violation) := false if {
    true  # default
}

assess_business_impact(violation, stage) := "customer_blocking" if {
    stage != "pre-revenue"
    blocking_types := {
        "missing_encryption",
        "no_access_controls",
        "missing_baa"
    }
    blocking_types[violation.type]
}

assess_business_impact(violation, stage) := "fundraising_risk" if {
    stage == "growth"
    risk_types := {
        "inadequate_policies",
        "no_risk_assessment"
    }
    risk_types[violation.type]
}

assess_business_impact(violation, stage) := "operational" if {
    true  # default
}

# Simple date calculation function
days_between(date1, date2) := days if {
    # Simple implementation - in production you'd use proper date libraries
    # This assumes dates are in timestamp format
    diff := date2 - date1
    days := diff / 86400000000000  # nanoseconds to days
}

has_baa(asset) if {
    asset.business_associate_agreement.signed == true
    not is_baa_expired(asset.business_associate_agreement.signed_date)
}

has_signed_baa(vendor) if {
    vendor.baa_status == "signed"
    not is_baa_expired(vendor.baa_signed_date)
}

is_baa_expired(signed_date) if {
    # BAAs should be reviewed annually
    days_since_signing := days_between(signed_date, time.now_ns())
    days_since_signing > 365
}

is_training_expired(last_training_date) if {
    days_since_training := days_between(last_training_date, time.now_ns())
    days_since_training > 365
}

has_embedded_secrets(container) if {
    secrets := {"password", "api_key", "private_key", "token"}
    env_var := container.environment_variables[_]
    secrets[_] == lower(env_var.name)
}

# Risk multipliers for startup-specific factors
stage_risk_multipliers := {
    "pre-revenue": 0.8,
    "early": 1.0,
    "growth": 1.3,
    "scale": 1.5
}

team_size_risk_multipliers := {
    "1-5": 1.2,
    "6-20": 1.0,
    "21-50": 0.9,
    "50+": 0.8
}

phi_volume_risk_multipliers := {
    "low": 0.8,
    "medium": 1.0,
    "high": 1.4
}

funding_cost_multipliers := {
    "bootstrap": 0.5,
    "pre-seed": 0.7,
    "seed": 1.0,
    "series-a": 1.2,
    "series-b+": 1.5
}

violation_base_costs := {
    "implement_encryption": 500,
    "access_control_setup": 1000,
    "policy_creation": 200,
    "privacy_officer": 0,
    "training_program": 300
}
