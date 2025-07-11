import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useDemoData } from '../contexts/DemoContext';
import { 
  DocumentTextIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  FolderIcon,
  DocumentArrowUpIcon,
  CodeBracketIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  ArrowPathIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const Documentation = () => {
  const location = useLocation();
  const { demoData } = useDemoData();
  const isDemoMode = location.pathname.startsWith('/demo');
  
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('updated');

  // Demo documentation data
  const documentCategories = [
    { id: 'all', name: 'All Documents', count: 24 },
    { id: 'policies', name: 'Security Policies', count: 8 },
    { id: 'assessments', name: 'Risk Assessments', count: 5 },
    { id: 'procedures', name: 'Procedures', count: 6 },
    { id: 'compliance', name: 'Compliance Reports', count: 3 },
    { id: 'templates', name: 'Templates', count: 2 }
  ];

  const demoDocuments = [
    {
      id: 'doc-001',
      title: 'HIPAA Risk Assessment 2024',
      category: 'assessments',
      type: 'Risk Assessment',
      status: 'published',
      lastModified: '2024-01-15T10:30:00Z',
      author: 'Security Team',
      size: '2.1 MB',
      description: 'Comprehensive HIPAA risk assessment covering all administrative, physical, and technical safeguards.',
      tags: ['HIPAA', 'Risk Assessment', 'Compliance'],
      githubPath: 'docs/assessments/hipaa-risk-assessment-2024.md',
      syncStatus: 'synced'
    },
    {
      id: 'doc-002',
      title: 'Information Security Policy',
      category: 'policies',
      type: 'Security Policy',
      status: 'published',
      lastModified: '2024-01-10T14:20:00Z',
      author: 'CISO',
      size: '1.8 MB',
      description: 'Organization-wide information security policy defining roles, responsibilities, and security controls.',
      tags: ['Security Policy', 'Governance', 'ISO 27001'],
      githubPath: 'docs/policies/information-security-policy.md',
      syncStatus: 'synced'
    },
    {
      id: 'doc-003',
      title: 'Incident Response Playbook',
      category: 'procedures',
      type: 'Procedure',
      status: 'draft',
      lastModified: '2024-01-14T09:15:00Z',
      author: 'Incident Response Team',
      size: '3.2 MB',
      description: 'Detailed procedures for responding to various types of security incidents.',
      tags: ['Incident Response', 'Procedures', 'Security Operations'],
      githubPath: 'docs/procedures/incident-response-playbook.md',
      syncStatus: 'pending'
    },
    {
      id: 'doc-004',
      title: 'SOC 2 Compliance Report',
      category: 'compliance',
      type: 'Compliance Report',
      status: 'published',
      lastModified: '2024-01-08T16:45:00Z',
      author: 'Compliance Officer',
      size: '4.7 MB',
      description: 'SOC 2 Type II compliance assessment report with findings and remediation plans.',
      tags: ['SOC 2', 'Compliance', 'Audit'],
      githubPath: 'docs/compliance/soc2-compliance-report.md',
      syncStatus: 'synced'
    },
    {
      id: 'doc-005',
      title: 'Vulnerability Assessment Template',
      category: 'templates',
      type: 'Template',
      status: 'published',
      lastModified: '2024-01-05T11:30:00Z',
      author: 'Security Team',
      size: '856 KB',
      description: 'Standardized template for conducting and documenting vulnerability assessments.',
      tags: ['Template', 'Vulnerability Assessment', 'Security Testing'],
      githubPath: 'docs/templates/vulnerability-assessment-template.md',
      syncStatus: 'synced'
    },
    {
      id: 'doc-006',
      title: 'Access Control Procedures',
      category: 'procedures',
      type: 'Procedure',
      status: 'review',
      lastModified: '2024-01-12T13:20:00Z',
      author: 'IT Security',
      size: '1.4 MB',
      description: 'Detailed procedures for user access provisioning, modification, and deprovisioning.',
      tags: ['Access Control', 'Procedures', 'Identity Management'],
      githubPath: 'docs/procedures/access-control-procedures.md',
      syncStatus: 'conflict'
    }
  ];

  const filteredDocuments = demoDocuments.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === 'all' || doc.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const sortedDocuments = [...filteredDocuments].sort((a, b) => {
    switch (sortBy) {
      case 'title':
        return a.title.localeCompare(b.title);
      case 'updated':
        return new Date(b.lastModified) - new Date(a.lastModified);
      case 'author':
        return a.author.localeCompare(b.author);
      default:
        return 0;
    }
  });

  const getStatusBadge = (status) => {
    const badges = {
      published: { color: 'bg-green-100 text-green-800', text: 'Published' },
      draft: { color: 'bg-yellow-100 text-yellow-800', text: 'Draft' },
      review: { color: 'bg-blue-100 text-blue-800', text: 'Under Review' },
      archived: { color: 'bg-gray-100 text-gray-800', text: 'Archived' }
    };
    return badges[status] || badges.draft;
  };

  const getSyncStatusIcon = (syncStatus) => {
    switch (syncStatus) {
      case 'synced':
        return <CheckCircleIcon className="h-4 w-4 text-green-500" title="Synced with GitHub" />;
      case 'pending':
        return <ClockIcon className="h-4 w-4 text-yellow-500" title="Sync Pending" />;
      case 'conflict':
        return <ExclamationTriangleIcon className="h-4 w-4 text-red-500" title="Sync Conflict" />;
      default:
        return <ArrowPathIcon className="h-4 w-4 text-gray-400" title="Not Synced" />;
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Documentation Portal
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage security documentation, policies, and compliance reports
          </p>
        </div>
        <div className="mt-4 flex space-x-3 md:mt-0 md:ml-4">
          <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <CloudArrowUpIcon className="h-4 w-4 mr-2" />
            Sync with GitHub
          </button>
          <button className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700">
            <PlusIcon className="h-4 w-4 mr-2" />
            New Document
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {isDemoMode && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DocumentTextIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Documents</dt>
                    <dd className="text-lg font-medium text-gray-900">24</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckCircleIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Published</dt>
                    <dd className="text-lg font-medium text-gray-900">18</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CloudArrowUpIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">GitHub Synced</dt>
                    <dd className="text-lg font-medium text-gray-900">22</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ClockIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Last Updated</dt>
                    <dd className="text-lg font-medium text-gray-900">Today</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar - Categories and Filters */}
        <div className="lg:col-span-1">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Categories</h3>
            <nav className="space-y-2">
              {documentCategories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`w-full text-left flex items-center justify-between px-3 py-2 text-sm rounded-md transition-colors ${
                    selectedCategory === category.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center">
                    <FolderIcon className="h-4 w-4 mr-2" />
                    <span>{category.name}</span>
                  </div>
                  <span className="text-xs text-gray-500">{category.count}</span>
                </button>
              ))}
            </nav>

            {/* Quick Actions */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Quick Actions</h4>
              <div className="space-y-2">
                <button className="w-full text-left flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md">
                  <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
                  Generate Report
                </button>
                <button className="w-full text-left flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md">
                  <CodeBracketIcon className="h-4 w-4 mr-2" />
                  View Templates
                </button>
                <button className="w-full text-left flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md">
                  <ArrowPathIcon className="h-4 w-4 mr-2" />
                  Sync All
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content - Document List */}
        <div className="lg:col-span-3">
          {/* Search and Sort */}
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search documents..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <label className="text-sm font-medium text-gray-700">Sort by:</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="updated">Last Updated</option>
                  <option value="title">Title</option>
                  <option value="author">Author</option>
                </select>
              </div>
            </div>
          </div>

          {/* Document List */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Documents ({sortedDocuments.length})
              </h3>
            </div>
            
            <div className="divide-y divide-gray-200">
              {sortedDocuments.map((doc) => {
                const statusBadge = getStatusBadge(doc.status);
                return (
                  <div key={doc.id} className="p-6 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="text-lg font-medium text-gray-900 truncate">
                            {doc.title}
                          </h4>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusBadge.color}`}>
                            {statusBadge.text}
                          </span>
                          {getSyncStatusIcon(doc.syncStatus)}
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                          {doc.description}
                        </p>
                        
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>Updated {formatDate(doc.lastModified)}</span>
                          <span>by {doc.author}</span>
                          <span>{doc.size}</span>
                          <span className="text-blue-600 hover:text-blue-800">
                            {doc.githubPath}
                          </span>
                        </div>
                        
                        <div className="flex flex-wrap gap-1 mt-3">
                          {doc.tags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-md"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md">
                          <EyeIcon className="h-4 w-4" title="View" />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md">
                          <PencilIcon className="h-4 w-4" title="Edit" />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md">
                          <TrashIcon className="h-4 w-4" title="Delete" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {sortedDocuments.length === 0 && (
              <div className="text-center py-12">
                <DocumentTextIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No documents found
                </h3>
                <p className="text-gray-500 mb-6">
                  {searchTerm || selectedCategory !== 'all' 
                    ? 'Try adjusting your search or filter criteria.'
                    : 'Get started by creating your first document.'
                  }
                </p>
                <button className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700">
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Create Document
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Documentation;