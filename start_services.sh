#!/bin/bash

# Multi-API Chat Services Startup Script
# Frontend: http://localhost:8001
# Backend: http://localhost:8002

echo "🚀 Starting Multi-API Chat Services..."

# Check if ports are already in use
check_port() {
    local port=$1
    local service=$2
    
    if lsof -ti tcp:$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use by another process"
        echo "   Stopping existing process on port $port..."
        kill $(lsof -ti tcp:$port) 2>/dev/null || true
        sleep 2
    fi
}

# Function to start backend
start_backend() {
    echo "🔧 Starting Backend Server (Port 8002)..."
    
    # Check if backend dependencies are available
    if [ ! -f "backend_server.py" ]; then
        echo "❌ backend_server.py not found!"
        exit 1
    fi
    
    # Start backend server in background
    python backend_server.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    
    # Wait for backend to start
    echo "   Waiting for backend to initialize..."
    sleep 3
    
    # Test backend health
    if curl -s http://localhost:8002/api/health >/dev/null 2>&1; then
        echo "✅ Backend Server running on http://localhost:8002"
        echo "   Process ID: $BACKEND_PID"
        echo "   Log file: backend.log"
    else
        echo "❌ Backend failed to start. Check backend.log for errors."
        cat backend.log
        exit 1
    fi
}

# Function to start frontend
start_frontend() {
    echo "🌐 Starting Frontend Server (Port 8001)..."
    
    # Check if frontend files exist
    if [ ! -f "index.html" ] && [ ! -f "ai_dashboard.html" ]; then
        echo "❌ No frontend files found (index.html or ai_dashboard.html)!"
        exit 1
    fi
    
    # Start frontend server in background
    python -m http.server 8001 > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid
    
    # Wait for frontend to start
    echo "   Waiting for frontend to initialize..."
    sleep 2
    
    # Test frontend availability
    if curl -s http://localhost:8001 >/dev/null 2>&1; then
        echo "✅ Frontend Server running on http://localhost:8001"
        echo "   Process ID: $FRONTEND_PID"
        echo "   Log file: frontend.log"
    else
        echo "❌ Frontend failed to start. Check frontend.log for errors."
        cat frontend.log
        exit 1
    fi
}

# Function to show service status
show_status() {
    echo ""
    echo "📊 Service Status:"
    echo "==================="
    
    # Check backend
    if [ -f "backend.pid" ] && kill -0 $(cat backend.pid) 2>/dev/null; then
        echo "✅ Backend:  Running (PID: $(cat backend.pid)) - http://localhost:8002"
    else
        echo "❌ Backend:  Not running"
    fi
    
    # Check frontend
    if [ -f "frontend.pid" ] && kill -0 $(cat frontend.pid) 2>/dev/null; then
        echo "✅ Frontend: Running (PID: $(cat frontend.pid)) - http://localhost:8001"
    else
        echo "❌ Frontend: Not running"
    fi
    
    echo ""
    echo "📱 Available Interfaces:"
    echo "========================"
    echo "Main Dashboard:     http://localhost:8001"
    echo "AI Agents Dashboard: http://localhost:8001/ai_dashboard.html"
    echo "Backend API:        http://localhost:8002/api/health"
    echo ""
    echo "📋 Quick Commands:"
    echo "=================="
    echo "Stop services:      ./stop_services.sh"
    echo "View backend logs:  tail -f backend.log"
    echo "View frontend logs: tail -f frontend.log"
    echo "Check API health:   curl http://localhost:8002/api/health"
}

# Function to test AI agents
test_ai_agents() {
    echo "🤖 Testing AI Agents Integration..."
    
    # Test AI status endpoint
    if ai_status=$(curl -s http://localhost:8002/api/ai/status 2>/dev/null); then
        if echo "$ai_status" | grep -q '"available": true'; then
            echo "✅ AI Agents: Available and active"
        else
            echo "⚠️  AI Agents: Available but may have issues"
        fi
    else
        echo "❌ AI Agents: Not responding"
    fi
}

# Main execution
main() {
    # Parse command line arguments
    case "${1:-start}" in
        "start")
            check_port 8002 "backend"
            check_port 8001 "frontend"
            
            start_backend
            start_frontend
            test_ai_agents
            show_status
            
            echo "🎉 All services started successfully!"
            echo "   Access the application at http://localhost:8001"
            ;;
        "stop")
            echo "🛑 Stopping services..."
            if [ -f "backend.pid" ]; then
                kill $(cat backend.pid) 2>/dev/null || true
                rm -f backend.pid
                echo "   Backend stopped"
            fi
            if [ -f "frontend.pid" ]; then
                kill $(cat frontend.pid) 2>/dev/null || true
                rm -f frontend.pid
                echo "   Frontend stopped"
            fi
            echo "✅ All services stopped"
            ;;
        "status")
            show_status
            ;;
        "restart")
            $0 stop
            sleep 2
            $0 start
            ;;
        "logs")
            echo "📄 Recent Backend Logs:"
            echo "======================="
            if [ -f "backend.log" ]; then
                tail -20 backend.log
            else
                echo "No backend logs found"
            fi
            
            echo ""
            echo "📄 Recent Frontend Logs:"
            echo "========================"
            if [ -f "frontend.log" ]; then
                tail -20 frontend.log
            else
                echo "No frontend logs found"
            fi
            ;;
        "test")
            echo "🧪 Running Service Tests..."
            
            # Test backend health
            if curl -s http://localhost:8002/api/health >/dev/null; then
                echo "✅ Backend health check passed"
            else
                echo "❌ Backend health check failed"
            fi
            
            # Test frontend
            if curl -s http://localhost:8001 >/dev/null; then
                echo "✅ Frontend accessibility check passed"
            else
                echo "❌ Frontend accessibility check failed"
            fi
            
            # Test AI agents
            test_ai_agents
            ;;
        "help"|"-h"|"--help")
            echo "Multi-API Chat Services Manager"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start     Start all services (default)"
            echo "  stop      Stop all services"
            echo "  restart   Restart all services"
            echo "  status    Show service status"
            echo "  logs      Show recent logs"
            echo "  test      Run service tests"
            echo "  help      Show this help message"
            echo ""
            echo "Services:"
            echo "  Frontend: http://localhost:8001"
            echo "  Backend:  http://localhost:8002"
            ;;
        *)
            echo "❌ Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'echo ""; echo "🛑 Interrupted. Stopping services..."; $0 stop; exit 1' INT TERM

# Execute main function with all arguments
main "$@"
