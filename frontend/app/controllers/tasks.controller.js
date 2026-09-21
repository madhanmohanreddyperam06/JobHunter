'use strict';

/**
 * TasksController
 * Coordinates job-search action items, deadlines, coding test preparation,
 * and follow-up tracking with MySQL persistence via TaskService.
 */
angular.module('jobCommandCenter')
.controller('TasksController', [
  'TaskService',
  'ApplicationService',
  '$timeout',
  function(TaskService, ApplicationService, $timeout) {
    var vm = this;

    // View state
    vm.isLoading = true;
    vm.isSaving = false;
    vm.togglingTaskId = null;

    // Lists
    vm.tasks = [];
    vm.applications = [];

    // Filter and search parameters
    vm.filters = {
      search: '',
      status: '',
      priority: '',
      due: '',
      page: 1,
      page_size: 50,
      sort_by: 'due_date',
      sort_order: 'asc'
    };

    // Summary KPIs
    vm.stats = {
      total: 0,
      pending: 0,
      due_today: 0,
      overdue: 0,
      completed: 0
    };

    // Modal state
    vm.modalMode = 'create'; // 'create' | 'edit'
    vm.editingId = null;
    vm.formData = {};
    vm.formErrors = {};
    vm.taskToDelete = null;

    // Feedback alert
    vm.alert = null;

    vm.showAlert = function(message, type) {
      vm.alert = { message: message, type: type || 'success' };
      $timeout(function() {
        vm.alert = null;
      }, 4000);
    };

    /**
     * Compute relative due date badge and styling
     */
    vm.getDueInfo = function(task) {
      if (!task.dueDate) {
        return { label: 'No due date', class: 'text-muted' };
      }

      if (task.status === 'COMPLETED') {
        return { label: 'Completed', class: 'text-success' };
      }
      if (task.status === 'CANCELLED') {
        return { label: 'Cancelled', class: 'text-muted' };
      }

      var now = new Date();
      var todayDateStr = now.toISOString().split('T')[0];
      var dueDateStr = task.dueDate.toISOString().split('T')[0];

      if (task.isOverdue || (task.dueDate < now && dueDateStr !== todayDateStr)) {
        return { label: 'Overdue', class: 'badge bg-danger text-white' };
      }

      if (dueDateStr === todayDateStr) {
        return { label: 'Due Today', class: 'badge bg-warning text-dark' };
      }

      // Check tomorrow
      var tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      var tomorrowDateStr = tomorrow.toISOString().split('T')[0];
      if (dueDateStr === tomorrowDateStr) {
        return { label: 'Due Tomorrow', class: 'badge bg-info-subtle text-info border border-info-subtle' };
      }

      return { label: null, class: 'text-slate-muted' };
    };

    /**
     * Priority badge CSS class
     */
    vm.getPriorityBadgeClass = function(priority) {
      var p = (priority || '').toUpperCase();
      switch (p) {
        case 'URGENT':
          return 'bg-danger-subtle text-danger border border-danger-subtle';
        case 'HIGH':
          return 'bg-warning-subtle text-warning border border-warning-subtle';
        case 'MEDIUM':
          return 'bg-primary-subtle text-primary border border-primary-subtle';
        case 'LOW':
          return 'bg-secondary-subtle text-secondary border border-secondary-subtle';
        default:
          return 'bg-light text-dark border';
      }
    };

    vm.getPriorityIcon = function(priority) {
      var p = (priority || '').toUpperCase();
      switch (p) {
        case 'URGENT': return 'bi-exclamation-octagon-fill';
        case 'HIGH': return 'bi-exclamation-triangle-fill';
        case 'MEDIUM': return 'bi-flag-fill';
        case 'LOW': return 'bi-dash-circle';
        default: return 'bi-flag';
      }
    };

    /**
     * Status badge CSS class
     */
    vm.getStatusBadgeClass = function(status) {
      var s = (status || '').toUpperCase();
      switch (s) {
        case 'TODO': return 'bg-secondary-subtle text-secondary border';
        case 'IN_PROGRESS': return 'bg-info-subtle text-info border border-info-subtle';
        case 'COMPLETED': return 'bg-success-subtle text-success border border-success-subtle';
        case 'CANCELLED': return 'bg-dark-subtle text-dark border border-dark-subtle';
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
          console.error('Error loading applications:', err);
        });
    };

    /**
     * Load summary KPI counters
     */
    vm.loadSummary = function() {
      return TaskService.getSummary()
        .then(function(data) {
          vm.stats.total = data.total || 0;
          vm.stats.pending = data.pending || 0;
          vm.stats.due_today = data.due_today || 0;
          vm.stats.overdue = data.overdue || 0;
          vm.stats.completed = data.completed || 0;
        })
        .catch(function(err) {
          console.error('Error loading task summary:', err);
        });
    };

    /**
     * Load tasks with active filters
     */
    vm.loadTasks = function() {
      vm.isLoading = true;
      return TaskService.getTasks(vm.filters)
        .then(function(res) {
          vm.tasks = res.items || [];
          vm.isLoading = false;
        })
        .catch(function(err) {
          console.error('Error loading tasks:', err);
          vm.showAlert('Unable to load tasks. Please try again.', 'danger');
          vm.isLoading = false;
        });
    };

    /**
     * Initialize page
     */
    vm.init = function() {
      vm.loadApplications();
      vm.loadSummary();
      vm.loadTasks();
    };

    // Filter actions
    vm.onFilterChange = function() {
      vm.loadTasks();
    };

    vm.clearFilters = function() {
      vm.filters.search = '';
      vm.filters.status = '';
      vm.filters.priority = '';
      vm.filters.due = '';
      vm.loadTasks();
    };

    /**
     * Fast toggle completion from checkbox
     */
    vm.toggleTaskComplete = function(task) {
      if (vm.togglingTaskId === task.id) return;
      vm.togglingTaskId = task.id;

      var newStatus = (task.status === 'COMPLETED') ? 'TODO' : 'COMPLETED';
      var oldStatus = task.status;
      task.status = newStatus;

      TaskService.updateStatus(task.id, newStatus)
        .then(function(updated) {
          task.status = updated.status;
          task.completedAt = updated.completedAt;
          task.isOverdue = updated.isOverdue;
          vm.togglingTaskId = null;
          vm.loadSummary();
        })
        .catch(function(err) {
          task.status = oldStatus;
          vm.togglingTaskId = null;
          console.error('Error toggling task:', err);
          vm.showAlert('Could not update task status.', 'danger');
        });
    };

    /**
     * Open Modal to Create New Task
     */
    vm.openCreateModal = function() {
      vm.modalMode = 'create';
      vm.editingId = null;
      vm.formErrors = {};

      vm.formData = {
        title: '',
        description: '',
        priority: 'MEDIUM',
        status: 'TODO',
        due_date: '',
        application_id: ''
      };

      var modalEl = document.getElementById('taskFormModal');
      if (modalEl && window.bootstrap) {
        var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
      }
    };

    /**
     * Open Modal to Edit Existing Task
     */
    vm.openEditModal = function(task) {
      vm.modalMode = 'edit';
      vm.editingId = task.id;
      vm.formErrors = {};

      var dateStr = '';
      if (task.dueDate) {
        var d = task.dueDate;
        var yyyy = d.getFullYear();
        var mm = String(d.getMonth() + 1).padStart(2, '0');
        var dd = String(d.getDate()).padStart(2, '0');
        dateStr = yyyy + '-' + mm + '-' + dd;
      }

      vm.formData = {
        title: task.title,
        description: task.description || '',
        priority: task.priority || 'MEDIUM',
        status: task.status || 'TODO',
        due_date: dateStr,
        application_id: task.application_id ? String(task.application_id) : ''
      };

      var modalEl = document.getElementById('taskFormModal');
      if (modalEl && window.bootstrap) {
        var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
      }
    };

    /**
     * Save Task (Create or Update)
     */
    vm.saveTask = function() {
      vm.formErrors = {};

      if (!vm.formData.title || !vm.formData.title.trim()) {
        vm.formErrors.title = 'Task title is required.';
        return;
      }

      vm.isSaving = true;

      var dueDateTime = null;
      if (vm.formData.due_date) {
        dueDateTime = vm.formData.due_date + 'T23:59:59';
      }

      var payload = {
        title: vm.formData.title.trim(),
        description: vm.formData.description ? vm.formData.description.trim() : null,
        priority: vm.formData.priority || 'MEDIUM',
        status: vm.formData.status || 'TODO',
        due_date: dueDateTime,
        application_id: vm.formData.application_id ? Number(vm.formData.application_id) : null
      };

      var operation;
      if (vm.modalMode === 'create') {
        operation = TaskService.createTask(payload);
      } else {
        operation = TaskService.updateTask(vm.editingId, payload);
      }

      operation
        .then(function() {
          vm.isSaving = false;
          var modalEl = document.getElementById('taskFormModal');
          if (modalEl && window.bootstrap) {
            var modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
          }
          vm.showAlert(
            vm.modalMode === 'create' ? 'Task created successfully!' : 'Task updated successfully!',
            'success'
          );
          vm.loadTasks();
          vm.loadSummary();
        })
        .catch(function(err) {
          vm.isSaving = false;
          console.error('Error saving task:', err);
          var msg = (err && err.detail) ? err.detail : 'Could not save task. Please verify inputs.';
          vm.showAlert(msg, 'danger');
        });
    };

    /**
     * Confirm Delete Modal
     */
    vm.confirmDelete = function(task) {
      vm.taskToDelete = task;
      var modalEl = document.getElementById('deleteTaskModal');
      if (modalEl && window.bootstrap) {
        var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
      }
    };

    /**
     * Execute Delete
     */
    vm.deleteTask = function() {
      if (!vm.taskToDelete) return;
      vm.isSaving = true;

      TaskService.deleteTask(vm.taskToDelete.id)
        .then(function() {
          vm.isSaving = false;
          var modalEl = document.getElementById('deleteTaskModal');
          if (modalEl && window.bootstrap) {
            var modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
          }
          vm.showAlert('Task deleted successfully.', 'info');
          vm.taskToDelete = null;
          vm.loadTasks();
          vm.loadSummary();
        })
        .catch(function(err) {
          vm.isSaving = false;
          console.error('Error deleting task:', err);
          vm.showAlert('Failed to delete task.', 'danger');
        });
    };

    vm.init();
  }
]);
