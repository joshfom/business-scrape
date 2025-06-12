# Business Scraper

A comprehensive web scraping application for extracting business data from Yello business directory websites across multiple domains. Built with FastAPI backend, React frontend, and MongoDB database with API export capabilities.

## 🚀 Features

- **Multi-domain scraping**: Support for multiple Yello websites (UAE, Saudi Arabia, Qatar, etc.)
- **Concurrent processing**: Configurable concurrent requests with rate limiting
- **Resume functionality**: Ability to pause and resume scraping jobs
- **Real-time monitoring**: Live dashboard with progress tracking and statistics
- **API Export**: Export scraped data to external APIs with batch processing
- **Data export**: JSON export functionality with filtering options
- **Modern UI**: React-based dashboard with Material-UI components (Port 3020)
- **Robust scraping**: BeautifulSoup and Selenium for reliable data extraction
- **Network resilience**: Automatic job pausing/resuming on network interruptions

## 📋 Prerequisites

- Python 3.8+
- Node.js 14+
- MongoDB 4.4+
- Chrome browser (for Selenium)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd business-scraper
   ```

2. **Run the setup script**
   ```bash
   python scripts/setup.py
   ```
   
   This will:
   - Install Python dependencies
   - Install frontend dependencies
   - Create `.env` configuration file
   - Initialize database with indexes

3. **Start MongoDB**
   ```bash
   mongod
   ```

## 🚀 Running the Application

### Quick Start (Both Services)
```bash
# Start both backend and frontend in background
./start_app.sh

# OR manually start each service:
```

### Manual Start

#### Backend (FastAPI) - Port 8000
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (React) - Port 3020
```bash
cd frontend
PORT=3020 npm start
```

### Using VS Code Tasks
```bash
# In VS Code, run these tasks:
# Ctrl+Shift+P -> "Tasks: Run Task"
- "Start Backend API"
- "Start Frontend"
```

### Application URLs
- **Frontend Dashboard**: http://localhost:3020
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Export Page**: http://localhost:3020/api-export

## 🔧 Process Management

### Check Running Services
```bash
# Check if backend is running (port 8000)
lsof -ti:8000

# Check if frontend is running (port 3020)
lsof -ti:3020

# Check all Python processes
ps aux | grep python | grep uvicorn

# Check all Node processes
ps aux | grep node | grep react-scripts
```

### Stop Services
```bash
# Stop backend
pkill -f "uvicorn main:app"

# Stop frontend
pkill -f "react-scripts start"

# Stop all related processes
./stop_app.sh

# Or kill by port
kill $(lsof -ti:8000)  # Backend
kill $(lsof -ti:3020)  # Frontend
```

### Background Process Management
```bash
# Start services in background (detached)
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
cd frontend && nohup npm start > frontend.log 2>&1 &

# Check background processes
jobs -l
ps aux | grep -E "(uvicorn|react-scripts)"

# Stop background processes
kill %1  # Kill first background job
kill %2  # Kill second background job
```

## 🌐 Network Interruption Handling

### What Happens When Network Is Lost?

#### Scraping Jobs
- **Automatic Pause**: Jobs automatically pause when network errors are detected
- **Graceful Degradation**: Current batch completes, then job pauses
- **State Preservation**: All progress and state is saved to database
- **Error Logging**: Network errors are logged with timestamps

#### API Export Jobs
- **Retry Mechanism**: Failed API calls are retried with exponential backoff
- **Batch Preservation**: Failed batches are marked for retry
- **Job Status**: Jobs remain in "running" state but pause execution
- **Resume Capability**: Jobs automatically resume when network is restored

### Manual Job Control

#### Pause All Active Jobs
```bash
# API endpoint to pause all running jobs
curl -X POST "http://localhost:8000/api/jobs/pause-all"

# Pause specific job
curl -X POST "http://localhost:8000/api/jobs/{job_id}/pause"
```

#### Resume Paused Jobs
```bash
# Resume all paused jobs
curl -X POST "http://localhost:8000/api/jobs/resume-all"

# Resume specific job
curl -X POST "http://localhost:8000/api/jobs/{job_id}/resume"

# Resume only network-paused jobs
curl -X POST "http://localhost:8000/api/jobs/resume-network-paused"
```

### Laptop Closure / System Sleep

#### What Happens
1. **Background Services**: Services continue if system doesn't sleep
2. **Process Suspension**: Services pause if system sleeps
3. **Network Disconnection**: Jobs pause on network loss
4. **Database Persistence**: All state saved to MongoDB

#### Recovery Steps
```bash
# 1. Check if services are still running
./check_services.sh

# 2. Restart services if needed
./start_app.sh

# 3. Check job statuses
curl -X GET "http://localhost:8000/api/jobs/status-summary"

# 4. Resume network-paused jobs
curl -X POST "http://localhost:8000/api/jobs/resume-network-paused"
```

## 🔧 Utility Scripts

### Create Application Control Scripts

#### start_app.sh
```bash
#!/bin/bash
echo "Starting Business Scraper Application..."

