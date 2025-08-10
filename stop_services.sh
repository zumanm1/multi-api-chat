#!/bin/bash

# Multi-API Chat Services Stop Script

echo "🛑 Stopping Multi-API Chat Services..."

# Stop backend
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "   Stopping Backend Server (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        sleep 1
        
        # Force kill if still running
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "   Force stopping backend..."
            kill -9 $BACKEND_PID 2>/dev/null || true
        fi
    fi
    rm -f backend.pid
    echo "✅ Backend stopped"
else
    echo "   No backend PID file found"
fi

# Stop frontend
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "   Stopping Frontend Server (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
        sleep 1
        
        # Force kill if still running
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "   Force stopping frontend..."
            kill -9 $FRONTEND_PID 2>/dev/null || true
        fi
    fi
    rm -f frontend.pid
    echo "✅ Frontend stopped"
else
    echo "   No frontend PID file found"
fi

# Clean up any remaining processes on our ports
echo "   Cleaning up remaining processes..."
lsof -ti tcp:8001 | xargs kill -9 2>/dev/null || true
lsof -ti tcp:8002 | xargs kill -9 2>/dev/null || true

echo "🎉 All services stopped successfully!"
