'use strict';

/**
 * AuthInterceptor
 * Centralized AngularJS HTTP interceptor.
 * - Injects 'Authorization: Bearer <token>' for all HTTP requests when token is available.
 * - Captures 401 Unauthorized responses to clear stale credentials and redirect to /login.
 */
angular.module('jobCommandCenter')
.factory('AuthInterceptor', ['$q', '$injector', function($q, $injector) {
  var TOKEN_KEY = 'jcc_access_token';

  return {
    request: function(config) {
      var token = sessionStorage.getItem(TOKEN_KEY);
      if (token && !config.headers.Authorization) {
        config.headers.Authorization = 'Bearer ' + token;
      }
      return config;
    },

    responseError: function(rejection) {
      if (rejection.status === 401) {
        // Clear stored token
        sessionStorage.removeItem(TOKEN_KEY);

        // Safely retrieve services via $injector to avoid circular dependency
        var $location = $injector.get('$location');
        var currentPath = $location.path();

        // Avoid infinite redirect loops on login/register
        if (currentPath !== '/login' && currentPath !== '/register') {
          var AuthService = $injector.get('AuthService');
          AuthService.clearAuth();
          $location.path('/login');
        }
      }
      return $q.reject(rejection);
    }
  };
}]);
