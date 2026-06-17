from sqlalchemy import Column, String, DateTime, Float, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base
from app.db_types import GUID


class Agrovet(Base):
    __tablename__ = "agrovets"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    owner_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)
    contact_person_name = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    phone_number = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    website = Column(String, nullable=True)
    location_latitude = Column(Float, nullable=False)
    location_longitude = Column(Float, nullable=False)
    location_name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    verification_status = Column(Boolean, default=False)
    rating = Column(Float, default=0.0)  # Average rating
    review_count = Column(Integer, default=0)
    profile_image_url = Column(String, nullable=True)
    cover_image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="agrovets")
    products = relationship("AgrovetProduct", back_populates="agrovet", cascade="all, delete-orphan")
    endorsements = relationship("ExpertEndorsement", back_populates="agrovet", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Agrovet {self.name}>"
