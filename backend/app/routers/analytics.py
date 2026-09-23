from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Integer, select

from app.database.database import get_db
from app.models.user import User
from app.models.application import Application, APPLICATION_STATUSES
from app.routers.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", summary="Get Dashboard Analytics")
def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retrieve high-level dashboard metrics for the authenticated user.
    Returns counts for applications, interviews, tasks, and pipeline statistics.
    """
    # Get application counts by status
    status_counts = db.execute(
        select(
            Application.status,
            func.count(Application.id).label('count')
        )
        .where(Application.user_id == current_user.id)
        .group_by(Application.status)
    ).all()
    
    status_dict = {status: 0 for status in APPLICATION_STATUSES}
    for status, count in status_counts:
        status_dict[status] = count
    
    total_applications = sum(status_dict.values())
    
    return {
        "total_applications": total_applications,
        "saved": status_dict.get("SAVED", 0),
        "applied": status_dict.get("APPLIED", 0),
        "assessment": status_dict.get("ASSESSMENT", 0),
        "interview": status_dict.get("INTERVIEW", 0),
        "offer": status_dict.get("OFFER", 0),
        "rejected": status_dict.get("REJECTED", 0),
        "withdrawn": status_dict.get("WITHDRAWN", 0),
    }


@router.get("/funnel", summary="Get Application Funnel Analytics")
def get_funnel_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retrieve application funnel conversion metrics.
    Shows how applications move through the pipeline stages.
    """
    # Get total applications
    total = db.execute(
        select(func.count(Application.id))
        .where(Application.user_id == current_user.id)
    ).scalar() or 0
    
    if total == 0:
        return {
            "total": 0,
            "stages": []
        }
    
    # Get counts by status
    status_counts = db.execute(
        select(
            Application.status,
            func.count(Application.id).label('count')
        )
        .where(Application.user_id == current_user.id)
        .group_by(Application.status)
    ).all()
    
    status_dict = {status: 0 for status in APPLICATION_STATUSES}
    for status, count in status_counts:
        status_dict[status] = count
    
    # Calculate funnel stages
    stages = [
        {
            "stage": "Saved",
            "count": status_dict.get("SAVED", 0),
            "percentage": round((status_dict.get("SAVED", 0) / total) * 100, 1) if total > 0 else 0
        },
        {
            "stage": "Applied",
            "count": status_dict.get("APPLIED", 0),
            "percentage": round((status_dict.get("APPLIED", 0) / total) * 100, 1) if total > 0 else 0
        },
        {
            "stage": "Assessment",
            "count": status_dict.get("ASSESSMENT", 0),
            "percentage": round((status_dict.get("ASSESSMENT", 0) / total) * 100, 1) if total > 0 else 0
        },
        {
            "stage": "Interview",
            "count": status_dict.get("INTERVIEW", 0),
            "percentage": round((status_dict.get("INTERVIEW", 0) / total) * 100, 1) if total > 0 else 0
        },
        {
            "stage": "Offer",
            "count": status_dict.get("OFFER", 0),
            "percentage": round((status_dict.get("OFFER", 0) / total) * 100, 1) if total > 0 else 0
        },
        {
            "stage": "Rejected",
            "count": status_dict.get("REJECTED", 0),
            "percentage": round((status_dict.get("REJECTED", 0) / total) * 100, 1) if total > 0 else 0
        }
    ]
    
    return {
        "total": total,
        "stages": stages
    }


@router.get("/skills", summary="Get Skills Analytics")
def get_skills_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retrieve skills usage analytics.
    Shows most used skills across applications and job descriptions.
    """
    from app.models.skill import Skill
    from app.models.application_skill import ApplicationSkill
    from app.models.job_description_skill import JobDescriptionSkill
    
    # Get total skills in catalog
    total_skills = db.execute(
        select(func.count(Skill.id))
        .where(Skill.user_id == current_user.id)
    ).scalar() or 0
    
    # Get skills usage in applications
    application_skill_usage = db.execute(
        select(
            Skill.name,
            func.count(ApplicationSkill.id).label('usage_count')
        )
        .join(ApplicationSkill, Skill.id == ApplicationSkill.skill_id)
        .join(Application, ApplicationSkill.application_id == Application.id)
        .where(Application.user_id == current_user.id)
        .group_by(Skill.id, Skill.name)
        .order_by(func.count(ApplicationSkill.id).desc())
        .limit(10)
    ).all()
    
    # Get skills usage in job descriptions
    jd_skill_usage = db.execute(
        select(
            Skill.name,
            func.count(JobDescriptionSkill.id).label('usage_count')
        )
        .join(JobDescriptionSkill, Skill.id == JobDescriptionSkill.skill_id)
        .join(Application, JobDescriptionSkill.job_description_id == Application.id)
        .where(Application.user_id == current_user.id)
        .group_by(Skill.id, Skill.name)
        .order_by(func.count(JobDescriptionSkill.id).desc())
        .limit(10)
    ).all()
    
    return {
        "total_skills": total_skills,
        "top_application_skills": [
            {"name": name, "count": count} for name, count in application_skill_usage
        ],
        "top_jd_skills": [
            {"name": name, "count": count} for name, count in jd_skill_usage
        ]
    }
