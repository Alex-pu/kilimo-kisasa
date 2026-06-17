# Neon PostgreSQL Setup Guide

## Overview

Your Kilimo Kisasa backend is configured to use **Neon PostgreSQL**, a cloud-hosted PostgreSQL database. This means:

✅ **No local PostgreSQL needed**  
✅ **Automatic backups**  
✅ **Scalable infrastructure**  
✅ **Free tier available**  
✅ **Connection pooling included**  

## Current Configuration

```
Database: neondb
Host: your-neon-host
User: your-neon-user
Password: your-neon-password
Region: US-East-1 (AWS)
SSL Mode: Required
```

## Starting the Backend

### With Docker (Simplest)
```bash
cd kisasa-backend
docker-compose up --build
```

The backend will:
1. Connect to Neon cloud database
2. Run migrations automatically
3. Start at http://localhost:8000

### Without Docker (Local)
```bash
cd kisasa-backend

# Activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (connects to Neon)
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## Managing Your Database

### Option 1: Neon Console (Recommended)
1. Go to https://console.neon.tech
2. Log in to your account
3. Select the project
4. View tables, data, and backups

### Option 2: pgAdmin (Web Interface)
When running Docker Compose:
1. Open http://localhost:5050
2. Add server connection:
   - Name: Neon Database
   - Host: `your-neon-host`
   - Port: `5432`
   - Username: `your-neon-user`
   - Password: `your-neon-password`
   - SSL Mode: Require

### Option 3: psql Command Line
```bash
psql postgresql://USER:PASSWORD@HOST/neondb?sslmode=require

# Inside psql:
\dt                    # List tables
\d+ users              # Show table schema
SELECT * FROM users;   # Query data
\q                     # Exit
```

### Option 4: Python
```python
from sqlalchemy import inspect
from app.database import engine

# Get table names
inspector = inspect(engine)
print(inspector.get_table_names())

# Query data
from app.models import User
from app.database import SessionLocal

db = SessionLocal()
users = db.query(User).all()
print(users)
db.close()
```

## Environment Variables

Connection string is in `.env`:
```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/neondb?sslmode=require&channel_binding=require
```

## Important Notes

### ⚠️ Keep Credentials Secure
- **Never commit `.env` to Git**
- `.gitignore` already excludes it
- In production, use environment variables only
- Rotate credentials if exposed

### 🔒 Connection Security
- SSL Mode: **Required** (sslmode=require)
- Channel Binding: **Required** (channel_binding=require)
- These ensure encrypted connections to the database

### 📊 Database Limits
- Free tier: Up to 30 GB storage
- Fair usage: Connections, CPU, bandwidth shared
- See https://neon.tech/pricing for tier details

### 🚀 Performance Tips
- Connection pooling is enabled (built-in to Neon)
- Migrations auto-run on container startup
- Keep indexes on frequently queried columns

## Troubleshooting

### Connection Refused
```bash
# Check internet connection (Neon is cloud-hosted)
ping google.com

# Verify credentials in .env
cat .env | grep DATABASE_URL

# Test connection directly
psql postgresql://USER:PASSWORD@HOST/...
```

### SSL Mode Error
If you get `SSL mode required` error:
- Connection string already has `?sslmode=require`
- Ensure you're not modifying DATABASE_URL
- Use exact string from .env

### Slow Queries
- Check Neon console for slow queries
- Add indexes if needed
- Monitor CPU/connections in Neon dashboard

### Data Not Persisting
- Verify migrations ran: `alembic current`
- Check database in Neon console
- Ensure DATABASE_URL is correct

## Scaling Your Database

When you need more power:

### Upgrade Tier
1. Go to https://console.neon.tech
2. Settings > Plan
3. Choose paid tier for higher limits

### Add Replicas (Pro)
1. Console > Compute
2. Add read-only replicas for load distribution

### Backup Strategy
- Neon auto-backs up data
- 30-day retention on paid plans
- Manual backups available

## Database Migrations

### Auto-migrations on Startup
When you run `docker-compose up`:
```bash
alembic upgrade head
```
Runs automatically before server starts

### Manual Migration Commands
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Check status
alembic current

# View history
alembic history

# Revert last migration
alembic downgrade -1
```

## Monitoring & Alerts

### In Neon Console
- View connection count
- Monitor query performance
- Check storage usage
- View recent backups

### In Application
Add logging to app/main.py:
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log database connections
logger.info("Database connected successfully")
```

## Next Steps

1. ✅ **Start Backend**
   ```bash
   docker-compose up
   ```

2. ✅ **Test API**
   ```bash
   curl http://localhost:8000/health
   ```

3. ✅ **Browse Data** (Optional)
   - Open http://localhost:5050 (pgAdmin)
   - Or https://console.neon.tech (Neon console)

4. ✅ **Check Migrations**
   ```bash
   alembic current
   ```

5. ✅ **Test Auth** (when frontend ready)
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/firebase-login \
     -d '{"firebase_id_token": "YOUR_TOKEN"}'
   ```

## Resources

- **Neon Docs**: https://neon.tech/docs
- **PostgreSQL Docs**: https://www.postgresql.org/docs
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org
- **Alembic Docs**: https://alembic.sqlalchemy.org

## Questions?

Check:
1. `.env` file for configuration
2. README.md for full documentation
3. QUICKSTART.md for setup help
4. API Docs at http://localhost:8000/api/docs

---

**Ready to go!** Your database is in the cloud and your backend is ready. 🚀
