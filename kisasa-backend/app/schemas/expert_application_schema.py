from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl

from app.models.expert_application import ExpertApplicationStatus


class ExpertApplicationCreate(BaseModel):
    linkedin_url: HttpUrl
    education: str
    credentials: Optional[str] = None
    experience_summary: Optional[str] = None


class ExpertApplicationReview(BaseModel):
    status: ExpertApplicationStatus
    review_notes: Optional[str] = None


class ExpertApplicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    linkedin_url: str
    education: str
    credentials: Optional[str] = None
    experience_summary: Optional[str] = None
    status: ExpertApplicationStatus
    review_notes: Optional[str] = None
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpertApplicationAdminResponse(ExpertApplicationResponse):
    applicant_name: str
    applicant_email: str
