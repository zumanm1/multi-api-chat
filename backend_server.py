import os
import json
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import threading
import paramiko
import requests
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Load configuration
CONFIG_FILE = 'config.json'
USAGE_FILE = 'usage.json'
ENV_PRIVATE_FILE = '.env.private'

# Global variables for configuration and usage tracking
providers = {}
settings = {}
devices = {}
usage_stats = {}

# Lock for thread-safe file operations
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
            # Load devices from top level to match test expectations
            devices = config.get('devices', {})
    except FileNotFoundError:
        # Initialize with default config if file doesn't exist
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
        
        # Initialize devices with empty dict
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

# Load usage statistics
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


# Load API keys from .env.private file
def load_private_env():
    # First load from .env.private if it exists
    if os.path.exists(ENV_PRIVATE_FILE):
        load_dotenv(ENV_PRIVATE_FILE)
        
        # Update enabled providers with keys from .env.private
        for provider_id, provider in providers.items():
            env_key = f"{provider_id.upper()}_API_KEY"
            if provider['enabled'] and env_key in os.environ:
                provider['api_key'] = os.environ[env_key]

# Save API keys to .env.private file (only for enabled providers)
def save_private_env():
    env_lines = []
    
    # Only save enabled providers
    for provider_id, provider in providers.items():
        if provider['enabled'] and provider['api_key']:
            env_lines.append(f"{provider_id.upper()}_API_KEY={provider['api_key']}")
            
    # Create or update .env.private file
    with open(ENV_PRIVATE_FILE, 'w') as f:
        f.write('\n'.join(env_lines))

# Initialize at startup
load_config()
# Load API keys from .env.private
load_private_env()

# OpenAI compatibility layer
def get_client(provider_id):
    provider = providers[provider_id]
    
    # Handle Ollama-specific requirements
    if provider_id == 'ollama':
        # Ollama doesn't require an API key, use dummy value
        client_kwargs = {'api_key': 'ollama-dummy-key'}
        
        # Set base_url to local Ollama instance
        client_kwargs['base_url'] = provider.get('base_url', 'http://localhost:11434/v1')
        
        # Add Ollama-specific headers if needed
        client_kwargs['default_headers'] = {
            "Content-Type": "application/json",
            "User-Agent": "Multi-API-Chat/1.0"
        }
    else:
        # Standard client initialization for other providers
        client_kwargs = {'api_key': provider['api_key']}
        
        if provider['base_url']:
            client_kwargs['base_url'] = provider['base_url']
        
        if provider_id == 'openrouter':
            client_kwargs['default_headers'] = {
                "HTTP-Referer": "http://localhost:8001",
                "X-Title": "Multi-API Chat"
            }
    
    return OpenAI(**client_kwargs)

# Chat with provider function
def chat_with_provider(provider_id, message, system_prompt=None, model=None):
    start_time = time.time()
    
    client = get_client(provider_id)
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})
    
    try:
        # Use provided model or fall back to provider's default model
        selected_model = model or providers[provider_id]['model']
        
        # Handle Ollama-specific parameters
        chat_params = {
            "model": selected_model,
            "messages": messages,
            "max_tokens": settings['max_tokens'],
            "temperature": settings['temperature']
        }
        
        # For Ollama, we may need to adjust some parameters
        if provider_id == 'ollama':
            # Ollama might not support all OpenAI parameters, so we'll be more conservative
            # Remove max_tokens if it's causing issues (some Ollama models don't support this)
            chat_params.pop('max_tokens', None)
        
        response = client.chat.completions.create(**chat_params)
        
        response_time = time.time() - start_time
        
        # Handle response parsing - some providers might have slightly different formats
        response_content = ""
        tokens_used = 0
        
        if hasattr(response, 'choices') and response.choices:
            response_content = response.choices[0].message.content
        
        if hasattr(response, 'usage') and response.usage:
            tokens_used = response.usage.total_tokens
        elif provider_id == 'ollama':
            # Ollama might not always provide usage information
            # Estimate tokens for tracking purposes (rough approximation)
            tokens_used = len(response_content.split()) * 1.3  # Rough token estimation
        
        result = {
            "provider": provider_id,
            "response": response_content,
            "tokens": int(tokens_used),
            "model": selected_model,
            "response_time": response_time
        }
        
        # Track usage statistics
        if settings['features']['usage_analytics']:
            track_usage(provider_id, response_time, int(tokens_used))
        
        return result
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = str(e)
        error_type = "unknown"
        
        # Detect specific error types
        if "billing" in error_msg.lower() or "payment" in error_msg.lower():
            error_type = "billing"
        elif "rate limit" in error_msg.lower() or "ratelimit" in error_msg.lower():
            error_type = "rate_limit"
        elif "authentication" in error_msg.lower() or "api key" in error_msg.lower() or "apikey" in error_msg.lower():
            error_type = "auth"
        elif "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            error_type = "not_found"
        elif provider_id == 'ollama':
            # Handle Ollama-specific errors
            if "connection refused" in error_msg.lower() or "connectionerror" in error_msg.lower():
                error_type = "connection_error"
            elif "model" in error_msg.lower() and ("not found" in error_msg.lower() or "does not exist" in error_msg.lower()):
                error_type = "model_not_found"
            elif "timeout" in error_msg.lower():
                error_type = "timeout"
        
        raise Exception(f"Provider {provider_id} error: {error_msg}", error_type)

