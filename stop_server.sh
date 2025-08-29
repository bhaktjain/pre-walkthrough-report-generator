#!/bin/bash

# Pre-Walkthrough Report Generator - Stop Script
# This script stops the server and ngrok tunnel

echo "Stopping Pre-Walkthrough Report Generator services..."

# Kill server processes
echo "Stopping FastAPI server..."
pkill -f "python.*fastapi_server.py"
pkill -f "python.*app.py"

# Kill ngrok processes
echo "Stopping ngrok tunnel..."
pkill -f "ngrok.*8000"

echo "✅ All services stopped."

# Clean up log files (optional)
read -p "Do you want to clear log files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    > server.log
    > ngrok.log
    echo "Log files cleared."
fi