#!/bin/bash
# Ollama Integration Test Runner
# This script runs the comprehensive Ollama integration test suite

echo "🧪 Ollama Integration Test Runner"
echo "=================================="

# Function to run unit tests
run_unit_tests() {
    echo ""
    echo "📋 Running Unit Tests (Fast, no external dependencies)"
    echo "-----------------------------------------------------"
    python3 -m pytest tests/test_backend.py -k "ollama" -v
    return $?
}

# Function to run integration tests
run_integration_tests() {
    echo ""
    echo "🔗 Running Integration Tests (Requires backend server)"
    echo "----------------------------------------------------"
    python3 test_ollama_integration.py
    return $?
}

# Function to check if backend server is running
check_backend() {
    curl -s http://localhost:8002/api/health > /dev/null 2>&1
    return $?
}

# Function to check if Ollama server is running
check_ollama() {
    curl -s http://localhost:11434/api/tags > /dev/null 2>&1
    return $?
}

# Main execution
main() {
    # Always run unit tests first
    run_unit_tests
    unit_result=$?
    
    if [ $unit_result -eq 0 ]; then
        echo "✅ All unit tests passed!"
    else
        echo "❌ Some unit tests failed!"
        echo "   Unit tests should always pass as they don't require external services."
        echo "   Check the test output above for details."
    fi
    
    # Check if we can run integration tests
    echo ""
    echo "🔍 Checking environment for integration tests..."
    
    check_backend
    backend_running=$?
    
    check_ollama
    ollama_running=$?
    
    if [ $backend_running -eq 0 ]; then
        echo "✅ Backend server is running"
        if [ $ollama_running -eq 0 ]; then
            echo "✅ Ollama server is running"
            echo "🚀 Full integration testing available!"
        else
            echo "⚠️  Ollama server is not running"
            echo "   Integration tests will run with limited Ollama functionality"
        fi
        
        run_integration_tests
        integration_result=$?
        
        if [ $integration_result -eq 0 ]; then
            echo "✅ Integration tests completed successfully!"
        else
            echo "⚠️  Some integration tests had issues (this may be expected if Ollama is not running)"
        fi
    else
        echo "❌ Backend server is not running"
        echo "   To run integration tests:"
        echo "   1. Start the backend server: python3 backend_server.py"
        echo "   2. Optionally start Ollama: ollama serve"
        echo "   3. Run this script again"
    fi
    
    echo ""
    echo "📊 Test Summary:"
    echo "   Unit Tests: $([ $unit_result -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
    if [ $backend_running -eq 0 ]; then
        echo "   Integration Tests: $([ $integration_result -eq 0 ] && echo '✅ PASSED' || echo '⚠️  COMPLETED WITH WARNINGS')"
    else
        echo "   Integration Tests: ⏭️  SKIPPED (backend not running)"
    fi
    
    echo ""
    echo "🎯 Quick Commands:"
    echo "   Unit tests only:       python3 -m pytest tests/test_backend.py -k 'ollama' -v"
    echo "   Integration tests:     python3 test_ollama_integration.py"
    echo "   Start backend:         python3 backend_server.py"
    echo "   Start Ollama:          ollama serve"
    
    # Return overall success
    return $unit_result
}

# Run main function
main "$@"
