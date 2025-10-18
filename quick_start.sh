#!/bin/bash

# Quick Start Script for RAG-IR System
# This script starts both backend and frontend servers

echo "🚀 Starting RAG-IR System..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "backend_main.py" ]; then
    echo "❌ Error: backend_main.py not found. Please run from RAG-IR directory"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use. Killing existing process..."
        lsof -ti :$1 | xargs kill -9
        sleep 2
    fi
}

# Kill existing processes
echo "🧹 Cleaning up existing processes..."
check_port 8000
check_port 5173

echo ""
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${GREEN}Starting Backend Server (Port 8000)${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Activate venv and start backend
source venv/bin/activate
python -m uvicorn backend_main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✅ Backend is running at http://localhost:8000"
    echo "📖 API Documentation: http://localhost:8000/docs"
else
    echo "❌ Backend failed to start. Check logs above."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${GREEN}Starting Frontend Server (Port 5173)${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

echo ""
echo "${GREEN}✅ System started successfully!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌐 Frontend:      http://localhost:5173/scraping-analysis"
echo "  🔧 Backend API:   http://localhost:8000/docs"
echo "  💚 Health Check:  http://localhost:8000/api/v1/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Logs:"
echo "  Backend PID: $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "⚠️  Press Ctrl+C to stop all servers"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# Keep script running
wait
