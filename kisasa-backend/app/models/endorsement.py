from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base
from app.db_types import GUID


class ExpertEndorsement(Base):
    __tablename__ = "expert_endorsements"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    expert_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    agrovet_id = Column(GUID(), ForeignKey("agrovets.id"), nullable=False)
    rating = Column(Float, nullable=False)  # 1-5 stars
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    agrovet = relationship("Agrovet", back_populates="endorsements")
    
    def __repr__(self):
        return f"<ExpertEndorsement for {self.agrovet_id}>"
