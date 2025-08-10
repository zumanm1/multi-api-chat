#!/bin/bash
set -e

# Multi-API Chat Application Start Script (Python 3.11 .venv)
# - Cleans ports 8001 (frontend) and 8002 (backend)
# - Ensures .venv (Python 3.11) exists and installs dependencies
# - Starts backend and frontend in the background
# - Writes logs and PID files under ./logs

echo "Multi-API Chat Application Start Script"
echo "========================================"

# Function to kill processes on a specific port
kill_port_processes() {
    local port=$1
    local process_name=$2
    echo "Checking for processes on port $port..."
    local pids=$(lsof -ti:$port || true)
    if [ -n "$pids" ]; then
        echo "Killing existing $process_name processes on port $port..."
        kill -9 $pids || true
        echo "Processes killed successfully"
    else
        echo "No processes found on port $port"
    fi
}

# Kill processes on ports 8002 and 8001
kill_port_processes 8002 "backend"
kill_port_processes 8001 "frontend"

# Prepare logs directory
mkdir -p logs

# Ensure Python 3.11 virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python 3.11 virtual environment (.venv)..."
    if command -v python3.11 >/dev/null 2>&1; then
        python3.11 -m venv .venv
    else
        echo "python3.11 not found, falling back to system python3"
        python3 -m venv .venv
    fi
    echo ".venv created"
fi

# Upgrade pip and install dependencies in the venv
echo "Installing/Updating dependencies in .venv..."
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

# Initialize default config.json if missing (safe no-op if present)
if [ ! -f "config.json" ]; then
    echo "Creating default config.json..."
    cat > config.json << 'EOF'
{
  "providers": {
    "openai": {"name": "OpenAI", "enabled": false, "api_key": "", "model": "gpt-4o", "base_url": "https://api.openai.com/v1", "status": "disconnected", "last_checked": ""},
    "groq": {"name": "Groq", "enabled": false, "api_key": "", "model": "llama-3.1-70b-versatile", "base_url": "https://api.groq.com/openai/v1", "status": "disconnected", "last_checked": ""},
    "cerebras": {"name": "Cerebras", "enabled": false, "api_key": "", "model": "llama-4-scout-wse-3", "base_url": "https://api.cerebras.ai/v1", "status": "disconnected", "last_checked": ""},
    "sambanova": {"name": "SambaNova", "enabled": false, "api_key": "", "model": "llama-3.3-70b", "base_url": "https://api.sambanova.ai/v1", "status": "disconnected", "last_checked": ""},
    "anthropic": {"name": "Anthropic", "enabled": false, "api_key": "", "model": "claude-sonnet-4", "base_url": "https://api.anthropic.com/v1/openai", "status": "disconnected", "last_checked": ""},
    "openrouter": {"name": "OpenRouter", "enabled": false, "api_key": "", "model": "openrouter/auto", "base_url": "https://openrouter.ai/api/v1", "status": "disconnected", "last_checked": ""}
  },
  "settings": {
    "default_provider": "groq",
    "fallback_provider": null,
    "temperature": 0.7,
    "max_tokens": 1000,
    "system_prompt": "You are a helpful AI assistant.",
    "features": {"auto_fallback": true, "speed_optimization": false, "cost_optimization": false, "multi_provider_compare": false, "usage_analytics": true}
  }
}
EOF
fi

# Start backend server (port 8002) in background using .venv
echo "Starting backend server on port 8002..."
nohup ./.venv/bin/python backend_server.py > logs/backend.log 2>&1 &
echo $! > logs/backend.pid

# Small delay for backend readiness
sleep 2

# Start frontend static server (port 8001) in background using .venv
echo "Starting frontend server on port 8001..."
echo "Available pages: index.html (Chat), dashboard.html, operations.html, automation.html, devices.html"
nohup ./.venv/bin/python -m http.server 8001 > logs/frontend.log 2>&1 &
echo $! > logs/frontend.pid

sleep 2

# Show status
echo "Backend PID: $(cat logs/backend.pid)"
echo "Frontend PID: $(cat logs/frontend.pid)"
if command -v ss >/dev/null 2>&1; then
  ss -tulpn | grep -E '(:8001|:8002)' || true
fi

echo "Started. Backend: http://localhost:8002  |  Frontend: http://localhost:8001"
exit 0
