import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from models.database import database
from models.schemas import ScrapingJob, ScrapingStatus

logger = logging.getLogger(__name__)

class JobSeedingService:
    """Service for seeding and managing jobs from the countries configuration"""
    
    def __init__(self):
        self.countries_data = None
        self._load_countries_data()
    
    def _load_countries_data(self):
        """Load countries data from JSON file"""
        try:
            import os
            # In Docker container, the file is copied to the working directory
            countries_file = os.path.join(os.getcwd(), 'countries_updated.json')
            
            # Fallback to different locations if needed
            if not os.path.exists(countries_file):
                # Try relative to the backend directory
                current_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from services to backend
                project_dir = os.path.dirname(current_dir)  # Go up from backend to project root
                countries_file = os.path.join(project_dir, 'countries_updated.json')
            
            with open(countries_file, 'r', encoding='utf-8') as file:
                self.countries_data = json.load(file)
            logger.info(f"Loaded countries data with {len(self.countries_data.get('countries', []))} regions")
        except Exception as e:
            logger.error(f"Failed to load countries data: {e}")
            self.countries_data = {"countries": []}
    
    async def seed_jobs(self, overwrite: bool = False) -> Dict[str, Any]:
        """
        Seed jobs from countries data
        
        Args:
            overwrite: If True, removes existing jobs and creates new ones
                      If False, only creates jobs for countries that don't exist
        
        Returns:
            Dict with seeding results
        """
        if not self.countries_data:
            raise Exception("Countries data not loaded")
        
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        results = {
            "total_countries": 0,
            "jobs_created": 0,
            "jobs_skipped": 0,
            "jobs_updated": 0,
            "errors": []
        }
        
        try:
            # If overwrite, remove all existing jobs
            if overwrite:
                deleted_result = await jobs_collection.delete_many({})
                logger.info(f"Deleted {deleted_result.deleted_count} existing jobs")
            
            # Get existing jobs to avoid duplicates (if not overwriting)
            existing_jobs = {}
            if not overwrite:
                async for job in jobs_collection.find({}):
                    # Store by domain for quick lookup
                    for domain in job.get('domains', []):
                        existing_jobs[domain] = job
            
            # Seed jobs from countries data
            for region_data in self.countries_data.get('countries', []):
                region_name = region_data.get('region', 'Unknown')
                
                for country in region_data.get('countries', []):
                    results["total_countries"] += 1
                    
                    try:
                        await self._create_country_job(
                            country, region_name, existing_jobs, results, overwrite
                        )
                    except Exception as e:
                        error_msg = f"Failed to create job for {country.get('name', 'Unknown')}: {str(e)}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg)
            
            logger.info(f"Job seeding completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error during job seeding: {e}")
            raise
    
    async def _create_country_job(
        self, 
        country: Dict[str, Any], 
        region_name: str, 
        existing_jobs: Dict[str, Any],
        results: Dict[str, Any],
        overwrite: bool
    ):
        """Create a job for a single country"""
        country_name = country.get('name', 'Unknown')
        domain = country.get('domain', '')
        url = country.get('url', '')
        
        if not domain:
            results["errors"].append(f"No domain found for {country_name}")
            return
        
        # Check if job already exists (if not overwriting)
        if not overwrite and domain in existing_jobs:
            results["jobs_skipped"] += 1
            logger.debug(f"Skipping {country_name} - job already exists")
            return
        
        # Create job data
        job_data = {
            "name": f"{country_name} Business Directory",
            "domains": [domain],
            "status": ScrapingStatus.PENDING,
            "concurrent_requests": 5,
            "request_delay": 1.0,
            "created_at": datetime.utcnow(),
            "total_cities": 0,
            "cities_completed": 0,
            "total_businesses": 0,
            "businesses_scraped": 0,
            "current_page": 1,
            "errors": [],
            # Additional metadata for job management
            "country": country_name,
            "region": region_name,
            "base_url": url,
            "latitude": float(country.get('latitude', 0)),
            "longitude": float(country.get('longitude', 0)),
            "is_seeded": True,  # Mark as seeded job
        }
        
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        # Insert the job
        result = await jobs_collection.insert_one(job_data)
        results["jobs_created"] += 1
        
        logger.info(f"Created job for {country_name} ({domain}) with ID {result.inserted_id}")
    
    async def get_countries_summary(self) -> Dict[str, Any]:
        """Get a summary of all countries in the configuration"""
        if not self.countries_data:
            return {"regions": [], "total_countries": 0}
        
        summary = {
            "regions": [],
            "total_countries": 0
        }
        
        for region_data in self.countries_data.get('countries', []):
            region_name = region_data.get('region', 'Unknown')
            countries = region_data.get('countries', [])
            
            region_summary = {
                "name": region_name,
                "country_count": len(countries),
                "countries": [
                    {
                        "name": c.get('name', 'Unknown'),
                        "domain": c.get('domain', ''),
                        "url": c.get('url', ''),
                    }
                    for c in countries
                ]
            }
            
            summary["regions"].append(region_summary)
            summary["total_countries"] += len(countries)
        
        return summary
    
    async def get_seeded_jobs_status(self) -> Dict[str, Any]:
        """Get status of all seeded jobs organized by region"""
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        # Get all seeded jobs
        seeded_jobs = []
        async for job in jobs_collection.find({"is_seeded": True}):
            # Convert ObjectId to string
            job['_id'] = str(job['_id'])
            seeded_jobs.append(job)
        
        # Organize by region
        regions = {}
        for job in seeded_jobs:
            region = job.get('region', 'Unknown')
            if region not in regions:
                regions[region] = {
                    "name": region,
                    "total_jobs": 0,
                    "completed": 0,
                    "running": 0,
                    "pending": 0,
                    "failed": 0,
                    "cancelled": 0,
                    "paused": 0,
                    "jobs": []
                }
            
            regions[region]["total_jobs"] += 1
            regions[region][job.get('status', 'pending')] += 1
            regions[region]["jobs"].append(job)
        
        return {
            "regions": list(regions.values()),
            "total_seeded_jobs": len(seeded_jobs),
            "jobs": seeded_jobs
        }

# Global instance
job_seeding_service = JobSeedingService()
