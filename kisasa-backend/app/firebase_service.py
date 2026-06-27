import firebase_admin
from firebase_admin import credentials, auth
from app.config import settings
import os


class FirebaseService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            if os.path.exists(settings.firebase_credentials_path):
                cred = credentials.Certificate(settings.firebase_credentials_path)
            else:
                # If no credentials file, initialize without credentials (use GOOGLE_APPLICATION_CREDENTIALS)
                cred = credentials.ApplicationDefault()
            
            firebase_admin.initialize_app(
                cred,
                {"storageBucket": settings.firebase_storage_bucket},
            )
        
        self._initialized = True
    
    @staticmethod
    def verify_id_token(token: str) -> dict:
        """
        Verify Firebase ID token and return user claims
        """
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise Exception(f"Invalid Firebase token: {str(e)}")
    
    @staticmethod
    def get_user(uid: str) -> dict:
        """Get user from Firebase by UID"""
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
    
    @staticmethod
    def create_user(email: str, password: str, display_name: str = None) -> str:
        """Create new Firebase user and return UID"""
        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            return user.uid
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")
    
    @staticmethod
    def update_user_profile(uid: str, display_name: str = None, photo_url: str = None) -> None:
        """Update Firebase user profile"""
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
