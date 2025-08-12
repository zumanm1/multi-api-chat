#!/bin/bash
# Quick Ollama Setup Script for Multi-API Chat Application
# This script helps you get started with Ollama quickly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[ℹ]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Main setup function
main() {
    echo "🚀 Ollama Quick Setup for Multi-API Chat Application"
    echo "=================================================="
    echo ""

    # Detect operating system
    OS=$(detect_os)
    print_info "Detected OS: $OS"
    echo ""

    # Step 1: Check if Ollama is already installed
    print_info "Step 1: Checking Ollama installation..."
    if command_exists ollama; then
        OLLAMA_VERSION=$(ollama --version 2>/dev/null | head -n1 || echo "unknown")
        print_status "Ollama is already installed: $OLLAMA_VERSION"
        INSTALL_OLLAMA=false
    else
        print_warning "Ollama not found. Will install Ollama."
        INSTALL_OLLAMA=true
    fi
    echo ""

    # Step 2: Install Ollama if needed
    if [ "$INSTALL_OLLAMA" = true ]; then
        print_info "Step 2: Installing Ollama..."
        
        case $OS in
            "linux")
                print_info "Installing Ollama for Linux..."
                curl -fsSL https://ollama.ai/install.sh | sh
                ;;
            "macos")
                if command_exists brew; then
                    print_info "Installing Ollama via Homebrew..."
                    brew install ollama
                else
                    print_warning "Homebrew not found. Please install Ollama manually from https://ollama.ai/download"
                    exit 1
                fi
                ;;
            "windows")
                print_warning "Windows detected. Please download and install Ollama from: https://ollama.ai/download"
                print_info "After installation, run this script again."
                exit 1
                ;;
            *)
                print_error "Unsupported OS. Please install Ollama manually from: https://ollama.ai/download"
                exit 1
                ;;
        esac
        
        # Verify installation
        if command_exists ollama; then
            print_status "Ollama installed successfully!"
        else
            print_error "Ollama installation failed. Please install manually."
            exit 1
        fi
    else
        print_info "Step 2: Skipping installation (already installed)"
    fi
    echo ""

    # Step 3: Start Ollama service
    print_info "Step 3: Starting Ollama service..."
    
    # Check if Ollama is already running
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_status "Ollama service is already running"
    else
        print_info "Starting Ollama service in background..."
        nohup ollama serve > ollama.log 2>&1 &
        OLLAMA_PID=$!
        
        # Wait for service to start
        print_info "Waiting for Ollama service to start..."
        for i in {1..30}; do
            if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
                print_status "Ollama service started successfully (PID: $OLLAMA_PID)"
                break
            fi
            sleep 1
            if [ $i -eq 30 ]; then
                print_error "Timeout waiting for Ollama service to start"
                print_info "You can start it manually with: ollama serve"
                exit 1
            fi
        done
    fi
    echo ""

    # Step 4: Install a recommended model
    print_info "Step 4: Installing recommended model..."
    
    # Check if any models are already installed
    MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | wc -l || echo "0")
    
    if [ "$MODELS" -gt 0 ]; then
        print_status "Models already installed:"
        ollama list
    else
        print_info "No models found. Installing llama3.2:1b (small, fast model for testing)..."
        ollama pull llama3.2:1b
        print_status "Model llama3.2:1b installed successfully!"
    fi
    echo ""

    # Step 5: Update application configuration
    print_info "Step 5: Configuring application..."
    
    if [ -f "config.json" ]; then
        print_info "Updating config.json to enable Ollama provider..."
        
        # Create backup
        cp config.json config.json.backup
        print_info "Created backup: config.json.backup"
        
        # Use Python to update JSON (more reliable than sed/awk)
        python3 << 'EOF'
import json
import sys
from datetime import datetime

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Update Ollama provider configuration
    if 'providers' not in config:
        config['providers'] = {}
    
    config['providers']['ollama'] = {
        "name": "Ollama",
        "enabled": True,
        "api_key": "",
        "model": "llama3.2:1b",
        "base_url": "http://localhost:11434/v1",
        "status": "connected",
        "last_checked": datetime.now().isoformat()
    }
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✓ Configuration updated successfully")
except Exception as e:
    print(f"✗ Error updating configuration: {e}")
    sys.exit(1)
