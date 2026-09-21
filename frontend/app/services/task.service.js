'use strict';

/**
 * TaskService
 * Manages action items, recruiter follow-ups, and coding test deadlines
 * via FastAPI REST endpoints connected to MySQL persistence.
 */
angular.module('jobCommandCenter')
.factory('TaskService', ['$http', '$q', 'API_CONFIG', function($http, $q, API_CONFIG) {
  var API_URL = API_CONFIG.BASE_URL + '/tasks';

  /**
   * Normalize task record properties for template bindings.
   */
  function normalizeTask(item) {
    if (!item) return null;
    var copy = angular.copy(item);
    copy.jobTitle = copy.job_title || (copy.application && copy.application.job_title) || null;
    copy.companyName = copy.company_name || (copy.application && copy.application.company_name) || null;
    copy.dueDate = copy.due_date ? new Date(copy.due_date) : null;
    copy.completedAt = copy.completed_at ? new Date(copy.completed_at) : null;
    copy.createdAt = copy.created_at ? new Date(copy.created_at) : null;
    copy.isOverdue = Boolean(copy.is_overdue);
    copy.priority = (copy.priority || 'MEDIUM').toUpperCase();
    copy.status = (copy.status || 'TODO').toUpperCase();
    return copy;
  }

  return {
    /**
     * Retrieve paginated tasks with search, status, priority, due filters
     * @param {Object} params - { page, page_size, status, priority, application_id, search, due, sort_by, sort_order }
     * @returns {Promise<Object>} { items, total, page, pageSize, totalPages }
     */
    getTasks: function(params) {
      params = params || {};
      var queryParams = {};

      if (params.page) queryParams.page = params.page;
      if (params.page_size) queryParams.page_size = params.page_size;
      if (params.status && params.status.trim()) queryParams.status = params.status.trim();
      if (params.priority && params.priority.trim()) queryParams.priority = params.priority.trim();
      if (params.application_id) queryParams.application_id = params.application_id;
      if (params.search && params.search.trim()) queryParams.search = params.search.trim();
      if (params.due && params.due.trim()) queryParams.due = params.due.trim();
      if (params.sort_by) queryParams.sort_by = params.sort_by;
      if (params.sort_order) queryParams.sort_order = params.sort_order;

      return $http.get(API_URL, { params: queryParams })
        .then(function(res) {
          var data = res.data || {};
          var items = (data.items || []).map(normalizeTask);
          return {
            items: items,
            total: data.total || 0,
            page: data.page || 1,
            pageSize: data.page_size || 20,
            totalPages: data.total_pages || 1
          };
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    },

    /**
     * Retrieve summary KPI counts for the user
     * @returns {Promise<Object>} { total, pending, due_today, overdue, completed }
     */
    getSummary: function() {
      return $http.get(API_URL + '/summary')
        .then(function(res) {
          return res.data;
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    },

    /**
     * Retrieve single task by ID
     * @param {number} id
     * @returns {Promise<Object>}
     */
    getTask: function(id) {
      return $http.get(API_URL + '/' + id)
        .then(function(res) {
          return normalizeTask(res.data);
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    },

    /**
     * Create a new task record
     * @param {Object} taskData
     * @returns {Promise<Object>}
     */
    createTask: function(taskData) {
      var payload = {
        title: taskData.title ? taskData.title.trim() : '',
        description: taskData.description ? taskData.description.trim() : null,
        priority: taskData.priority || 'MEDIUM',
        status: taskData.status || 'TODO',
        due_date: taskData.due_date || null,
        application_id: taskData.application_id ? Number(taskData.application_id) : null
      };

      return $http.post(API_URL, payload)
        .then(function(res) {
          return normalizeTask(res.data);
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    },

    /**
     * Update an existing task record
     * @param {number} id
     * @param {Object} updatedFields
     * @returns {Promise<Object>}
     */
    updateTask: function(id, updatedFields) {
      var payload = angular.copy(updatedFields);
      if (payload.application_id) {
        payload.application_id = Number(payload.application_id);
      } else if (payload.application_id === '' || payload.application_id === null) {
        payload.application_id = null;
      }

      return $http.put(API_URL + '/' + id, payload)
        .then(function(res) {
          return normalizeTask(res.data);
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    },

    /**
     * Update task status with automatic completed_at management
     * @param {number} id
     * @param {string} status
     * @returns {Promise<Object>}
     */
    updateStatus: function(id, status) {
      return $http.patch(API_URL + '/' + id + '/status', { status: status })
        .then(function(res) {
          return normalizeTask(res.data);
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    },

    /**
     * Delete a task record
     * @param {number} id
     * @returns {Promise<boolean>}
     */
    deleteTask: function(id) {
      return $http.delete(API_URL + '/' + id)
        .then(function() {
          return true;
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    }
  };
}]);
