'use strict';

/**
 * statCard Component
 * Displays a single KPI summary metric tile with an icon, count, and title.
 */
angular.module('jobCommandCenter')
.component('statCard', {
  bindings: {
    title: '@',
    count: '<',
    icon: '@',
    color: '@',
    subtitle: '@'
  },
  templateUrl: 'app/components/stat-card/stat-card.html',
  controller: function() {}
});
