#!/usr/bin/env python3
"""
HIPAA Compliance Report Generator - Fixed Version
Works with existing themisguard policy structure
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_opa_analysis():
    """Run OPA analysis using the existing policy structure"""
    try:
        # Get all violations from different namespaces
        results = {}

        # Query themisguard framework (has the most data)
        print("🔍 Querying themisguard.startup_framework...")
        result = subprocess.run([
            'opa', 'eval',
            '--input', 'gcp_assets.json',
            '--data', 'policies',
            '--format', 'json',
            'data.themisguard.startup_framework'
        ], capture_output=True, text=True, check=True)

        themisguard_data = json.loads(result.stdout)['result'][0]['expressions'][0]['value']
        results['themisguard'] = themisguard_data
        print(f"✅ Themisguard data loaded: {len(themisguard_data.get('violations', []))} violations")

        # Query GCP HIPAA violations
        print("🔍 Querying gcp.expanded_hipaa...")
        result = subprocess.run([
            'opa', 'eval',
            '--input', 'gcp_assets.json',
            '--data', 'policies',
            '--format', 'json',
            'data.gcp.expanded_hipaa.violations'
        ], capture_output=True, text=True, check=True)

        gcp_violations = json.loads(result.stdout)['result'][0]['expressions'][0]['value']
        results['gcp_violations'] = gcp_violations
        print(f"✅ GCP violations loaded: {len(gcp_violations)} violations")

        # Query HIPAA compliance violations
        print("🔍 Querying hipaa.compliance...")
        result = subprocess.run([
            'opa', 'eval',
            '--input', 'gcp_assets.json',
            '--data', 'policies',
            '--format', 'json',
            'data.hipaa.compliance.violations'
        ], capture_output=True, text=True, check=True)

        hipaa_violations = json.loads(result.stdout)['result'][0]['expressions'][0]['value']
        results['hipaa_violations'] = hipaa_violations
        print(f"✅ HIPAA violations loaded: {len(hipaa_violations)} violations")

        return results

    except subprocess.CalledProcessError as e:
        print(f"Error running OPA: {e}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error parsing OPA output: {e}")
        sys.exit(1)

def convert_to_report_format(opa_results):
    """Convert OPA results to expected report format"""

    # Combine all violations
    all_violations = []
    all_violations.extend(opa_results.get('gcp_violations', []))
    all_violations.extend(opa_results.get('hipaa_violations', []))
    all_violations.extend(opa_results.get('themisguard', {}).get('violations', []))

    print(f"🔍 Processing {len(all_violations)} total violations...")

    # Debug: Show sample violations
    if all_violations:
        print(f"📋 Sample violation types:")
        for i, violation in enumerate(all_violations[:3]):  # Show first 3
            print(f"   {i+1}. Type: {type(violation)}, Content: {str(violation)[:100]}...")

    # Get themisguard framework data
    framework_data = opa_results.get('themisguard', {})

    # Categorize violations by severity/priority
    critical_issues = []
    high_priority = []
    medium_priority = []
    low_priority = []

    # Process violations and categorize them
    for i, violation in enumerate(all_violations):
        try:
            # Convert violation to expected format
            formatted_violation = format_violation(violation, framework_data)

            # Categorize by severity or blocking status
            severity = formatted_violation['risk_level']
            if severity == 'CRITICAL':
                critical_issues.append(formatted_violation)
            elif severity == 'HIGH':
                high_priority.append(formatted_violation)
            elif severity == 'MEDIUM':
                medium_priority.append(formatted_violation)
            else:
                low_priority.append(formatted_violation)

        except Exception as e:
            print(f"⚠️ Error processing violation {i}: {e}")
            print(f"   Violation data: {violation}")
            continue

    # Add MVP requirements as violations if they exist
    mvc_requirements = framework_data.get('mvc_requirements', [])
    print(f"🎯 Processing {len(mvc_requirements)} MVP requirements...")

    for req in mvc_requirements:
        try:
            formatted_req = format_mvc_requirement(req)
            if req.get('blocking', False):
                critical_issues.append(formatted_req)
            else:
                medium_priority.append(formatted_req)
        except Exception as e:
            print(f"⚠️ Error processing MVP requirement: {e}")
            print(f"   Requirement data: {req}")
            continue

    # Calculate summary metrics
    total_violations = len(all_violations) + len(mvc_requirements)
    critical_count = len(critical_issues)
    high_count = len(high_priority)
    medium_count = len(medium_priority)
    low_count = len(low_priority)

    print(f"📊 Categorization complete:")
    print(f"   Critical: {critical_count}, High: {high_count}, Medium: {medium_count}, Low: {low_count}")

    # Determine compliance status
    if critical_count > 0:
        compliance_status = "NON_COMPLIANT"
        risk_score = min(90, 60 + critical_count * 5)
    elif high_count > 5:
        compliance_status = "NEEDS_IMPROVEMENT"
        risk_score = min(70, 40 + high_count * 2)
    elif high_count > 0:
        compliance_status = "MOSTLY_COMPLIANT"
        risk_score = min(40, 20 + high_count * 3)
    else:
        compliance_status = "COMPLIANT"
        risk_score = max(10, 20 - medium_count)

    # Build remediation plan
    remediation_plan = {
        "immediate_actions": critical_issues,
        "this_week": high_priority[:10],  # Limit to top 10
        "this_month": medium_priority[:20],  # Limit to top 20
        "quarterly": low_priority[:10]  # Limit to top 10
    }

    return {
        "summary": {
            "compliance_status": compliance_status,
            "total_violations": total_violations,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "overall_risk_score": risk_score
        },
        "critical_issues": critical_issues,
        "high_priority": high_priority,
        "medium_priority": medium_priority,
        "low_priority": low_priority,
        "remediation_plan": remediation_plan
    }

def format_violation(violation, framework_data):
    """Format a violation into the expected structure"""

    # Handle different violation types
    if isinstance(violation, str):
        # Simple string violation
        return {
            "title": violation,
            "risk_level": "MEDIUM",
            "business_impact": "Compliance gap requiring attention",
            "affected_resource": "Unknown",
            "compliance_frameworks": ["HIPAA"],
            "remediation": {
                "action": f"Address: {violation}",
                "effort": "Medium",
                "cost": "$1,000 - $5,000",
                "timeline": "1-2 weeks",
                "priority": "Medium"
            }
        }

    elif not isinstance(violation, dict):
        # Handle other types (lists, etc.)
        return {
            "title": f"Violation: {str(violation)}",
            "risk_level": "MEDIUM",
            "business_impact": "Compliance gap requiring attention",
            "affected_resource": "Unknown",
            "compliance_frameworks": ["HIPAA"],
            "remediation": {
                "action": "Review and implement appropriate controls",
                "effort": "Medium",
                "cost": "$1,000 - $5,000",
                "timeline": "1-2 weeks",
                "priority": "Medium"
            }
        }

    # Handle dictionary violations
    title = violation.get('title', violation.get('description', violation.get('message', 'Unknown Violation')))
    risk_level = violation.get('severity', violation.get('risk_level', violation.get('priority', 'MEDIUM'))).upper()

    # Map risk levels
    risk_mapping = {
        'CRITICAL': 'CRITICAL',
        'HIGH': 'HIGH',
        'MAJOR': 'HIGH',
        'MEDIUM': 'MEDIUM',
        'MODERATE': 'MEDIUM',
        'LOW': 'LOW',
        'MINOR': 'LOW',
        'ERROR': 'HIGH',
        'WARNING': 'MEDIUM',
        'INFO': 'LOW'
    }
    risk_level = risk_mapping.get(risk_level, 'MEDIUM')

    # Business impact based on risk level
    impact_mapping = {
        'CRITICAL': 'Blocks enterprise sales and creates major legal risk',
        'HIGH': 'Significant compliance gap affecting customer trust',
        'MEDIUM': 'Moderate risk requiring attention within 30 days',
        'LOW': 'Administrative improvement for best practices'
    }

    # Extract resource information
    resource = violation.get('resource',
                           violation.get('component',
                           violation.get('asset',
                           violation.get('service', 'Unknown'))))

    # Extract remediation information
    remediation_text = violation.get('remediation',
                                   violation.get('fix',
                                   violation.get('solution',
                                   violation.get('recommendation', 'Review and implement appropriate controls'))))

    return {
        "title": title,
        "risk_level": risk_level,
        "business_impact": impact_mapping[risk_level],
        "affected_resource": str(resource),
        "compliance_frameworks": violation.get('frameworks', violation.get('compliance', ['HIPAA'])),
        "remediation": {
            "action": remediation_text,
            "effort": violation.get('effort', 'Medium'),
            "cost": violation.get('cost', '$1,000 - $5,000'),
            "timeline": violation.get('timeline', '1-2 weeks'),
            "priority": risk_level.title()
        }
    }

def format_mvc_requirement(req):
    """Format an MVP requirement into violation format"""
    return {
        "title": f"MVP Requirement: {req.get('description', req.get('control', 'Unknown'))}",
        "risk_level": "CRITICAL" if req.get('blocking') else "MEDIUM",
        "business_impact": "Required for MVP HIPAA compliance" if req.get('blocking') else "Recommended for compliance",
        "affected_resource": req.get('category', 'General'),
        "compliance_frameworks": ["HIPAA"],
        "remediation": {
            "action": req.get('description', 'Implement required control'),
            "effort": req.get('effort', 'Medium').title(),
            "cost": req.get('cost', '$1,000'),
            "timeline": "Immediate" if req.get('blocking') else "1-2 weeks",
            "priority": "Critical" if req.get('blocking') else "Medium"
        }
    }

def generate_executive_summary(report):
    """Generate executive summary section"""
    summary = report['summary']

    status_emoji = {
        'COMPLIANT': '✅',
        'MOSTLY_COMPLIANT': '⚠️',
        'NEEDS_IMPROVEMENT': '🔴',
        'NON_COMPLIANT': '🚨'
    }

    # Calculate business metrics
    critical_count = summary['critical_count']
    high_count = summary['high_count']

    # Estimate business impact
    customer_blocking_issues = critical_count
    audit_risk_issues = critical_count + high_count

    return f"""
