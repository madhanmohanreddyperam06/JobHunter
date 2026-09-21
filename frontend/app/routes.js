'use strict';

/**
 * Route Configuration
 * Configured with AngularJS ngRoute and authentication metadata.
 */
angular.module('jobCommandCenter')
.config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider) {
  // Use hashbang routing compatible with static web servers and local files
  $locationProvider.hashPrefix('');

  $routeProvider
    // Public Authentication Routes
    .when('/login', {
      templateUrl: 'app/views/login.html',
      controller: 'LoginController',
      controllerAs: 'vm',
      requiresAuth: false
    })
    .when('/register', {
      templateUrl: 'app/views/register.html',
      controller: 'RegisterController',
      controllerAs: 'vm',
      requiresAuth: false
    })

    // Protected Application Routes
    .when('/dashboard', {
      templateUrl: 'app/views/dashboard.html',
      controller: 'DashboardController',
      controllerAs: 'vm',
      requiresAuth: true
    })
    .when('/applications', {
      templateUrl: 'app/views/applications.html',
      controller: 'ApplicationsController',
      controllerAs: 'vm',
      requiresAuth: true
    })
    .when('/kanban', {
      templateUrl: 'app/views/kanban.html',
      controller: 'KanbanController',
      controllerAs: 'vm',
      requiresAuth: true
    })
    .when('/interviews', {
      templateUrl: 'app/views/interviews.html',
      controller: 'InterviewsController',
      controllerAs: 'vm',
      requiresAuth: true
    })
    .when('/tasks', {
      templateUrl: 'app/views/tasks.html',
      controller: 'TasksController',
      controllerAs: 'vm',
      requiresAuth: true
    })
    .when('/resumes', {
      templateUrl: 'app/views/resumes.html',
      controller: 'ResumesController',
      controllerAs: 'vm',
      requiresAuth: true
    })
    .when('/job-descriptions', {
      templateUrl: 'app/views/job-descriptions.html',
      controller: 'JobDescriptionsController',
      controllerAs: 'vm',
      requiresAuth: true
    })
    .when('/skills', {
      templateUrl: 'app/views/skills.html',
      controller: 'SkillsController',
      controllerAs: 'vm',
      requiresAuth: true
    })
    .when('/analytics', {
      templateUrl: 'app/views/analytics.html',
      controller: 'AnalyticsController',
      controllerAs: 'vm',
      requiresAuth: true
    })
    .when('/settings', {
      templateUrl: 'app/views/settings.html',
      controller: 'SettingsController',
      controllerAs: 'vm',
      requiresAuth: true
    })

    // Fallbacks
    .when('/', {
      redirectTo: '/dashboard'
    })
    .otherwise({
      redirectTo: '/dashboard'
    });
}]);
