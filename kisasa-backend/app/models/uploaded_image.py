from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.db_types import GUID


class UploadedImage(Base):
    __tablename__ = "uploaded_images"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    uploaded_by_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    issue_id = Column(GUID(), ForeignKey("issues.id"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    url = Column(String(), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    uploaded_by = relationship("User", back_populates="uploaded_images")
    issue = relationship("Issue", back_populates="uploaded_images")

    def __repr__(self):
        return f"<UploadedImage {self.stored_filename}>"
