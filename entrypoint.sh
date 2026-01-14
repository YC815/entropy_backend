#!/bin/bash
# EntroPy Backend Entrypoint Script
# This script runs database migrations before starting the application

set -e

echo "Starting EntroPy Backend..."

# Run database migrations
echo "Running Alembic migrations..."
uv run alembic upgrade head

# Check if migrations succeeded
if [ $? -eq 0 ]; then
    echo "Migrations completed successfully!"
else
    echo "Migration failed!"
    exit 1
fi

# Start the application
echo "Starting Uvicorn server..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
