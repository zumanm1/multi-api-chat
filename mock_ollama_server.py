#!/usr/bin/env python3
"""
Mock Ollama Server for Testing
This simple server simulates Ollama API responses for testing the model fetching functionality
"""

import json
import time
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Mock models data
MOCK_MODELS = [
    {
        "name": "llama3.2:latest",
        "modified_at": "2024-01-15T10:30:00Z",
        "size": 4661224448,
        "digest": "sha256:a110482c9f4",
        "details": {
            "format": "gguf",
            "family": "llama",
            "families": ["llama"],
            "parameter_size": "3B",
            "quantization_level": "Q4_0"
        }
    },
    {
        "name": "llama3:latest",
        "modified_at": "2024-01-10T15:45:00Z",
        "size": 8934738976,
        "digest": "sha256:b221c9e2b84",
        "details": {
            "format": "gguf",
            "family": "llama",
            "families": ["llama"],
            "parameter_size": "8B",
            "quantization_level": "Q4_0"
        }
    },
    {
        "name": "codellama:latest",
        "modified_at": "2024-01-08T12:20:00Z",
        "size": 7365960704,
        "digest": "sha256:c887abc123f",
        "details": {
            "format": "gguf", 
            "family": "llama",
            "families": ["llama"],
            "parameter_size": "7B",
            "quantization_level": "Q4_0"
        }
    }
]

@app.route('/api/tags', methods=['GET'])
def get_models():
    """Mock Ollama models endpoint"""
    print(f"[MOCK OLLAMA] Received request for models at {datetime.now()}")
    return jsonify({
        "models": MOCK_MODELS
    })

@app.route('/api/version', methods=['GET'])
def get_version():
    """Mock Ollama version endpoint"""
    print(f"[MOCK OLLAMA] Received version request at {datetime.now()}")
    return jsonify({
        "version": "0.1.7"
    })

@app.route('/api/generate', methods=['POST'])
def generate():
    """Mock generate endpoint"""
    data = request.json
    model = data.get('model', 'llama3:latest')
    prompt = data.get('prompt', '')
    
    print(f"[MOCK OLLAMA] Generate request for model: {model}")
    
    # Simple mock response
    response = f"This is a mock response from {model} for prompt: {prompt[:50]}..."
    
    return jsonify({
        "model": model,
        "created_at": datetime.now().isoformat(),
        "response": response,
        "done": True
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Mock chat endpoint"""
    data = request.json
    model = data.get('model', 'llama3:latest')
    messages = data.get('messages', [])
    
    print(f"[MOCK OLLAMA] Chat request for model: {model}")
    
    # Simple mock response
    return jsonify({
        "model": model,
        "created_at": datetime.now().isoformat(),
        "message": {
            "role": "assistant",
            "content": f"This is a mock response from {model}. I received {len(messages)} messages."
        },
        "done": True
    })

@app.route('/v1/chat/completions', methods=['POST'])
def openai_chat_completions():
    """OpenAI-compatible chat completions endpoint for mock Ollama"""
    data = request.json
    model = data.get('model', 'llama3:latest')
    messages = data.get('messages', [])
    
    print(f"[MOCK OLLAMA] OpenAI-compatible chat request for model: {model}")
    
    # Extract the last user message for response generation
    user_message = ""
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            user_message = msg.get('content', '')
            break
    
    # Generate a mock response based on the user's message
    response_text = f"Hello! This is a mock response from {model}. I understand you said: '{user_message[:50]}...' I'm working correctly through the Ollama integration!"
    
    # Return OpenAI-compatible format
    return jsonify({
        "id": f"chatcmpl-mock-{datetime.now().timestamp()}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": sum(len(msg.get('content', '').split()) for msg in messages),
            "completion_tokens": len(response_text.split()),
            "total_tokens": sum(len(msg.get('content', '').split()) for msg in messages) + len(response_text.split())
        }
    })

@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "mock-ollama",
        "models_available": len(MOCK_MODELS),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Mock Ollama Server")
    print("=====================================")
    print("Available endpoints:")
    print("- GET  /api/tags     - List models")
    print("- GET  /api/version  - Get version") 
    print("- POST /api/generate - Generate text")
    print("- POST /api/chat     - Chat completion")
    print("- GET  /health       - Health check")
    print("")
    print(f"Mock models available: {len(MOCK_MODELS)}")
    for model in MOCK_MODELS:
        print(f"  - {model['name']}")
    print("")
    print("Server running on http://localhost:11434")
    print("=====================================")
    
    app.run(host='localhost', port=11434, debug=False)
