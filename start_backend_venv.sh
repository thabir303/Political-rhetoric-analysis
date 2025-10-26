#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RAG-IR Backend Startup Script${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Navigate to project directory
cd /home/bs01127/Desktop/RAG-IR

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}✓ Activating virtual environment...${NC}"
source venv/bin/activate

# Check if requirements are installed
echo -e "${GREEN}✓ Checking dependencies...${NC}"
pip install -q -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env file with required credentials.${NC}"
    echo -e "${YELLOW}Use .env.example as a template.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment configured${NC}\n"

# Start the backend server
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Starting Backend Server${NC}"
echo -e "${BLUE}========================================${NC}\n"
echo -e "${GREEN}Server will run on: http://localhost:8000${NC}"
echo -e "${GREEN}API Documentation: http://localhost:8000/docs${NC}\n"

# Run the server
python main.py
