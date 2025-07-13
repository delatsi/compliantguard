#!/usr/bin/env python3
"""
Developer-focused violation analyzer
Shows specific, actionable violations with fix commands.
"""

import json
import subprocess
import sys
from collections import defaultdict, Counter
import re

def get_raw_violations_detailed():
    """Get detailed violations with full context"""
    try:
        # Get the 290 GCP violations with full detail
        print("🔍 Getting detailed GCP expanded HIPAA violations...")
        result = subprocess.run([
            'opa', 'eval',
            '--input', 'gcp_assets.json',
            '--data', 'policies',
            '--format', 'json',
            'data.gcp.expanded_hipaa.violations'
        ], capture_output=True, text=True, check=True)
        
        violations_raw = json.loads(result.stdout)['result'][0]['expressions'][0]['value']
        print(f"✅ Got {len(violations_raw)} GCP violations")
        
        # Show first few violations to understand structure
        print("\n🔍 Sample violation structures:")
        for i, violation in enumerate(violations_raw[:3]):
            print(f"\nViolation {i+1}:")
            print(f"Type: {type(violation)}")
            if isinstance(violation, dict):
                print(f"Keys: {list(violation.keys())}")
                for key, value in list(violation.items())[:3]:  # Show first 3 key-value pairs
                    print(f"  {key}: {str(value)[:100]}...")
            else:
                print(f"Content: {str(violation)[:200]}...")
        
        return violations_raw
        
    except Exception as e:
        print(f"❌ Error getting violations: {e}")
        return []

def analyze_gcp_violations_for_developers(violations):
    """Analyze GCP violations from a developer perspective"""
    
    # Group violations by actionable categories
    grouped_violations = {
        'gke_cluster_issues': [],
        'pod_security_issues': [],
        'storage_security_issues': [],
        'network_security_issues': [],
        'iam_access_issues': [],
        'encryption_issues': [],
        'logging_audit_issues': [],
        'resource_management_issues': [],
        'unknown_issues': []
    }
    
    # Track resources and violation patterns
    resource_violations = defaultdict(list)
    violation_patterns = Counter()
    
    for violation in violations:
        categorized = False
        violation_str = str(violation).lower()
        
        # Extract resource information
        resource_info = extract_resource_info(violation)
        resource_violations[resource_info['type']].append(violation)
        
        # Categorize by actionable developer tasks
        if any(keyword in violation_str for keyword in ['cluster', 'gke', 'kubernetes']):
            if 'private' in violation_str:
                grouped_violations['gke_cluster_issues'].append({
                    'type': 'GKE Private Cluster Not Enabled',
                    'violation': violation,
                    'resource': resource_info,
                    'fix_action': 'Enable private cluster configuration'
                })
                categorized = True
            elif 'network' in violation_str and 'policy' in violation_str:
                grouped_violations['network_security_issues'].append({
                    'type': 'Network Policies Missing',
                    'violation': violation,
                    'resource': resource_info,
                    'fix_action': 'Create Kubernetes NetworkPolicy resources'
                })
                categorized = True
        
        if any(keyword in violation_str for keyword in ['pod', 'container', 'securitycontext']):
            grouped_violations['pod_security_issues'].append({
                'type': 'Pod Security Context Missing',
                'violation': violation,
                'resource': resource_info,
                'fix_action': 'Add securityContext to pod specifications'
            })
            categorized = True
        
        elif any(keyword in violation_str for keyword in ['storage', 'bucket', 'volume']):
            if 'public' in violation_str:
                grouped_violations['storage_security_issues'].append({
                    'type': 'Public Storage Access',
                    'violation': violation,
                    'resource': resource_info,
                    'fix_action': 'Remove public access from storage buckets'
                })
                categorized = True
            elif 'encryption' in violation_str:
                grouped_violations['encryption_issues'].append({
                    'type': 'Storage Encryption Missing',
                    'violation': violation,
                    'resource': resource_info,
                    'fix_action': 'Enable encryption at rest for storage'
                })
                categorized = True
        
        elif any(keyword in violation_str for keyword in ['service', 'account', 'iam', 'permission']):
            grouped_violations['iam_access_issues'].append({
                'type': 'IAM/Service Account Issues',
                'violation': violation,
                'resource': resource_info,
                'fix_action': 'Review and restrict service account permissions'
            })
            categorized = True
        
        elif any(keyword in violation_str for keyword in ['logging', 'audit', 'monitor']):
            grouped_violations['logging_audit_issues'].append({
                'type': 'Audit Logging Not Enabled',
                'violation': violation,
                'resource': resource_info,
                'fix_action': 'Enable audit logging and monitoring'
            })
            categorized = True
        
        elif any(keyword in violation_str for keyword in ['firewall', 'network', 'vpc', 'subnet']):
            grouped_violations['network_security_issues'].append({
                'type': 'Network Security Configuration',
                'violation': violation,
                'resource': resource_info,
                'fix_action': 'Configure network security rules'
            })
            categorized = True
        
        elif any(keyword in violation_str for keyword in ['encrypt', 'ssl', 'tls']):
            grouped_violations['encryption_issues'].append({
                'type': 'Encryption Configuration Missing',
                'violation': violation,
                'resource': resource_info,
                'fix_action': 'Configure encryption in transit/at rest'
            })
            categorized = True
        
        elif any(keyword in violation_str for keyword in ['label', 'tag', 'name']):
            grouped_violations['resource_management_issues'].append({
                'type': 'Resource Labeling/Naming',
                'violation': violation,
                'resource': resource_info,
                'fix_action': 'Add proper labels and naming conventions'
            })
            categorized = True
        
        if not categorized:
            grouped_violations['unknown_issues'].append({
                'type': 'Unknown Configuration Issue',
                'violation': violation,
                'resource': resource_info,
                'fix_action': 'Manual review required'
            })
        
        # Track violation patterns
        pattern = extract_specific_pattern(violation)
        violation_patterns[pattern] += 1
    
    return grouped_violations, resource_violations, violation_patterns

