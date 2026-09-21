'use strict';

/**
 * InterviewsController
 * State coordinator for interview rounds, scheduling, preparation notes,
 * and status transitions connected directly to FastAPI REST persistence.
 */
angular.module('jobCommandCenter')
.controller('InterviewsController', [
  'InterviewService',
  'ApplicationService',
  '$timeout',
  function(InterviewService, ApplicationService, $timeout) {
    var vm = this;

    // View & Loading states
    vm.isLoading = true;
    vm.isSaving = false;
    vm.activeTab = 'upcoming'; // 'upcoming', 'past', 'all'

    // Data lists
    vm.interviews = [];
    vm.upcomingInterviews = [];
    vm.pastInterviews = [];
    vm.applications = [];

    // Filter and search criteria
    vm.filters = {
      search: '',
      status: '',
      interview_type: '',
      page: 1,
      page_size: 50,
      sort_by: 'scheduled_at',
      sort_order: 'asc'
    };

    // Summary KPIs
    vm.stats = {
      total: 0,
      upcoming: 0,
      completed: 0,
      scheduled: 0
    };

    // Modal state
    vm.modalMode = 'create'; // 'create' | 'edit'
    vm.editingId = null;
    vm.formData = {};
    vm.formErrors = {};
    vm.interviewToDelete = null;

    // Feedback notifications
    vm.alert = null;

    vm.showAlert = function(message, type) {
      vm.alert = { message: message, type: type || 'success' };
      $timeout(function() {
        vm.alert = null;
      }, 4000);
    };

    /**
     * Compute human-readable countdowns or relative time strings
     */
    vm.getCountdown = function(scheduledAt) {
      if (!scheduledAt) return 'Time TBD';
      var now = new Date();
      var target = new Date(scheduledAt);
      var diffMs = target.getTime() - now.getTime();

      if (diffMs > 0) {
        var diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        var diffDays = Math.floor(diffHours / 24);

        if (diffDays > 1) {
          return 'In ' + diffDays + ' days';
        } else if (diffDays === 1) {
          return 'Tomorrow (' + (diffHours % 24) + 'h left)';
        } else if (diffHours > 0) {
          var diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
          return 'In ' + diffHours + 'h ' + diffMins + 'm';
        } else {
          var mins = Math.max(1, Math.floor(diffMs / (1000 * 60)));
          return 'Starts in ' + mins + 'm';
        }
      } else {
        var elapsedMs = Math.abs(diffMs);
        var elapsedDays = Math.floor(elapsedMs / (1000 * 60 * 60 * 24));
        if (elapsedDays === 0) return 'Earlier today';
        if (elapsedDays === 1) return 'Yesterday';
        return elapsedDays + ' days ago';
      }
    };

    /**
     * Get badge styling class and icon for interview types
     */
    vm.getTypeBadgeClass = function(type) {
      var t = (type || '').toUpperCase();
      switch (t) {
        case 'VIDEO':
          return 'bg-purple-subtle text-purple border border-purple-subtle';
        case 'TECHNICAL':
          return 'bg-info-subtle text-info border border-info-subtle';
        case 'PHONE':
          return 'bg-primary-subtle text-primary border border-primary-subtle';
        case 'HR':
          return 'bg-success-subtle text-success border border-success-subtle';
        case 'BEHAVIORAL':
          return 'bg-warning-subtle text-warning border border-warning-subtle';
        case 'ONSITE':
          return 'bg-secondary-subtle text-secondary border border-secondary-subtle';
        default:
          return 'bg-light text-dark border';
      }
    };

    vm.getTypeIcon = function(type) {
      var t = (type || '').toUpperCase();
      switch (t) {
        case 'VIDEO': return 'bi-camera-video';
        case 'TECHNICAL': return 'bi-code-slash';
        case 'PHONE': return 'bi-telephone';
        case 'HR': return 'bi-person-badge';
        case 'BEHAVIORAL': return 'bi-chat-dots';
        case 'ONSITE': return 'bi-building';
        default: return 'bi-calendar-event';
      }
    };

    /**
     * Get badge styling class for status
     */
    vm.getStatusBadgeClass = function(status) {
      var s = (status || '').toUpperCase();
      switch (s) {
        case 'SCHEDULED': return 'bg-primary-subtle text-primary border border-primary-subtle';
        case 'COMPLETED': return 'bg-success-subtle text-success border border-success-subtle';
        case 'CANCELLED': return 'bg-danger-subtle text-danger border border-danger-subtle';
        case 'RESCHEDULED': return 'bg-warning-subtle text-warning border border-warning-subtle';
        case 'NO_SHOW': return 'bg-dark-subtle text-dark border border-dark-subtle';
        default: return 'bg-secondary-subtle text-secondary border';
      }
    };

    /**
     * Load applications for selector dropdown
     */
    vm.loadApplications = function() {
      return ApplicationService.getApplications({ page_size: 100 })
        .then(function(res) {
          vm.applications = res.items || [];
        })
        .catch(function(err) {
          console.error('Error loading applications list:', err);
        });
    };

    /**
     * Load interviews with active filters and group into Upcoming / Past
     */
    vm.loadInterviews = function() {
      vm.isLoading = true;
      return InterviewService.getInterviews(vm.filters)
        .then(function(res) {
          var items = res.items || [];
          vm.interviews = items;

          var now = new Date();
          vm.upcomingInterviews = [];
          vm.pastInterviews = [];

          items.forEach(function(item) {
            var isUpcoming = false;
            if (item.scheduledAt && item.scheduledAt >= now && item.status !== 'COMPLETED' && item.status !== 'CANCELLED') {
              isUpcoming = true;
            } else if (item.status === 'SCHEDULED') {
              isUpcoming = true;
            }

            if (isUpcoming) {
              vm.upcomingInterviews.push(item);
            } else {
              vm.pastInterviews.push(item);
            }
          });

          // Sort upcoming ascending (nearest first)
          vm.upcomingInterviews.sort(function(a, b) {
            var timeA = a.scheduledAt ? a.scheduledAt.getTime() : Infinity;
            var timeB = b.scheduledAt ? b.scheduledAt.getTime() : Infinity;
            return timeA - timeB;
          });

          // Sort past descending (most recent first)
          vm.pastInterviews.sort(function(a, b) {
            var timeA = a.scheduledAt ? a.scheduledAt.getTime() : 0;
            var timeB = b.scheduledAt ? b.scheduledAt.getTime() : 0;
            return timeB - timeA;
          });

          // Compute summary stats
          vm.stats.total = items.length;
          vm.stats.upcoming = vm.upcomingInterviews.length;
          vm.stats.completed = items.filter(function(i) { return i.status === 'COMPLETED'; }).length;
          vm.stats.scheduled = items.filter(function(i) { return i.status === 'SCHEDULED'; }).length;

          vm.isLoading = false;
        })
        .catch(function(err) {
          console.error('Error loading interviews:', err);
          vm.showAlert('Failed to load interviews. Please check your connection.', 'danger');
          vm.isLoading = false;
        });
    };

    /**
     * Initial controller setup
     */
    vm.init = function() {
      vm.loadApplications();
      vm.loadInterviews();
    };

    // Filter triggers
    vm.onFilterChange = function() {
      vm.loadInterviews();
    };

    vm.clearFilters = function() {
      vm.filters.search = '';
      vm.filters.status = '';
      vm.filters.interview_type = '';
      vm.loadInterviews();
    };

    /**
     * Open Modal to Schedule New Interview
     */
    vm.openCreateModal = function() {
      vm.modalMode = 'create';
      vm.editingId = null;
      vm.formErrors = {};

      var tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      var dateStr = tomorrow.toISOString().split('T')[0];

      vm.formData = {
        application_id: vm.applications.length ? vm.applications[0].id : '',
        round_name: 'Technical Screen',
        interview_type: 'VIDEO',
        scheduled_date: dateStr,
        scheduled_time: '14:00',
        duration_minutes: 45,
        location: '',
        meeting_link: '',
        interviewer: '',
        interviewer_email: '',
        status: 'SCHEDULED',
        notes: ''
      };

      var modalEl = document.getElementById('interviewFormModal');
      if (modalEl && window.bootstrap) {
        var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
      }
    };

    /**
     * Open Modal to Edit Existing Interview
     */
    vm.openEditModal = function(interview) {
      vm.modalMode = 'edit';
      vm.editingId = interview.id;
      vm.formErrors = {};

      var dateStr = '';
      var timeStr = '10:00';
      if (interview.scheduledAt) {
        var d = interview.scheduledAt;
        var yyyy = d.getFullYear();
        var mm = String(d.getMonth() + 1).padStart(2, '0');
        var dd = String(d.getDate()).padStart(2, '0');
        dateStr = yyyy + '-' + mm + '-' + dd;

        var hh = String(d.getHours()).padStart(2, '0');
        var min = String(d.getMinutes()).padStart(2, '0');
        timeStr = hh + ':' + min;
      }

      vm.formData = {
        application_id: interview.application_id,
        round_name: interview.round_name || interview.roundName,
        interview_type: interview.interview_type || interview.interviewType || 'VIDEO',
        scheduled_date: dateStr,
        scheduled_time: timeStr,
        duration_minutes: interview.duration_minutes || interview.durationMinutes || 45,
        location: interview.location || '',
        meeting_link: interview.meeting_link || interview.meetingUrl || '',
        interviewer: interview.interviewer || interview.interviewerName || '',
        interviewer_email: interview.interviewer_email || interview.interviewerEmail || '',
        status: interview.status || 'SCHEDULED',
        notes: interview.notes || ''
      };

      var modalEl = document.getElementById('interviewFormModal');
      if (modalEl && window.bootstrap) {
        var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
      }
    };

    /**
     * Validate and Save Interview
     */
    vm.saveInterview = function() {
      vm.formErrors = {};

      if (!vm.formData.application_id) {
        vm.formErrors.application_id = 'Please select a job application.';
      }
      if (!vm.formData.round_name || !vm.formData.round_name.trim()) {
        vm.formErrors.round_name = 'Round name is required.';
      }
      if (!vm.formData.scheduled_date) {
        vm.formErrors.scheduled_date = 'Interview date is required.';
      }

      if (Object.keys(vm.formErrors).length > 0) {
        return;
      }

      vm.isSaving = true;

      // Construct scheduled_at ISO timestamp
      var scheduledAt = null;
      if (vm.formData.scheduled_date) {
        var time = vm.formData.scheduled_time || '00:00';
        scheduledAt = vm.formData.scheduled_date + 'T' + time + ':00';
      }

      var payload = {
        application_id: Number(vm.formData.application_id),
        round_name: vm.formData.round_name.trim(),
        interview_type: vm.formData.interview_type || 'VIDEO',
        scheduled_at: scheduledAt,
        duration_minutes: Number(vm.formData.duration_minutes || 45),
        location: vm.formData.location ? vm.formData.location.trim() : null,
        meeting_link: vm.formData.meeting_link ? vm.formData.meeting_link.trim() : null,
        interviewer: vm.formData.interviewer ? vm.formData.interviewer.trim() : null,
        interviewer_email: vm.formData.interviewer_email ? vm.formData.interviewer_email.trim() : null,
        status: vm.formData.status || 'SCHEDULED',
        notes: vm.formData.notes ? vm.formData.notes.trim() : null
      };

      var operation;
      if (vm.modalMode === 'create') {
        operation = InterviewService.createInterview(payload);
      } else {
        operation = InterviewService.updateInterview(vm.editingId, payload);
      }

      operation
        .then(function(saved) {
          vm.isSaving = false;
          var modalEl = document.getElementById('interviewFormModal');
          if (modalEl && window.bootstrap) {
            var modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
          }
          vm.showAlert(
            vm.modalMode === 'create' ? 'Interview scheduled successfully!' : 'Interview details updated successfully!',
            'success'
          );
          vm.loadInterviews();
        })
        .catch(function(err) {
          vm.isSaving = false;
          console.error('Error saving interview:', err);
          var msg = (err && err.detail) ? err.detail : 'Could not save interview. Please check inputs.';
          vm.showAlert(msg, 'danger');
        });
    };

    /**
     * Quick status transition directly from card
     */
    vm.updateInterviewStatus = function(interview, newStatus) {
      if (!newStatus || newStatus === interview.status) return;

      var oldStatus = interview.status;
      interview.status = newStatus;

      InterviewService.updateStatus(interview.id, newStatus)
        .then(function() {
          vm.showAlert('Status updated to ' + newStatus, 'success');
          vm.loadInterviews();
        })
        .catch(function(err) {
          interview.status = oldStatus;
          console.error('Error updating status:', err);
          vm.showAlert('Failed to update status.', 'danger');
        });
    };

    /**
     * Confirm interview deletion
     */
    vm.confirmDelete = function(interview) {
      vm.interviewToDelete = interview;
      var modalEl = document.getElementById('deleteInterviewModal');
      if (modalEl && window.bootstrap) {
        var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
      }
    };

    /**
     * Execute interview deletion
     */
    vm.deleteInterview = function() {
      if (!vm.interviewToDelete) return;
      vm.isSaving = true;

      InterviewService.deleteInterview(vm.interviewToDelete.id)
        .then(function() {
          vm.isSaving = false;
          var modalEl = document.getElementById('deleteInterviewModal');
          if (modalEl && window.bootstrap) {
            var modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
          }
          vm.showAlert('Interview removed successfully.', 'info');
          vm.interviewToDelete = null;
          vm.loadInterviews();
        })
        .catch(function(err) {
          vm.isSaving = false;
          console.error('Error deleting interview:', err);
          vm.showAlert('Failed to delete interview.', 'danger');
        });
    };

    vm.init();
  }
]);
