#!/usr/bin/env python3
"""
Test script to verify company selector works across specified domains
"""
import asyncio
import aiohttp
import sys
import os
from bs4 import BeautifulSoup

# Add the backend directory to Python path
sys.path.append('/Users/joshua/Code/business-scrape/backend')

from scrapers.base_scraper import YelloScraper

async def test_specific_domains():
    """Test company URL extraction for specified domains"""
    
    # Test URLs for the requested domains
    test_cases = [
        {
            "name": "Kenya (businesslist.co.ke)",
            "domain": "https://www.businesslist.co.ke",
            "url": "https://www.businesslist.co.ke/location/nairobi"
        },
        {
            "name": "Suriname (surinamyp.com)", 
            "domain": "https://www.surinamyp.com",
            "url": "https://www.surinamyp.com/location/Paramaribo"
        },
        {
            "name": "Brazil (brazilyello.com)",
            "domain": "https://www.brazilyello.com",
            "url": "https://www.brazilyello.com/location/sao-paulo"
        },
        {
            "name": "Nigeria (businesslist.com.ng)",
            "domain": "https://www.businesslist.com.ng",
            "url": "https://www.businesslist.com.ng/location/lagos"
        },
        {
            "name": "Philippines (businesslist.ph)",
            "domain": "https://www.businesslist.ph",
            "url": "https://www.businesslist.ph/location/manila"
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
                    print("   Sample URLs (first 5):")
                    for i, url in enumerate(business_urls[:5]):
                        print(f"   {i+1}. {url}")
                        
                    # Analyze the HTML structure for debugging
                    print(f"\n   Analyzing HTML structure:")
                    async with session.get(test_case['url'], headers=scraper.get_headers()) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Test all our selectors
                            selectors = [
                                ('Primary (h3)', 'div.company h3 a[href^="/company/"]'),
                                ('Header', 'div.company .company_header a[href^="/company/"]'),
                                ('All company', 'div.company a[href^="/company/"]'),
                                ('Page-wide', 'a[href^="/company/"]')
                            ]
                            
                            print(f"     Company divs: {len(soup.select('div.company'))}")
                            
                            for name, selector in selectors:
                                links = soup.select(selector)
                                unique_hrefs = set()
                                for link in links:
                                    href = link.get('href')
                                    if href:
                                        unique_hrefs.add(href)
                                print(f"     {name}: {len(links)} links, {len(unique_hrefs)} unique")
                            
                            # Check what the actual structure looks like
                            company_divs = soup.select('div.company')[:3]  # First 3 companies
                            print(f"\n   Sample company structure (first 3):")
                            for i, div in enumerate(company_divs, 1):
                                # Look for company links
                                company_links = div.select('a[href^="/company/"]')
                                h3_links = div.select('h3 a[href^="/company/"]')
                                header_links = div.select('.company_header a[href^="/company/"]')
                                
                                print(f"     Company {i}:")
                                print(f"       Total company links: {len(company_links)}")
                                print(f"       H3 links: {len(h3_links)}")
                                print(f"       Header links: {len(header_links)}")
                                
                                if company_links:
                                    print(f"       First link: {company_links[0].get('href', 'NO_HREF')}")
                                    print(f"       Link text: {company_links[0].get_text().strip()[:50]}")
                                    print(f"       Link classes: {company_links[0].get('class', [])}")
                            
                        else:
                            print(f"     Failed to fetch for analysis: {response.status}")
                else:
                    print("❌ No business URLs found - analyzing why...")
                    
                    # If no URLs found, let's see what's on the page
                    async with session.get(test_case['url'], headers=scraper.get_headers()) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            print("   Looking for alternative patterns:")
                            
                            # Check for different URL patterns
                            patterns = [
                                'a[href*="/company/"]',
                                'a[href*="/business/"]', 
                                'a[href*="/listing/"]',
                                'a[href*="/profile/"]'
                            ]
                            
                            for pattern in patterns:
                                links = soup.select(pattern)
                                if links:
                                    print(f"     {pattern}: {len(links)} links found")
                                    if links:
                                        print(f"       Sample: {links[0].get('href', 'NO_HREF')}")
                            
                            # Check page title and content to see if it's the right page
                            title = soup.select_one('title')
                            if title:
                                print(f"   Page title: {title.get_text().strip()}")
                            
                            # Look for any indication this is a business listing page
                            business_indicators = soup.select('div[class*="company"], div[class*="business"], div[class*="listing"]')
                            print(f"   Business-like divs: {len(business_indicators)}")
                            
                        else:
                            print(f"   Failed to analyze page: {response.status}")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                print(f"   Exception type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_specific_domains())
