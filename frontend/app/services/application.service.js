'use strict';

/**
 * ApplicationService
 * Manages job applications data and state operations via FastAPI REST APIs.
 * Connects directly to backend MySQL persistence.
 */
angular.module('jobCommandCenter')
.factory('ApplicationService', ['$http', '$q', 'API_CONFIG', function($http, $q, API_CONFIG) {
  var API_URL = API_CONFIG.BASE_URL + '/applications';

  /**
   * Helper to normalize application data structures between backend schema
   * and frontend component bindings.
   */
  function normalizeApplication(app) {
    if (!app) return null;
    var copy = angular.copy(app);
    copy.companyName = (copy.company && copy.company.name) ? copy.company.name : (copy.company || '');
    copy.company = copy.companyName;
    copy.jobTitle = copy.job_title || copy.jobTitle;
    copy.appliedDate = copy.applied_date || copy.appliedDate;
    copy.employmentType = copy.employment_type || copy.employmentType || copy.jobType;
    copy.jobType = copy.employmentType;
    copy.jobUrl = copy.job_url || copy.jobUrl;
    copy.jobDescription = copy.job_description || copy.jobDescription;
    return copy;
  }

  return {
    /**
     * Retrieve paginated job applications with search and filters
     * @param {Object} params - { search, status, location, sort_by, sort_order, page, page_size }
     * @returns {Promise<Object>} { items, page, pageSize, total, totalPages }
     */
    getApplications: function(params) {
      params = params || {};
      var queryParams = {};

      if (params.search && params.search.trim()) {
        queryParams.search = params.search.trim();
      }
      if (params.status && params.status.trim()) {
        queryParams.status = params.status.trim();
      }
      if (params.location && params.location.trim()) {
        queryParams.location = params.location.trim();
      }
      if (params.sort_by) {
        queryParams.sort_by = params.sort_by;
      }
      if (params.sort_order) {
        queryParams.sort_order = params.sort_order;
      }
      if (params.page) {
        queryParams.page = params.page;
      }
      if (params.page_size) {
        queryParams.page_size = params.page_size;
      }

      return $http.get(API_URL, { params: queryParams })
        .then(function(response) {
          var data = response.data || {};
          var items = (data.items || []).map(normalizeApplication);
          return {
            items: items,
            page: data.page || 1,
            pageSize: data.page_size || 10,
            total: data.total || 0,
            totalPages: data.total_pages || 1
          };
        })
        .catch(function(err) {
          var message = (err.data && err.data.detail) ? err.data.detail : 'Unable to load applications.';
          return $q.reject(message);
        });
    },

    /**
     * Retrieve a single application by ID
     * @param {number} id
     * @returns {Promise<Object>}
     */
    getApplication: function(id) {
      return $http.get(API_URL + '/' + id)
        .then(function(response) {
          return normalizeApplication(response.data);
        })
        .catch(function(err) {
          var message = (err.data && err.data.detail) ? err.data.detail : 'Application not found.';
          return $q.reject(message);
        });
    },

    /**
     * Create a new job application
     * @param {Object} appData
     * @returns {Promise<Object>}
     */
    createApplication: function(appData) {
      var payload = {
        company_name: appData.company_name || appData.companyName || appData.company,
        job_title: appData.job_title || appData.jobTitle,
        location: appData.location || null,
        job_url: appData.job_url || appData.jobUrl || null,
        salary: appData.salary || null,
        employment_type: appData.employment_type || appData.employmentType || appData.jobType || null,
        status: appData.status || 'SAVED',
        job_description: appData.job_description || appData.jobDescription || null,
        applied_date: appData.applied_date || appData.appliedDate || null
      };

      return $http.post(API_URL, payload)
        .then(function(response) {
          return normalizeApplication(response.data);
        })
        .catch(function(err) {
          var message = (err.data && err.data.detail) ? err.data.detail : 'Failed to create application.';
          return $q.reject(message);
        });
    },

    /**
     * Update an existing application
     * @param {number} id
     * @param {Object} updatedFields
     * @returns {Promise<Object>}
     */
    updateApplication: function(id, updatedFields) {
      var payload = {
        company_name: updatedFields.company_name || updatedFields.companyName || updatedFields.company || undefined,
        job_title: updatedFields.job_title || updatedFields.jobTitle || undefined,
        location: updatedFields.location !== undefined ? updatedFields.location : undefined,
        job_url: updatedFields.job_url || updatedFields.jobUrl || undefined,
        salary: updatedFields.salary !== undefined ? updatedFields.salary : undefined,
        employment_type: updatedFields.employment_type || updatedFields.employmentType || updatedFields.jobType || undefined,
        status: updatedFields.status || undefined,
        job_description: updatedFields.job_description || updatedFields.jobDescription || undefined,
        applied_date: updatedFields.applied_date || updatedFields.appliedDate || undefined
      };

      return $http.put(API_URL + '/' + id, payload)
        .then(function(response) {
          return normalizeApplication(response.data);
        })
        .catch(function(err) {
          var message = (err.data && err.data.detail) ? err.data.detail : 'Failed to update application.';
          return $q.reject(message);
        });
    },

    /**
     * Update only the pipeline status of an application
     * @param {number} id
     * @param {string} status
     * @returns {Promise<Object>}
     */
    updateStatus: function(id, status) {
      return $http.patch(API_URL + '/' + id + '/status', { status: status })
        .then(function(response) {
          return normalizeApplication(response.data);
        })
        .catch(function(err) {
          var message = (err.data && err.data.detail) ? err.data.detail : 'Failed to update status.';
          return $q.reject(message);
        });
    },

    /**
     * Delete an application permanently
     * @param {number} id
     * @returns {Promise<boolean>}
     */
    deleteApplication: function(id) {
      return $http.delete(API_URL + '/' + id)
        .then(function() {
          return true;
        })
        .catch(function(err) {
          var message = (err.data && err.data.detail) ? err.data.detail : 'Failed to delete application.';
          return $q.reject(message);
        });
    }
  };
}]);
