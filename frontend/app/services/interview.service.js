'use strict';

/**
 * InterviewService
 * Manages interview rounds, schedules, preparation notes, and status transitions
 * via FastAPI REST endpoints connected to MySQL persistence.
 */
angular.module('jobCommandCenter')
.factory('InterviewService', ['$http', '$q', 'API_CONFIG', function($http, $q, API_CONFIG) {
  var API_URL = API_CONFIG.BASE_URL + '/interviews';

  /**
   * Helper to normalize interview record properties for consistent template binding.
   */
  function normalizeInterview(item) {
    if (!item) return null;
    var copy = angular.copy(item);
    copy.jobTitle = copy.job_title || (copy.application && copy.application.job_title) || 'Role Not Specified';
    copy.companyName = copy.company_name || (copy.application && copy.application.company_name) || 'Company Not Specified';
    copy.companyLogo = (copy.application && copy.application.company_logo) || null;
    copy.meetingUrl = copy.meeting_link || copy.meeting_url || '';
    copy.interviewerName = copy.interviewer || copy.interviewer_name || '';
    copy.interviewerEmail = copy.interviewer_email || '';
    copy.durationMinutes = copy.duration_minutes || 45;
    copy.roundName = copy.round_name || 'Interview Round';
    copy.interviewType = (copy.interview_type || 'VIDEO').toUpperCase();
    copy.scheduledAt = copy.scheduled_at ? new Date(copy.scheduled_at) : null;
    return copy;
  }

  return {
    /**
     * Retrieve paginated interviews with optional filters and search
     * @param {Object} params - { page, page_size, status, interview_type, application_id, search, upcoming, sort_by, sort_order }
     * @returns {Promise<Object>} { items, total, page, page_size, total_pages }
     */
    getInterviews: function(params) {
      params = params || {};
      var queryParams = {};

      if (params.page) queryParams.page = params.page;
      if (params.page_size) queryParams.page_size = params.page_size;
      if (params.status && params.status.trim()) queryParams.status = params.status.trim();
      if (params.interview_type && params.interview_type.trim()) queryParams.interview_type = params.interview_type.trim();
      if (params.application_id) queryParams.application_id = params.application_id;
      if (params.search && params.search.trim()) queryParams.search = params.search.trim();
      if (params.upcoming !== undefined && params.upcoming !== null) queryParams.upcoming = params.upcoming;
      if (params.sort_by) queryParams.sort_by = params.sort_by;
      if (params.sort_order) queryParams.sort_order = params.sort_order;

      return $http.get(API_URL, { params: queryParams })
        .then(function(res) {
          var data = res.data || {};
          var items = (data.items || []).map(normalizeInterview);
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
     * Retrieve single interview by ID
     * @param {number} id
     * @returns {Promise<Object>}
     */
    getInterview: function(id) {
      return $http.get(API_URL + '/' + id)
        .then(function(res) {
          return normalizeInterview(res.data);
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    },

    /**
     * Create a new interview record
     * @param {Object} interviewData
     * @returns {Promise<Object>}
     */
    createInterview: function(interviewData) {
      var payload = {
        application_id: Number(interviewData.application_id),
        round_name: interviewData.round_name,
        interview_type: interviewData.interview_type || 'VIDEO',
        scheduled_at: interviewData.scheduled_at || null,
        duration_minutes: Number(interviewData.duration_minutes || 45),
        location: interviewData.location || null,
        meeting_link: interviewData.meeting_link || interviewData.meeting_url || null,
        interviewer: interviewData.interviewer || interviewData.interviewer_name || null,
        interviewer_email: interviewData.interviewer_email || null,
        status: interviewData.status || 'SCHEDULED',
        notes: interviewData.notes || null
      };

      return $http.post(API_URL, payload)
        .then(function(res) {
          return normalizeInterview(res.data);
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    },

    /**
     * Update an interview record
     * @param {number} id
     * @param {Object} updatedFields
     * @returns {Promise<Object>}
     */
    updateInterview: function(id, updatedFields) {
      var payload = angular.copy(updatedFields);
      if (payload.application_id) payload.application_id = Number(payload.application_id);
      if (payload.duration_minutes) payload.duration_minutes = Number(payload.duration_minutes);
      if (payload.meeting_url && !payload.meeting_link) payload.meeting_link = payload.meeting_url;
      if (payload.interviewer_name && !payload.interviewer) payload.interviewer = payload.interviewer_name;

      return $http.put(API_URL + '/' + id, payload)
        .then(function(res) {
          return normalizeInterview(res.data);
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    },

    /**
     * Update only the status of an interview
     * @param {number} id
     * @param {string} status
     * @returns {Promise<Object>}
     */
    updateStatus: function(id, status) {
      return $http.patch(API_URL + '/' + id + '/status', { status: status })
        .then(function(res) {
          return normalizeInterview(res.data);
        })
        .catch(function(err) {
          return $q.reject(err.data || err);
        });
    },

    /**
     * Delete an interview record
     * @param {number} id
     * @returns {Promise<boolean>}
     */
    deleteInterview: function(id) {
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
