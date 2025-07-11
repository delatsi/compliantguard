# Security Assessment Template

**Document Version:** 1.0  
**Assessment Date:** [DATE]  
**Assessed By:** [ASSESSOR NAME]  
**Organization:** [ORGANIZATION NAME]  
**Scope:** [ASSESSMENT SCOPE]

---

## 📋 Executive Summary

### Assessment Overview
<!-- Provide a high-level summary of the security assessment, including scope, methodology, and key findings -->

**Assessment Period:** [START DATE] - [END DATE]  
**Assessment Type:** [Internal/External/Third-Party]  
**Methodology:** [NIST CSF/ISO 27001/Custom]  

### Key Findings Summary
- **Total Issues Identified:** [NUMBER]
- **Critical Risk Issues:** [NUMBER]
- **High Risk Issues:** [NUMBER]
- **Medium Risk Issues:** [NUMBER]
- **Low Risk Issues:** [NUMBER]

### Risk Rating Summary
| Risk Level | Count | Percentage |
|------------|-------|------------|
| Critical   | [N]   | [%]        |
| High       | [N]   | [%]        |
| Medium     | [N]   | [%]        |
| Low        | [N]   | [%]        |

### Overall Security Posture Score: [SCORE]/100

---

## 🎯 Assessment Scope

### In Scope
- [ ] Network Infrastructure
- [ ] Cloud Services (AWS/GCP/Azure)
- [ ] Applications and Databases
- [ ] Endpoint Devices
- [ ] Security Controls
- [ ] Policies and Procedures
- [ ] Personnel and Training

### Out of Scope
- [List items explicitly excluded from assessment]

### Assessment Methodology
<!-- Describe the methodology used for the assessment -->

1. **Information Gathering**
   - Document review
   - Stakeholder interviews
   - System inventory

2. **Technical Assessment**
   - Vulnerability scanning
   - Configuration review
   - Penetration testing (if applicable)

3. **Risk Analysis**
   - Threat modeling
   - Impact assessment
   - Risk prioritization

---

## 🔍 Detailed Findings

### Critical Risk Findings

#### Finding C-001: [FINDING TITLE]
**Risk Level:** Critical  
**CVSS Score:** [SCORE] (if applicable)  
**Affected Systems:** [SYSTEMS/ASSETS]

**Description:**
[Detailed description of the vulnerability or security issue]

**Technical Details:**
[Technical information about how the issue was identified]

**Business Impact:**
[Potential impact on business operations, data, or reputation]

**Recommendation:**
[Specific steps to remediate the issue]

**Timeline:** [IMMEDIATE/30 DAYS/60 DAYS]

---

#### Finding C-002: [FINDING TITLE]
[Repeat format for each critical finding]

### High Risk Findings

#### Finding H-001: [FINDING TITLE]
**Risk Level:** High  
**Affected Systems:** [SYSTEMS/ASSETS]

[Follow same format as critical findings]

### Medium Risk Findings

#### Finding M-001: [FINDING TITLE]
**Risk Level:** Medium  
**Affected Systems:** [SYSTEMS/ASSETS]

[Follow same format]

### Low Risk Findings

#### Finding L-001: [FINDING TITLE]
**Risk Level:** Low  
**Affected Systems:** [SYSTEMS/ASSETS]

[Follow same format]

---

## 📊 Security Control Assessment

### Administrative Controls

| Control Area | Status | Effectiveness | Comments |
|--------------|--------|---------------|----------|
| Security Governance | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Risk Management | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Personnel Security | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Security Awareness | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Incident Response | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |

### Technical Controls

| Control Area | Status | Effectiveness | Comments |
|--------------|--------|---------------|----------|
| Access Control | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Authentication | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Encryption | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Network Security | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Endpoint Security | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Monitoring & Logging | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |

### Physical Controls

| Control Area | Status | Effectiveness | Comments |
|--------------|--------|---------------|----------|
| Facility Security | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Access Controls | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |
| Environmental | [✅/⚠️/❌] | [High/Medium/Low] | [Comments] |

---

## 🎯 Compliance Assessment

### HIPAA Compliance (if applicable)

| Safeguard Category | Compliance Level | Gap Areas |
|-------------------|------------------|-----------|
| Administrative Safeguards | [Compliant/Partial/Non-Compliant] | [List gaps] |
| Physical Safeguards | [Compliant/Partial/Non-Compliant] | [List gaps] |
| Technical Safeguards | [Compliant/Partial/Non-Compliant] | [List gaps] |

### Other Compliance Frameworks

| Framework | Compliance Level | Key Gaps |
|-----------|------------------|----------|
| SOC 2 | [Level] | [Gaps] |
| ISO 27001 | [Level] | [Gaps] |
| NIST CSF | [Level] | [Gaps] |

---

## 📈 Risk Analysis

