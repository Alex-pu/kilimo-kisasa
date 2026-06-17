from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole


class UserBase(BaseModel):
    email: str
    full_name: str
    role: UserRole = UserRole.FARMER
    firebase_uid: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    profile_pic_url: Optional[str] = None
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    location_name: Optional[str] = None


class UserRoleUpdate(BaseModel):
    role: UserRole
    verification_status: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    firebase_uid: str
    profile_pic_url: Optional[str] = None
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    location_name: Optional[str] = None
    verification_status: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileResponse(UserResponse):
    issues_count: Optional[int] = 0
    comments_count: Optional[int] = 0
    recommendations_count: Optional[int] = 0