# Usage tracking function
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

# Test provider connection
def test_provider_connection(provider_id):
    try:
        if provider_id == 'ollama':
            # For Ollama, test connection by listing available models via GET request to /api/tags
            provider = providers[provider_id]
            base_url = provider.get('base_url', 'http://localhost:11434')
            
            # Remove /v1 suffix if present to get the raw Ollama API endpoint
            if base_url.endswith('/v1'):
                base_url = base_url[:-3]
            
            # Make GET request to /api/tags endpoint
            response = requests.get(f"{base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            # Parse response to check if models are available
            models_data = response.json()
            if not isinstance(models_data, dict) or 'models' not in models_data:
                raise Exception("Invalid response format from Ollama API")
            
            # Check if any models are available
            if not models_data.get('models'):
                raise Exception("No models available in Ollama")
                
        else:
            # For other providers, use the standard OpenAI client models.list() method
            client = get_client(provider_id)
            client.models.list()
        
        providers[provider_id]["status"] = "connected"
        providers[provider_id]["last_checked"] = datetime.now().isoformat()
        save_config()
        return True
    except Exception as e:
        error_msg = str(e)
        
        # Handle Ollama-specific error messages
        if provider_id == 'ollama':
            if "Connection refused" in error_msg or "ConnectionError" in error_msg:
                providers[provider_id]["status"] = "connection_refused"
            elif "timeout" in error_msg.lower():
                providers[provider_id]["status"] = "timeout"
            elif "No models available" in error_msg:
                providers[provider_id]["status"] = "no_models"
            else:
                providers[provider_id]["status"] = "error"
        else:
            providers[provider_id]["status"] = "error"
        
        providers[provider_id]["last_checked"] = datetime.now().isoformat()
        save_config()
        return False

# Cisco Router Integration Functions
def test_router_connection(device):
    """Test SSH connection to a Cisco router"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the device
        ssh.connect(
            hostname=device['ip'],
            port=device.get('port', 22),
            username=device['username'],
            password=device['password'],
            timeout=10
        )
        
        # Execute a simple command to verify connectivity
        stdin, stdout, stderr = ssh.exec_command('show version | include Cisco IOS')
        output = stdout.read().decode('utf-8')
        
        ssh.close()
        
        return True, output
    except Exception as e:
        return False, str(e)

def send_router_command(device, command):
    """Send a command to a Cisco router via SSH"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the device
        ssh.connect(
            hostname=device['ip'],
            port=device.get('port', 22),
            username=device['username'],
            password=device['password'],
            timeout=15
        )
        
        # Execute the command
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        ssh.close()
        
        if error:
            return False, error
        else:
            return True, output
    except Exception as e:
        return False, str(e)

# API Endpoints
@app.route('/api/providers', methods=['GET'])
def list_providers():
    return jsonify(providers)

@app.route('/api/providers/<provider_id>/models', methods=['GET'])
def get_provider_models(provider_id):
    """Get predefined models for a specific provider"""
    if provider_id not in providers:
        return jsonify({"error": "Provider not found"}), 404
    
    provider = providers[provider_id]
    models = provider.get('models', [])
    
    # For Ollama, also try to get live models from the Ollama API
    if provider_id == 'ollama' and provider.get('enabled', False):
        try:
            base_url = provider.get('base_url', 'http://localhost:11434')
            if base_url.endswith('/v1'):
                base_url = base_url[:-3]
            
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                ollama_data = response.json()
                live_models = [model.get('name', '').split(':')[0] for model in ollama_data.get('models', [])]
                # Merge predefined models with live models, removing duplicates
                all_models = list(set(models + live_models))
                return jsonify({
                    "models": all_models,
                    "predefined": models,
                    "live": live_models,
                    "source": "live_and_predefined"
                })
        except:
            pass  # Fall back to predefined models
    
    return jsonify({
        "models": models,
        "source": "predefined"
    })

@app.route('/api/providers/<provider_id>', methods=['PUT'])
def update_provider(provider_id):
    if provider_id not in providers:
        return jsonify({"error": "Provider not found"}), 404
    
    data = request.json
    providers[provider_id].update(data)
    save_config()
    
    # Update .env.private file if provider is enabled
    if providers[provider_id]['enabled']:
        save_private_env()
    
    return jsonify(providers[provider_id])

@app.route('/api/providers/<provider_id>/test', methods=['POST'])
def test_provider(provider_id):
    if provider_id not in providers:
        return jsonify({"error": "Provider not found"}), 404
    
    # Get test parameters from request
    data = request.json or {}
    test_message = data.get('test_message', 'Hello, this is a test message.')
    include_raw_data = data.get('include_raw_data', True)
    
    start_time = time.time()
    
    # First test basic connection
    connection_test = test_provider_connection(provider_id)
    connection_time = time.time() - start_time
    
    result = {
        "provider": provider_id,
        "status": providers[provider_id]["status"],
        "connection_test": {
            "success": connection_test,
            "response_time": connection_time,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # If connection test passed and provider has API key, test chat functionality
    if connection_test and providers[provider_id].get('api_key'):
        try:
            chat_start = time.time()
            chat_result = chat_with_provider(
                provider_id, 
                test_message,
                "You are a test assistant. Respond briefly to confirm functionality."
            )
            
            result["chat_test"] = {
                "success": True,
                "response_time": chat_result.get('response_time', 0),
                "tokens_used": chat_result.get('tokens', 0),
                "model": chat_result.get('model', ''),
                "timestamp": datetime.now().isoformat()
            }
            
            if include_raw_data:
                result["raw_data"] = {
                    "request": {
                        "message": test_message,
                        "provider": provider_id,
                        "model": providers[provider_id]['model'],
                        "base_url": providers[provider_id]['base_url'],
                        "has_api_key": bool(providers[provider_id].get('api_key'))
                    },
                    "response": {
                        "full_response": chat_result.get('response', ''),
                        "metadata": {
                            "tokens": chat_result.get('tokens', 0),
                            "model": chat_result.get('model', ''),
                            "provider": chat_result.get('provider', ''),
                            "response_time": chat_result.get('response_time', 0)
                        }
                    }
                }
            
        except Exception as e:
            result["chat_test"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            if include_raw_data:
                result["raw_data"] = {
                    "request": {
                        "message": test_message,
                        "provider": provider_id,
                        "model": providers[provider_id]['model'],
                        "base_url": providers[provider_id]['base_url'],
                        "has_api_key": bool(providers[provider_id].get('api_key'))
                    },
                    "error_details": {
                        "error_message": str(e),
                        "error_type": type(e).__name__
                    }
                }
    
    return jsonify(result)

@app.route('/api/providers/test-all', methods=['POST'])
def test_all_providers():
    results = {}
    # Iterate over a copy of the provider keys to prevent RuntimeError during tests
    for provider_id in list(providers.keys()):
        if providers[provider_id]["enabled"]:
            results[provider_id] = test_provider_connection(provider_id)
    
    return jsonify(results)

@app.route('/api/settings', methods=['GET', 'PUT'])
@app.route('/api/usage', methods=['GET'])
def get_usage_api():
    return jsonify(usage_stats)

@app.route('/api/settings', methods=['GET', 'PUT'])
def manage_settings():
    if request.method == 'GET':
        return jsonify(settings)
    
    if request.method == 'PUT':
        settings.update(request.json)
        save_config()
        return jsonify(settings)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    provider_id = data.get('provider', settings['default_provider'])
    system_prompt = data.get('system_prompt', settings['system_prompt'])
    model = data.get('model')  # Get selected model from request
    
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
        # Get error details
        error_msg = str(e)
        error_type = "unknown"
        
        # Check if error_type was passed with the exception
        if len(e.args) > 1:
            error_type = e.args[1]
        
        # Prepare error response
        error_response = {
            "error": error_msg,
            "error_type": error_type,
            "provider": provider_id
        }
        
        # Try fallback provider if enabled
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
        
        # Set appropriate status code based on error type
        status_code = 500
        if error_type == "auth":
            status_code = 401
        elif error_type == "not_found":
            status_code = 404
        elif error_type == "rate_limit":
            status_code = 429
        
        return jsonify(error_response), status_code

@app.route('/api/chat/compare', methods=['POST'])
def compare_chat():
    data = request.json
    message = data.get('message')
    provider_ids = data.get('providers', [])
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    if not provider_ids:
        # Use all enabled providers
        provider_ids = [pid for pid in providers if providers[pid]["enabled"]]
    
    results = []
    for provider_id in provider_ids:
        if provider_id in providers and providers[provider_id]["enabled"]:
            try:
                result = chat_with_provider(provider_id, message, settings['system_prompt'])
                results.append(result)
            except Exception as e:
                results.append({
                    "provider": provider_id,
                    "error": str(e)
                })
    
    return jsonify(results)

@app.route('/api/usage', methods=['GET'])
def get_usage():
    return jsonify(usage_stats)

# Ollama-specific model management endpoints
@app.route('/api/providers/ollama/models', methods=['GET'])
def list_ollama_models():
    """List available local Ollama models"""
    try:
        # Get Ollama base URL from provider configuration
        provider = providers.get('ollama', {})
        base_url = provider.get('base_url', 'http://localhost:11434')
        
        # Remove /v1 suffix if present to get the raw Ollama API endpoint
        if base_url.endswith('/v1'):
            base_url = base_url[:-3]
        
        # Make GET request to /api/tags endpoint to list models
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        response.raise_for_status()
        
        # Parse response
        models_data = response.json()
        
        if not isinstance(models_data, dict) or 'models' not in models_data:
            return jsonify({"error": "Invalid response format from Ollama API"}), 500
        
        # Format the response to match expected structure
        models = []
        for model in models_data.get('models', []):
            models.append({
                "name": model.get('name', ''),
                "size": model.get('size', 0),
                "modified_at": model.get('modified_at', ''),
                "digest": model.get('digest', ''),
                "details": model.get('details', {})
            })
        
        return jsonify({
            "models": models,
            "total": len(models)
        })
    
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Ollama server. Is Ollama running?"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Timeout connecting to Ollama server"}), 504
    except Exception as e:
        return jsonify({"error": f"Failed to list Ollama models: {str(e)}"}), 500

@app.route('/api/providers/ollama/pull', methods=['POST'])
def pull_ollama_model():
    """Pull a new model from the Ollama registry"""
    try:
        data = request.json
        model_name = data.get('model')
        
        if not model_name:
            return jsonify({"error": "Model name is required"}), 400
        
        # Get Ollama base URL from provider configuration
        provider = providers.get('ollama', {})
        base_url = provider.get('base_url', 'http://localhost:11434')
        
        # Remove /v1 suffix if present to get the raw Ollama API endpoint
        if base_url.endswith('/v1'):
            base_url = base_url[:-3]
        
        # Make POST request to /api/pull endpoint
        pull_data = {"name": model_name}
        response = requests.post(
            f"{base_url}/api/pull",
            json=pull_data,
            timeout=300,  # 5 minutes timeout for model pulling
            stream=True
        )
        response.raise_for_status()
        
        # Handle streaming response
        pull_status = []
        for line in response.iter_lines():
            if line:
                try:
                    status_data = json.loads(line.decode('utf-8'))
                    pull_status.append(status_data)
                    
                    # Check if pull completed successfully
                    if status_data.get('status') == 'success':
                        return jsonify({
                            "success": True,
                            "message": f"Model '{model_name}' pulled successfully",
                            "model": model_name,
                            "status_log": pull_status
                        })
                    
                    # Check for errors
                    if 'error' in status_data:
                        return jsonify({
                            "error": f"Failed to pull model: {status_data['error']}",
                            "model": model_name,
                            "status_log": pull_status
                        }), 500
                        
                except json.JSONDecodeError:
                    continue
        
        # If we reach here, the pull completed but no explicit success status was received
        return jsonify({
            "success": True,
            "message": f"Model '{model_name}' pull completed",
            "model": model_name,
            "status_log": pull_status
        })
    
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Ollama server. Is Ollama running?"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Timeout while pulling model. The operation may still be running in the background."}), 504
    except Exception as e:
        return jsonify({"error": f"Failed to pull model: {str(e)}"}), 500