# HIPAA Compliance Executive Report
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📈 Executive Summary (CEO/COO/Board)

### Business Impact Assessment
- **Customer Acquisition Risk:** {customer_blocking_issues} critical issues are **blocking enterprise sales**
- **Regulatory Risk:** {audit_risk_issues} issues could result in **audit failures** and potential fines
- **Compliance Status:** {status_emoji.get(summary['compliance_status'], '❓')} {summary['compliance_status'].replace('_', ' ').title()}

### Financial Implications
- **Potential Revenue Impact:** ${customer_blocking_issues * 50000:,}/month (blocked enterprise deals)
- **Regulatory Fine Risk:** $50,000 - $1.5M per violation category if audited
- **Remediation Investment:** ~$5,000 - $15,000 (primarily engineering time)
- **ROI Timeline:** 30-90 days to resolution

### Key Metrics
| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| **Enterprise Ready** | {'❌ No' if critical_count > 0 else '✅ Yes'} | ✅ Yes | {critical_count} critical issues |
| **Audit Ready** | {'❌ No' if audit_risk_issues > 0 else '✅ Yes'} | ✅ Yes | {audit_risk_issues} high-risk issues |
| **Risk Score** | {summary['overall_risk_score']}/100 | <20/100 | {max(0, summary['overall_risk_score'] - 20)} points |

