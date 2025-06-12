#!/usr/bin/env python3
"""
Test script to check database connection and business data
"""
import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from models.database import database
from config import settings

async def test_database_connection():
    """Test database connection and check businesses"""
    try:
        # Test direct MongoDB connection
        print("Testing direct MongoDB connection...")
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        businesses_collection = db.businesses
        
        # Count businesses
        count = await businesses_collection.count_documents({})
        print(f"✅ Direct connection successful")
        print(f"Total businesses in database: {count}")
        
        # Test application database connection
        print("\nTesting application database connection...")
        await database.connect_db()
        app_db = database.get_database()
        app_businesses = app_db.businesses
        
        app_count = await app_businesses.count_documents({})
        print(f"✅ Application connection successful")
        print(f"Total businesses via app database: {app_count}")
        
        # Get sample businesses
        businesses = await businesses_collection.find({}).limit(5).to_list(5)
        print(f"\nSample businesses ({len(businesses)} found):")
        
        for i, business in enumerate(businesses, 1):
            print(f"\nBusiness {i}:")
            print(f"  Name: {business.get('name', 'N/A')}")
            print(f"  City: {business.get('city', 'N/A')}")
            print(f"  Domain: {business.get('domain', 'N/A')}")
            print(f"  URL: {business.get('page_url', 'N/A')}")
            print(f"  Scraped At: {business.get('scraped_at', 'N/A')}")
            
        # Test insertion
        print("\nTesting data insertion...")
        test_business = {
            "name": "Test Business",
            "city": "Test City",
            "country": "Test Country",
            "domain": "test.com",
            "page_url": "https://test.com/business/test",
            "scraped_at": "2024-01-01T00:00:00Z"
        }
        
        try:
            result = await businesses_collection.insert_one(test_business)
            print(f"✅ Test insertion successful: {result.inserted_id}")
            
            # Remove test business
            await businesses_collection.delete_one({"_id": result.inserted_id})
            print("✅ Test cleanup successful")
            
        except Exception as insert_error:
            print(f"❌ Test insertion failed: {insert_error}")
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close connections
        try:
            client.close()
            await database.close_db()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_database_connection())
