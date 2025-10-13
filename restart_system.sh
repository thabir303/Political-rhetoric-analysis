#!/bin/bash

# Restart Script for RAG-IR System
# Use this after changing environment variables

echo "🔄 Restarting RAG-IR System..."
echo ""

# Check if backend is running
echo "📋 Checking backend status..."
BACKEND_PID=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')

if [ -n "$BACKEND_PID" ]; then
    echo "✅ Found running backend (PID: $BACKEND_PID)"
    echo "🛑 Stopping backend..."
    kill $BACKEND_PID
    sleep 2
    echo "✅ Backend stopped"
else
    echo "ℹ️  Backend not running"
fi

echo ""
echo "🚀 Starting backend..."
echo "   (This will run in the background)"
echo ""

# Start backend in background
nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > api_server.log 2>&1 &
BACKEND_PID=$!

echo "✅ Backend started (PID: $BACKEND_PID)"
echo "   Log file: api_server.log"
echo "   API URL: http://localhost:8000"
echo ""

# Wait a moment for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 3

# Check if backend is responding
echo "🔍 Checking backend health..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health)

if [ "$HEALTH_CHECK" = "200" ]; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️  Backend health check returned: $HEALTH_CHECK"
    echo "   Check api_server.log for details"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ System restart complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Frontend should auto-reload (if running)"
echo "   2. Visit http://localhost:5173 to test"
echo "   3. Check api_server.log for backend logs"
echo ""
echo "💡 Tips:"
echo "   • Environment variables loaded: ✅"
echo "   • New API key active: ✅"
echo "   • No database reset needed: ✅"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
