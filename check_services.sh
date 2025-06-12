#!/bin/bash
echo "=== Business Scraper Service Status ==="
echo ""

# Check backend
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "✅ Backend (Port 8000): RUNNING"
    echo "   🔧 API: http://localhost:8000"
    echo "   📚 Docs: http://localhost:8000/docs"
    echo "   🏥 Health: http://localhost:8000/health"
else
    echo "❌ Backend (Port 8000): NOT RUNNING"
fi

echo ""

# Check frontend
if lsof -ti:3020 > /dev/null 2>&1; then
    echo "✅ Frontend (Port 3020): RUNNING"
    echo "   📊 Dashboard: http://localhost:3020"
    echo "   📤 API Export: http://localhost:3020/api-export"
else
    echo "❌ Frontend (Port 3020): NOT RUNNING"
fi

echo ""

# Check MongoDB
if pgrep mongod > /dev/null 2>&1; then
    echo "✅ MongoDB: RUNNING"
else
    echo "❌ MongoDB: NOT RUNNING"
    echo "   💡 Start with: mongod"
fi

echo ""
echo "=== Active Jobs Status ==="

# Try to get job status from API
if curl -s --max-time 5 "http://localhost:8000/api/jobs" > /dev/null 2>&1; then
    echo "📊 Fetching job statistics..."
    
    # Get scraping jobs summary
    SCRAPING_RESPONSE=$(curl -s --max-time 5 "http://localhost:8000/api/jobs" 2>/dev/null)
    if [ $? -eq 0 ] && [ ! -z "$SCRAPING_RESPONSE" ]; then
        echo "🔄 Scraping Jobs:"
        echo "$SCRAPING_RESPONSE" | jq -r '.[] | "   • \(.name) - Status: \(.status) - Progress: \(.cities_completed)/\(.total_cities) cities"' 2>/dev/null || echo "   📊 Jobs data available (install jq for formatted display)"
    fi
    
    # Get API export jobs summary
    EXPORT_RESPONSE=$(curl -s --max-time 5 "http://localhost:8000/api/api-export/stats" 2>/dev/null)
    if [ $? -eq 0 ] && [ ! -z "$EXPORT_RESPONSE" ]; then
        echo "📤 API Export Summary:"
        echo "$EXPORT_RESPONSE" | jq -r '"   • Total Configs: \(.total_configs)\n   • Active Configs: \(.active_configs)\n   • Total Jobs: \(.total_jobs)\n   • Jobs Today: \(.jobs_today)\n   • Records Exported: \(.total_exported_records)"' 2>/dev/null || echo "   📊 Export stats available (install jq for formatted display)"
    fi
else
    echo "❌ Cannot connect to backend API"
    echo "   💡 Start backend with: ./start_app.sh"
fi

echo ""
echo "=== Process Information ==="

# Show PID files if they exist
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "🔧 Backend PID: $BACKEND_PID (running)"
    else
        echo "⚠️  Backend PID: $BACKEND_PID (stale - process not found)"
        rm logs/backend.pid
    fi
fi

if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🌐 Frontend PID: $FRONTEND_PID (running)"
    else
        echo "⚠️  Frontend PID: $FRONTEND_PID (stale - process not found)"
        rm logs/frontend.pid
    fi
fi

echo ""
echo "=== Quick Commands ==="
echo "🚀 Start application: ./start_app.sh"
echo "🛑 Stop application: ./stop_app.sh"
echo "📊 Check status: ./check_services.sh"
echo "📝 View backend logs: tail -f logs/backend.log"
echo "📝 View frontend logs: tail -f logs/frontend.log"
