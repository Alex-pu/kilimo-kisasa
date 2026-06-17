from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base
from app.db_types import GUID


class AgrovetProduct(Base):
    __tablename__ = "agrovet_products"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    agrovet_id = Column(GUID(), ForeignKey("agrovets.id"), nullable=False)
    product_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False)  # Fertilizer, Pesticide, Seeds, etc.
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="KES")  # Kenyan Shilling
    stock_quantity = Column(Integer, default=0)
    unit = Column(String(50), nullable=True)  # kg, L, pieces, etc.
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    agrovet = relationship("Agrovet", back_populates="products")
    
    def __repr__(self):
        return f"<AgrovetProduct {self.product_name}>"
