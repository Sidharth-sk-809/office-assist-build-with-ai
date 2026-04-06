#!/bin/bash

# Startup script for Office Assist API

echo "Starting Office Assist API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check environment variables
if [ -z "$GCP_PROJECT_ID" ]; then
    echo "Warning: GCP_PROJECT_ID not set. Please set environment variables."
    echo "Copy .env.example to .env and update with your values."
fi

# Start the server
echo "Starting FastAPI server on port ${PORT:-8000}..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
