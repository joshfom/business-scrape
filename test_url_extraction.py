#!/usr/bin/env python3
"""
Test script to debug business URL extraction from listing pages
"""
import asyncio
import aiohttp
import sys
import os
from bs4 import BeautifulSoup

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from scrapers.base_scraper import YelloScraper

async def test_business_url_extraction():
    """Test business URL extraction from listing pages"""
    
    # Test URLs for listing pages
    test_pages = [
        "https://bahrainyellow.com/location/aali",  # Bahrain - first page
        "https://businesslist.pk/location/abbottabad",  # Pakistan - first page
    ]
    
    async with aiohttp.ClientSession() as session:
        for page_url in test_pages:
            print(f"\n{'='*60}")
            print(f"Testing business URL extraction from: {page_url}")
            print('='*60)
            
            # Extract domain from URL
            if 'bahrainyellow.com' in page_url:
                domain = 'https://bahrainyellow.com'
            elif 'businesslist.pk' in page_url:
                domain = 'https://businesslist.pk'
            else:
                continue
                
            try:
                scraper = YelloScraper(domain, session)
                business_urls, has_next = await scraper.get_business_listings(page_url, 1)
                
                print(f"✅ Found {len(business_urls)} business URLs")
                print(f"   Has next page: {has_next}")
                
                if business_urls:
                    print("   Sample URLs:")
                    for i, url in enumerate(business_urls[:3]):  # Show first 3
                        print(f"   {i+1}. {url}")
                else:
                    print("❌ No business URLs found - checking HTML structure...")
                    
                    # Get raw HTML and analyze structure
                    async with session.get(page_url, headers=scraper.get_headers()) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Look for different potential selectors
                            selectors_to_try = [
                                'div.company h3 a[href^="/company/"]',  # Current selector
                                'h3 a[href*="/company/"]',  # Less specific
                                'a[href*="/company/"]',  # Even less specific
                                'div.company a',  # Any link in company div
                                'h3 a',  # Any link in h3
                            ]
                            
                            for selector in selectors_to_try:
                                links = soup.select(selector)
                                print(f"   Selector '{selector}': {len(links)} matches")
                                if links:
                                    for i, link in enumerate(links[:2]):  # Show first 2
                                        href = link.get('href', 'NO_HREF')
                                        text = link.get_text().strip()[:50]
                                        print(f"     {i+1}. {href} - {text}")
                        else:
                            print(f"   Failed to fetch page: {response.status}")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_business_url_extraction())
