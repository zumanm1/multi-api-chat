# Ollama Setup and Configuration Guide

This guide provides comprehensive instructions for setting up and configuring Ollama with the Multi-API Chat application, enabling local AI model inference without external API dependencies.

## Table of Contents

1. [What is Ollama?](#what-is-ollama)
2. [Prerequisites](#prerequisites)
3. [Installing Ollama](#installing-ollama)
4. [Running Ollama](#running-ollama)
5. [Downloading Models](#downloading-models)
6. [Application Configuration](#application-configuration)
7. [Testing the Integration](#testing-the-integration)
8. [Managing Models](#managing-models)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Configuration](#advanced-configuration)
11. [Performance Tuning](#performance-tuning)
12. [Security Considerations](#security-considerations)

## What is Ollama?

Ollama is a tool that allows you to run large language models locally on your machine. It provides:
- **Privacy**: All data stays on your local machine
- **Cost Efficiency**: No API charges for model usage
- **Offline Operation**: Works without internet connectivity
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API calls
- **Model Management**: Easy installation and management of various models

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows (WSL2)
- **RAM**: 8GB minimum (16GB+ recommended for larger models)
- **Storage**: 4GB+ free space per model
- **CPU**: x64 processor (ARM64 supported on macOS)
- **GPU**: Optional but recommended (NVIDIA CUDA, AMD ROCm, or Apple Metal)

### Python Environment
- Python 3.11+ (as per project requirements)
- All application dependencies from `requirements.txt` already installed

## Quick Setup (Recommended)

For a fully automated setup, use the provided script:

```bash
# Quick setup - installs Ollama, starts service, installs model, and configures app
bash setup_ollama.sh

# Check current status
bash setup_ollama.sh --status

# Get help
bash setup_ollama.sh --help
```

This script will:
1. Install Ollama if not already installed
2. Start the Ollama service
3. Install a recommended model (`llama3.2:1b`)
4. Update your application configuration
5. Test the integration

**If the quick setup works for you, you can skip to [Testing the Integration](#testing-the-integration). Otherwise, continue with the manual installation below.**

## Manual Installation

### Installing Ollama

#### Linux and WSL2
```bash
# Download and install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Alternative: Manual installation
# Download the binary and make it executable
curl -L https://ollama.ai/download/ollama-linux-amd64 -o ollama
chmod +x ollama
sudo mv ollama /usr/local/bin/
```

### macOS
```bash
# Using Homebrew (recommended)
brew install ollama

# Alternative: Download from website
# Visit https://ollama.ai/download and download the macOS installer
```

### Windows
1. Download the Ollama installer from https://ollama.ai/download
2. Run the installer and follow the setup wizard
3. Ollama will be available in your system PATH

### Verify Installation
```bash
# Check if Ollama is installed correctly
ollama --version

# Expected output: ollama version 0.x.x
```

## Running Ollama

### Start the Ollama Service

#### Linux/macOS
```bash
# Start Ollama server (runs in foreground)
ollama serve

# Alternative: Run as background service
nohup ollama serve > ollama.log 2>&1 &

# Check if server is running
curl http://localhost:11434/api/tags
```

#### Windows
```cmd
# Open Command Prompt or PowerShell
ollama serve

# The server will start on http://localhost:11434
```

### Service Configuration
By default, Ollama runs on:
- **Host**: `localhost` (127.0.0.1)
- **Port**: `11434`
- **API Endpoints**:
  - Native API: `http://localhost:11434/api/`
  - OpenAI-compatible API: `http://localhost:11434/v1/`

## Downloading Models

### Recommended Models for Getting Started

#### Small Models (Good for testing and resource-constrained systems)
```bash
# Llama 3.2 1B - Very fast, minimal RAM usage
ollama pull llama3.2:1b

# Phi-3 Mini - Microsoft's efficient small model
ollama pull phi3:mini

# Gemma 2B - Google's lightweight model
ollama pull gemma:2b
```

#### Medium Models (Balanced performance and resource usage)
```bash
# Llama 3.2 3B - Good balance of speed and capability
ollama pull llama3.2:3b

# Code Llama 7B - Specialized for code generation
ollama pull codellama:7b

# Mistral 7B - Excellent general-purpose model
ollama pull mistral:7b
```

#### Large Models (Best performance, requires more resources)
```bash
# Llama 3.1 8B - High-quality responses
ollama pull llama3.1:8b

# Llama 3.1 70B - Excellent but requires significant RAM
ollama pull llama3.1:70b
```

### Model Pull Command Examples
```bash
# Pull the default version of a model
ollama pull llama3.2

# Pull a specific version/size
ollama pull llama3.2:1b
ollama pull llama3.2:3b
ollama pull llama3.2:8b

# Pull with specific quantization
ollama pull llama3.2:7b-q4_0
ollama pull llama3.2:7b-q8_0
```

### Verify Model Installation
```bash
# List all installed models
ollama list

# Test a model directly
ollama run llama3.2:1b "Hello, how are you?"

# Check model details
ollama show llama3.2:1b
```

## Application Configuration

### Enable Ollama Provider

1. **Start the Application**:
   ```bash
   # Start backend server
   python backend_server.py
   
   # In another terminal, start frontend
   bash start_frontend.sh
   ```

2. **Open Settings Interface**:
   - Navigate to `http://localhost:7001`
   - Click on "Settings" or go to `http://localhost:7001/settings.html`

3. **Configure Ollama Provider**:
   - Find the "Ollama" provider section
   - Enable the provider by checking the checkbox
   - Set the base URL: `http://localhost:11434/v1`
   - Select your installed model (e.g., `llama3.2:1b`)
   - Leave API key empty (not required for local Ollama)
   - Click "Test Connection" to verify

### Manual Configuration (config.json)

Alternatively, edit the `config.json` file directly:

```json
{
  "providers": {
    "ollama": {
      "name": "Ollama",
      "enabled": true,
      "api_key": "",
      "model": "llama3.2:1b",
      "base_url": "http://localhost:11434/v1",
      "status": "connected",
      "last_checked": "2025-01-09T10:00:00Z"
    }
  }
}
```

### Available Configuration Options

| Setting | Description | Default | Notes |
|---------|-------------|---------|--------|
| `enabled` | Enable/disable provider | `false` | Set to `true` to use Ollama |
| `model` | Model to use | `llama3.2` | Must match installed model name |
| `base_url` | Ollama server URL | `http://localhost:11434/v1` | Include `/v1` for OpenAI compatibility |
| `api_key` | Authentication key | `""` | Leave empty for local Ollama |

## Testing the Integration

### Quick Test via Web Interface
1. Start both Ollama and the application
2. Go to the main chat interface
3. Select "Ollama" as the provider
4. Send a test message: "Hello, can you introduce yourself?"
5. Verify you receive a response from your local model

### Test via API
```bash
# Test provider connection
curl -X POST http://localhost:7002/api/providers/ollama/test

# Test chat completion
curl -X POST http://localhost:7002/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "provider": "ollama",
    "system_prompt": "You are a helpful AI assistant."
  }'
```

### Run Comprehensive Tests
```bash
# Run all Ollama-related tests
bash run_ollama_tests.sh

# Run only unit tests (no external dependencies)
python -m pytest tests/test_backend.py -k "ollama" -v

# Run integration tests (requires running servers)
python test_ollama_integration.py
```

## Managing Models

### List Available Models Online
```bash
# Search for available models
ollama search llama

# Browse models at https://ollama.ai/models
```

### Model Management Commands
```bash
# List installed models
ollama list

# Remove a model
ollama rm llama3.2:1b

# Update a model
ollama pull llama3.2:1b

# Show model information
ollama show llama3.2:1b

# Copy a model with new name
ollama cp llama3.2:1b my-custom-model
```

### Via Application API
```bash
# List models through the application
curl http://localhost:7002/api/providers/ollama/models

# Pull a new model through the application
curl -X POST http://localhost:7002/api/providers/ollama/pull \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2:1b"}'
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "Connection Refused" Error
**Problem**: Application can't connect to Ollama
**Solutions**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama
ollama serve

# Check for port conflicts
netstat -tulpn | grep :11434
```

#### 2. "No Models Available" Error
**Problem**: Ollama is running but no models are installed
**Solutions**:
```bash
# Check installed models
ollama list

# If empty, install a model
ollama pull llama3.2:1b

# Verify model is available
curl http://localhost:11434/api/tags
```

#### 3. Slow Response Times
**Problem**: Models are responding slowly
**Solutions**:
- Use smaller models (1B-3B parameters)
- Enable GPU acceleration if available
- Increase system RAM
- Close other resource-intensive applications

#### 4. Out of Memory Errors
**Problem**: System runs out of memory when using large models
**Solutions**:
```bash
# Use smaller quantized models
ollama pull llama3.2:1b-q4_0  # 4-bit quantization

# Check system resources
free -h  # Linux/macOS
systeminfo  # Windows
```

#### 5. Port Already in Use
**Problem**: Port 11434 is already occupied
**Solutions**:
```bash
# Find what's using the port
lsof -i :11434  # macOS/Linux
netstat -ano | findstr :11434  # Windows

# Kill the process or use different port
OLLAMA_HOST=localhost:11435 ollama serve
```

### Application-Specific Troubleshooting

#### Provider Test Fails
1. Verify Ollama is running: `curl http://localhost:11434/api/tags`
2. Check model is installed: `ollama list`
3. Test direct model access: `ollama run llama3.2:1b "Hello"`
4. Check application logs for detailed error messages

#### Chat Requests Timeout
- Increase timeout settings in the application
- Use smaller, faster models
- Check system resources during inference

#### Model Not Found Error
- Ensure model name in config matches exactly: `ollama list`
- Re-pull the model if corrupted: `ollama pull model_name`
- Check for typos in model name

### Debug Mode
Enable detailed logging for troubleshooting:

```bash
# Start Ollama with verbose logging
OLLAMA_DEBUG=1 ollama serve

# Run application with debug mode
DEBUG=1 python backend_server.py
```

## Advanced Configuration

### Custom Model Configuration

#### Create Custom Modelfile
```bash
# Create a custom model configuration
cat > Modelfile << EOF
FROM llama3.2:1b

# Set custom parameters
PARAMETER temperature 0.8
PARAMETER top_p 0.9
PARAMETER stop "<|end|>"

# Set custom system prompt
SYSTEM You are a helpful AI assistant specialized in technical support.
EOF

# Create the custom model
ollama create my-support-bot -f Modelfile

# Use the custom model in the application
# Set model to "my-support-bot" in config.json
```

#### Model Parameters
Common parameters you can customize:

| Parameter | Description | Default | Range |
|-----------|-------------|---------|--------|
| `temperature` | Response randomness | 0.7 | 0.0-1.0 |
| `top_p` | Nucleus sampling | 0.9 | 0.0-1.0 |
| `top_k` | Top-k sampling | 40 | 1-100 |
| `repeat_penalty` | Repetition penalty | 1.1 | 0.0-2.0 |
| `seed` | Random seed | -1 | Any integer |

### Network Configuration

#### Remote Access
To allow remote access to Ollama:

```bash
# Allow connections from any IP
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Allow specific IP range
OLLAMA_HOST=192.168.1.0/24:11434 ollama serve
```

**Security Warning**: Only enable remote access on trusted networks.

#### Proxy Configuration
If behind a proxy:

```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Start Ollama
ollama serve
```

### Environment Variables

Key environment variables for Ollama:

```bash
# Server configuration
export OLLAMA_HOST=localhost:11434
export OLLAMA_ORIGINS="*"  # CORS origins

# Resource limits
export OLLAMA_NUM_PARALLEL=1  # Parallel requests
export OLLAMA_MAX_LOADED_MODELS=1  # Loaded models
export OLLAMA_MAX_QUEUE=512  # Request queue size

# Storage location
export OLLAMA_MODELS=/custom/model/path

# GPU configuration
export OLLAMA_GPU_LAYERS=35  # GPU layers
export CUDA_VISIBLE_DEVICES=0  # Specific GPU
```

## Performance Tuning

### Hardware Optimization

#### GPU Acceleration
```bash
# NVIDIA GPU (CUDA)
# Ensure CUDA is installed and accessible
nvidia-smi

# AMD GPU (ROCm) - Linux only
# Install ROCm according to AMD documentation

# Apple Silicon (Metal) - macOS only
# Automatically used when available
```

#### RAM Optimization
- **Minimum**: 8GB for 1B-3B models
- **Recommended**: 16GB for 7B models
- **High-end**: 32GB+ for 13B+ models

#### CPU Optimization
```bash
# Set CPU affinity (Linux)
taskset -c 0-7 ollama serve

# Adjust thread count
export OMP_NUM_THREADS=8
```

### Model Selection for Performance

| Model Size | RAM Usage | Speed | Quality | Use Case |
|------------|-----------|-------|---------|----------|
| 1B | 2GB | Very Fast | Good | Testing, simple tasks |
| 3B | 4GB | Fast | Better | General chat, basic coding |
| 7B | 8GB | Medium | Good | Complex tasks, detailed responses |
| 13B | 16GB | Slow | Better | High-quality responses |
| 70B | 64GB+ | Very Slow | Excellent | Production applications |

### Application Performance Settings

In `config.json`, adjust these settings for better performance:

```json
{
  "settings": {
    "temperature": 0.7,
    "max_tokens": 1000,
    "features": {
      "speed_optimization": true,
      "cost_optimization": true
    }
  }
}
```

## Security Considerations

### Network Security
- **Default**: Ollama binds to localhost only
- **Firewall**: Ensure port 11434 is not exposed externally
- **VPN**: Use VPN for remote access instead of public exposure

### Data Privacy
- **Local Processing**: All data stays on your machine
- **No Telemetry**: Ollama doesn't send usage data
- **Audit Trail**: Monitor access logs if needed

### Model Security
- **Source Verification**: Only download models from trusted sources
- **Model Scanning**: Scan downloaded models for security issues
- **Version Control**: Keep track of model versions and updates

### Access Control
```bash
# Restrict file permissions
chmod 600 ~/.ollama/models/*

# Run as non-root user
sudo -u ollama ollama serve

# Use systemd for service management (Linux)
sudo systemctl enable ollama
sudo systemctl start ollama
```

### Monitoring and Logging
```bash
# Monitor resource usage
htop
nvidia-smi  # For GPU monitoring

# Log all requests (development only)
OLLAMA_DEBUG=1 ollama serve > ollama.log 2>&1

# Monitor API access
tail -f /var/log/nginx/access.log  # If using reverse proxy
```

## Integration with CI/CD

### Automated Testing
```bash
#!/bin/bash
# ci-ollama-test.sh - CI script for Ollama integration

# Start Ollama in background
ollama serve &
OLLAMA_PID=$!

# Wait for service to start
sleep 10

# Install test model
ollama pull llama3.2:1b

# Run tests
python -m pytest tests/test_backend.py -k "ollama" -v

# Cleanup
kill $OLLAMA_PID
```

### Docker Integration
```dockerfile
# Dockerfile.ollama
FROM ollama/ollama:latest

# Install models
RUN ollama pull llama3.2:1b

# Expose port
EXPOSE 11434

# Start service
CMD ["ollama", "serve"]
```

## Getting Help

### Documentation Resources
- **Official Ollama Documentation**: https://ollama.ai/docs
- **Model Library**: https://ollama.ai/models
- **GitHub Repository**: https://github.com/jmorganca/ollama

### Community Support
- **Discord**: Ollama Community Discord
- **GitHub Issues**: Report bugs and feature requests
- **Reddit**: r/LocalLLaMA community

### Application-Specific Support
- **Project Documentation**: See other `.md` files in this repository
- **Test Suite**: Run `bash run_ollama_tests.sh` for diagnostics
- **Debug Logs**: Enable debug mode for detailed logging

---

## Quick Reference Commands

```bash
# Installation verification
ollama --version

# Start service
ollama serve

# Install model
ollama pull llama3.2:1b

# Test model
ollama run llama3.2:1b "Hello"

# List models
ollama list

# Remove model
ollama rm llama3.2:1b

# Application test
curl http://localhost:7002/api/providers/ollama/test

# Full test suite
bash run_ollama_tests.sh
```

This completes the comprehensive Ollama setup and configuration guide. Follow these instructions to successfully integrate Ollama with your Multi-API Chat application for local AI inference capabilities.
