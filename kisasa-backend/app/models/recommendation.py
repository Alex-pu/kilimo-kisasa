from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base
from app.db_types import GUID, GUIDList


class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    issue_id = Column(GUID(), ForeignKey("issues.id"), nullable=False)
    recommender_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    farm_input_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=False)  # Why this recommendation
    estimated_cost = Column(Float, nullable=True)
    linked_product_ids = Column(GUIDList(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    issue = relationship("Issue", back_populates="recommendations")
    recommender = relationship("User", back_populates="recommendations")
    
    def __repr__(self):
        return f"<Recommendation {self.farm_input_name}>"
