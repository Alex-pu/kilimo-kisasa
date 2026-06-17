from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class ProductBase(BaseModel):
    product_name: str
    category: str
    price: float
    unit: Optional[str] = None


class ProductCreate(ProductBase):
    description: Optional[str] = None
    instructions: Optional[str] = None
    stock_quantity: int = 0
    image_url: Optional[str] = None


class ProductResponse(ProductBase):
    id: UUID
    agrovet_id: UUID
    description: Optional[str] = None
    instructions: Optional[str] = None
    stock_quantity: int
    currency: str
    image_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductAgrovetSummary(BaseModel):
    id: UUID
    name: str
    phone_number: str
    location_name: str
    location_latitude: float
    location_longitude: float
    rating: float
    verification_status: bool

    class Config:
        from_attributes = True


class ProductWithAgrovetResponse(ProductResponse):
    agrovet: Optional[ProductAgrovetSummary] = None
