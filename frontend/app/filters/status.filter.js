'use strict';

/**
 * Status Formatter Filter
 * Converts internal uppercase status slugs to readable labels
 */
angular.module('jobCommandCenter')
.filter('statusLabel', function() {
  var statusLabels = {
    'SAVED': 'Saved',
    'APPLIED': 'Applied',
    'ASSESSMENT': 'Assessment',
    'INTERVIEW': 'Interview',
    'OFFER': 'Offer',
    'REJECTED': 'Rejected'
  };

  return function(input) {
    if (!input) return '';
    var key = String(input).toUpperCase();
    return statusLabels[key] || input;
  };
});
