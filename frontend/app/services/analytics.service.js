'use strict';

/**
 * AnalyticsService
 * Provides aggregated metrics, funnel conversion stats, and performance indicators.
 */
angular.module('jobCommandCenter')
.factory('AnalyticsService', ['$q', function($q) {
  return {
    /**
     * Retrieve high-level dashboard metrics
     * Values match Section 11 specifications:
     * - Applications: 42
     * - Assessments: 12
     * - Interviews: 8
     * - Offers: 2
     * @returns {Promise<Object>}
     */
    getDashboardStats: function() {
      var stats = {
        applications: 42,
        assessments: 12,
        interviews: 8,
        offers: 2,
        saved: 15,
        rejected: 16
      };
      return $q.resolve(stats);
    },

    /**
     * Retrieve application statistics and conversion funnel breakdown
     * @returns {Promise<Object>}
     */
    getApplicationStatistics: function() {
      var data = {
        pipelineFunnel: [
          { stage: 'Applied', count: 42, percentage: '100%' },
          { stage: 'Assessments', count: 12, percentage: '28.5%' },
          { stage: 'Interviews', count: 8, percentage: '19.0%' },
          { stage: 'Offers', count: 2, percentage: '4.8%' }
        ],
        monthlyTrends: [
          { month: 'Jun', count: 6 },
          { month: 'Jul', count: 10 },
          { month: 'Aug', count: 14 },
          { month: 'Sep', count: 12 }
        ]
      };
      return $q.resolve(data);
    },

    /**
     * Retrieve resume match statistics
     * @returns {Promise<Object>}
     */
    getResumeStatistics: function() {
      var data = {
        totalResumes: 3,
        primaryResume: 'FullStack_Engineer_2026.pdf',
        averageMatchScore: 84
      };
      return $q.resolve(data);
    }
  };
}]);
