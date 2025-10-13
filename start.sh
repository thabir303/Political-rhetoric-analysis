#!/bin/bash

# RAG-IR Quick Start Script

echo "🚀 Starting RAG-IR System..."
echo ""

# Check if backend is running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Backend is already running on port 8000"
else
    echo "⚠️  Backend is not running. Starting backend..."
    cd /home/bs01127/Desktop/RAG-IR
    python3 main.py &
    sleep 3
    echo "✅ Backend started on port 8000"
fi

echo ""

# Start frontend
echo "🎨 Starting frontend..."
cd /home/bs01127/Desktop/RAG-IR/frontend
npm run dev
