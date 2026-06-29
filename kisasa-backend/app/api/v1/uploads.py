from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from firebase_admin import storage
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.firebase_service import firebase_service
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


def store_image_in_firebase(content: bytes, stored_filename: str, content_type: str) -> str:
    firebase_service.ensure_initialized()
    bucket = storage.bucket(settings.firebase_storage_bucket)
    blob = bucket.blob(f"uploads/images/{stored_filename}")
    download_token = str(uuid4())
    blob.metadata = {"firebaseStorageDownloadTokens": download_token}
    blob.upload_from_string(content, content_type=content_type)

    encoded_path = quote(blob.name, safe="")
    return (
        f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/"
        f"{encoded_path}?alt=media&token={download_token}"
    )


@router.post("/images", response_model=UploadedImageResponse)
async def upload_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Store a post image and return its reference link."""
    extension = ALLOWED_IMAGE_TYPES.get(image.content_type or "")
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, WebP, and GIF images are supported",
        )

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
    content_type = image.content_type or "application/octet-stream"
    try:
        image_url = store_image_in_firebase(content, stored_filename, content_type)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not store image: {exc}",
        ) from exc

    uploaded_image = UploadedImage(
        uploaded_by_id=current_user.id,
        original_filename=image.filename or stored_filename,
        stored_filename=stored_filename,
        content_type=content_type,
        file_size=len(content),
        url=image_url,
    )
    db.add(uploaded_image)
    db.commit()
    db.refresh(uploaded_image)

    return uploaded_image
