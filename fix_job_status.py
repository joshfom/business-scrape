#!/usr/bin/env python3
"""
Script to fix jobs with null status values to have 'pending' status
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_job_status():
    """Update jobs with null status to pending"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        db = client.business_scraper
        jobs_collection = db.scraping_jobs
        
        # Find jobs with null status
        jobs_with_null_status = await jobs_collection.find({"status": None}).to_list(100)
        print(f"Found {len(jobs_with_null_status)} jobs with null status")
        
        if jobs_with_null_status:
            # Update all jobs with null status to pending
            result = await jobs_collection.update_many(
                {"status": None},
                {"$set": {"status": "pending"}}
            )
            print(f"Updated {result.modified_count} jobs to 'pending' status")
        
        # Show all jobs now
        all_jobs = await jobs_collection.find({}).to_list(100)
        print("\nAll jobs in database:")
        for job in all_jobs:
            print(f"Job {job.get('_id')}: {job.get('name')} - Status: {job.get('status')}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_job_status())
