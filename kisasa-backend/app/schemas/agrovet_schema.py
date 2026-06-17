from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class AgrovetBase(BaseModel):
    name: str
    contact_person_name: Optional[str] = None
    phone_number: str
    email: Optional[str] = None
    website: Optional[str] = None
    location_name: str


class AgrovetCreate(AgrovetBase):
    location_latitude: float
    location_longitude: float
    description: Optional[str] = None
    address: Optional[str] = None


class AgrovetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None


class AgrovetResponse(AgrovetBase):
    id: UUID
    owner_id: Optional[UUID] = None
    description: Optional[str] = None
    location_latitude: float
    location_longitude: float
    verification_status: bool
    rating: float
    review_count: int
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgrovetDetailResponse(AgrovetResponse):
    products_count: Optional[int] = 0
