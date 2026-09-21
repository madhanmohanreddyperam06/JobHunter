'use strict';

/**
 * RegisterController
 * Handles candidate registration form validation, submission, and feedback.
 */
angular.module('jobCommandCenter')
.controller('RegisterController', ['AuthService', '$location', function(AuthService, $location) {
  var vm = this;

  vm.userData = {
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  };

  vm.isLoading = false;
  vm.errorMessage = '';
  vm.successMessage = '';

  /**
   * Submit registration form
   */
  vm.submitRegister = function(form) {
    vm.errorMessage = '';
    vm.successMessage = '';

    if (form && form.$invalid) {
      return;
    }

    if (vm.userData.password !== vm.userData.confirmPassword) {
      vm.errorMessage = 'Passwords do not match. Please verify your confirmation password.';
      return;
    }

    vm.isLoading = true;

    var payload = {
      name: vm.userData.name,
      email: vm.userData.email,
      password: vm.userData.password
    };

    AuthService.register(payload)
      .then(function() {
        vm.isLoading = false;
        vm.successMessage = 'Account created successfully! Redirecting to sign in...';
        // Auto-navigate to login after short interval
        setTimeout(function() {
          $location.path('/login');
        }, 1200);
      })
      .catch(function(errMessage) {
        vm.isLoading = false;
        vm.errorMessage = typeof errMessage === 'string' ? errMessage : 'Registration failed. Please try again.';
      });
  };
}]);