# Start backend in background
cd backend
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Start frontend in background
cd ../frontend
nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

# Save PIDs
echo $BACKEND_PID > ../logs/backend.pid
echo $FRONTEND_PID > ../logs/frontend.pid

echo "Application started successfully!"
echo "Frontend: http://localhost:3020"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
```

#### stop_app.sh
```bash
#!/bin/bash
echo "Stopping Business Scraper Application..."

# Stop by PID files if they exist
if [ -f logs/backend.pid ]; then
    kill $(cat logs/backend.pid) 2>/dev/null
    rm logs/backend.pid
fi

if [ -f logs/frontend.pid ]; then
    kill $(cat logs/frontend.pid) 2>/dev/null
    rm logs/frontend.pid
fi

# Fallback: kill by port
kill $(lsof -ti:8000) 2>/dev/null  # Backend
kill $(lsof -ti:3020) 2>/dev/null  # Frontend

# Fallback: kill by process name
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null

echo "Application stopped!"
```

#### check_services.sh
```bash
#!/bin/bash
echo "=== Business Scraper Service Status ==="

# Check backend
if lsof -ti:8000 > /dev/null; then
    echo "✅ Backend (Port 8000): RUNNING"
    echo "   API: http://localhost:8000"
    echo "   Docs: http://localhost:8000/docs"
else
    echo "❌ Backend (Port 8000): NOT RUNNING"
fi

# Check frontend
if lsof -ti:3020 > /dev/null; then
    echo "✅ Frontend (Port 3020): RUNNING"
    echo "   URL: http://localhost:3020"
else
    echo "❌ Frontend (Port 3020): NOT RUNNING"
fi

# Check MongoDB
if pgrep mongod > /dev/null; then
    echo "✅ MongoDB: RUNNING"
else
    echo "❌ MongoDB: NOT RUNNING"
fi

echo ""
echo "=== Active Jobs Status ==="
curl -s "http://localhost:8000/api/jobs/status-summary" 2>/dev/null || echo "❌ Cannot connect to backend"
```

## 📊 Usage

### Dashboard
- View real-time scraping statistics
- Monitor active jobs and progress
- Visualize business data by city and category

### Creating Scraping Jobs
1. Navigate to "Scraping Jobs" section
2. Click "New Job"
3. Configure:
   - Job name
   - Target domains
   - Concurrent request limits
   - Request delay settings
4. Start the job and monitor progress

### Business Data Management
- Browse scraped business listings
- Filter by domain, city, category, or search terms
- View detailed business information
- Export data in JSON format

## 🔧 Configuration

Edit `.env` file to customize settings:

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=business_scraper

# Scraping Configuration
MAX_CONCURRENT_SCRAPERS=5
MAX_CONCURRENT_REQUESTS=10
REQUEST_DELAY=1.0

# Browser Configuration
HEADLESS_BROWSER=true
BROWSER_TIMEOUT=30
```

## 📁 Project Structure

```
business-scraper/
├── backend/
│   ├── api/endpoints/          # FastAPI route handlers
│   ├── models/                 # Database models and schemas
│   ├── scrapers/               # Web scraping logic
│   ├── services/               # Business logic services
│   ├── utils/                  # Utility functions
│   ├── config.py               # Configuration settings
│   └── main.py                 # FastAPI application entry point
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── api.ts              # API client
│   │   └── types.ts            # TypeScript types
│   └── public/                 # Static assets
├── scripts/
│   └── setup.py               # Setup and installation script
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## 🎯 Supported Domains

The scraper supports these Yello business directory websites:
- 🇦🇪 UAE: https://www.yello.ae
- 🇸🇦 Saudi Arabia: https://www.yello.sa
- 🇶🇦 Qatar: https://www.yello.qa
- 🇴🇲 Oman: https://www.yello.om
- 🇰🇼 Kuwait: https://www.yello.kw
- 🇧🇭 Bahrain: https://www.yello.bh

## 📊 Data Schema

Each business record includes:
- Basic information (name, title, description)
- Contact details (phone, mobile, website, address)
- Location data (city, country, coordinates)
- Business details (category, working hours, establishment year)
- Review metrics (rating, review count)
- Metadata (source URL, scraping timestamp)

## 🛡️ Best Practices

- **Rate limiting**: Configurable delays between requests
- **Respectful scraping**: Honors robots.txt and implements reasonable delays
- **Error handling**: Comprehensive error logging and recovery
- **Data integrity**: Duplicate detection and data validation
- **Resume capability**: Jobs can be paused and resumed safely

## 🔍 Monitoring

The dashboard provides:
- Real-time job progress tracking
- Business data statistics
- Error monitoring and logging
- Performance metrics

## 📤 Data Export

Export filtered business data:
- JSON format with all business details
- Filter by domain, city, or category
- Bulk export capabilities
- Preserves data relationships

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check connection string in `.env`

2. **Chrome Driver Issues**
   - Install Chrome browser
   - Update chromedriver via webdriver-manager

3. **Frontend Build Errors**
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Check the API documentation at `/docs`
- Review the troubleshooting section
- Open an issue on GitHub
