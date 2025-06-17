#!/usr/bin/env python3
"""
Test alternative URLs for domains that failed
"""
import asyncio
import aiohttp
import sys
import os
from bs4 import BeautifulSoup

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from scrapers.base_scraper import YelloScraper

async def test_alternative_urls():
    """Test alternative URLs for failed domains"""
    
    # Test alternative URLs for failed domains
    test_cases = [
        {
            "name": "Brazil - Alternative URLs",
            "domain": "https://www.brazilyello.com",
            "urls": [
                "https://www.brazilyello.com/location/rio-de-janeiro",
                "https://www.brazilyello.com/location/brasilia",
                "https://www.brazilyello.com/browse-business-cities",
                "https://www.brazilyello.com"
            ]
        },
        {
            "name": "Philippines - Alternative URLs",
            "domain": "https://www.businesslist.ph",
            "urls": [
                "https://www.businesslist.ph/location/quezon-city",
                "https://www.businesslist.ph/location/cebu",
                "https://www.businesslist.ph/browse-business-cities",
                "https://www.businesslist.ph"
            ]
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            print(f"\n{'='*80}")
            print(f"Testing: {test_case['name']}")
            print('='*80)
            
            scraper = YelloScraper(test_case['domain'], session)
            
            for url in test_case['urls']:
                print(f"\nTrying: {url}")
                try:
                    async with session.get(url, headers=scraper.get_headers()) as response:
                        print(f"   Status: {response.status}")
                        
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Check page title
                            title = soup.select_one('title')
                            if title:
                                print(f"   Title: {title.get_text().strip()[:100]}")
                            
                            # Look for city/location links
                            location_links = soup.select('a[href*="/location/"]')
                            print(f"   Location links found: {len(location_links)}")
                            
                            if location_links:
                                print("   Sample locations:")
                                for i, link in enumerate(location_links[:5]):
                                    href = link.get('href')
                                    text = link.get_text().strip()
                                    print(f"     {i+1}. {href} - {text}")
                            
                            # If this looks like a listing page, test business extraction
                            if '/location/' in url:
                                business_urls, has_next = await scraper.get_business_listings(url, 1)
                                print(f"   ✅ Found {len(business_urls)} business URLs")
                                if business_urls:
                                    print("   Sample business URLs:")
                                    for i, burl in enumerate(business_urls[:3]):
                                        print(f"     {i+1}. {burl}")
                            
                        elif response.status in [403, 404]:
                            print(f"   ❌ Access denied/not found")
                        else:
                            print(f"   ⚠️  Unexpected status: {response.status}")
                            
                except Exception as e:
                    print(f"   ❌ ERROR: {e}")

# Also test if these domains use different patterns
async def test_domain_availability():
    """Check if domains are accessible and what structure they use"""
    
    domains = [
        "https://www.brazilyello.com",
        "https://www.businesslist.ph"
    ]
    
    async with aiohttp.ClientSession() as session:
        print(f"\n{'='*80}")
        print("Testing domain accessibility")
        print('='*80)
        
        for domain in domains:
            print(f"\nTesting: {domain}")
            try:
                async with session.get(domain, timeout=10) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Check if it's a Yello-style site
                        yello_indicators = [
                            soup.select('a[href*="/location/"]'),
                            soup.select('a[href*="/company/"]'),
                            soup.select('div.company'),
                            soup.select('a[href*="/browse-business-cities"]')
                        ]
                        
                        print(f"   Location links: {len(yello_indicators[0])}")
                        print(f"   Company links: {len(yello_indicators[1])}")
                        print(f"   Company divs: {len(yello_indicators[2])}")
                        print(f"   Browse cities link: {len(yello_indicators[3])}")
                        
                        # Check page content
                        title = soup.select_one('title')
                        if title:
                            print(f"   Title: {title.get_text().strip()[:100]}")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_alternative_urls())
    asyncio.run(test_domain_availability())
