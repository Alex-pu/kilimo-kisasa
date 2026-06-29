from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth_schema import LocalLoginRequest, LocalRegisterRequest, TokenResponse
from app.schemas.user_schema import UserResponse, UserCreate
from app.models.user import User, UserRole
from app.services.auth_service import auth_service
from uuid import uuid4

router = APIRouter(prefix="/auth", tags=["authentication"])


def local_email(identifier: str) -> str:
    value = identifier.strip().lower()
    return value if "@" in value else f"{value}@kisasa.local"


def token_for_user(user: User) -> TokenResponse:
    subject = str(user.id)
    access_token = auth_service.create_access_token(data={"sub": subject})
    refresh_token = auth_service.create_refresh_token(data={"sub": subject})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,
    )


@router.post("/local-login", response_model=TokenResponse)
async def local_login(
    credentials: LocalLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Log in with a database-backed Kisasa account.
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
    Register a database-backed Kisasa account and return a JWT.
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
        firebase_uid=f"user:{uuid4()}",
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
    Register a new user record.
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
    user_payload["firebase_uid"] = f"user:{uuid4()}"
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
