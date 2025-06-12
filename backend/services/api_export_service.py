from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging
from models.database import database
from models.schemas import (
    ApiExportConfig, ApiExportJob, ApiExportLog, 
    ApiExportJobCreate, ApiExportJobResponse,
    ApiExportStatus, BusinessData
)
import httpx
import json
from bson import ObjectId
from config import settings

logger = logging.getLogger(__name__)

class ApiExportService:
    """Service for handling API export functionality"""
    
    def __init__(self):
        self.active_exports: Dict[str, bool] = {}
    
    def get_db(self):
        """Get database instance"""
        return database.client[settings.DATABASE_NAME]
    
    async def create_export_job(self, config: ApiExportJobCreate) -> ApiExportJobResponse:
        """Create a new API export job"""
        try:
            db = self.get_db()
            
            # Create job document
            job_data = {
                "_id": ObjectId(),
                "config": config.dict(),
                "status": ApiExportStatus.PENDING,
                "created_at": datetime.utcnow(),
                "started_at": None,
                "completed_at": None,
                "total_records": 0,
                "exported_records": 0,
                "failed_records": 0,
                "error_message": None,
                "logs": []
            }
            
            # Insert into database
            result = await db.api_export_jobs.insert_one(job_data)
            job_data["_id"] = str(result.inserted_id)
            
            logger.info(f"Created API export job: {job_data['_id']}")
            
            # Start export in background if auto_start is enabled
            if config.auto_start:
                asyncio.create_task(self._execute_export_job(str(result.inserted_id)))
            
            return ApiExportJobResponse(**job_data)
            
        except Exception as e:
            logger.error(f"Error creating export job: {str(e)}")
            raise
    
    async def get_export_jobs(self, limit: int = 50, offset: int = 0) -> List[ApiExportJobResponse]:
        """Get list of export jobs"""
        try:
            db = self.get_db()
            cursor = db.api_export_jobs.find().sort("created_at", -1).skip(offset).limit(limit)
            jobs = []
            
            async for job_doc in cursor:
                job_doc["_id"] = str(job_doc["_id"])
                jobs.append(ApiExportJobResponse(**job_doc))
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching export jobs: {str(e)}")
            raise
    
    async def get_export_job(self, job_id: str) -> Optional[ApiExportJobResponse]:
        """Get a specific export job"""
        try:
            db = self.get_db()
            job_doc = await db.api_export_jobs.find_one({"_id": ObjectId(job_id)})
            if job_doc:
                job_doc["_id"] = str(job_doc["_id"])
                return ApiExportJobResponse(**job_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching export job {job_id}: {str(e)}")
            raise
    
    async def start_export_job(self, job_id: str) -> bool:
        """Start an export job"""
        try:
            db = self.get_db()
            # Update job status to running
            result = await db.api_export_jobs.update_one(
                {"_id": ObjectId(job_id), "status": ApiExportStatus.PENDING},
                {
                    "$set": {
                        "status": ApiExportStatus.RUNNING,
                        "started_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Start export in background
                asyncio.create_task(self._execute_export_job(job_id))
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error starting export job {job_id}: {str(e)}")
            raise
    
    async def stop_export_job(self, job_id: str) -> bool:
        """Stop a running export job"""
        try:
            db = self.get_db()
            # Mark for stopping
            self.active_exports[job_id] = False
            
            # Update job status
            result = await db.api_export_jobs.update_one(
                {"_id": ObjectId(job_id), "status": ApiExportStatus.RUNNING},
                {
                    "$set": {
                        "status": ApiExportStatus.STOPPED,
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error stopping export job {job_id}: {str(e)}")
            raise
    
    async def delete_export_job(self, job_id: str) -> bool:
        """Delete an export job"""
        try:
            db = self.get_db()
            # Stop if running
            if job_id in self.active_exports:
                self.active_exports[job_id] = False
            
            # Delete from database
            result = await db.api_export_jobs.delete_one({"_id": ObjectId(job_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting export job {job_id}: {str(e)}")
            raise
    
    async def _execute_export_job(self, job_id: str):
        """Execute an export job in the background"""
        try:
            db = self.get_db()
            self.active_exports[job_id] = True
            
            # Get job details
            job_doc = await db.api_export_jobs.find_one({"_id": ObjectId(job_id)})
            if not job_doc:
                return
            
            config = job_doc["config"]
            
            # Build query filters
            query = {}
            if config.get("filters"):
                filters = config["filters"]
                if filters.get("city"):
                    query["city"] = {"$regex": filters["city"], "$options": "i"}
                if filters.get("business_type"):
                    query["business_type"] = {"$regex": filters["business_type"], "$options": "i"}
                if filters.get("date_range"):
                    date_range = filters["date_range"]
                    if date_range.get("start"):
                        query["created_at"] = {"$gte": datetime.fromisoformat(date_range["start"])}
                    if date_range.get("end"):
                        query.setdefault("created_at", {})["$lte"] = datetime.fromisoformat(date_range["end"])
            
            # Get total count
            total_count = await db.businesses.count_documents(query)
            await db.api_export_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {"total_records": total_count}}
            )
            
            # Export in batches
            batch_size = config.get("batch_size", 100)
            exported_count = 0
            failed_count = 0
            
            cursor = db.businesses.find(query).batch_size(batch_size)
            
            async for business_doc in cursor:
                # Check if job should continue
                if not self.active_exports.get(job_id, False):
                    break
                
                try:
                    # Prepare business data
                    business_data = self._prepare_business_data(business_doc, config.get("fields", []))
                    
                    # Send to API endpoint
                    success = await self._send_to_api(
                        config["endpoint_url"],
                        config.get("auth_token"),
                        business_data,
                        config.get("request_method", "POST")
                    )
                    
                    if success:
                        exported_count += 1
                    else:
                        failed_count += 1
                    
                    # Update progress
                    if (exported_count + failed_count) % 10 == 0:
                        await db.api_export_jobs.update_one(
                            {"_id": ObjectId(job_id)},
                            {
                                "$set": {
                                    "exported_records": exported_count,
                                    "failed_records": failed_count
                                }
                            }
                        )
                    
                    # Rate limiting
                    if config.get("rate_limit_delay", 0) > 0:
                        await asyncio.sleep(config["rate_limit_delay"])
                
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error exporting business record: {str(e)}")
            
            # Mark job as completed
            status = ApiExportStatus.COMPLETED if self.active_exports.get(job_id, False) else ApiExportStatus.STOPPED
            await db.api_export_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": status,
                        "completed_at": datetime.utcnow(),
                        "exported_records": exported_count,
                        "failed_records": failed_count
                    }
                }
            )
            
            # Clean up
            if job_id in self.active_exports:
                del self.active_exports[job_id]
            
            logger.info(f"Export job {job_id} completed: {exported_count} exported, {failed_count} failed")
            
        except Exception as e:
            db = self.get_db()
            # Mark job as failed
            await db.api_export_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": ApiExportStatus.FAILED,
                        "completed_at": datetime.utcnow(),
                        "error_message": str(e)
                    }
                }
            )
            
            # Clean up
            if job_id in self.active_exports:
                del self.active_exports[job_id]
            
            logger.error(f"Export job {job_id} failed: {str(e)}")
    
    def _prepare_business_data(self, business_doc: Dict[str, Any], selected_fields: List[str]) -> Dict[str, Any]:
        """Prepare business data for export"""
        # Convert ObjectId to string
        if "_id" in business_doc:
            business_doc["_id"] = str(business_doc["_id"])
        
        # Filter fields if specified
        if selected_fields:
            filtered_data = {}
            for field in selected_fields:
                if field in business_doc:
                    filtered_data[field] = business_doc[field]
            return filtered_data
        
        return business_doc
    
    async def _send_to_api(self, endpoint_url: str, auth_token: Optional[str], data: Dict[str, Any], method: str = "POST") -> bool:
        """Send data to external API endpoint"""
        try:
            headers = {"Content-Type": "application/json"}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "POST":
                    response = await client.post(endpoint_url, json=data, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(endpoint_url, json=data, headers=headers)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return False
                
                # Consider 2xx status codes as success
                return 200 <= response.status_code < 300
                
        except Exception as e:
            logger.error(f"Error sending data to API: {str(e)}")
            return False

# Global service instance
api_export_service = ApiExportService()