from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from models.schemas import ApiExportJobCreate, ApiExportJobResponse
from services.api_export_service import api_export_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api-export", tags=["API Export"])

@router.post("/jobs", response_model=ApiExportJobResponse)
async def create_export_job(job_data: ApiExportJobCreate):
    """Create a new API export job"""
    try:
        job = await api_export_service.create_export_job(job_data)
        return job
    except Exception as e:
        logger.error(f"Error creating export job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create export job: {str(e)}")

@router.get("/jobs", response_model=List[ApiExportJobResponse])
async def list_export_jobs(skip: int = 0, limit: int = 50):
    """List API export jobs"""
    try:
        jobs = await api_export_service.get_export_jobs(limit=limit, offset=skip)
        return jobs
    except Exception as e:
        logger.error(f"Error listing export jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list export jobs: {str(e)}")

@router.get("/jobs/{job_id}", response_model=ApiExportJobResponse)
async def get_export_job(job_id: str):
    """Get a specific export job"""
    try:
        job = await api_export_service.get_export_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get export job: {str(e)}")

@router.post("/jobs/{job_id}/start")
async def start_export_job(job_id: str):
    """Start an export job"""
    try:
        success = await api_export_service.start_export_job(job_id)
        if not success:
            raise HTTPException(status_code=400, detail="Unable to start job (may already be running or not found)")
        return {"message": "Export job started successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting export job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start export job: {str(e)}")

@router.post("/jobs/{job_id}/stop")
async def stop_export_job(job_id: str):
    """Stop an export job"""
    try:
        success = await api_export_service.stop_export_job(job_id)
        if not success:
            raise HTTPException(status_code=400, detail="Unable to stop job (may not be running or not found)")
        return {"message": "Export job stopped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping export job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop export job: {str(e)}")

@router.delete("/jobs/{job_id}")
async def delete_export_job(job_id: str):
    """Delete an export job"""
    try:
        success = await api_export_service.delete_export_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Export job not found")
        return {"message": "Export job deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete export job: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for API export service"""
    return {"status": "healthy", "service": "api-export"}