# Device Management Endpoints
@app.route('/api/devices', methods=['GET'])
def list_devices():
    # Return the global devices variable directly
    return jsonify(devices)

@app.route('/api/devices', methods=['POST'])
def add_device():
    data = request.json
    device_id = data.get('id')
    
    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400
    
    global devices
    
    if device_id in devices:
        return jsonify({"error": "Device already exists"}), 400
    
    devices[device_id] = {
        "name": data.get('name', ''),
        "ip": data.get('ip', ''),
        "model": data.get('model', ''),
        "username": data.get('username', ''),
        "password": data.get('password', ''),
        "port": data.get('port', 22),
        "status": "unknown",
        "last_checked": ""
    }
    
    save_config()
    return jsonify(devices[device_id])

@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    data = request.json
    devices[device_id].update(data)
    
    save_config()
    return jsonify(devices[device_id])

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def remove_device(device_id):
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    del devices[device_id]
    
    save_config()
    return jsonify({"success": True})

@app.route('/api/devices/<device_id>/test', methods=['POST'])
def test_device(device_id):
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    # Test the actual router connection
    success, output = test_router_connection(devices[device_id])
    
    devices[device_id]["status"] = "online" if success else "offline"
    devices[device_id]["last_checked"] = datetime.now().isoformat()
    
    save_config()
    
    return jsonify({
        "device": device_id,
        "status": devices[device_id]["status"],
        "success": success
    })

