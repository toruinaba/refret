#!/bin/bash
echo "🎸 Starting Refret Backend..."
cd backend
# Check if venv is active or available, otherwise hint
# Assuming user runs this from root where venv might be active
uvicorn app.main:app --reload --port 8000
