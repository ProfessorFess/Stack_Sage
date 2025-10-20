#!/bin/bash

# Start Stack Sage Frontend

echo "=================================================="
echo "✨ Starting Stack Sage Frontend"
echo "=================================================="
echo ""

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies (first time only)..."
    echo ""
    npm install
    echo ""
fi

# Start the development server
echo "🚀 Starting Vite development server..."
echo ""
npm run dev

