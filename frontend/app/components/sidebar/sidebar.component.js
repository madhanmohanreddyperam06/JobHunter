'use strict';

/**
 * appSidebar Component
 * Provides responsive route-aware navigation for all primary command center modules.
 */
angular.module('jobCommandCenter')
.component('appSidebar', {
  templateUrl: 'app/components/sidebar/sidebar.html',
  controller: ['$location', function($location) {
    var $ctrl = this;

    /**
     * Determine whether the given route is currently active
     * @param {string} route
     * @returns {boolean}
     */
    $ctrl.isActive = function(route) {
      return $location.path() === route;
    };
  }]
});
