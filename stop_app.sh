#!/bin/bash
set -e

# Multi-API Chat Application Stop Script
# This script stops the application by attempting PID-based shutdown first,
# falling back to killing processes listening on ports 8001 and 8002.

echo "Multi-API Chat Application Stop Script"
echo "======================================="

LOG_DIR="logs"
BACKEND_PID_FILE="$LOG_DIR/backend.pid"
FRONTEND_PID_FILE="$LOG_DIR/frontend.pid"

# Gracefully stop a PID if running
stop_by_pid() {
  local pid_file=$1
  local name=$2
  if [ -f "$pid_file" ]; then
    local pid=$(cat "$pid_file" 2>/dev/null || true)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $name (PID $pid) ..."
      kill "$pid" 2>/dev/null || true
      # Wait up to 5s, then force kill if still alive
      for i in {1..5}; do
        if kill -0 "$pid" 2>/dev/null; then
          sleep 1
        else
          break
        fi
      done
      if kill -0 "$pid" 2>/dev/null; then
        echo "$name still running, sending SIGKILL"
        kill -9 "$pid" 2>/dev/null || true
      fi
      rm -f "$pid_file"
      echo "$name stopped"
    else
      echo "$name not running (no PID or process not found)"
      rm -f "$pid_file" || true
    fi
  else
    echo "PID file for $name not found ($pid_file)"
  fi
}

# Function to kill processes on a specific port (fallback)
kill_port_processes() {
    local port=$1
    local process_name=$2
    echo "Checking for processes on port $port..."
    local pids=$(lsof -ti:$port || true)
    if [ -n "$pids" ]; then
        echo "Killing existing $process_name processes on port $port..."
        kill -9 $pids || true
        echo "$process_name processes killed successfully"
    else
        echo "No processes found on port $port"
    fi
}

# Try PID-based stop
stop_by_pid "$BACKEND_PID_FILE" "backend"
stop_by_pid "$FRONTEND_PID_FILE" "frontend"

# Fallback to port-based termination
kill_port_processes 8002 "backend"
kill_port_processes 8001 "frontend"

echo "Application stopped successfully"
