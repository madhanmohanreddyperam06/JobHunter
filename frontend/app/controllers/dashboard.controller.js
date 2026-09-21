'use strict';

/**
 * DashboardController
 * Orchestrates high-level pipeline metrics, recent applications, upcoming interviews,
 * and high-priority action tracker tasks directly from real MySQL persistence.
 */
angular.module('jobCommandCenter')
.controller('DashboardController', [
  'ApplicationService',
  'InterviewService',
  'TaskService',
  'ResumeService',
  'JobDescriptionService',
  function(ApplicationService, InterviewService, TaskService, ResumeService, JobDescriptionService) {
    var vm = this;

    vm.isLoading = true;
    vm.totalResumes = 0;
    vm.activeResume = null;
    vm.totalJobDescriptions = 0;
    vm.recentJobDescriptions = [];
    vm.stats = {
      applications: 0,
      assessments: 0,
      interviews: 0,
      offers: 0
    };
    vm.taskStats = {
      pending: 0,
      due_today: 0,
      overdue: 0
    };
    vm.recentApplications = [];
    vm.upcomingInterviews = [];
    vm.pendingTasks = [];

    // Pipeline stages definition
    vm.pipelineStages = [
      { label: 'Saved', status: 'SAVED', count: 0, icon: 'bi-bookmark', color: 'text-secondary' },
      { label: 'Applied', status: 'APPLIED', count: 0, icon: 'bi-send', color: 'text-primary' },
      { label: 'Assessment', status: 'ASSESSMENT', count: 0, icon: 'bi-pencil-square', color: 'text-warning' },
      { label: 'Interview', status: 'INTERVIEW', count: 0, icon: 'bi-calendar-check', color: 'text-purple' },
      { label: 'Offer', status: 'OFFER', count: 0, icon: 'bi-trophy', color: 'text-success' },
      { label: 'Rejected', status: 'REJECTED', count: 0, icon: 'bi-x-circle', color: 'text-danger' }
    ];

    /**
     * Compute human-readable relative countdown
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
          return 'Tomorrow';
        } else if (diffHours > 0) {
          return 'In ' + diffHours + 'h';
        } else {
          var mins = Math.max(1, Math.floor(diffMs / (1000 * 60)));
          return 'In ' + mins + 'm';
        }
      } else {
        return 'Today';
      }
    };

    /**
     * Fast toggle complete for tasks directly from dashboard
     */
    vm.toggleTask = function(task) {
      var newStatus = (task.status === 'COMPLETED') ? 'TODO' : 'COMPLETED';
      task.status = newStatus;

      TaskService.updateStatus(task.id, newStatus)
        .then(function() {
          vm.loadTasksData();
        })
        .catch(function(err) {
          console.error('Error toggling task from dashboard:', err);
        });
    };

    /**
     * Load tasks data and summary
     */
    vm.loadTasksData = function() {
      var summaryPromise = TaskService.getSummary()
        .then(function(summary) {
          vm.taskStats.pending = summary.pending || 0;
          vm.taskStats.due_today = summary.due_today || 0;
          vm.taskStats.overdue = summary.overdue || 0;
        })
        .catch(function(err) {
          console.error('Error loading task summary on dashboard:', err);
        });

      var tasksPromise = TaskService.getTasks({ page_size: 4, status: 'TODO', sort_by: 'due_date', sort_order: 'asc' })
        .then(function(res) {
          vm.pendingTasks = res.items || [];
        })
        .catch(function(err) {
          console.error('Error loading pending tasks on dashboard:', err);
        });

      return Promise.all([summaryPromise, tasksPromise]);
    };

    /**
     * Load all dashboard modules
     */
    vm.loadDashboard = function() {
      vm.isLoading = true;

      // Load applications
      var appPromise = ApplicationService.getApplications({ page_size: 100 })
        .then(function(res) {
          var items = res.items || [];
          vm.recentApplications = items.slice(0, 4);

          // Derive live metrics from user's persisted pipeline
          vm.stats.applications = res.total || 0;
          vm.stats.assessments = items.filter(function(a) { return a.status === 'ASSESSMENT'; }).length;
          vm.stats.interviews = items.filter(function(a) { return a.status === 'INTERVIEW'; }).length;
          vm.stats.offers = items.filter(function(a) { return a.status === 'OFFER'; }).length;

          // Synchronize stage counts
          vm.pipelineStages.forEach(function(stage) {
            stage.count = items.filter(function(a) {
              return (a.status || '').toUpperCase() === stage.status;
            }).length;
          });
        })
        .catch(function(err) {
          console.error('Error loading dashboard applications:', err);
        });

      // Load upcoming interviews
      var interviewPromise = InterviewService.getInterviews({ page_size: 10, sort_by: 'scheduled_at', sort_order: 'asc' })
        .then(function(res) {
          var items = res.items || [];
          var now = new Date();
          vm.upcomingInterviews = items.filter(function(i) {
            return (i.scheduledAt && i.scheduledAt >= now && i.status !== 'COMPLETED' && i.status !== 'CANCELLED') || i.status === 'SCHEDULED';
          }).slice(0, 3);
        })
        .catch(function(err) {
          console.error('Error loading dashboard interviews:', err);
        });

      var tasksPromise = vm.loadTasksData();

      var resumePromise = ResumeService.getResumes({ page_size: 20 })
        .then(function(res) {
          var items = res.items || [];
          vm.totalResumes = res.total || 0;
          vm.activeResume = items.find(function(r) { return r.is_active; }) || null;
        })
        .catch(function(err) {
          console.error('Error loading dashboard resumes:', err);
        });

      var jdPromise = JobDescriptionService.getJobDescriptions({ page_size: 5, sort_by: 'captured_at', sort_order: 'desc' })
        .then(function(res) {
          vm.totalJobDescriptions = res.total || 0;
          vm.recentJobDescriptions = res.items || [];
        })
        .catch(function(err) {
          console.error('Error loading dashboard JDs:', err);
        });

      Promise.all([appPromise, interviewPromise, tasksPromise, resumePromise, jdPromise])
        .finally(function() {
          vm.isLoading = false;
        });
    };

    vm.loadDashboard();
  }
]);
