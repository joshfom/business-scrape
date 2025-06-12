#!/usr/bin/env python3
"""
Test script to debug the full workflow 
"""
import asyncio
import aiohttp
import sys
import os

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from scrapers.base_scraper import YelloScraper
from models.schemas import BusinessData

async def test_full_workflow():
    """Test the full workflow: get URLs -> scrape details"""
    
    page_url = "https://bahrainyellow.com/location/aali"
    domain = 'https://bahrainyellow.com'
    
    async with aiohttp.ClientSession() as session:
        print("Testing full workflow...")
        
        scraper = YelloScraper(domain, session)
        
        # Step 1: Get business URLs
        print(f"\n1. Getting business URLs from: {page_url}")
        business_urls, has_next = await scraper.get_business_listings(page_url, 1)
        print(f"   Found {len(business_urls)} URLs")
        
        # Step 2: Test scraping first 3 businesses
        print(f"\n2. Testing business detail scraping for first 3 businesses...")
        
        # Test with semaphore like the real workflow
        semaphore = asyncio.Semaphore(3)  # 3 concurrent requests
        
        async def scrape_with_semaphore(business_url):
            async with semaphore:
                try:
                    print(f"   Starting: {business_url}")
                    business_data = await scraper.scrape_business_details(business_url)
                    if business_data:
                        print(f"   ✅ Success: {business_data.name}")
                        return business_data
                    else:
                        print(f"   ❌ Failed: No data returned")
                        return None
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    return None
                finally:
                    await asyncio.sleep(0.5)  # Small delay
        
        # Test first 3 URLs
        test_urls = business_urls[:3]
        tasks = [asyncio.create_task(scrape_with_semaphore(url)) for url in test_urls]
        
        print(f"\n3. Running {len(tasks)} tasks concurrently...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"\n4. Results analysis:")
        successful_scrapes = 0
        for i, result in enumerate(results):
            print(f"   Task {i+1}:")
            print(f"     Type: {type(result)}")
            if isinstance(result, BusinessData):
                print(f"     ✅ BusinessData: {result.name}")
                successful_scrapes += 1
            elif isinstance(result, Exception):
                print(f"     ❌ Exception: {result}")
            elif result is None:
                print(f"     ❌ None result")
            else:
                print(f"     ❓ Other: {result}")
        
        print(f"\n5. Summary:")
        print(f"   Total tasks: {len(tasks)}")
        print(f"   Successful scrapes: {successful_scrapes}")
        print(f"   Success rate: {successful_scrapes}/{len(tasks)} = {successful_scrapes/len(tasks)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_full_workflow())
