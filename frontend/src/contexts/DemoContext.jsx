import React, { createContext, useContext, useState } from 'react';

const DemoContext = createContext();

export const useDemoData = () => {
  const context = useContext(DemoContext);
  if (!context) {
    throw new Error('useDemoData must be used within a DemoProvider');
  }
  return context;
};

export const DemoProvider = ({ children }) => {
  const [isDemoMode, setIsDemoMode] = useState(false);

  // Comprehensive demo data
  const demoData = {
    user: {
      user_id: 'demo-user-123',
      email: 'demo@company.com',
      first_name: 'Demo',
      last_name: 'User',
      company: 'Acme Healthcare Corp',
      plan: 'Professional',
      subscription_status: 'active'
    },

    dashboardStats: {
      total_scans: 47,
      total_projects: 8,
      overall_compliance_score: 87.3,
      last_scan_date: '2024-01-15T14:30:00Z',
      violation_summary: {
        total_violations: 25,
        critical_violations: 2,
        high_violations: 8,
        medium_violations: 12,
        low_violations: 3
      },
      monthly_scans: [
        { month: 'Jan', scans: 12 },
        { month: 'Feb', scans: 18 },
        { month: 'Mar', scans: 15 },
        { month: 'Apr', scans: 22 },
        { month: 'May', scans: 19 },
        { month: 'Jun', scans: 25 }
      ]
    },

    recentScans: [
      {
        scan_id: 'scan-001',
        project_id: 'production-healthcare-app',
        project_name: 'Production Healthcare App',
        scan_timestamp: '2024-01-15T14:30:00Z',
        total_violations: 10,
        compliance_score: 92,
        status: 'completed',
        duration: '2m 34s'
      },
      {
        scan_id: 'scan-002',
        project_id: 'staging-patient-portal',
        project_name: 'Staging Patient Portal',
        scan_timestamp: '2024-01-14T09:15:00Z',
        total_violations: 15,
        compliance_score: 78,
        status: 'completed',
        duration: '1m 52s'
      },
      {
        scan_id: 'scan-003',
        project_id: 'dev-analytics-pipeline',
        project_name: 'Dev Analytics Pipeline',
        scan_timestamp: '2024-01-13T16:45:00Z',
        total_violations: 12,
        compliance_score: 85,
        status: 'completed',
        duration: '3m 18s'
      },
      {
        scan_id: 'scan-004',
        project_id: 'backup-storage-system',
        project_name: 'Backup Storage System',
        scan_timestamp: '2024-01-12T11:20:00Z',
        total_violations: 5,
        compliance_score: 95,
        status: 'completed',
        duration: '1m 15s'
      }
    ],

    detailedReports: [
      {
        scan_id: 'scan-001',
        project_id: 'production-healthcare-app',
        project_name: 'Production Healthcare App',
        scan_timestamp: '2024-01-15T14:30:00Z',
        compliance_score: 92,
        total_violations: 10,
        critical_violations: 1,
        high_violations: 2,
        medium_violations: 5,
        low_violations: 2,
        status: 'completed',
        violations: [
          {
            id: 'viol-001',
            type: 'hipaa_violation',
            severity: 'critical',
            title: 'Storage bucket allows public access',
            description: 'Storage bucket "patient-data-backup" allows public access, violating HIPAA access controls (§164.312)',
            resource_type: 'storage.bucket',
            resource_name: 'patient-data-backup',
            hipaa_section: '§164.312(a)(1)',
            remediation_steps: [
              'Remove public access permissions from bucket',
              'Implement bucket-level IAM policies',
              'Enable uniform bucket-level access',
              'Review and audit bucket permissions regularly'
            ],
            risk_level: 'High',
            estimated_fix_time: '30 minutes'
          },
          {
            id: 'viol-002',
            type: 'hipaa_violation',
            severity: 'high',
            title: 'Firewall rule allows unrestricted SSH access',
            description: 'Firewall rule "default-allow-ssh" allows unrestricted access to port 22 from any IP address',
            resource_type: 'compute.firewall',
            resource_name: 'default-allow-ssh',
            hipaa_section: '§164.312(a)(2)',
            remediation_steps: [
              'Restrict SSH access to specific IP ranges',
              'Implement VPN-based access',
              'Use Identity-Aware Proxy for secure access',
              'Enable firewall logging'
            ],
            risk_level: 'High',
            estimated_fix_time: '15 minutes'
          },
          {
            id: 'viol-003',
            type: 'hipaa_review_required',
            severity: 'medium',
            title: 'Service account has excessive permissions',
            description: 'Service account "app-service-account" has broader permissions than necessary for minimum access',
            resource_type: 'iam.serviceAccount',
            resource_name: 'app-service-account@project.iam.gserviceaccount.com',
            hipaa_section: '§164.308(a)(4)',
            remediation_steps: [
              'Review current service account permissions',
              'Apply principle of least privilege',
              'Create role-specific service accounts',
              'Implement regular access reviews'
            ],
            risk_level: 'Medium',
            estimated_fix_time: '45 minutes'
          },
          {
            id: 'viol-004',
            type: 'compliance_gap',
            severity: 'medium',
            title: 'Environment Separation Violation',
            description: 'Compute instance "web-server-01" lacks proper environment tagging (dev/staging/prod). Required for HIPAA Administrative Safeguards and SOC 2 Security controls.',
            resource_type: 'compute.instance',
            resource_name: 'web-server-01',
            hipaa_section: '§164.308(a)(3)',
            remediation_steps: [
              'Implement environment tagging strategy (dev/staging/prod)',
              'Create environment-specific resource naming conventions',
              'Apply consistent labels to all cloud resources',
              'Set up automated tagging policies and compliance monitoring',
              'Document environment classification procedures'
            ],
            risk_level: 'Medium',
            estimated_fix_time: '30 minutes'
          },
          {
            id: 'viol-005',
            type: 'compliance_gap',
            severity: 'medium',
            title: 'Environment Separation Violation',
            description: 'Storage bucket "app-data-store" lacks proper environment tagging (dev/staging/prod). Required for data classification and access controls.',
            resource_type: 'storage.bucket',
            resource_name: 'app-data-store',
            hipaa_section: 'SOC 2 CC6.1',
            remediation_steps: [
              'Implement environment tagging strategy (dev/staging/prod)',
              'Create environment-specific resource naming conventions',
              'Apply consistent labels to all cloud resources',
              'Set up automated tagging policies and compliance monitoring',
              'Document environment classification procedures'
            ],
            risk_level: 'Medium',
            estimated_fix_time: '20 minutes'
          }
        ]
      }
    ],

    projects: [
      {
        id: 'production-healthcare-app',
        name: 'Production Healthcare App',
        environment: 'production',
        last_scan: '2024-01-15T14:30:00Z',
        compliance_score: 92,
        violations: 10,
        status: 'active'
      },
      {
        id: 'staging-patient-portal',
        name: 'Staging Patient Portal',
        environment: 'staging',
        last_scan: '2024-01-14T09:15:00Z',
        compliance_score: 78,
        violations: 15,
        status: 'active'
      },
      {
        id: 'dev-analytics-pipeline',
        name: 'Dev Analytics Pipeline',
        environment: 'development',
        last_scan: '2024-01-13T16:45:00Z',
        compliance_score: 85,
        violations: 12,
        status: 'active'
      },
      {
        id: 'backup-storage-system',
        name: 'Backup Storage System',
        environment: 'production',
        last_scan: '2024-01-12T11:20:00Z',
        compliance_score: 95,
        violations: 5,
        status: 'active'
      }
    ],

    complianceMetrics: {
      trendsData: [
        { date: '2024-01-01', score: 82 },
        { date: '2024-01-02', score: 84 },
        { date: '2024-01-03', score: 83 },
        { date: '2024-01-04', score: 86 },
        { date: '2024-01-05', score: 88 },
        { date: '2024-01-06', score: 87 },
        { date: '2024-01-07', score: 89 },
        { date: '2024-01-08', score: 90 },
        { date: '2024-01-09', score: 88 },
        { date: '2024-01-10', score: 91 },
        { date: '2024-01-11', score: 89 },
        { date: '2024-01-12', score: 92 },
        { date: '2024-01-13', score: 90 },
        { date: '2024-01-14', score: 87 },
        { date: '2024-01-15', score: 92 }
      ],
      
      violationsByCategory: [
        { category: 'Access Controls', count: 8, percentage: 32 },
        { category: 'Environment Separation', count: 6, percentage: 24 },
        { category: 'Data Encryption', count: 5, percentage: 20 },
        { category: 'Network Security', count: 4, percentage: 16 },
        { category: 'Audit Logging', count: 2, percentage: 8 }
      ]
    }
  };

  const enterDemoMode = () => {
    setIsDemoMode(true);
    localStorage.setItem('demo_mode', 'true');
  };

  const exitDemoMode = () => {
    setIsDemoMode(false);
    localStorage.removeItem('demo_mode');
  };

  const value = {
    isDemoMode,
    demoData,
    enterDemoMode,
    exitDemoMode
  };

  return (
    <DemoContext.Provider value={value}>
      {children}
    </DemoContext.Provider>
  );
};