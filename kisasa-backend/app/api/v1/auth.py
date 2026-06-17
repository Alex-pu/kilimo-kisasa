from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth_schema import LocalLoginRequest, LocalRegisterRequest, TokenResponse
from app.schemas.user_schema import UserResponse, UserCreate
from app.models.user import User, UserRole
from app.services.auth_service import auth_service
from app.firebase_service import firebase_service
from datetime import timedelta
from uuid import uuid4

router = APIRouter(prefix="/auth", tags=["authentication"])


def local_email(identifier: str) -> str:
    value = identifier.strip().lower()
    return value if "@" in value else f"{value}@kisasa.local"


def token_for_user(user: User) -> TokenResponse:
    access_token = auth_service.create_access_token(data={"sub": user.firebase_uid})
    refresh_token = auth_service.create_refresh_token(data={"sub": user.firebase_uid})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,
    )


@router.post("/firebase-login", response_model=TokenResponse)
async def firebase_login(
    firebase_token: dict,
    db: Session = Depends(get_db)
):
    """
    Exchange Firebase ID token for JWT access token
    
    Request body:
    ```json
    {
        "firebase_id_token": "your_firebase_token_here"
    }
    ```
    """
    try:
        # Verify Firebase token
        firebase_id_token = firebase_token.get("firebase_id_token")
        if not firebase_id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="firebase_id_token is required"
            )
        
        decoded_token = firebase_service.verify_id_token(firebase_id_token)
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        
        # Check if user exists
        user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
        
        if not user:
            # Create new user from Firebase data
            firebase_user_info = firebase_service.get_user(firebase_uid)
            user = User(
                firebase_uid=firebase_uid,
                email=email or firebase_user_info.get("email"),
                full_name=firebase_user_info.get("display_name", ""),
                profile_pic_url=firebase_user_info.get("photo_url")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create JWT token
        access_token_expires = timedelta(minutes=30)
        access_token = auth_service.create_access_token(
            data={"sub": firebase_uid},
            expires_delta=access_token_expires
        )
        
        refresh_token = auth_service.create_refresh_token(
            data={"sub": firebase_uid}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/local-login", response_model=TokenResponse)
async def local_login(
    credentials: LocalLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Local development login for the mobile UI.

    Firebase remains the production auth path. This endpoint keeps the frontend
    on Kisasa-native routes while the local user model has no password column.
    """
    if not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="password is required",
        )

    email = local_email(credentials.identity)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if user.password_hash and not auth_service.verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )

    return token_for_user(user)


@router.post("/local-register", response_model=TokenResponse)
async def local_register(
    user_data: LocalRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Local development signup that returns a Kisasa JWT.
    """
    username = user_data.display_name.strip()
    email = local_email(user_data.identity)

    if len(username) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username must be at least 2 characters",
        )
    if not user_data.password or user_data.password != user_data.password_verify:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="passwords do not match",
        )

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = User(
        firebase_uid=f"local:{email}",
        email=email,
        password_hash=auth_service.hash_password(user_data.password),
        full_name=username,
        role=UserRole.FARMER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return token_for_user(user)


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user (requires Firebase authentication first)
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    user_payload = user_data.model_dump()
    user_payload["role"] = UserRole.FARMER
    user_payload["firebase_uid"] = (
        user_payload.get("firebase_uid")
        or f"local:{user_data.email}:{uuid4()}"
    )
    user = User(**user_payload)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token_request: dict
):
    """
    Refresh access token using refresh token
    
    Request body:
    ```json
    {
        "refresh_token": "your_refresh_token_here"
    }
    ```
    """
    refresh_token = refresh_token_request.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token is required"
        )

    try:
        payload = auth_service.verify_access_token(refresh_token)
        user_id = payload.get("sub")
        
        access_token_expires = timedelta(minutes=30)
        new_access_token = auth_service.create_access_token(
            data={"sub": user_id},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=new_access_token,
            expires_in=30 * 60
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
