from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Create database connection"""
        # Use MONGODB_URI which supports full connection strings including database name
        mongodb_uri = settings.MONGODB_URI
        cls.client = AsyncIOMotorClient(mongodb_uri)
        
        # Test connection
        try:
            await cls.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB at {mongodb_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB at {mongodb_uri}: {e}")
            raise
            
        # Create indexes
        await cls._create_indexes()
        
    @classmethod
    async def close_db(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    async def _create_indexes(cls):
        """Create database indexes for performance"""
        db = cls.get_database()
        
        # Business data indexes
        businesses = db.businesses
        await businesses.create_index([("domain", ASCENDING), ("page_url", ASCENDING)], unique=True)
        await businesses.create_index([("city", ASCENDING), ("country", ASCENDING)])
        await businesses.create_index([("category", ASCENDING)])
        await businesses.create_index([("scraped_at", DESCENDING)])
        await businesses.create_index([("exported_at", ASCENDING)])  # New index for export tracking
        await businesses.create_index([("export_mode", ASCENDING)])  # New index for export mode
        
        # Job indexes
        jobs = db.scraping_jobs
        await jobs.create_index([("status", ASCENDING)])
        await jobs.create_index([("created_at", DESCENDING)])
        
        # Progress indexes
        progress = db.scraping_progress
        await progress.create_index([("job_id", ASCENDING), ("timestamp", DESCENDING)])
        
        logger.info("Database indexes created successfully")

    @classmethod
    def get_database(cls):
        """Get database instance"""
        # Extract database name from URI or use default
        if '/' in settings.MONGODB_URI and settings.MONGODB_URI.count('/') >= 3:
            # Extract database name from URI like mongodb://host:port/dbname
            db_name = settings.MONGODB_URI.split('/')[-1].split('?')[0]
            if db_name:
                return cls.client[db_name]
        # Fallback to configured database name
        return cls.client[settings.DATABASE_NAME]

# Global database instance
database = Database()
