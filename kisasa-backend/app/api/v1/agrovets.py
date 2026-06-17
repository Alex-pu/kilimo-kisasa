from math import asin, cos, radians, sin, sqrt
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agrovet import Agrovet
from app.models.product import AgrovetProduct
from app.models.user import User, UserRole
from app.schemas.agrovet_schema import AgrovetCreate, AgrovetResponse, AgrovetUpdate
from app.schemas.product_schema import ProductCreate, ProductResponse
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/agrovets", tags=["agrovets"])


def distance_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


@router.post("/", response_model=AgrovetResponse)
async def create_agrovet(
    agrovet_data: AgrovetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create the current user's agrovet listing."""
    existing_listing = (
        db.query(Agrovet)
        .filter(Agrovet.owner_id == current_user.id)
        .first()
    )
    if existing_listing and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user already has an agrovet listing",
        )

    agrovet = Agrovet(
        owner_id=current_user.id,
        contact_person_name=agrovet_data.contact_person_name or current_user.full_name,
        **agrovet_data.model_dump(exclude={"contact_person_name"}),
    )
    if current_user.role != UserRole.ADMIN:
        current_user.role = UserRole.AGROVET
    db.add(agrovet)
    db.commit()
    db.refresh(agrovet)
    return agrovet


@router.get("/me", response_model=AgrovetResponse)
async def get_my_agrovet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's agrovet listing."""
    agrovet = db.query(Agrovet).filter(Agrovet.owner_id == current_user.id).first()
    if not agrovet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agrovet listing not found",
        )
    return agrovet


@router.get("/managed/", response_model=List[AgrovetResponse])
async def list_managed_agrovets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List agrovet shops owned by the current account."""
    return (
        db.query(Agrovet)
        .filter(Agrovet.owner_id == current_user.id)
        .order_by(Agrovet.created_at.desc())
        .all()
    )


@router.get("/", response_model=List[AgrovetResponse])
async def list_agrovets(
    search: str = Query(None),
    verified: bool = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List agrovets with simple search/filtering."""
    query = db.query(Agrovet)

    if search:
        query = query.filter(Agrovet.name.ilike(f"%{search}%"))
    if verified is not None:
        query = query.filter(Agrovet.verification_status == verified)

    return (
        query.order_by(Agrovet.rating.desc(), Agrovet.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/nearby/", response_model=List[AgrovetResponse])
async def nearby_agrovets(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: int = Query(25, ge=1, le=200),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Find agrovets near a location."""
    agrovets = db.query(Agrovet).limit(limit * 3).all()
    return [
        agrovet
        for agrovet in agrovets
        if distance_km(
            longitude,
            latitude,
            agrovet.location_longitude,
            agrovet.location_latitude,
        )
        <= radius_km
    ][:limit]


@router.get("/{agrovet_id}", response_model=AgrovetResponse)
async def get_agrovet(agrovet_id: str, db: Session = Depends(get_db)):
    """Get an agrovet listing."""
    agrovet = db.query(Agrovet).filter(Agrovet.id == agrovet_id).first()
    if not agrovet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agrovet not found",
        )
    agrovet.products_count = len(agrovet.products)
    return agrovet


@router.put("/{agrovet_id}", response_model=AgrovetResponse)
async def update_agrovet(
    agrovet_id: str,
    agrovet_update: AgrovetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an agrovet listing as its owner or an admin."""
    agrovet = db.query(Agrovet).filter(Agrovet.id == agrovet_id).first()
    if not agrovet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agrovet not found",
        )

    if current_user.role != UserRole.ADMIN and agrovet.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only agrovet owner or admin can update this listing",
        )

    for field, value in agrovet_update.model_dump(exclude_unset=True).items():
        setattr(agrovet, field, value)

    db.add(agrovet)
    db.commit()
    db.refresh(agrovet)
    return agrovet


@router.post("/{agrovet_id}/products", response_model=ProductResponse)
async def create_product(
    agrovet_id: str,
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a product to an agrovet listing as its owner or an admin."""
    agrovet = db.query(Agrovet).filter(Agrovet.id == agrovet_id).first()
    if not agrovet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agrovet not found",
        )
    if current_user.role != UserRole.ADMIN and agrovet.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only agrovet owner or admin can add products",
        )

    product = AgrovetProduct(agrovet_id=agrovet.id, **product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{agrovet_id}/products", response_model=List[ProductResponse])
async def list_products(
    agrovet_id: str,
    category: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List products for an agrovet."""
    agrovet = db.query(Agrovet.id).filter(Agrovet.id == agrovet_id).first()
    if not agrovet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agrovet not found",
        )

    query = db.query(AgrovetProduct).filter(AgrovetProduct.agrovet_id == agrovet_id)
    if category:
        query = query.filter(AgrovetProduct.category == category)

    return query.order_by(AgrovetProduct.product_name.asc()).offset(skip).limit(limit).all()
