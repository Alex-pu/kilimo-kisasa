from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.issue import IssueCategory, IssueStatus, PostType
from app.schemas.upload_schema import UploadedImageResponse


class IssueBase(BaseModel):
    title: str
    description: str
    post_type: PostType = PostType.ISSUE
    category: IssueCategory
    is_urgent: bool = False


class IssueCreate(IssueBase):
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    location_name: Optional[str] = None
    image_urls: Optional[List[str]] = None
    image_ids: Optional[List[UUID]] = None


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[IssueCategory] = None
    status: Optional[IssueStatus] = None
    is_urgent: Optional[bool] = None


class IssueResponse(IssueBase):
    id: UUID
    creator_id: UUID
    status: IssueStatus
    image_urls: Optional[List[str]] = None
    images: List[UploadedImageResponse] = Field(default_factory=list)
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    location_name: Optional[str] = None
    views_count: int
    score: int = 0
    my_vote: Optional[int] = None
    comments_count: int = 0
    recommendations_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IssueDetailResponse(IssueResponse):
    creator: Optional[dict] = None


class IssueVoteRequest(BaseModel):
    value: int


class IssueVoteResponse(BaseModel):
    issue_id: UUID
    score: int
    my_vote: int
