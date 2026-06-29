from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base
from app.db_types import GUID, StringList


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    issue_id = Column(GUID(), ForeignKey("issues.id"), nullable=False)
    author_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    parent_comment_id = Column(GUID(), ForeignKey("comments.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    media_urls = Column(StringList(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    issue = relationship("Issue", back_populates="comments")
    author = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent")
    
    def __repr__(self):
        return f"<Comment by {self.author_id} on issue {self.issue_id}>"
