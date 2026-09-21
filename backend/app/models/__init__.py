"""
SQLAlchemy 2.0 ORM Models for Job Application Command Center.
"""
from app.models.user import User
from app.models.company import Company
from app.models.application import Application, APPLICATION_STATUSES
from app.models.interview import Interview
from app.models.task import Task, TASK_PRIORITIES, TASK_STATUSES
from app.models.resume import Resume
from app.models.job_description import JobDescription, EMPLOYMENT_TYPES, WORK_ARRANGEMENTS
from app.models.skill import Skill, SKILL_CATEGORIES, normalize_skill_name
from app.models.application_skill import ApplicationSkill, PROFICIENCY_LEVELS
from app.models.job_description_skill import JobDescriptionSkill, IMPORTANCE_LEVELS, SOURCE_SECTIONS
from app.models.note import Note
from app.models.activity_log import ActivityLog

__all__ = [
    "User",
    "Company",
    "Application",
    "APPLICATION_STATUSES",
    "Interview",
    "Task",
    "TASK_PRIORITIES",
    "TASK_STATUSES",
    "Resume",
    "JobDescription",
    "EMPLOYMENT_TYPES",
    "WORK_ARRANGEMENTS",
    "Skill",
    "SKILL_CATEGORIES",
    "normalize_skill_name",
    "ApplicationSkill",
    "PROFICIENCY_LEVELS",
    "JobDescriptionSkill",
    "IMPORTANCE_LEVELS",
    "SOURCE_SECTIONS",
    "Note",
    "ActivityLog",
]
