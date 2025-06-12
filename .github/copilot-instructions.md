<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Business Scraper Project Instructions

This is a Python-based web scraping application with the following architecture:

## Tech Stack
- **Backend**: FastAPI + Python for web scraping, API, and data management
- **Frontend**: React for dashboard and monitoring interface
- **Database**: MongoDB for storing scraped business data
- **Web Scraping**: BeautifulSoup, Selenium, and requests for scraping Yello business directory websites

## Project Structure
- `backend/`: FastAPI application with scraping engine
- `frontend/`: React dashboard for monitoring and controls
- `database/`: MongoDB configuration and scripts
- `scripts/`: Utility scripts for setup and maintenance

## Scraping Strategy
The scraper targets Yello business directory websites with the following flow:
1. Start from `/browse-business-cities` to get all cities
2. Visit each city page at `/location/{city}` 
3. Scrape business listings with pagination support
4. Extract detailed business information from individual company pages
5. Store data with resume functionality and concurrent processing controls

## Key Features
- Concurrent scraping with configurable thread limits
- Resume functionality for interrupted scraping sessions
- Real-time monitoring dashboard
- Data export capabilities (JSON)
- Rate limiting and respectful scraping practices
