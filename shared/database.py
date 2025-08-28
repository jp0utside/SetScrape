import os
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData, text
from contextlib import asynccontextmanager
from pathlib import Path

# Import SQLAlchemy models
from .database_models import Base

# Database configuration - SQLite for local development
# Use environment variable or default to data directory
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/music_player.db")

# Ensure data directory exists
data_dir = Path("./data")
data_dir.mkdir(exist_ok=True)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
# Base = declarative_base() # This line is now redundant as Base is imported directly

# Metadata for migrations
metadata = MetaData()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables using SQLAlchemy models"""
    async with engine.begin() as conn:
        try:
            # Create all tables using SQLAlchemy models
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database initialized successfully using SQLAlchemy models")
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            raise

async def close_db():
    """Close database connections"""
    await engine.dispose()

# Database utilities
class DatabaseUtils:
    """Utility class for common database operations"""
    
    @staticmethod
    async def check_table_exists(table_name: str) -> bool:
        """Check if a table exists in the database"""
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                {"table_name": table_name}
            )
            return result.scalar() is not None
    
    @staticmethod
    async def get_table_count(table_name: str) -> int:
        """Get the number of rows in a table"""
        async with engine.begin() as conn:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    
    @staticmethod
    async def get_table_info(table_name: str) -> list:
        """Get table schema information"""
        async with engine.begin() as conn:
            result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
            return result.fetchall()

# Health check
async def check_db_health() -> bool:
    """Check database health"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"    ❌ Health check error: {e}")
        return False

# Connection pool monitoring
async def get_db_stats() -> dict:
    """Get database statistics"""
    stats = {}
    try:
        # Get list of tables
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in result.fetchall()]
        
        # Get row counts for each table
        for table in tables:
            count = await DatabaseUtils.get_table_count(table)
            stats[table] = count
            
    except Exception as e:
        stats["error"] = str(e)
    
    return stats
