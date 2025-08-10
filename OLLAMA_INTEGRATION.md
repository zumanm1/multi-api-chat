# Ollama Integration Features

## Overview

This document describes the Ollama-specific model management functionality implemented in `backend_server.py`. The integration allows users to manage their local Ollama models directly from the application.

## New API Endpoints

### 1. List Ollama Models
- **Endpoint**: `GET /api/providers/ollama/models`
- **Description**: Lists all available local Ollama models
- **Response Format**:
```json
{
  "models": [
    {
      "name": "llama3.2:latest",
      "size": 2048576000,
      "modified_at": "2025-01-08T10:30:00Z",
      "digest": "sha256:abc123...",
      "details": {
        "format": "gguf",
        "family": "llama",
        "families": ["llama"],
        "parameter_size": "3.2B",
        "quantization_level": "Q4_0"
      }
    }
  ],
  "total": 1
}
```
- **Error Responses**:
  - `503`: Ollama server not running
  - `504`: Timeout connecting to Ollama
  - `500`: Invalid response format or other errors

### 2. Pull Ollama Model
- **Endpoint**: `POST /api/providers/ollama/pull`
- **Description**: Pulls a new model from the Ollama registry
- **Request Body**:
```json
{
  "model": "llama3.2:1b"
}
```
- **Response Format** (Success):
```json
{
  "success": true,
  "message": "Model 'llama3.2:1b' pulled successfully",
  "model": "llama3.2:1b",
  "status_log": [
    {
      "status": "pulling manifest",
      "digest": "sha256:...",
      "total": 1024,
      "completed": 1024
    }
  ]
}
```
- **Error Responses**:
  - `400`: Model name is required
  - `503`: Ollama server not running
  - `504`: Timeout while pulling (operation may continue in background)
  - `500`: Pull failed with error details

### 3. Enhanced Chat Endpoint
- **Endpoint**: `POST /api/chat`
- **Description**: Updated to better handle Ollama's response format
- **Ollama-Specific Enhancements**:
  - Removes `max_tokens` parameter which some Ollama models don't support
  - Provides better error handling for Ollama-specific errors
  - Estimates token usage when Ollama doesn't provide usage statistics
  - Handles connection errors, model not found, and timeout scenarios

## Implementation Details

### Ollama Server Communication

The implementation uses Ollama's native API endpoints (not the OpenAI-compatible ones) for model management:
- Model listing: `GET http://localhost:11434/api/tags`
- Model pulling: `POST http://localhost:11434/api/pull`

For chat functionality, it continues to use Ollama's OpenAI-compatible endpoint:
- Chat completions: `POST http://localhost:11434/v1/chat/completions`

### Configuration

The Ollama provider is configured in the `providers` section with these defaults:
```json
{
  "ollama": {
    "name": "Ollama",
    "enabled": false,
    "api_key": "",
    "model": "llama3.2",
    "base_url": "http://localhost:11434/v1",
    "status": "disconnected",
    "last_checked": ""
  }
}
```

### Error Handling

The implementation includes comprehensive error handling:
- Connection refused: When Ollama server is not running
- Timeout: For long-running operations like model pulling
- Model not found: When specified model doesn't exist
- Invalid response format: When Ollama returns unexpected data

### Token Estimation

For Ollama providers that don't return token usage, the system estimates tokens using:
```python
tokens_used = len(response_content.split()) * 1.3  # Rough token estimation
```

## Usage Examples

### List Models
```bash
curl -X GET http://localhost:8002/api/providers/ollama/models
```

### Pull a Model
```bash
curl -X POST http://localhost:8002/api/providers/ollama/pull \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2:1b"}'
```

### Chat with Ollama
```bash
curl -X POST http://localhost:8002/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "provider": "ollama",
    "system_prompt": "You are a helpful AI assistant."
  }'
```

## Testing

A test script `test_ollama_endpoints.py` is provided to verify the functionality:

```bash
python test_ollama_endpoints.py
```

The test script checks:
- Ollama server availability
- Model listing endpoint
- Model pulling endpoint (with small model)
- Chat endpoint functionality

## Prerequisites

To use these features:
1. Install Ollama: https://ollama.ai/
2. Start Ollama server: `ollama serve`
3. Pull at least one model: `ollama pull llama3.2:1b`
4. Enable Ollama provider in the application settings

## Benefits

This integration provides users with:
- **Local Model Management**: View and download models without leaving the application
- **No Internet Dependency**: Once models are downloaded, chat works completely offline
- **Privacy**: All data stays on the local machine
- **Cost Efficiency**: No API costs for using local models
- **Fast Responses**: Local inference can be faster than API calls for smaller models

## Technical Notes

- The implementation handles both Ollama's native API and OpenAI-compatible endpoints appropriately
- Streaming responses from model pulling are properly parsed
- The chat endpoint gracefully falls back to token estimation when usage data isn't available
- Connection timeouts are handled to prevent hanging requests
- The system maintains compatibility with existing OpenAI client architecture

## Future Enhancements

Potential improvements could include:
- Model deletion endpoint
- Model information/details endpoint
- Streaming chat responses for Ollama
- Model performance metrics
- Automatic model updates
