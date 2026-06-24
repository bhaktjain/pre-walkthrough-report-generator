#!/bin/bash
echo "Starting Pre-Walkthrough Report Generator..."
echo "Using Python version: $(python --version)"
echo "Starting with Uvicorn..."
exec python -m uvicorn app:app --host 0.0.0.0 --port $PORT