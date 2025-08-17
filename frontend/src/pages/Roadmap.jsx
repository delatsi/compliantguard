import React, { useState, useEffect } from 'react';
import { roadmapAPI } from '../services/api';

const Roadmap = () => {
  const [roadmapData, setRoadmapData] = useState(null);
  const [progressSummary, setProgressSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPhase, setSelectedPhase] = useState('phase_1');
  const [updatingMilestone, setUpdatingMilestone] = useState(null);

  useEffect(() => {
    fetchRoadmapData();
    fetchProgressSummary();
  }, []);

  const fetchRoadmapData = async () => {
    try {
      setLoading(true);
      const response = await roadmapAPI.getRoadmap();
      setRoadmapData(response.data);
    } catch (err) {
      console.error('Failed to load roadmap:', err);
      setError('Failed to load compliance roadmap');
    } finally {
      setLoading(false);
    }
  };

  const fetchProgressSummary = async () => {
    try {
      const response = await roadmapAPI.getProgressSummary();
      setProgressSummary(response.data);
    } catch (err) {
      console.error('Failed to load progress summary:', err);
    }
  };

  const handleMilestoneUpdate = async (milestoneId, newStatus, notes = '') => {
    try {
      setUpdatingMilestone(milestoneId);
      await roadmapAPI.updateMilestone(milestoneId, newStatus, notes);
      
      // Refresh data
      await fetchRoadmapData();
      await fetchProgressSummary();
    } catch (err) {
      console.error('Failed to update milestone:', err);
      alert('Failed to update milestone progress');
    } finally {
      setUpdatingMilestone(null);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50 border-green-200';
      case 'in_progress': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'blocked': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getMaturityLevelColor = (level) => {
    switch (level) {
      case 'advanced': return 'text-green-700 bg-green-100';
      case 'intermediate': return 'text-blue-700 bg-blue-100';
      case 'developing': return 'text-yellow-700 bg-yellow-100';
      case 'basic': return 'text-orange-700 bg-orange-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading compliance roadmap...</p>
        </div>
      </div>
    );
  }

  if (error || !roadmapData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Unable to Load Roadmap</h2>
          <p className="text-gray-600 mb-4">{error || 'Something went wrong'}</p>
          <button 
            onClick={() => window.location.reload()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const { roadmap, user_progress } = roadmapData;
  const phases = Object.entries(roadmap);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            HIPAA Compliance Roadmap
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            Your comprehensive guide to achieving and maintaining HIPAA compliance. 
            Track your progress through each phase of implementation.
          </p>

          {/* Progress Overview */}
          {user_progress && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Overall Progress</h2>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getMaturityLevelColor(user_progress.maturity_level)}`}>
                  {user_progress.maturity_level.charAt(0).toUpperCase() + user_progress.maturity_level.slice(1)} Level
                </span>
              </div>
              
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>{user_progress.completed_milestones} of {user_progress.total_milestones} milestones completed</span>
                  <span>{user_progress.progress_percentage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${user_progress.progress_percentage}%` }}
                  ></div>
                </div>
              </div>

              {progressSummary && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {progressSummary.overall_progress.in_progress_milestones}
                    </div>
                    <div className="text-gray-600">In Progress</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {progressSummary.overall_progress.completed_milestones}
                    </div>
                    <div className="text-gray-600">Completed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {progressSummary.overall_progress.estimated_hours_remaining}h
                    </div>
                    <div className="text-gray-600">Est. Remaining</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Phase Navigation */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 overflow-x-auto">
              {phases.map(([phaseKey, phase]) => {
                const phaseProgress = progressSummary?.phase_progress?.[phaseKey];
                const isActive = selectedPhase === phaseKey;
                
                return (
                  <button
                    key={phaseKey}
                    onClick={() => setSelectedPhase(phaseKey)}
                    className={`whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm ${
                      isActive
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span>{phase.name}</span>
                      {phaseProgress && (
                        <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
                          {phaseProgress.completed_milestones}/{phaseProgress.total_milestones}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Selected Phase Content */}
        {selectedPhase && roadmap[selectedPhase] && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {roadmap[selectedPhase].name}
                  </h2>
                  <p className="text-gray-600 mb-4">
                    {roadmap[selectedPhase].description}
                  </p>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span className="flex items-center">
                      📅 {roadmap[selectedPhase].timeline}
                    </span>
                    <span className="flex items-center">
                      📋 {roadmap[selectedPhase].milestones.length} milestones
                    </span>
                  </div>
                </div>
                
                {progressSummary?.phase_progress?.[selectedPhase] && (
                  <div className="text-right">
                    <div className="text-2xl font-bold text-blue-600">
                      {Math.round(progressSummary.phase_progress[selectedPhase].progress_percentage)}%
                    </div>
                    <div className="text-sm text-gray-500">Complete</div>
                  </div>
                )}
              </div>
            </div>

            {/* Milestones */}
            <div className="p-6">
              <div className="space-y-4">
                {roadmap[selectedPhase].milestones.map((milestone, index) => {
                  const isUpdating = updatingMilestone === milestone.id;
                  
                  return (
                    <div
                      key={milestone.id}
                      className={`border border-gray-200 rounded-lg p-4 ${getStatusColor(milestone.status || 'pending')}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <span className="flex-shrink-0 w-8 h-8 bg-white rounded-full flex items-center justify-center text-sm font-medium border">
                              {index + 1}
                            </span>
                            <h3 className="text-lg font-semibold text-gray-900">
                              {milestone.title}
                              {milestone.required && (
                                <span className="ml-2 text-red-500 text-sm">*Required</span>
                              )}
                            </h3>
                          </div>
                          
                          <p className="text-gray-600 mb-3 ml-11">
                            {milestone.description}
                          </p>
                          
                          <div className="flex items-center space-x-4 text-sm text-gray-500 ml-11">
                            <span>⏱️ ~{milestone.estimated_hours}h</span>
                            {milestone.completion_date && (
                              <span>✅ Completed: {new Date(milestone.completion_date).toLocaleDateString()}</span>
                            )}
                            {milestone.started_date && !milestone.completion_date && (
                              <span>🚀 Started: {new Date(milestone.started_date).toLocaleDateString()}</span>
                            )}
                          </div>
                          
                          {milestone.notes && (
                            <div className="mt-2 ml-11 text-sm text-gray-600 bg-white bg-opacity-50 p-2 rounded">
                              📝 {milestone.notes}
                            </div>
                          )}
                        </div>

                        {/* Status Controls */}
                        <div className="flex-shrink-0 ml-4">
                          <div className="flex items-center space-x-2">
                            <select
                              value={milestone.status || 'pending'}
                              onChange={(e) => handleMilestoneUpdate(milestone.id, e.target.value)}
                              disabled={isUpdating}
                              className="text-sm border border-gray-300 rounded px-2 py-1 bg-white"
                            >
                              <option value="pending">Pending</option>
                              <option value="in_progress">In Progress</option>
                              <option value="completed">Completed</option>
                              <option value="blocked">Blocked</option>
                            </select>
                            
                            {isUpdating && (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Maturity Assessment */}
        {progressSummary?.maturity_assessment && (
          <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Compliance Maturity Assessment</h2>
            <div className="flex items-start space-x-4">
              <div className={`px-4 py-2 rounded-lg ${getMaturityLevelColor(progressSummary.maturity_assessment.level)}`}>
                <div className="font-semibold text-lg">
                  {progressSummary.maturity_assessment.level.charAt(0).toUpperCase() + progressSummary.maturity_assessment.level.slice(1)} Level
                </div>
              </div>
              <div className="flex-1">
                <p className="text-gray-600">
                  {progressSummary.maturity_assessment.description}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Roadmap;