from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.uploaded_image import UploadedImage
from app.models.user import User
from app.schemas.upload_schema import UploadedImageResponse
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@router.post("/images", response_model=UploadedImageResponse)
async def upload_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Store a post image locally and return its reference link."""
    extension = ALLOWED_IMAGE_TYPES.get(image.content_type or "")
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, WebP, and GIF images are supported",
        )

    image_dir = Path(settings.uploads_dir) / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    content = await image.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file is empty",
        )
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be 5 MB or smaller",
        )

    stored_filename = f"{uuid4()}{extension}"
    stored_path = image_dir / stored_filename
    stored_path.write_bytes(content)

    uploaded_image = UploadedImage(
        uploaded_by_id=current_user.id,
        original_filename=image.filename or stored_filename,
        stored_filename=stored_filename,
        content_type=image.content_type or "application/octet-stream",
        file_size=len(content),
        url=f"/uploads/images/{stored_filename}",
    )
    db.add(uploaded_image)
    db.commit()
    db.refresh(uploaded_image)

    return uploaded_image
