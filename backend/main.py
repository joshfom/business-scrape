from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import scraping, businesses, api_export_simple
from models.database import database
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Business Scraper API",
    description="API for managing business scraping jobs and data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3020", "http://127.0.0.1:3020"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scraping.router, prefix="/api")
app.include_router(businesses.router, prefix="/api")
app.include_router(api_export_simple.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await database.connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await database.close_db()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Business Scraper API is running"}

@app.get("/health")
async def health_check():
    """Simple health check endpoint that doesn't depend on database"""
    return {"status": "healthy", "service": "business-scraper-api", "timestamp": "2024-06-14"}

@app.get("/health/full")
async def full_health_check():
    """Full health check including database connectivity"""
    try:
        # Test database connection
        await database.client.admin.command('ping')
        return {
            "status": "healthy", 
            "service": "business-scraper-api",
            "database": "connected",
            "timestamp": "2024-06-14"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "business-scraper-api", 
            "database": "disconnected",
            "error": str(e),
            "timestamp": "2024-06-14"
        }
