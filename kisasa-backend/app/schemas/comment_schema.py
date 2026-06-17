from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    media_urls: Optional[List[str]] = None
    parent_comment_id: Optional[UUID] = None


class CommentResponse(CommentBase):
    id: UUID
    issue_id: UUID
    author_id: UUID
    parent_comment_id: Optional[UUID] = None
    media_urls: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CommentDetailResponse(CommentResponse):
    author: Optional[dict] = None
