'use strict';

/**
 * ResumeService
 * Manages resume versions, physical file uploads, active designation, and download
 * via FastAPI REST endpoints connected to MySQL persistence and filesystem storage.
 */
angular.module('jobCommandCenter')
.factory('ResumeService', ['$http', '$q', 'API_CONFIG', function($http, $q, API_CONFIG) {
  var API_URL = API_CONFIG.BASE_URL + '/resumes';

  /**
   * Helper to format file size in human-readable units.
   */
  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 KB';
    var k = 1024;
    var sizes = ['Bytes', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  /**
   * Helper to normalize resume properties for consistent template binding.
   */
  function normalizeResume(item) {
    if (!item) return null;
    var copy = angular.copy(item);
    copy.versionLabel = 'v' + copy.version;
    copy.formattedSize = formatBytes(copy.file_size);
    copy.isPdf = copy.mime_type && copy.mime_type.indexOf('pdf') !== -1;
    copy.isDocx = copy.mime_type && (copy.mime_type.indexOf('word') !== -1 || copy.mime_type.indexOf('officedocument') !== -1);
    copy.fileTypeLabel = copy.isPdf ? 'PDF' : (copy.isDocx ? 'DOCX' : 'FILE');
    copy.updatedAtDate = copy.updated_at ? new Date(copy.updated_at) : (copy.created_at ? new Date(copy.created_at) : new Date());
    copy.applicationCount = copy.application_count || 0;
    return copy;
  }

  return {
    /**
     * Retrieve paginated resumes with optional filters and search
     */
    getResumes: function(params) {
      params = params || {};
      var queryParams = {};
      if (params.page) queryParams.page = params.page;
      if (params.page_size) queryParams.page_size = params.page_size;
      if (params.search && params.search.trim()) queryParams.search = params.search.trim();
      if (params.file_type && params.file_type.trim()) queryParams.file_type = params.file_type.trim();
      if (params.sort_by) queryParams.sort_by = params.sort_by;
      if (params.sort_order) queryParams.sort_order = params.sort_order;

      return $http.get(API_URL, { params: queryParams })
        .then(function(res) {
          var data = res.data || {};
          var items = (data.items || []).map(normalizeResume);
          return {
            items: items,
            total: data.total || 0,
            page: data.page || 1,
            pageSize: data.page_size || 10,
            totalPages: data.total_pages || 1
          };
        });
    },

    /**
     * Retrieve metadata for a single resume
     */
    getResume: function(id) {
      return $http.get(API_URL + '/' + id)
        .then(function(res) {
          return normalizeResume(res.data);
        });
    },

    /**
     * Upload a new resume family (version 1)
     */
    uploadResume: function(formData) {
      return $http.post(API_URL, formData, {
        transformRequest: angular.identity,
        headers: { 'Content-Type': undefined }
      }).then(function(res) {
        return normalizeResume(res.data);
      });
    },

    /**
     * Upload a new version for an existing resume family
     */
    createVersion: function(id, formData) {
      return $http.post(API_URL + '/' + id + '/versions', formData, {
        transformRequest: angular.identity,
        headers: { 'Content-Type': undefined }
      }).then(function(res) {
        return normalizeResume(res.data);
      });
    },

    /**
     * Update editable metadata for a resume
     */
    updateResume: function(id, data) {
      return $http.put(API_URL + '/' + id, data)
        .then(function(res) {
          return normalizeResume(res.data);
        });
    },

    /**
     * Designate resume as user's active resume
     */
    activateResume: function(id) {
      return $http.patch(API_URL + '/' + id + '/activate')
        .then(function(res) {
          return normalizeResume(res.data);
        });
    },

    /**
     * Delete resume (rejected with 409 if attached to applications)
     */
    deleteResume: function(id) {
      return $http.delete(API_URL + '/' + id)
        .then(function() {
          return true;
        });
    },

    /**
     * Retrieve all versions in a resume family
     */
    getVersions: function(id) {
      return $http.get(API_URL + '/' + id + '/versions')
        .then(function(res) {
          return (res.data || []).map(normalizeResume);
        });
    },

    /**
     * Download stored resume file using authenticated bearer token
     */
    downloadResume: function(id, defaultFileName) {
      return $http.get(API_URL + '/' + id + '/download', {
        responseType: 'blob'
      }).then(function(res) {
        var blob = new Blob([res.data], { type: res.headers('Content-Type') || 'application/octet-stream' });
        var filename = defaultFileName || 'resume.pdf';

        var disposition = res.headers('Content-Disposition') || res.headers('content-disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
          var match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
          if (match && match[1]) {
            filename = match[1].replace(/['"]/g, '').trim();
          }
        }

        var link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(link.href);
        return true;
      });
    }
  };
}]);
