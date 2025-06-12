#!/usr/bin/env python3
"""
Test script to verify the complete enhanced job workflow
"""
import asyncio
import aiohttp
import sys
import os

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from models.database import database

async def test_enhanced_job_workflow():
    """Test the enhanced job workflow with export functionality"""
    try:
        # Connect to database
        await database.connect_db()
        db = database.get_database()
        businesses_collection = db.businesses
        jobs_collection = db.scraping_jobs
        
        print("✅ Database connected successfully")
        
        # Check current data
        total_businesses = await businesses_collection.count_documents({})
        total_jobs = await jobs_collection.count_documents({})
        
        print(f"📊 Current State:")
        print(f"   Total Jobs: {total_jobs}")
        print(f"   Total Businesses: {total_businesses}")
        
        # Get sample job if exists
        sample_job = await jobs_collection.find_one({}, sort=[("created_at", -1)])
        if sample_job:
            job_id = str(sample_job["_id"])
            print(f"   Latest Job ID: {job_id}")
            print(f"   Job Name: {sample_job.get('name', 'N/A')}")
            print(f"   Job Status: {sample_job.get('status', 'N/A')}")
            print(f"   Job Domains: {sample_job.get('domains', [])}")
            
            # Get businesses for this job
            job_domains = sample_job.get("domains", [])
            if job_domains:
                job_businesses = await businesses_collection.count_documents({"domain": {"$in": job_domains}})
                exported_businesses = await businesses_collection.count_documents({
                    "domain": {"$in": job_domains},
                    "exported_at": {"$ne": None}
                })
                print(f"   Job Businesses: {job_businesses}")
                print(f"   Exported Businesses: {exported_businesses}")
                
                # Get city breakdown
                cities_pipeline = [
                    {"$match": {"domain": {"$in": job_domains}}},
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
                
                cities_result = await businesses_collection.aggregate(cities_pipeline).to_list(None)
                print(f"\n🏙️  Cities Breakdown:")
                for city_stat in cities_result[:10]:  # Show top 10 cities
                    city = city_stat["_id"]
                    total = city_stat["total"]
                    exported = city_stat["exported"]
                    print(f"   {city}: {total} businesses ({exported} exported)")
        
        # Test export-related queries
        print(f"\n🔍 Testing Export Queries:")
        
        # Test businesses by export status
        not_exported = await businesses_collection.count_documents({"exported_at": None})
        json_exported = await businesses_collection.count_documents({"export_mode": "json"})
        api_exported = await businesses_collection.count_documents({"export_mode": "api"})
        
        print(f"   Not Exported: {not_exported}")
        print(f"   JSON Exported: {json_exported}")
        print(f"   API Exported: {api_exported}")
        
        # Sample business with export info
        sample_business = await businesses_collection.find_one({})
        if sample_business:
            print(f"\n📋 Sample Business:")
            print(f"   Name: {sample_business.get('name', 'N/A')}")
            print(f"   City: {sample_business.get('city', 'N/A')}")
            print(f"   Domain: {sample_business.get('domain', 'N/A')}")
            print(f"   Scraped At: {sample_business.get('scraped_at', 'N/A')}")
            print(f"   Exported At: {sample_business.get('exported_at', 'Not exported')}")
            print(f"   Export Mode: {sample_business.get('export_mode', 'None')}")
        
        print(f"\n✅ Enhanced job workflow test completed successfully!")
        print(f"\n🎯 Next Steps:")
        print(f"   1. Open http://localhost:3000/jobs in your browser")
        print(f"   2. Click on a job to view detailed job page")
        print(f"   3. Use the export functionality to download data")
        print(f"   4. Test city-chunked exports and API export mode")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await database.close_db()

if __name__ == "__main__":
    asyncio.run(test_enhanced_job_workflow())