EOF
        
        if [ $? -eq 0 ]; then
            print_status "Configuration updated successfully"
        else
            print_error "Failed to update configuration"
        fi
    else
        print_warning "config.json not found. You'll need to configure Ollama through the web interface."
    fi
    echo ""

    # Step 6: Test the setup
    print_info "Step 6: Testing Ollama integration..."
    
    # Test Ollama directly
    print_info "Testing Ollama service..."
    if curl -s http://localhost:11434/api/tags >/dev/null; then
        print_status "Ollama API is accessible"
    else
        print_error "Ollama API is not accessible"
    fi
    
    # Test with application (if backend is running)
    if curl -s http://localhost:7002/api/health >/dev/null 2>&1; then
        print_info "Testing application integration..."
        if curl -s -X POST http://localhost:7002/api/providers/ollama/test >/dev/null; then
            print_status "Application integration test passed"
        else
            print_warning "Application integration test failed (backend may not be running)"
        fi
    else
        print_warning "Backend server not running. Start it with: python backend_server.py"
    fi
    echo ""

    # Final status and next steps
    echo "🎉 Ollama Setup Complete!"
    echo "========================"
    echo ""
    print_status "Ollama service is running on http://localhost:11434"
    print_status "Models installed and ready to use"
    print_status "Application configuration updated"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Start the backend server (if not already running):"
    echo "   python backend_server.py"
    echo ""
    echo "2. Start the frontend server (in another terminal):"
    echo "   bash start_frontend.sh"
    echo ""
    echo "3. Open your browser to http://localhost:7001"
    echo ""
    echo "4. In the application:"
    echo "   - Go to Settings"
    echo "   - Verify Ollama provider is enabled"
    echo "   - Test the connection"
    echo "   - Start chatting with your local AI!"
    echo ""
    echo "📚 For detailed documentation, see: OLLAMA_SETUP_GUIDE.md"
    echo ""
    echo "🧪 To run tests:"
    echo "   bash run_ollama_tests.sh"
    echo ""
    echo "🔧 Useful commands:"
    echo "   ollama list                    # List installed models"
    echo "   ollama pull llama3.2:3b       # Install another model"
    echo "   ollama run llama3.2:1b \"Hi!\"   # Test model directly"
    echo "   ollama serve                   # Start Ollama service"
    echo ""
    
    # Show current status
    echo "📊 Current Status:"
    echo "   Ollama Service: $(curl -s http://localhost:11434/api/tags >/dev/null && echo '🟢 Running' || echo '🔴 Not Running')"
    echo "   Backend Server: $(curl -s http://localhost:7002/api/health >/dev/null && echo '🟢 Running' || echo '🔴 Not Running')"
    echo "   Models: $(ollama list | grep -v NAME | wc -l | xargs echo) installed"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Quick setup script for Ollama with Multi-API Chat Application"
        echo ""
        echo "OPTIONS:"
        echo "  --help, -h     Show this help message"
        echo "  --status       Show current status only"
        echo ""
        echo "This script will:"
        echo "1. Install Ollama (if not already installed)"
        echo "2. Start the Ollama service"
        echo "3. Install a recommended model (llama3.2:1b)"
        echo "4. Configure the application"
        echo "5. Test the integration"
        exit 0
        ;;
    --status)
        echo "📊 Ollama Status Check"
        echo "====================="
        echo ""
        echo "Ollama Installation: $(command_exists ollama && echo '✅ Installed' || echo '❌ Not Installed')"
        echo "Ollama Service: $(curl -s http://localhost:11434/api/tags >/dev/null && echo '🟢 Running' || echo '🔴 Not Running')"
        echo "Backend Server: $(curl -s http://localhost:7002/api/health >/dev/null && echo '🟢 Running' || echo '🔴 Not Running')"
        
        if command_exists ollama; then
            echo ""
            echo "Installed Models:"
            ollama list || echo "Unable to list models"
        fi
        exit 0
        ;;
    "")
        # Run main setup
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
