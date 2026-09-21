'use strict';

/**
 * SettingsController
 * Coordinator for user profile preferences and application settings.
 */
angular.module('jobCommandCenter')
.controller('SettingsController', [function() {
  var vm = this;

  vm.activeTab = 'profile';

  vm.setTab = function(tab) {
    vm.activeTab = tab;
  };
}]);
