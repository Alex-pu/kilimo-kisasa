# Kilimo Kisasa Backend - Command Reference

## 🚀 Start Server

### Option A: Docker (Recommended - Easiest)
```bash
cd kisasa-backend
docker-compose up --build
```
- Backend: http://localhost:8000
- pgAdmin: http://localhost:5050
- API Docs: http://localhost:8000/api/docs

### Option B: Local Python
```bash
cd kisasa-backend

# Create virtual environment (first time only)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start PostgreSQL (ensure it's running)
# Then run:
uvicorn app.main:app --reload
```
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

---

## 🔧 Database Commands

```bash
# Create initial migration from models
alembic revision --autogenerate -m "Initial schema"

# Apply all migrations
alembic upgrade head

# Check current migration status
alembic current

# View migration history
alembic history

# Revert to previous migration
alembic downgrade -1

# Drop all tables and reset
alembic downgrade base
alembic upgrade head
```

---

## 🧪 Testing

```bash
# Run all tests
pytest app/tests/ -v

# Run specific test file
pytest app/tests/test_api.py -v

# Run with coverage report
pytest app/tests/ --cov=app --cov-report=html

# Run in watch mode (requires pytest-watch)
ptw app/tests/
```

---

## 📝 Creating New Models

1. Create model file in `app/models/new_model.py`:
```python
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class NewModel(Base):
    __tablename__ = "new_models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Add columns...
```

2. Create schema in `app/schemas/new_schema.py`:
```python
from pydantic import BaseModel

class NewModelCreate(BaseModel):
    # Add fields...
    pass

class NewModelResponse(NewModelCreate):
    id: str
    # Add response fields...
```

3. Create endpoints in `app/api/v1/new_endpoint.py`:
```python
from fastapi import APIRouter, Depends
router = APIRouter(prefix="/new", tags=["new"])

@router.post("/", response_model=NewModelResponse)
def create(data: NewModelCreate, db: Session = Depends(get_db)):
    # Implementation
    pass
```

4. Include router in `app/api/v1/__init__.py`

5. Generate migration:
```bash
alembic revision --autogenerate -m "Add NewModel"
alembic upgrade head
```

---

## 📦 Adding Dependencies

```bash
# Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Install in virtual environment
pip install new-package

# Update requirements.txt with pinned versions
pip freeze > requirements.txt
```

---

## 🔍 Debugging

### Check Running Processes
```bash
# Check if port 8000 is in use
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9  # Mac/Linux
```

### Database Debugging (Neon Cloud)
```bash
# Connect to Neon database directly
psql postgresql://USER:PASSWORD@HOST/neondb?sslmode=require

# Or use pgAdmin at http://localhost:5050 (if running)
# Email: admin@kisasa.com
# Password: admin

# Check connection from Python
python -c "from app.database import engine; print(engine.url)"
```

### API Debugging
```bash
# Test endpoint with curl
curl -X GET http://localhost:8000/health

# With headers
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# POST with data
curl -X POST http://localhost:8000/api/v1/issues/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","description":"Test","category":"crop_disease"}'
```

---

## 🐳 Docker Commands

```bash
# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Logs for specific service
docker-compose logs -f backend

# Stop services
docker-compose down

# Remove all data (fresh start)
docker-compose down -v

# Rebuild only backend
docker-compose build backend

# Execute command in container
docker-compose exec backend bash

# Drop into Python shell in container
docker-compose exec backend python -i app/main.py
```

---

## 🔐 Firebase Integration

### Get Firebase Credentials
1. Go to Firebase Console: https://console.firebase.google.com
2. Select project: onlyfarms-1b916
3. Settings > Service Accounts > Generate New Private Key
4. Save as `firebase-credentials.json` in project root

### Test Firebase Integration
```python
from app.firebase_service import firebase_service

# Verify a Firebase token
user_data = firebase_service.verify_id_token("firebase_token_here")
print(user_data)

# Get user from Firebase
user = firebase_service.get_user("uid_here")
print(user)
```

---

## 📊 API Testing Tools

### Interactive: Swagger UI
```
http://localhost:8000/api/docs
```

### Interactive: ReDoc
```
http://localhost:8000/api/redoc
```

### Command Line: curl
```bash
# GET request
curl http://localhost:8000/api/v1/issues/

# POST request
curl -X POST http://localhost:8000/api/v1/issues/ \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Python: httpx
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8000/api/v1/issues/")
    print(response.json())
```

### Python: requests
```python
import requests

response = requests.get("http://localhost:8000/api/v1/issues/")
print(response.json())
```

---

## 📂 Project Navigation

```bash
# Backend root
cd kisasa-backend

# View directory structure
tree -L 2 -I '__pycache__'
# Or on Windows:
# powershell command

# List main files
ls -la

# View specific file
cat app/main.py
```

---

## 🔄 Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/add-comments
```

### 2. Make Changes
- Add model in `app/models/`
- Add schema in `app/schemas/`
- Add endpoint in `app/api/v1/`
- Add tests in `app/tests/`

### 3. Run Tests
```bash
pytest app/tests/ -v
```

### 4. Create Migration
```bash
alembic revision --autogenerate -m "Add comments feature"
alembic upgrade head
```

### 5. Commit & Push
```bash
git add .
git commit -m "feat: add comments feature"
git push origin feature/add-comments
```

---

## 🔑 Common Errors & Fixes

| Error | Solution |
|-------|----------|
| `psycopg2.OperationalError: could not connect` | Ensure PostgreSQL running, check DATABASE_URL |
| `ModuleNotFoundError: app` | Activate virtual environment, in correct directory |
| `Address already in use` | Kill process: `lsof -ti:8000 \| xargs kill -9` |
| `Invalid Firebase token` | Verify credentials file, check token freshness |
| `Alembic table not found` | Run: `alembic upgrade head` |
| `CORS error in frontend` | Add frontend URL to CORS_ORIGINS in .env |

---

## 📈 Scaling Checklist

- [ ] Add database connection pooling
- [ ] Add caching layer (Redis)
- [ ] Add rate limiting
- [ ] Add request logging
- [ ] Add application monitoring
- [ ] Setup CI/CD pipeline
- [ ] Add database backups
- [ ] Setup load balancer
- [ ] Add full-text search (PostgreSQL FTS)
- [ ] Add async task queue (Celery)

---

## 🌐 Environment Variables Guide

| Variable | Purpose | Example |
|----------|---------|---------|
| DATABASE_URL | PostgreSQL connection | postgresql://user:pass@host:5432/db |
| SECRET_KEY | JWT signing key | your-secret-key-here |
| FIREBASE_PROJECT_ID | Firebase project | onlyfarms-1b916 |
| DEBUG | Enable debug mode | True/False |
| CORS_ORIGINS | Allowed frontend origins | ["http://localhost:3000"] |

---

## 📚 Documentation Files

- **README.md** - Full project documentation
- **QUICKSTART.md** - 5-minute setup guide
- **COMMAND_REFERENCE.md** - This file
- **API Docs** - Interactive at `/api/docs`

---

## 🆘 Getting Help

1. Check README.md for full docs
2. Check QUICKSTART.md for setup issues
3. Check error message in API response
4. Check `/api/docs` for endpoint documentation
5. Check test files for usage examples
