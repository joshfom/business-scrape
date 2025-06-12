from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import requests
import asyncio
import aiohttp
import re
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from models.schemas import BusinessData, CityData
from config import settings

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base scraper class for all Yello domain scrapers"""
    
    def __init__(self, domain: str, session: aiohttp.ClientSession):
        self.domain = domain
        self.session = session
        self.ua = UserAgent()
        
    def get_headers(self) -> Dict[str, str]:
        """Get randomized headers for requests"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    @abstractmethod
    async def get_cities(self) -> List[CityData]:
        """Get list of all cities from the domain"""
        pass
    
    @abstractmethod
    async def get_business_listings(self, city_url: str, page: int = 1) -> Tuple[List[str], bool]:
        """Get business listing URLs from city page. Returns (urls, has_next_page)"""
        pass
    
    @abstractmethod
    async def scrape_business_details(self, business_url: str) -> Optional[BusinessData]:
        """Scrape detailed business information from business page"""
        pass

class YelloScraper(BaseScraper):
    """Universal scraper for all Yello business directory websites"""
    
    def __init__(self, domain: str, session: aiohttp.ClientSession):
        super().__init__(domain, session)
        # Extract the base domain and construct proper URL
        if self.domain.startswith(('http://', 'https://')):
            self.base_url = self.domain
            self.domain_name = self.domain.replace('https://', '').replace('http://', '')
        else:
            self.base_url = f"https://{self.domain}"
            self.domain_name = self.domain
    
    async def get_cities(self) -> List[CityData]:
        """Get all cities by discovering them from the main navigation or using common city patterns"""
        try:
            # First try the browse-business-cities endpoint
            cities = await self._get_cities_from_browse_page()
            if cities:
                return cities
            
            # Then try the homepage navigation
            async with self.session.get(self.base_url, headers=self.get_headers()) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch homepage from {self.base_url}: {response.status}")
                    return await self._get_common_cities()
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                cities = []
                
                # Look for city links in various common patterns
                city_selectors = [
                    'a[href*="/location/"]',  # Most common pattern
                    'a[href*="/city/"]',      # Alternative pattern
                    'select[name="location"] option',  # Dropdown options
                    '.location-link',         # Class-based
                ]
                
                for selector in city_selectors:
                    city_links = soup.select(selector)
                    if city_links:
                        for link in city_links[:50]:  # Limit to 50 cities to avoid overwhelming
                            if link.name == 'option':
                                city_name = link.get_text().strip()
                                if city_name and city_name.lower() not in ['all', 'select', 'choose']:
                                    href = f"/location/{city_name.lower().replace(' ', '-')}"
                            else:
                                href = link.get('href')
                                city_name = link.get_text().strip()
                            
                            if href and '/location/' in href and city_name:
                                cities.append(CityData(
                                    name=city_name,
                                    url=urljoin(self.base_url, href),
                                    business_count=0,  # Will be determined when scraping
                                    domain=self.domain_name
                                ))
                        break  # Stop after finding cities with first successful selector
                
                if cities:
                    logger.info(f"Found {len(cities)} cities for {self.domain_name}")
                    return cities
                
                # If no cities found, fall back to common cities
                return await self._get_common_cities()
                
        except Exception as e:
            logger.error(f"Error fetching cities from {self.domain_name}: {e}")
            return await self._get_common_cities()

    async def _get_cities_from_browse_page(self) -> List[CityData]:
        """Try to get cities from browse-business-cities endpoint"""
        try:
            browse_url = f"{self.base_url}/browse-business-cities"
            async with self.session.get(browse_url, headers=self.get_headers()) as response:
                if response.status != 200:
                    logger.debug(f"Browse cities page not found for {self.domain_name}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                cities = []
                # Look for city links on the browse page
                city_links = soup.select('a[href*="/location/"]')
                
                for link in city_links:
                    href = link.get('href')
                    city_text = link.get_text().strip()
                    
                    # Extract city name and business count
                    if city_text and href and '/location/' in href:
                        # Parse city name and count (e.g., "Karachi 68,340")
                        match = re.match(r'^([^0-9]+)\s*(\d[\d,]*)?$', city_text)
                        if match:
                            city_name = match.group(1).strip()
                            business_count_str = match.group(2) or '0'
                            business_count = int(business_count_str.replace(',', '')) if business_count_str else 0
                            
                            cities.append(CityData(
                                name=city_name,
                                url=urljoin(self.base_url, href),
                                business_count=business_count,
                                domain=self.domain_name
                            ))
                
                if cities:
                    logger.info(f"Found {len(cities)} cities from browse page for {self.domain_name}")
                    return cities
                
        except Exception as e:
            logger.debug(f"Error fetching from browse cities page for {self.domain_name}: {e}")
        
        return []
    
    async def _get_common_cities(self) -> List[CityData]:
        """Fallback method to get common cities based on country/region"""
        # Map common city patterns by domain
        common_cities_map = {
            # UAE
            'yello.ae': ['Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman', 'Ras Al Khaimah', 'Fujairah', 'Umm Al Quwain'],
            
            # India
            'yelu.in': ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad'],
            
            # Ghana
            'ghanayellow.com': ['Accra', 'Kumasi', 'Tamale', 'Cape Coast', 'Sekondi-Takoradi', 'Sunyani', 'Ho'],
            
            # Pakistan - Updated with all 69 cities from browse-business-cities
            'businesslist.pk': [
                'Karachi', 'Lahore', 'Faisalabad', 'Islamabad', 'Rawalpindi', 'Gujranwala', 'Sialkot',
                'Multan', 'Peshawar', 'Hyderabad', 'Quetta', 'Bahawalpur', 'Gujrat', 'Abbottabad',
                'Rawalpini', 'Sargodha', 'Kasur', 'Sukkur', 'Sahiwal', 'Larkana', 'Jhelum', 'Daska',
                'Okara', 'Wazirabad', 'Jhang', 'Mardan', 'Chiniot', 'Rahim Yar Khan', 'Chakwal',
                'Hafizabad', 'Mandi Bahauddin', 'Taxila', 'Swabi', 'Vehari', 'Wah Cantonment',
                'Nowshera', 'Nawabshah', 'Khairpur', 'Burewala', 'Kamoke', 'Kohat', 'Dera Ghazi Khan',
                'Muridke', 'Toba Tek Singh', 'Dadu', 'Chishtian', 'Timergara', 'Kamalia', 'Khanewal',
                'Mingora', 'Mirpur Khas', 'Gojra', 'Khushab', 'Pakpattan', 'Bahawalnagar', 'Shekhupura',
                'Sadiqabad', 'Dera Ismail Khan', 'Muzaffargarh', 'Ahmadpur East', 'Chakdara', 'Chaman',
                'Jaranwala', 'Khanpur', 'Kot Adu', 'Shikarpur', 'Tando Allahyar', 'Jacobabad', 'Khuzdar'
            ],
            
            # Nigeria
            'businesslist.com.ng': ['Lagos', 'Abuja', 'Kano', 'Ibadan', 'Port Harcourt', 'Benin City', 'Maiduguri'],
            
            # Kenya
            'businesslist.co.ke': ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 'Malindi'],
            
            # South Africa
            'yellosa.co.za': ['Johannesburg', 'Cape Town', 'Durban', 'Pretoria', 'Port Elizabeth', 'Bloemfontein'],
            
            # UK
            'yelu.uk': ['London', 'Manchester', 'Birmingham', 'Liverpool', 'Leeds', 'Sheffield', 'Bristol'],
            
            # Singapore
            'yelu.sg': ['Central Singapore', 'North Singapore', 'South Singapore', 'East Singapore', 'West Singapore'],
            
            # Australia
            'australiayp.com': ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide', 'Canberra', 'Darwin'],
        }
        
        cities_list = common_cities_map.get(self.domain_name, ['Capital', 'Main City', 'Central'])
        
        cities = []
        for city_name in cities_list:
            city_url = f"{self.base_url}/location/{city_name.lower().replace(' ', '-')}"
            cities.append(CityData(
                name=city_name,
                url=city_url,
                business_count=0,
                domain=self.domain_name
            ))
        
        logger.info(f"Using {len(cities)} common cities for {self.domain_name}")
        return cities
    
    async def get_business_listings(self, city_url: str, page: int = 1) -> Tuple[List[str], bool]:
        """Get business listing URLs from city page"""
        if page > 1:
            city_url = f"{city_url}/{page}"
            
        try:
            async with self.session.get(city_url, headers=self.get_headers()) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch page {page} from {city_url}: {response.status}")
                    return [], False
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                business_urls = []
                # Find business links in company divs
                business_links = soup.select('div.company h3 a[href^="/company/"]')
                
                for link in business_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        business_urls.append(full_url)
                
                # Check for next page
                has_next = bool(soup.select('a.pages_arrow[rel="next"]'))
                
                logger.debug(f"Found {len(business_urls)} businesses on page {page} of {city_url}")
                return business_urls, has_next
                
        except Exception as e:
            logger.error(f"Error fetching business listings from {city_url} page {page}: {e}")
            return [], False
    
    async def scrape_business_details(self, business_url: str) -> Optional[BusinessData]:
        """Scrape detailed business information"""
        try:
            logger.debug(f"Scraping business details from: {business_url}")
            async with self.session.get(business_url, headers=self.get_headers()) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch business details from {business_url}: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract title
                title_tag = soup.select_one('h1')
                title = title_tag.get_text().strip() if title_tag else ""
                logger.debug(f"Extracted title: {title}")
                
                # Extract breadcrumb info (country, city, category)
                breadcrumb = soup.select('ul[itemtype*="BreadcrumbList"] li span[itemprop="name"]')
                country = breadcrumb[0].get_text().strip() if len(breadcrumb) > 0 else ""
                city = breadcrumb[1].get_text().strip() if len(breadcrumb) > 1 else ""
                category = breadcrumb[2].get_text().strip() if len(breadcrumb) > 2 else ""
                logger.debug(f"Extracted location: {country}, {city}, {category}")
                
                # Extract business name
                name_tag = soup.select_one('div.text#company_name, .company_header h3')
                name = name_tag.get_text().strip() if name_tag else title.split(' - ')[0] if ' - ' in title else title
                logger.debug(f"Extracted name: {name}")
                
                # Extract coordinates from directions link
                coordinates = None
                # Look for Google Maps directions link with coordinates
                directions_link = soup.select_one('a[href*="maps.google.com"][href*="daddr="], a[href*="Get Directions"]')
                if not directions_link:
                    # Try alternative selectors for the directions link
                    directions_link = soup.select_one('.location_links a[href*="maps.google.com"]')
                
                if directions_link:
                    href = directions_link.get('href')
                    if href:
                        # Extract coordinates from the daddr parameter
                        match = re.search(r'daddr=([0-9.-]+),([0-9.-]+)', href)
                        if match:
                            coordinates = {
                                "lat": float(match.group(1)),
                                "lng": float(match.group(2))
                            }
                            logger.debug(f"Extracted coordinates: {coordinates} from {href}")
                        else:
                            logger.debug(f"No coordinates found in directions link: {href}")
                    else:
                        logger.debug("Directions link found but no href attribute")
                
                # Extract contact information
                phone = self._extract_contact_info(soup, 'tel:', 'Phone')
                mobile = self._extract_contact_info(soup, 'tel:', 'Mobile phone')
                fax = self._extract_text_by_label(soup, 'Fax')
                
                # Extract website
                website_link = soup.select_one('div.weblinks a[href*="/redir/"]')
                website = None
                if website_link:
                    website = website_link.get_text().strip()
                
                # Extract address
                address = None
                # Try multiple selectors for address in order of specificity
                address_selectors = [
                    '#company_address',  # Most specific - from your example
                    'div.text.location #company_address',  # Full path
                    'div.info div.text.location #company_address',  # Even more specific
                    '.address',  # Generic class
                    'div:contains("Address:") + div',  # Label-based
                    '.location_links',  # Container
                    'div[id*="address"]',  # Any div with "address" in ID
                    'div.text.location div',  # Any div inside location
                ]
                
                for selector in address_selectors:
                    address_div = soup.select_one(selector)
                    if address_div:
                        address_text = address_div.get_text().strip()
                        # Clean up the address and validate it
                        if address_text and len(address_text) > 5 and not address_text.lower() in ['view map', 'get directions']:
                            # Remove extra whitespace and newlines
                            address = ' '.join(address_text.split())
                            logger.debug(f"Extracted address using selector '{selector}': {address}")
                            break
                
                if not address:
                    # Fallback: look for any text that looks like an address
                    all_text_divs = soup.find_all('div', string=re.compile(r'\w+\s+(St|Street|Rd|Road|Ave|Avenue|Blvd|Boulevard|Al\s+\w+)', re.I))
                    if all_text_divs:
                        address = all_text_divs[0].get_text().strip()
                        logger.debug(f"Extracted address from fallback: {address}")
                
                # Extract working hours
                working_hours = self._extract_working_hours(soup)
                
                # Extract description
                description_div = soup.select_one('div.text.desc, .company_description')
                description = description_div.get_text().strip() if description_div else None
                
                # Extract tags/categories
                tags = []
                tag_links = soup.select('div.tags a[href^="/category/"]')
                for tag_link in tag_links:
                    tag_text = tag_link.get_text().strip()
                    if tag_text:
                        tags.append(tag_text)
                
                # Extract reviews and rating
                reviews_count = 0
                rating = None
                rating_div = soup.select_one('.company_reviews')
                if rating_div:
                    rating_text = rating_div.select_one('.rate')
                    if rating_text:
                        try:
                            rating = float(rating_text.get_text().strip())
                        except ValueError:
                            pass
                    
                    reviews_text = rating_div.get_text()
                    match = re.search(r'(\d+)\s+Reviews?', reviews_text)
                    if match:
                        reviews_count = int(match.group(1))
                
                # Extract establishment year
                established_year = None
                established_text = self._extract_text_by_label(soup, 'Established')
                if established_text:
                    match = re.search(r'(\d{4})', established_text)
                    if match:
                        established_year = int(match.group(1))
                
                # Extract employees
                employees = self._extract_text_by_label(soup, 'Employees')
                
                business_data = BusinessData(
                    title=title,
                    name=name,
                    country=country,
                    city=city,
                    category=category,
                    coordinates=coordinates,
                    phone=phone,
                    mobile=mobile,
                    fax=fax,
                    website=website,
                    address=address,
                    working_hours=working_hours,
                    description=description,
                    tags=tags,
                    reviews_count=reviews_count,
                    rating=rating,
                    established_year=established_year,
                    employees=employees,
                    page_url=business_url,
                    domain=self.domain
                )
                
                logger.debug(f"Successfully scraped business: {name} with coordinates: {coordinates}")
                return business_data
                
        except Exception as e:
            logger.error(f"Error scraping business details from {business_url}: {e}")
            return None
    
    def _extract_contact_info(self, soup: BeautifulSoup, href_prefix: str, label: str) -> Optional[str]:
        """Extract contact information by href prefix and label"""
        # Try to find by label first
        contact_div = soup.find('div', class_='label', string=label)
        if contact_div:
            text_div = contact_div.find_next_sibling('div', class_='text')
            if text_div:
                link = text_div.find('a', href=lambda x: x and x.startswith(href_prefix))
                if link:
                    return link.get_text().strip()
        
        # Fallback: search for any link with the prefix
        link = soup.find('a', href=lambda x: x and x.startswith(href_prefix))
        if link:
            return link.get_text().strip()
        
        return None
    
    def _extract_text_by_label(self, soup: BeautifulSoup, label: str) -> Optional[str]:
        """Extract text content by label"""
        label_div = soup.find('div', class_='label', string=label)
        if label_div:
            text_div = label_div.find_next_sibling('div', class_='text')
            if text_div:
                return text_div.get_text().strip()
        return None
    
    def _extract_working_hours(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract working hours information"""
        hours_div = soup.select_one('#open_hours ul')
        if not hours_div:
            return None
        
        working_hours = {}
        for li in hours_div.find_all('li'):
            text = li.get_text().strip()
            if ':' in text:
                parts = text.split(':', 1)
                if len(parts) == 2:
                    day = parts[0].strip()
                    hours = parts[1].strip()
                    working_hours[day] = hours
        
        return working_hours if working_hours else None

def get_scraper(domain: str, session: aiohttp.ClientSession) -> BaseScraper:
    """Factory function to get appropriate scraper for domain"""
    return YelloScraper(domain, session)
