'use strict';

/**
 * JobDescriptionsController
 * Coordinates job description browsing, section inspection, modal workflows,
 * filtering, clipboard extraction, and application linking.
 */
angular.module('jobCommandCenter')
.controller('JobDescriptionsController', [
  'JobDescriptionService',
  'ApplicationService',
  '$scope',
  '$routeParams',
  '$location',
  '$timeout',
  function(JobDescriptionService, ApplicationService, $scope, $routeParams, $location, $timeout) {
    var vm = this;

    // View & data state
    vm.jobDescriptions = [];
    vm.isLoading = true;
    vm.isSubmitting = false;
    vm.isDeleting = false;
    vm.total = 0;
    vm.page = 1;
    vm.pageSize = 9;
    vm.totalPages = 1;

    // Filter & sort options
    vm.filters = {
      search: '',
      employment_type: '',
      work_arrangement: '',
      sort_by: 'captured_at',
      sort_order: 'desc'
    };

    vm.stats = {
      total: 0,
      remote: 0,
      hybrid: 0,
      fullTime: 0
    };

    // Detail Modal State
    vm.detailModalOpen = false;
    vm.selectedJd = null;
    vm.activeDetailTab = 'all';

    // Create / Edit Modal State
    vm.formModalOpen = false;
    vm.formMode = 'create'; // 'create' | 'edit'
    vm.formData = {};
    vm.formError = '';
    vm.availableApplications = [];
    vm.isLoadingApplications = false;

    // Delete Modal State
    vm.deleteModalOpen = false;
    vm.deleteTarget = null;
    vm.deleteError = '';

    // Copy Notification Toast
    vm.copyToastMessage = '';
    vm.copiedSectionKey = '';
    var copyToastTimer = null;
    var searchTimer = null;

    /**
     * Compute overview stats across JDs
     */
    function updateStats(items, totalCount) {
      vm.stats.total = totalCount;
      var remoteCount = 0;
      var hybridCount = 0;
      var fullTimeCount = 0;

      (items || []).forEach(function(item) {
        if (item.work_arrangement === 'REMOTE') remoteCount++;
        if (item.work_arrangement === 'HYBRID') hybridCount++;
        if (item.employment_type === 'FULL_TIME') fullTimeCount++;
      });

      vm.stats.remote = remoteCount;
      vm.stats.hybrid = hybridCount;
      vm.stats.fullTime = fullTimeCount;
    }

    /**
     * Load job descriptions from backend API
     */
    vm.loadJobDescriptions = function() {
      vm.isLoading = true;
      var params = {
        page: vm.page,
        page_size: vm.pageSize,
        search: vm.filters.search,
        employment_type: vm.filters.employment_type,
        work_arrangement: vm.filters.work_arrangement,
        sort_by: vm.filters.sort_by,
        sort_order: vm.filters.sort_order
      };

      JobDescriptionService.getJobDescriptions(params)
        .then(function(result) {
          vm.jobDescriptions = result.items || [];
          vm.total = result.total || 0;
          vm.totalPages = result.totalPages || 1;
          vm.isLoading = false;
          updateStats(vm.jobDescriptions, vm.total);

          // Check if $routeParams requested a specific JD
          if ($routeParams.id && !vm.selectedJd) {
            var targetId = parseInt($routeParams.id, 10);
            var found = vm.jobDescriptions.find(function(j) { return j.id === targetId; });
            if (found) {
              vm.openDetailModal(found);
            } else {
              // Fetch directly by ID
              JobDescriptionService.getJobDescription(targetId)
                .then(function(jd) {
                  vm.openDetailModal(jd);
                })
                .catch(function(err) {
                  console.warn('Requested JD ID not found:', err);
                });
            }
          }
        })
        .catch(function(err) {
          console.error('Failed to load job descriptions:', err);
          vm.isLoading = false;
        });
    };

    /**
     * Debounced search handler
     */
    vm.onSearchChange = function() {
      if (searchTimer) $timeout.cancel(searchTimer);
      searchTimer = $timeout(function() {
        vm.page = 1;
        vm.loadJobDescriptions();
      }, 300);
    };

    /**
     * Filter change handler
     */
    vm.applyFilters = function() {
      vm.page = 1;
      vm.loadJobDescriptions();
    };

    /**
     * Reset filters to defaults
     */
    vm.resetFilters = function() {
      vm.filters.search = '';
      vm.filters.employment_type = '';
      vm.filters.work_arrangement = '';
      vm.filters.sort_by = 'captured_at';
      vm.filters.sort_order = 'desc';
      vm.page = 1;
      vm.loadJobDescriptions();
    };

    /**
     * Pagination handlers
     */
    vm.goToPage = function(pageNum) {
      if (pageNum < 1 || pageNum > vm.totalPages || pageNum === vm.page) return;
      vm.page = pageNum;
      vm.loadJobDescriptions();
    };

    /**
     * Load applications for the dropdown selector
     */
    vm.loadAvailableApplications = function() {
      vm.isLoadingApplications = true;
      ApplicationService.getApplications({ page_size: 100, sort_by: 'created_at', sort_order: 'desc' })
        .then(function(result) {
          vm.availableApplications = (result.items || []);
          vm.isLoadingApplications = false;
        })
        .catch(function(err) {
          console.error('Failed to load applications for JD attachment:', err);
          vm.isLoadingApplications = false;
        });
    };

    /**
     * Pre-populate title and company when user picks an application in the modal
     */
    vm.onApplicationSelected = function() {
      if (!vm.formData.application_id) return;
      var selectedApp = vm.availableApplications.find(function(a) {
        return a.id === parseInt(vm.formData.application_id, 10);
      });
      if (selectedApp) {
        if (!vm.formData.title) vm.formData.title = selectedApp.job_title;
        if (!vm.formData.company_name) vm.formData.company_name = selectedApp.company ? selectedApp.company.name : '';
        if (!vm.formData.location && selectedApp.location) vm.formData.location = selectedApp.location;
        if (!vm.formData.job_url && selectedApp.job_url) vm.formData.job_url = selectedApp.job_url;
        if (!vm.formData.salary && selectedApp.salary) vm.formData.salary = selectedApp.salary;
      }
    };

    /**
     * Open Detail Modal
     */
    vm.openDetailModal = function(jd) {
      vm.selectedJd = jd;
      vm.activeDetailTab = 'all';
      vm.detailModalOpen = true;
    };

    vm.closeDetailModal = function() {
      vm.detailModalOpen = false;
      vm.selectedJd = null;
    };

    vm.setDetailTab = function(tabName) {
      vm.activeDetailTab = tabName;
    };

    /**
     * Open Create Modal
     */
    vm.openCreateModal = function(preselectedAppId) {
      vm.formMode = 'create';
      vm.formError = '';
      vm.formData = {
        application_id: preselectedAppId ? parseInt(preselectedAppId, 10) : null,
        title: '',
        company_name: '',
        job_url: '',
        location: '',
        employment_type: 'FULL_TIME',
        work_arrangement: 'HYBRID',
        salary: '',
        experience_required: '',
        description: '',
        responsibilities: '',
        requirements: '',
        qualifications: '',
        benefits: ''
      };
      vm.formModalOpen = true;
      vm.loadAvailableApplications();

      if (preselectedAppId) {
        $timeout(function() {
          vm.onApplicationSelected();
        }, 300);
      }
    };

    /**
     * Open Edit Modal
     */
    vm.openEditModal = function(jd) {
      vm.formMode = 'edit';
      vm.formError = '';
      vm.formData = {
        id: jd.id,
        application_id: jd.application_id,
        title: jd.title,
        company_name: jd.company_name,
        job_url: jd.job_url || '',
        location: jd.location || '',
        employment_type: jd.employment_type || 'FULL_TIME',
        work_arrangement: jd.work_arrangement || 'HYBRID',
        salary: jd.salary || '',
        experience_required: jd.experience_required || '',
        description: jd.description || '',
        responsibilities: jd.responsibilities || '',
        requirements: jd.requirements || '',
        qualifications: jd.qualifications || '',
        benefits: jd.benefits || ''
      };
      vm.formModalOpen = true;
    };

    vm.closeFormModal = function() {
      if (vm.isSubmitting) return;
      vm.formModalOpen = false;
      vm.formData = {};
      vm.formError = '';
    };

    /**
     * Submit Create or Edit Form
     */
    vm.submitForm = function() {
      if (!vm.formData.title || !vm.formData.title.trim()) {
        vm.formError = 'Job title is required.';
        return;
      }
      if (!vm.formData.company_name || !vm.formData.company_name.trim()) {
        vm.formError = 'Company name is required.';
        return;
      }

      vm.isSubmitting = true;
      vm.formError = '';

      if (vm.formMode === 'create') {
        if (!vm.formData.application_id) {
          vm.formError = 'Please link this job description to an application.';
          vm.isSubmitting = false;
          return;
        }

        var createPayload = angular.copy(vm.formData);
        createPayload.application_id = parseInt(createPayload.application_id, 10);

        JobDescriptionService.createJobDescription(createPayload)
          .then(function(created) {
            vm.isSubmitting = false;
            vm.formModalOpen = false;
            vm.showCopyToast('Job description captured successfully!');
            vm.loadJobDescriptions();
          })
          .catch(function(err) {
            vm.isSubmitting = false;
            vm.formError = err || 'Failed to create job description.';
          });
      } else {
        var updatePayload = angular.copy(vm.formData);
        var jdId = updatePayload.id;
        delete updatePayload.id;
        delete updatePayload.application_id;
        delete updatePayload.captured_at;

        JobDescriptionService.updateJobDescription(jdId, updatePayload)
          .then(function(updated) {
            vm.isSubmitting = false;
            vm.formModalOpen = false;
            if (vm.selectedJd && vm.selectedJd.id === jdId) {
              vm.selectedJd = updated;
            }
            vm.showCopyToast('Job description updated successfully!');
            vm.loadJobDescriptions();
          })
          .catch(function(err) {
            vm.isSubmitting = false;
            vm.formError = err || 'Failed to update job description.';
          });
      }
    };

    /**
     * Delete Confirmation Modal
     */
    vm.openDeleteModal = function(jd) {
      vm.deleteTarget = jd;
      vm.deleteError = '';
      vm.deleteModalOpen = true;
    };

    vm.closeDeleteModal = function() {
      if (vm.isDeleting) return;
      vm.deleteModalOpen = false;
      vm.deleteTarget = null;
      vm.deleteError = '';
    };

    vm.submitDelete = function() {
      if (!vm.deleteTarget) return;

      vm.isDeleting = true;
      vm.deleteError = '';

      JobDescriptionService.deleteJobDescription(vm.deleteTarget.id)
        .then(function() {
          vm.isDeleting = false;
          vm.deleteModalOpen = false;
          if (vm.selectedJd && vm.selectedJd.id === vm.deleteTarget.id) {
            vm.closeDetailModal();
          }
          vm.deleteTarget = null;
          vm.showCopyToast('Job description deleted. Application remains intact.');
          vm.loadJobDescriptions();
        })
        .catch(function(err) {
          vm.isDeleting = false;
          vm.deleteError = err || 'Failed to delete job description.';
        });
    };

    /**
     * Clipboard Copy helper with toast feedback
     */
    vm.copyToClipboard = function(text, label, sectionKey) {
      if (!text || !text.trim()) {
        vm.showCopyToast('Section is empty, nothing to copy.');
        return;
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
          $scope.$apply(function() {
            vm.copiedSectionKey = sectionKey || '';
            vm.showCopyToast('Copied ' + (label || 'content') + ' to clipboard!');
          });
        }).catch(function(err) {
          fallbackCopy(text, label, sectionKey);
        });
      } else {
        fallbackCopy(text, label, sectionKey);
      }
    };

    function fallbackCopy(text, label, sectionKey) {
      try {
        var textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        vm.copiedSectionKey = sectionKey || '';
        vm.showCopyToast('Copied ' + (label || 'content') + ' to clipboard!');
      } catch (e) {
        console.error('Clipboard copy failed:', e);
        vm.showCopyToast('Unable to copy automatically. Please select text manually.');
      }
    }

    /**
     * Copy entire structured JD formatted with Markdown section headers
     */
    vm.copyEntireJd = function(jd) {
      if (!jd) return;
      var lines = [];
      lines.push('# ' + jd.title + ' at ' + jd.company_name);
      if (jd.location) lines.push('**Location:** ' + jd.location);
      if (jd.employment_type) lines.push('**Employment Type:** ' + jd.employmentTypeLabel);
      if (jd.work_arrangement) lines.push('**Work Arrangement:** ' + jd.workArrangementLabel);
      if (jd.salary) lines.push('**Salary:** ' + jd.salary);
      if (jd.experience_required) lines.push('**Experience:** ' + jd.experience_required);
      if (jd.job_url) lines.push('**Posting URL:** ' + jd.job_url);
      lines.push('');

      if (jd.hasDescription) {
        lines.push('## Overview & Description');
        lines.push(jd.description.trim());
        lines.push('');
      }
      if (jd.hasResponsibilities) {
        lines.push('## Responsibilities');
        lines.push(jd.responsibilities.trim());
        lines.push('');
      }
      if (jd.hasRequirements) {
        lines.push('## Requirements');
        lines.push(jd.requirements.trim());
        lines.push('');
      }
      if (jd.hasQualifications) {
        lines.push('## Preferred Qualifications');
        lines.push(jd.qualifications.trim());
        lines.push('');
      }
      if (jd.hasBenefits) {
        lines.push('## Benefits & Perks');
        lines.push(jd.benefits.trim());
        lines.push('');
      }

      vm.copyToClipboard(lines.join('\n'), 'full Job Description', 'full');
    };

    /**
     * Show transient notification toast
     */
    vm.showCopyToast = function(message) {
      vm.copyToastMessage = message;
      if (copyToastTimer) $timeout.cancel(copyToastTimer);
      copyToastTimer = $timeout(function() {
        vm.copyToastMessage = '';
        vm.copiedSectionKey = '';
      }, 2800);
    };

    // Check if opened with pre-selected application_id
    if ($routeParams.application_id) {
      vm.openCreateModal($routeParams.application_id);
    }

    // Initial load
    vm.loadJobDescriptions();
  }
]);
