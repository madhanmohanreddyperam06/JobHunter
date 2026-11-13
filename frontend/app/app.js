'use strict';

/**
 * Job Application Command Center
 * Main AngularJS Application Module
 * Architecture: AngularJS 1.8.x + ngRoute
 */
angular.module('jobCommandCenter', [
  'ngRoute'
])
.constant('API_CONFIG', {
  BASE_URL: 'http://localhost:8000/api'
})
.config(['$httpProvider', function($httpProvider) {
  // Centralized HTTP interceptor for Bearer token & 401 handling
  $httpProvider.interceptors.push('AuthInterceptor');
}])
.run(['$rootScope', '$location', 'AuthService', function($rootScope, $location, AuthService) {
  // Mobile sidebar state management
  $rootScope.sidebarOpen = false;

  $rootScope.toggleSidebar = function() {
    $rootScope.sidebarOpen = !$rootScope.sidebarOpen;
  };

  $rootScope.closeSidebar = function() {
    $rootScope.sidebarOpen = false;
  };

  // Helper to check if current route is a standalone auth screen (login/register)
  $rootScope.isAuthPage = function() {
    var path = $location.path();
    return path === '/login' || path === '/register';
  };

  // Helper to check if current route is the landing page
  $rootScope.isLandingPage = function() {
    var path = $location.path();
    return path === '/' || path === '';
  };

  // Hydrate user profile on application boot if token exists
  AuthService.init();

  // Centralized Route Protection Guard
  $rootScope.$on('$routeChangeStart', function(event, next) {
    if (!next) return;

    var isAuthRoute = next.originalPath === '/login' || next.originalPath === '/register';
    var isLandingRoute = next.originalPath === '/';
    var requiresAuth = next.requiresAuth !== false && !isAuthRoute && !isLandingRoute;

    if (requiresAuth && !AuthService.isAuthenticated()) {
      event.preventDefault();
      $location.path('/login');
      return;
    }

    if (isAuthRoute && AuthService.isAuthenticated()) {
      event.preventDefault();
      $location.path('/dashboard');
      return;
    }
  });

  // Close mobile sidebar on successful route changes
  $rootScope.$on('$routeChangeSuccess', function() {
    $rootScope.sidebarOpen = false;
  });
}]);
