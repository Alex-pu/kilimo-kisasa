# QUICK START GUIDE - Kilimo Kisasa Backend

## 🚀 Getting Started (5 minutes)

### Option 1: Quick Start with Docker (Recommended)

```bash
cd kisasa-backend

# Start everything with Docker Compose
docker-compose up --build

# In another terminal, check if API is running
curl http://localhost:8000/health

# Visit API docs
# Browser: http://localhost:8000/api/docs
```

**That's it!** Your backend is running with:
- ✅ PostgreSQL database
- ✅ FastAPI server
- ✅ pgAdmin (http://localhost:5050)
- ✅ Auto-migrations

### Option 2: Manual Setup (Local Development)

#### 1. Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Git

#### 2. Setup
```bash
cd kisasa-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (already created, just verify settings)
cat .env
```

#### 3. Database Setup
```bash
# Using Neon PostgreSQL Cloud (Already configured!)
# Connection string is in .env
# No local PostgreSQL needed - it's cloud-hosted
```

#### 4. Run Migrations
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

#### 5. Start Server
```bash
uvicorn app.main:app --reload

# Server running at http://localhost:8000
```

---

## 📚 Testing the API

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Firebase Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/firebase-login \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_id_token": "YOUR_FIREBASE_TOKEN"
  }'
```

### 3. Create an Issue
```bash
# First get a JWT token from firebase login
TOKEN="your_jwt_token_here"

curl -X POST http://localhost:8000/api/v1/issues/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tomato plant disease",
    "description": "My tomato plants have brown spots",
    "category": "crop_disease",
    "is_urgent": true,
    "location_latitude": -1.2867,
    "location_longitude": 36.8172,
    "location_name": "Nairobi, Kenya"
  }'
```

### 4. Get Current User
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

### 5. List Issues
```bash
curl http://localhost:8000/api/v1/issues/
```

### 6. Get Issue Details
```bash
curl http://localhost:8000/api/v1/issues/{issue_id}
```

---

## 📖 API Documentation

Interactive docs available at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

Try endpoints directly in the browser!

---

## 🔧 Common Commands

```bash
# Run server in debug mode
uvicorn app.main:app --reload

# Run with custom port
uvicorn app.main:app --port 8001

# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Revert last migration
alembic downgrade -1

# Check migration status
alembic current

# View migration history
alembic history

# Run tests
pytest app/tests/

# View database
# Open pgAdmin at http://localhost:5050
# Or use psql
psql -U kisasa_user -d kisasa_db
```

---

## 🔑 Firebase Setup

To use Firebase authentication:

1. Go to Firebase Console: https://console.firebase.google.com
2. Select your project (onlyfarms-1b916)
3. Generate service account key:
   - Settings > Service Accounts > Generate New Private Key
   - Save as `firebase-credentials.json` in project root

Or set environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/firebase-credentials.json"
```

---

## 🌾 Next Steps

### Phase 2: Setup Migrations (Optional - Already auto-done)
- Migrations are auto-generated from models
- Just run: `alembic upgrade head`

### Phase 3: Complete Authentication
- Firebase token validation ✅ (Done)
- JWT generation ✅ (Done)
- Protected routes ✅ (Done)
- Test with real Firebase tokens

### Phase 4: Add More Endpoints
Ready to add:
- Comments CRUD
- Recommendations CRUD
- Agrovet listings
- Search functionality
- Feed algorithm

---

## 🐛 Troubleshooting

### "psycopg2.OperationalError: could not connect to server"
- Check PostgreSQL is running
- Verify DATABASE_URL in .env
- Test connection: `psql -U kisasa_user -d kisasa_db`

### "ModuleNotFoundError: No module named 'app'"
- Ensure you're in `kisasa-backend` directory
- Check virtual environment is activated
- Run: `pip install -r requirements.txt`

### "Invalid Firebase token"
- Verify Firebase credentials path in .env
- Check token hasn't expired
- Test with Firebase emulator

### Port 8000 already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8000   # Windows (then taskkill)
```

### Database migrations not working
```bash
# Reset migrations
alembic downgrade base

# Reinitialize
alembic upgrade head
```

---

## 📝 Project Structure Review

```
kisasa-backend/
├── app/
│   ├── models/          # ✅ 7 ORM models created
│   ├── schemas/         # ✅ Pydantic schemas created
│   ├── api/v1/          # ✅ Basic endpoints created
│   ├── services/        # ✅ Auth service created
│   ├── utils/           # ✅ Dependencies & exceptions
│   ├── main.py          # ✅ FastAPI app
│   ├── config.py        # ✅ Settings
│   ├── database.py      # ✅ DB setup
│   └── firebase_service.py  # ✅ Firebase integration
├── migrations/          # ✅ Alembic setup ready
├── requirements.txt     # ✅ Dependencies listed
├── .env                 # ✅ Configuration ready
├── Dockerfile           # ✅ Container ready
├── docker-compose.yml   # ✅ Full stack ready
└── README.md            # ✅ Full documentation
```

---

## 🎯 What's Ready to Use

### ✅ Authentication
- Firebase token validation
- JWT generation and refresh
- Protected route dependencies

### ✅ User Management
- User registration
- Profile viewing
- Profile updating
- User deletion

### ✅ Issues (Farm Problems)
- Create issues
- List with filtering
- View issue details
- Update issues
- Delete issues
- Find nearby issues

### ✅ Database
- 7 complete ORM models
- Migrations setup
- Relationships defined
- Timestamps on all models

---

## 🚢 Ready for Production?

Before deploying:
- [ ] Change SECRET_KEY in .env
- [ ] Set DEBUG=False
- [ ] Setup proper database credentials
- [ ] Configure CORS_ORIGINS for your domain
- [ ] Setup Firebase service account JSON
- [ ] Use environment variables for secrets
- [ ] Setup HTTPS/SSL
- [ ] Configure logging
- [ ] Setup monitoring/alerts

---

## 📞 Need Help?

- Check README.md for full documentation
- Review .env.example for all configuration options
- Check app/main.py for FastAPI setup
- Visit http://localhost:8000/api/docs for interactive API docs

---

Start server now:
```bash
docker-compose up
```

Or without Docker:
```bash
uvicorn app.main:app --reload
```

Happy developing! 🌾
