#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Kill existing processes on target ports
kill -9 $(lsof -ti:3000) 2>/dev/null || true
kill -9 $(lsof -ti:8000) 2>/dev/null || true
sleep 1

# Start backend
echo "Starting backend on port 8000..."
cd "$ROOT/backend"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on port 3000..."
cd "$ROOT/frontend"
npm run dev -- --host &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Use './stop.sh' to stop both"
