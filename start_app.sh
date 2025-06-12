#!/bin/bash
echo "Starting Business Scraper Application..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Start backend in background
cd backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Start frontend in background
cd ../frontend
nohup env PORT=3020 npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

# Save PIDs
echo $BACKEND_PID > ../logs/backend.pid
echo $FRONTEND_PID > ../logs/frontend.pid

echo ""
echo "✅ Application started successfully!"
echo "📊 Frontend Dashboard: http://localhost:3020"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📤 API Export Page: http://localhost:3020/api-export"
echo ""
echo "📝 Logs:"
echo "   Backend: logs/backend.log"
echo "   Frontend: logs/frontend.log"
echo ""
echo "🛑 To stop: ./stop_app.sh"
echo "📊 To check status: ./check_services.sh"
