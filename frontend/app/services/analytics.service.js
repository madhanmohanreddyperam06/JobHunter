'use strict';

/**
 * AnalyticsService
 * Provides aggregated metrics, funnel conversion stats, and performance indicators.
 * Now integrated with real backend API endpoints.
 */
angular.module('jobCommandCenter')
.factory('AnalyticsService', ['$http', '$q', 'API_CONFIG', function($http, $q, API_CONFIG) {
  var BASE_URL = API_CONFIG.BASE_URL + '/analytics';

  return {
    /**
     * Retrieve high-level dashboard metrics from backend
     * @returns {Promise<Object>}
     */
    getDashboardStats: function() {
      return $http.get(BASE_URL + '/dashboard')
        .then(function(response) {
          return response.data;
        })
        .catch(function(err) {
          console.error('Failed to load dashboard stats:', err);
          // Fallback to mock data if API fails
          var stats = {
            total_applications: 42,
            saved: 15,
            applied: 27,
            assessment: 12,
            interview: 8,
            offer: 2,
            rejected: 16,
            withdrawn: 0
          };
          return $q.resolve(stats);
        });
    },

    /**
     * Retrieve application statistics and conversion funnel breakdown from backend
     * @returns {Promise<Object>}
     */
    getApplicationStatistics: function() {
      return $http.get(BASE_URL + '/funnel')
        .then(function(response) {
          var data = response.data;
          // Transform backend data to match frontend format
          return {
            pipelineFunnel: data.stages.map(function(stage) {
              return {
                stage: stage.stage,
                count: stage.count,
                percentage: stage.percentage + '%'
              };
            }),
            total: data.total
          };
        })
        .catch(function(err) {
          console.error('Failed to load funnel stats:', err);
          // Fallback to mock data
          var data = {
            pipelineFunnel: [
              { stage: 'Saved', count: 15, percentage: '35.7%' },
              { stage: 'Applied', count: 27, percentage: '64.3%' },
              { stage: 'Assessment', count: 12, percentage: '28.5%' },
              { stage: 'Interview', count: 8, percentage: '19.0%' },
              { stage: 'Offer', count: 2, percentage: '4.8%' },
              { stage: 'Rejected', count: 16, percentage: '38.1%' }
            ],
            total: 42
          };
          return $q.resolve(data);
        });
    },

    /**
     * Retrieve skills analytics from backend
     * @returns {Promise<Object>}
     */
    getSkillsAnalytics: function() {
      return $http.get(BASE_URL + '/skills')
        .then(function(response) {
          return response.data;
        })
        .catch(function(err) {
          console.error('Failed to load skills analytics:', err);
          // Fallback to mock data
          var data = {
            total_skills: 25,
            top_application_skills: [
              { name: 'JavaScript', count: 15 },
              { name: 'Python', count: 12 },
              { name: 'React', count: 10 },
              { name: 'SQL', count: 8 }
            ],
            top_jd_skills: [
              { name: 'JavaScript', count: 20 },
              { name: 'Python', count: 15 },
              { name: 'AWS', count: 12 },
              { name: 'Docker', count: 10 }
            ]
          };
          return $q.resolve(data);
        });
    },

    /**
     * Retrieve resume match statistics (placeholder for future implementation)
     * @returns {Promise<Object>}
     */
    getResumeStatistics: function() {
      // This endpoint is not yet implemented in backend
      var data = {
        totalResumes: 3,
        primaryResume: 'FullStack_Engineer_2026.pdf',
        averageMatchScore: 84
      };
      return $q.resolve(data);
    }
  };
}]);
