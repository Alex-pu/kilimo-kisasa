from sqlalchemy import Column, String, DateTime, Enum, Boolean, Float, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.database import Base
from app.db_types import GUID


def enum_values(enum_class):
    return [item.value for item in enum_class]


class UserRole(str, enum.Enum):
    FARMER = "farmer"
    EXPERT = "expert"
    AGROVET = "agrovet"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole, values_callable=enum_values), nullable=False, default=UserRole.FARMER)
    bio = Column(String(500), nullable=True)
    profile_pic_url = Column(String, nullable=True)
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    location_name = Column(String, nullable=True)
    verification_status = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    issues = relationship("Issue", back_populates="creator")
    comments = relationship("Comment", back_populates="author")
    recommendations = relationship("Recommendation", back_populates="recommender")
    uploaded_images = relationship("UploadedImage", back_populates="uploaded_by")
    issue_votes = relationship("IssueVote", back_populates="user", cascade="all, delete-orphan")
    agrovets = relationship("Agrovet", back_populates="owner")
    expert_applications = relationship(
        "ExpertApplication",
        foreign_keys="ExpertApplication.user_id",
        back_populates="user",
    )
    
    def __repr__(self):
        return f"<User {self.email}>"
