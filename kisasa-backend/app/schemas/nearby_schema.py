from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.schemas.product_schema import ProductAgrovetSummary, ProductResponse


class NearbyRecommendedProduct(BaseModel):
    recommendation_id: UUID
    farm_input_name: str
    product: ProductResponse
    agrovet: ProductAgrovetSummary
    distance_km: Optional[float] = None
