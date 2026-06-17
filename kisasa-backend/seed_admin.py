from app.database import Base, SessionLocal, engine
from app.models.user import User, UserRole
from app.services.auth_service import auth_service


ADMIN_EMAIL = "kamaua1752@gmail.com"
ADMIN_PASSWORD = "Admin@2026"


def seed_admin():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                firebase_uid=f"local:{ADMIN_EMAIL}",
                email=ADMIN_EMAIL,
                full_name="Kisasa Admin",
            )
            db.add(admin)

        admin.role = UserRole.ADMIN
        admin.verification_status = True
        admin.password_hash = auth_service.hash_password(ADMIN_PASSWORD)
        db.commit()
        print(f"Admin ready: {ADMIN_EMAIL}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
