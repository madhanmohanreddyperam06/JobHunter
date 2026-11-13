'use strict';

/**
 * LandingController
 * Controller for the landing page with interactive elements and animations
 */
angular.module('jobCommandCenter')
.controller('LandingController', [function() {
  var vm = this;

  // Landing page state
  vm.isLoading = false;
  vm.currentYear = new Date().getFullYear();

  // Initialize any interactive elements
  vm.init = function() {
    // Scroll animations are handled by CSS
    // Additional JavaScript interactions can be added here
    console.log('Landing page loaded');
  };

  // Call initialization
  vm.init();
}]);