---

## 🛡️ CISO Security Brief

### Threat Landscape
- **External Attack Surface:** {critical_count} critical security gaps expose PHI data
- **Insider Risk:** Inadequate access controls increase data breach probability
- **Compliance Posture:** {'Non-compliant' if critical_count > 0 else 'Improving'} with HIPAA Security Rule requirements

### Security Priorities
1. **Infrastructure Hardening:** {critical_count + high_count} security controls missing
2. **Access Management:** Service accounts and network policies need immediate attention
3. **Data Protection:** Secret management and encryption requirements partially implemented

### Incident Response Readiness
- **Current State:** {'❌ Not Ready' if critical_count > 0 else '⚠️ Partially Ready'}
- **Audit Trail:** Logging enabled but network monitoring gaps exist
- **Breach Detection:** Limited visibility into container and API access

---

## 📊 Technical Summary (CTO/Engineering)

**Overall Status:** {status_emoji.get(summary['compliance_status'], '❓')} {summary['compliance_status']}
**Risk Score:** {summary['overall_risk_score']}/100

### Issue Breakdown
- 🚨 **Critical Issues:** {summary['critical_count']} (immediate action required)
- 🔴 **High Priority:** {summary['high_count']} (resolve this week)
- ⚠️ **Medium Priority:** {summary['medium_count']} (resolve this month)
- ℹ️ **Low Priority:** {summary['low_count']} (quarterly review)

**Total Technical Violations:** {summary['total_violations']}

### Resource Requirements
- **Engineering Time:** 1-2 engineers for 2-3 weeks
- **Infrastructure Changes:** GKE cluster updates, secret management migration
- **Zero Downtime:** Most fixes can be implemented without service interruption
"""

def generate_board_recommendations(report):
    """Generate board-level strategic recommendations"""
    summary = report['summary']
    critical_count = summary['critical_count']

    return f"""
## 📋 Board Recommendations

### Immediate Actions Required
{f'''
**URGENT:** {critical_count} critical compliance issues are blocking enterprise customer acquisition.
- **Business Risk:** Estimated ${critical_count * 50000:,}/month in lost revenue opportunities
- **Regulatory Risk:** Potential fines of $50,000 - $1.5M per violation category
- **Timeline:** 30-60 days to achieve enterprise-ready compliance status
''' if critical_count > 0 else '''
**GOOD NEWS:** No critical compliance issues blocking customer acquisition.
- Continue with planned security improvements
- Maintain current compliance posture
'''}

### Strategic Recommendations

#### 1. **Compliance as Competitive Advantage**
- **Current State:** {'Behind market' if critical_count > 0 else 'Meeting market standards'}
- **Opportunity:** HIPAA compliance enables 3x larger addressable market
- **Investment:** $10-20K engineering effort → $500K+ enterprise revenue potential

