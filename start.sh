#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Kill existing processes on target ports
kill -9 $(lsof -ti:3000) 2>/dev/null || true
kill -9 $(lsof -ti:8000) 2>/dev/null || true
sleep 1

# Start backend
cd "$ROOT/backend"
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$ROOT/backend.log" 2>&1 &
BACKEND_PID=$!

# Start frontend
cd "$ROOT/frontend"
nohup npm run dev -- --host > "$ROOT/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Logs: backend.log / frontend.log"
echo "Use './stop.sh' to stop both"
