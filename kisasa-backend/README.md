# Kilimo Kisasa - Backend API

Agricultural social media platform backend built with FastAPI, PostgreSQL, and Firebase.

## Features

- 🌾 **Farm Issues Management** - Farmers post issues, experts provide recommendations
- 💬 **Social Interactions** - Comments, discussions, community support
- 🏪 **Agrovet Integration** - Connect to local agrovets with expert recommendations
- 🔐 **Firebase Auth** - Secure authentication and user management
- 📍 **Location-Based Services** - Find nearby issues and agrovets
- ⚡ **FastAPI** - Modern, async Python web framework
- 📊 **PostgreSQL** - Reliable relational database
- 🐳 **Docker** - Easy deployment and scaling

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15 (Neon Cloud)
- **Authentication**: Firebase Admin SDK
- **ORM**: SQLAlchemy 2.0
- **API Documentation**: OpenAPI/Swagger
- **Python**: 3.11+

## Quick Start

### Prerequisites

- Python 3.11+
- Neon PostgreSQL account (already setup)
- Firebase account
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd kisasa-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Firebase and database credentials
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```
   *(Migrations will connect to Neon cloud database)*

6. **Run development server**
   ```bash
   uvicorn app.main:app --reload
   ```

   API will be available at: `http://localhost:8000`
   API Docs: `http://localhost:8000/api/docs`

## Docker Setup

Run everything with Docker Compose:

```bash
docker-compose up --build
```

Services will start:
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Database**: localhost:5432
- **pgAdmin**: http://localhost:5050

## API Endpoints

### Authentication
- `POST /api/v1/auth/firebase-login` - Login with Firebase token
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/refresh` - Refresh access token

### Users
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update profile
- `GET /api/v1/users/{user_id}` - Get user profile
- `DELETE /api/v1/users/me` - Delete account

### Issues
- `POST /api/v1/issues/` - Create new issue
- `GET /api/v1/issues/` - List issues (with filters)
- `GET /api/v1/issues/{issue_id}` - Get issue details
- `PUT /api/v1/issues/{issue_id}` - Update issue
- `DELETE /api/v1/issues/{issue_id}` - Delete issue
- `GET /api/v1/issues/nearby/` - Get nearby issues

See full API documentation at `/api/docs` when server is running.

## Database Schema

### Core Tables
- `users` - User accounts and profiles
- `issues` - Farm problems/posts
- `comments` - Discussion threads
- `recommendations` - Expert recommendations
- `agrovets` - Agricultural input suppliers
- `agrovet_products` - Product catalogues
- `expert_endorsements` - Expert ratings of agrovets

## Project Structure

```
kisasa-backend/
├── app/
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response models
│   ├── api/v1/              # API endpoints
│   ├── services/            # Business logic
│   ├── middleware/          # Custom middleware
│   ├── utils/               # Utilities & dependencies
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── firebase_service.py  # Firebase integration
│   └── main.py              # FastAPI app
├── migrations/              # Alembic database migrations
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
└── README.md                # This file
```

## Environment Variables

```env
# Firebase
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your_auth_domain
FIREBASE_STORAGE_BUCKET=your_storage_bucket

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/kisasa_db

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
DEBUG=True
```

## Testing

Run tests:
```bash
pytest app/tests/
```

With coverage:
```bash
pytest --cov=app app/tests/
```

## Development

### Create database migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Revert last migration
```bash
alembic downgrade -1
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

## Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Submit a pull request

## Deployment

### Local
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker-compose up -d
```

### Production Notes
- Change `SECRET_KEY` in .env
- Set `DEBUG=False`
- Use strong database password
- Enable HTTPS
- Configure proper CORS origins
- Setup Firebase credentials properly

## Troubleshooting

### Database connection error
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database credentials

### Firebase authentication error
- Verify Firebase credentials file path
- Check Firebase project configuration
- Ensure GOOGLE_APPLICATION_CREDENTIALS is set if using default credentials

### Migration errors
- Delete migrations and start fresh: `alembic stamp head`
- Check database schema manually

## License

[Your License Here]

## Support

For issues and questions:
- 📧 Email: support@kisamoapp.com
- 🐛 Issues: [GitHub Issues]
- 💬 Discussions: [GitHub Discussions]
