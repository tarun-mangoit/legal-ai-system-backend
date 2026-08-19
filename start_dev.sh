#!/bin/bash

echo "Starting required Docker containers (PostgreSQL and Redis)..."
docker start legal-ai-system-db-1 legal-ai-system-redis-1

# Activate virtual environment
source venv/bin/activate

echo "Starting Celery worker..."
celery -A app.core.celery_app worker --loglevel=info &
CELERY_PID=$!

# Ensure Celery stops when you press Ctrl+C
function cleanup {
  echo "Stopping Celery worker..."
  kill $CELERY_PID
}
trap cleanup EXIT

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