def extract_resource_info(violation):
    """Extract actionable resource information"""
    resource_info = {
        'type': 'Unknown',
        'name': 'Unknown',
        'namespace': None,
        'component': 'Unknown'
    }
    
    if isinstance(violation, dict):
        # Look for resource identifiers
        for key in ['resource', 'asset', 'name', 'component']:
            if key in violation:
                value = str(violation[key])
                if 'k8s.io' in value or 'apps/' in value:
                    resource_info['type'] = 'Kubernetes'
                    resource_info['component'] = value.split('/')[-1]
                elif 'compute' in value.lower():
                    resource_info['type'] = 'Compute Engine'
                elif 'storage' in value.lower():
                    resource_info['type'] = 'Cloud Storage'
                elif 'gke' in value.lower():
                    resource_info['type'] = 'GKE'
                resource_info['name'] = value
                break
        
        # Look for namespace
        if 'namespace' in violation:
            resource_info['namespace'] = violation['namespace']
    
    violation_str = str(violation).lower()
    if resource_info['type'] == 'Unknown':
        if 'kubernetes' in violation_str or 'k8s' in violation_str:
            resource_info['type'] = 'Kubernetes'
        elif 'gke' in violation_str:
            resource_info['type'] = 'GKE'
        elif 'storage' in violation_str:
            resource_info['type'] = 'Cloud Storage'
        elif 'compute' in violation_str:
            resource_info['type'] = 'Compute Engine'
    
    return resource_info

def extract_specific_pattern(violation):
    """Extract specific violation pattern for developers"""
    violation_str = str(violation).lower()
    
    # Look for specific technical patterns
    if 'securitycontext' in violation_str or ('security' in violation_str and 'context' in violation_str):
        return 'Pod missing securityContext'
    elif 'private' in violation_str and 'cluster' in violation_str:
        return 'GKE cluster not private'
    elif 'networkpolicy' in violation_str or ('network' in violation_str and 'policy' in violation_str):
        return 'Missing NetworkPolicy'
    elif 'public' in violation_str and ('bucket' in violation_str or 'storage' in violation_str):
        return 'Public storage bucket'
    elif 'encryption' in violation_str and 'rest' in violation_str:
        return 'Missing encryption at rest'
    elif 'ssl' in violation_str or 'tls' in violation_str:
        return 'Missing SSL/TLS'
    elif 'audit' in violation_str and 'log' in violation_str:
        return 'Audit logging not enabled'
    elif 'service' in violation_str and 'account' in violation_str:
        return 'Service account misconfigured'
    elif 'firewall' in violation_str:
        return 'Firewall rules too permissive'
    elif 'label' in violation_str:
        return 'Resource not labeled'
    else:
        # Extract first meaningful words
        words = [w for w in violation_str.split()[:5] if len(w) > 3]
        return ' '.join(words[:2]) if words else 'Unknown issue'

