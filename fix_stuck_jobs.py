#!/usr/bin/env python3
"""
Script to fix stuck scraping jobs after server restart
This handles jobs that are marked as "running" but have no active process
"""

import asyncio
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database configuration
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "business_scraper"

async def fix_stuck_jobs():
    """Fix jobs that are stuck in running state after server restart"""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    jobs_collection = db.scraping_jobs
    
    print("🔍 Checking for stuck jobs...")
    
    # Find all jobs marked as "running"
    running_jobs = await jobs_collection.find({"status": "running"}).to_list(None)
    
    if not running_jobs:
        print("✅ No stuck jobs found!")
        client.close()
        return
    
    print(f"🔧 Found {len(running_jobs)} potentially stuck jobs:")
    
    for job in running_jobs:
        job_id = str(job["_id"])
        job_name = job.get("name", "Unknown")
        started_at = job.get("started_at", "Unknown")
        
        print(f"   • Job: {job_name} (ID: {job_id})")
        print(f"     Started: {started_at}")
        print(f"     Status: {job['status']}")
    
    # Ask user for confirmation
    print("\n❓ These jobs appear to be stuck (marked as running but no active process).")
    choice = input("Would you like to:\n  1. Set them to 'paused' (recommended)\n  2. Set them to 'cancelled'\n  3. Exit without changes\nChoice (1/2/3): ").strip()
    
    if choice == "3":
        print("🚫 No changes made.")
        client.close()
        return
    
    new_status = "paused" if choice == "1" else "cancelled"
    
    if choice not in ["1", "2"]:
        print("❌ Invalid choice. Exiting.")
        client.close()
        return
    
    # Update the jobs
    update_data = {
        "$set": {
            "status": new_status,
            "paused_at": datetime.utcnow() if new_status == "paused" else None,
            "completed_at": datetime.utcnow() if new_status == "cancelled" else None,
            "pause_reason": "server_restart" if new_status == "paused" else None
        }
    }
    
    if new_status == "cancelled":
        update_data["$unset"] = {"pause_reason": "", "paused_at": ""}
    
    result = await jobs_collection.update_many(
        {"status": "running"},
        update_data
    )
    
    print(f"✅ Updated {result.modified_count} jobs to '{new_status}' status")
    
    # Show updated jobs
    print("\n📊 Updated jobs:")
    updated_jobs = await jobs_collection.find({"status": new_status}).to_list(None)
    for job in updated_jobs:
        job_id = str(job["_id"])
        job_name = job.get("name", "Unknown")
        print(f"   • {job_name} (ID: {job_id}) -> {new_status}")
    
    client.close()

async def fix_specific_job(job_id: str, new_status: str = "paused"):
    """Fix a specific job by ID"""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    jobs_collection = db.scraping_jobs
    
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(job_id)
    except Exception as e:
        print(f"❌ Invalid job ID format: {e}")
        client.close()
        return False
    
    # Check if job exists
    job = await jobs_collection.find_one({"_id": object_id})
    if not job:
        print(f"❌ Job not found: {job_id}")
        client.close()
        return False
    
    job_name = job.get("name", "Unknown")
    current_status = job.get("status", "unknown")
    
    print(f"🔧 Fixing job: {job_name} (ID: {job_id})")
    print(f"   Current status: {current_status}")
    print(f"   New status: {new_status}")
    
    # Update the specific job
    update_data = {
        "$set": {
            "status": new_status,
            "paused_at": datetime.utcnow() if new_status == "paused" else None,
            "completed_at": datetime.utcnow() if new_status == "cancelled" else None,
            "pause_reason": "server_restart" if new_status == "paused" else None
        }
    }
    
    if new_status == "cancelled":
        update_data["$unset"] = {"pause_reason": "", "paused_at": ""}
    
    result = await jobs_collection.update_one(
        {"_id": object_id},
        update_data
    )
    
    if result.modified_count > 0:
        print(f"✅ Successfully updated job to '{new_status}' status")
        client.close()
        return True
    else:
        print(f"❌ Failed to update job")
        client.close()
        return False

async def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Fix specific job
        job_id = sys.argv[1]
        status = sys.argv[2] if len(sys.argv) > 2 else "paused"
        await fix_specific_job(job_id, status)
    else:
        # Interactive mode - fix all stuck jobs
        await fix_stuck_jobs()

if __name__ == "__main__":
    print("🔧 Stuck Job Fixer")
    print("==================")
    print("This script fixes jobs stuck in 'running' state after server restart\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🚫 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
