#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting Hackathon Agent..."

# Set environment variables for production
export PYTHONPATH="${PYTHONPATH}:."
export PYTHONUNBUFFERED=1

# Run database migrations/setup if needed
echo "🗄️ Setting up database..."
python -c "from database import create_tables; create_tables()"

# Start the application with gunicorn
echo "🌟 Starting FastAPI application..."
exec gunicorn main:app \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --preload \
    --log-level info \
    --access-logfile - \
    --error-logfile - 