from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.comment import Comment
from app.models.issue import Issue
from app.models.recommendation import Recommendation
from app.models.user import User, UserRole
from app.schemas.user_schema import UserResponse, UserUpdate, UserProfileResponse, UserRoleUpdate
from app.utils.dependencies import get_current_user
from sqlalchemy import func

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    role_update: UserRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin-only role/badge update for experts, agrovets, and admins."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update user roles"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.role = role_update.role
    if role_update.verification_status is not None:
        user.verification_status = role_update.verification_status

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user profile by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Add profile counters expected by the response schema.
    user.issues_count = db.query(func.count(Issue.id)).filter(Issue.creator_id == user.id).scalar()
    user.comments_count = db.query(func.count(Comment.id)).filter(Comment.author_id == user.id).scalar()
    user.recommendations_count = db.query(func.count(Recommendation.id)).filter(
        Recommendation.recommender_id == user.id
    ).scalar()
    
    return user


@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user account"""
    db.delete(current_user)
    db.commit()
    
    return {"message": "User account deleted successfully"}
