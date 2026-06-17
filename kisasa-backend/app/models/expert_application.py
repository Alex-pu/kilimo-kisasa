from datetime import datetime
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.db_types import GUID
from app.models.user import enum_values


class ExpertApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExpertApplication(Base):
    __tablename__ = "expert_applications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    linkedin_url = Column(String(500), nullable=False)
    education = Column(Text, nullable=False)
    credentials = Column(Text, nullable=True)
    experience_summary = Column(Text, nullable=True)
    status = Column(
        Enum(ExpertApplicationStatus, values_callable=enum_values),
        nullable=False,
        default=ExpertApplicationStatus.PENDING,
        index=True,
    )
    review_notes = Column(Text, nullable=True)
    reviewed_by_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id], back_populates="expert_applications")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
