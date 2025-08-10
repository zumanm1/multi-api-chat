#!/bin/bash

echo "🚀 Multi-API Chat Integration Test Runner"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    echo -n "Checking $service_name (port $port)... "
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    echo "Waiting for $service_name to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name is ready${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    echo -e "${RED}✗ $service_name failed to start within ${max_attempts}s${NC}"
    return 1
}

# Pre-flight checks
echo -e "${BLUE}Pre-flight Checks${NC}"
echo "=================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Node.js installed:$(node --version)${NC}"
fi

# Check if Python is installed  
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Python 3 installed: $(python3 --version)${NC}"
fi

# Check if required files exist
required_files=("final_integration_test.js" "backend_server.py" "index.html" "package.json")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Required file missing: $file${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ Found: $file${NC}"
    fi
done

echo

# Install dependencies if needed
echo -e "${BLUE}Installing Dependencies${NC}"
echo "======================"

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install Node.js dependencies${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Node.js dependencies already installed${NC}"
fi

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install Python dependencies${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Python virtual environment exists${NC}"
    source .venv/bin/activate
fi

echo

# Service startup
echo -e "${BLUE}Starting Services${NC}"
echo "=================="

# Start backend server
echo "Starting backend server..."
source .venv/bin/activate
python3 backend_server.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Start frontend server (simple HTTP server)
echo "Starting frontend server..."
python3 -m http.server 8001 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo

# Wait for services to be ready
echo -e "${BLUE}Waiting for Services${NC}"
echo "==================="

if ! wait_for_service "Backend" "http://localhost:8002/api/health"; then
    echo -e "${RED}Backend server failed to start${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

if ! wait_for_service "Frontend" "http://localhost:8001"; then
    echo -e "${RED}Frontend server failed to start${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo

# Run integration tests
echo -e "${BLUE}Running Integration Tests${NC}"
echo "=========================="

echo "Executing comprehensive frontend-backend integration tests..."
echo

# Run the test suite
node final_integration_test.js
TEST_EXIT_CODE=$?

echo

# Cleanup
echo -e "${BLUE}Cleaning Up${NC}"
echo "==========="

echo "Stopping services..."
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
sleep 2

# Force kill if still running
pkill -f "backend_server.py" 2>/dev/null
pkill -f "python3 -m http.server 8001" 2>/dev/null

echo -e "${GREEN}✓ Services stopped${NC}"

echo

# Final results
echo -e "${BLUE}Test Results${NC}"
echo "============"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 INTEGRATION TESTS PASSED${NC}"
    echo "📋 View detailed report: test_reports/final_integration_report.html"
    echo "📊 JSON data: test_reports/final_integration_report.json"
    echo "📝 Summary: TEST_SUMMARY_REPORT.md"
else
    echo -e "${RED}❌ INTEGRATION TESTS FAILED${NC}"
    echo "📋 Check detailed report: test_reports/final_integration_report.html"
    echo "📸 Screenshots: test_failures/"
fi

echo
echo -e "${BLUE}Test Runner Complete${NC}"
echo "===================="

exit $TEST_EXIT_CODE
