import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database - supports both MongoDB URI and individual components
    MONGODB_URI: str = os.getenv("MONGODB_URI", os.getenv("DATABASE_URL", "mongodb://localhost:27017/business_scraper"))
    MONGODB_URL: str = "mongodb://localhost:27017"  # Deprecated, use MONGODB_URI
    DATABASE_NAME: str = "business_scraper"
    
    # Redis for task queue
    REDIS_URL: str = "redis://localhost:6379"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Scraping
    DEFAULT_DOMAINS: List[str] = [
        "https://www.yello.ae",
    ]
    
    # Concurrency
    MAX_CONCURRENT_SCRAPERS: int = 5
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_DELAY: float = 1.0
    
    # Browser settings
    HEADLESS_BROWSER: bool = True
    BROWSER_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env file

settings = Settings()
