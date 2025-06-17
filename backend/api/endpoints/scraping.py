from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from models.schemas import ScrapingJobCreate, ScrapingJob, DashboardStats
from services.scraping_service import scraping_service
from services.job_seeding_service import job_seeding_service
from models.database import database
from datetime import datetime, timedelta
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraping", tags=["scraping"])

@router.post("/jobs", response_model=dict)
async def create_scraping_job(job_data: ScrapingJobCreate):
    """Create a new scraping job"""
    try:
        # Validate: only one domain per job
        if len(job_data.domains) != 1:
            raise HTTPException(status_code=400, detail="Each job must target exactly one domain")
        
        domain = job_data.domains[0]
        
        # Helper function to normalize domain names for comparison
        def normalize_domain(domain_str: str) -> str:
            # Remove protocol and www prefix, convert to lowercase
            normalized = domain_str.replace("https://", "").replace("http://", "").replace("www.", "").lower()
            # Treat yellowpages.ae as yello.ae for consistency
            return normalized.replace("yellowpages.", "yello.")
        
        normalized_domain = normalize_domain(domain)
        
        # Check if domain is already in use by active jobs
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        active_jobs = await jobs_collection.find({
            "status": {"$in": ["pending", "running", "paused"]}
        }).to_list(None)
        
        # Check for domain conflicts using normalized comparison
        for active_job in active_jobs:
            for active_domain in active_job.get("domains", []):
                if normalize_domain(active_domain) == normalized_domain:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Domain {domain} is already being processed by another job (conflicts with {active_domain})"
                    )
        
        job_id = await scraping_service.create_job(job_data.dict())
        return {"job_id": job_id, "message": "Job created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/start")
async def start_scraping_job(job_id: str):
    """Start a scraping job"""
    try:
        success = await scraping_service.start_job(job_id)
        if success:
            return {"message": "Job started successfully"}
        else:
            raise HTTPException(status_code=400, detail="Job is already running or not found")
    except Exception as e:
        logger.error(f"Error starting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/force-start")
async def force_start_scraping_job(job_id: str):
    """Force start a scraping job, stopping any existing instance first"""
    try:
        success = await scraping_service.force_start_job(job_id)
        if success:
            return {"message": "Job force started successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to force start job")
    except Exception as e:
        logger.error(f"Error force starting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/pause")
async def pause_scraping_job(job_id: str):
    """Pause a running job"""
    try:
        success = await scraping_service.pause_job(job_id)
        if success:
            return {"message": "Job paused successfully"}
        else:
            raise HTTPException(status_code=400, detail="Job not found or not running")
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/resume")
async def resume_scraping_job(job_id: str):
    """Resume a paused job"""
    try:
        success = await scraping_service.resume_job(job_id)
        if success:
            return {"message": "Job resumed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Job not found or cannot be resumed")
    except Exception as e:
        logger.error(f"Error resuming job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/cancel")