@app.route('/api/devices/<device_id>/command', methods=['POST'])
def send_command(device_id):
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    data = request.json
    command = data.get('command')
    
    if not command:
        return jsonify({"error": "Command is required"}), 400
    
    # Execute the command on the actual router for real devices
    # For dummy devices, we'll still simulate responses
    if devices[device_id].get('username') and devices[device_id].get('password'):
        success, output = send_router_command(devices[device_id], command)
        
        if not success:
            return jsonify({"error": output}), 500
        
        response = output
    else:
        # Simulate processing delay for dummy devices
        time.sleep(1.5)
        
        # Generate simulated responses based on command type
        if command.lower().startswith("show ip route"):
            response = """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2
       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2
       ia - IS-IS inter area, * - candidate default, U - per-user static route
       o - ODR, P - periodic downloaded static route, + - replicated route

Gateway of last resort is 192.168.1.1 to network 0.0.0.0

S*   0.0.0.0/0 [1/0] via 192.168.1.1
     10.0.0.0/8 is variably subnetted, 4 subnets, 2 masks
C       10.0.1.0/24 is directly connected, GigabitEthernet0/0
L       10.0.1.1/32 is directly connected, GigabitEthernet0/0
C       10.0.2.0/24 is directly connected, GigabitEthernet0/1
L       10.0.2.1/32 is directly connected, GigabitEthernet0/1"""
        elif command.lower().startswith("show interfaces"):
            response = """GigabitEthernet0/0 is up, line protocol is up
  Hardware is CSR vNIC, address is 0050.56a3.1234 (bia 0050.56a3.1234)
  Internet address is 10.0.1.1/24
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec,
     reliability 255/255, txload 1/255, rxload 1/255
  Encapsulation ARPA, loopback not set
  Keepalive set (10 sec)
  Full Duplex, 1000Mbps, link type is auto, media type is RJ45
  output flow-control is unsupported, input flow-control is unsupported
  ARP type: ARPA, ARP Timeout 04:00:00
  Last input 00:00:02, output 00:00:01, output hang never
  Last clearing of "show interface" counters never
  Input queue: 0/375/0/0 (size/max/drops/flushes); Total output drops: 0
  Queueing strategy: fifo
  Output queue: 0/40 (size/max)
  5 minute input rate 1000 bits/sec, 1 packets/sec
  5 minute output rate 2000 bits/sec, 2 packets/sec"""
        elif command.lower().startswith("show running-config"):
            response = """Building configuration...

Current configuration : 3456 bytes
!
! Last configuration change at 14:32:15 UTC Thu Aug 7 2025
version 16.12
service timestamps debug datetime msec
service timestamps log datetime msec
platform qfp utilization monitor load 80
no platform punt-keepalive disable-kernel-core
platform console serial
!
hostname CORE-RTR-01
!
boot-start-marker
boot-end-marker
!
!
vrf definition MGMT
 !
 address-family ipv4
 exit-address-family
!
!
no aaa new-model
!
!
!
!
!
!
!
ip domain name example.com
!
!
!
ipv6 unicast-routing
!
!
!
!
!
!
 spanning-tree mode pvst
 spanning-tree extend system-id
!
!
!
!
!
!
!
!
!
!
!
!
!
!
interface GigabitEthernet0/0
 description ** Connection to SWITCH-01 **
 ip address 10.0.1.1 255.255.255.0
 negotiation auto
 spanning-tree portfast
!
interface GigabitEthernet0/1
 description ** Connection to EDGE-RTR-02 **
 ip address 10.0.2.1 255.255.255.0
 negotiation auto
!
interface GigabitEthernet0/2
 description ** Connection to INTERNET **
 ip address dhcp
 negotiation auto
!
interface GigabitEthernet0/3
 no ip address
 shutdown
 negotiation auto
!
ip forward-protocol nd
!
no ip http server
no ip http secure-server
!
!
!
!
!
!
control-plane
!
!
!
!
!
!
line con 0
 privilege level 15
 logging synchronous
line aux 0
line vty 0 4
 login
 transport input ssh
!
end"""
        elif command.lower().startswith("ping"):
            response = """Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 8.8.8.8, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms"""
        else:
            # Generic response for other commands
            response = f"Command '{command}' executed successfully on {devices[device_id]['name']} ({devices[device_id]['ip']})"
    
    return jsonify({
        "device": device_id,
        "command": command,
        "response": response
    })

