#!/usr/bin/env python3
"""
Script to investigate the mismatch between job table counts and actual database content
"""

import asyncio
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from config import settings

async def investigate_data_mismatch():
    """Compare job table data with actual database content"""
    
    print("🔍 INVESTIGATING DATA MISMATCH")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        
        # Get collections
        jobs_collection = db.scraping_jobs
        businesses_collection = db.businesses
        
        print("\n📊 JOB TABLE ANALYSIS")
        print("-" * 30)
        
        # Get all jobs
        jobs = await jobs_collection.find({}).to_list(None)
        
        for job in jobs:
            job_id = str(job["_id"])
            name = job.get("name", "Unknown")
            status = job.get("status", "unknown")
            total_businesses = job.get("total_businesses", 0)
            businesses_scraped = job.get("businesses_scraped", 0)
            domains = job.get("domains", [])
            
            print(f"\nJob: {name} ({job_id})")
            print(f"  Status: {status}")
            print(f"  Domains: {domains}")
            print(f"  Total Businesses (claimed): {total_businesses:,}")
            print(f"  Businesses Scraped (claimed): {businesses_scraped:,}")
            
            # Check actual database for this domain
            if domains:
                domain = domains[0]  # Get first domain
                
                # Count businesses in database for this domain
                actual_count = await businesses_collection.count_documents({"domain": domain})
                print(f"  Actual DB Count: {actual_count:,}")
                
                # Calculate mismatch
                claimed_scraped = businesses_scraped
                difference = claimed_scraped - actual_count
                
                if difference > 0:
                    print(f"  ⚠️  MISMATCH: Job claims {difference:,} more than DB has!")
                elif difference < 0:
                    print(f"  ✅ DB has {abs(difference):,} more than job claims")
                else:
                    print(f"  ✅ Perfect match!")
        
        print("\n📊 DATABASE CONTENT ANALYSIS")
        print("-" * 30)
        
        # Get total count
        total_businesses = await businesses_collection.count_documents({})
        print(f"Total businesses in database: {total_businesses:,}")
        
        # Get breakdown by domain
        print("\nBreakdown by domain:")
        pipeline = [
            {"$group": {"_id": "$domain", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        domain_stats = await businesses_collection.aggregate(pipeline).to_list(None)
        for stat in domain_stats:
            domain = stat["_id"]
            count = stat["count"]
            print(f"  {domain}: {count:,} businesses")
        
        print("\n🔍 RECENT BUSINESSES SAMPLE")
        print("-" * 30)
        
        # Get recent businesses to see what's actually being saved
        recent_businesses = await businesses_collection.find({}).sort("_id", -1).limit(5).to_list(5)
        
        for i, business in enumerate(recent_businesses, 1):
            name = business.get("name", "Unknown")
            domain = business.get("domain", "Unknown")
            city = business.get("city", "Unknown")
            scraped_at = business.get("scraped_at", "Unknown")
            
            print(f"  {i}. {name}")
            print(f"     Domain: {domain}")
            print(f"     City: {city}")
            print(f"     Scraped: {scraped_at}")
        
        print("\n🔍 DUPLICATE CHECK")
        print("-" * 30)
        
        # Check for duplicates
        pipeline = [
            {"$group": {"_id": "$page_url", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        duplicates = await businesses_collection.aggregate(pipeline).to_list(5)
        
        if duplicates:
            print("Found duplicates (by page_url):")
            for dup in duplicates:
                url = dup["_id"]
                count = dup["count"]
                print(f"  {url}: {count} copies")
        else:
            print("✅ No duplicates found (by page_url)")
        
        # Check if businesses have proper scraped_at timestamps
        print("\n🔍 TIMESTAMP ANALYSIS")
        print("-" * 30)
        
        with_scraped_at = await businesses_collection.count_documents({"scraped_at": {"$exists": True}})
        without_scraped_at = await businesses_collection.count_documents({"scraped_at": {"$exists": False}})
        
        print(f"Businesses with scraped_at: {with_scraped_at:,}")
        print(f"Businesses without scraped_at: {without_scraped_at:,}")
        
        if without_scraped_at > 0:
            print("⚠️  Some businesses missing scraped_at timestamp")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate_data_mismatch())
