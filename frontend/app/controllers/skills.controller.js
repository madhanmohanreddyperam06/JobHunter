'use strict';

/**
 * SkillsController
 * Coordinates skill catalog browsing, CRUD modals, category filtering,
 * search debouncing, duplicate prevention alerts, and contextual skill mapping
 * for Applications and Job Descriptions.
 */
angular.module('jobCommandCenter')
.controller('SkillsController', [
  'SkillService',
  'ApplicationService',
  'JobDescriptionService',
  '$scope',
  '$location',
  '$timeout',
  function(SkillService, ApplicationService, JobDescriptionService, $scope, $location, $timeout) {
    var vm = this;

    // Metadata constants
    vm.categories = SkillService.CATEGORIES;
    vm.proficiencyLevels = SkillService.PROFICIENCY_LEVELS;
    vm.importanceLevels = SkillService.IMPORTANCE_LEVELS;
    vm.sourceSections = SkillService.SOURCE_SECTIONS;

    // View & data state
    vm.skills = [];
    vm.isLoading = true;
    vm.isSubmitting = false;
    vm.isDeleting = false;
    vm.total = 0;
    vm.page = 1;
    vm.pageSize = 18;
    vm.totalPages = 1;

    // Filters & sorting
    vm.filters = {
      search: '',
      category: '',
      sort_by: 'name',
      sort_order: 'asc'
    };

    // Stats
    vm.stats = {
      total_skills: 0,
      skills_in_applications: 0,
      skills_in_job_descriptions: 0,
      top_used_skills: [],
      category_counts: {}
    };

    // Contextual Mode (when navigated via ?application_id=... or ?job_description_id=...)
    vm.contextualAppId = null;
    vm.contextualJdId = null;
    vm.contextualApp = null;
    vm.contextualJd = null;
    vm.contextualMappedSkills = [];
    vm.isLoadingContext = false;

    // Contextual Mapping Form Modal
    vm.mappingModalOpen = false;
    vm.mappingMode = 'add'; // 'add' | 'edit'
    vm.mappingData = {};
    vm.mappingError = '';
    vm.isSubmittingMapping = false;

    // Catalog Create / Edit Modal State
    vm.formModalOpen = false;
    vm.formMode = 'create'; // 'create' | 'edit'
    vm.formData = {};
    vm.formError = '';

    // Delete Modal State
    vm.deleteModalOpen = false;
    vm.deleteTarget = null;
    vm.deleteError = '';

    // Toast alert message
    vm.toastMessage = '';
    vm.toastType = 'success';
    var toastTimer = null;

    function showToast(msg, type) {
      vm.toastMessage = msg;
      vm.toastType = type || 'success';
      if (toastTimer) $timeout.cancel(toastTimer);
      toastTimer = $timeout(function() {
        vm.toastMessage = '';
      }, 4000);
    }
    vm.dismissToast = function() {
      vm.toastMessage = '';
    };

    // =====================================================================
    // Catalog Loading & Search
    // =====================================================================

    var searchDebouncePromise = null;
    vm.onSearchChange = function() {
      if (searchDebouncePromise) $timeout.cancel(searchDebouncePromise);
      searchDebouncePromise = $timeout(function() {
        vm.page = 1;
        vm.loadSkills();
      }, 300);
    };

    vm.setCategoryFilter = function(cat) {
      vm.filters.category = (vm.filters.category === cat) ? '' : cat;
      vm.page = 1;
      vm.loadSkills();
    };

    vm.onSortChange = function() {
      vm.page = 1;
      vm.loadSkills();
    };

    vm.goToPage = function(p) {
      if (p < 1 || p > vm.totalPages || p === vm.page) return;
      vm.page = p;
      vm.loadSkills();
    };

    vm.loadSkills = function() {
      vm.isLoading = true;
      SkillService.getSkills({
        page: vm.page,
        page_size: vm.pageSize,
        search: vm.filters.search,
        category: vm.filters.category,
        sort_by: vm.filters.sort_by,
        sort_order: vm.filters.sort_order
      })
      .then(function(data) {
        vm.skills = data.items || [];
        vm.total = data.total || 0;
        vm.totalPages = data.total_pages || 1;
        vm.page = data.page || 1;
      })
      .catch(function(err) {
        console.error('Failed to load skills:', err);
        showToast('Error loading skills catalog', 'danger');
      })
      .finally(function() {
        vm.isLoading = false;
      });
    };

    vm.loadStats = function() {
      SkillService.getSkillStats()
        .then(function(data) {
          vm.stats = data;
        })
        .catch(function(err) {
          console.error('Failed to load skill stats:', err);
        });
    };

    // =====================================================================
    // Catalog CRUD Modals
    // =====================================================================

    vm.openCreateModal = function() {
      vm.formMode = 'create';
      vm.formData = {
        name: '',
        category: 'PROGRAMMING_LANGUAGE',
        description: '',
        aliases: ''
      };
      vm.formError = '';
      vm.formModalOpen = true;
    };

    vm.openEditModal = function(skill) {
      vm.formMode = 'edit';
      vm.formData = {
        id: skill.id,
        name: skill.name,
        category: skill.category,
        description: skill.description || '',
        aliases: skill.aliases || ''
      };
      vm.formError = '';
      vm.formModalOpen = true;
    };

    vm.closeFormModal = function() {
      vm.formModalOpen = false;
      vm.formData = {};
      vm.formError = '';
    };

    vm.saveSkill = function() {
      if (!vm.formData.name || !vm.formData.name.trim()) {
        vm.formError = 'Skill name is required.';
        return;
      }
      if (!vm.formData.category) {
        vm.formError = 'Please select a skill category.';
        return;
      }

      vm.isSubmitting = true;
      vm.formError = '';

      var payload = {
        name: vm.formData.name.trim(),
        category: vm.formData.category,
        description: vm.formData.description ? vm.formData.description.trim() : null,
        aliases: vm.formData.aliases ? vm.formData.aliases.trim() : null
      };

      var promise = (vm.formMode === 'create')
        ? SkillService.createSkill(payload)
        : SkillService.updateSkill(vm.formData.id, payload);

      promise
        .then(function(saved) {
          vm.closeFormModal();
          showToast(
            (vm.formMode === 'create' ? 'Skill created successfully!' : 'Skill updated successfully!'),
            'success'
          );
          vm.loadSkills();
          vm.loadStats();

          // If in contextual mode and just created a skill, auto-prompt to attach it
          if (vm.contextualAppId || vm.contextualJdId) {
            vm.openAddMappingModal(saved);
          }
        })
        .catch(function(err) {
          if (err.status === 409) {
            vm.formError = err.data && err.data.detail ? err.data.detail : 'Skill with this name already exists in your catalog.';
          } else if (err.status === 422) {
            vm.formError = 'Validation error: Please check all required fields.';
          } else {
            vm.formError = err.data && err.data.detail ? err.data.detail : 'An unexpected error occurred.';
          }
        })
        .finally(function() {
          vm.isSubmitting = false;
        });
    };

    // Delete Modal
    vm.openDeleteModal = function(skill) {
      vm.deleteTarget = skill;
      vm.deleteError = '';
      vm.deleteModalOpen = true;
    };

    vm.closeDeleteModal = function() {
      vm.deleteModalOpen = false;
      vm.deleteTarget = null;
      vm.deleteError = '';
    };

    vm.confirmDelete = function() {
      if (!vm.deleteTarget) return;
      vm.isDeleting = true;
      vm.deleteError = '';

      SkillService.deleteSkill(vm.deleteTarget.id)
        .then(function() {
          vm.closeDeleteModal();
          showToast('Skill deleted from catalog.', 'info');
          vm.loadSkills();
          vm.loadStats();
        })
        .catch(function(err) {
          if (err.status === 409) {
            vm.deleteError = err.data && err.data.detail ? err.data.detail : 'Cannot delete: Skill is linked to applications or job descriptions.';
          } else {
            vm.deleteError = err.data && err.data.detail ? err.data.detail : 'Failed to delete skill.';
          }
        })
        .finally(function() {
          vm.isDeleting = false;
        });
    };

    // =====================================================================
    // Contextual Mapping Mode (Applications & Job Descriptions)
    // =====================================================================

    vm.initContextualMode = function() {
      var searchParams = $location.search();
      var appId = searchParams.application_id ? parseInt(searchParams.application_id, 10) : null;
      var jdId = searchParams.job_description_id ? parseInt(searchParams.job_description_id, 10) : null;

      if (appId) {
        vm.contextualAppId = appId;
        vm.isLoadingContext = true;
        $q.all([
          ApplicationService.getApplication(appId),
          SkillService.getApplicationSkills(appId)
        ])
        .then(function(results) {
          vm.contextualApp = results[0];
          vm.contextualMappedSkills = results[1] || [];
        })
        .catch(function(err) {
          console.error('Failed to load contextual application:', err);
          showToast('Could not load application context.', 'warning');
        })
        .finally(function() {
          vm.isLoadingContext = false;
        });
      } else if (jdId) {
        vm.contextualJdId = jdId;
        vm.isLoadingContext = true;
        $q.all([
          JobDescriptionService.getJobDescription(jdId),
          SkillService.getJobDescriptionSkills(jdId)
        ])
        .then(function(results) {
          vm.contextualJd = results[0];
          vm.contextualMappedSkills = results[1] || [];
        })
        .catch(function(err) {
          console.error('Failed to load contextual job description:', err);
          showToast('Could not load job description context.', 'warning');
        })
        .finally(function() {
          vm.isLoadingContext = false;
        });
      }
    };

    vm.exitContextualMode = function() {
      vm.contextualAppId = null;
      vm.contextualJdId = null;
      vm.contextualApp = null;
      vm.contextualJd = null;
      vm.contextualMappedSkills = [];
      $location.search('application_id', null);
      $location.search('job_description_id', null);
    };

    vm.isSkillMappedToContext = function(skillId) {
      if (!vm.contextualMappedSkills || !vm.contextualMappedSkills.length) return false;
      return vm.contextualMappedSkills.some(function(m) { return m.skill_id === skillId; });
    };

    // Mapping Modal (Add or Edit)
    vm.openAddMappingModal = function(skill) {
      vm.mappingMode = 'add';
      vm.mappingError = '';
      if (vm.contextualAppId) {
        vm.mappingData = {
          skill_id: skill ? skill.id : null,
          skill_name: skill ? skill.name : '',
          proficiency: 'INTERMEDIATE',
          years_experience: null,
          is_primary: false
        };
      } else if (vm.contextualJdId) {
        vm.mappingData = {
          skill_id: skill ? skill.id : null,
          skill_name: skill ? skill.name : '',
          importance: 'REQUIRED',
          source_section: 'REQUIREMENTS'
        };
      }
      vm.mappingModalOpen = true;
    };

    vm.openEditMappingModal = function(mappingItem) {
      vm.mappingMode = 'edit';
      vm.mappingError = '';
      if (vm.contextualAppId) {
        vm.mappingData = {
          skill_id: mappingItem.skill_id,
          skill_name: mappingItem.skill_name,
          proficiency: mappingItem.proficiency || 'UNKNOWN',
          years_experience: mappingItem.years_experience,
          is_primary: !!mappingItem.is_primary
        };
      } else if (vm.contextualJdId) {
        vm.mappingData = {
          skill_id: mappingItem.skill_id,
          skill_name: mappingItem.skill_name,
          importance: mappingItem.importance || 'REQUIRED',
          source_section: mappingItem.source_section || 'REQUIREMENTS'
        };
      }
      vm.mappingModalOpen = true;
    };

    vm.closeMappingModal = function() {
      vm.mappingModalOpen = false;
      vm.mappingData = {};
      vm.mappingError = '';
    };

    vm.saveMapping = function() {
      if (!vm.mappingData.skill_id) {
        vm.mappingError = 'Please choose a skill to map.';
        return;
      }

      vm.isSubmittingMapping = true;
      vm.mappingError = '';

      var promise;
      if (vm.contextualAppId) {
        var appPayload = {
          proficiency: vm.mappingData.proficiency,
          years_experience: vm.mappingData.years_experience !== '' && vm.mappingData.years_experience !== null ? parseFloat(vm.mappingData.years_experience) : null,
          is_primary: !!vm.mappingData.is_primary
        };
        if (vm.mappingMode === 'add') {
          appPayload.skill_id = vm.mappingData.skill_id;
          promise = SkillService.addApplicationSkill(vm.contextualAppId, appPayload);
        } else {
          promise = SkillService.updateApplicationSkill(vm.contextualAppId, vm.mappingData.skill_id, appPayload);
        }
      } else if (vm.contextualJdId) {
        var jdPayload = {
          importance: vm.mappingData.importance,
          source_section: vm.mappingData.source_section
        };
        if (vm.mappingMode === 'add') {
          jdPayload.skill_id = vm.mappingData.skill_id;
          promise = SkillService.addJobDescriptionSkill(vm.contextualJdId, jdPayload);
        } else {
          promise = SkillService.updateJobDescriptionSkill(vm.contextualJdId, vm.mappingData.skill_id, jdPayload);
        }
      }

      if (!promise) {
        vm.isSubmittingMapping = false;
        return;
      }

      promise
        .then(function() {
          vm.closeMappingModal();
          showToast('Skill mapping updated successfully!', 'success');
          // Reload mapped skills and catalog counts
          if (vm.contextualAppId) {
            SkillService.getApplicationSkills(vm.contextualAppId).then(function(list) {
              vm.contextualMappedSkills = list || [];
            });
          } else if (vm.contextualJdId) {
            SkillService.getJobDescriptionSkills(vm.contextualJdId).then(function(list) {
              vm.contextualMappedSkills = list || [];
            });
          }
          vm.loadSkills();
          vm.loadStats();
        })
        .catch(function(err) {
          if (err.status === 409) {
            vm.mappingError = err.data && err.data.detail ? err.data.detail : 'This skill is already mapped.';
          } else {
            vm.mappingError = err.data && err.data.detail ? err.data.detail : 'Failed to save skill mapping.';
          }
        })
        .finally(function() {
          vm.isSubmittingMapping = false;
        });
    };

    vm.removeMapping = function(mappingItem) {
      if (!confirm('Remove skill "' + mappingItem.skill_name + '" from this record?')) return;

      var promise;
      if (vm.contextualAppId) {
        promise = SkillService.removeApplicationSkill(vm.contextualAppId, mappingItem.skill_id);
      } else if (vm.contextualJdId) {
        promise = SkillService.removeJobDescriptionSkill(vm.contextualJdId, mappingItem.skill_id);
      }

      if (!promise) return;

      promise
        .then(function() {
          showToast('Skill unlinked successfully.', 'info');
          if (vm.contextualAppId) {
            SkillService.getApplicationSkills(vm.contextualAppId).then(function(list) {
              vm.contextualMappedSkills = list || [];
            });
          } else if (vm.contextualJdId) {
            SkillService.getJobDescriptionSkills(vm.contextualJdId).then(function(list) {
              vm.contextualMappedSkills = list || [];
            });
          }
          vm.loadSkills();
          vm.loadStats();
        })
        .catch(function(err) {
          showToast('Failed to unlink skill.', 'danger');
        });
    };

    // Initialize
    vm.loadSkills();
    vm.loadStats();
    vm.initContextualMode();
  }
]);
