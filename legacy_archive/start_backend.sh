#!/bin/bash
echo "🎸 Starting Refret Backend..."
# Run from project root to ensure 'backend' package is resolvable
export PYTHONPATH=$PYTHONPATH:.
uvicorn backend.app.main:app --reload --port 8000