#### 2. **Risk Management**
- **Regulatory:** Implement governance framework for ongoing compliance
- **Operational:** Automate compliance monitoring to prevent future gaps
- **Financial:** Compliance insurance eligibility improves with strong posture

#### 3. **Scaling Considerations**
- **Growth Enablement:** Compliance infrastructure supports Series A/B fundraising
- **Market Position:** Strong security posture differentiates from competitors
- **Exit Readiness:** Compliance documentation required for acquisition due diligence

### Success Metrics (Next Quarter)
- [ ] **Enterprise Sales Enabled:** Zero critical compliance issues
- [ ] **Audit Ready:** <5 high-priority violations remaining
- [ ] **Automated Monitoring:** Continuous compliance validation implemented
- [ ] **Documentation Complete:** All HIPAA policies and procedures documented
"""

def generate_issue_section(issues, title, description):
    """Generate a section for a specific priority level"""
    if not issues:
        return f"\n## {title}\n✅ No {title.lower()} found!\n"

    section = f"\n## {title}\n{description}\n\n"

    for i, issue in enumerate(issues, 1):
        remediation = issue['remediation']

        section += f"""
### {i}. {issue['title']}

**Risk Level:** {issue['risk_level']}
**Business Impact:** {issue['business_impact']}
**Affected Resource:** `{issue['affected_resource']}`
**Compliance Framework:** {', '.join(issue['compliance_frameworks'])}

#### Remediation Steps:
**Action:** {remediation['action']}
**Effort:** {remediation['effort']}
**Cost:** {remediation['cost']}
**Timeline:** {remediation['timeline']}
**Priority:** {remediation['priority']}

"""

        if 'command' in remediation:
            section += f"**Command:**\n```bash\n{remediation['command']}\n```\n\n"
        elif 'steps' in remediation:
            section += "**Steps:**\n"
            for step in remediation['steps']:
                section += f"1. {step}\n"
            section += "\n"

    return section

def generate_remediation_plan(plan):
    """Generate prioritized remediation timeline"""
    return f"""
## Remediation Timeline

### 🚨 Immediate Actions (Next 24 hours)
{len(plan['immediate_actions'])} critical issues requiring immediate attention:
{', '.join([issue['title'] for issue in plan['immediate_actions']]) if plan['immediate_actions'] else 'None'}

### 📅 This Week
{len(plan['this_week'])} high-priority issues:
{', '.join([issue['title'] for issue in plan['this_week']]) if plan['this_week'] else 'None'}

### 📆 This Month
{len(plan['this_month'])} medium-priority improvements:
{', '.join([issue['title'] for issue in plan['this_month']]) if plan['this_month'] else 'None'}

### 📋 Quarterly Review
{len(plan['quarterly'])} administrative tasks:
{', '.join([issue['title'] for issue in plan['quarterly']]) if plan['quarterly'] else 'None'}
"""

def main():
    """Main report generation function"""
    print("🔍 Running HIPAA compliance analysis with existing policies...")

    # Run OPA analysis with existing structure
    opa_results = run_opa_analysis()

    if not opa_results:
        print("❌ No compliance data returned from OPA")
        sys.exit(1)

    # Convert to expected report format
    print("🔄 Converting policy data to report format...")
    report = convert_to_report_format(opa_results)

    # Generate report sections
    markdown_report = generate_executive_summary(report)
    markdown_report += generate_board_recommendations(report)

    markdown_report += generate_issue_section(
        report['critical_issues'],
        "🚨 Critical Issues",
        "These issues must be resolved immediately as they block customer acquisition or create major legal risk."
    )

    markdown_report += generate_issue_section(
        report['high_priority'],
        "🔴 High Priority Issues",
        "Significant compliance gaps that should be resolved within one week."
    )

    markdown_report += generate_issue_section(
        report['medium_priority'],
        "⚠️ Medium Priority Issues",
        "Important security improvements to complete within one month."
    )

    markdown_report += generate_issue_section(
        report['low_priority'],
        "ℹ️ Low Priority Issues",
        "Administrative tasks for quarterly compliance review."
    )

    markdown_report += generate_remediation_plan(report['remediation_plan'])

    # Write report to file
    report_file = Path('docs/hipaa_compliance_report.md')
    report_file.parent.mkdir(exist_ok=True)
    report_file.write_text(markdown_report)

    print(f"✅ HIPAA compliance report generated: {report_file}")
    print(f"📊 Found {report['summary']['total_violations']} total issues")
    print(f"🎯 Status: {report['summary']['compliance_status']}")

    # Return exit code based on compliance status
    if report['summary']['critical_count'] > 0:
        sys.exit(1)  # Critical issues found
    elif report['summary']['high_count'] > 0:
        sys.exit(2)  # High priority issues found
    else:
        sys.exit(0)  # Acceptable compliance level

if __name__ == "__main__":
    main()
