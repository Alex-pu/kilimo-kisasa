import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
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


def is_remote_storage_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def get_cloudinary_credentials() -> tuple[str, str, str]:
    cloudinary_url = settings.cloudinary_url
    if not cloudinary_url:
        raise RuntimeError("CLOUDINARY_URL is required for image uploads.")

    parsed = urlparse(cloudinary_url)
    if parsed.scheme != "cloudinary" or not parsed.username or not parsed.password or not parsed.hostname:
        raise RuntimeError("CLOUDINARY_URL must use cloudinary://<api_key>:<api_secret>@<cloud_name>.")

    return parsed.hostname, parsed.username, parsed.password


def make_cloudinary_signature(params: dict[str, str], api_secret: str) -> str:
    signing_payload = "&".join(f"{key}={params[key]}" for key in sorted(params))
    return hashlib.sha1(f"{signing_payload}{api_secret}".encode("utf-8")).hexdigest()


def encode_multipart_form(fields: dict[str, str], file_field: str, filename: str, content: bytes, content_type: str) -> tuple[bytes, str]:
    boundary = f"----kisasa-{uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                f"{value}\r\n".encode("utf-8"),
            ]
        )

    chunks.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            content,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def store_image_in_cloudinary(content: bytes, stored_filename: str, content_type: str) -> str:
    cloud_name, api_key, api_secret = get_cloudinary_credentials()
    public_id = Path(stored_filename).stem
    timestamp = str(int(time.time()))
    signed_params = {
        "folder": "kisasa/uploads/images",
        "public_id": public_id,
        "timestamp": timestamp,
    }
    fields = {
        **signed_params,
        "api_key": api_key,
        "signature": make_cloudinary_signature(signed_params, api_secret),
    }
    body, multipart_content_type = encode_multipart_form(
        fields,
        "file",
        stored_filename,
        content,
        content_type,
    )
    request = Request(
        f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
        data=body,
        headers={"Content-Type": multipart_content_type},
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudinary upload failed ({exc.code}): {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"Cloudinary upload failed: {exc.reason}") from exc

    image_url = payload.get("secure_url") or payload.get("url")
    if not isinstance(image_url, str):
        raise RuntimeError("Cloudinary upload response did not include an image URL.")
    return image_url


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
        image_url = store_image_in_cloudinary(content, stored_filename, content_type)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not store image: {exc}",
        ) from exc
    if not is_remote_storage_url(image_url):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image storage returned a non-remote URL",
        )

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
