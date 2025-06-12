#!/usr/bin/env python3
"""
Test script to debug the database saving issue in scraping service
"""
import asyncio
import aiohttp
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from scrapers.base_scraper import YelloScraper
from models.database import database
from models.schemas import BusinessData
from config import settings

async def test_database_save_workflow():
    """Test the exact database saving workflow used in scraping service"""
    try:
        # Connect to database
        await database.connect_db()
        db = database.get_database()
        businesses_collection = db.businesses
        
        print("✅ Database connected successfully")
        
        # Test URLs
        test_urls = [
            "https://businesslist.pk/company/258988/dlb-consulting-llc",
            "https://www.bahrainyellow.com/company/21808/Auto_Lines_Repairs_Services"
        ]
        
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(test_urls, 1):
                print(f"\n{'='*60}")
                print(f"Test {i}: {url}")
                print('='*60)
                
                # Determine domain
                if 'businesslist.pk' in url:
                    domain = 'https://businesslist.pk'
                elif 'bahrainyellow.com' in url:
                    domain = 'https://bahrainyellow.com'
                else:
                    continue
                
                try:
                    # Create scraper
                    scraper = YelloScraper(domain, session)
                    
                    # Check if business already exists
                    existing = await businesses_collection.find_one({"page_url": url})
                    if existing:
                        print(f"⚠️  Business already exists in database: {existing.get('name')}")
                        continue
                    
                    # Scrape business details
                    print(f"🔍 Scraping business details...")
                    business_data = await scraper.scrape_business_details(url)
                    
                    if business_data:
                        print(f"✅ Successfully scraped: {business_data.name}")
                        print(f"   City: {business_data.city}")
                        print(f"   Country: {business_data.country}")
                        print(f"   Coordinates: {business_data.coordinates}")
                        
                        # Test database saving (exact same code as scraping service)
                        print(f"💾 Attempting to save to database...")
                        try:
                            # Convert to dict and exclude None _id field to avoid MongoDB duplicate key error
                            business_dict = business_data.model_dump(by_alias=True, exclude_unset=True)
                            if '_id' in business_dict and business_dict['_id'] is None:
                                del business_dict['_id']
                            
                            result = await businesses_collection.insert_one(business_dict)
                            print(f"✅ SAVED SUCCESSFULLY: ID = {result.inserted_id}")
                            
                            # Verify it was saved
                            saved_business = await businesses_collection.find_one({"_id": result.inserted_id})
                            if saved_business:
                                print(f"✅ VERIFICATION: Business found in database")
                                print(f"   Saved name: {saved_business.get('name')}")
                            else:
                                print(f"❌ VERIFICATION FAILED: Business not found after save")
                                
                        except Exception as db_error:
                            print(f"❌ DATABASE SAVE ERROR: {db_error}")
                            import traceback
                            traceback.print_exc()
                            
                    else:
                        print(f"❌ Failed to scrape business details")
                        
                except Exception as e:
                    print(f"❌ ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                    
        # Final database count
        final_count = await businesses_collection.count_documents({})
        print(f"\n📊 Final database count: {final_count} businesses")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await database.close_db()

if __name__ == "__main__":
    asyncio.run(test_database_save_workflow())
