#!/bin/bash
echo "🎸 Starting Refret (Backend + Frontend)..."

# Find and activate venv if exists
if [ -d "venv" ]; then
    echo "Using venv..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Using .venv..."
    source .venv/bin/activate
fi

# Set PYTHONPATH to verify imports work
export PYTHONPATH=$PYTHONPATH:.

# Start Backend
echo "Starting Backend..."
uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Refret is running!"
echo "Backend: http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both."

# Trap exit to kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

# Wait for processes
wait
