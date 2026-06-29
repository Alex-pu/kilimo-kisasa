from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.database import get_db
from app.models.comment import Comment
from app.models.issue import Issue, IssueStatus, PostType
from app.models.issue_vote import IssueVote
from app.models.product import AgrovetProduct
from app.models.recommendation import Recommendation
from app.models.uploaded_image import UploadedImage
from app.models.user import User, UserRole
from app.schemas.issue_schema import IssueCreate, IssueResponse, IssueUpdate, IssueDetailResponse, IssueVoteRequest, IssueVoteResponse
from app.schemas.nearby_schema import NearbyRecommendedProduct
from app.utils.dependencies import get_current_user, get_optional_user
from typing import List
import uuid

router = APIRouter(prefix="/issues", tags=["issues"])


def haversine_km(lon1, lat1, lon2, lat2):
    """Calculate distance between two points on Earth (in km)."""
    from math import radians, cos, sin, asin, sqrt

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c


def issue_score(db: Session, issue_id):
    return db.query(func.coalesce(func.sum(IssueVote.value), 0)).filter(
        IssueVote.issue_id == issue_id
    ).scalar()


def attach_my_votes(db: Session, issues: List[Issue], current_user: User | None):
    if not current_user or not issues:
        return issues

    issue_ids = [issue.id for issue in issues]
    votes = (
        db.query(IssueVote)
        .filter(
            IssueVote.user_id == current_user.id,
            IssueVote.issue_id.in_(issue_ids),
        )
        .all()
    )
    votes_by_issue = {vote.issue_id: vote.value for vote in votes}
    for issue in issues:
        issue.my_vote = votes_by_issue.get(issue.id, 0)
    return issues


def attach_thread_counts(db: Session, issues: List[Issue]):
    if not issues:
        return issues

    issue_ids = [issue.id for issue in issues]
    comment_counts = dict(
        db.query(Comment.issue_id, func.count(Comment.id))
        .filter(Comment.issue_id.in_(issue_ids))
        .group_by(Comment.issue_id)
        .all()
    )
    recommendation_counts = dict(
        db.query(Recommendation.issue_id, func.count(Recommendation.id))
        .filter(Recommendation.issue_id.in_(issue_ids))
        .group_by(Recommendation.issue_id)
        .all()
    )

    for issue in issues:
        issue.comments_count = comment_counts.get(issue.id, 0)
        issue.recommendations_count = recommendation_counts.get(issue.id, 0)
    return issues


def attach_issue_metadata(db: Session, issues: List[Issue], current_user: User | None):
    attach_thread_counts(db, issues)
    return attach_my_votes(db, issues, current_user)


