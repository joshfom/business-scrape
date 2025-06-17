#!/usr/bin/env python3

import asyncio
import logging
import sys
import os
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models.database import database
from services.job_seeding_service import job_seeding_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_job_seeding():
    """Test the job seeding functionality"""
    try:
        # Connect to database
        await database.connect_db()
        
        print("🌱 Testing Job Seeding Service...")
        
        # Test loading countries data
        print("\n📋 Countries Summary:")
        summary = await job_seeding_service.get_countries_summary()
        print(f"Total regions: {len(summary['regions'])}")
        print(f"Total countries: {summary['total_countries']}")
        
        for region in summary['regions']:
            print(f"  {region['name']}: {region['country_count']} countries")
        
        # Test seeding jobs
        print("\n🚀 Seeding jobs...")
        results = await job_seeding_service.seed_jobs(overwrite=False)
        
        print(f"✅ Seeding Results:")
        print(f"  Total countries processed: {results['total_countries']}")
        print(f"  Jobs created: {results['jobs_created']}")
        print(f"  Jobs skipped: {results['jobs_skipped']}")
        print(f"  Errors: {len(results['errors'])}")
        
        if results['errors']:
            print("❌ Errors:")
            for error in results['errors']:
                print(f"    {error}")
        
        # Test getting seeded jobs status
        print("\n📊 Seeded Jobs Status:")
        status = await job_seeding_service.get_seeded_jobs_status()
        print(f"Total seeded jobs: {status['total_seeded_jobs']}")
        
        for region in status['regions']:
            print(f"  {region['name']}: {region['total_jobs']} jobs")
            print(f"    Pending: {region['pending']}, Running: {region['running']}")
            print(f"    Completed: {region['completed']}, Failed: {region['failed']}")
        
        print("\n✅ Job seeding test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        await database.close_db()

async def show_sample_jobs():
    """Show a sample of created jobs"""
    try:
        await database.connect_db()
        
        db = database.get_database()
        jobs_collection = db.scraping_jobs
        
        print("\n📄 Sample Jobs:")
        async for job in jobs_collection.find({"is_seeded": True}).limit(5):
            print(f"  Country: {job.get('country', 'Unknown')}")
            print(f"  Region: {job.get('region', 'Unknown')}")
            print(f"  Domain: {job.get('domains', ['Unknown'])[0]}")
            print(f"  Status: {job.get('status', 'Unknown')}")
            print(f"  Base URL: {job.get('base_url', 'Unknown')}")
            print("  ---")
        
    except Exception as e:
        logger.error(f"Error showing sample jobs: {e}")
    finally:
        await database.close_db()

if __name__ == "__main__":
    print("🔧 Business Scraper - Job Seeding Test")
    print("=" * 50)
    
    asyncio.run(test_job_seeding())
    asyncio.run(show_sample_jobs())
