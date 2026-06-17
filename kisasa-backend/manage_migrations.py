#!/usr/bin/env python
"""
Migration helper script for Kilimo Kisasa Backend
Simplifies common migration tasks
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from alembic.config import Config
from alembic import command
from app.config import settings
from app.database import engine
from sqlalchemy import inspect


def setup_alembic():
    """Setup Alembic config"""
    alembic_cfg = Config("migrations/alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return alembic_cfg


def get_tables():
    """Get list of tables in database"""
    inspector = inspect(engine)
    return inspector.get_table_names()


def show_status():
    """Show current migration status"""
    print("\n" + "="*60)
    print("MIGRATION STATUS")
    print("="*60)
    
    alembic_cfg = setup_alembic()
    
    try:
        print("\n📍 Current Migration:")
        command.current(alembic_cfg)
    except Exception as e:
        print(f"  No migrations applied yet: {e}")
    
    print("\n📋 Migration History:")
    try:
        command.history(alembic_cfg)
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n🗄️  Database Tables:")
    tables = get_tables()
    if tables:
        for table in sorted(tables):
            print(f"  ✅ {table}")
    else:
        print("  ⚠️  No tables found")
    
    print("\n" + "="*60 + "\n")


def upgrade():
    """Run migrations upgrade"""
    print("\n🔄 Running migrations upgrade...")
    print("="*60)
    
    alembic_cfg = setup_alembic()
    
    try:
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations upgrade completed successfully!")
        show_status()
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)


def downgrade(revision="-1"):
    """Rollback migrations"""
    print(f"\n⏮️  Rolling back to {revision}...")
    print("="*60)
    
    alembic_cfg = setup_alembic()
    
    try:
        command.downgrade(alembic_cfg, revision)
        print(f"✅ Rollback to {revision} completed!")
        show_status()
    except Exception as e:
        print(f"❌ Error during rollback: {e}")
        sys.exit(1)


def create_migration(message):
    """Create new migration"""
    print(f"\n📝 Creating migration: {message}")
    print("="*60)
    
    alembic_cfg = setup_alembic()
    
    try:
        revision = command.revision(alembic_cfg, autogenerate=True, message=message)
        print(f"✅ Migration created: {revision}")
    except Exception as e:
        print(f"❌ Error creating migration: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("""
Usage: python manage_migrations.py [command]

Commands:
  status              Show migration status
  upgrade             Run all pending migrations (migrate up)
  downgrade           Rollback last migration
  downgrade base      Rollback all migrations
  create <message>    Create new migration

Examples:
  python manage_migrations.py status
  python manage_migrations.py upgrade
  python manage_migrations.py downgrade
  python manage_migrations.py downgrade base
  python manage_migrations.py create "Add new column"
        """)
        return
    
    command = sys.argv[1]
    
    if command == "status":
        show_status()
    elif command == "upgrade":
        upgrade()
    elif command == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        downgrade(revision)
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Please provide migration message: python manage_migrations.py create 'Your message'")
            sys.exit(1)
        message = " ".join(sys.argv[2:])
        create_migration(message)
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
