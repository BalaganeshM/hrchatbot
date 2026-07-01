#!/usr/bin/env bash
set -e

# Start backend
echo "Starting backend on port 8000..."
cd "$(dirname "$0")/backend"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on port 3000..."
cd "$(dirname "$0")/frontend"
npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Use 'kill $BACKEND_PID $FRONTEND_PID' to stop both"

wait
