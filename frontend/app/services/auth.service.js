'use strict';

/**
 * AuthService
 * Centralized authentication service for Job Application Command Center.
 * Handles user registration, login, logout, token management, and profile hydration.
 */
angular.module('jobCommandCenter')
.factory('AuthService', ['$http', '$q', '$location', 'API_CONFIG', function($http, $q, $location, API_CONFIG) {
  var API_BASE = API_CONFIG.BASE_URL + '/auth';
  var TOKEN_KEY = 'jcc_access_token';

  // Private state
  var state = {
    token: sessionStorage.getItem(TOKEN_KEY) || null,
    currentUser: null,
    initialized: false
  };

  var service = {
    /**
     * Check whether an active authenticated session exists
     * @returns {boolean}
     */
    isAuthenticated: function() {
      return !!state.token;
    },

    /**
     * Retrieve the stored access token
     * @returns {string|null}
     */
    getToken: function() {
      return state.token;
    },

    /**
     * Retrieve the currently authenticated user
     * @returns {Object|null}
     */
    getCurrentUser: function() {
      return state.currentUser;
    },

    /**
     * Register a new user account
     * @param {Object} userData - { name, email, password }
     * @returns {Promise}
     */
    register: function(userData) {
      return $http.post(API_BASE + '/register', userData)
        .then(function(response) {
          return response.data;
        })
        .catch(function(err) {
          var message = (err.data && err.data.detail) ? err.data.detail : 'Registration failed. Please try again.';
          return $q.reject(message);
        });
    },

    /**
     * Authenticate user credentials and store JWT token
     * @param {Object} credentials - { email, password }
     * @returns {Promise}
     */
    login: function(credentials) {
      return $http.post(API_BASE + '/login', credentials)
        .then(function(response) {
          var token = response.data.access_token;
          state.token = token;
          sessionStorage.setItem(TOKEN_KEY, token);
          return service.fetchCurrentUser();
        })
        .catch(function(err) {
          var message = (err.data && err.data.detail) ? err.data.detail : 'Invalid email or password.';
          return $q.reject(message);
        });
    },

    /**
     * Fetch user profile using current bearer token
     * @returns {Promise<Object>}
     */
    fetchCurrentUser: function() {
      if (!state.token) {
        return $q.reject('No token available');
      }

      return $http.get(API_BASE + '/me')
        .then(function(response) {
          state.currentUser = response.data;
          state.initialized = true;
          return state.currentUser;
        })
        .catch(function(err) {
          service.clearAuth();
          return $q.reject(err);
        });
    },

    /**
     * Clear token and user profile
     */
    clearAuth: function() {
      state.token = null;
      state.currentUser = null;
      sessionStorage.removeItem(TOKEN_KEY);
    },

    /**
     * Terminate user session and redirect to login
     */
    logout: function() {
      service.clearAuth();
      $location.path('/login');
    },

    /**
     * Initialize auth state on application startup
     */
    init: function() {
      if (state.token && !state.currentUser) {
        service.fetchCurrentUser();
      }
    }
  };

  return service;
}]);
