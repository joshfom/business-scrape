#!/usr/bin/env python3
"""
Test script to debug business detail extraction
"""
import asyncio
import aiohttp
import sys
import os

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from scrapers.base_scraper import YelloScraper

async def test_extraction():
    """Test business detail extraction for specific URLs"""
    
    # Test URLs from different domains
    test_urls = [
        "https://www.bahrainyellow.com/company/21808/Auto_Lines_Repairs_Services",  # Bahrain
        "https://businesslist.pk/company/258988/dlb-consulting-llc",  # Pakistan
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in test_urls:
            print(f"\n{'='*60}")
            print(f"Testing extraction for: {url}")
            print('='*60)
            
            # Extract domain from URL
            if 'bahrainyellow.com' in url:
                domain = 'https://bahrainyellow.com'
            elif 'businesslist.pk' in url:
                domain = 'https://businesslist.pk'
            else:
                continue
                
            try:
                scraper = YelloScraper(domain, session)
                business_data = await scraper.scrape_business_details(url)
                
                if business_data:
                    print(f"✅ SUCCESS: Extracted business data")
                    print(f"   Name: {business_data.name}")
                    print(f"   City: {business_data.city}")
                    print(f"   Country: {business_data.country}")
                    print(f"   Phone: {business_data.phone}")
                    print(f"   Address: {business_data.address}")
                    print(f"   Coordinates: {business_data.coordinates}")
                    print(f"   Category: {business_data.category}")
                else:
                    print(f"❌ FAILED: No business data extracted")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_extraction())
