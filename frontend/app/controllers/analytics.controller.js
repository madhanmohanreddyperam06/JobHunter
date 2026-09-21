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

  AnalyticsService.getDashboardStats()
    .then(function(data) {
      vm.stats = data;
      vm.isLoading = false;
    })
    .catch(function(err) {
      console.error('Failed to load analytics:', err);
      vm.isLoading = false;
    });
}]);
