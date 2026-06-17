from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.product_schema import ProductWithAgrovetResponse


class RecommendationBase(BaseModel):
    farm_input_name: str
    rationale: str


class RecommendationCreate(RecommendationBase):
    description: Optional[str] = None
    estimated_cost: Optional[float] = None
    linked_product_ids: Optional[List[UUID]] = None


class RecommendationResponse(RecommendationBase):
    id: UUID
    issue_id: UUID
    recommender_id: UUID
    description: Optional[str] = None
    estimated_cost: Optional[float] = None
    linked_product_ids: Optional[List[UUID]] = None
    linked_products: Optional[List[ProductWithAgrovetResponse]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class RecommendationDetailResponse(RecommendationResponse):
    recommender: Optional[dict] = None
