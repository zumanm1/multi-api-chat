#!/bin/bash

# Multi-API Chat Application Stop Script
# This script stops the application by killing processes on ports 8001 and 8002

echo "Multi-API Chat Application Stop Script"
echo "======================================="

# Function to kill processes on a specific port
kill_port_processes() {
    local port=$1
    local process_name=$2
    
    echo "Checking for processes on port $port..."
    
    # Find processes using the port
    local pids=$(lsof -ti:$port)
    
    if [ -n "$pids" ]; then
        echo "Killing existing $process_name processes on port $port..."
        kill -9 $pids
        echo "$process_name processes killed successfully"
    else
        echo "No processes found on port $port"
    fi
}

# Kill processes on ports 8001 and 8002
kill_port_processes 8002 "backend"
kill_port_processes 8001 "frontend"

# Deactivate virtual environment if active
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Deactivating virtual environment..."
    deactivate
    echo "Virtual environment deactivated"
fi

echo "Application stopped successfully"