async def cancel_scraping_job(job_id: str):
    """Cancel a job"""
    try:
        success = await scraping_service.cancel_job(job_id)
        if success:
            return {"message": "Job cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Job not found")
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get job status and progress"""
    try:
        status = await scraping_service.get_job_status(job_id)
        if status:
            # Convert ObjectId to string for JSON serialization
            if '_id' in status:
                status['_id'] = str(status['_id'])
            return status
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs", response_model=List[dict])
async def list_scraping_jobs(skip: int = 0, limit: int = 20):
    """List all scraping jobs"""
    try:
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        cursor = jobs_collection.find().sort("created_at", -1).skip(skip).limit(limit)
        jobs = []
        async for job in cursor:
            # Convert ObjectId to string for JSON serialization
            if '_id' in job:
                job['_id'] = str(job['_id'])
            jobs.append(job)
        
        return jobs
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        businesses_collection = db.businesses
        
        # Count total jobs
        total_jobs = await jobs_collection.count_documents({})
        
        # Count active jobs
        active_jobs = await jobs_collection.count_documents({
            "status": {"$in": ["running", "pending"]}
        })
        
        # Count total businesses
        total_businesses = await businesses_collection.count_documents({})
        
        # Count businesses scraped today - handle missing scraped_at field gracefully
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            businesses_today = await businesses_collection.count_documents({
                "scraped_at": {"$gte": today}
            })
        except Exception:
            # If scraped_at field doesn't exist, fallback to 0
            businesses_today = 0
        
        # Get last scrape time - handle missing field gracefully
        try:
            last_business = await businesses_collection.find_one(
                {"scraped_at": {"$exists": True}}, 
                sort=[("scraped_at", -1)]
            )
            last_scrape = last_business["scraped_at"] if last_business else None
        except Exception:
            # If scraped_at field doesn't exist, fallback to None
            last_scrape = None
        
        # Count configured domains
        pipeline = [
            {"$group": {"_id": "$domain"}},
            {"$count": "domains"}
        ]
        domain_result = await businesses_collection.aggregate(pipeline).to_list(1)
        domains_configured = domain_result[0]["domains"] if domain_result else 0
        
        return DashboardStats(
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            total_businesses=total_businesses,
            businesses_today=businesses_today,
            domains_configured=domains_configured,
            last_scrape=last_scrape
        )
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/details")
async def get_job_details(job_id: str):
    """Get detailed job information including scraped data summary"""
    try:
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        businesses_collection = db.businesses
        
        # Get job details
        job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Convert ObjectId to string
        job['_id'] = str(job['_id'])
        
        # Get business data for this job
        job_domains = job.get("domains", [])
        filter_query = {"domain": {"$in": job_domains}}
        
        # Get business counts by city
        city_stats_pipeline = [
            {"$match": filter_query},
            {
                "$group": {
                    "_id": "$city",
                    "total": {"$sum": 1},
                    "exported": {
                        "$sum": {
                            "$cond": [{"$ne": ["$exported_at", None]}, 1, 0]
                        }
                    }
                }
            },
            {"$sort": {"total": -1}}
        ]
        city_stats = await businesses_collection.aggregate(city_stats_pipeline).to_list(None)
        
        # Get latest scraped businesses (sample)
        latest_businesses = []
        async for business in businesses_collection.find(filter_query).sort("scraped_at", -1).limit(10):
            business["_id"] = str(business["_id"])
            latest_businesses.append({
                "id": business["_id"],
                "name": business.get("name", ""),
                "city": business.get("city", ""),
                "category": business.get("category", ""),
                "scraped_at": business.get("scraped_at"),
                "exported_at": business.get("exported_at"),
                "export_mode": business.get("export_mode")
            })
        
        # Add computed fields to job
        job["city_stats"] = [
            {
                "city": stat["_id"],
                "total_businesses": stat["total"],
                "exported_businesses": stat["exported"]
            }
            for stat in city_stats
        ]
        job["latest_businesses"] = latest_businesses
        job["total_scraped_businesses"] = sum(stat["total"] for stat in city_stats)
        job["total_exported_businesses"] = sum(stat["exported"] for stat in city_stats)
        
        return job
        
    except Exception as e:
        logger.error(f"Error getting job details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-domains")
async def get_available_domains():
    """Get list of available domains that don't have active jobs"""
    try:
        # Define the complete list of domains in backend
        ALL_DOMAINS = [
            # Asia
            {'domain': 'https://armeniayp.com', 'country': 'Armenia'},
            {'domain': 'https://azerbaijanyp.com', 'country': 'Azerbaijan'},
            {'domain': 'https://bangladeshyp.com', 'country': 'Bangladesh'},
            {'domain': 'https://bruneiyp.com', 'country': 'Brunei'},
            {'domain': 'https://cambodiayp.com', 'country': 'Cambodia'},
            {'domain': 'https://chinayello.com', 'country': 'China'},
            {'domain': 'https://georgiayp.com', 'country': 'Georgia'},
            {'domain': 'https://yelo.hk', 'country': 'Hong Kong'},
            {'domain': 'https://indiayp.com', 'country': 'India'},
            {'domain': 'https://indonesiayp.com', 'country': 'Indonesia'},
            {'domain': 'https://japanyp.com', 'country': 'Japan'},
            {'domain': 'https://kazakhstanyp.com', 'country': 'Kazakhstan'},
            {'domain': 'https://kyrgyzstanyp.com', 'country': 'Kyrgyzstan'},
            {'domain': 'https://laosyp.com', 'country': 'Laos'},
            {'domain': 'https://malaysiayp.com', 'country': 'Malaysia'},
            {'domain': 'https://maldivesyp.com', 'country': 'Maldives'},
            {'domain': 'https://mongoliayp.com', 'country': 'Mongolia'},
            {'domain': 'https://myanmaryp.com', 'country': 'Myanmar'},
            {'domain': 'https://nepalyp.com', 'country': 'Nepal'},
            {'domain': 'https://businesslist.pk', 'country': 'Pakistan'},
            {'domain': 'https://philippinesyp.com', 'country': 'Philippines'},
            {'domain': 'https://singaporeyp.com', 'country': 'Singapore'},
            {'domain': 'https://southkoreayp.com', 'country': 'South Korea'},
            {'domain': 'https://srilankayp.com', 'country': 'Sri Lanka'},
            {'domain': 'https://taiwanyp.com', 'country': 'Taiwan'},
            {'domain': 'https://tajikistanyp.com', 'country': 'Tajikistan'},
            {'domain': 'https://thailandyp.com', 'country': 'Thailand'},
            {'domain': 'https://turkmenistanyp.com', 'country': 'Turkmenistan'},
            {'domain': 'https://uzbekistanyp.com', 'country': 'Uzbekistan'},
            {'domain': 'https://vietnamyp.com', 'country': 'Vietnam'},
            
            # Middle East
            {'domain': 'https://www.yello.ae', 'country': 'UAE'},
            {'domain': 'https://www.yello.sa', 'country': 'Saudi Arabia'},
            {'domain': 'https://www.yello.qa', 'country': 'Qatar'},
            {'domain': 'https://www.yello.om', 'country': 'Oman'},
            {'domain': 'https://www.yello.kw', 'country': 'Kuwait'},
            {'domain': 'https://www.yello.bh', 'country': 'Bahrain'},
            {'domain': 'https://bahrainyellow.com', 'country': 'Bahrain'},
            {'domain': 'https://iraqyp.com', 'country': 'Iraq'},
            {'domain': 'https://jordanyp.com', 'country': 'Jordan'},
            {'domain': 'https://lebanonyp.com', 'country': 'Lebanon'},
            
            # Africa  
            {'domain': 'https://algeriayp.com', 'country': 'Algeria'},
            {'domain': 'https://angolayp.com', 'country': 'Angola'},
            {'domain': 'https://egyptyp.com', 'country': 'Egypt'},
            {'domain': 'https://ethiopiayp.com', 'country': 'Ethiopia'},
            {'domain': 'https://ghanayp.com', 'country': 'Ghana'},
            {'domain': 'https://kenyayp.com', 'country': 'Kenya'},
            {'domain': 'https://libyayp.com', 'country': 'Libya'},
            {'domain': 'https://moroccoyp.com', 'country': 'Morocco'},
            {'domain': 'https://www.businesslist.com.ng/', 'country': 'Nigeria'},
            {'domain': 'https://southafricayp.com', 'country': 'South Africa'},
            {'domain': 'https://sudanyp.com', 'country': 'Sudan'},
            {'domain': 'https://tunisiayp.com', 'country': 'Tunisia'},
            {'domain': 'https://ugandayp.com', 'country': 'Uganda'},
        ]
        
        # Helper function to normalize domain names for comparison
        def normalize_domain(domain_str: str) -> str:
            normalized = domain_str.replace("https://", "").replace("http://", "").replace("www.", "").lower()
            return normalized.replace("yellowpages.", "yello.")
        
        # Get active job domains
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        active_jobs = await jobs_collection.find({
            "status": {"$in": ["pending", "running", "paused"]}
        }).to_list(None)
        
        # Collect normalized active domains
        active_domains = set()
        for job in active_jobs:
            for domain in job.get("domains", []):
                active_domains.add(normalize_domain(domain))
        
        # Filter out domains that are already in use
        available_domains = []
        for domain_info in ALL_DOMAINS:
            domain = domain_info['domain']
            if normalize_domain(domain) not in active_domains:
                available_domains.append(domain_info)
        
        return {
            "available_domains": available_domains,
            "total_domains": len(ALL_DOMAINS),
            "available_count": len(available_domains),
            "active_count": len(active_domains)
        }
        
    except Exception as e:
        logger.error(f"Error getting available domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Network Resilience and Job Control Endpoints

@router.post("/jobs/pause-all")
async def pause_all_jobs():
    """Pause all running jobs"""
    try:
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        # Update all running jobs to paused
        result = await jobs_collection.update_many(
            {"status": "running"},
            {"$set": {"status": "paused", "paused_at": datetime.utcnow(), "pause_reason": "manual"}}
        )
        
        logger.info(f"Paused {result.modified_count} running jobs")
        return {
            "message": f"Successfully paused {result.modified_count} running jobs",
            "paused_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Error pausing all jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause jobs")

@router.post("/jobs/resume-all")
async def resume_all_jobs():
    """Resume all paused jobs"""
    try:
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        # Update all paused jobs to running
        result = await jobs_collection.update_many(
            {"status": "paused"},
            {"$set": {"status": "running", "resumed_at": datetime.utcnow()}, "$unset": {"pause_reason": "", "paused_at": ""}}
        )
        
        logger.info(f"Resumed {result.modified_count} paused jobs")
        return {
            "message": f"Successfully resumed {result.modified_count} paused jobs",
            "resumed_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Error resuming all jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume jobs")

@router.post("/jobs/resume-network-paused")
async def resume_network_paused_jobs():
    """Resume only jobs that were paused due to network issues"""
    try:
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        # Update only network-paused jobs to running
        result = await jobs_collection.update_many(
            {"status": "paused", "pause_reason": "network_error"},
            {"$set": {"status": "running", "resumed_at": datetime.utcnow()}, "$unset": {"pause_reason": "", "paused_at": ""}}
        )
        
        logger.info(f"Resumed {result.modified_count} network-paused jobs")
        return {
            "message": f"Successfully resumed {result.modified_count} network-paused jobs",
            "resumed_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Error resuming network-paused jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume network-paused jobs")

@router.get("/jobs/status-summary")
async def get_jobs_status_summary():
    """Get a summary of all job statuses"""
    try:
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        # Aggregate job statuses
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        
        status_counts = {}
        async for result in jobs_collection.aggregate(pipeline):
            status_counts[result["_id"]] = result["count"]
        
        # Get jobs paused due to network issues
        network_paused = await jobs_collection.count_documents({
            "status": "paused", 
            "pause_reason": "network_error"
        })
        
        # Get recently active jobs
        recent_jobs = []
        cursor = jobs_collection.find({}).sort("created_at", -1).limit(5)
        async for job in cursor:
            job["_id"] = str(job["_id"])
            recent_jobs.append({
                "id": job["_id"],
                "name": job["name"],
                "status": job["status"],
                "progress": f"{job.get('cities_completed', 0)}/{job.get('total_cities', 0)}",
                "created_at": job["created_at"],
                "pause_reason": job.get("pause_reason")
            })
        
        return {
            "status_counts": status_counts,
            "network_paused_count": network_paused,
            "recent_jobs": recent_jobs,
            "total_jobs": sum(status_counts.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting jobs status summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job status summary")

# Job Seeding Endpoints
@router.post("/seed-jobs")
async def seed_jobs_from_countries(overwrite: bool = False):
    """
    Seed jobs from the countries configuration file
    
    Args:
        overwrite: If True, removes existing jobs and creates new ones
    """
    try:
        results = await job_seeding_service.seed_jobs(overwrite=overwrite)
        return {
            "message": "Job seeding completed",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error seeding jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/countries-summary")
async def get_countries_summary():
    """Get summary of all countries available for seeding"""
    try:
        summary = await job_seeding_service.get_countries_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting countries summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/seeded-jobs-status")
async def get_seeded_jobs_status():
    """Get status of all seeded jobs organized by region"""
    try:
        status = await job_seeding_service.get_seeded_jobs_status()
        return status
    except Exception as e:
        logger.error(f"Error getting seeded jobs status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Job Management Endpoints
@router.get("/jobs/search")
async def search_jobs(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    status: Optional[str] = Query(None, description="Filter by status"),
    region: Optional[str] = Query(None, description="Filter by region"),
    country: Optional[str] = Query(None, description="Filter by country"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(20, description="Maximum number of records to return")
):
    """
    Search and filter jobs with advanced options
    """
    try:
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        # Build filter query
        filter_query = {}
        
        if domain:
            filter_query["domains"] = {"$in": [domain]}
        
        if status:
            filter_query["status"] = status
        
        if region:
            filter_query["region"] = {"$regex": region, "$options": "i"}
        
        if country:
            filter_query["country"] = {"$regex": country, "$options": "i"}
        
        # Build sort criteria
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        sort_criteria = [(sort_by, sort_direction)]
        
        # Execute query
        cursor = jobs_collection.find(filter_query).sort(sort_criteria).skip(skip).limit(limit)
        jobs = []
        async for job in cursor:
            if '_id' in job:
                job['_id'] = str(job['_id'])
            jobs.append(job)
        
        # Get total count for pagination
        total_count = await jobs_collection.count_documents(filter_query)
        
        return {
            "jobs": jobs,
            "total_count": total_count,
            "has_more": (skip + limit) < total_count
        }
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/jobs/{job_id}/settings")
async def update_job_settings(
    job_id: str,
    concurrent_requests: Optional[int] = None,
    request_delay: Optional[float] = None
):
    """Update job settings (concurrency and delay)"""
    try:
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        # Build update query
        update_data = {}
        if concurrent_requests is not None:
            if concurrent_requests < 1 or concurrent_requests > 20:
                raise HTTPException(status_code=400, detail="Concurrent requests must be between 1 and 20")
            update_data["concurrent_requests"] = concurrent_requests
        
        if request_delay is not None:
            if request_delay < 0.1 or request_delay > 10:
                raise HTTPException(status_code=400, detail="Request delay must be between 0.1 and 10 seconds")
            update_data["request_delay"] = request_delay
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid settings provided")
        
        # Update the job
        result = await jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"message": "Job settings updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
