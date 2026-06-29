import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
from app.config import settings
from app.main import app
from app.database import Base, get_db
from app.models.issue import PostType
from app.models.uploaded_image import UploadedImage
from app.models.user import User, UserRole
from app.firebase_service import _load_firebase_credentials

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_test_db():
    grok_enabled = settings.jack_grok_fallback_enabled
    codex_enabled = settings.jack_codex_fallback_enabled
    settings.jack_grok_fallback_enabled = False
    settings.jack_codex_fallback_enabled = False
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    settings.jack_grok_fallback_enabled = grok_enabled
    settings.jack_codex_fallback_enabled = codex_enabled


class TestHealthCheck:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestRoot:
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "version" in response.json()


class TestAuth:
    def test_firebase_credentials_json_env_is_supported(self, monkeypatch):
        """Test Render-style pasted service account JSON can initialize Firebase."""
        previous_credentials_json = settings.firebase_credentials_json
        previous_credentials_path = settings.firebase_credentials_path
        credential_payload = '{"project_id":"test-project","client_email":"test@example.com"}'
        captured = {}

        def fake_certificate(value):
            captured["value"] = value
            return "credential"

        settings.firebase_credentials_json = credential_payload
        settings.firebase_credentials_path = "./missing-firebase-credentials.json"
        monkeypatch.setattr("app.firebase_service.credentials.Certificate", fake_certificate)

        try:
            assert _load_firebase_credentials() == "credential"
            assert captured["value"]["project_id"] == "test-project"
        finally:
            settings.firebase_credentials_json = previous_credentials_json
            settings.firebase_credentials_path = previous_credentials_path

    def test_render_firebase_secret_file_is_supported(self, monkeypatch, tmp_path):
        """Test Render Secret File named FIREBASE_CREDENTIALS_PATH can initialize Firebase."""
        previous_credentials_json = settings.firebase_credentials_json
        previous_credentials_path = settings.firebase_credentials_path
        secret_file = tmp_path / "FIREBASE_CREDENTIALS_PATH"
        secret_file.write_text('{"project_id":"secret-file-project"}')
        captured = {}

        def fake_certificate(value):
            captured["value"] = value
            return "credential"

        settings.firebase_credentials_json = None
        settings.firebase_credentials_path = "./missing-firebase-credentials.json"
        monkeypatch.setattr("app.firebase_service.RENDER_FIREBASE_SECRET_FILE", str(secret_file))
        monkeypatch.setattr("app.firebase_service.credentials.Certificate", fake_certificate)

        try:
            assert _load_firebase_credentials() == "credential"
            assert captured["value"] == str(secret_file)
        finally:
            settings.firebase_credentials_json = previous_credentials_json
            settings.firebase_credentials_path = previous_credentials_path

    def test_missing_firebase_credentials_fails_fast(self, monkeypatch):
        """Test the app does not silently fall back when Firebase credentials are missing."""
        previous_credentials_json = settings.firebase_credentials_json
        previous_credentials_path = settings.firebase_credentials_path
        settings.firebase_credentials_json = None
        settings.firebase_credentials_path = "./missing-firebase-credentials.json"
        monkeypatch.setattr("app.firebase_service.RENDER_FIREBASE_SECRET_FILE", "./missing-render-secret")

        try:
            with pytest.raises(RuntimeError, match="Firebase credentials are required"):
                _load_firebase_credentials()
        finally:
            settings.firebase_credentials_json = previous_credentials_json
            settings.firebase_credentials_path = previous_credentials_path

    def test_firebase_login_missing_token(self):
        """Test firebase login without token"""
        response = client.post("/api/v1/auth/firebase-login", json={})
        assert response.status_code == 401

    def test_refresh_token_missing(self):
        """Test refresh token endpoint without token"""
        response = client.post("/api/v1/auth/refresh", json={})
        assert response.status_code == 400

    def test_local_register_returns_token(self):
        """Test native local signup for the mobile UI"""
        email = f"local-{uuid4()}@kisasa.local"
        response = client.post(
            "/api/v1/auth/local-register",
            json={
                "identity": email,
                "display_name": "Local Farmer",
                "password": "password123",
                "password_verify": "password123",
            },
        )
        assert response.status_code == 200
        assert response.json()["access_token"]

    def test_local_login_returns_token(self):
        """Test native local login for the mobile UI"""
        email = f"login-{uuid4()}@kisasa.local"
        client.post(
            "/api/v1/auth/local-register",
            json={
                "identity": email,
                "display_name": "Login Farmer",
                "password": "password123",
                "password_verify": "password123",
            },
        )

        response = client.post(
            "/api/v1/auth/local-login",
            json={
                "identity": email,
                "password": "password123",
            },
        )
        assert response.status_code == 200
        assert response.json()["access_token"]

    def test_dev_cors_allows_vite_fallback_port(self):
        """Test Vite dev ports are allowed when 3000 is occupied"""
        response = client.options(
            "/api/v1/auth/local-register",
            headers={
                "Origin": "http://127.0.0.1:3001",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200


class TestIssues:
    def create_user_and_issue(self):
        email = f"vote-{uuid4()}@kisasa.local"
        auth_response = client.post(
            "/api/v1/auth/local-register",
            json={
                "identity": email,
                "display_name": "Vote Farmer",
                "password": "password123",
                "password_verify": "password123",
            },
        )
        headers = {"Authorization": f"Bearer {auth_response.json()['access_token']}"}
        issue_response = client.post(
            "/api/v1/issues/",
            headers=headers,
            json={
                "title": "Beans are wilting",
                "description": "The plants wilt during the day.",
                "category": "water_management",
                "location_name": "Nairobi, Kenya",
            },
        )
        return headers, issue_response.json()["id"]

    def test_list_issues_empty(self):
        """Test listing issues when none exist"""
        response = client.get("/api/v1/issues/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_issues_with_filter(self):
        """Test listing issues with category filter"""
        response = client.get("/api/v1/issues/?category=crop_disease")
        assert response.status_code == 200

    def test_create_issue_with_uploaded_image(self, monkeypatch):
        """Test creating a Reddit-style image post"""
        email = f"image-post-{uuid4()}@kisasa.local"
        auth_response = client.post(
            "/api/v1/auth/local-register",
            json={
                "identity": email,
                "display_name": "Image Farmer",
                "password": "password123",
                "password_verify": "password123",
            },
        )
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        cloudinary_url = "https://res.cloudinary.com/test-cloud/image/upload/v1/kisasa/uploads/images/crop.png"
        monkeypatch.setattr(
            "app.api.v1.uploads.store_image_in_cloudinary",
            lambda content, stored_filename, content_type: cloudinary_url,
        )

        upload_response = client.post(
            "/api/v1/uploads/images",
            headers=headers,
            files={"image": ("crop.png", b"fake-png-bytes", "image/png")},
        )
        assert upload_response.status_code == 200
        uploaded_image = upload_response.json()
        assert uploaded_image["url"] == cloudinary_url

        issue_response = client.post(
            "/api/v1/issues/",
            headers=headers,
            json={
                "title": "Tomato leaves have spots",
                "description": "The leaves have brown spots after rain.",
                "category": "crop_disease",
                "location_name": "Nairobi, Kenya",
                "image_ids": [uploaded_image["id"]],
            },
        )
        assert issue_response.status_code == 200
        issue = issue_response.json()
        assert uploaded_image["url"] in issue["image_urls"]
        assert issue["images"][0]["id"] == uploaded_image["id"]

    def test_upload_accepts_non_firebase_remote_image_url(self, monkeypatch):
        """Test uploads can use any remote storage provider."""
        email = f"remote-upload-{uuid4()}@kisasa.local"
        auth_response = client.post(
            "/api/v1/auth/local-register",
            json={
                "identity": email,
                "display_name": "Remote Upload Farmer",
                "password": "password123",
                "password_verify": "password123",
            },
        )
        headers = {"Authorization": f"Bearer {auth_response.json()['access_token']}"}
        remote_url = "https://kisasa-images.s3.amazonaws.com/uploads/crop.jpg"
        monkeypatch.setattr(
            "app.api.v1.uploads.store_image_in_cloudinary",
            lambda content, stored_filename, content_type: remote_url,
        )

        upload_response = client.post(
            "/api/v1/uploads/images",
            headers=headers,
            files={"image": ("crop.jpg", b"fake-jpg-bytes", "image/jpeg")},
        )

        assert upload_response.status_code == 200
        assert upload_response.json()["url"] == remote_url

    def test_upload_rejects_local_image_url(self, monkeypatch):
        """Test uploads cannot save local /uploads image references."""
        email = f"local-upload-{uuid4()}@kisasa.local"
        auth_response = client.post(
            "/api/v1/auth/local-register",
            json={
                "identity": email,
                "display_name": "Local Upload Farmer",
                "password": "password123",
                "password_verify": "password123",
            },
        )
        headers = {"Authorization": f"Bearer {auth_response.json()['access_token']}"}
        monkeypatch.setattr(
            "app.api.v1.uploads.store_image_in_cloudinary",
            lambda content, stored_filename, content_type: f"/uploads/images/{stored_filename}",
        )

        upload_response = client.post(
            "/api/v1/uploads/images",
            headers=headers,
            files={"image": ("crop.jpg", b"fake-jpg-bytes", "image/jpeg")},
        )

        assert upload_response.status_code == 502
        assert upload_response.json()["detail"] == "Image storage returned a non-remote URL"

        db = TestingSessionLocal()
        try:
            assert db.query(UploadedImage).count() == 0
        finally:
            db.close()

    def test_user_can_upvote_downvote_and_clear_issue_vote(self):
        """Test Reddit-style issue voting"""
        headers, issue_id = self.create_user_and_issue()

        upvote_response = client.post(
            f"/api/v1/issues/{issue_id}/vote",
            headers=headers,
            json={"value": 1},
        )
        assert upvote_response.status_code == 200
        assert upvote_response.json()["score"] == 1
        assert upvote_response.json()["my_vote"] == 1

        downvote_response = client.post(
            f"/api/v1/issues/{issue_id}/vote",
            headers=headers,
            json={"value": -1},
        )
        assert downvote_response.status_code == 200
        assert downvote_response.json()["score"] == -1
        assert downvote_response.json()["my_vote"] == -1

        clear_response = client.post(
            f"/api/v1/issues/{issue_id}/vote",
            headers=headers,
            json={"value": -1},
        )
        assert clear_response.status_code == 200
        assert clear_response.json()["score"] == 0
        assert clear_response.json()["my_vote"] == 0

    def test_issue_list_includes_vote_score(self):
        """Test issue feed includes the current score"""
        headers, issue_id = self.create_user_and_issue()
        client.post(
            f"/api/v1/issues/{issue_id}/vote",
            headers=headers,
            json={"value": 1},
        )

        response = client.get("/api/v1/issues/", headers=headers)
        assert response.status_code == 200
        assert response.json()[0]["score"] == 1
        assert response.json()[0]["my_vote"] == 1

    def test_unauthenticated_user_cannot_vote(self):
        """Test voting requires login"""
        headers, issue_id = self.create_user_and_issue()
        del headers

        response = client.post(
            f"/api/v1/issues/{issue_id}/vote",
            json={"value": 1},
        )
        assert response.status_code in {401, 403}


class TestThreads:
    def create_user_and_issue(self, role=UserRole.FARMER):
        email = f"thread-{uuid4()}@kisasa.local"
        auth_response = client.post(
            "/api/v1/auth/local-register",
            json={
                "identity": email,
                "display_name": "Thread Farmer",
                "password": "password123",
                "password_verify": "password123",
            },
        )
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        if role != UserRole.FARMER:
            db = TestingSessionLocal()
            try:
                user = db.query(User).filter(User.email == email).first()
                user.role = role
                db.commit()
            finally:
                db.close()

        issue_response = client.post(
            "/api/v1/issues/",
            headers=headers,
            json={
                "title": "Maize leaves are yellowing",
                "description": "The crop is yellowing from the base.",
                "category": "soil_health",
                "location_name": "Nairobi, Kenya",
            },
        )
        return headers, issue_response.json()["id"]

    def test_create_and_list_comments(self):
        headers, issue_id = self.create_user_and_issue()

        create_response = client.post(
            f"/api/v1/issues/{issue_id}/comments/",
            headers=headers,
            json={"content": "Try checking soil moisture first."},
        )
        assert create_response.status_code == 200

        list_response = client.get(f"/api/v1/issues/{issue_id}/comments/")
        assert list_response.status_code == 200
        assert list_response.json()[0]["content"] == "Try checking soil moisture first."
        assert list_response.json()[0]["parent_comment_id"] is None

    def test_create_nested_comment_reply(self):
        headers, issue_id = self.create_user_and_issue()

        parent = client.post(
            f"/api/v1/issues/{issue_id}/comments/",
            headers=headers,
            json={"content": "The leaves are yellow near the bottom."},
        ).json()

        reply_response = client.post(
            f"/api/v1/issues/{issue_id}/comments/",
            headers=headers,
            json={
                "content": "That sounds like a moisture or nitrogen issue.",
                "parent_comment_id": parent["id"],
            },
        )
        assert reply_response.status_code == 200
        assert reply_response.json()["parent_comment_id"] == parent["id"]

        list_response = client.get(f"/api/v1/issues/{issue_id}/comments/")
        comments = list_response.json()
        assert comments[1]["content"] == "That sounds like a moisture or nitrogen issue."
        assert comments[1]["parent_comment_id"] == parent["id"]

    def test_nested_comment_parent_must_belong_to_same_issue(self):
        headers, first_issue_id = self.create_user_and_issue()
        _, second_issue_id = self.create_user_and_issue()

        parent = client.post(
            f"/api/v1/issues/{first_issue_id}/comments/",
            headers=headers,
            json={"content": "Parent from another issue."},
        ).json()

        response = client.post(
            f"/api/v1/issues/{second_issue_id}/comments/",
            headers=headers,
            json={
                "content": "This should not attach across issues.",
                "parent_comment_id": parent["id"],
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Parent comment must belong to this issue"

    def test_jack_replies_when_tagged_in_comment(self):
        headers, issue_id = self.create_user_and_issue()

        create_response = client.post(
            f"/api/v1/issues/{issue_id}/comments/",
            headers=headers,
            json={"content": "@Jack what should I check first? The maize is yellowing."},
        )
        assert create_response.status_code == 200

        list_response = client.get(f"/api/v1/issues/{issue_id}/comments/")
        assert list_response.status_code == 200
        comments = list_response.json()
        assert len(comments) == 2
        assert comments[1]["content"].startswith("Jack:")
        assert comments[1]["parent_comment_id"] == comments[0]["id"]

    def test_jack_tag_uses_post_location_and_nearby_agrovet_context(self, monkeypatch):
        captured = {}

        def fake_grok(prompt, issue=None, history=None, farmer_context=None, context_text=None):
            captured["prompt"] = prompt
            captured["issue_title"] = issue.title
            captured["issue_description"] = issue.description
            captured["issue_location_name"] = issue.location_name
            captured["issue_latitude"] = issue.location_latitude
            captured["issue_longitude"] = issue.location_longitude
            captured["context_text"] = context_text
            return "Jack: The berries may be dropping from moisture stress, nutrition, pests, or disease. Mary can check the nearby agrovet listed."

        monkeypatch.setattr(
            "app.jack_assistant.service._generate_grok_fallback",
            fake_grok,
        )

        farmer_headers, _ = self.create_user_and_issue()
        admin_headers, _ = self.create_user_and_issue(role=UserRole.ADMIN)

        issue = client.post(
            "/api/v1/issues/",
            headers=farmer_headers,
            json={
                "title": "Coffee tree shedding berries before maturity",
                "description": "The coffee berries are dropping before they mature.",
                "category": "crop_disease",
                "location_name": "Ruiru, Kenya",
                "location_latitude": -1.1457,
                "location_longitude": 36.9630,
            },
        ).json()

        agrovet = client.post(
            "/api/v1/agrovets/",
            headers=admin_headers,
            json={
                "contact_person_name": "Mary Wanjiku",
                "name": "Ruiru Farm Inputs",
                "phone_number": "+254700000001",
                "location_name": "Ruiru Town",
                "location_latitude": -1.148,
                "location_longitude": 36.96,
            },
        ).json()
        client.post(
            f"/api/v1/agrovets/{agrovet['id']}/products",
            headers=admin_headers,
            json={
                "product_name": "Coffee foliar feed",
                "category": "fertilizer",
                "price": 1200,
                "stock_quantity": 8,
                "unit": "1L",
                "instructions": "Use only after checking label guidance.",
            },
        )

        comment_response = client.post(
            f"/api/v1/issues/{issue['id']}/comments/",
            headers=farmer_headers,
            json={"content": "What can this farmer do? @Jack"},
        )
        assert comment_response.status_code == 200

        comments = client.get(f"/api/v1/issues/{issue['id']}/comments/").json()
        assert len(comments) == 2
        assert comments[1]["parent_comment_id"] == comments[0]["id"]
        assert comments[1]["content"].startswith("Jack:")

        assert captured["prompt"] == "What can this farmer do? @Jack"
        assert captured["issue_title"] == "Coffee tree shedding berries before maturity"
        assert "dropping before they mature" in captured["issue_description"]
        assert captured["issue_location_name"] == "Ruiru, Kenya"
        assert captured["issue_latitude"] == -1.1457
        assert captured["issue_longitude"] == 36.9630
        assert "Nearby agrovet inventory" in captured["context_text"]
        assert "Ruiru Farm Inputs" in captured["context_text"]
        assert "Coffee foliar feed" in captured["context_text"]

    def test_jack_local_fallback_reads_post_context_for_pesticide_question(self):
        farmer_headers, _ = self.create_user_and_issue()
        admin_headers, _ = self.create_user_and_issue(role=UserRole.ADMIN)

        issue = client.post(
            "/api/v1/issues/",
            headers=farmer_headers,
            json={
                "title": "Kales have small insects under the leaves",
                "description": "My sukuma wiki leaves have tiny insects and curling leaves.",
                "category": "pest_management",
                "location_name": "Ruiru, Kenya",
                "location_latitude": -1.1457,
                "location_longitude": 36.9630,
            },
        ).json()
        agrovet = client.post(
            "/api/v1/agrovets/",
            headers=admin_headers,
            json={
                "contact_person_name": "John Kamau",
                "name": "Ruiru Crop Care",
                "phone_number": "+254700000009",
                "location_name": "Ruiru",
                "location_latitude": -1.146,
                "location_longitude": 36.965,
            },
        ).json()
        client.post(
            f"/api/v1/agrovets/{agrovet['id']}/products",
            headers=admin_headers,
            json={
                "product_name": "Vegetable pest control",
                "category": "pesticide",
                "price": 650,
                "stock_quantity": 4,
                "unit": "250ml",
            },
        )

        client.post(
            f"/api/v1/issues/{issue['id']}/comments/",
            headers=farmer_headers,
            json={"content": "@jack, what pesticide will work?"},
        )

        comments = client.get(f"/api/v1/issues/{issue['id']}/comments/").json()
        jack_reply = comments[1]["content"]
        assert "IssueCategory" not in jack_reply
        assert "pest management" in jack_reply
        assert "identify the pest" in jack_reply
        assert "Ruiru Crop Care" in jack_reply
        assert "Vegetable pest control" in jack_reply
        assert "+254700000009" in jack_reply
        assert "visit or call" in jack_reply
        assert "expert recommendation" in jack_reply
        assert comments[1]["parent_comment_id"] == comments[0]["id"]

    def test_chat_with_jack(self):
        response = client.post(
            "/api/v1/jack/chat",
            json={"prompt": "My tomato leaves have brown spots after rain."},
        )
        assert response.status_code == 200
        assert response.json()["assistant"] == "Jack"
        assert "Jack:" in response.json()["reply"]
        assert response.json()["source"] is None

    def test_chat_with_jack_accepts_context_without_using_sources(self):
        response = client.post(
            "/api/v1/jack/chat",
            json={
                "prompt": "How should I handle purple trap aphids?",
                "context_text": (
                    "# Purple Trap Aphids\n"
                    "Scout the underside of leaves every morning. "
                    "Use yellow sticky cards and prune the worst affected shoots."
                ),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["assistant"] == "Jack"
        assert body["source"] is None
        assert "Jack:" in body["reply"]

    def test_chat_with_jack_accepts_farmer_location_context(self):
        response = client.post(
            "/api/v1/jack/chat",
            json={
                "prompt": "My beans are wilting.",
                "farmer_context": {
                    "location_name": "Nakuru, Kenya",
                    "location_latitude": -0.3031,
                    "location_longitude": 36.08,
                },
            },
        )
        assert response.status_code == 200
        assert response.json()["assistant"] == "Jack"

    def test_jack_lists_knowledge_documents(self):
        response = client.get("/api/v1/jack/knowledge")
        assert response.status_code == 200
        sources = {document["source"] for document in response.json()}
        assert "tomato-early-blight.md" in sources

    def test_admin_can_manage_jack_knowledge_documents(self):
        admin_headers, _ = self.create_user_and_issue(role=UserRole.ADMIN)
        filename = "test-jack-admin-note.md"

        create_response = client.post(
            "/api/v1/jack/knowledge",
            headers=admin_headers,
            json={
                "filename": filename,
                "content": "# Admin Jack Note\n\nUse clean trays when raising seedlings.",
            },
        )
        assert create_response.status_code == 200
        assert create_response.json()["source"] == filename

        detail_response = client.get(
            f"/api/v1/jack/knowledge/{filename}",
            headers=admin_headers,
        )
        assert detail_response.status_code == 200
        assert "clean trays" in detail_response.json()["content"]

        list_response = client.get("/api/v1/jack/knowledge")
        sources = {document["source"] for document in list_response.json()}
        assert filename in sources

        delete_response = client.delete(
            f"/api/v1/jack/knowledge/{filename}",
            headers=admin_headers,
        )
        assert delete_response.status_code == 204

    def test_non_admin_cannot_manage_jack_knowledge_documents(self):
        headers, _ = self.create_user_and_issue(role=UserRole.FARMER)

        response = client.post(
            "/api/v1/jack/knowledge",
            headers=headers,
            json={
                "filename": "blocked-note.md",
                "content": "# Blocked Note\n\nThis should not be saved.",
            },
        )
        assert response.status_code == 403

    def test_create_and_list_expert_recommendations(self):
        headers, issue_id = self.create_user_and_issue(role=UserRole.EXPERT)

        create_response = client.post(
            f"/api/v1/issues/{issue_id}/recommendations/",
            headers=headers,
            json={
                "farm_input_name": "Soil test and compost",
                "rationale": "Yellowing can come from nutrient deficiency.",
                "description": "Test first, then amend based on results.",
                "estimated_cost": 1500,
            },
        )
        assert create_response.status_code == 200

        list_response = client.get(f"/api/v1/issues/{issue_id}/recommendations/")
        assert list_response.status_code == 200
        assert list_response.json()[0]["farm_input_name"] == "Soil test and compost"

    def test_expert_can_create_educational_post_and_users_can_comment(self):
        headers, _ = self.create_user_and_issue(role=UserRole.EXPERT)

        post_response = client.post(
            "/api/v1/issues/",
            headers=headers,
            json={
                "title": "How to scout for fall armyworm",
                "description": "Check the whorl early in the morning and look for fresh frass.",
                "post_type": "educational",
                "category": "pest_management",
            },
        )
        assert post_response.status_code == 200
        post = post_response.json()
        assert post["post_type"] == "educational"

        comment_response = client.post(
            f"/api/v1/issues/{post['id']}/comments/",
            headers=headers,
            json={"content": "Helpful guidance."},
        )
        assert comment_response.status_code == 200

    @pytest.mark.parametrize("role", [UserRole.FARMER, UserRole.AGROVET])
    @pytest.mark.parametrize("post_type", [PostType.EDUCATIONAL, PostType.FARMING_NEWS])
    def test_non_experts_cannot_create_expert_post_types(self, role, post_type):
        headers, _ = self.create_user_and_issue(role=role)

        response = client.post(
            "/api/v1/issues/",
            headers=headers,
            json={
                "title": "Restricted expert post",
                "description": "This should be expert-only.",
                "post_type": post_type.value,
                "category": "other",
            },
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Only experts can create educational or farming news posts"

    @pytest.mark.parametrize("role", [UserRole.FARMER, UserRole.AGROVET])
    def test_non_experts_cannot_create_recommendations(self, role):
        headers, issue_id = self.create_user_and_issue(role=role)

        response = client.post(
            f"/api/v1/issues/{issue_id}/recommendations/",
            headers=headers,
            json={
                "farm_input_name": "Restricted recommendation",
                "rationale": "Only experts should be allowed to post this.",
            },
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Only experts can create recommendations"


class TestExpertApplications:
    def create_user(self, role=UserRole.FARMER):
        email = f"expert-app-{uuid4()}@kisasa.local"
        auth_response = client.post(
            "/api/v1/auth/local-register",
            json={
                "identity": email,
                "display_name": "Expert Applicant",
                "password": "password123",
                "password_verify": "password123",
            },
        )
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        if role != UserRole.FARMER:
            db = TestingSessionLocal()
            try:
                user = db.query(User).filter(User.email == email).first()
                user.role = role
                db.commit()
            finally:
                db.close()

        return headers, email

    def test_user_can_apply_for_expert_status(self):
        headers, _ = self.create_user()

        response = client.post(
            "/api/v1/expert-applications/",
            headers=headers,
            json={
                "linkedin_url": "https://www.linkedin.com/in/kisasa-expert",
                "education": "BSc Agriculture, University of Nairobi",
                "credentials": "Plant health certificate",
                "experience_summary": "Five years advising tomato farmers.",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_duplicate_pending_application_is_rejected(self):
        headers, _ = self.create_user()
        payload = {
            "linkedin_url": "https://www.linkedin.com/in/kisasa-expert",
            "education": "BSc Agriculture",
        }

        assert client.post("/api/v1/expert-applications/", headers=headers, json=payload).status_code == 200
        response = client.post("/api/v1/expert-applications/", headers=headers, json=payload)
        assert response.status_code == 409

    def test_only_admin_can_review_application(self):
        applicant_headers, _ = self.create_user()
        application = client.post(
            "/api/v1/expert-applications/",
            headers=applicant_headers,
            json={
                "linkedin_url": "https://www.linkedin.com/in/kisasa-expert",
                "education": "Diploma in Agronomy",
            },
        ).json()

        response = client.put(
            f"/api/v1/expert-applications/{application['id']}/review",
            headers=applicant_headers,
            json={"status": "approved"},
        )
        assert response.status_code == 403

    def test_admin_approval_promotes_user_to_expert(self):
        applicant_headers, applicant_email = self.create_user()
        admin_headers, _ = self.create_user(role=UserRole.ADMIN)
        application = client.post(
            "/api/v1/expert-applications/",
            headers=applicant_headers,
            json={
                "linkedin_url": "https://www.linkedin.com/in/kisasa-expert",
                "education": "MSc Crop Protection",
                "credentials": "Certified agronomist",
            },
        ).json()

        response = client.put(
            f"/api/v1/expert-applications/{application['id']}/review",
            headers=admin_headers,
            json={"status": "approved", "review_notes": "Credentials verified."},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

        db = TestingSessionLocal()
        try:
            user = db.query(User).filter(User.email == applicant_email).first()
            assert user.role == UserRole.EXPERT
            assert user.verification_status is True
        finally:
            db.close()


class TestAgrovetOnboarding:
    def create_user(self, role=UserRole.FARMER):
        email = f"agrovet-{uuid4()}@kisasa.local"
        auth_response = client.post(
            "/api/v1/auth/local-register",
            json={
                "identity": email,
                "display_name": "Agrovet Owner",
                "password": "password123",
                "password_verify": "password123",
            },
        )
        headers = {"Authorization": f"Bearer {auth_response.json()['access_token']}"}

        if role != UserRole.FARMER:
            db = TestingSessionLocal()
            try:
                user = db.query(User).filter(User.email == email).first()
                user.role = role
                db.commit()
            finally:
                db.close()

        return headers, email

    def test_user_can_register_agrovet_and_add_catalogue_item(self):
        headers, _ = self.create_user()

        agrovet_response = client.post(
            "/api/v1/agrovets/",
            headers=headers,
            json={
                "contact_person_name": "Mary Wanjiku",
                "name": "Mary's Farm Inputs",
                "phone_number": "+254700000001",
                "email": "mary.agrovet@example.com",
                "location_name": "Nakuru",
                "location_latitude": -0.3031,
                "location_longitude": 36.0800,
                "address": "Biashara Street",
            },
        )
        assert agrovet_response.status_code == 200
        agrovet = agrovet_response.json()
        assert agrovet["contact_person_name"] == "Mary Wanjiku"

        user_response = client.get("/api/v1/users/me", headers=headers)
        assert user_response.json()["role"] == "agrovet"

        product_response = client.post(
            f"/api/v1/agrovets/{agrovet['id']}/products",
            headers=headers,
            json={
                "product_name": "Tomato fungicide",
                "category": "pesticide",
                "price": 850,
                "stock_quantity": 12,
                "unit": "500g",
                "instructions": "Mix 20g in 20L of water and spray in the evening.",
            },
        )
        assert product_response.status_code == 200
        assert product_response.json()["instructions"] == "Mix 20g in 20L of water and spray in the evening."

        nearby_response = client.get(
            "/api/v1/agrovets/nearby/?latitude=-0.3030&longitude=36.0801&radius_km=5"
        )
        assert nearby_response.status_code == 200
        assert nearby_response.json()[0]["id"] == agrovet["id"]

    def test_only_owner_or_admin_can_add_catalogue_items(self):
        owner_headers, _ = self.create_user()
        other_headers, _ = self.create_user()
        agrovet = client.post(
            "/api/v1/agrovets/",
            headers=owner_headers,
            json={
                "contact_person_name": "Peter Kamau",
                "name": "Kamau Agrovet",
                "phone_number": "+254700000002",
                "location_name": "Eldoret",
                "location_latitude": 0.5143,
                "location_longitude": 35.2698,
            },
        ).json()

        response = client.post(
            f"/api/v1/agrovets/{agrovet['id']}/products",
            headers=other_headers,
            json={
                "product_name": "DAP fertilizer",
                "category": "fertilizer",
                "price": 4200,
                "stock_quantity": 20,
            },
        )
        assert response.status_code == 403

    def test_admin_can_manage_multiple_agrovets_and_add_products(self):
        admin_headers, email = self.create_user(role=UserRole.ADMIN)

        first_response = client.post(
            "/api/v1/agrovets/",
            headers=admin_headers,
            json={
                "contact_person_name": "Jane Admin",
                "name": "Admin Managed Inputs",
                "phone_number": "+254700000010",
                "location_name": "Kisumu",
                "location_latitude": -0.0917,
                "location_longitude": 34.7680,
            },
        )
        second_response = client.post(
            "/api/v1/agrovets/",
            headers=admin_headers,
            json={
                "contact_person_name": "Jane Admin",
                "name": "Admin Rural Agrovet",
                "phone_number": "+254700000011",
                "location_name": "Kericho",
                "location_latitude": -0.3677,
                "location_longitude": 35.2831,
            },
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        assert first_response.json()["owner_id"] == second_response.json()["owner_id"]

        user_response = client.get("/api/v1/users/me", headers=admin_headers)
        assert user_response.json()["role"] == "admin"

        managed_response = client.get("/api/v1/agrovets/managed/", headers=admin_headers)
        assert managed_response.status_code == 200
        assert len(managed_response.json()) == 2

        product_response = client.post(
            f"/api/v1/agrovets/{second_response.json()['id']}/products",
            headers=admin_headers,
            json={
                "product_name": "Admin listed seed",
                "category": "seeds",
                "price": 300,
                "stock_quantity": 40,
                "instructions": "Plant after the first consistent rains.",
            },
        )
        assert product_response.status_code == 200
        assert product_response.json()["product_name"] == "Admin listed seed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
