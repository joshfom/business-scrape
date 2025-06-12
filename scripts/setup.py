#!/usr/bin/env python3
"""
Setup script for Business Scraper
"""

import asyncio
import sys
import os
import subprocess
import logging

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.models.database import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_database():
    """Initialize database and create indexes"""
    try:
        logger.info("Connecting to database...")
        await database.connect_db()
        logger.info("Database setup completed successfully")
        await database.close_db()
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    try:
        logger.info("Installing Python dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", 
            os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
        ], check=True)
        logger.info("Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Python dependencies: {e}")
        return False

def install_frontend_dependencies():
    """Install frontend dependencies"""
    try:
        frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
        logger.info("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        logger.info("Frontend dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install frontend dependencies: {e}")
        return False

def create_env_file():
    """Create .env file with default settings"""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    
    if os.path.exists(env_path):
        logger.info(".env file already exists")
        return True
    
    try:
        logger.info("Creating .env file...")
        with open(env_path, 'w') as f:
            f.write("""# Business Scraper Configuration

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=business_scraper

# Redis (for task queue)
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Scraping Configuration
MAX_CONCURRENT_SCRAPERS=5
MAX_CONCURRENT_REQUESTS=10
REQUEST_DELAY=1.0

# Browser Configuration
HEADLESS_BROWSER=true
BROWSER_TIMEOUT=30
""")
        logger.info(".env file created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create .env file: {e}")
        return False

async def main():
    """Main setup function"""
    logger.info("Starting Business Scraper setup...")
    
    # Create .env file
    if not create_env_file():
        return 1
    
    # Install Python dependencies
    if not install_python_dependencies():
        return 1
    
    # Install frontend dependencies
    if not install_frontend_dependencies():
        return 1
    
    # Setup database
    if not await setup_database():
        return 1
    
    logger.info("Setup completed successfully!")
    logger.info("To start the application:")
    logger.info("1. Start MongoDB: mongod")
    logger.info("2. Start the backend: cd backend && python -m uvicorn main:app --reload")
    logger.info("3. Start the frontend: cd frontend && npm start")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
