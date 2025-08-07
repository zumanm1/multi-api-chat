#!/bin/bash

# Multi-API Chat Application Start Script
# This script cleans ports 8001 and 8002 before starting the application
# Application includes: Chat interface, Dashboard, Operations, Automation, and Device Management

echo "Multi-API Chat Application Start Script"
echo "========================================"

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
        echo "Processes killed successfully"
    else
        echo "No processes found on port $port"
    fi
}

# Kill processes on ports 8001 and 8002
kill_port_processes 8002 "backend"
kill_port_processes 8001 "frontend"

# Check if virtual environment exists or create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if config.json exists or create it
if [ ! -f "config.json" ]; then
    echo "Creating default config.json..."
    cat > config.json << EOF
{
  "providers": {
    "openai": {
      "name": "OpenAI",
      "enabled": false,
      "api_key": "",
      "model": "gpt-4o",
      "base_url": "https://api.openai.com/v1",
      "status": "disconnected",
      "last_checked": ""
    },
    "groq": {
      "name": "Groq",
      "enabled": false,
      "api_key": "",
      "model": "llama-3.1-70b-versatile",
      "base_url": "https://api.groq.com/openai/v1",
      "status": "disconnected",
      "last_checked": ""
    },
    "cerebras": {
      "name": "Cerebras",
      "enabled": false,
      "api_key": "",
      "model": "llama-4-scout-wse-3",
      "base_url": "https://api.cerebras.ai/v1",
      "status": "disconnected",
      "last_checked": ""
    },
    "sambanova": {
      "name": "SambaNova",
      "enabled": false,
      "api_key": "",
      "model": "llama-3.3-70b",
      "base_url": "https://api.sambanova.ai/v1",
      "status": "disconnected",
      "last_checked": ""
    },
    "anthropic": {
      "name": "Anthropic",
      "enabled": false,
      "api_key": "",
      "model": "claude-sonnet-4",
      "base_url": "https://api.anthropic.com/v1/openai",
      "status": "disconnected",
      "last_checked": ""
    },
    "openrouter": {
      "name": "OpenRouter",
      "enabled": false,
      "api_key": "",
      "model": "openrouter/auto",
      "base_url": "https://openrouter.ai/api/v1",
      "status": "disconnected",
      "last_checked": ""
    }
  },
  "settings": {
    "default_provider": "groq",
    "fallback_provider": null,
    "temperature": 0.7,
    "max_tokens": 1000,
    "system_prompt": "You are a helpful AI assistant.",
    "features": {
      "auto_fallback": true,
      "speed_optimization": false,
      "cost_optimization": false,
      "multi_provider_compare": false,
      "usage_analytics": true
    }
  }
}
EOF
fi

# Start backend server in background
echo "Starting backend server on port 8002..."
python backend_server.py &

# Wait a moment for backend to start
sleep 2

# Start frontend server
echo "Starting frontend server on port 8001..."
echo "Available pages: index.html (Chat), dashboard.html, operations.html, automation.html, devices.html"
python -m http.server 8001

echo "Application stopped"