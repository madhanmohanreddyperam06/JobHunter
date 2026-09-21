'use strict';

/**
 * kanbanSortable Directive
 * Integrates SortableJS with AngularJS for drag-and-drop Kanban pipeline stages.
 * Handles cross-column drag events, DOM lifecycle, and triggers AngularJS state updates safely.
 */
angular.module('jobCommandCenter')
.directive('kanbanSortable', ['$timeout', function($timeout) {
  return {
    restrict: 'A',
    scope: {
      kanbanStatus: '@',
      onStatusChange: '&',
      kanbanDisabled: '=?'
    },
    link: function(scope, element) {
      if (typeof Sortable === 'undefined') {
        console.error('SortableJS library is not available. Please ensure sortablejs is loaded.');
        return;
      }

      var sortableInstance = null;

      function initSortable() {
        if (sortableInstance) {
          sortableInstance.destroy();
        }

        sortableInstance = Sortable.create(element[0], {
          group: {
            name: 'job-applications',
            pull: true,
            put: true
          },
          animation: 150,
          ghostClass: 'sortable-ghost',
          chosenClass: 'sortable-chosen',
          dragClass: 'sortable-drag',
          filter: '.is-updating',
          preventOnFilter: true,
          fallbackOnBody: true,
          swapThreshold: 0.65,
          disabled: !!scope.kanbanDisabled,
          onEnd: function(evt) {
            // Check if item was moved to a different column
            if (evt.from === evt.to) {
              return;
            }

            var itemEl = evt.item;
            var applicationId = itemEl.getAttribute('data-application-id');
            var oldStatus = evt.from.getAttribute('data-status') || scope.kanbanStatus;
            var newStatus = evt.to.getAttribute('data-status');

            if (applicationId && oldStatus && newStatus && oldStatus !== newStatus) {
              scope.$apply(function() {
                scope.onStatusChange({
                  applicationId: parseInt(applicationId, 10),
                  oldStatus: oldStatus,
                  newStatus: newStatus,
                  itemEl: itemEl,
                  fromEl: evt.from,
                  toEl: evt.to,
                  oldIndex: evt.oldIndex
                });
              });
            }
          }
        });
      }

      // Initialize Sortable on next tick after DOM has populated
      $timeout(initSortable, 0);

      // Watch for disabled state toggles
      if (scope.kanbanDisabled !== undefined) {
        scope.$watch('kanbanDisabled', function(newVal) {
          if (sortableInstance) {
            sortableInstance.option('disabled', !!newVal);
          }
        });
      }

      // Clean up instance on scope destruction to prevent memory leaks
      scope.$on('$destroy', function() {
        if (sortableInstance) {
          sortableInstance.destroy();
          sortableInstance = null;
        }
      });
    }
  };
}]);
