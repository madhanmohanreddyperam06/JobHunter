'use strict';

/**
 * priority-badge Directive
 * Usage: <priority-badge priority="task.priority"></priority-badge>
 * Displays priority badges: LOW, MEDIUM, HIGH, URGENT
 */
angular.module('jobCommandCenter')
.directive('priorityBadge', function() {
  return {
    restrict: 'E',
    scope: {
      priority: '='
    },
    template:
      '<span class="app-priority-badge" ng-class="getPriorityClass()">' +
      '  <i class="bi" ng-class="getIconClass()"></i>&nbsp;' +
      '  <span>{{ priority || \'LOW\' }}</span>' +
      '</span>',
    link: function(scope) {
      scope.getPriorityClass = function() {
        var p = (scope.priority || 'LOW').toUpperCase();
        switch (p) {
          case 'URGENT':
            return 'priority-urgent';
          case 'HIGH':
            return 'priority-high';
          case 'MEDIUM':
            return 'priority-medium';
          case 'LOW':
          default:
            return 'priority-low';
        }
      };

      scope.getIconClass = function() {
        var p = (scope.priority || 'LOW').toUpperCase();
        switch (p) {
          case 'URGENT':
            return 'bi-exclamation-octagon-fill';
          case 'HIGH':
            return 'bi-arrow-up-circle-fill';
          case 'MEDIUM':
            return 'bi-dash-circle-fill';
          case 'LOW':
          default:
            return 'bi-arrow-down-circle-fill';
        }
      };
    }
  };
});
