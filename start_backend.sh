#!/bin/bash

# Start Stack Sage Backend Server

echo "=================================================="
echo "📘 Starting Stack Sage Backend Server"
echo "=================================================="
echo ""

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please set up the backend first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env template..."
    echo "OPENAI_API_KEY=your_openai_api_key_here" > backend/.env
    echo ""
    echo "📝 Please edit backend/.env and add your OpenAI API key"
    echo "Then run this script again."
    exit 1
fi

# Activate virtual environment and start server
echo "🚀 Activating virtual environment and starting server..."
echo ""

source backend/venv/bin/activate
python backend/api/server.py

