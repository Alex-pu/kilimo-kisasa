from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.expert_application import ExpertApplication, ExpertApplicationStatus
from app.models.user import User, UserRole
from app.schemas.expert_application_schema import (
    ExpertApplicationAdminResponse,
    ExpertApplicationCreate,
    ExpertApplicationResponse,
    ExpertApplicationReview,
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/expert-applications", tags=["expert applications"])


def require_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can review expert applications",
        )


def admin_response(application: ExpertApplication) -> ExpertApplicationAdminResponse:
    return ExpertApplicationAdminResponse(
        **ExpertApplicationResponse.model_validate(application).model_dump(),
        applicant_name=application.user.full_name,
        applicant_email=application.user.email,
    )


@router.post("/", response_model=ExpertApplicationResponse)
async def apply_for_expert(
    application_data: ExpertApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit expert profile details for admin approval."""
    if current_user.role in {UserRole.EXPERT, UserRole.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already an expert or admin",
        )

    existing_pending = (
        db.query(ExpertApplication)
        .filter(
            ExpertApplication.user_id == current_user.id,
            ExpertApplication.status == ExpertApplicationStatus.PENDING,
        )
        .first()
    )
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending expert application",
        )

    application = ExpertApplication(
        user_id=current_user.id,
        linkedin_url=str(application_data.linkedin_url),
        education=application_data.education,
        credentials=application_data.credentials,
        experience_summary=application_data.experience_summary,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/me", response_model=List[ExpertApplicationResponse])
async def list_my_expert_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the current user's expert applications."""
    return (
        db.query(ExpertApplication)
        .filter(ExpertApplication.user_id == current_user.id)
        .order_by(ExpertApplication.created_at.desc())
        .all()
    )


@router.get("/", response_model=List[ExpertApplicationAdminResponse])
async def list_expert_applications(
    status_filter: ExpertApplicationStatus = Query(ExpertApplicationStatus.PENDING, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin list of expert applications."""
    require_admin(current_user)

    applications = (
        db.query(ExpertApplication)
        .filter(ExpertApplication.status == status_filter)
        .order_by(ExpertApplication.created_at.asc())
        .all()
    )
    return [admin_response(application) for application in applications]


@router.put("/{application_id}/review", response_model=ExpertApplicationAdminResponse)
async def review_expert_application(
    application_id: str,
    review: ExpertApplicationReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve or reject an expert application as an admin."""
    require_admin(current_user)

    application = db.query(ExpertApplication).filter(ExpertApplication.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expert application not found",
        )
    if application.status != ExpertApplicationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending applications can be reviewed",
        )
    if review.status == ExpertApplicationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review status must be approved or rejected",
        )

    application.status = review.status
    application.review_notes = review.review_notes
    application.reviewed_by_id = current_user.id
    application.reviewed_at = datetime.utcnow()

    if review.status == ExpertApplicationStatus.APPROVED:
        application.user.role = UserRole.EXPERT
        application.user.verification_status = True

    db.add(application)
    db.commit()
    db.refresh(application)
    return admin_response(application)