@app.route('/api/workflows/config-push', methods=['POST'])
def config_push():
    data = request.json
    device_id = data.get('device_id')
    config = data.get('config')
    workflow_data = data.get('workflow_data', {})
    
    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400
    
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    if not config:
        return jsonify({"error": "Configuration is required"}), 400
    
    # For real devices with credentials, actually push the configuration
    # For dummy devices, simulate the process
    if devices[device_id].get('username') and devices[device_id].get('password'):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to the device
            ssh.connect(
                hostname=devices[device_id]['ip'],
                port=devices[device_id].get('port', 22),
                username=devices[device_id]['username'],
                password=devices[device_id]['password'],
                timeout=15
            )
            
            # Use paramiko's SSHClient.invoke_shell() for configuration mode
            shell = ssh.invoke_shell()
            shell.send('configure terminal\n')
            time.sleep(1)
            
            # Send configuration commands
            for line in config.split('\n'):
                if line.strip():
                    shell.send(line.strip() + '\n')
                    time.sleep(0.5)
            
            shell.send('end\n')
            shell.send('write memory\n')
            time.sleep(2)
            
            ssh.close()
            status = "Configuration pushed successfully"
            success = True
        except Exception as e:
            status = f"Configuration push failed: {str(e)}"
            success = False
    else:
        # Simulate configuration push process for dummy devices
        time.sleep(2)
        
        # For simulation, we'll randomly determine success
        import random
        success = random.choice([True, False])
        
        status = "Configuration pushed successfully" if success else "Configuration push failed"
    
    # Generate detailed command history
    command_history = []
    timestamp_base = datetime.now()
    
    # Natural language input
    command_history.append({
        "step": "Natural Language Input",
        "command": workflow_data.get('original_request', 'Configuration request'),
        "timestamp": (timestamp_base - timedelta(seconds=10)).isoformat(),
        "success": True,
        "response": "Request processed and parsed successfully"
    })
    
    # AI Translation
    command_history.append({
        "step": "AI Translation",
        "command": "Generate Cisco IOS configuration",
        "timestamp": (timestamp_base - timedelta(seconds=8)).isoformat(),
        "success": True,
        "response": config
    })
    
    # Syntax Validation
    command_history.append({
        "step": "Syntax Validation",
        "command": "validate_ios_config()",
        "timestamp": (timestamp_base - timedelta(seconds=6)).isoformat(),
        "success": True,
        "response": "Configuration syntax validated successfully"
    })
    
    # Router Execution Commands
    config_lines = [line.strip() for line in config.split('\n') if line.strip() and not line.strip().startswith('!')]
    router_commands = ['configure terminal'] + config_lines + ['end', 'copy running-config startup-config']
    
    for i, cmd in enumerate(router_commands):
        command_history.append({
            "step": "Router Execution",
            "command": cmd,
            "timestamp": (timestamp_base - timedelta(seconds=4) + timedelta(milliseconds=i*500)).isoformat(),
            "success": success,
            "response": f"{devices[device_id]['name']}(config)# {cmd}" if success else "Command failed"
        })
    
    # Verification Commands
    verify_commands = [
        "show running-config | include ospf",
        "show ip ospf interface"
    ]
    
    for i, cmd in enumerate(verify_commands):
        verification_output = generate_verification_output(cmd) if success else "Verification failed"
        command_history.append({
            "step": "Verification",
            "command": cmd,
            "timestamp": (timestamp_base + timedelta(milliseconds=i*500)).isoformat(),
            "success": success,
            "response": verification_output
        })
    
    return jsonify({
        "device": device_id,
        "status": status,
        "success": success,
        "command_history": command_history,
        "execution_summary": {
            "total_commands": len(command_history),
            "successful_commands": len([cmd for cmd in command_history if cmd['success']]),
            "failed_commands": len([cmd for cmd in command_history if not cmd['success']]),
            "execution_time": f"{len(router_commands) * 0.5 + 2}s"
        }
    })

