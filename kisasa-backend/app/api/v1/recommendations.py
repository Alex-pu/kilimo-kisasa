from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.issue import Issue
from app.models.product import AgrovetProduct
from app.models.recommendation import Recommendation
from app.models.user import User, UserRole
from app.schemas.recommendation_schema import RecommendationCreate, RecommendationResponse
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/issues/{issue_id}/recommendations", tags=["recommendations"])


def attach_linked_products(recommendation: Recommendation, db: Session) -> Recommendation:
    product_ids = recommendation.linked_product_ids or []
    if not product_ids:
        recommendation.linked_products = []
        return recommendation

    recommendation.linked_products = (
        db.query(AgrovetProduct)
        .filter(AgrovetProduct.id.in_(product_ids))
        .all()
    )
    return recommendation


@router.post("/", response_model=RecommendationResponse)
async def create_recommendation(
    issue_id: str,
    recommendation_data: RecommendationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add an expert recommendation to an issue."""
    if current_user.role not in {UserRole.EXPERT, UserRole.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only experts can create recommendations",
        )

    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )

    linked_product_ids = recommendation_data.linked_product_ids or []
    if linked_product_ids:
        parsed_ids = [uuid.UUID(str(product_id)) for product_id in linked_product_ids]
        found_count = (
            db.query(AgrovetProduct)
            .filter(AgrovetProduct.id.in_(parsed_ids))
            .count()
        )
        if found_count != len(parsed_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more linked products were not found",
            )
    else:
        parsed_ids = None

    payload = recommendation_data.model_dump(exclude={"linked_product_ids"})
    recommendation = Recommendation(
        issue_id=issue.id,
        recommender_id=current_user.id,
        linked_product_ids=parsed_ids,
        **payload,
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return attach_linked_products(recommendation, db)


@router.get("/", response_model=List[RecommendationResponse])
async def list_recommendations(
    issue_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List recommendations for an issue."""
    issue = db.query(Issue.id).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )

    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.issue_id == issue_id)
        .order_by(Recommendation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [attach_linked_products(recommendation, db) for recommendation in recommendations]


@router.delete("/{recommendation_id}")
async def delete_recommendation(
    issue_id: str,
    recommendation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a recommendation as its recommender or an admin."""
    recommendation = (
        db.query(Recommendation)
        .filter(
            Recommendation.id == recommendation_id,
            Recommendation.issue_id == issue_id,
        )
        .first()
    )
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )

    if recommendation.recommender_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recommender or admin can delete it",
        )

    db.delete(recommendation)
    db.commit()
    return {"message": "Recommendation deleted successfully"}
