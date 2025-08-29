#!/bin/bash

# Pre-Walkthrough Report Generator - Startup Script
# This script starts the server and ngrok tunnel persistently

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Pre-Walkthrough Report Generator..."

# Kill any existing processes
pkill -f "python.*app.py"
pkill -f "ngrok.*8000"

# Wait a moment for processes to stop
sleep 2

# Start the FastAPI server
echo "Starting FastAPI server..."
source pre_walkthrough_generator/venv/bin/activate
nohup python fastapi_server.py > server.log 2>&1 &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Wait for server to start
sleep 3

# Start ngrok tunnel
echo "Starting ngrok tunnel..."
nohup ngrok http 8000 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!
echo "Ngrok started with PID: $NGROK_PID"

# Wait for ngrok to initialize
sleep 5

# Extract and display the public URL
echo "Extracting public URL..."
PUBLIC_URL=$(grep -o 'https://[a-z0-9]*\.ngrok-free\.app' ngrok.log | head -1)

if [ -n "$PUBLIC_URL" ]; then
    echo "✅ Server is running!"
    echo "📍 Local URL: http://localhost:8000"
    echo "🌐 Public URL: $PUBLIC_URL"
    echo ""
    echo "Process IDs:"
    echo "  Server PID: $SERVER_PID"
    echo "  Ngrok PID: $NGROK_PID"
    echo ""
    echo "To stop the services, run: ./stop_server.sh"
else
    echo "❌ Failed to get ngrok URL. Check ngrok.log for details."
fi

echo "Services are running in the background."