'use strict';

/**
 * AnalyticsController
 * Coordinator for job search metrics, funnel conversions, and response times.
 */
angular.module('jobCommandCenter')
.controller('AnalyticsController', ['AnalyticsService', function(AnalyticsService) {
  var vm = this;

  vm.isLoading = true;
  vm.stats = {};
  vm.funnelData = {};
  vm.skillsData = {};
  vm.resumeData = {};

  // Load dashboard stats
  AnalyticsService.getDashboardStats()
    .then(function(data) {
      vm.stats = data;
    })
    .catch(function(err) {
      console.error('Failed to load dashboard stats:', err);
    });

  // Load funnel analytics
  AnalyticsService.getApplicationStatistics()
    .then(function(data) {
      vm.funnelData = data;
    })
    .catch(function(err) {
      console.error('Failed to load funnel stats:', err);
    });

  // Load skills analytics
  AnalyticsService.getSkillsAnalytics()
    .then(function(data) {
      vm.skillsData = data;
    })
    .catch(function(err) {
      console.error('Failed to load skills analytics:', err);
    });

  // Load resume statistics
  AnalyticsService.getResumeStatistics()
    .then(function(data) {
      vm.resumeData = data;
      vm.isLoading = false;
    })
    .catch(function(err) {
      console.error('Failed to load resume stats:', err);
      vm.isLoading = false;
    });
}]);
