from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from pydantic import BaseModel
from models.database import database
from models.schemas import (
    ApiExportConfig, ApiExportConfigCreate, ApiExportConfigUpdate,
    ApiExportJob, ApiExportJobCreate, ApiExportJobResponse, ApiExportLog, ApiExportStats
)
from services.api_export_service import api_export_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api-export", tags=["API Export"])

# Dependency to get the API export service
def get_api_export_service():
    return api_export_service

@router.get("/configs", response_model=List[ApiExportConfig])
async def list_export_configs(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
):
    """List all API export configurations"""
    try:
        db = database.get_database()
        query = {}
        if active_only:
            query["is_active"] = True
            
        cursor = db.api_export_configs.find(query).skip(skip).limit(limit).sort("created_at", -1)
        configs = []
        
        async for config in cursor:
            config["_id"] = str(config["_id"])
            configs.append(ApiExportConfig(**config))
            
        return configs
    except Exception as e:
        logger.error(f"Error listing export configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch export configurations")

@router.post("/configs", response_model=ApiExportConfig)
async def create_export_config(config: ApiExportConfigCreate):
    """Create a new API export configuration"""
    try:
        db = database.get_database()
        
        # Check if name already exists
        existing = await db.api_export_configs.find_one({"name": config.name})
        if existing:
            raise HTTPException(status_code=400, detail="Configuration name already exists")
        
        config_dict = config.dict()
        config_dict["created_at"] = datetime.utcnow()
        config_dict["updated_at"] = datetime.utcnow()
        
        result = await db.api_export_configs.insert_one(config_dict)
        config_dict["_id"] = str(result.inserted_id)
        
        logger.info(f"Created export config: {config.name}")
        return ApiExportConfig(**config_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating export config: {e}")
        raise HTTPException(status_code=500, detail="Failed to create export configuration")

@router.get("/configs/{config_id}", response_model=ApiExportConfig)
async def get_export_config(config_id: str):
    """Get a specific API export configuration"""
    try:
        db = database.get_database()
        config = await db.api_export_configs.find_one({"_id": ObjectId(config_id)})
        
        if not config:
            raise HTTPException(status_code=404, detail="Export configuration not found")
        
        config["_id"] = str(config["_id"])
        return ApiExportConfig(**config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching export config {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch export configuration")

@router.put("/configs/{config_id}", response_model=ApiExportConfig)
async def update_export_config(config_id: str, update: ApiExportConfigUpdate):
    """Update an API export configuration"""
    try:
        db = database.get_database()
        
        # Check if config exists
        existing = await db.api_export_configs.find_one({"_id": ObjectId(config_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Export configuration not found")
        
        # Prepare update data
        update_data = {k: v for k, v in update.dict().items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            await db.api_export_configs.update_one(
                {"_id": ObjectId(config_id)},
                {"$set": update_data}
            )
        
        # Return updated config
        updated_config = await db.api_export_configs.find_one({"_id": ObjectId(config_id)})
        updated_config["_id"] = str(updated_config["_id"])
        
        logger.info(f"Updated export config: {config_id}")
        return ApiExportConfig(**updated_config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating export config {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update export configuration")

@router.delete("/configs/{config_id}")
async def delete_export_config(config_id: str):
    """Delete an API export configuration"""
    try:
        db = database.get_database()
        
        # Check if config exists
        existing = await db.api_export_configs.find_one({"_id": ObjectId(config_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Export configuration not found")
        
        # Check if there are any running jobs for this config
        running_jobs = await db.api_export_jobs.find_one({
            "config_id": config_id,
            "status": {"$in": ["pending", "running"]}
        })
        if running_jobs:
            raise HTTPException(status_code=400, detail="Cannot delete configuration with active jobs")
        
        await db.api_export_configs.delete_one({"_id": ObjectId(config_id)})
        
        logger.info(f"Deleted export config: {config_id}")
        return {"message": "Configuration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export config {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete export configuration")

@router.get("/jobs", response_model=List[ApiExportJob])
async def list_export_jobs(
    skip: int = 0,
    limit: int = 100,
    config_id: Optional[str] = None,
    status: Optional[str] = None
):
    """List API export jobs"""
    try:
        db = database.get_database()
        query = {}
        
        if config_id:
            query["config_id"] = config_id
        if status:
            query["status"] = status
            
        cursor = db.api_export_jobs.find(query).skip(skip).limit(limit).sort("created_at", -1)
        jobs = []
        
        async for job in cursor:
            job["_id"] = str(job["_id"])
            jobs.append(ApiExportJob(**job))
            
        return jobs
    except Exception as e:
        logger.error(f"Error listing export jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch export jobs")

@router.post("/jobs", response_model=ApiExportJobResponse)
async def create_export_job(
    job_data: ApiExportJobCreate,
    background_tasks: BackgroundTasks,
    service = Depends(get_api_export_service)
):
    """Create and start a new API export job"""
    try:
        db = database.get_database()
        
        # Verify config exists and is active
        config = await db.api_export_configs.find_one({
            "_id": ObjectId(job_data.config_id),
            "is_active": True
        })
        if not config:
            raise HTTPException(status_code=404, detail="Active export configuration not found")
        
        # Create job record
        job_dict = job_data.dict()
        job_dict["created_at"] = datetime.utcnow()
        
        result = await db.api_export_jobs.insert_one(job_dict)
        job_id = str(result.inserted_id)
        job_dict["_id"] = job_id
        
        # Start export job in background
        background_tasks.add_task(service.run_export_job, job_id)
        
        logger.info(f"Created and started export job: {job_id}")
        return ApiExportJob(**job_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating export job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create export job")

@router.get("/jobs/{job_id}", response_model=ApiExportJob)
async def get_export_job(job_id: str):
    """Get a specific export job"""
    try:
        db = database.get_database()
        job = await db.api_export_jobs.find_one({"_id": ObjectId(job_id)})
        
        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")
        
        job["_id"] = str(job["_id"])
        return ApiExportJob(**job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching export job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch export job")

@router.post("/jobs/{job_id}/cancel")
async def cancel_export_job(job_id: str):
    """Cancel a running export job"""
    try:
        db = database.get_database()
        
        # Check if job exists and can be cancelled
        job = await db.api_export_jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")
        
        if job["status"] not in ["pending", "running"]:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled")
        
        # Update job status
        await db.api_export_jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "cancelled", "end_time": datetime.utcnow()}}
        )
        
        logger.info(f"Cancelled export job: {job_id}")
        return {"message": "Job cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling export job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel export job")

@router.get("/jobs/{job_id}/logs", response_model=List[ApiExportLog])
async def get_job_logs(job_id: str, skip: int = 0, limit: int = 100):
    """Get logs for a specific export job"""
    try:
        db = database.get_database()
        
        cursor = db.api_export_logs.find({"job_id": job_id}).skip(skip).limit(limit).sort("timestamp", -1)
        logs = []
        
        async for log in cursor:
            log["_id"] = str(log["_id"])
            logs.append(ApiExportLog(**log))
            
        return logs
    except Exception as e:
        logger.error(f"Error fetching logs for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job logs")

@router.get("/stats", response_model=ApiExportStats)
async def get_export_stats():
    """Get API export statistics"""
    try:
        db = database.get_database()
        
        # Get basic counts with fallbacks for new installations
        total_configs = await db.api_export_configs.count_documents({})
        active_configs = await db.api_export_configs.count_documents({"is_active": True})
        total_jobs = await db.api_export_jobs.count_documents({})
        
        # Jobs created today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        jobs_today = await db.api_export_jobs.count_documents({"created_at": {"$gte": today_start}})
        
        # Total exported records (with fallback for new installations)
        try:
            pipeline = [
                {"$group": {"_id": None, "total": {"$sum": "$successful_records"}}}
            ]
            result = await db.api_export_jobs.aggregate(pipeline).to_list(1)
            total_exported_records = result[0]["total"] if result else 0
        except:
            total_exported_records = 0
        
        # Recent jobs
        recent_jobs = []
        try:
            cursor = db.api_export_jobs.find({}).sort("created_at", -1).limit(5)
            async for job in cursor:
                job["_id"] = str(job["_id"])
                recent_jobs.append(ApiExportJob(**job))
        except:
            pass  # Collection might not exist yet
        
        return ApiExportStats(
            total_configs=total_configs,
            active_configs=active_configs,
            total_jobs=total_jobs,
            jobs_today=jobs_today,
            total_exported_records=total_exported_records,
            recent_jobs=recent_jobs
        )
    except Exception as e:
        logger.error(f"Error fetching export stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch export statistics")

class TestConnectionRequest(BaseModel):
    endpoint_url: str
    bearer_token: str

@router.post("/test-connection")
async def test_api_connection(
    endpoint_url: str,
    bearer_token: str,
    service = Depends(get_api_export_service)
):
    """Test connection to an API endpoint"""
    try:
        result = await service.test_api_connection(endpoint_url, bearer_token)
        return result
    except Exception as e:
        logger.error(f"Error testing API connection: {e}")
        raise HTTPException(status_code=500, detail="Failed to test API connection")

# Network Resilience and Job Control Endpoints for API Export

@router.post("/jobs/pause-all")
async def pause_all_export_jobs():
    """Pause all running API export jobs"""
    try:
        db = database.get_database()
        
        # Update all running export jobs to cancelled (API exports don't have pause state)
        result = await db.api_export_jobs.update_many(
            {"status": "running"},
            {"$set": {"status": "cancelled", "end_time": datetime.utcnow(), "error_message": "Manually paused - network interruption"}}
        )
        
        logger.info(f"Paused {result.modified_count} running API export jobs")
        return {
            "message": f"Successfully paused {result.modified_count} running API export jobs",
            "paused_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Error pausing all API export jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause API export jobs")

@router.post("/jobs/resume-network-paused")
async def resume_network_paused_export_jobs():
    """Create new jobs for previously network-paused API export jobs"""
    try:
        db = database.get_database()
        
        # Find jobs that were cancelled due to network issues
        cancelled_jobs = await db.api_export_jobs.find({
            "status": "cancelled",
            "error_message": "Manually paused - network interruption"
        }).to_list(None)
        
        resumed_count = 0
        for job in cancelled_jobs:
            # Create a new job with the same configuration
            new_job = {
                "config_id": job["config_id"],
                "filters_applied": job.get("filters_applied", {}),
                "created_at": datetime.utcnow(),
                "status": "pending"
            }
            
            await db.api_export_jobs.insert_one(new_job)
            resumed_count += 1
            
            # Mark the old job as superseded
            await db.api_export_jobs.update_one(
                {"_id": job["_id"]},
                {"$set": {"error_message": "Superseded by new job after network recovery"}}
            )
        
        logger.info(f"Created {resumed_count} new API export jobs to replace network-paused ones")
        return {
            "message": f"Successfully created {resumed_count} new API export jobs",
            "resumed_count": resumed_count
        }
        
    except Exception as e:
        logger.error(f"Error resuming network-paused API export jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume network-paused API export jobs")
