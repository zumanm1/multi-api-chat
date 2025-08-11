"""
Backend Core Server - Main server without complex AI integrations to avoid circular imports
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import threading
import paramiko
import requests
from dotenv import load_dotenv
from requests.exceptions import ConnectionError, Timeout, RequestException

# Import our clean AI core module
from ai_core import (
    initialize_ai_core,
    get_cached_ai_status,
    ai_health_check,
    get_installation_command,
    fallback_ai_chat,
    fallback_ai_analytics,
    fallback_ai_operation
)

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_api_chat.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration files
CONFIG_FILE = 'config.json'
USAGE_FILE = 'usage.json'
ENV_PRIVATE_FILE = '.env.private'

# Global variables
providers = {}
settings = {}
devices = {}
usage_stats = {}

# Thread locks
config_lock = threading.Lock()
usage_lock = threading.Lock()

# Load configuration at startup
def load_config():
    global providers, settings, devices
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            providers = config.get('providers', {})
            settings = config.get('settings', {})
            devices = config.get('devices', {})
    except FileNotFoundError:
        # Initialize with default config
        providers = {
            "openai": {
                "name": "OpenAI",
                "enabled": False,
                "api_key": "",
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1",
                "status": "disconnected",
                "last_checked": ""
            },
            "groq": {
                "name": "Groq",
                "enabled": False,
                "api_key": "",
                "model": "llama-3.1-70b-versatile",
                "base_url": "https://api.groq.com/openai/v1",
                "status": "disconnected",
                "last_checked": ""
            },
            "cerebras": {
                "name": "Cerebras",
                "enabled": False,
                "api_key": "",
                "model": "llama-4-scout-wse-3",
                "base_url": "https://api.cerebras.ai/v1",
                "status": "disconnected",
                "last_checked": ""
            },
            "sambanova": {
                "name": "SambaNova",
                "enabled": False,
                "api_key": "",
                "model": "llama-3.3-70b",
                "base_url": "https://api.sambanova.ai/v1",
                "status": "disconnected",
                "last_checked": ""
            },
            "anthropic": {
                "name": "Anthropic",
                "enabled": False,
                "api_key": "",
                "model": "claude-sonnet-4",
                "base_url": "https://api.anthropic.com/v1/openai",
                "status": "disconnected",
                "last_checked": ""
            },
            "openrouter": {
                "name": "OpenRouter",
                "enabled": False,
                "api_key": "",
                "model": "openrouter/auto",
                "base_url": "https://openrouter.ai/api/v1",
                "status": "disconnected",
                "last_checked": ""
            },
            "ollama": {
                "name": "Ollama",
                "enabled": False,
                "api_key": "",
                "model": "llama3.2",
                "base_url": "http://localhost:11434/v1",
                "status": "disconnected",
                "last_checked": ""
            }
        }
        
        settings = {
            "default_provider": "groq",
            "fallback_provider": None,
            "temperature": 0.7,
            "max_tokens": 1000,
            "system_prompt": "You are a helpful AI assistant.",
            "features": {
                "auto_fallback": True,
                "speed_optimization": False,
                "cost_optimization": False,
                "multi_provider_compare": False,
                "usage_analytics": True
            }
        }
        
        devices = {}
        save_config()

def save_config():
    with config_lock:
        config = {
            'providers': providers,
            'settings': settings,
            'devices': devices
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

def load_usage():
    global usage_stats
    try:
        with open(USAGE_FILE, 'r') as f:
            usage_stats = json.load(f)
    except FileNotFoundError:
        usage_stats = {}
        save_usage()

def save_usage():
    with usage_lock:
        with open(USAGE_FILE, 'w') as f:
            json.dump(usage_stats, f, indent=2)

def load_private_env():
    if os.path.exists(ENV_PRIVATE_FILE):
        load_dotenv(ENV_PRIVATE_FILE)
        for provider_id, provider in providers.items():
            env_key = f"{provider_id.upper()}_API_KEY"
            if provider['enabled'] and env_key in os.environ:
                provider['api_key'] = os.environ[env_key]

def save_private_env():
    env_lines = []
    for provider_id, provider in providers.items():
        if provider['enabled'] and provider['api_key']:
            env_lines.append(f"{provider_id.upper()}_API_KEY={provider['api_key']}")
    
    with open(ENV_PRIVATE_FILE, 'w') as f:
        f.write('\\n'.join(env_lines))

# OpenAI client wrapper
def get_client(provider_id):
    provider = providers[provider_id]
    
    if provider_id == 'ollama':
        client_kwargs = {'api_key': 'ollama-dummy-key'}
        client_kwargs['base_url'] = provider.get('base_url', 'http://localhost:11434/v1')
        client_kwargs['default_headers'] = {
            "Content-Type": "application/json",
            "User-Agent": "Multi-API-Chat/1.0"
        }
    else:
        client_kwargs = {'api_key': provider['api_key']}
        if provider['base_url']:
            client_kwargs['base_url'] = provider['base_url']
        
        if provider_id == 'openrouter':
            client_kwargs['default_headers'] = {
                "HTTP-Referer": "http://localhost:8001",
                "X-Title": "Multi-API Chat"
            }
    
    return OpenAI(**client_kwargs)

# Chat function
def chat_with_provider(provider_id, message, system_prompt=None, model=None):
    start_time = time.time()
    
    client = get_client(provider_id)
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})
    
    try:
        selected_model = model or providers[provider_id]['model']
        
        chat_params = {
            "model": selected_model,
            "messages": messages,
            "max_tokens": settings['max_tokens'],
            "temperature": settings['temperature']
        }
        
        if provider_id == 'ollama':
            chat_params.pop('max_tokens', None)
        
        response = client.chat.completions.create(**chat_params)
        response_time = time.time() - start_time
        
        response_content = ""
        tokens_used = 0
        
        if hasattr(response, 'choices') and response.choices:
            response_content = response.choices[0].message.content
        
        if hasattr(response, 'usage') and response.usage:
            tokens_used = response.usage.total_tokens
        elif provider_id == 'ollama':
            tokens_used = len(response_content.split()) * 1.3
        
        result = {
            "provider": provider_id,
            "response": response_content,
            "tokens": int(tokens_used),
            "model": selected_model,
            "response_time": response_time
        }
        
        if settings['features']['usage_analytics']:
            track_usage(provider_id, response_time, int(tokens_used))
        
        return result
        
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = str(e)
        error_type = "unknown"
        
        if "billing" in error_msg.lower() or "payment" in error_msg.lower():
            error_type = "billing"
        elif "rate limit" in error_msg.lower():
            error_type = "rate_limit"
        elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            error_type = "auth"
        elif "not found" in error_msg.lower():
            error_type = "not_found"
        
        raise Exception(f"Provider {provider_id} error: {error_msg}", error_type)

def track_usage(provider_id, response_time, tokens):
    timestamp = datetime.now().isoformat()
    date_key = datetime.now().strftime('%Y-%m-%d')
    
    if date_key not in usage_stats:
        usage_stats[date_key] = {}
    
    if provider_id not in usage_stats[date_key]:
        usage_stats[date_key][provider_id] = {
            "requests": 0,
            "tokens": 0,
            "total_response_time": 0
        }
    
    usage_stats[date_key][provider_id]["requests"] += 1
    usage_stats[date_key][provider_id]["tokens"] += tokens
    usage_stats[date_key][provider_id]["total_response_time"] += response_time
    
    save_usage()

def test_provider_connection(provider_id):
    try:
        client = get_client(provider_id)
        client.models.list()
        providers[provider_id]["status"] = "connected"
        providers[provider_id]["last_checked"] = datetime.now().isoformat()
        save_config()
        return True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Provider connection test failed for {provider_id}: {error_msg}")
        providers[provider_id]["status"] = "error"
        providers[provider_id]["last_checked"] = datetime.now().isoformat()
        save_config()
        return False

# API Routes
@app.route('/api/providers', methods=['GET'])
def list_providers():
    return jsonify(providers)

@app.route('/api/providers/<provider_id>', methods=['PUT'])
def update_provider(provider_id):
    if provider_id not in providers:
        return jsonify({"error": "Provider not found"}), 404
    
    data = request.json
    providers[provider_id].update(data)
    save_config()
    
    if providers[provider_id]['enabled']:
        save_private_env()
    
    return jsonify(providers[provider_id])

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    provider_id = data.get('provider', settings['default_provider'])
    system_prompt = data.get('system_prompt', settings['system_prompt'])
    model = data.get('model')
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    if provider_id not in providers:
        return jsonify({"error": "Provider not found"}), 404
    
    if not providers[provider_id]["enabled"]:
        return jsonify({"error": "Provider is disabled"}), 400
    
    try:
        result = chat_with_provider(provider_id, message, system_prompt, model)
        return jsonify(result)
    except Exception as e:
        error_msg = str(e)
        error_type = "unknown"
        
        if len(e.args) > 1:
            error_type = e.args[1]
        
        error_response = {
            "error": error_msg,
            "error_type": error_type,
            "provider": provider_id
        }
        
        # Try fallback provider
        if settings['features']['auto_fallback'] and settings['fallback_provider']:
            fallback_id = settings['fallback_provider']
            if fallback_id in providers and providers[fallback_id]["enabled"]:
                try:
                    result = chat_with_provider(fallback_id, message, system_prompt)
                    result["fallback_used"] = True
                    return jsonify(result)
                except Exception as fallback_e:
                    fallback_error_type = "unknown"
                    if len(fallback_e.args) > 1:
                        fallback_error_type = fallback_e.args[1]
                    
                    error_response["fallback_error"] = str(fallback_e)
                    error_response["fallback_error_type"] = fallback_error_type
                    error_response["fallback_provider"] = fallback_id
                    return jsonify(error_response), 500
        
        status_code = 500
        if error_type == "auth":
            status_code = 401
        elif error_type == "not_found":
            status_code = 404
        elif error_type == "rate_limit":
            status_code = 429
        
        return jsonify(error_response), status_code

@app.route('/api/settings', methods=['GET', 'PUT'])
def manage_settings():
    if request.method == 'GET':
        return jsonify(settings)
    
    if request.method == 'PUT':
        settings.update(request.json)
        save_config()
        return jsonify(settings)

@app.route('/api/usage', methods=['GET'])
def get_usage():
    return jsonify(usage_stats)

# AI Status endpoints using our clean AI core
@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """Get AI status using our clean core module"""
    status = get_cached_ai_status()
    health = ai_health_check()
    
    return jsonify({
        "ai_status": status,
        "health_check": health,
        "installation_command": get_installation_command(),
        "note": "AI integration temporarily simplified to resolve circular imports"
    })

# Fallback AI endpoints
@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Fallback AI chat endpoint"""
    data = request.json
    message = data.get('message', '')
    context = data.get('context', {})
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    result = fallback_ai_chat(message, context)
    return jsonify(result)

@app.route('/api/ai/analytics', methods=['POST'])
def ai_analytics():
    """Fallback AI analytics endpoint"""
    data = request.json
    message = data.get('message', '')
    context = data.get('context', {})
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    result = fallback_ai_analytics(message, context)
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health_check():
    ai_status_data = get_cached_ai_status()
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "providers_enabled": len([p for p in providers.values() if p["enabled"]]),
        "env_private_exists": os.path.exists(ENV_PRIVATE_FILE),
        "ai_packages_available": ai_status_data["ai_available"],
        "ai_status": ai_status_data["status_message"],
        "mode": "core_mode",
        "note": "Running in core mode to avoid circular imports"
    }
    
    return jsonify(health_data)

# Initialize and start server
def initialize_server():
    """Initialize the server"""
    logger.info("Initializing Backend Core Server...")
    load_config()
    load_private_env()
    load_usage()
    
    # Initialize AI core
    ai_status = initialize_ai_core()
    logger.info(f"AI Status: {ai_status['status_message']}")
    
    logger.info("Backend Core Server initialized successfully")

if __name__ == '__main__':
    initialize_server()
    start_time = time.time()
    logger.info("Starting Backend Core Server on port 8002...")
    app.run(host='localhost', port=8002, debug=True)
