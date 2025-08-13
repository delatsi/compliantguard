"""
AWS Bedrock Integration for Automated Security Documentation Generation
Supports various AI models for generating comprehensive security documents
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types for generation"""

    HIPAA_ASSESSMENT = "hipaa_assessment"
    SECURITY_POLICY = "security_policy"
    INCIDENT_RESPONSE = "incident_response_plan"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_REPORT = "compliance_report"
    SECURITY_ARCHITECTURE = "security_architecture"
    PENETRATION_TEST = "penetration_test_report"
    VULNERABILITY_REPORT = "vulnerability_report"


class BedrockModel(Enum):
    """Available Bedrock models"""

    CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
    CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
    TITAN_TEXT = "amazon.titan-text-express-v1"


@dataclass
class DocumentContext:
    """Context information for document generation"""

    organization_name: str
    assessment_scope: List[str]
    compliance_frameworks: List[str]
    risk_level: str
    findings: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class BedrockDocumentationGenerator:
    """Main class for generating security documentation using AWS Bedrock"""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize the Bedrock client"""
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_config = {
            BedrockModel.CLAUDE_3_SONNET: {
                "max_tokens": 8000,
                "temperature": 0.1,
                "top_p": 0.9,
            },
            BedrockModel.CLAUDE_3_HAIKU: {
                "max_tokens": 4000,
                "temperature": 0.1,
                "top_p": 0.9,
            },
        }

    async def generate_document(
        self,
        doc_type: DocumentType,
        context: DocumentContext,
        model: BedrockModel = BedrockModel.CLAUDE_3_SONNET,
    ) -> str:
        """Generate a security document using Bedrock"""

        try:
            prompt = self._build_prompt(doc_type, context)
            response = await self._invoke_bedrock_model(model, prompt)

            # Post-process and validate the response
            processed_response = self._post_process_response(response, doc_type)

            return processed_response

        except Exception as e:
            logger.error(f"Error generating document: {str(e)}")
            raise

    def _build_prompt(self, doc_type: DocumentType, context: DocumentContext) -> str:
        """Build the prompt for document generation"""

        prompts = {
            DocumentType.HIPAA_ASSESSMENT: self._build_hipaa_assessment_prompt,
            DocumentType.SECURITY_POLICY: self._build_security_policy_prompt,
            DocumentType.INCIDENT_RESPONSE: self._build_incident_response_prompt,
            DocumentType.RISK_ASSESSMENT: self._build_risk_assessment_prompt,
            DocumentType.COMPLIANCE_REPORT: self._build_compliance_report_prompt,
            DocumentType.VULNERABILITY_REPORT: self._build_vulnerability_report_prompt,
        }

        prompt_builder = prompts.get(doc_type)
        if not prompt_builder:
            raise ValueError(f"Unsupported document type: {doc_type}")

        return prompt_builder(context)

    def _build_hipaa_assessment_prompt(self, context: DocumentContext) -> str:
        """Build prompt for HIPAA assessment report"""
        return f"""
You are a HIPAA compliance expert tasked with generating a comprehensive HIPAA assessment report. 

Organization: {context.organization_name}
Assessment Scope: {', '.join(context.assessment_scope)}
Risk Level: {context.risk_level}

Based on the following findings and context, generate a detailed HIPAA compliance assessment report:

Findings Data:
{json.dumps(context.findings, indent=2)}

Metadata:
{json.dumps(context.metadata, indent=2)}

Please generate a comprehensive report that includes:

1. Executive Summary with key findings and risk levels
2. Detailed assessment of Administrative Safeguards (§164.308)
3. Detailed assessment of Physical Safeguards (§164.310) 
4. Detailed assessment of Technical Safeguards (§164.312)
5. Risk analysis and business impact assessment
6. Specific remediation recommendations with timelines
7. Compliance scoring and gap analysis
8. Implementation roadmap with priorities

Format the response as a professional assessment report with clear sections, bullet points, and actionable recommendations. Include specific HIPAA regulation references where applicable.

Focus on practical, implementable recommendations that address the identified gaps and risks.
"""

    def _build_security_policy_prompt(self, context: DocumentContext) -> str:
        """Build prompt for security policy generation"""
        return f"""
You are a cybersecurity policy expert. Generate a comprehensive information security policy for:

Organization: {context.organization_name}
Compliance Requirements: {', '.join(context.compliance_frameworks)}
Business Context: {json.dumps(context.metadata, indent=2)}

Create a policy document that includes:

1. Policy Statement and Objectives
2. Scope and Applicability  
3. Roles and Responsibilities
4. Security Controls Framework
5. Risk Management Procedures
6. Incident Response Requirements
7. Compliance and Audit Requirements
8. Policy Enforcement and Violations
9. Training and Awareness Requirements
10. Policy Review and Update Procedures

Ensure the policy aligns with industry best practices and relevant compliance frameworks.
Make it specific to the organization's needs while maintaining broad applicability.
"""

    def _build_incident_response_prompt(self, context: DocumentContext) -> str:
        """Build prompt for incident response plan"""
        return f"""
