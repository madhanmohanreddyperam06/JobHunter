'use strict';

/**
 * JobDescriptionService
 * Manages structured job descriptions linked 1-to-1 to applications
 * via FastAPI REST endpoints and MySQL persistence.
 */
angular.module('jobCommandCenter')
.factory('JobDescriptionService', ['$http', '$q', 'API_CONFIG', function($http, $q, API_CONFIG) {
  var API_URL = API_CONFIG.BASE_URL + '/job-descriptions';

  /**
   * Normalize a job description object with computed helper properties for the UI.
   */
  function normalizeJobDescription(item) {
    if (!item) return null;
    var copy = angular.copy(item);

    copy.capturedAtDate = copy.captured_at ? new Date(copy.captured_at) : (copy.created_at ? new Date(copy.created_at) : new Date());
    copy.updatedAtDate = copy.updated_at ? new Date(copy.updated_at) : copy.capturedAtDate;

    // Flags for section availability
    copy.hasDescription = !!(copy.description && copy.description.trim());
    copy.hasResponsibilities = !!(copy.responsibilities && copy.responsibilities.trim());
    copy.hasRequirements = !!(copy.requirements && copy.requirements.trim());
    copy.hasQualifications = !!(copy.qualifications && copy.qualifications.trim());
    copy.hasBenefits = !!(copy.benefits && copy.benefits.trim());

    // Count how many detailed sections are captured
    copy.sectionsCount = (copy.hasDescription ? 1 : 0) +
                         (copy.hasResponsibilities ? 1 : 0) +
                         (copy.hasRequirements ? 1 : 0) +
                         (copy.hasQualifications ? 1 : 0) +
                         (copy.hasBenefits ? 1 : 0);

    // Human-friendly badges
    copy.employmentTypeLabel = (copy.employment_type || 'FULL_TIME').replace(/_/g, ' ');
    copy.workArrangementLabel = (copy.work_arrangement || 'HYBRID').replace(/_/g, ' ');

    return copy;
  }

  return {
    /**
     * Retrieve paginated job descriptions with optional search, filters, and sorting.
     */
    getJobDescriptions: function(params) {
      params = params || {};
      var queryParams = {};
      if (params.page) queryParams.page = params.page;
      if (params.page_size) queryParams.page_size = params.page_size;
      if (params.search && params.search.trim()) queryParams.search = params.search.trim();
      if (params.employment_type && params.employment_type.trim()) queryParams.employment_type = params.employment_type.trim();
      if (params.work_arrangement && params.work_arrangement.trim()) queryParams.work_arrangement = params.work_arrangement.trim();
      if (params.application_id) queryParams.application_id = params.application_id;
      if (params.sort_by) queryParams.sort_by = params.sort_by;
      if (params.sort_order) queryParams.sort_order = params.sort_order;

      return $http.get(API_URL, { params: queryParams })
        .then(function(res) {
          var data = res.data || {};
          var items = (data.items || []).map(normalizeJobDescription);
          return {
            items: items,
            total: data.total || 0,
            page: data.page || 1,
            pageSize: data.page_size || 10,
            totalPages: data.total_pages || 0,
          };
        })
        .catch(function(err) {
          return $q.reject((err.data && err.data.detail) ? err.data.detail : 'Failed to load job descriptions.');
        });
    },

    /**
     * Retrieve a specific job description by its ID.
     */
    getJobDescription: function(id) {
      return $http.get(API_URL + '/' + id)
        .then(function(res) {
          return normalizeJobDescription(res.data);
        })
        .catch(function(err) {
          return $q.reject((err.data && err.data.detail) ? err.data.detail : 'Failed to retrieve job description.');
        });
    },

    /**
     * Retrieve the job description linked to a specific application ID.
     */
    getByApplicationId: function(applicationId) {
      return $http.get(API_URL + '/by-application/' + applicationId)
        .then(function(res) {
          return normalizeJobDescription(res.data);
        })
        .catch(function(err) {
          return $q.reject((err.data && err.data.detail) ? err.data.detail : 'No job description found for this application.');
        });
    },

    /**
     * Create a new job description linked 1-to-1 to an application.
     */
    createJobDescription: function(data) {
      return $http.post(API_URL, data)
        .then(function(res) {
          return normalizeJobDescription(res.data);
        })
        .catch(function(err) {
          return $q.reject((err.data && err.data.detail) ? err.data.detail : 'Failed to create job description.');
        });
    },

    /**
     * Update an existing job description.
     */
    updateJobDescription: function(id, data) {
      return $http.put(API_URL + '/' + id, data)
        .then(function(res) {
          return normalizeJobDescription(res.data);
        })
        .catch(function(err) {
          return $q.reject((err.data && err.data.detail) ? err.data.detail : 'Failed to update job description.');
        });
    },

    /**
     * Delete a job description.
     */
    deleteJobDescription: function(id) {
      return $http.delete(API_URL + '/' + id)
        .then(function(res) {
          return res.data;
        })
        .catch(function(err) {
          return $q.reject((err.data && err.data.detail) ? err.data.detail : 'Failed to delete job description.');
        });
    }
  };
}]);
