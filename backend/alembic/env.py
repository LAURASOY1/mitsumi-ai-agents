from logging.config import fileConfig
import os
import asyncio
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from alembic import context

from app.models.base import Base
from app.core.config import settings

# CONFIGURATION

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Get database URL from settings (resolves secrets)
DATABASE_URL = settings.resolved_postgres_url if hasattr(settings, 'resolved_postgres_url') else settings.POSTGRES_URL

# ASYNC SUPPORT

def do_run_migrations(connection):
    """Run migrations with comparison support"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,           # Detect type changes
        compare_server_default=True, # Detect default value changes
        render_as_batch=True,        # Better for SQLite (not needed for PG)
        include_schemas=True,
        version_table='alembic_version',
        version_table_schema='public',
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online_async():
    """Run migrations with advisory lock for multi-replica safety"""
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)
    
    async with engine.connect() as connection:
        # 🔒 GET ADVISORY LOCK - prevents multiple replicas from running migrations
        # Lock ID: 123456789 (unique for this project)
        await connection.execute(text("SELECT pg_advisory_lock(123456789)"))
        
        try:
            # Run migrations
            await connection.run_sync(do_run_migrations)
            print("✅ Migrations completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise
            
        finally:
            # 🔓 RELEASE LOCK
            await connection.execute(text("SELECT pg_advisory_unlock(123456789)"))
            await connection.commit()

# OFFLINE MODE (For script generation)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()
    print("✅ Offline migration script generated!")


# ONLINE MODE - actual deployment

def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async support."""
    try:
        asyncio.run(run_migrations_online_async())
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

# MAIN ENTRY POINT

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
