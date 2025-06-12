#!/usr/bin/env python3
"""
Script to test database connection and check businesses
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_database():
    """Test database connection and check businesses"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        db = client.business_scraper
        businesses_collection = db.businesses
        
        # Count businesses
        count = await businesses_collection.count_documents({})
        print(f"Total businesses in database: {count}")
        
        # Get all businesses
        businesses = await businesses_collection.find({}).to_list(10)
        print(f"\nFound {len(businesses)} businesses:")
        
        for i, business in enumerate(businesses, 1):
            print(f"\nBusiness {i}:")
            print(f"  Name: {business.get('name')}")
            print(f"  Address: {business.get('address')}")
            print(f"  Coordinates: {business.get('coordinates')}")
            print(f"  URL: {business.get('page_url')}")
            print(f"  Domain: {business.get('domain')}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_database())
