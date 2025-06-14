# PostgreSQL Database Configuration
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
import asyncpg

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/business_scraper")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Async database for FastAPI
database = Database(DATABASE_URL)

# Business data table definition
metadata = MetaData()

businesses_table = Table(
    "businesses",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, index=True),
    Column("description", Text),
    Column("address", String),
    Column("phone", String),
    Column("email", String),
    Column("website", String),
    Column("category", String, index=True),
    Column("city", String, index=True),
    Column("state", String, index=True),
    Column("country", String, index=True),
    Column("source_url", String),
    Column("scraped_at", DateTime),
    Column("is_active", Boolean, default=True),
    Column("metadata", JSON),
)

# Jobs table for scraping status
jobs_table = Table(
    "scraping_jobs",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("job_id", String, unique=True, index=True),
    Column("status", String, index=True),  # pending, running, completed, failed
    Column("domain", String),
    Column("start_time", DateTime),
    Column("end_time", DateTime),
    Column("total_businesses", Integer, default=0),
    Column("scraped_businesses", Integer, default=0),
    Column("error_message", Text),
    Column("metadata", JSON),
)

async def create_tables():
    """Create database tables"""
    metadata.create_all(bind=engine)

async def connect_db():
    """Connect to database"""
    await database.connect()

async def disconnect_db():
    """Disconnect from database"""
    await database.disconnect()

# Database operations
class BusinessDAO:
    """Data Access Object for businesses"""
    
    @staticmethod
    async def create_business(business_data: dict):
        """Insert a new business"""
        query = businesses_table.insert().values(**business_data)
        return await database.execute(query)
    
    @staticmethod
    async def get_businesses(limit: int = 100, offset: int = 0):
        """Get businesses with pagination"""
        query = businesses_table.select().limit(limit).offset(offset)
        return await database.fetch_all(query)
    
    @staticmethod
    async def get_business_count():
        """Get total business count"""
        query = "SELECT COUNT(*) FROM businesses"
        result = await database.fetch_one(query)
        return result[0] if result else 0
    
    @staticmethod
    async def search_businesses(search_term: str, limit: int = 100):
        """Search businesses by name or description"""
        query = businesses_table.select().where(
            businesses_table.c.name.ilike(f"%{search_term}%") |
            businesses_table.c.description.ilike(f"%{search_term}%")
        ).limit(limit)
        return await database.fetch_all(query)

class JobDAO:
    """Data Access Object for scraping jobs"""
    
    @staticmethod
    async def create_job(job_data: dict):
        """Create a new scraping job"""
        query = jobs_table.insert().values(**job_data)
        return await database.execute(query)
    
    @staticmethod
    async def update_job(job_id: str, updates: dict):
        """Update a scraping job"""
        query = jobs_table.update().where(
            jobs_table.c.job_id == job_id
        ).values(**updates)
        return await database.execute(query)
    
    @staticmethod
    async def get_job(job_id: str):
        """Get a specific job"""
        query = jobs_table.select().where(jobs_table.c.job_id == job_id)
        return await database.fetch_one(query)
    
    @staticmethod
    async def get_jobs(limit: int = 50):
        """Get recent jobs"""
        query = jobs_table.select().order_by(jobs_table.c.start_time.desc()).limit(limit)
        return await database.fetch_all(query)
