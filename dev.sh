#!/bin/bash
# Start both backend and frontend in parallel for development

set -e

echo "🚀 Starting Stack Sage in development mode..."
echo ""
echo "Backend will run on: http://localhost:8000"
echo "Frontend will run on: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Trap to kill all background processes on exit
trap 'kill 0' EXIT

# Start backend
(
  echo "📘 Starting backend server..."
  if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
  fi
  python3 -m uvicorn backend.api.server:app --reload --port 8000
) &

# Start frontend
(
  cd frontend
  echo "⚛️  Starting frontend dev server..."
  npm run dev
) &

# Wait for both processes
wait

