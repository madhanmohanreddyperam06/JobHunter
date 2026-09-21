'use strict';

/**
 * job-card Directive
 * Usage: <job-card job="job" on-edit="vm.openEditModal(job)" on-delete="vm.confirmDelete(job)" on-status-change="vm.updateStatus(job, newStatus)"></job-card>
 * Displays job application details with edit, delete, and status action capabilities.
 */
angular.module('jobCommandCenter')
.directive('jobCard', function() {
  return {
    restrict: 'E',
    scope: {
      job: '=',
      onEdit: '&?',
      onDelete: '&?',
      onStatusChange: '&?'
    },
    template:
      '<div class="job-card-wrapper position-relative">' +
      '  <div class="job-card-main d-flex justify-content-between align-items-start gap-2">' +
      '    <div>' +
      '      <h4 class="job-card-company mb-1">{{ job.company.name || job.company || "Company" }}</h4>' +
      '      <p class="job-card-role mb-0 text-dark fw-medium">{{ job.job_title || job.jobTitle }}</p>' +
      '    </div>' +
      '    <div class="d-flex align-items-center gap-2">' +
      '      <div class="dropdown">' +
      '        <button class="btn btn-sm p-0 border-0" type="button" data-bs-toggle="dropdown" aria-expanded="false" title="Change pipeline status">' +
      '          <status-badge status="job.status"></status-badge>' +
      '        </button>' +
      '        <ul class="dropdown-menu dropdown-menu-end shadow-sm">' +
      '          <li><h6 class="dropdown-header text-uppercase fs-xs">Change Status</h6></li>' +
      '          <li><button class="dropdown-item py-1" type="button" ng-click="handleStatusChange(\'SAVED\')"><span class="badge bg-secondary me-2">Saved</span></button></li>' +
      '          <li><button class="dropdown-item py-1" type="button" ng-click="handleStatusChange(\'APPLIED\')"><span class="badge bg-primary me-2">Applied</span></button></li>' +
      '          <li><button class="dropdown-item py-1" type="button" ng-click="handleStatusChange(\'ASSESSMENT\')"><span class="badge bg-warning text-dark me-2">Assessment</span></button></li>' +
      '          <li><button class="dropdown-item py-1" type="button" ng-click="handleStatusChange(\'INTERVIEW\')"><span class="badge bg-purple text-white me-2">Interview</span></button></li>' +
      '          <li><button class="dropdown-item py-1" type="button" ng-click="handleStatusChange(\'OFFER\')"><span class="badge bg-success me-2">Offer</span></button></li>' +
      '          <li><button class="dropdown-item py-1" type="button" ng-click="handleStatusChange(\'REJECTED\')"><span class="badge bg-danger me-2">Rejected</span></button></li>' +
      '          <li><button class="dropdown-item py-1" type="button" ng-click="handleStatusChange(\'WITHDRAWN\')"><span class="badge bg-dark me-2">Withdrawn</span></button></li>' +
      '        </ul>' +
      '      </div>' +
      '      <div class="btn-group btn-group-sm ms-2" role="group" aria-label="Job actions">' +
      '        <button class="btn btn-outline-secondary px-2" type="button" ng-if="onEdit" ng-click="onEdit({ job: job })" title="Edit Application">' +
      '          <i class="bi bi-pencil"></i>' +
      '        </button>' +
      '        <button class="btn btn-outline-danger px-2" type="button" ng-if="onDelete" ng-click="onDelete({ job: job })" title="Delete Application">' +
      '          <i class="bi bi-trash"></i>' +
      '        </button>' +
      '      </div>' +
      '    </div>' +
      '  </div>' +
      '  <div class="job-card-meta mt-2 pt-2 border-top d-flex flex-wrap align-items-center gap-3 text-muted fs-sm">' +
      '    <span class="job-card-meta-item" ng-if="job.location">' +
      '      <i class="bi bi-geo-alt text-primary"></i> {{ job.location }}' +
      '    </span>' +
      '    <span class="job-card-meta-item" ng-if="job.salary">' +
      '      <i class="bi bi-cash-stack text-success"></i> {{ job.salary }}' +
      '    </span>' +
      '    <span class="job-card-meta-item" ng-if="job.applied_date || job.appliedDate">' +
      '      <i class="bi bi-calendar3"></i> Applied: {{ job.applied_date || job.appliedDate }}' +
      '    </span>' +
      '    <span class="job-card-meta-item" ng-if="job.job_url || job.jobUrl">' +
      '      <a ng-href="{{ job.job_url || job.jobUrl }}" target="_blank" rel="noopener noreferrer" class="text-decoration-none text-primary">' +
      '        <i class="bi bi-box-arrow-up-right"></i> Job Link' +
      '      </a>' +
      '    </span>' +
      '    <span class="job-card-meta-item" ng-if="job.resume || job.resume_id">' +
      '      <span class="badge bg-secondary bg-opacity-25 text-info border border-info border-opacity-25">' +
      '        <i class="bi bi-file-earmark-person me-1"></i> {{ job.resume ? (job.resume.name + " (" + (job.resume.versionLabel || "v" + job.resume.version) + ")") : "Resume Attached" }}' +
      '      </span>' +
      '    </span>' +
      '    <span class="job-card-meta-item" ng-if="job.has_job_description">' +
      '      <a ng-href="#/job-descriptions?id={{ job.job_description_id }}" class="badge bg-primary bg-opacity-25 text-primary border border-primary border-opacity-25 text-decoration-none" title="View attached job description">' +
      '        <i class="bi bi-file-earmark-check me-1"></i> JD Saved' +
      '      </a>' +
      '    </span>' +
      '    <span class="job-card-meta-item" ng-if="!job.has_job_description">' +
      '      <a ng-href="#/job-descriptions?application_id={{ job.id }}" class="badge bg-secondary bg-opacity-25 text-muted border border-secondary border-opacity-25 text-decoration-none" title="Capture and link job description">' +
      '        <i class="bi bi-file-earmark-plus me-1"></i> + Add JD' +
      '      </a>' +
      '    </span>' +
      '    <span class="job-card-meta-item ms-auto" ng-if="job.employment_type || job.employmentType || job.jobType">' +
      '      <span class="badge bg-light text-dark border">{{ job.employment_type || job.employmentType || job.jobType }}</span>' +
      '    </span>' +
      '  </div>' +
      '</div>',
    link: function(scope) {
      scope.handleStatusChange = function(newStatus) {
        if (scope.onStatusChange) {
          scope.onStatusChange({ job: scope.job, newStatus: newStatus });
        }
      };
    }
  };
});
