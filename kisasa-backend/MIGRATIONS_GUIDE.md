# Database Migrations Guide

## What Happened

I've created the **initial migration** file that will:
- Create 7 database tables
- Set up all relationships
- Add indexes for performance
- Configure constraints

## Migration File

**Location**: `migrations/versions/001_initial_schema.py`

**Tables Created**:
1. ✅ `users` - User accounts and profiles
2. ✅ `issues` - Farm problems/posts
3. ✅ `comments` - Discussion threads
4. ✅ `recommendations` - Expert suggestions
5. ✅ `agrovets` - Agricultural suppliers
6. ✅ `agrovet_products` - Product catalogues
7. ✅ `expert_endorsements` - Expert ratings

---

## Run Migrations

### Option 1: Docker (Automatic)
Migrations run automatically when you start Docker:
```bash
cd kisasa-backend
docker-compose up --build
```

The startup command includes:
```bash
alembic upgrade head
```

### Option 2: Local Python
```bash
cd kisasa-backend

# Activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Verify tables were created
alembic current
```

### Option 3: Manual Commands

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Apply all pending migrations
alembic upgrade head

# Apply one specific migration
alembic upgrade 001_initial_schema

# Rollback last migration
alembic downgrade -1

# Rollback to specific migration
alembic downgrade 001_initial_schema

# Rollback all migrations
alembic downgrade base
```

---

## Verify Migrations Worked

### Check Migration Status
```bash
alembic current
# Output: 001_initial_schema
```

### List All Tables (via psql)
```bash
psql postgresql://USER:PASSWORD@HOST/neondb?sslmode=require

# Inside psql:
\dt                    # List all tables
\d+ users              # Show users table schema
\d+ issues             # Show issues table schema
# etc...
\q                     # Exit
```

### Check via pgAdmin (If Running)
1. Open http://localhost:5050
2. Username: admin@kisasa.com
3. Password: admin
4. Browse: Servers > Neon Database > Databases > neondb > Schemas > public > Tables

### Check via Python
```bash
cd kisasa-backend
python -c "
from sqlalchemy import inspect
from app.database import engine

inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables created:')
for table in sorted(tables):
    print(f'  - {table}')
"
```

### Check via API Health
```bash
# If server is running
curl http://localhost:8000/health
# If database is connected properly, you'll get a 200 response
```

---

## Database Schema Overview

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  firebase_uid VARCHAR UNIQUE,
  email VARCHAR UNIQUE,
  full_name VARCHAR,
  role ENUM (farmer, expert, agrovet, admin),
  profile_pic_url VARCHAR,
  location_latitude FLOAT,
  location_longitude FLOAT,
  verification_status BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
)
```

### Issues Table
```sql
CREATE TABLE issues (
  id UUID PRIMARY KEY,
  creator_id UUID REFERENCES users(id),
  title VARCHAR(255),
  description TEXT,
  category ENUM (crop_disease, pest_management, ...),
  status ENUM (open, in_progress, resolved, closed),
  image_urls VARCHAR ARRAY,
  location_latitude FLOAT,
  location_longitude FLOAT,
  views_count INT DEFAULT 0,
  is_urgent BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
)
```

### Comments Table
```sql
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  issue_id UUID REFERENCES issues(id),
  author_id UUID REFERENCES users(id),
  content TEXT,
  media_urls VARCHAR ARRAY,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
)
```

### Recommendations Table
```sql
CREATE TABLE recommendations (
  id UUID PRIMARY KEY,
  issue_id UUID REFERENCES issues(id),
  recommender_id UUID REFERENCES users(id),
  farm_input_name VARCHAR(255),
  rationale TEXT,
  estimated_cost FLOAT,
  linked_product_ids UUID ARRAY,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
)
```

### Agrovets Table
```sql
CREATE TABLE agrovets (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  phone_number VARCHAR,
  email VARCHAR,
  location_latitude FLOAT,
  location_longitude FLOAT,
  location_name VARCHAR,
  verification_status BOOLEAN DEFAULT false,
  rating FLOAT DEFAULT 0.0,
  review_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
)
```

### Agrovet Products Table
```sql
CREATE TABLE agrovet_products (
  id UUID PRIMARY KEY,
  agrovet_id UUID REFERENCES agrovets(id),
  product_name VARCHAR(255),
  category VARCHAR(100),
  price FLOAT,
  currency VARCHAR(3) DEFAULT 'KES',
  stock_quantity INT DEFAULT 0,
  unit VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
)
```

### Expert Endorsements Table
```sql
CREATE TABLE expert_endorsements (
  id UUID PRIMARY KEY,
  expert_id UUID REFERENCES users(id),
  agrovet_id UUID REFERENCES agrovets(id),
  rating FLOAT,
  review_text TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
)
```

---

## Creating New Migrations

### After Modifying Models

If you change any model (add/remove/modify columns):

```bash
# Auto-generate migration based on model changes
alembic revision --autogenerate -m "Add new column to issues"

# Review the generated migration
cat migrations/versions/002_*.py

# Apply it
alembic upgrade head
```

### Manual Migration

For more control:

```bash
# Create empty migration
alembic revision -m "Custom migration name"

# Edit the generated file in migrations/versions/
# Add upgrade() and downgrade() code

# Apply it
alembic upgrade head
```

---

## Troubleshooting

### "FAILED: Target database is not up to date"
```bash
# Check current status
alembic current

# Apply pending migrations
alembic upgrade head
```

### "Foreign key constraint fails"
- Ensure parent tables are created first
- Check migration order in `down_revision`
- Create new tables in dependency order

### "Column already exists"
- Check if migration was already applied
- Use `alembic current` to see latest
- Revert and reapply if needed

### "Cannot drop table - foreign key constraint"
- Drop dependent tables first
- Or drop constraints before dropping table
- Check downgrade() function

### Connection Timeout
- Verify Neon database is accessible
- Check `DATABASE_URL` in `.env`
- Ensure SSL mode is enabled
- Test: `psql postgresql://...`

---

## Migration Status Commands

```bash
# Current migration
alembic current

# Next pending migration
alembic upgrade --sql

# Show what would be migrated
alembic upgrade --sql head

# Show history
alembic history

# Show heads
alembic heads

# Show branches
alembic branches
```

---

## Best Practices

1. **Test migrations locally first**
   ```bash
   # Test upgrade
   alembic upgrade head
   
   # Test downgrade
   alembic downgrade base
   
   # Test upgrade again
   alembic upgrade head
   ```

2. **Always write both upgrade() and downgrade()**
   - Ensures you can rollback if needed

3. **Use descriptive migration names**
   ```bash
   alembic revision -m "Add user verification_status column"  # ✅ Good
   alembic revision -m "Update"                               # ❌ Bad
   ```

4. **Keep migrations small and focused**
   - One feature per migration
   - Easier to rollback if issues

5. **Never edit migration files after running**
   - Create new migration instead
   - Ensures history is consistent

---

## Next Steps

1. ✅ **Run migrations**
   ```bash
   docker-compose up --build
   # OR
   alembic upgrade head
   ```

2. ✅ **Verify tables created**
   ```bash
   alembic current
   ```

3. ✅ **Start using the API**
   - Visit http://localhost:8000/api/docs
   - Test endpoints

4. ✅ **Monitor database**
   - Visit Neon console: https://console.neon.tech
   - Or pgAdmin: http://localhost:5050

---

## Files Created

- `migrations/versions/001_initial_schema.py` - Initial migration
- `migrations/env.py` - Updated to use app config
- `migrations/alembic.ini` - Updated configuration

---

Ready to run migrations! 🚀
