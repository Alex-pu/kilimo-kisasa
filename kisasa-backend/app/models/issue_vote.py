from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.db_types import GUID


class IssueVote(Base):
    __tablename__ = "issue_votes"
    __table_args__ = (
        UniqueConstraint("issue_id", "user_id", name="uq_issue_votes_issue_user"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    issue_id = Column(GUID(), ForeignKey("issues.id"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    value = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    issue = relationship("Issue", back_populates="votes")
    user = relationship("User", back_populates="issue_votes")