def generate_developer_report(grouped_violations, resource_violations, violation_patterns):
    """Generate a developer-focused report with actionable fixes"""
    
    total_violations = sum(len(violations) for violations in grouped_violations.values())
    
    report = f"""
# Developer Action Plan: Infrastructure Violations
**Total Issues Found:** {total_violations}

This report breaks down the 290 infrastructure violations into actionable developer tasks.

## 🎯 Priority Fix Areas

"""
    
    # Sort violation groups by count and impact
    sorted_groups = sorted(
        [(name, violations) for name, violations in grouped_violations.items() if violations],
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    for group_name, violations in sorted_groups:
        count = len(violations)
        if count == 0:
            continue
            
        group_title = group_name.replace('_', ' ').title()
        priority = get_priority_level(group_name, count)
        
        report += f"""
### {priority} {group_title} ({count} issues)

"""
        
        # Group by violation type within each category
        violation_types = defaultdict(list)
        for v in violations:
            violation_types[v['type']].append(v)
        
        for vtype, vlist in violation_types.items():
            resource_examples = [v['resource']['name'] for v in vlist[:3]]
            fix_action = vlist[0]['fix_action']
            
            report += f"""
#### {vtype} ({len(vlist)} instances)
**Fix Required:** {fix_action}
**Affected Resources:** {', '.join(resource_examples)}{'...' if len(vlist) > 3 else ''}

"""
            
            # Provide specific fix commands for common issues
            fix_commands = get_fix_commands(vtype, vlist)
            if fix_commands:
                report += f"**Fix Commands:**\n```bash\n{fix_commands}\n```\n\n"
    
    report += f"""
## 📊 Violation Breakdown by Resource Type

"""
    
    sorted_resources = sorted(resource_violations.items(), key=lambda x: len(x[1]), reverse=True)
    for resource_type, violations in sorted_resources[:10]:
        report += f"- **{resource_type}**: {len(violations)} violations\n"
    
    report += f"""
## 🔧 Most Common Issues (Developer Focus)

"""
    
    for pattern, count in violation_patterns.most_common(10):
        percentage = (count / total_violations) * 100
        urgency = "🚨" if count > 50 else "🔴" if count > 20 else "⚠️"
        report += f"{urgency} **{pattern}**: {count} instances ({percentage:.1f}%)\n"
    
    report += f"""
## 🚀 Quick Wins (High Impact, Low Effort)

### 1. GKE Cluster Security (Potential: {len(grouped_violations.get('gke_cluster_issues', []))} fixes)
```bash
# Enable private cluster (requires cluster recreation)
gcloud container clusters create-auto my-cluster \\
    --enable-private-nodes \\
    --master-ipv4-cidr-block 172.16.0.0/28 \\
    --enable-network-policy
```

### 2. Pod Security Contexts (Potential: {len(grouped_violations.get('pod_security_issues', []))} fixes)
```yaml
# Add to all pod specs in your deployments
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
  containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```

### 3. Storage Security (Potential: {len(grouped_violations.get('storage_security_issues', []))} fixes)
```bash
# Remove public access from buckets
gsutil iam ch -d allUsers:objectViewer gs://your-bucket-name
gsutil uniformbucketlevelaccess set on gs://your-bucket-name
```

## 📋 Step-by-Step Remediation Plan

### Week 1: Critical Security Issues
1. **Enable GKE private cluster** (if using GKE)
2. **Remove public storage access** (if any buckets are public)
3. **Add pod security contexts** to critical workloads

### Week 2: Network Security
1. **Implement NetworkPolicies** for pod-to-pod communication
2. **Review firewall rules** and apply principle of least privilege
3. **Enable audit logging** for all critical services

### Week 3: Encryption and Access Control
1. **Enable encryption at rest** for all storage
2. **Review service account permissions**
3. **Implement proper resource labeling**

### Week 4: Monitoring and Compliance
1. **Set up continuous monitoring** for new violations
2. **Document security procedures**
3. **Train team on secure defaults**

## 🎯 Success Metrics

Track your progress with these metrics:
- **Critical violations**: Reduce from current count to 0
- **Pod security coverage**: 100% of pods have securityContext
- **Storage security**: 0 public buckets, all encrypted
- **Network security**: All namespaces have NetworkPolicies

## 💡 Prevention Tips

1. **Use security-focused base images**
2. **Implement security policies as code**
3. **Set up automated security scanning**
4. **Use Kubernetes Pod Security Standards**
5. **Implement GitOps with security validation**
"""
    
    return report

def get_priority_level(group_name, count):
    """Get priority level based on group name and count"""
    high_priority_groups = ['gke_cluster_issues', 'pod_security_issues', 'storage_security_issues']
    
    if group_name in high_priority_groups:
        return "🚨 CRITICAL:"
    elif count > 50:
        return "🔴 HIGH:"
    elif count > 20:
        return "⚠️ MEDIUM:"
    else:
        return "ℹ️ LOW:"

def get_fix_commands(violation_type, violations):
    """Get specific fix commands for violation types"""
    
    if 'Pod Security Context' in violation_type:
        return """# Add to your Kubernetes deployment YAML
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: your-app
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true"""
    
    elif 'GKE Private Cluster' in violation_type:
        return """# Create new private cluster (requires migration)
gcloud container clusters create-auto private-cluster \\
    --enable-private-nodes \\
    --master-ipv4-cidr-block 172.16.0.0/28"""
    
    elif 'Public Storage' in violation_type:
        # Extract bucket names from violations
        bucket_names = []
        for v in violations[:3]:
            resource_name = v['resource']['name']
            if 'bucket' in resource_name.lower():
                bucket_names.append(resource_name)
        
        if bucket_names:
            commands = []
            for bucket in bucket_names:
                commands.append(f"gsutil iam ch -d allUsers:objectViewer gs://{bucket}")
            return '\n'.join(commands)
    
    elif 'Network Policies' in violation_type:
        return """# Create NetworkPolicy to restrict pod communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress"""
    
    elif 'Audit Logging' in violation_type:
        return """# Enable audit logging for GKE
gcloud container clusters update CLUSTER_NAME \\
    --enable-cloud-logging \\
    --logging=SYSTEM,WORKLOAD,API_SERVER"""
    
    return None

def main():
    """Main analysis function"""
    print("🔍 Analyzing violations for developer action plan...")
    
    # Get detailed violations
    violations = get_raw_violations_detailed()
    
    if not violations:
        print("❌ Could not retrieve violations")
        return
    
    # Analyze from developer perspective
    grouped_violations, resource_violations, violation_patterns = analyze_gcp_violations_for_developers(violations)
    
    # Show quick summary
    print(f"\n📊 Developer-Focused Breakdown:")
    for group_name, violations in grouped_violations.items():
        if violations:
            print(f"   {group_name.replace('_', ' ').title()}: {len(violations)} issues")
    
    # Generate developer report
    report = generate_developer_report(grouped_violations, resource_violations, violation_patterns)
    
    # Save report
    with open('docs/developer_action_plan.md', 'w') as f:
        f.write(report)
    
    print(f"\n✅ Developer action plan generated!")
    print(f"📋 Report saved to: docs/developer_action_plan.md")
    print(f"\n🎯 Top 3 actionable issues:")
    
    sorted_groups = sorted(
        [(name, violations) for name, violations in grouped_violations.items() if violations],
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    for name, violations in sorted_groups[:3]:
        print(f"   {name.replace('_', ' ').title()}: {len(violations)} fixes needed")

if __name__ == "__main__":
    main()