Create a comprehensive incident response plan for {context.organization_name}.

Organization Details:
- Scope: {', '.join(context.assessment_scope)}
- Compliance Requirements: {', '.join(context.compliance_frameworks)}
- Context: {json.dumps(context.metadata, indent=2)}

Generate an incident response plan with:

1. Incident Response Team Structure and Roles
2. Incident Classification and Severity Levels
3. Detection and Analysis Procedures
4. Containment, Eradication, and Recovery Steps
5. Communication and Notification Procedures
6. Evidence Preservation and Forensics
7. Post-Incident Activities and Lessons Learned
8. Specific Procedures for Common Incident Types:
   - Data Breach
   - Malware Infection
   - Unauthorized Access
   - Denial of Service
   - Insider Threats
9. Contact Information and Escalation Matrix
10. Testing and Training Requirements

Include specific timelines, responsible parties, and decision criteria for each phase.
"""

    def _build_risk_assessment_prompt(self, context: DocumentContext) -> str:
        """Build prompt for risk assessment"""
        return f"""
Conduct a comprehensive cybersecurity risk assessment for {context.organization_name}.

Assessment Context:
- Scope: {', '.join(context.assessment_scope)}
- Current Risk Level: {context.risk_level}
- Identified Issues: {len(context.findings)} findings
- Business Context: {json.dumps(context.metadata, indent=2)}

Generate a risk assessment that includes:

1. Risk Assessment Methodology and Framework
2. Asset Inventory and Classification
3. Threat Landscape Analysis
4. Vulnerability Assessment Summary
5. Risk Analysis Matrix (Likelihood × Impact)
6. Risk Register with Detailed Risk Scenarios
7. Risk Treatment Recommendations
8. Residual Risk Analysis
9. Risk Monitoring and Review Procedures
10. Risk Communication and Reporting

For each identified risk, provide:
- Risk description and scenario
- Likelihood assessment (1-5 scale)
- Impact assessment (1-5 scale)  
- Current controls effectiveness
- Recommended additional controls
- Cost-benefit analysis for risk treatment

Present risks in order of priority with clear rationale for prioritization.
"""

    def _build_compliance_report_prompt(self, context: DocumentContext) -> str:
        """Build prompt for compliance report"""
        return f"""
Generate a comprehensive compliance report for {context.organization_name}.

Compliance Scope:
- Frameworks: {', '.join(context.compliance_frameworks)}
- Assessment Areas: {', '.join(context.assessment_scope)}
- Findings: {json.dumps(context.findings, indent=2)}

Create a compliance report with:

1. Executive Summary of Compliance Status
2. Compliance Framework Mapping and Requirements
3. Current Compliance Posture Assessment
4. Gap Analysis by Framework/Control Family
5. Detailed Finding Analysis with Evidence
6. Compliance Risk Assessment
7. Remediation Plan with Timelines and Resources
8. Ongoing Compliance Monitoring Recommendations
9. Compliance Metrics and KPIs
10. Next Steps and Continuous Improvement

Include specific compliance scores, gap percentages, and actionable recommendations for achieving and maintaining compliance.
"""

    def _build_vulnerability_report_prompt(self, context: DocumentContext) -> str:
        """Build prompt for vulnerability assessment report"""
        return f"""
Create a comprehensive vulnerability assessment report for {context.organization_name}.

Assessment Details:
- Scope: {', '.join(context.assessment_scope)}
- Findings: {json.dumps(context.findings, indent=2)}
- Context: {json.dumps(context.metadata, indent=2)}

Generate a vulnerability report with:

1. Executive Summary and Risk Overview
2. Assessment Methodology and Scope
3. Vulnerability Summary Statistics
4. Critical and High-Risk Vulnerabilities (Detailed)
5. Medium and Low-Risk Vulnerabilities (Summary)
6. Exploitation Scenarios and Business Impact
7. Remediation Recommendations by Priority
8. Compensating Controls Analysis
9. Vulnerability Trends and Patterns
10. Recommendations for Ongoing Vulnerability Management

For each critical/high vulnerability:
- Technical description and proof of concept
- CVSS score and risk rating
- Affected systems and potential impact
- Specific remediation steps
- Timeline for remediation
- Verification procedures

