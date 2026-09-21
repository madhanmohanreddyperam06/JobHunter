'use strict';

/**
 * SkillService
 * Manages user-owned skills catalog, application-skill linkages,
 * job-description-skill linkages, and skill intelligence stats
 * via FastAPI REST endpoints.
 */
angular.module('jobCommandCenter')
.factory('SkillService', ['$http', '$q', 'API_CONFIG', function($http, $q, API_CONFIG) {
  var BASE_URL = API_CONFIG.BASE_URL;

  var CATEGORIES = [
    { value: 'PROGRAMMING_LANGUAGE', label: 'Programming Language', icon: 'bi-code-slash', badgeClass: 'bg-primary' },
    { value: 'FRONTEND', label: 'Frontend', icon: 'bi-browser-chrome', badgeClass: 'bg-info text-dark' },
    { value: 'BACKEND', label: 'Backend', icon: 'bi-server', badgeClass: 'bg-success' },
    { value: 'DATABASE', label: 'Database', icon: 'bi-database', badgeClass: 'bg-warning text-dark' },
    { value: 'CLOUD', label: 'Cloud Infrastructure', icon: 'bi-cloud', badgeClass: 'bg-cyan text-dark' },
    { value: 'DEVOPS', label: 'DevOps & CI/CD', icon: 'bi-gear-wide-connected', badgeClass: 'bg-secondary' },
    { value: 'AI_ML', label: 'AI & Machine Learning', icon: 'bi-cpu', badgeClass: 'bg-purple' },
    { value: 'DATA', label: 'Data Engineering & Analytics', icon: 'bi-graph-up', badgeClass: 'bg-teal' },
    { value: 'MOBILE', label: 'Mobile Development', icon: 'bi-phone', badgeClass: 'bg-indigo' },
    { value: 'TESTING', label: 'QA & Testing', icon: 'bi-check2-circle', badgeClass: 'bg-danger' },
    { value: 'SECURITY', label: 'Security & Auth', icon: 'bi-shield-lock', badgeClass: 'bg-dark' },
    { value: 'TOOLS', label: 'Tools & Workflows', icon: 'bi-wrench-adjustable', badgeClass: 'bg-light text-dark' },
    { value: 'SOFT_SKILL', label: 'Soft Skills & Leadership', icon: 'bi-people', badgeClass: 'bg-pink' },
    { value: 'OTHER', label: 'Other', icon: 'bi-tag', badgeClass: 'bg-secondary' }
  ];

  var PROFICIENCY_LEVELS = [
    { value: 'BEGINNER', label: 'Beginner', badgeClass: 'bg-secondary' },
    { value: 'INTERMEDIATE', label: 'Intermediate', badgeClass: 'bg-info text-dark' },
    { value: 'ADVANCED', label: 'Advanced', badgeClass: 'bg-primary' },
    { value: 'EXPERT', label: 'Expert', badgeClass: 'bg-success' },
    { value: 'UNKNOWN', label: 'Not Specified', badgeClass: 'bg-light text-dark' }
  ];

  var IMPORTANCE_LEVELS = [
    { value: 'REQUIRED', label: 'Required / Must-Have', badgeClass: 'bg-danger' },
    { value: 'PREFERRED', label: 'Preferred / Nice-to-Have', badgeClass: 'bg-secondary' }
  ];

  var SOURCE_SECTIONS = [
    { value: 'REQUIREMENTS', label: 'Requirements' },
    { value: 'RESPONSIBILITIES', label: 'Responsibilities' },
    { value: 'QUALIFICATIONS', label: 'Qualifications' },
    { value: 'DESCRIPTION', label: 'Overview / Description' },
    { value: 'BENEFITS', label: 'Benefits' },
    { value: 'OTHER', label: 'Other' }
  ];

  function getCategoryMeta(catValue) {
    for (var i = 0; i < CATEGORIES.length; i++) {
      if (CATEGORIES[i].value === catValue) return CATEGORIES[i];
    }
    return { value: catValue, label: catValue, icon: 'bi-tag', badgeClass: 'bg-secondary' };
  }

  function getProficiencyMeta(val) {
    for (var i = 0; i < PROFICIENCY_LEVELS.length; i++) {
      if (PROFICIENCY_LEVELS[i].value === val) return PROFICIENCY_LEVELS[i];
    }
    return { value: val, label: val || 'Unknown', badgeClass: 'bg-light text-dark' };
  }

  function getImportanceMeta(val) {
    for (var i = 0; i < IMPORTANCE_LEVELS.length; i++) {
      if (IMPORTANCE_LEVELS[i].value === val) return IMPORTANCE_LEVELS[i];
    }
    return { value: val, label: val || 'Required', badgeClass: 'bg-secondary' };
  }

  function normalizeSkill(item) {
    if (!item) return null;
    var copy = angular.copy(item);
    copy.categoryMeta = getCategoryMeta(copy.category);
    copy.totalUsage = (copy.application_count || 0) + (copy.job_description_count || 0);
    copy.aliasList = copy.aliases ? copy.aliases.split(',').map(function(s) { return s.trim(); }).filter(Boolean) : [];
    return copy;
  }

  return {
    CATEGORIES: CATEGORIES,
    PROFICIENCY_LEVELS: PROFICIENCY_LEVELS,
    IMPORTANCE_LEVELS: IMPORTANCE_LEVELS,
    SOURCE_SECTIONS: SOURCE_SECTIONS,
    getCategoryMeta: getCategoryMeta,
    getProficiencyMeta: getProficiencyMeta,
    getImportanceMeta: getImportanceMeta,

    // =====================================================================
    // Skill Catalog
    // =====================================================================

    getSkills: function(params) {
      params = params || {};
      var queryParams = {};
      if (params.page) queryParams.page = params.page;
      if (params.page_size) queryParams.page_size = params.page_size;
      if (params.search && params.search.trim()) queryParams.search = params.search.trim();
      if (params.category && params.category.trim()) queryParams.category = params.category.trim();
      if (params.sort_by) queryParams.sort_by = params.sort_by;
      if (params.sort_order) queryParams.sort_order = params.sort_order;

      return $http.get(BASE_URL + '/skills', { params: queryParams })
        .then(function(res) {
          var data = res.data;
          data.items = (data.items || []).map(normalizeSkill);
          return data;
        });
    },

    getSkill: function(skillId) {
      return $http.get(BASE_URL + '/skills/' + skillId)
        .then(function(res) {
          return normalizeSkill(res.data);
        });
    },

    createSkill: function(payload) {
      return $http.post(BASE_URL + '/skills', payload)
        .then(function(res) {
          return normalizeSkill(res.data);
        });
    },

    updateSkill: function(skillId, payload) {
      return $http.put(BASE_URL + '/skills/' + skillId, payload)
        .then(function(res) {
          return normalizeSkill(res.data);
        });
    },

    deleteSkill: function(skillId) {
      return $http.delete(BASE_URL + '/skills/' + skillId)
        .then(function(res) {
          return res.data;
        });
    },

    getSkillStats: function() {
      return $http.get(BASE_URL + '/skills/stats')
        .then(function(res) {
          return res.data;
        });
    },

    // =====================================================================
    // Application ↔ Skill Mapping
    // =====================================================================

    getApplicationSkills: function(applicationId) {
      return $http.get(BASE_URL + '/applications/' + applicationId + '/skills')
        .then(function(res) {
          return (res.data || []).map(function(item) {
            item.categoryMeta = getCategoryMeta(item.category);
            item.proficiencyMeta = getProficiencyMeta(item.proficiency);
            return item;
          });
        });
    },

    addApplicationSkill: function(applicationId, payload) {
      return $http.post(BASE_URL + '/applications/' + applicationId + '/skills', payload)
        .then(function(res) {
          var item = res.data;
          item.categoryMeta = getCategoryMeta(item.category);
          item.proficiencyMeta = getProficiencyMeta(item.proficiency);
          return item;
        });
    },

    updateApplicationSkill: function(applicationId, skillId, payload) {
      return $http.put(BASE_URL + '/applications/' + applicationId + '/skills/' + skillId, payload)
        .then(function(res) {
          var item = res.data;
          item.categoryMeta = getCategoryMeta(item.category);
          item.proficiencyMeta = getProficiencyMeta(item.proficiency);
          return item;
        });
    },

    removeApplicationSkill: function(applicationId, skillId) {
      return $http.delete(BASE_URL + '/applications/' + applicationId + '/skills/' + skillId)
        .then(function(res) {
          return res.data;
        });
    },

    // =====================================================================
    // Job Description ↔ Skill Mapping
    // =====================================================================

    getJobDescriptionSkills: function(jobDescriptionId) {
      return $http.get(BASE_URL + '/job-descriptions/' + jobDescriptionId + '/skills')
        .then(function(res) {
          return (res.data || []).map(function(item) {
            item.categoryMeta = getCategoryMeta(item.category);
            item.importanceMeta = getImportanceMeta(item.importance);
            return item;
          });
        });
    },

    addJobDescriptionSkill: function(jobDescriptionId, payload) {
      return $http.post(BASE_URL + '/job-descriptions/' + jobDescriptionId + '/skills', payload)
        .then(function(res) {
          var item = res.data;
          item.categoryMeta = getCategoryMeta(item.category);
          item.importanceMeta = getImportanceMeta(item.importance);
          return item;
        });
    },

    updateJobDescriptionSkill: function(jobDescriptionId, skillId, payload) {
      return $http.put(BASE_URL + '/job-descriptions/' + jobDescriptionId + '/skills/' + skillId, payload)
        .then(function(res) {
          var item = res.data;
          item.categoryMeta = getCategoryMeta(item.category);
          item.importanceMeta = getImportanceMeta(item.importance);
          return item;
        });
    },

    removeJobDescriptionSkill: function(jobDescriptionId, skillId) {
      return $http.delete(BASE_URL + '/job-descriptions/' + jobDescriptionId + '/skills/' + skillId)
        .then(function(res) {
          return res.data;
        });
    }
  };
}]);