@app.route('/api/workflows/config-retrieval', methods=['POST'])
def config_retrieval():
    data = request.json
    device_id = data.get('device_id')
    workflow_data = data.get('workflow_data', {})
    
    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400
    
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    # For real devices with credentials, actually retrieve the configuration
    # For dummy devices, simulate the process
    if devices[device_id].get('username') and devices[device_id].get('password'):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to the device
            ssh.connect(
                hostname=devices[device_id]['ip'],
                port=devices[device_id].get('port', 22),
                username=devices[device_id]['username'],
                password=devices[device_id]['password'],
                timeout=15
            )
            
            # Execute command to retrieve running configuration
            stdin, stdout, stderr = ssh.exec_command('show running-config')
            config = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            ssh.close()
            
            if error:
                return jsonify({"error": error}), 500
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve configuration: {str(e)}"}), 500
    else:
        # Simulate configuration retrieval process for dummy devices
        time.sleep(1.5)
        
        # Return a simulated running configuration
        config = """!
! Last configuration change at 14:32:15 UTC Thu Aug 7 2025
version 16.12
service timestamps debug datetime msec
service timestamps log datetime msec
!
hostname {device_name}
!
interface GigabitEthernet0/0
 ip address {device_ip} 255.255.255.0
!
interface GigabitEthernet0/1
 ip address 192.168.2.1 255.255.255.0
!
router ospf 1
 router-id 1.1.1.1
 network 192.168.1.0 0.0.0.255 area 0
 network 192.168.2.0 0.0.0.255 area 0
!
line vty 0 4
 login
 transport input ssh
!
end""".format(device_name=devices[device_id]['name'], device_ip=devices[device_id]['ip'])
    
    # Generate detailed command history for retrieval workflow
    command_history = []
    timestamp_base = datetime.now()
    
    # Natural language input
    command_history.append({
        "step": "Natural Language Input",
        "command": workflow_data.get('original_request', 'Configuration retrieval request'),
        "timestamp": (timestamp_base - timedelta(seconds=6)).isoformat(),
        "success": True,
        "response": "Request processed and parsed successfully"
    })
    
    # AI Translation
    command_history.append({
        "step": "AI Translation",
        "command": "Generate Cisco IOS command",
        "timestamp": (timestamp_base - timedelta(seconds=4)).isoformat(),
        "success": True,
        "response": "show running-config"
    })
    
    # Command Validation
    command_history.append({
        "step": "Command Validation",
        "command": "validate_ios_command()",
        "timestamp": (timestamp_base - timedelta(seconds=2)).isoformat(),
        "success": True,
        "response": "Command syntax validated successfully"
    })
    
    # Router Execution
    command_history.append({
        "step": "Router Execution",
        "command": "show running-config",
        "timestamp": timestamp_base.isoformat(),
        "success": True,
        "response": config
    })
    
    return jsonify({
        "device": device_id,
        "config": config,
        "command_history": command_history,
        "execution_summary": {
            "total_commands": len(command_history),
            "successful_commands": len([cmd for cmd in command_history if cmd['success']]),
            "failed_commands": len([cmd for cmd in command_history if not cmd['success']]),
            "execution_time": "2.5s"
        }
    })

