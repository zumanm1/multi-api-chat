#!/bin/bash

# Comprehensive Test Runner for Multi-API Chat Application
# This script runs both backend (pytest) and frontend (Puppeteer) tests

set -e  # Exit on any error

# Configuration
BACKEND_PORT=7002
FRONTEND_PORT=7001
TEST_TIMEOUT=300  # 5 minutes
PROJECT_DIR="$(pwd)"
VENV_PATH="${PROJECT_DIR}/.venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    lsof -ti:$port > /dev/null 2>&1
}

# Function to kill processes on a port
kill_port() {
    local port=$1
    if check_port $port; then
        log_warning "Killing existing processes on port $port"
        lsof -ti:$port | xargs kill -9 > /dev/null 2>&1 || true
        sleep 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local timeout=$3
    
    log_info "Waiting for $service_name to be ready at $url..."
    
    for ((i=0; i<timeout; i++)); do
        if curl -s "$url" > /dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi
        sleep 1
    done
    
    log_error "$service_name failed to start within $timeout seconds"
    return 1
}

# Function to setup Python virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."
    
    if [ ! -d "$VENV_PATH" ]; then
        log_info "Creating virtual environment at $VENV_PATH"
        python3.11 -m venv "$VENV_PATH"
    fi
    
    source "$VENV_PATH/bin/activate"
    
    log_info "Installing Python dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    pip install -q -r requirements-testing.txt
    
    log_success "Python environment ready"
}

# Function to setup Node.js dependencies
setup_node() {
    log_info "Setting up Node.js dependencies..."
    
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # Install additional testing dependencies if needed
    if ! npm list chai > /dev/null 2>&1; then
        log_info "Installing Mocha, Chai for Puppeteer tests..."
        npm install --save-dev mocha chai
    fi
    
    log_success "Node.js environment ready"
}

# Function to start the backend server
start_backend() {
    log_info "Starting backend server on port $BACKEND_PORT..."
    
    kill_port $BACKEND_PORT
    
    source "$VENV_PATH/bin/activate"
    
    # Start backend in background
    export FLASK_APP=backend_server.py
    export FLASK_ENV=development
    python backend_server.py > backend_test.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to be ready
    if wait_for_service "http://localhost:$BACKEND_PORT/api/health" "Backend" 30; then
        log_success "Backend server started with PID $BACKEND_PID"
        echo $BACKEND_PID > backend_test.pid
        return 0
    else
        log_error "Backend server failed to start"
        return 1
    fi
}

# Function to start the frontend server
start_frontend() {
    log_info "Starting frontend server on port $FRONTEND_PORT..."
    
    kill_port $FRONTEND_PORT
    
    # Start simple HTTP server for frontend
    python3 -m http.server $FRONTEND_PORT > frontend_test.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for frontend to be ready
    if wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend" 15; then
        log_success "Frontend server started with PID $FRONTEND_PID"
        echo $FRONTEND_PID > frontend_test.pid
        return 0
    else
        log_error "Frontend server failed to start"
        return 1
    fi
}

# Function to run pytest backend tests
run_backend_tests() {
    log_info "Running backend unit tests with pytest..."
    
    source "$VENV_PATH/bin/activate"
    
    # Create test reports directory
    mkdir -p test-reports/backend
    
    # Run comprehensive backend tests
    pytest tests/test_comprehensive_backend.py \
        -v \
        --tb=short \
        --maxfail=5 \
        --durations=10 \
        --cov=backend_server \
        --cov-report=html:test-reports/backend/coverage \
        --cov-report=term-missing \
        --junit-xml=test-reports/backend/junit.xml \
        > test-reports/backend/pytest-output.log 2>&1
    
    BACKEND_EXIT_CODE=$?
    
    if [ $BACKEND_EXIT_CODE -eq 0 ]; then
        log_success "Backend tests completed successfully"
    else
        log_error "Backend tests failed with exit code $BACKEND_EXIT_CODE"
    fi
    
    return $BACKEND_EXIT_CODE
}

