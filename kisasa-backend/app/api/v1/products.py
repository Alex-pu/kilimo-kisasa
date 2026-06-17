from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import AgrovetProduct
from app.schemas.product_schema import ProductWithAgrovetResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductWithAgrovetResponse])
async def list_products(
    search: str = Query(None),
    category: str = Query(None),
    in_stock: bool = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search the cross-agrovet product catalogue."""
    query = db.query(AgrovetProduct)

    if search:
        query = query.filter(
            or_(
                AgrovetProduct.product_name.ilike(f"%{search}%"),
                AgrovetProduct.description.ilike(f"%{search}%"),
            )
        )
    if category:
        query = query.filter(AgrovetProduct.category == category)
    if in_stock is not None:
        if in_stock:
            query = query.filter(AgrovetProduct.stock_quantity > 0)
        else:
            query = query.filter(AgrovetProduct.stock_quantity <= 0)

    return (
        query.order_by(AgrovetProduct.product_name.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
