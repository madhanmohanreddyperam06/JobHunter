'use strict';

/**
 * status-badge Directive
 * Usage: <status-badge status="job.status"></status-badge>
 * Displays semantic status pills with distinct colors and icons.
 */
angular.module('jobCommandCenter')
.directive('statusBadge', function() {
  return {
    restrict: 'E',
    scope: {
      status: '='
    },
    template:
      '<span class="app-status-badge" ng-class="getBadgeClass()">' +
      '  <i class="bi" ng-class="getIconClass()"></i>' +
      '  <span>{{ status | statusLabel }}</span>' +
      '</span>',
    link: function(scope) {
      scope.getBadgeClass = function() {
        var s = (scope.status || '').toUpperCase();
        switch (s) {
          case 'APPLIED':
            return 'status-applied';
          case 'ASSESSMENT':
            return 'status-assessment';
          case 'INTERVIEW':
            return 'status-interview';
          case 'OFFER':
            return 'status-offer';
          case 'REJECTED':
            return 'status-rejected';
          case 'SAVED':
          default:
            return 'status-saved';
        }
      };

      scope.getIconClass = function() {
        var s = (scope.status || '').toUpperCase();
        switch (s) {
          case 'APPLIED':
            return 'bi-send-fill';
          case 'ASSESSMENT':
            return 'bi-pencil-square';
          case 'INTERVIEW':
            return 'bi-calendar-check-fill';
          case 'OFFER':
            return 'bi-trophy-fill';
          case 'REJECTED':
            return 'bi-x-circle-fill';
          case 'SAVED':
          default:
            return 'bi-bookmark-fill';
        }
      };
    }
  };
});
