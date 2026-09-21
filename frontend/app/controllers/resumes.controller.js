'use strict';

/**
 * ResumesController
 * State coordinator for resume library, versioning, file uploads, active designation,
 * and application references.
 */
angular.module('jobCommandCenter')
.controller('ResumesController', ['ResumeService', '$scope', '$timeout', function(ResumeService, $scope, $timeout) {
  var vm = this;

  vm.resumes = [];
  vm.activeResume = null;
  vm.otherResumes = [];
  vm.isLoading = true;
  vm.isSubmitting = false;
  vm.isDeleting = false;
  vm.searchQuery = '';
  vm.fileTypeFilter = '';

  // Upload Modal State
  vm.uploadModalOpen = false;
  vm.uploadMode = 'new'; // 'new' | 'version'
  vm.targetResume = null;
  vm.uploadForm = {
    name: '',
    description: '',
    file: null
  };
  vm.uploadError = '';
  vm.uploadSuccess = '';

  // Edit Modal State
  vm.editModalOpen = false;
  vm.editForm = {
    name: '',
    description: ''
  };
  vm.editError = '';

  // Delete Modal State
  vm.deleteModalOpen = false;
  vm.deleteTarget = null;
  vm.deleteError = '';

  // Versions Modal State
  vm.versionsModalOpen = false;
  vm.versionHistory = [];
  vm.isLoadingVersions = false;

  var searchTimer = null;

  /**
   * Load resumes from backend API
   */
  vm.loadResumes = function() {
    vm.isLoading = true;
    var params = {
      search: vm.searchQuery,
      file_type: vm.fileTypeFilter,
      page_size: 50
    };

    ResumeService.getResumes(params)
      .then(function(result) {
        vm.resumes = result.items || [];
        vm.activeResume = vm.resumes.find(function(r) { return r.is_active; }) || null;
        vm.otherResumes = vm.resumes.filter(function(r) { return !r.is_active; });
        vm.isLoading = false;
      })
      .catch(function(err) {
        console.error('Failed to load resumes:', err);
        vm.isLoading = false;
      });
  };

  /**
   * Trigger debounced search
   */
  vm.onSearchChange = function() {
    if (searchTimer) $timeout.cancel(searchTimer);
    searchTimer = $timeout(function() {
      vm.loadResumes();
    }, 300);
  };

  /**
   * Clear all filters
   */
  vm.clearFilters = function() {
    vm.searchQuery = '';
    vm.fileTypeFilter = '';
    vm.loadResumes();
  };

  /**
   * Open upload modal in 'new' or 'version' mode
   */
  vm.openUploadModal = function(mode, resume) {
    vm.uploadMode = mode || 'new';
    vm.targetResume = resume || null;
    vm.uploadForm = {
      name: resume ? resume.name : '',
      description: '',
      file: null
    };
    vm.uploadError = '';
    vm.uploadSuccess = '';
    vm.uploadModalOpen = true;

    // Reset file input element if present
    var fileInput = document.getElementById('resumeFileInput');
    if (fileInput) fileInput.value = '';
  };

  vm.closeUploadModal = function() {
    if (vm.isSubmitting) return;
    vm.uploadModalOpen = false;
    vm.uploadError = '';
  };

  /**
   * Handle native file input change
   */
  vm.onFileSelected = function(element) {
    $scope.$apply(function() {
      if (element.files && element.files.length > 0) {
        var file = element.files[0];
        // Client-side quick size validation (10 MB)
        if (file.size > 10 * 1024 * 1024) {
          vm.uploadError = 'File is too large. Maximum size is 10 MB.';
          vm.uploadForm.file = null;
          element.value = '';
          return;
        }

        // Client-side quick extension check
        var name = file.name.toLowerCase();
        if (!name.endsWith('.pdf') && !name.endsWith('.docx')) {
          vm.uploadError = 'Unsupported file type. Only PDF and DOCX files are allowed.';
          vm.uploadForm.file = null;
          element.value = '';
          return;
        }

        vm.uploadError = '';
        vm.uploadForm.file = file;

        // Auto-populate resume name if empty
        if (!vm.uploadForm.name && vm.uploadMode === 'new') {
          var cleanName = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
          vm.uploadForm.name = cleanName;
        }
      }
    });
  };

  /**
   * Submit upload form (multipart)
   */
  vm.submitUpload = function() {
    if (!vm.uploadForm.file) {
      vm.uploadError = 'Please select a resume file (PDF or DOCX).';
      return;
    }

    if (!vm.uploadForm.name || !vm.uploadForm.name.trim()) {
      vm.uploadError = 'Please enter a name for this resume.';
      return;
    }

    vm.isSubmitting = true;
    vm.uploadError = '';

    var formData = new FormData();
    formData.append('file', vm.uploadForm.file);
    formData.append('name', vm.uploadForm.name.trim());
    if (vm.uploadForm.description && vm.uploadForm.description.trim()) {
      formData.append('description', vm.uploadForm.description.trim());
    }

    var requestPromise;
    if (vm.uploadMode === 'version' && vm.targetResume) {
      requestPromise = ResumeService.createVersion(vm.targetResume.id, formData);
    } else {
      requestPromise = ResumeService.uploadResume(formData);
    }

    requestPromise
      .then(function() {
        vm.isSubmitting = false;
        vm.uploadModalOpen = false;
        vm.loadResumes();
      })
      .catch(function(err) {
        vm.isSubmitting = false;
        var detail = (err.data && err.data.detail) || 'Resume upload failed. Please try again.';
        vm.uploadError = detail;
      });
  };

  /**
   * Designate resume as primary active resume
   */
  vm.activateResume = function(resume) {
    if (!resume || resume.is_active) return;

    ResumeService.activateResume(resume.id)
      .then(function() {
        vm.loadResumes();
      })
      .catch(function(err) {
        console.error('Failed to activate resume:', err);
      });
  };

  /**
   * Trigger authenticated download
   */
  vm.downloadResume = function(resume) {
    if (!resume) return;
    ResumeService.downloadResume(resume.id, resume.file_name)
      .catch(function(err) {
        console.error('Failed to download resume:', err);
      });
  };

  /**
   * Open Edit modal
   */
  vm.openEditModal = function(resume) {
    vm.targetResume = resume;
    vm.editForm = {
      name: resume.name,
      description: resume.description || ''
    };
    vm.editError = '';
    vm.editModalOpen = true;
  };

  vm.closeEditModal = function() {
    if (vm.isSubmitting) return;
    vm.editModalOpen = false;
    vm.editError = '';
  };

  vm.submitEdit = function() {
    if (!vm.editForm.name || !vm.editForm.name.trim()) {
      vm.editError = 'Resume name is required.';
      return;
    }

    vm.isSubmitting = true;
    vm.editError = '';

    ResumeService.updateResume(vm.targetResume.id, {
      name: vm.editForm.name.trim(),
      description: vm.editForm.description ? vm.editForm.description.trim() : null
    })
      .then(function() {
        vm.isSubmitting = false;
        vm.editModalOpen = false;
        vm.loadResumes();
      })
      .catch(function(err) {
        vm.isSubmitting = false;
        vm.editError = (err.data && err.data.detail) || 'Failed to update resume.';
      });
  };

  /**
   * Open Delete confirmation modal
   */
  vm.openDeleteModal = function(resume) {
    vm.deleteTarget = resume;
    vm.deleteError = '';
    vm.deleteModalOpen = true;
  };

  vm.closeDeleteModal = function() {
    if (vm.isDeleting) return;
    vm.deleteModalOpen = false;
    vm.deleteError = '';
  };

  vm.submitDelete = function() {
    if (!vm.deleteTarget) return;

    vm.isDeleting = true;
    vm.deleteError = '';

    ResumeService.deleteResume(vm.deleteTarget.id)
      .then(function() {
        vm.isDeleting = false;
        vm.deleteModalOpen = false;
        vm.loadResumes();
      })
      .catch(function(err) {
        vm.isDeleting = false;
        if (err.status === 409) {
          vm.deleteError = 'This resume is currently associated with one or more applications and cannot be deleted. Reassign those applications first.';
        } else {
          vm.deleteError = (err.data && err.data.detail) || 'Unable to delete resume. Please try again.';
        }
      });
  };

  /**
   * Open Version History modal
   */
  vm.openVersionsModal = function(resume) {
    vm.targetResume = resume;
    vm.versionHistory = [];
    vm.isLoadingVersions = true;
    vm.versionsModalOpen = true;

    ResumeService.getVersions(resume.id)
      .then(function(versions) {
        vm.versionHistory = versions;
        vm.isLoadingVersions = false;
      })
      .catch(function(err) {
        console.error('Failed to load version history:', err);
        vm.isLoadingVersions = false;
      });
  };

  vm.closeVersionsModal = function() {
    vm.versionsModalOpen = false;
  };

  // Initial load
  vm.loadResumes();
}]);
