from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UploadedImageResponse(BaseModel):
    id: UUID
    issue_id: UUID | None = None
    original_filename: str
    content_type: str
    file_size: int
    url: str
    created_at: datetime

    class Config:
        from_attributes = True
