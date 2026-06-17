from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text, Enum, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.database import Base
from app.db_types import GUID, StringList


def enum_values(enum_class):
    return [item.value for item in enum_class]


class IssueStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IssueCategory(str, enum.Enum):
    CROP_DISEASE = "crop_disease"
    PEST_MANAGEMENT = "pest_management"
    SOIL_HEALTH = "soil_health"
    WATER_MANAGEMENT = "water_management"
    FERTILIZER = "fertilizer"
    SEED_QUALITY = "seed_quality"
    WEATHER = "weather"
    MARKET_PRICE = "market_price"
    OTHER = "other"


class PostType(str, enum.Enum):
    ISSUE = "issue"
    EDUCATIONAL = "educational"
    FARMING_NEWS = "farming_news"


class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    creator_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    post_type = Column(Enum(PostType, values_callable=enum_values), nullable=False, default=PostType.ISSUE, index=True)
    category = Column(Enum(IssueCategory, values_callable=enum_values), nullable=False, index=True)
    status = Column(Enum(IssueStatus, values_callable=enum_values), nullable=False, default=IssueStatus.OPEN, index=True)
    image_urls = Column(StringList(), nullable=True)  # Firebase Storage URLs
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    location_name = Column(String, nullable=True)
    views_count = Column(Integer, default=0)
    is_urgent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    creator = relationship("User", back_populates="issues")
    comments = relationship("Comment", back_populates="issue", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="issue", cascade="all, delete-orphan")
    uploaded_images = relationship("UploadedImage", back_populates="issue")
    votes = relationship("IssueVote", back_populates="issue", cascade="all, delete-orphan")

    @property
    def images(self):
        return self.uploaded_images

    @property
    def score(self):
        return sum(vote.value for vote in self.votes)
    
    def __repr__(self):
        return f"<Issue {self.title}>"
