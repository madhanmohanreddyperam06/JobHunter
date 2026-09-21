'use strict';

/**
 * LoginController
 * Handles presentation and credential submission for the user login view.
 */
angular.module('jobCommandCenter')
.controller('LoginController', ['AuthService', '$location', function(AuthService, $location) {
  var vm = this;

  vm.credentials = {
    email: '',
    password: ''
  };

  vm.isLoading = false;
  vm.errorMessage = '';

  /**
   * Submit login form
   */
  vm.submitLogin = function(form) {
    if (form && form.$invalid) {
      return;
    }

    vm.isLoading = true;
    vm.errorMessage = '';

    AuthService.login(vm.credentials)
      .then(function() {
        vm.isLoading = false;
        $location.path('/dashboard');
      })
      .catch(function(errMessage) {
        vm.isLoading = false;
        vm.errorMessage = typeof errMessage === 'string' ? errMessage : 'Invalid email or password.';
      });
  };
}]);