@router.post("/", response_model=IssueResponse)
async def create_issue(
    issue_data: IssueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new issue"""
    issue_payload = issue_data.model_dump(exclude={"image_ids"})
    if issue_data.post_type != PostType.ISSUE and current_user.role not in {
        UserRole.EXPERT,
        UserRole.ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only experts can create educational or farming news posts",
        )

    image_ids = issue_data.image_ids or []
    uploaded_images = []
    if image_ids:
        uploaded_images = (
            db.query(UploadedImage)
            .filter(
                UploadedImage.id.in_(image_ids),
                UploadedImage.uploaded_by_id == current_user.id,
                UploadedImage.issue_id.is_(None),
            )
            .all()
        )
        if len(uploaded_images) != len(set(image_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more images are invalid or already attached to a post",
            )
        issue_payload["image_urls"] = [
            *(issue_payload.get("image_urls") or []),
            *[image.url for image in uploaded_images],
        ]

    issue = Issue(
        creator_id=current_user.id,
        **issue_payload
    )
    db.add(issue)
    db.flush()

    for image in uploaded_images:
        image.issue_id = issue.id

    db.commit()
    db.refresh(issue)
    issue.comments_count = 0
    issue.recommendations_count = 0
    issue.my_vote = 0
    
    return issue


@router.get("/", response_model=List[IssueResponse])
async def list_issues(
    category: str = Query(None),
    post_type: PostType = Query(None),
    status: IssueStatus = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """List all issues with optional filtering"""
    query = db.query(Issue)
    
    if category:
        query = query.filter(Issue.category == category)

    if post_type:
        query = query.filter(Issue.post_type == post_type)
    
    if status:
        query = query.filter(Issue.status == status)
    
    issues = query.order_by(Issue.created_at.desc()).offset(skip).limit(limit).all()
    return attach_issue_metadata(db, issues, current_user)


@router.get("/nearby/", response_model=List[IssueResponse])
async def get_nearby_issues(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: int = Query(10, ge=1, le=100),
    limit: int = Query(20, ge=1, le=100),
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Get issues near a specific location.
    Uses simple distance calculation (for production, use PostGIS).
    """
    issues = db.query(Issue).filter(
        Issue.location_latitude != None,
        Issue.location_longitude != None
    ).limit(limit * 2).all()
    
    nearby = [
        issue for issue in issues
        if issue.location_latitude and issue.location_longitude and
        haversine_km(longitude, latitude, issue.location_longitude, issue.location_latitude) <= radius_km
    ][:limit]
    
    return attach_issue_metadata(db, nearby, current_user)


@router.get("/{issue_id}/nearby-products", response_model=List[NearbyRecommendedProduct])
async def get_nearby_recommended_products(
    issue_id: str,
    latitude: float = Query(None),
    longitude: float = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Return linked recommendation products sorted by distance from issue/user location."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )

    origin_lat = latitude if latitude is not None else issue.location_latitude
    origin_lon = longitude if longitude is not None else issue.location_longitude

    rows = []
    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.issue_id == issue.id)
        .all()
    )

    for recommendation in recommendations:
        product_ids = recommendation.linked_product_ids or []
        if not product_ids:
            continue

        products = (
            db.query(AgrovetProduct)
            .filter(AgrovetProduct.id.in_(product_ids))
            .all()
        )
        for product in products:
            distance = None
            if origin_lat is not None and origin_lon is not None:
                distance = haversine_km(
                    origin_lon,
                    origin_lat,
                    product.agrovet.location_longitude,
                    product.agrovet.location_latitude,
                )
            rows.append({
                "recommendation_id": str(recommendation.id),
                "farm_input_name": recommendation.farm_input_name,
                "product": product,
                "agrovet": product.agrovet,
                "distance_km": round(distance, 2) if distance is not None else None,
            })

    rows.sort(key=lambda row: row["distance_km"] if row["distance_km"] is not None else float("inf"))
    return rows[:limit]


@router.get("/{issue_id}", response_model=IssueDetailResponse)
async def get_issue(
    issue_id: str,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get single issue by ID"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Increment view count
    issue.views_count += 1
    db.commit()
    
    issue.comments_count = len(issue.comments)
    issue.recommendations_count = len(issue.recommendations)
    if current_user:
        vote = (
            db.query(IssueVote)
            .filter(IssueVote.issue_id == issue.id, IssueVote.user_id == current_user.id)
            .first()
        )
        issue.my_vote = vote.value if vote else 0
    return issue


@router.post("/{issue_id}/vote", response_model=IssueVoteResponse)
async def vote_issue(
    issue_id: str,
    vote_data: IssueVoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create, switch, or clear the current user's vote on an issue."""
    if vote_data.value not in {-1, 0, 1}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Vote value must be -1, 0, or 1"
        )

    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )

    existing_vote = (
        db.query(IssueVote)
        .filter(
            IssueVote.issue_id == issue.id,
            IssueVote.user_id == current_user.id,
        )
        .first()
    )

    my_vote = vote_data.value
    if existing_vote and (vote_data.value == 0 or existing_vote.value == vote_data.value):
        db.delete(existing_vote)
        my_vote = 0
    elif existing_vote:
        existing_vote.value = vote_data.value
        db.add(existing_vote)
    elif vote_data.value != 0:
        db.add(IssueVote(issue_id=issue.id, user_id=current_user.id, value=vote_data.value))

    db.commit()
    db.refresh(issue)

    return {
        "issue_id": issue.id,
        "score": issue_score(db, issue.id),
        "my_vote": my_vote,
    }


@router.put("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: str,
    issue_update: IssueUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an issue (owner only)"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    if issue.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only issue creator can update it"
        )
    
    update_data = issue_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(issue, field, value)
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    return issue


@router.delete("/{issue_id}")
async def delete_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an issue (owner only)"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    if issue.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only issue creator can delete it"
        )
    
    db.delete(issue)
    db.commit()
    
    return {"message": "Issue deleted successfully"}


