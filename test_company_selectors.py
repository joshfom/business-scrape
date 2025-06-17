#!/usr/bin/env python3
"""
Test script to verify company selector works for both UAE and Suriname formats
"""
import asyncio
import aiohttp
import sys
import os
from bs4 import BeautifulSoup

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from scrapers.base_scraper import YelloScraper

async def test_company_selectors():
    """Test company URL extraction for both formats"""
    
    # Test URLs from your examples
    test_cases = [
        {
            "name": "UAE (yello.ae)",
            "domain": "https://www.yello.ae",
            "url": "https://www.yello.ae/location/abu-dhabi/2",
            "expected_pattern": "/company/358857/point-to-point-advertising-designs"
        },
        {
            "name": "Suriname (surinamyp.com)", 
            "domain": "https://www.surinamyp.com",
            "url": "https://www.surinamyp.com/location/Paramaribo",
            "expected_pattern": "/company/2959/Business_Directory_Suriname"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            print(f"\n{'='*60}")
            print(f"Testing: {test_case['name']}")
            print(f"URL: {test_case['url']}")
            print('='*60)
            
            try:
                scraper = YelloScraper(test_case['domain'], session)
                business_urls, has_next = await scraper.get_business_listings(test_case['url'], 1)
                
                print(f"✅ Found {len(business_urls)} business URLs")
                print(f"   Has next page: {has_next}")
                
                # Check if expected pattern is found
                expected_found = any(test_case['expected_pattern'] in url for url in business_urls)
                if expected_found:
                    print(f"✅ Expected pattern '{test_case['expected_pattern']}' found!")
                else:
                    print(f"❌ Expected pattern '{test_case['expected_pattern']}' NOT found")
                
                if business_urls:
                    print("   Sample URLs (first 5):")
                    for i, url in enumerate(business_urls[:5]):
                        print(f"   {i+1}. {url}")
                        
                    # Test different selector patterns manually
                    print("\n   Testing different selectors manually:")
                    async with session.get(test_case['url'], headers=scraper.get_headers()) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Test various selectors
                            selectors = [
                                'div.company h3 a[href^="/company/"]',  # Original
                                'div.company a[href^="/company/"]',     # Any company link
                                'div.company .company_header a[href^="/company/"]',  # Header links
                                'h3 a[href*="/company/"]',             # Any h3 company link
                                'a[href*="/company/"]',                # Any company link anywhere
                            ]
                            
                            for selector in selectors:
                                links = soup.select(selector)
                                unique_links = set()
                                for link in links:
                                    href = link.get('href')
                                    if href:
                                        unique_links.add(href)
                                print(f"     '{selector}': {len(unique_links)} unique URLs")
                                
                else:
                    print("❌ No business URLs found")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_company_selectors())
