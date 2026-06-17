from fastapi import APIRouter

# Import all routers
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.issues import router as issues_router
from app.api.v1.comments import router as comments_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.agrovets import router as agrovets_router
from app.api.v1.products import router as products_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.expert_applications import router as expert_applications_router
from app.jack_assistant.router import router as jack_assistant_router

# Create main router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(issues_router)
api_router.include_router(comments_router)
api_router.include_router(recommendations_router)
api_router.include_router(agrovets_router)
api_router.include_router(products_router)
api_router.include_router(uploads_router)
api_router.include_router(expert_applications_router)
api_router.include_router(jack_assistant_router)

__all__ = ["api_router"]