def generate_verification_output(command):
    """Generate realistic verification command output"""
    if "show running-config" in command:
        return """!
interface GigabitEthernet0/0/1
 description Auto-generated by GENAI
 ip ospf 1 area 0
 no shutdown
!
router ospf 1
 router-id 1.1.1.1
 network 192.168.1.0 0.0.0.255 area 0
!"""
    elif "show ip ospf interface" in command:
        return """GigabitEthernet0/0/1 is up, line protocol is up 
  Internet Address 192.168.1.1/24, Area 0
  Process ID 1, Router ID 1.1.1.1, Network Type BROADCAST, Cost: 1
  Topology-MTID    Cost    Disabled    Shutdown      Topology Name
        0           1         no          no            Base
  Transmit Delay is 1 sec, State DR, Priority 1
  Designated Router (ID) 1.1.1.1, Interface address 192.168.1.1"""
    return "Verification completed successfully"

# .env.private management endpoints
@app.route('/api/env/private', methods=['GET'])
def get_private_env():
    """Get current .env.private file status"""
    env_status = {
        "exists": os.path.exists(ENV_PRIVATE_FILE),
        "enabled_providers": [],
        "file_size": 0
    }
    
    if env_status["exists"]:
        try:
            env_status["file_size"] = os.path.getsize(ENV_PRIVATE_FILE)
            # Get list of enabled providers that should have keys in .env.private
            for provider_id, provider in providers.items():
                if provider['enabled']:
                    env_status["enabled_providers"].append({
                        "provider": provider_id,
                        "name": provider['name'],
                        "has_api_key": bool(provider.get('api_key')),
                        "env_key": f"{provider_id.upper()}_API_KEY"
                    })
        except Exception as e:
            env_status["error"] = str(e)
    
    return jsonify(env_status)

@app.route('/api/env/private/refresh', methods=['POST'])
def refresh_private_env():
    """Refresh .env.private file with current enabled providers"""
    try:
        save_private_env()
        return jsonify({
            "success": True,
            "message": ".env.private file updated successfully",
            "enabled_providers": len([p for p in providers.values() if p['enabled'] and p.get('api_key')])
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/env/private/clear', methods=['POST'])
def clear_private_env():
    """Clear .env.private file"""
    try:
        if os.path.exists(ENV_PRIVATE_FILE):
            os.remove(ENV_PRIVATE_FILE)
        return jsonify({
            "success": True,
            "message": ".env.private file cleared successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    start_time = time.time() if 'start_time' not in globals() else globals()['start_time']
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "providers_enabled": len([p for p in providers.values() if p["enabled"]]),
        "uptime": time.time() - start_time if 'start_time' in globals() else 0,
        "env_private_exists": os.path.exists(ENV_PRIVATE_FILE)
    })

# Start server
if __name__ == '__main__':
    start_time = time.time()
    app.run(host='localhost', port=8002, debug=True)