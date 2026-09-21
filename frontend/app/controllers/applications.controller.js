'use strict';

/**
 * ApplicationsController
 * Manages the listing, pagination, debounced search, status/location filtering,
 * creation, editing, status updating, and deletion of job applications via ApplicationService.
 */
angular.module('jobCommandCenter')
.controller('ApplicationsController', ['$timeout', 'ApplicationService', 'ResumeService', function($timeout, ApplicationService, ResumeService) {
  var vm = this;

  // View state
  vm.isLoading = false;
  vm.errorMessage = '';
  vm.hasLoadedOnce = false;
  vm.applications = [];
  vm.availableResumes = [];

  // Search & Filter parameters
  vm.searchQuery = '';
  vm.statusFilter = '';
  vm.locationFilter = '';
  vm.sortBy = 'applied_date';
  vm.sortOrder = 'desc';

  // Pagination state
  vm.page = 1;
  vm.pageSize = 10;
  vm.total = 0;
  vm.totalPages = 1;

  // Filter dropdown options
  vm.statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'SAVED', label: 'Saved' },
    { value: 'APPLIED', label: 'Applied' },
    { value: 'ASSESSMENT', label: 'Assessment' },
    { value: 'INTERVIEW', label: 'Interview' },
    { value: 'OFFER', label: 'Offer' },
    { value: 'REJECTED', label: 'Rejected' },
    { value: 'WITHDRAWN', label: 'Withdrawn' }
  ];

  vm.locationOptions = [
    { value: '', label: 'All Locations' },
    { value: 'Bangalore', label: 'Bangalore' },
    { value: 'Hyderabad', label: 'Hyderabad' },
    { value: 'Pune', label: 'Pune' },
    { value: 'Chennai', label: 'Chennai' },
    { value: 'Remote', label: 'Remote' }
  ];

  vm.employmentTypes = [
    'Full-time',
    'Part-time',
    'Contract',
    'Internship'
  ];

  // Debounce timer handle
  var searchTimeout = null;

  // Modal states
  vm.showModal = false;
  vm.modalMode = 'create'; // 'create' | 'edit'
  vm.modalTitle = 'Add Application';
  vm.isSubmitting = false;
  vm.formError = '';
  vm.formData = {};

  vm.showDeleteModal = false;
  vm.jobToDelete = null;
  vm.isDeleting = false;
  vm.deleteError = '';

  /**
   * Fetch applications from real backend API
   */
  vm.loadApplications = function() {
    vm.isLoading = true;
    vm.errorMessage = '';

    var params = {
      search: vm.searchQuery,
      status: vm.statusFilter,
      location: vm.locationFilter,
      sort_by: vm.sortBy,
      sort_order: vm.sortOrder,
      page: vm.page,
      page_size: vm.pageSize
    };

    ApplicationService.getApplications(params)
      .then(function(res) {
        vm.applications = res.items;
        vm.page = res.page;
        vm.pageSize = res.pageSize;
        vm.total = res.total;
        vm.totalPages = res.totalPages;
        vm.isLoading = false;
        vm.hasLoadedOnce = true;
      })
      .catch(function(err) {
        vm.errorMessage = typeof err === 'string' ? err : 'Unable to load applications. Please check your connection and try again.';
        vm.isLoading = false;
        vm.hasLoadedOnce = true;
      });
  };

  /**
   * Search input handler with 350ms debounce
   */
  vm.onSearchChange = function() {
    if (searchTimeout) {
      $timeout.cancel(searchTimeout);
    }
    searchTimeout = $timeout(function() {
      vm.page = 1;
      vm.loadApplications();
    }, 350);
  };

  /**
   * Filter/sort changes immediately reload with page reset
   */
  vm.onFilterChange = function() {
    vm.page = 1;
    vm.loadApplications();
  };

  /**
   * Reset all filters to default
   */
  vm.resetFilters = function() {
    vm.searchQuery = '';
    vm.statusFilter = '';
    vm.locationFilter = '';
    vm.sortBy = 'applied_date';
    vm.sortOrder = 'desc';
    vm.page = 1;
    vm.loadApplications();
  };

  /**
   * Pagination navigation
   */
  vm.goToPage = function(pageNum) {
    if (pageNum >= 1 && pageNum <= vm.totalPages && pageNum !== vm.page) {
      vm.page = pageNum;
      vm.loadApplications();
    }
  };

  vm.prevPage = function() {
    if (vm.page > 1) {
      vm.goToPage(vm.page - 1);
    }
  };

  vm.nextPage = function() {
    if (vm.page < vm.totalPages) {
      vm.goToPage(vm.page + 1);
    }
  };

  /**
   * Generates pagination array [1, 2, 3...]
   */
  vm.getPagesArray = function() {
    var pages = [];
    for (var i = 1; i <= vm.totalPages; i++) {
      pages.push(i);
    }
    return pages;
  };

  /**
   * Load available resumes for the application form dropdown
   */
  vm.loadAvailableResumes = function() {
    ResumeService.getResumes({ page_size: 100 })
      .then(function(res) {
        vm.availableResumes = res.items || [];
      })
      .catch(function(err) {
        console.error('Failed to load resumes for application form:', err);
      });
  };

  /**
   * Open modal to create a new application
   */
  vm.openCreateModal = function() {
    vm.modalMode = 'create';
    vm.modalTitle = 'Add Job Application';
    vm.formError = '';
    vm.isSubmitting = false;

    vm.loadAvailableResumes();

    var defaultResumeId = null;
    if (vm.availableResumes && vm.availableResumes.length > 0) {
      var activeResume = vm.availableResumes.find(function(r) { return r.is_active; });
      if (activeResume) defaultResumeId = activeResume.id;
    }

    var today = new Date().toISOString().slice(0, 10);
    vm.formData = {
      company_name: '',
      job_title: '',
      location: '',
      job_url: '',
      salary: '',
      employment_type: 'Full-time',
      status: 'APPLIED',
      applied_date: today,
      job_description: '',
      resume_id: defaultResumeId
    };
    vm.showModal = true;
  };

  /**
   * Open modal to edit an existing application
   */
  vm.openEditModal = function(job) {
    vm.modalMode = 'edit';
    vm.modalTitle = 'Edit Job Application';
    vm.formError = '';
    vm.isSubmitting = false;

    vm.loadAvailableResumes();

    var resId = null;
    if (job.resume_id !== undefined && job.resume_id !== null) {
      resId = job.resume_id;
    } else if (job.resume && job.resume.id) {
      resId = job.resume.id;
    }

    vm.formData = {
      id: job.id,
      company_name: (job.company && job.company.name) ? job.company.name : (job.company || ''),
      job_title: job.job_title || job.jobTitle || '',
      location: job.location || '',
      job_url: job.job_url || job.jobUrl || '',
      salary: job.salary || '',
      employment_type: job.employment_type || job.employmentType || job.jobType || 'Full-time',
      status: job.status || 'SAVED',
      applied_date: job.applied_date || job.appliedDate || '',
      job_description: job.job_description || job.jobDescription || '',
      resume_id: resId
    };
    vm.showModal = true;
  };

  /**
   * Close create/edit modal
   */
  vm.closeModal = function() {
    vm.showModal = false;
    vm.formError = '';
    vm.formData = {};
  };

  /**
   * Submit create or edit form
   */
  vm.submitForm = function() {
    if (!vm.formData.company_name || !vm.formData.company_name.trim()) {
      vm.formError = 'Company name is required.';
      return;
    }
    if (!vm.formData.job_title || !vm.formData.job_title.trim()) {
      vm.formError = 'Job title is required.';
      return;
    }

    if (vm.formData.resume_id) {
      vm.formData.resume_id = Number(vm.formData.resume_id);
    } else {
      vm.formData.resume_id = null;
    }

    vm.isSubmitting = true;
    vm.formError = '';

    var promise;
    if (vm.modalMode === 'create') {
      promise = ApplicationService.createApplication(vm.formData);
    } else {
      promise = ApplicationService.updateApplication(vm.formData.id, vm.formData);
    }

    promise
      .then(function() {
        vm.isSubmitting = false;
        vm.closeModal();
        vm.loadApplications();
      })
      .catch(function(err) {
        vm.isSubmitting = false;
        vm.formError = typeof err === 'string' ? err : 'Operation failed. Please verify form values.';
      });
  };

  /**
   * Quick status change from inline dropdown
   */
  vm.updateStatus = function(job, newStatus) {
    if (!job || !newStatus || job.status === newStatus) return;

    var oldStatus = job.status;
    job.status = newStatus; // optimistic UI update

    ApplicationService.updateStatus(job.id, newStatus)
      .then(function(updatedApp) {
        job.status = updatedApp.status;
      })
      .catch(function(err) {
        job.status = oldStatus; // revert on failure
        console.error('Failed to update application status:', err);
      });
  };

  /**
   * Open Delete confirmation dialog
   */
  vm.confirmDelete = function(job) {
    vm.jobToDelete = job;
    vm.deleteError = '';
    vm.isDeleting = false;
    vm.showDeleteModal = true;
  };

  /**
   * Close Delete confirmation modal
   */
  vm.closeDeleteModal = function() {
    vm.showDeleteModal = false;
    vm.jobToDelete = null;
    vm.deleteError = '';
  };

  /**
   * Execute permanent application deletion
   */
  vm.submitDelete = function() {
    if (!vm.jobToDelete) return;

    vm.isDeleting = true;
    vm.deleteError = '';

    ApplicationService.deleteApplication(vm.jobToDelete.id)
      .then(function() {
        vm.isDeleting = false;
        vm.closeDeleteModal();
        // Reload list to synchronize pagination and counts
        vm.loadApplications();
      })
      .catch(function(err) {
        vm.isDeleting = false;
        vm.deleteError = typeof err === 'string' ? err : 'Unable to delete application.';
      });
  };

  // Initial load
  vm.loadApplications();
}]);