### Risk Matrix

| Risk Level | Likelihood | Impact | Examples |
|------------|------------|--------|----------|
| Critical | High | High | [Examples] |
| High | High | Medium OR Medium | High | [Examples] |
| Medium | Medium | Medium OR Low | High | [Examples] |
| Low | Low | Low/Medium | [Examples] |

### Top 5 Risks by Business Impact

1. **[Risk Name]** - [Impact Description]
2. **[Risk Name]** - [Impact Description]
3. **[Risk Name]** - [Impact Description]
4. **[Risk Name]** - [Impact Description]
5. **[Risk Name]** - [Impact Description]

---

## 🛠️ Remediation Plan

### Immediate Actions (0-30 days)

| Priority | Finding ID | Action Required | Owner | Target Date |
|----------|------------|-----------------|-------|-------------|
| Critical | C-001 | [Action] | [Owner] | [Date] |
| Critical | C-002 | [Action] | [Owner] | [Date] |

### Short-term Actions (1-3 months)

| Priority | Finding ID | Action Required | Owner | Target Date |
|----------|------------|-----------------|-------|-------------|
| High | H-001 | [Action] | [Owner] | [Date] |
| High | H-002 | [Action] | [Owner] | [Date] |

### Medium-term Actions (3-6 months)

| Priority | Finding ID | Action Required | Owner | Target Date |
|----------|------------|-----------------|-------|-------------|
| Medium | M-001 | [Action] | [Owner] | [Date] |
| Medium | M-002 | [Action] | [Owner] | [Date] |

### Long-term Actions (6-12 months)

| Priority | Finding ID | Action Required | Owner | Target Date |
|----------|------------|-----------------|-------|-------------|
| Low | L-001 | [Action] | [Owner] | [Date] |

---

## 💰 Cost Estimate

### Remediation Costs

| Category | Estimated Cost | Timeline |
|----------|----------------|----------|
| Critical Issues | $[AMOUNT] | [TIMELINE] |
| High Priority Issues | $[AMOUNT] | [TIMELINE] |
| Medium Priority Issues | $[AMOUNT] | [TIMELINE] |
| Low Priority Issues | $[AMOUNT] | [TIMELINE] |
| **Total Estimated Cost** | **$[TOTAL]** | **[TIMELINE]** |

### Cost-Benefit Analysis
[Provide analysis of security investment vs. risk reduction]

---

## 📋 Recommendations

### Strategic Recommendations

1. **[Recommendation Title]**
   - Description: [Details]
   - Business Benefit: [Benefits]
   - Implementation Effort: [High/Medium/Low]
   - Timeline: [Timeline]

2. **[Recommendation Title]**
   - [Continue format]

### Tactical Recommendations

1. **[Recommendation Title]**
   - [Follow same format]

### Operational Recommendations

1. **[Recommendation Title]**
   - [Follow same format]

---

## 📊 Metrics and KPIs

### Current Security Metrics

| Metric | Current Value | Target Value | Gap |
|--------|---------------|--------------|-----|
| Mean Time to Detection | [VALUE] | [TARGET] | [GAP] |
| Mean Time to Response | [VALUE] | [TARGET] | [GAP] |
| Vulnerability Remediation Time | [VALUE] | [TARGET] | [GAP] |
| Security Training Completion | [VALUE] | [TARGET] | [GAP] |

### Recommended Security KPIs

- Security Incident Frequency
- Compliance Score Trends
- Security Control Effectiveness
- Risk Exposure Trends
- Security Investment ROI

---

## 🔄 Follow-up Actions

### Assessment Follow-up

- [ ] Schedule follow-up assessment in [TIMEFRAME]
- [ ] Quarterly progress reviews
- [ ] Annual comprehensive assessment
- [ ] Continuous monitoring implementation

### Stakeholder Communication

- [ ] Present findings to executive leadership
- [ ] Communicate with IT leadership
- [ ] Update security committee
- [ ] Inform compliance team

---

## 📎 Appendices

### Appendix A: Detailed Technical Findings
[Include detailed technical evidence, screenshots, logs, etc.]

### Appendix B: Assessment Tools and Methodology
[List tools used and detailed methodology]

### Appendix C: Compliance Mapping
[Map findings to specific compliance requirements]

### Appendix D: Risk Register
[Comprehensive risk register with all identified risks]

---

## ✍️ Assessment Team

**Lead Assessor:** [Name, Title, Credentials]  
**Technical Assessors:** [Names and specialties]  
**Review Team:** [Names and roles]

**Contact Information:**  
Email: [EMAIL]  
Phone: [PHONE]  

---

**Document Classification:** [CONFIDENTIAL/INTERNAL/PUBLIC]  
**Distribution:** [List authorized recipients]  
**Retention Period:** [PERIOD]  
**Next Review Date:** [DATE]