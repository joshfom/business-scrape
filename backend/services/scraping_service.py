import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import MongoClient
from bson.objectid import ObjectId
from models.database import database
from models.schemas import ScrapingJob, ScrapingStatus, BusinessData, ScrapingProgress
from scrapers.base_scraper import get_scraper
from config import settings
import time

logger = logging.getLogger(__name__)

class ScrapingService:
    """Service for managing and executing scraping jobs"""
    
    def __init__(self):
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.job_stats: Dict[str, Dict] = {}
    
    async def create_job(self, job_data: Dict) -> str:
        """Create a new scraping job"""
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        job = ScrapingJob(**job_data)
        job_dict = job.dict(by_alias=True, exclude_unset=False)  # Changed to include defaults
        # Remove _id field so MongoDB can generate it
        if '_id' in job_dict:
            del job_dict['_id']
        result = await jobs_collection.insert_one(job_dict)
        job_id = str(result.inserted_id)
        
        logger.info(f"Created scraping job {job_id} with status {job.status}")
        return job_id
    
    async def start_job(self, job_id: str) -> bool:
        """Start a scraping job"""
        if job_id in self.active_jobs:
            logger.warning(f"Job {job_id} is already running")
            return False
        
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        # Update job status
        await jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": ScrapingStatus.RUNNING,
                    "started_at": datetime.utcnow()
                }
            }
        )
        
        # Start the scraping task
        task = asyncio.create_task(self._execute_job(job_id))
        self.active_jobs[job_id] = task
        
        logger.info(f"Started scraping job {job_id}")
        return True
    
    async def force_start_job(self, job_id: str) -> bool:
        """Force start a scraping job, stopping any existing instance first"""
        # If job is already running, stop it first
        if job_id in self.active_jobs:
            logger.info(f"Job {job_id} is already running, stopping it first for force start")
            task = self.active_jobs.pop(job_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        # Update job status and reset started_at time
        await jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": ScrapingStatus.RUNNING,
                    "started_at": datetime.utcnow()
                }
            }
        )
        
        # Start the scraping task
        task = asyncio.create_task(self._execute_job(job_id))
        self.active_jobs[job_id] = task
        
        logger.info(f"Force started scraping job {job_id}")
        return True
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a running job"""
        if job_id not in self.active_jobs:
            return False
        
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        await jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": ScrapingStatus.PAUSED}}
        )
        
        # Cancel the task
        task = self.active_jobs.pop(job_id)
        task.cancel()
        
        logger.info(f"Paused scraping job {job_id}")
        return True
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        if job_id in self.active_jobs:
            logger.warning(f"Job {job_id} is already running")
            return False
        
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        progress_collection = db.scraping_progress
        
        # Get the most recent progress record to ensure accurate resumption
        latest_progress = await progress_collection.find_one(
            {"job_id": job_id},
            sort=[("timestamp", -1)]  # Sort by timestamp descending to get the most recent
        )
        
        # Update job status and maintain the current_city and current_page values
        update_data = {
            "status": ScrapingStatus.RUNNING,
            "resumed_at": datetime.utcnow()
        }
        
        # If we found progress records, use them to set the exact resume point
        if latest_progress:
            update_data["current_city"] = latest_progress.get("city")
            update_data["current_page"] = latest_progress.get("page", 1)
            logger.info(f"Found resume point at city '{latest_progress.get('city')}', page {latest_progress.get('page', 1)}")
        
        await jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_data}
        )
        
        # Start the scraping task
        task = asyncio.create_task(self._execute_job(job_id))
        self.active_jobs[job_id] = task
        
        logger.info(f"Resumed scraping job {job_id}")
        return True
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        await jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": ScrapingStatus.CANCELLED,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        if job_id in self.active_jobs:
            task = self.active_jobs.pop(job_id)
            task.cancel()
        
        logger.info(f"Cancelled scraping job {job_id}")
        return True
    
    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get current job status and progress"""
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            return None
        
        # Add runtime stats
        if job_id in self.job_stats:
            job.update(self.job_stats[job_id])
        
        return job
        
    async def _execute_job(self, job_id: str):
        """Execute a scraping job"""
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        businesses_collection = db.businesses
        progress_collection = db.scraping_progress

        try:
            # Get job details
            job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
            if not job:
                logger.error(f"Job {job_id} not found")
                return

            self.job_stats[job_id] = {
                "current_domain": None,
                "current_city": None,
                "current_page": 1,
                "businesses_scraped": 0,
                "cities_completed": 0,
                "start_time": time.time()
            }

            # Create aiohttp session with timeout and concurrency limits
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(limit=job["concurrent_requests"])

            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                for domain in job["domains"]:
                    # Check if job is still running
                    current_job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
                    if current_job["status"] != ScrapingStatus.RUNNING:
                        logger.info(f"Job {job_id} stopped (status: {current_job['status']})")
                        break

                    self.job_stats[job_id]["current_domain"] = domain
                    await jobs_collection.update_one(
                        {"_id": ObjectId(job_id)},
                        {"$set": {"current_domain": domain}}
                    )

                    logger.info(f"Scraping domain: {domain}")
                    scraper = get_scraper(domain, session)

                    # Get all cities for this domain
                    cities = await scraper.get_cities()
                    
                    # Only update total_cities if we haven't done this before (for new jobs)
                    if job.get("total_cities", 0) == 0:
                        await jobs_collection.update_one(
                            {"_id": ObjectId(job_id)},
                            {"$set": {"total_cities": len(cities)}}
                        )

                    # 🚀 RESUME LOGIC: Start from where we left off
                    start_city_index = 0
                    start_page = 1
                    
                    # If resuming, find where we stopped
                    current_city = job.get("current_city")
                    current_page = job.get("current_page", 1)
                    
                    # Check if we're resuming from a previous run
                    is_resuming = job.get("status") == ScrapingStatus.RUNNING and job.get("resumed_at")
                    
                    # If job was previously running and has progress info, try to resume
                    if current_city:
                        # Find the index of the current city
                        for i, city in enumerate(cities):
                            if city.name == current_city:
                                start_city_index = i
                                
                                # When resuming, start from current_page (not current_page+1)
                                # This is because current_page points to the next page that needs processing
                                start_page = current_page
                                
                                logger.info(f"🔄 RESUMING from city '{current_city}' (index {i}) at page {start_page}")
                                break
                        else:
                            # City not found, start from beginning
                            logger.warning(f"Current city '{current_city}' not found in cities list, starting from beginning")
                            
                    # Double-check with progress collection to find the most accurate resume point
                    if is_resuming:
                        # Get most recent progress record
                        latest_progress = await progress_collection.find_one(
                            {"job_id": job_id},
                            sort=[("timestamp", -1)]
                        )
                        
                        if latest_progress:
                            latest_city = latest_progress.get("city")
                            latest_page = latest_progress.get("page", 1)
                            
                            # Find city index
                            for i, city in enumerate(cities):
                                if city.name == latest_city:
                                    # Only override if this record is more recent
                                    if latest_progress.get("timestamp") > job.get("last_progress_timestamp", datetime.min):
                                        start_city_index = i
                                        # Resume from the NEXT page since this one was completed
                                        start_page = latest_page + 1  
                                        logger.info(f"📊 Found more recent progress record: city '{latest_city}', resuming from page {start_page}")
                                    break

                    # Process each city starting from resume point
                    for city_idx, city in enumerate(cities[start_city_index:], start=start_city_index):                        # Check job status again
                        current_job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
                        if current_job["status"] != ScrapingStatus.RUNNING:
                            break

                        self.job_stats[job_id]["current_city"] = city.name
                        await jobs_collection.update_one(
                            {"_id": ObjectId(job_id)},
                            {"$set": {"current_city": city.name}}
                        )

                        logger.info(f"Scraping city: {city.name} ({city.business_count} businesses) - City {city_idx + 1}/{len(cities)}")

                        # 🚀 RESUME LOGIC: Start from correct page
                        initial_page = start_page if city_idx == start_city_index else 1
                        if initial_page > 1:
                            logger.info(f"🔄 RESUMING at page {initial_page} for city '{city.name}'")

                        # Process pages for this city starting from resume point
                        page = initial_page
                        while True:
                            # Check job status
                            current_job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
                            if current_job["status"] != ScrapingStatus.RUNNING:
                                break

                            # First update just in-memory stats
                            self.job_stats[job_id]["current_page"] = page

                            # Get business listings for this page
                            business_urls, has_next = await scraper.get_business_listings(city.url, page)

                            if not business_urls:
                                logger.warning(f"No businesses found on page {page} of {city.name}")
                                break

                            # Update total businesses count (track URLs found, not processed)
                            await jobs_collection.update_one(
                                {"_id": ObjectId(job_id)},
                                {"$inc": {"total_businesses": len(business_urls)}}
                            )

                            logger.info(f"Found {len(business_urls)} businesses on page {page} of {city.name} - starting immediate scraping")

                            # 🎯 SMART DUPLICATE CHECKING: Filter out already processed businesses
                            new_business_urls = []
                            for business_url in business_urls:
                                # Check if business already exists in database
                                existing = await businesses_collection.find_one({"page_url": business_url})
                                if not existing:
                                    new_business_urls.append(business_url)
                                else:
                                    logger.debug(f"⏭️  Skipping existing business: {business_url}")

                            logger.info(f"📊 Page {page}: {len(business_urls)} total URLs, {len(new_business_urls)} new businesses to scrape")

                            if new_business_urls:
                                # Scrape only new businesses with semaphore for concurrency control
                                semaphore = asyncio.Semaphore(job["concurrent_requests"])
                                tasks = []

                                for business_url in new_business_urls:
                                    task = asyncio.create_task(
                                        self._scrape_business_with_semaphore(
                                            semaphore, scraper, business_url, 
                                            businesses_collection, job_id, job["request_delay"]
                                        )
                                    )
                                    tasks.append(task)

                                # Wait for all new businesses on this page to be scraped
                                results = await asyncio.gather(*tasks, return_exceptions=True)

                                # 🎯 ACCURATE COUNTING: Only count actual successful database saves
                                successful_saves = 0
                                for result in results:
                                    if isinstance(result, BusinessData):
                                        successful_saves += 1
                                    elif isinstance(result, Exception):
                                        logger.error(f"Task failed with exception: {result}")

                                # Update job counter only with actual saves
                                if successful_saves > 0:
                                    self.job_stats[job_id]["businesses_scraped"] += successful_saves
                                    await jobs_collection.update_one(
                                        {"_id": ObjectId(job_id)},
                                        {"$inc": {"businesses_scraped": successful_saves}}
                                    )

                                logger.info(f"✅ Page {page} of {city.name}: successfully saved {successful_saves}/{len(new_business_urls)} new businesses")
                            else:
                                logger.info(f"⏭️  Page {page} of {city.name}: all businesses already exist, skipping")

                            # Log progress and update database with current position AFTER processing the page
                            progress_data = {
                                "job_id": job_id,
                                "domain": domain,
                                "city": city.name,
                                "page": page,
                                "businesses_found": len(business_urls),
                                "new_businesses": len(new_business_urls),
                                "businesses_scraped": successful_saves if new_business_urls else 0,
                                "timestamp": datetime.utcnow()
                            }
                            
                            # Save progress to the progress collection
                            await progress_collection.insert_one(progress_data)
                            
                            # Update job document with current position AFTER processing the page
                            # This ensures we'll resume from the next page, not repeat this page
                            await jobs_collection.update_one(
                                {"_id": ObjectId(job_id)},
                                {"$set": {
                                    "current_city": city.name,
                                    "current_page": page,
                                    "last_progress_timestamp": datetime.utcnow()
                                }}
                            )

                            # Move to next page if available
                            if not has_next:
                                logger.info(f"✅ Completed all pages for {city.name}")
                                break
                                
                            # Increment page number for next iteration
                            page += 1
                            
                            # When a page is completed, update the job record to point to the NEXT page
                            # This ensures that if we resume, we start with the next unprocessed page
                            await jobs_collection.update_one(
                                {"_id": ObjectId(job_id)},
                                {"$set": {"current_page": page}}
                            )

                            # Small delay between pages to be respectful
                            await asyncio.sleep(job["request_delay"])

                        # Reset start_page for next city
                        start_page = 1

                        # Mark city as completed
                        self.job_stats[job_id]["cities_completed"] += 1
                        await jobs_collection.update_one(
                            {"_id": ObjectId(job_id)},
                            {"$inc": {"cities_completed": 1}}
                        )
            
            # Mark job as completed
            await jobs_collection.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": ScrapingStatus.COMPLETED,
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Scraping job {job_id} completed successfully")
            
        except asyncio.CancelledError:
            # Check if job was paused or cancelled
            current_job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
            if current_job and current_job.get("status") == ScrapingStatus.PAUSED:
                logger.info(f"Scraping job {job_id} was paused")
                # Don't change status - it's already set to PAUSED
            else:
                logger.info(f"Scraping job {job_id} was cancelled")
                await jobs_collection.update_one(
                    {"_id": ObjectId(job_id)},
                    {
                        "$set": {
                            "status": ScrapingStatus.CANCELLED,
                            "completed_at": datetime.utcnow()
                        }
                    }
                )
        except Exception as e:
            # Check if this is a network-related error
            error_str = str(e).lower()
            network_error_indicators = [
                'connection', 'timeout', 'network', 'dns', 'resolve', 
                'unreachable', 'refused', 'reset', 'ssl', 'certificate'
            ]
            
            is_network_error = any(indicator in error_str for indicator in network_error_indicators)
            
            if is_network_error:
                logger.warning(f"Network error detected in job {job_id}: {e}")
                await jobs_collection.update_one(
                    {"_id": ObjectId(job_id)},
                    {
                        "$set": {
                            "status": ScrapingStatus.PAUSED,
                            "paused_at": datetime.utcnow(),
                            "pause_reason": "network_error"
                        },
                        "$push": {"errors": f"Network error (auto-paused): {str(e)}"}
                    }
                )
                logger.info(f"Job {job_id} automatically paused due to network error")
            else:
                logger.error(f"Error in scraping job {job_id}: {e}")
                await jobs_collection.update_one(
                    {"_id": ObjectId(job_id)},
                    {
                        "$set": {
                            "status": ScrapingStatus.FAILED,
                            "completed_at": datetime.utcnow()
                        },
                        "$push": {"errors": str(e)}
                    }
                )
        finally:
            # Clean up
            if job_id in self.active_jobs:
                self.active_jobs.pop(job_id)
            if job_id in self.job_stats:
                self.job_stats.pop(job_id)
    
    async def _scrape_business_with_semaphore(
        self, 
        semaphore: asyncio.Semaphore, 
        scraper, 
        business_url: str, 
        collection: AsyncIOMotorCollection,
        job_id: str,
        delay: float
    ):
        """Scrape a single business with concurrency control"""
        async with semaphore:
            try:
                # Check if business already exists
                existing = await collection.find_one({"page_url": business_url})
                if existing:
                    logger.debug(f"Business already exists: {business_url}")
                    # Return None to indicate no new business was scraped (don't count as success)
                    return None
                
                # Scrape business details
                logger.debug(f"Starting detail scraping for: {business_url}")
                business_data = await scraper.scrape_business_details(business_url)
                
                if business_data:
                    # Save to database
                    logger.debug(f"Attempting to save business: {business_data.name}")
                    try:
                        # Convert to dict and exclude None _id field to avoid MongoDB duplicate key error
                        business_dict = business_data.model_dump(by_alias=True, exclude_unset=True)
                        if '_id' in business_dict and business_dict['_id'] is None:
                            del business_dict['_id']
                        
                        result = await collection.insert_one(business_dict)
                        logger.info(f"✅ Saved new business: {business_data.name} (ID: {result.inserted_id})")
                        return business_data
                    except Exception as db_error:
                        logger.error(f"❌ Database save failed for {business_data.name}: {db_error}")
                        return None
                else:
                    logger.warning(f"❌ Failed to scrape business details: {business_url}")
                    return None
                    
            except Exception as e:
                # Check if this is a network error that should pause the job
                error_str = str(e).lower()
                network_error_indicators = [
                    'connection', 'timeout', 'network', 'dns', 'resolve', 
                    'unreachable', 'refused', 'reset', 'ssl', 'certificate'
                ]
                
                if any(indicator in error_str for indicator in network_error_indicators):
                    logger.warning(f"Network error scraping {business_url}: {e}")
                    # This individual error will be handled by the main job error handler
                    raise e
                else:
                    logger.error(f"Error scraping business {business_url}: {e}")
                    return None
            finally:
                # Delay between requests
                await asyncio.sleep(delay)

# Global scraping service instance
scraping_service = ScrapingService()
