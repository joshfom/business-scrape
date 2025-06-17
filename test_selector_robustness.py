#!/usr/bin/env python3
"""
Test script to verify company selector robustness across different domain formats
"""
import asyncio
import aiohttp
import sys
import os
from bs4 import BeautifulSoup

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from scrapers.base_scraper import YelloScraper

async def test_company_selector_robustness():
    """Test company URL extraction for multiple domain formats"""
    
    # Test URLs from different domains that might have different structures
    test_cases = [
        {
            "name": "UAE (yello.ae)",
            "domain": "https://www.yello.ae",
            "url": "https://www.yello.ae/location/abu-dhabi/2"
        },
        {
            "name": "Suriname (surinamyp.com)", 
            "domain": "https://www.surinamyp.com",
            "url": "https://www.surinamyp.com/location/Paramaribo"
        },
        {
            "name": "Bahrain (bahrainyellow.com)",
            "domain": "https://www.bahrainyellow.com", 
            "url": "https://www.bahrainyellow.com/location/aali"
        },
        {
            "name": "Pakistan (businesslist.pk)",
            "domain": "https://www.businesslist.pk",
            "url": "https://www.businesslist.pk/location/karachi"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            print(f"\n{'='*80}")
            print(f"Testing: {test_case['name']}")
            print(f"URL: {test_case['url']}")
            print('='*80)
            
            try:
                scraper = YelloScraper(test_case['domain'], session)
                business_urls, has_next = await scraper.get_business_listings(test_case['url'], 1)
                
                print(f"✅ Found {len(business_urls)} business URLs")
                print(f"   Has next page: {has_next}")
                
                if business_urls:
                    print("   Sample URLs (first 3):")
                    for i, url in enumerate(business_urls[:3]):
                        print(f"   {i+1}. {url}")
                        
                    # Analyze the HTML structure for debugging
                    print(f"\n   Analyzing HTML structure for {test_case['name']}:")
                    async with session.get(test_case['url'], headers=scraper.get_headers()) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Count different types of company containers
                            company_divs = soup.select('div.company')
                            company_divs_with_img = soup.select('div.company.with_img')
                            h3_links = soup.select('div.company h3 a[href^="/company/"]')
                            header_links = soup.select('div.company .company_header a[href^="/company/"]')
                            all_company_links = soup.select('div.company a[href^="/company/"]')
                            
                            print(f"     Company divs: {len(company_divs)}")
                            print(f"     Company divs with images: {len(company_divs_with_img)}")
                            print(f"     H3 company links: {len(h3_links)}")
                            print(f"     Header company links: {len(header_links)}")
                            print(f"     All company links in divs: {len(all_company_links)}")
                            
                            # Check for unique company URLs to detect duplicates
                            unique_company_urls = set()
                            for link in all_company_links:
                                href = link.get('href')
                                if href:
                                    unique_company_urls.add(href)
                            print(f"     Unique company URLs: {len(unique_company_urls)}")
                            
                        else:
                            print(f"     Failed to fetch for analysis: {response.status}")
                else:
                    print("❌ No business URLs found")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                # Don't print full traceback to keep output clean
                print(f"   Exception type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_company_selector_robustness())