Include a risk-based prioritization matrix for remediation efforts.
"""

    async def _invoke_bedrock_model(self, model: BedrockModel, prompt: str) -> str:
        """Invoke the Bedrock model with the generated prompt"""

        config = self.model_config.get(
            model, self.model_config[BedrockModel.CLAUDE_3_SONNET]
        )

        if model in [
            BedrockModel.CLAUDE_3_SONNET,
            BedrockModel.CLAUDE_3_HAIKU,
            BedrockModel.CLAUDE_3_OPUS,
        ]:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": config["max_tokens"],
                "temperature": config["temperature"],
                "top_p": config["top_p"],
                "messages": [{"role": "user", "content": prompt}],
            }
        else:
            # Titan model format
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": config["max_tokens"],
                    "temperature": config["temperature"],
                    "topP": config["top_p"],
                },
            }

        try:
            response = self.bedrock_client.invoke_model(
                modelId=model.value, body=json.dumps(body)
            )

            response_body = json.loads(response["body"].read())

            if model in [
                BedrockModel.CLAUDE_3_SONNET,
                BedrockModel.CLAUDE_3_HAIKU,
                BedrockModel.CLAUDE_3_OPUS,
            ]:
                return response_body["content"][0]["text"]
            else:
                return response_body["results"][0]["outputText"]

        except Exception as e:
            logger.error(f"Error invoking Bedrock model {model.value}: {str(e)}")
            raise

    def _post_process_response(self, response: str, doc_type: DocumentType) -> str:
        """Post-process the model response"""

        # Add document metadata
        metadata = f"""
---
Document Type: {doc_type.value}
Generated: {datetime.now().isoformat()}
Generator: AWS Bedrock AI
Version: 1.0
---

"""

        # Clean up the response
        cleaned_response = response.strip()

        # Add any document-specific formatting
        if doc_type == DocumentType.HIPAA_ASSESSMENT:
            cleaned_response = self._format_hipaa_document(cleaned_response)
        elif doc_type == DocumentType.SECURITY_POLICY:
            cleaned_response = self._format_policy_document(cleaned_response)

        return metadata + cleaned_response

    def _format_hipaa_document(self, content: str) -> str:
        """Format HIPAA-specific document"""
        # Add HIPAA-specific formatting, disclaimers, etc.
        disclaimer = """
**HIPAA Compliance Disclaimer:** This assessment is based on available information and should be reviewed by qualified legal and compliance professionals. Compliance requirements may vary based on specific organizational circumstances.

"""
        return disclaimer + content

    def _format_policy_document(self, content: str) -> str:
        """Format policy document"""
        header = """
**CONFIDENTIAL - INTERNAL USE ONLY**

This document contains sensitive security information and should be handled according to the organization's information classification policy.

"""
        return header + content


# Example usage and validation functions
class DocumentValidator:
    """Validate generated documents for completeness and quality"""

    @staticmethod
    def validate_hipaa_assessment(document: str) -> Dict[str, Any]:
        """Validate HIPAA assessment document"""
        required_sections = [
            "Executive Summary",
            "Administrative Safeguards",
            "Physical Safeguards",
            "Technical Safeguards",
            "Risk Analysis",
            "Recommendations",
        ]

        validation_results = {
            "is_valid": True,
            "missing_sections": [],
            "quality_score": 0,
            "recommendations": [],
        }

        for section in required_sections:
            if section.lower() not in document.lower():
                validation_results["missing_sections"].append(section)
                validation_results["is_valid"] = False

        # Calculate quality score based on various factors
        word_count = len(document.split())
        if word_count < 1000:
            validation_results["quality_score"] = 50
            validation_results["recommendations"].append(
                "Document appears too short for comprehensive assessment"
            )
        elif word_count > 5000:
            validation_results["quality_score"] = 95
        else:
            validation_results["quality_score"] = 75

        return validation_results


# Example implementation
async def generate_hipaa_assessment_example():
    """Example of generating a HIPAA assessment report"""

    # Initialize the generator
    doc_generator = BedrockDocumentationGenerator()

    # Create context
    context = DocumentContext(
        organization_name="Acme Healthcare Corp",
        assessment_scope=["AWS Infrastructure", "Web Applications", "Database Systems"],
        compliance_frameworks=["HIPAA", "SOC 2"],
        risk_level="Medium",
        findings=[
            {
                "id": "F001",
                "severity": "High",
                "title": "Unencrypted Data Storage",
                "description": "Patient data stored without encryption",
                "affected_systems": ["Database Server"],
                "cvss_score": 7.5,
            },
            {
                "id": "F002",
                "severity": "Medium",
                "title": "Weak Password Policy",
                "description": "Password policy does not meet HIPAA requirements",
                "affected_systems": ["All Systems"],
                "cvss_score": 5.3,
            },
        ],
        metadata={
            "assessment_date": "2024-01-15",
            "assessor": "Security Team",
            "previous_assessment": "2023-01-15",
        },
    )

    # Generate the document
    try:
        hipaa_report = await doc_generator.generate_document(
            DocumentType.HIPAA_ASSESSMENT, context, BedrockModel.CLAUDE_3_SONNET
        )

        # Validate the document
        validator = DocumentValidator()
        validation_results = validator.validate_hipaa_assessment(hipaa_report)

        print(f"Document generated successfully!")
        print(f"Validation Results: {validation_results}")

        return hipaa_report

    except Exception as e:
        print(f"Error generating document: {str(e)}")
        return None


if __name__ == "__main__":
    # Run the example
    asyncio.run(generate_hipaa_assessment_example())
