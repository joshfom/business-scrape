#!/usr/bin/env python3
"""
Script to fix the businesses_scraped count mismatch in job table
This corrects the job table to reflect actual database counts
"""

import asyncio
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Database configuration
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "business_scraper"

async def fix_business_count_mismatch():
    """Fix the mismatch between job table businesses_scraped and actual database counts"""
    
    print("🔧 BUSINESS COUNT MISMATCH FIXER")
    print("=" * 60)
    print("This script corrects job table counts to match actual database content")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        jobs_collection = db.scraping_jobs
        businesses_collection = db.businesses
        
        print("\n🔍 Analyzing Jobs...")
        
        # Get all jobs
        jobs = await jobs_collection.find({}).to_list(None)
        
        for job in jobs:
            job_id = str(job["_id"])
            name = job.get("name", "Unknown")
            domains = job.get("domains", [])
            claimed_scraped = job.get("businesses_scraped", 0)
            claimed_total = job.get("total_businesses", 0)
            
            print(f"\n📊 Job: {name} ({job_id})")
            print(f"   Domains: {domains}")
            print(f"   Claimed Total: {claimed_total:,}")
            print(f"   Claimed Scraped: {claimed_scraped:,}")
            
            if domains:
                domain = domains[0]  # Get first domain
                
                # Count actual businesses in database for this domain
                actual_count = await businesses_collection.count_documents({"domain": domain})
                print(f"   Actual DB Count: {actual_count:,}")
                
                # Calculate mismatch
                difference = claimed_scraped - actual_count
                
                if difference > 0:
                    print(f"   ⚠️  MISMATCH: Over-counted by {difference:,}")
                    
                    # Ask if user wants to fix this job
                    choice = input(f"   Fix {name} job counts? (y/n): ").strip().lower()
                    
                    if choice == 'y':
                        # Update job with correct counts
                        update_result = await jobs_collection.update_one(
                            {"_id": job["_id"]},
                            {
                                "$set": {
                                    "businesses_scraped": actual_count,
                                    "total_businesses": max(actual_count, claimed_total),  # Keep total at least as high as scraped
                                    "fixed_at": datetime.utcnow(),
                                    "fix_reason": "corrected_count_mismatch"
                                }
                            }
                        )
                        
                        if update_result.modified_count > 0:
                            print(f"   ✅ FIXED: Updated businesses_scraped from {claimed_scraped:,} to {actual_count:,}")
                        else:
                            print(f"   ❌ FAILED: Could not update job")
                    else:
                        print(f"   ⏭️  SKIPPED: Job not modified")
                        
                elif difference < 0:
                    print(f"   🤔 DB has {abs(difference):,} more than job claims (unusual)")
                else:
                    print(f"   ✅ PERFECT MATCH: No fix needed")
            else:
                print(f"   ❓ No domains specified")
        
        client.close()
        
        print(f"\n✅ COMPLETED: Business count mismatch analysis and fixes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def fix_all_jobs_automatically():
    """Automatically fix all jobs without user prompts"""
    
    print("🔧 AUTOMATIC BUSINESS COUNT FIXER")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        jobs_collection = db.scraping_jobs
        businesses_collection = db.businesses
        
        print("\n🔍 Fixing all jobs automatically...")
        
        # Get all jobs
        jobs = await jobs_collection.find({}).to_list(None)
        fixed_count = 0
        
        for job in jobs:
            job_id = str(job["_id"])
            name = job.get("name", "Unknown")
            domains = job.get("domains", [])
            claimed_scraped = job.get("businesses_scraped", 0)
            
            if domains:
                domain = domains[0]  # Get first domain
                
                # Count actual businesses in database for this domain
                actual_count = await businesses_collection.count_documents({"domain": domain})
                
                # Calculate mismatch
                difference = claimed_scraped - actual_count
                
                if difference > 0:
                    print(f"📊 Fixing {name}: {claimed_scraped:,} → {actual_count:,} (-{difference:,})")
                    
                    # Update job with correct counts
                    await jobs_collection.update_one(
                        {"_id": job["_id"]},
                        {
                            "$set": {
                                "businesses_scraped": actual_count,
                                "fixed_at": datetime.utcnow(),
                                "fix_reason": "auto_corrected_count_mismatch"
                            }
                        }
                    )
                    fixed_count += 1
                    
        print(f"\n✅ COMPLETED: Fixed {fixed_count} jobs")
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        await fix_all_jobs_automatically()
    else:
        await fix_business_count_mismatch()

if __name__ == "__main__":
    print("🔧 Business Count Mismatch Fixer")
    print("================================")
    print("This script fixes the mismatch between job table counts and actual database content")
    print("Usage:")
    print("  python3 fix_business_count_mismatch.py        # Interactive mode")
    print("  python3 fix_business_count_mismatch.py auto   # Automatic mode")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🚫 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
