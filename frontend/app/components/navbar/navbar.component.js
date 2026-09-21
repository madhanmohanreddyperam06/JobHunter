'use strict';

/**
 * appNavbar Component
 * Header navigation bar featuring application branding, notification alert,
 * dynamic authenticated candidate profile, and sign-out dropdown.
 */
angular.module('jobCommandCenter')
.component('appNavbar', {
  templateUrl: 'app/components/navbar/navbar.html',
  controller: ['$rootScope', 'AuthService', function($rootScope, AuthService) {
    var $ctrl = this;

    $ctrl.dropdownOpen = false;

    $ctrl.toggleSidebar = function() {
      $rootScope.toggleSidebar();
    };

    $ctrl.toggleDropdown = function() {
      $ctrl.dropdownOpen = !$ctrl.dropdownOpen;
    };

    $ctrl.getUserName = function() {
      var user = AuthService.getCurrentUser();
      return (user && user.name) ? user.name : 'Candidate';
    };

    $ctrl.getUserEmail = function() {
      var user = AuthService.getCurrentUser();
      return (user && user.email) ? user.email : '';
    };

    $ctrl.getUserInitial = function() {
      var name = $ctrl.getUserName();
      return name ? name.charAt(0).toUpperCase() : 'U';
    };

    $ctrl.logout = function() {
      $ctrl.dropdownOpen = false;
      AuthService.logout();
    };
  }]
});