# Function to run Puppeteer frontend tests
run_frontend_tests() {
    log_info "Running frontend integration tests with Puppeteer..."
    
    # Create test reports directory
    mkdir -p test-reports/frontend
    
    # Run Puppeteer tests using Mocha
    npx mocha tests/test_comprehensive_frontend.test.js \
        --timeout $((TEST_TIMEOUT * 1000)) \
        --reporter json \
        > test-reports/frontend/mocha-results.json 2>&1
    
    FRONTEND_EXIT_CODE=$?
    
    if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
        log_success "Frontend tests completed successfully"
    else
        log_error "Frontend tests failed with exit code $FRONTEND_EXIT_CODE"
    fi
    
    return $FRONTEND_EXIT_CODE
}

# Function to cleanup test processes
cleanup() {
    log_info "Cleaning up test processes..."
    
    # Kill backend if running
    if [ -f backend_test.pid ]; then
        BACKEND_PID=$(cat backend_test.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            log_info "Stopping backend server (PID: $BACKEND_PID)"
            kill $BACKEND_PID
        fi
        rm -f backend_test.pid
    fi
    
    # Kill frontend if running
    if [ -f frontend_test.pid ]; then
        FRONTEND_PID=$(cat frontend_test.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            log_info "Stopping frontend server (PID: $FRONTEND_PID)"
            kill $FRONTEND_PID
        fi
        rm -f frontend_test.pid
    fi
    
    # Clean up port processes
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    
    log_info "Cleanup completed"
}

# Function to generate test report
generate_report() {
    log_info "Generating comprehensive test report..."
    
    cat > test-reports/comprehensive-test-report.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-API Chat - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 8px; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; }
        .success { border-left-color: #28a745; background: #d4edda; }
        .error { border-left-color: #dc3545; background: #f8d7da; }
        .info { border-left-color: #17a2b8; background: #d1ecf1; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .badge { padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; }
        .badge.success { background-color: #28a745; }
        .badge.error { background-color: #dc3545; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Multi-API Chat Platform - Comprehensive Test Report</h1>
        <p>Generated on: $(date)</p>
        <p>Project Directory: $(pwd)</p>
    </div>
    
    <div class="section info">
        <h2>Test Summary</h2>
        <table>
            <tr><th>Test Suite</th><th>Status</th><th>Details</th></tr>
            <tr>
                <td>Backend Unit Tests (pytest)</td>
                <td><span class="badge $([ $BACKEND_TESTS_PASSED -eq 1 ] && echo 'success' || echo 'error')">$([ $BACKEND_TESTS_PASSED -eq 1 ] && echo 'PASSED' || echo 'FAILED')</span></td>
                <td>Tests: backend_server.py functionality</td>
            </tr>
            <tr>
                <td>Frontend Integration Tests (Puppeteer)</td>
                <td><span class="badge $([ $FRONTEND_TESTS_PASSED -eq 1 ] && echo 'success' || echo 'error')">$([ $FRONTEND_TESTS_PASSED -eq 1 ] && echo 'PASSED' || echo 'FAILED')</span></td>
                <td>Tests: UI functionality and API integration</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Backend Test Results</h2>
        <p>Backend tests $([ $BACKEND_TESTS_PASSED -eq 1 ] && echo 'completed successfully' || echo 'failed')</p>
        <p><strong>Coverage Report:</strong> test-reports/backend/coverage/index.html</p>
        <p><strong>JUnit XML:</strong> test-reports/backend/junit.xml</p>
        <p><strong>Full Output:</strong> test-reports/backend/pytest-output.log</p>
    </div>
    
    <div class="section">
        <h2>Frontend Test Results</h2>
        <p>Frontend tests $([ $FRONTEND_TESTS_PASSED -eq 1 ] && echo 'completed successfully' || echo 'failed')</p>
        <p><strong>Test Screenshots:</strong> test-reports/frontend/ (failure screenshots)</p>
        <p><strong>Mocha Results:</strong> test-reports/frontend/mocha-results.json</p>
    </div>
    
    <div class="section">
        <h2>Test Coverage Areas</h2>
        <ul>
            <li><strong>Backend:</strong> API endpoints, provider management, device management, AI agents integration, workflow orchestration</li>
            <li><strong>Frontend:</strong> Page loading, chat functionality, provider settings, responsive design, performance</li>
            <li><strong>Integration:</strong> Frontend-backend communication, error handling, data consistency</li>
        </ul>
    </div>
</body>
</html>
EOF
    
    log_success "Test report generated: test-reports/comprehensive-test-report.html"
}

# Main execution function
main() {
    log_info "Starting comprehensive test suite for Multi-API Chat Platform"
    
    # Setup trap for cleanup on exit
    trap cleanup EXIT
    
    # Initialize test results
    BACKEND_TESTS_PASSED=0
    FRONTEND_TESTS_PASSED=0
    
    # Step 1: Setup environments
    setup_venv
    setup_node
    
    # Step 2: Start services
    if ! start_backend; then
        log_error "Failed to start backend server"
        exit 1
    fi
    
    if ! start_frontend; then
        log_error "Failed to start frontend server"
        exit 1
    fi
    
    # Step 3: Run backend tests
    if run_backend_tests; then
        BACKEND_TESTS_PASSED=1
    fi
    
    # Step 4: Run frontend tests
    if run_frontend_tests; then
        FRONTEND_TESTS_PASSED=1
    fi
    
    # Step 5: Generate comprehensive report
    generate_report
    
    # Step 6: Print summary
    echo
    echo "=========================================="
    echo "COMPREHENSIVE TEST RESULTS SUMMARY"
    echo "=========================================="
    echo
    echo "Backend Tests (pytest):     $([ $BACKEND_TESTS_PASSED -eq 1 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${RED}FAILED${NC}")"
    echo "Frontend Tests (Puppeteer): $([ $FRONTEND_TESTS_PASSED -eq 1 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${RED}FAILED${NC}")"
    echo
    echo "Test Reports Location: test-reports/"
    echo "- Backend Coverage: test-reports/backend/coverage/index.html"
    echo "- Frontend Screenshots: test-reports/frontend/"
    echo "- Comprehensive Report: test-reports/comprehensive-test-report.html"
    echo
    
    # Exit with appropriate code
    if [ $BACKEND_TESTS_PASSED -eq 1 ] && [ $FRONTEND_TESTS_PASSED -eq 1 ]; then
        log_success "All tests passed successfully!"
        exit 0
    else
        log_error "Some tests failed. Check the reports for details."
        exit 1
    fi
}

# Script usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Comprehensive test runner for Multi-API Chat Platform"
    echo
    echo "OPTIONS:"
    echo "  --backend-only    Run only backend tests"
    echo "  --frontend-only   Run only frontend tests"
    echo "  --no-cleanup      Don't cleanup processes after tests"
    echo "  --help           Show this help message"
    echo
    echo "Examples:"
    echo "  $0                Run all tests"
    echo "  $0 --backend-only Run only backend pytest tests"
    echo "  $0 --frontend-only Run only frontend Puppeteer tests"
}

# Parse command line arguments
BACKEND_ONLY=false
FRONTEND_ONLY=false
NO_CLEANUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --no-cleanup)
            NO_CLEANUP=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Modify cleanup behavior based on arguments
if [ "$NO_CLEANUP" = true ]; then
    trap '' EXIT
fi

# Run main function with argument handling
if [ "$BACKEND_ONLY" = true ]; then
    log_info "Running backend tests only..."
    setup_venv
    start_backend
    run_backend_tests
    BACKEND_EXIT_CODE=$?
    [ "$NO_CLEANUP" = false ] && cleanup
    exit $BACKEND_EXIT_CODE
elif [ "$FRONTEND_ONLY" = true ]; then
    log_info "Running frontend tests only..."
    setup_venv
    setup_node
    start_backend  # Frontend tests need backend
    start_frontend
    run_frontend_tests
    FRONTEND_EXIT_CODE=$?
    [ "$NO_CLEANUP" = false ] && cleanup
    exit $FRONTEND_EXIT_CODE
else
    main
fi
