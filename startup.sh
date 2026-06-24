#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=========================================================="
echo "🚀 Starting Community Decision Intelligence Platform (CDIP)"
echo "=========================================================="

# 1. Resolve Project Root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 2. Database Environment Setup
# If DATABASE_URL is not set, default to a local SQLite database in the backend directory
if [ -z "$DATABASE_URL" ]; then
  export DATABASE_URL="sqlite:///$PROJECT_ROOT/backend/community.db"
  echo "📦 DATABASE_URL is not set. Defaulting to SQLite: $DATABASE_URL"
else
  echo "📦 Using custom database at: $DATABASE_URL"
fi

# 3. Start Backend FastAPI Server in background
echo "📡 Starting FastAPI Backend Server on port 8000..."
cd "$PROJECT_ROOT/backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Save the backend PID
BACKEND_PID=$!

# Setup trap to kill backend server process on script exit/interruption
trap "echo '🛑 Stopping backend server...'; kill $BACKEND_PID" EXIT

# Wait for backend server to spin up and bind port 8000
echo "⏳ Waiting for backend API to be ready..."
for i in {1..30}; do
  if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ Backend API is online!"
    break
  fi
  sleep 1
done

# 4. Start Frontend Streamlit Server in foreground
echo "📊 Starting Streamlit Frontend Dashboard on port 7860..."
cd "$PROJECT_ROOT/frontend"
python -m streamlit run app.py --server.port 7860 --server.address 0.0.0.0
