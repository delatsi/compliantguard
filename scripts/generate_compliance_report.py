#!/usr/bin/env python3
"""
HIPAA Compliance Report Generator
Converts OPA policy output into actionable administrator reports
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_opa_analysis():
    """Run OPA analysis and return structured results"""
    try:
        result = subprocess.run([
            'opa', 'eval', 
            '--input', 'gcp_assets.json',
            '--data', 'policies',
            '--format', 'json',
            'data.actionable_hipaa_report.compliance_report'
        ], capture_output=True, text=True, check=True)
        
        return json.loads(result.stdout)['result'][0]['expressions'][0]['value']
    except subprocess.CalledProcessError as e:
        print(f"Error running OPA: {e}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error parsing OPA output: {e}")
        sys.exit(1)

def generate_executive_summary(report):
    """Generate executive summary section"""
    summary = report['summary']
    
    status_emoji = {
        'COMPLIANT': '✅',
        'MOSTLY_COMPLIANT': '⚠️',
        'NEEDS_IMPROVEMENT': '🔴',
        'NON_COMPLIANT': '🚨'
    }
    
    return f"""
# HIPAA Compliance Report
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

**Overall Status:** {status_emoji.get(summary['compliance_status'], '❓')} {summary['compliance_status']}
**Risk Score:** {summary['overall_risk_score']}/100

### Issue Breakdown
- 🚨 **Critical Issues:** {summary['critical_count']} (immediate action required)
- 🔴 **High Priority:** {summary['high_count']} (resolve this week)  
- ⚠️ **Medium Priority:** {summary['medium_count']} (resolve this month)
- ℹ️ **Low Priority:** {summary['low_count']} (quarterly review)

**Total Violations:** {summary['total_violations']}
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

def generate_quick_wins(report):
    """Identify quick wins for immediate impact"""
    quick_wins = []
    
    for issue_list in [report['critical_issues'], report['high_priority'], report['medium_priority']]:
        for issue in issue_list:
            remediation = issue['remediation']
            if (remediation['effort'] in ['Low', 'Medium'] and 
                'hour' in remediation['timeline'] and
                int(remediation['timeline'].split()[0]) <= 4):
                quick_wins.append(issue)
    
    if not quick_wins:
        return "\n## Quick Wins\n✅ No quick wins identified - focus on prioritized plan above.\n"
    
    section = f"\n## Quick Wins (≤4 hours effort)\n{len(quick_wins)} issues can be resolved quickly for immediate compliance improvement:\n\n"
    
    for issue in quick_wins[:5]:  # Limit to top 5
        section += f"- **{issue['title']}** ({issue['remediation']['timeline']}, {issue['remediation']['effort']} effort)\n"
    
    return section

def main():
    """Main report generation function"""
    print("🔍 Running HIPAA compliance analysis...")
    
    # Run OPA analysis
    report = run_opa_analysis()
    
    if not report:
        print("❌ No compliance data returned from OPA")
        sys.exit(1)
    
    # Generate report sections
    markdown_report = generate_executive_summary(report)
    
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
    markdown_report += generate_quick_wins(report)
    
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
