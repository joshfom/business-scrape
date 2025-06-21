#!/usr/bin/env python3
"""
Job Restart Script for Business Scraper

This script allows you to:
1. Reset stuck/failed jobs to pending status
2. Restart specific countries/domains that had zero extraction
3. View job statistics and status
"""

import asyncio
import motor.motor_asyncio
import os
from datetime import datetime
from bson import ObjectId
import argparse
import sys

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:business123@localhost:27017/business_scraper?authSource=admin")

async def get_database():
    """Get database connection"""
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    return client.business_scraper

async def list_jobs(status_filter=None):
    """List all jobs with their status"""
    db = await get_database()
    jobs_collection = db.scraping_jobs
    
    query = {}
    if status_filter:
        query["status"] = status_filter
    
    jobs = await jobs_collection.find(query).sort("created_at", -1).to_list(None)
    
    print(f"\n{'='*80}")
    print(f"{'JOB ID':<25} {'DOMAIN':<25} {'STATUS':<12} {'BUSINESSES':<12} {'CITIES':<10}")
    print(f"{'='*80}")
    
    for job in jobs:
        job_id = str(job["_id"])[:24]
        domain = job.get("domains", ["Unknown"])[0][:24]
        status = job.get("status", "unknown")
        businesses = job.get("businesses_scraped", 0)
        cities_completed = job.get("cities_completed", 0)
        total_cities = job.get("total_cities", 0)
        
        print(f"{job_id:<25} {domain:<25} {status:<12} {businesses:<12} {cities_completed}/{total_cities}")
    
    print(f"{'='*80}")
    print(f"Total jobs: {len(jobs)}")

async def get_zero_extraction_jobs():
    """Find jobs with zero business extraction"""
    db = await get_database()
    jobs_collection = db.scraping_jobs
    
    zero_jobs = await jobs_collection.find({
        "businesses_scraped": {"$lte": 0},
        "status": {"$in": ["completed", "failed", "cancelled"]}
    }).to_list(None)
    
    print(f"\n{'='*100}")
    print(f"JOBS WITH ZERO EXTRACTION ({len(zero_jobs)} found)")
    print(f"{'='*100}")
    print(f"{'JOB ID':<25} {'DOMAIN':<30} {'STATUS':<12} {'CREATED':<20}")
    print(f"{'='*100}")
    
    for job in zero_jobs:
        job_id = str(job["_id"])[:24]
        domain = job.get("domains", ["Unknown"])[0][:29]
        status = job.get("status", "unknown")
        created = job.get("created_at", "").strftime("%Y-%m-%d %H:%M") if job.get("created_at") else "Unknown"
        
        print(f"{job_id:<25} {domain:<30} {status:<12} {created:<20}")
    
    return zero_jobs

async def reset_job_status(job_id):
    """Reset a job status to pending"""
    db = await get_database()
    jobs_collection = db.scraping_jobs
    
    try:
        # Convert string ID to ObjectId if needed
        if isinstance(job_id, str):
            job_id = ObjectId(job_id)
        
        result = await jobs_collection.update_one(
            {"_id": job_id},
            {
                "$set": {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "cities_completed": 0,
                    "businesses_scraped": 0,
                    "current_page": 1,
                    "errors": []
                },
                "$unset": {
                    "current_domain": "",
                    "current_city": ""
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Job {job_id} reset to pending status")
            return True
        else:
            print(f"❌ Job {job_id} not found or not modified")
            return False
    except Exception as e:
        print(f"❌ Error resetting job {job_id}: {e}")
        return False

async def restart_zero_extraction_jobs():
    """Reset all jobs with zero extraction to pending"""
    zero_jobs = await get_zero_extraction_jobs()
    
    if not zero_jobs:
        print("No jobs with zero extraction found.")
        return
    
    response = input(f"\nDo you want to reset all {len(zero_jobs)} jobs to pending status? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    success_count = 0
    for job in zero_jobs:
        if await reset_job_status(job["_id"]):
            success_count += 1
    
    print(f"\n✅ Successfully reset {success_count} out of {len(zero_jobs)} jobs")

async def restart_specific_job(job_id):
    """Reset a specific job to pending"""
    try:
        if len(job_id) < 24:
            # If partial ID provided, try to find matching job
            db = await get_database()
            jobs_collection = db.scraping_jobs
            
            # Find jobs that start with the provided ID
            jobs = await jobs_collection.find({}).to_list(None)
            matching_jobs = [job for job in jobs if str(job["_id"]).startswith(job_id)]
            
            if len(matching_jobs) == 0:
                print(f"❌ No jobs found starting with ID: {job_id}")
                return False
            elif len(matching_jobs) > 1:
                print(f"❌ Multiple jobs found starting with ID: {job_id}")
                for job in matching_jobs:
                    domain = job.get("domains", ["Unknown"])[0]
                    print(f"  - {job['_id']} ({domain})")
                return False
            else:
                job_id = matching_jobs[0]["_id"]
        
        return await reset_job_status(job_id)
    except Exception as e:
        print(f"❌ Error restarting job: {e}")
        return False

async def show_database_stats():
    """Show database statistics"""
    db = await get_database()
    
    # Job statistics
    jobs_collection = db.scraping_jobs
    total_jobs = await jobs_collection.count_documents({})
    
    job_stats = await jobs_collection.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]).to_list(None)
    
    # Business statistics
    businesses_collection = db.businesses
    total_businesses = await businesses_collection.count_documents({})
    
    # Domain statistics
    domain_stats = await businesses_collection.aggregate([
        {"$group": {"_id": "$domain", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(None)
    
    print(f"\n{'='*60}")
    print(f"DATABASE STATISTICS")
    print(f"{'='*60}")
    print(f"Total Jobs: {total_jobs:,}")
    print(f"Total Businesses: {total_businesses:,}")
    
    print(f"\nJob Status Breakdown:")
    for stat in job_stats:
        status = stat["_id"] or "unknown"
        count = stat["count"]
        print(f"  {status}: {count}")
    
    print(f"\nTop Domains by Business Count:")
    for i, stat in enumerate(domain_stats[:10]):
        domain = stat["_id"] or "unknown"
        count = stat["count"]
        print(f"  {i+1}. {domain}: {count:,}")

async def main():
    parser = argparse.ArgumentParser(description="Business Scraper Job Management")
    parser.add_argument("action", choices=[
        "list", "list-zero", "restart-zero", "restart", "stats"
    ], help="Action to perform")
    parser.add_argument("--job-id", help="Specific job ID to restart (partial ID accepted)")
    parser.add_argument("--status", help="Filter jobs by status (for list action)")
    
    args = parser.parse_args()
    
    try:
        if args.action == "list":
            await list_jobs(args.status)
        elif args.action == "list-zero":
            await get_zero_extraction_jobs()
        elif args.action == "restart-zero":
            await restart_zero_extraction_jobs()
        elif args.action == "restart":
            if not args.job_id:
                print("❌ --job-id is required for restart action")
                sys.exit(1)
            await restart_specific_job(args.job_id)
        elif args.action == "stats":
            await show_database_stats()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
