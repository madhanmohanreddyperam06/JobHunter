'use strict';

/**
 * KanbanController
 * Manages the interactive Kanban board pipeline stages and SortableJS drag-and-drop persistence.
 * Implements optimistic UI updates with automatic rollback on API failure and per-application locking.
 */
angular.module('jobCommandCenter')
.controller('KanbanController', ['$timeout', 'ApplicationService', function($timeout, ApplicationService) {
  var vm = this;

  vm.isLoading = true;
  vm.errorMessage = '';
  vm.successMessage = '';
  var messageTimeout = null;

  // Centralized pipeline column configuration
  vm.columns = [
    { key: 'SAVED', label: 'Saved' },
    { key: 'APPLIED', label: 'Applied' },
    { key: 'ASSESSMENT', label: 'Assessment' },
    { key: 'INTERVIEW', label: 'Interview' },
    { key: 'OFFER', label: 'Offer' },
    { key: 'REJECTED', label: 'Rejected' }
  ];

  // Column applications map
  vm.applicationsByColumn = {
    SAVED: [],
    APPLIED: [],
    ASSESSMENT: [],
    INTERVIEW: [],
    OFFER: [],
    REJECTED: []
  };

  // Withdrawn applications count
  vm.withdrawnCount = 0;

  // In-flight status update tracking to prevent concurrent conflicting drags
  vm.updatingApplicationIds = {};

  /**
   * Check if a specific application is currently persisting a status update
   */
  vm.isUpdating = function(applicationId) {
    return !!vm.updatingApplicationIds[applicationId];
  };

  /**
   * Fetch applications from backend MySQL and categorize into pipeline columns
   */
  vm.loadKanbanData = function() {
    vm.isLoading = true;
    vm.errorMessage = '';

    ApplicationService.getApplications({ page_size: 100 })
      .then(function(res) {
        var applications = (res && res.items) ? res.items : [];

        // Reset columns and withdrawn count
        vm.columns.forEach(function(col) {
          vm.applicationsByColumn[col.key] = [];
        });
        vm.withdrawnCount = 0;

        // Populate cards into their respective pipeline columns
        applications.forEach(function(app) {
          var status = (app.status || 'SAVED').toUpperCase();
          if (status === 'WITHDRAWN') {
            vm.withdrawnCount++;
          } else if (vm.applicationsByColumn[status]) {
            vm.applicationsByColumn[status].push(app);
          } else {
            vm.applicationsByColumn.SAVED.push(app);
          }
        });

        vm.isLoading = false;
      })
      .catch(function(err) {
        vm.errorMessage = typeof err === 'string' ? err : 'Unable to load pipeline data.';
        vm.isLoading = false;
      });
  };

  /**
   * Refresh Kanban board data
   */
  vm.refreshBoard = function() {
    vm.loadKanbanData();
  };

  /**
   * Handle drag-and-drop status change event triggered by kanbanSortable directive
   */
  vm.handleStatusChange = function(applicationId, oldStatus, newStatus, itemEl, fromEl, oldIndex) {
    if (!applicationId || !oldStatus || !newStatus || oldStatus === newStatus) {
      return;
    }

    // Prevent concurrent updates for the same application
    if (vm.updatingApplicationIds[applicationId]) {
      return;
    }

    vm.updatingApplicationIds[applicationId] = true;
    vm.errorMessage = '';

    // Locate the application in the source column array
    var sourceColumn = vm.applicationsByColumn[oldStatus] || [];
    var itemIndex = sourceColumn.findIndex(function(a) {
      return a.id === applicationId;
    });

    var appObj = itemIndex !== -1 ? sourceColumn[itemIndex] : null;

    // Optimistic UI Update: immediately transition in memory
    if (appObj) {
      sourceColumn.splice(itemIndex, 1);
      appObj.status = newStatus;
      if (vm.applicationsByColumn[newStatus]) {
        vm.applicationsByColumn[newStatus].push(appObj);
      }
    }

    // Persist status update to MySQL via existing REST API
    ApplicationService.updateStatus(applicationId, newStatus)
      .then(function(updatedApp) {
        delete vm.updatingApplicationIds[applicationId];
        // Synchronize state with backend response
        if (appObj && updatedApp) {
          appObj.status = updatedApp.status;
          appObj.updated_at = updatedApp.updated_at;
        }
      })
      .catch(function(err) {
        delete vm.updatingApplicationIds[applicationId];

        // Automatic Rollback: restore previous status in column arrays
        if (appObj) {
          var targetColumn = vm.applicationsByColumn[newStatus] || [];
          var currentIdx = targetColumn.findIndex(function(a) {
            return a.id === applicationId;
          });
          if (currentIdx !== -1) {
            targetColumn.splice(currentIdx, 1);
          }

          appObj.status = oldStatus;
          sourceColumn.splice(itemIndex !== -1 ? itemIndex : 0, 0, appObj);
        }

        // Rollback DOM position to source column
        if (itemEl && fromEl) {
          if (oldIndex !== undefined && fromEl.children.length > oldIndex) {
            fromEl.insertBefore(itemEl, fromEl.children[oldIndex]);
          } else {
            fromEl.appendChild(itemEl);
          }
        }

        // Display user-friendly error message with auto-dismiss
        vm.errorMessage = typeof err === 'string' 
          ? err 
          : 'Unable to update the application status. Reverted to ' + oldStatus + '.';

        if (messageTimeout) {
          $timeout.cancel(messageTimeout);
        }
        messageTimeout = $timeout(function() {
          vm.errorMessage = '';
        }, 5000);
      });
  };

  // Initial load
  vm.loadKanbanData();
}]);
