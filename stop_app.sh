#!/bin/bash
echo "Stopping Business Scraper Application..."

# Stop by PID files if they exist
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    kill $BACKEND_PID 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Backend stopped (PID: $BACKEND_PID)"
    fi
    rm logs/backend.pid
fi

if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    kill $FRONTEND_PID 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Frontend stopped (PID: $FRONTEND_PID)"
    fi
    rm logs/frontend.pid
fi

# Fallback: kill by port
BACKEND_PORT_PID=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$BACKEND_PORT_PID" ]; then
    kill $BACKEND_PORT_PID 2>/dev/null
    echo "✅ Stopped process on port 8000"
fi

FRONTEND_PORT_PID=$(lsof -ti:3020 2>/dev/null)
if [ ! -z "$FRONTEND_PORT_PID" ]; then
    kill $FRONTEND_PORT_PID 2>/dev/null
    echo "✅ Stopped process on port 3020"
fi

# Fallback: kill by process name
pkill -f "uvicorn main:app" 2>/dev/null && echo "✅ Stopped uvicorn processes"
pkill -f "react-scripts start" 2>/dev/null && echo "✅ Stopped react-scripts processes"

echo ""
echo "🛑 Business Scraper Application stopped!"
