import json
import os

import firebase_admin
from firebase_admin import credentials, auth
from app.config import settings

RENDER_FIREBASE_SECRET_FILE = "/etc/secrets/FIREBASE_CREDENTIALS_PATH"


def _load_firebase_credentials():
    credentials_json = settings.firebase_credentials_json
    credentials_path = settings.firebase_credentials_path

    if credentials_json:
        return credentials.Certificate(json.loads(credentials_json))

    if credentials_path.strip().startswith("{"):
        return credentials.Certificate(json.loads(credentials_path))

    if os.path.exists(credentials_path):
        return credentials.Certificate(credentials_path)

    if os.path.exists(RENDER_FIREBASE_SECRET_FILE):
        return credentials.Certificate(RENDER_FIREBASE_SECRET_FILE)

    raise RuntimeError(
        "Firebase credentials are required. Set FIREBASE_CREDENTIALS_JSON, "
        "set FIREBASE_CREDENTIALS_PATH to a real file path, or add a Render "
        "Secret File named FIREBASE_CREDENTIALS_PATH."
    )


class FirebaseService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        pass

    def initialize(self) -> None:
        if self._initialized:
            return

        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            cred = _load_firebase_credentials()

            firebase_admin.initialize_app(
                cred,
                {"storageBucket": settings.firebase_storage_bucket},
            )

        self._initialized = True

    def ensure_initialized(self) -> None:
        self.initialize()
    
    def verify_id_token(self, token: str) -> dict:
        """
        Verify Firebase ID token and return user claims
        """
        self.ensure_initialized()
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise Exception(f"Invalid Firebase token: {str(e)}")
    
    def get_user(self, uid: str) -> dict:
        """Get user from Firebase by UID"""
        self.ensure_initialized()
        try:
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "phone_number": user.phone_number,
                "photo_url": user.photo_url
            }
        except Exception as e:
            raise Exception(f"User not found: {str(e)}")
    
    def create_user(self, email: str, password: str, display_name: str = None) -> str:
        """Create new Firebase user and return UID"""
        self.ensure_initialized()
        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            return user.uid
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")
    
    def update_user_profile(self, uid: str, display_name: str = None, photo_url: str = None) -> None:
        """Update Firebase user profile"""
        self.ensure_initialized()
        try:
            auth.update_user(
                uid,
                display_name=display_name,
                photo_url=photo_url
            )
        except Exception as e:
            raise Exception(f"Failed to update user profile: {str(e)}")


# Singleton instance
firebase_service = FirebaseService()
