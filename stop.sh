#!/usr/bin/env bash
set -e

echo "Stopping processes on port 3000 and 8000..."
kill -9 $(lsof -ti:3000) 2>/dev/null || echo "Nothing on port 3000"
kill -9 $(lsof -ti:8000) 2>/dev/null || echo "Nothing on port 8000"
echo "Done."
