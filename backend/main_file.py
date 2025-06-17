from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime

# Import the file-based data router
from api.endpoints.file_data import router as file_data_router

# Create FastAPI app
app = FastAPI(
    title="Business Scraper API",
    description="File-based Business Data API for testing and development",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(file_data_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "data_source": "file-based"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Business Scraper API - File-based Data",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "businesses": "/api/file/businesses",
            "stats": "/api/file/stats",
            "domains": "/api/file/domains",
            "cities": "/api/file/cities",
            "categories": "/api/file/categories"
        }
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main_file:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
