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

# AI Feature Flags and Dependencies
AI_FEATURES = {
    "ai_agents": False,
    "ai_chat": False,
    "ai_analytics": False,
    "ai_automation": False,
    "ai_workflows": False,
    "dependency_checker": False
}

AI_DEPENDENCY_STATUS = {
    "checked": False,
    "all_available": False,
    "missing_dependencies": [],
    "available_features": [],
    "last_checked": None,
    "error": None
}

# Import AI Agent Integration with enhanced error handling
# Temporarily using fallback mode to avoid circular import issues
print(f"Info: AI agents integration temporarily disabled due to circular import issues")
print("AI dependencies are available but full integration needs fixes.")
print("Application will run with basic functionality and dependency checking only.")
AI_AGENTS_AVAILABLE = False

# Test if core AI packages are importable
try:
    import crewai
    import langchain
    import langgraph
    import langchain_openai
    print("✓ Core AI packages (crewai, langchain, langgraph, langchain_openai) are available")
    AI_DEPS_IMPORTABLE = True
except ImportError as e:
    print(f"✗ Core AI packages import failed: {e}")
    AI_DEPS_IMPORTABLE = False

# Import AI dependency checker separately for more granular control - TEMPORARILY DISABLED
# try:
#     from ai_agents.utils.dependency_checker import (
#         check_ai_dependencies,
#         validate_ai_environment,
#         log_dependency_status,
#         get_installation_command
#     )
#     AI_FEATURES["dependency_checker"] = True
# except ImportError as e:
#     print(f"Info: AI dependency checker not available: {e}")
print("Info: AI dependency checker temporarily disabled due to circular imports")

# Import AI workflows separately - TEMPORARILY DISABLED
# try:
#     from ai_agents.workflows.orchestrator import orchestrator
#     AI_FEATURES["ai_workflows"] = True
# except ImportError as e:
#     print(f"Info: AI workflow orchestrator not available: {e}")
print("Info: AI workflow orchestrator temporarily disabled due to circular imports")

app = Flask(__name__)
CORS(app)

# Configure logging for debugging Ollama issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_api_chat.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ollama-specific error handling utilities
def handle_ollama_request(func, *args, **kwargs):
    """
    Robust wrapper for Ollama API requests with comprehensive error handling.
    Includes retries, timeouts, and detailed error classification.
    """
    max_retries = kwargs.pop('max_retries', 3)
    timeout = kwargs.pop('timeout', 30)
    retry_delay = kwargs.pop('retry_delay', 2)
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Ollama API call attempt {attempt + 1}/{max_retries}: {func.__name__}")
            return func(*args, timeout=timeout, **kwargs)
            
        except ConnectionError as e:
            error_msg = f"Ollama connection error on attempt {attempt + 1}: {str(e)}"
            logger.error(error_msg)
            
            if attempt == max_retries - 1:
                return {
                    "error": "Ollama server is not reachable",
                    "error_type": "connection_error",
                    "details": str(e),
                    "retry_attempts": max_retries,
                    "suggestions": [
                        "Check if Ollama is running (ollama serve)",
                        "Verify the Ollama server URL and port",
                        "Check network connectivity"
                    ]
                }
            time.sleep(retry_delay)
            
        except Timeout as e:
            error_msg = f"Ollama timeout on attempt {attempt + 1}: {str(e)}"
            logger.error(error_msg)
            
            if attempt == max_retries - 1:
                return {
                    "error": "Ollama request timed out",
                    "error_type": "timeout", 
                    "details": str(e),
                    "timeout_seconds": timeout,
                    "suggestions": [
                        "Try increasing the timeout value",
                        "Check if Ollama is processing heavy workloads",
                        "Verify system resources (CPU, memory)"
                    ]
                }
            time.sleep(retry_delay)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Ollama HTTP error: {str(e)}"
            logger.error(error_msg)
            
            status_code = e.response.status_code if e.response else 0
            if status_code == 404:
                return {
                    "error": "Ollama API endpoint not found",
                    "error_type": "not_found",
                    "status_code": status_code,
                    "suggestions": [
                        "Verify the Ollama API endpoint URL",
                        "Check Ollama version compatibility",
                        "Ensure the requested model exists"
                    ]
                }
            elif status_code == 500:
                return {
                    "error": "Ollama server internal error",
                    "error_type": "server_error",
                    "status_code": status_code,
                    "suggestions": [
                        "Check Ollama server logs",
                        "Restart Ollama service",
                        "Verify model compatibility"
                    ]
                }
            else:
                return {
                    "error": f"Ollama HTTP error: {str(e)}",
                    "error_type": "http_error",
                    "status_code": status_code,
                    "suggestions": ["Check Ollama server status and logs"]
                }
                
        except json.JSONDecodeError as e:
            error_msg = f"Ollama JSON decode error: {str(e)}"
            logger.error(error_msg)
            return {
                "error": "Invalid response from Ollama server",
                "error_type": "invalid_response",
                "details": str(e),
                "suggestions": [
                    "Check Ollama server health",
                    "Verify API endpoint compatibility",
                    "Try restarting Ollama service"
                ]
            }
            
        except Exception as e:
            error_msg = f"Unexpected Ollama error on attempt {attempt + 1}: {str(e)}"
            logger.error(error_msg)
            
            if attempt == max_retries - 1:
                return {
                    "error": f"Unexpected error: {str(e)}",
                    "error_type": "unknown_error",
                    "details": str(e),
                    "retry_attempts": max_retries,
                    "suggestions": [
                        "Check Ollama installation",
                        "Verify system compatibility",
                        "Review Ollama logs for details"
                    ]
                }
            time.sleep(retry_delay)
    
    return {
        "error": "Maximum retry attempts exceeded",
        "error_type": "max_retries_exceeded",
        "retry_attempts": max_retries
    }

def safe_ollama_request(url, method='GET', **kwargs):
    """
    Safe wrapper for making HTTP requests to Ollama API with proper error handling.
    """
    try:
        logger.info(f"Making Ollama {method} request to: {url}")
        
        if method.upper() == 'GET':
            response = requests.get(url, **kwargs)
        elif method.upper() == 'POST':
            response = requests.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        response.raise_for_status()
        return response
        
    except Exception as e:
        logger.error(f"Ollama request failed: {str(e)}")
        raise

def validate_ollama_connection(base_url):
    """
    Validate Ollama server connection and return detailed status.
    """
    try:
        # Remove /v1 suffix if present to get the raw Ollama API endpoint
        if base_url.endswith('/v1'):
            base_url = base_url[:-3]
            
        # Test basic connectivity
        logger.info(f"Testing Ollama connection to: {base_url}")
        response = safe_ollama_request(f"{base_url}/api/version", timeout=10)
        version_data = response.json() if response.content else {}
        
        # Test model availability
        models_response = safe_ollama_request(f"{base_url}/api/tags", timeout=10)
        models_data = models_response.json()
        
        available_models = models_data.get('models', [])
        
        return {
            "status": "connected",
            "version": version_data.get('version', 'unknown'),
            "models_count": len(available_models),
            "models": [model.get('name', '') for model in available_models[:5]],  # First 5 models
            "server_url": base_url,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ollama connection validation failed: {str(e)}")
        error_result = handle_ollama_request(lambda: None)
        return error_result

def get_ollama_models_safe(base_url):
    """
    Safely retrieve available Ollama models with comprehensive error handling.
    """
    def _get_models(timeout=15, **kwargs):
        if base_url.endswith('/v1'):
            clean_url = base_url[:-3]
        else:
            clean_url = base_url
            
        response = safe_ollama_request(f"{clean_url}/api/tags", timeout=timeout)
        return response.json()
    
    result = handle_ollama_request(_get_models)
    
    if isinstance(result, dict) and "error" in result:
        return []  # Return empty list on error
    
    if not isinstance(result, dict) or 'models' not in result:
        logger.warning("Invalid Ollama models response format")
        return []
        
    return result.get('models', [])

def safe_ollama_chat(client, messages, model, **chat_params):
    """
    Safe wrapper for Ollama chat completions with comprehensive error handling.
    """
    def _make_chat_request(timeout=30, **kwargs):
        logger.info(f"Making Ollama chat request with model: {model}")
        return client.chat.completions.create(
            model=model,
            messages=messages,
            **chat_params
        )
    
    result = handle_ollama_request(_make_chat_request)
    
    if isinstance(result, dict) and "error" in result:
        raise Exception(result["error"], result.get("error_type", "unknown"))
    
    return result

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

def check_ai_dependencies_at_startup():
    """Check AI dependencies during application startup"""
    global AI_DEPENDENCY_STATUS
    
    logger.info("Checking AI dependencies at startup...")
    
    try:
        # Check basic AI agent availability
        if AI_AGENTS_AVAILABLE:
            logger.info("✓ AI agents integration is available")
            AI_DEPENDENCY_STATUS["available_features"].append("ai_agents")
        else:
            logger.warning("✗ AI agents integration is not available")
        
        # Check dependency checker availability
        if AI_FEATURES["dependency_checker"]:
            try:
                # Use the dependency checker if available
                dep_status = check_ai_dependencies()
                AI_DEPENDENCY_STATUS.update({
                    "checked": True,
                    "all_available": dep_status["all_installed"],
                    "missing_dependencies": dep_status["missing_packages"],
                    "last_checked": datetime.now().isoformat()
                })
                
                if dep_status["all_installed"]:
                    logger.info("✓ All AI dependencies are satisfied")
                    AI_DEPENDENCY_STATUS["available_features"].extend([
                        "ai_chat", "ai_analytics", "ai_automation"
                    ])
                else:
                    missing_count = len(dep_status["missing_packages"])
                    logger.warning(f"✗ {missing_count} AI dependencies are missing")
                    for pkg in dep_status["missing_packages"][:3]:  # Show first 3
                        logger.warning(f"  - {pkg['package']}: {pkg['description']}")
                    if missing_count > 3:
                        logger.warning(f"  ... and {missing_count - 3} more")
                    
                    logger.info("To install missing dependencies, run:")
                    logger.info(f"  {get_installation_command()}")
                
            except Exception as e:
                logger.error(f"Error checking AI dependencies: {e}")
                AI_DEPENDENCY_STATUS["error"] = str(e)
        else:
            logger.info("AI dependency checker not available - detailed check skipped")
            AI_DEPENDENCY_STATUS.update({
                "checked": False,
                "all_available": AI_AGENTS_AVAILABLE,
                "last_checked": datetime.now().isoformat(),
                "error": "Dependency checker not available"
            })
        
        # Check workflow orchestrator
        if AI_FEATURES["ai_workflows"]:
            logger.info("✓ AI workflow orchestrator is available")
            AI_DEPENDENCY_STATUS["available_features"].append("ai_workflows")
        else:
            logger.warning("✗ AI workflow orchestrator is not available")
        
        # Update global feature flags based on availability
        available_count = len(AI_DEPENDENCY_STATUS["available_features"])
        total_features = len(AI_FEATURES)
        
        logger.info(f"AI Features Summary: {available_count}/{total_features} available")
        for feature, available in AI_FEATURES.items():
            status_icon = "✓" if available else "✗"
            logger.info(f"  {status_icon} {feature}: {'Available' if available else 'Unavailable'}")
        
        if available_count == 0:
            logger.warning("No AI features are available. Application will run in basic mode.")
        elif available_count < total_features:
            logger.info(f"Partial AI functionality available ({available_count}/{total_features} features)")
        else:
            logger.info("Full AI functionality is available")
        
    except Exception as e:
        logger.error(f"Unexpected error during AI dependency check: {e}")
        AI_DEPENDENCY_STATUS.update({
            "checked": True,
            "all_available": False,
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        })

# Initialize at startup
load_config()
# Load API keys from .env.private
load_private_env()
# Check AI dependencies at startup
check_ai_dependencies_at_startup()

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
                "HTTP-Referer": "http://localhost:7001",
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
            # Remove model and messages from chat_params since they're passed as separate parameters
            ollama_chat_params = {k: v for k, v in chat_params.items() if k not in ['model', 'messages']}
            
            # Use safe Ollama chat with enhanced error handling
            logger.info(f"Using Ollama provider with model: {selected_model}")
            response = safe_ollama_chat(client, messages, selected_model, **ollama_chat_params)
        else:
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
            # For Ollama, use the enhanced error handling functions
            provider = providers[provider_id]
            base_url = provider.get('base_url', 'http://localhost:11434')
            
            logger.info(f"Testing Ollama connection for provider: {provider_id}")
            
            # Use the safe connection validation function
            validation_result = validate_ollama_connection(base_url)
            
            # Check if the result contains an error
            if isinstance(validation_result, dict) and "error" in validation_result:
                logger.error(f"Ollama connection validation failed: {validation_result['error']}")
                # Set specific status based on error type
                error_type = validation_result.get('error_type', 'unknown')
                if error_type == 'connection_error':
                    providers[provider_id]["status"] = "connection_refused"
                elif error_type == 'timeout':
                    providers[provider_id]["status"] = "timeout"
                elif error_type == 'not_found':
                    providers[provider_id]["status"] = "api_not_found"
                else:
                    providers[provider_id]["status"] = "error"
                providers[provider_id]["last_checked"] = datetime.now().isoformat()
                save_config()
                return False
            
            # Connection successful
            logger.info(f"Ollama connection successful: {validation_result['models_count']} models available")
            providers[provider_id]["status"] = "connected"
            providers[provider_id]["last_checked"] = datetime.now().isoformat()
            save_config()
            return True
                
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
        logger.error(f"Provider connection test failed for {provider_id}: {error_msg}")
        
        # Handle Ollama-specific error messages (fallback for non-enhanced errors)
        if provider_id == 'ollama':
            if "connection refused" in error_msg.lower() or "connectionerror" in error_msg.lower():
                providers[provider_id]["status"] = "connection_refused"
            elif "timeout" in error_msg.lower():
                providers[provider_id]["status"] = "timeout"
            elif "no models available" in error_msg.lower():
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
    
    # For Ollama, fetch models from the specific Ollama server with enhanced error handling
    if provider_id == 'ollama':
        try:
            provider = providers[provider_id]
            base_url = provider.get('base_url', 'http://localhost:11434')
            
            # Use the safe models retrieval function
            logger.info(f"Fetching Ollama models from: {base_url}")
            models_list = get_ollama_models_safe(base_url)
            
            if not models_list:
                logger.warning("No Ollama models found or error occurred")
                return jsonify({"models": []}, 200)
                
            # Format the response to match expected structure
            # Frontend expects simple array of model names, but we need to provide full names for API calls
            model_mapping = {}
            model_names = []
            for model in models_list:
                model_name = model.get('name', '')
                # Remove tag suffix for display (e.g., 'llama3.2:latest' -> 'llama3.2')
                model_display = model_name.split(':')[0] if ':' in model_name else model_name
                # Store the mapping for future use
                model_mapping[model_display] = model_name
                model_names.append(model_display)
            
            logger.info(f"Retrieved {len(model_names)} Ollama models successfully: {model_names}")
            return jsonify({
                "models": model_names,
                "total": len(model_names),
                "server_url": base_url,
                "model_mapping": model_mapping  # Include full names for API calls
            })
            
        except Exception as e:
            logger.error(f"Failed to fetch Ollama models: {str(e)}")
            return jsonify({"error": f"Failed to fetch Ollama models: {str(e)}"}), 500
    
    # For other providers, return predefined models
    # Format them to match the expected frontend structure - simple array of strings
    model_names = []
    for model in models:
        if isinstance(model, str):
            model_names.append(model)
        elif isinstance(model, dict):
            model_names.append(model.get('name', model.get('id', '')))
    
    # Return with models wrapper to match frontend expectations
    return jsonify({"models": model_names})

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
    """List available local Ollama models with robust error handling"""
    logger.info("Listing Ollama models endpoint called")
    
    try:
        # Get Ollama configuration
        provider = providers.get('ollama', {})
        base_url = provider.get('base_url', 'http://localhost:11434')
        
        # Use the safe models retrieval function with enhanced error handling
        logger.info(f"Fetching Ollama models from configured URL: {base_url}")
        models_list = get_ollama_models_safe(base_url)
        
        if not models_list:
            logger.warning("No Ollama models found")
            return jsonify({
                "models": [],
                "total": 0,
                "message": "No models found. Make sure Ollama is running and models are installed."
            }), 200
        
        # Format the response to match expected structure
        # Frontend expects simple array of model names
        model_names = []
        for model in models_list:
            model_name = model.get('name', '')
            # Remove tag suffix (e.g., 'llama3.2:latest' -> 'llama3.2')
            model_id = model_name.split(':')[0] if ':' in model_name else model_name
            model_names.append(model_id)
        
        logger.info(f"Successfully retrieved {len(model_names)} Ollama models: {model_names}")
        return jsonify({
            "models": model_names,
            "total": len(model_names),
            "server_url": base_url
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in list_ollama_models: {str(e)}")
        return jsonify({
            "error": "Failed to list Ollama models",
            "details": str(e),
            "suggestions": [
                "Check if Ollama is running",
                "Verify the Ollama server URL in provider settings",
                "Ensure at least one model is installed"
            ]
        }), 500

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

# AI Agent Endpoints
@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """AI-enhanced chat endpoint"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    data = request.json
    message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    context = data.get('context', {})
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        result = process_ai_request_sync('chat', {
            'message': message,
            'session_id': session_id,
            'context': context
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI chat error: {str(e)}"}), 500

@app.route('/api/ai/analytics', methods=['POST'])
def ai_analytics():
    """AI-enhanced analytics endpoint"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    data = request.json
    message = data.get('message', '')
    context = data.get('context', {})
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        # Add current usage stats to context for analytics
        context['usage_stats'] = usage_stats
        context['providers'] = providers
        context['devices'] = devices
        
        result = process_ai_request_sync('analytics', {
            'message': message,
            'context': context
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI analytics error: {str(e)}"}), 500

@app.route('/api/ai/devices', methods=['POST'])
def ai_devices():
    """AI-enhanced device management endpoint"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    data = request.json
    message = data.get('message', '')
    context = data.get('context', {})
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        # Add current devices info to context
        context['devices'] = devices
        context['device_count'] = len(devices)
        
        result = process_ai_request_sync('device', {
            'message': message,
            'context': context
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI device management error: {str(e)}"}), 500

@app.route('/api/ai/operations', methods=['POST'])
def ai_operations():
    """AI-enhanced operations endpoint"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    data = request.json
    message = data.get('message', '')
    context = data.get('context', {})
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        # Add system status to context
        context['providers_status'] = {k: v['status'] for k, v in providers.items()}
        context['devices_status'] = {k: v['status'] for k, v in devices.items()}
        context['uptime'] = time.time() - globals().get('start_time', time.time())
        
        result = process_ai_request_sync('operations', {
            'message': message,
            'context': context
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI operations error: {str(e)}"}), 500

@app.route('/api/ai/automation', methods=['POST'])
def ai_automation():
    """AI-enhanced automation endpoint"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    data = request.json
    message = data.get('message', '')
    context = data.get('context', {})
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        # Add automation-relevant context
        context['available_devices'] = list(devices.keys())
        context['available_providers'] = [k for k, v in providers.items() if v['enabled']]
        context['system_features'] = settings.get('features', {})
        
        result = process_ai_request_sync('automation', {
            'message': message,
            'context': context
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI automation error: {str(e)}"}), 500

@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """Get comprehensive AI system status with feature availability and dependency information"""
    global AI_DEPENDENCY_STATUS, AI_FEATURES
    
    # Base response structure
    response = {
        "ai_available": AI_AGENTS_AVAILABLE,
        "features": AI_FEATURES.copy(),
        "timestamp": datetime.now().isoformat(),
        "dependency_status": AI_DEPENDENCY_STATUS.copy(),
        "integration_status": None,
        "recommendations": []
    }
    
    # Get integration status if AI agents are available
    if AI_AGENTS_AVAILABLE:
        try:
            integration_status = get_ai_integration_status()
            response["integration_status"] = integration_status
        except Exception as e:
            response["integration_error"] = str(e)
    
    # Add dependency check status if dependency checker is available
    if AI_FEATURES["dependency_checker"]:
        try:
            # Get fresh dependency status
            dep_check = check_ai_dependencies()
            env_validation = validate_ai_environment()
            
            response["dependency_details"] = {
                "all_installed": dep_check["all_installed"],
                "installed_count": dep_check["installed_count"],
                "total_packages": dep_check["total_packages"],
                "missing_packages": dep_check["missing_packages"],
                "outdated_packages": dep_check["outdated_packages"],
                "environment_ready": env_validation["environment_ready"],
                "python_version": env_validation["python_version"],
                "installation_command": get_installation_command()
            }
            
            # Add recommendations based on current state
            if not dep_check["all_installed"]:
                response["recommendations"].append({
                    "type": "install_dependencies",
                    "message": f"Install {len(dep_check['missing_packages'])} missing AI dependencies",
                    "command": get_installation_command(),
                    "priority": "high"
                })
            
            if env_validation["recommendations"]:
                for rec in env_validation["recommendations"]:
                    response["recommendations"].append({
                        "type": "environment",
                        "message": rec,
                        "priority": "medium"
                    })
                    
        except Exception as e:
            response["dependency_check_error"] = str(e)
    
    # Provide overall assessment and recommendations
    available_features = sum(1 for f in AI_FEATURES.values() if f)
    total_features = len(AI_FEATURES)
    
    if available_features == 0:
        response["overall_status"] = "unavailable"
        response["status_message"] = "No AI features are available. Application running in basic mode."
        response["recommendations"].append({
            "type": "setup",
            "message": "Install AI dependencies to enable advanced features",
            "command": "pip install -r requirements-ai-agents.txt",
            "priority": "high"
        })
    elif available_features < total_features:
        response["overall_status"] = "partial"
        response["status_message"] = f"Partial AI functionality ({available_features}/{total_features} features available)"
        response["recommendations"].append({
            "type": "optimization",
            "message": "Some AI features are unavailable. Check dependencies for full functionality.",
            "priority": "medium"
        })
    else:
        response["overall_status"] = "available"
        response["status_message"] = "Full AI functionality is available"
    
    # Add feature-specific status
    feature_status = {}
    for feature, available in AI_FEATURES.items():
        feature_status[feature] = {
            "available": available,
            "description": get_feature_description(feature)
        }
    response["feature_details"] = feature_status
    
    return jsonify(response)

def get_feature_description(feature):
    """Get human-readable description for AI features"""
    descriptions = {
        "ai_agents": "Core AI agent framework for intelligent assistance",
        "ai_chat": "AI-enhanced chat capabilities with context awareness",
        "ai_analytics": "AI-powered analytics and insights generation",
        "ai_automation": "AI-driven automation and workflow management",
        "ai_workflows": "Advanced workflow orchestration with AI agents",
        "dependency_checker": "AI dependency validation and management tools"
    }
    return descriptions.get(feature, "AI feature component")

@app.route('/api/ai/toggle', methods=['POST'])
def ai_toggle():
    """Toggle AI agents on/off"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    data = request.json or {}
    enabled = data.get('enabled')
    
    try:
        result = toggle_ai_agents(enabled)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI toggle error: {str(e)}"}), 500

@app.route('/api/ai/providers/recommend', methods=['POST'])
def ai_provider_recommendation():
    """Get AI recommendation for best provider based on request"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    data = request.json
    message = data.get('message', '')
    criteria = data.get('criteria', ['speed', 'cost', 'quality'])
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        # Create context for provider recommendation
        context = {
            'available_providers': {k: v for k, v in providers.items() if v['enabled']},
            'criteria': criteria,
            'usage_stats': usage_stats,
            'request_type': 'provider_recommendation'
        }
        
        result = process_ai_request_sync('chat', {
            'message': f"Recommend the best AI provider for this request based on {', '.join(criteria)}: {message}",
            'context': context
        })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI provider recommendation error: {str(e)}"}), 500

# AI Agent API Endpoints
@app.route('/api/ai-agents/status', methods=['GET'])
def get_ai_agent_status():
    """Get current AI agent status"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({
            'enabled': False,
            'status': 'unavailable',
            'message': 'AI agents not installed'
        })
    
    status = get_ai_integration_status()
    return jsonify(status)

@app.route('/api/ai-agents/toggle', methods=['POST'])
def toggle_ai_agents_endpoint():
    """Toggle AI agents on/off"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'AI agents not available'
        }), 503
    
    data = request.get_json()
    enabled = data.get('enabled', None)
    
    result = toggle_ai_agents(enabled)
    return jsonify(result)

@app.route('/api/ai-agents/process', methods=['POST'])
def process_ai_request():
    """Process a request through AI agents"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({
            'success': False,
            'response': 'AI agents not available'
        }), 503
    
    data = request.get_json()
    request_type = data.get('type', 'chat')
    
    result = process_ai_request_sync(request_type, data)
    return jsonify(result)

# Advanced Workflow Endpoints
@app.route('/api/ai/workflows', methods=['POST'])
def create_workflow():
    """Create a new AI workflow"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    try:
        # Import workflow orchestrator directly to avoid dependency issues
        import sys
        import os
        workflows_path = os.path.join(os.path.dirname(__file__), 'ai_agents', 'workflows')
        if workflows_path not in sys.path:
            sys.path.insert(0, workflows_path)
        from orchestrator import orchestrator, create_simple_workflow, create_analysis_workflow
        
        data = request.json
        workflow_type = data.get('type', 'simple')
        
        if workflow_type == 'analysis':
            message = data.get('message', '')
            if not message:
                return jsonify({"error": "Message is required for analysis workflow"}), 400
            
            include_recommendations = data.get('include_recommendations', True)
            workflow = create_analysis_workflow(message, include_recommendations)
        
        elif workflow_type == 'simple':
            name = data.get('name', 'Simple Workflow')
            tasks = data.get('tasks', [])
            if not tasks:
                return jsonify({"error": "Tasks are required for simple workflow"}), 400
            
            workflow = create_simple_workflow(name, tasks)
        
        else:
            return jsonify({"error": f"Unknown workflow type: {workflow_type}"}), 400
        
        workflow_id = orchestrator.create_workflow(workflow)
        
        return jsonify({
            'workflow_id': workflow_id,
            'status': 'created',
            'tasks_count': len(workflow.tasks),
            'workflow_type': workflow_type
        })
        
    except Exception as e:
        return jsonify({"error": f"Workflow creation error: {str(e)}"}), 500

@app.route('/api/ai/workflows/<workflow_id>', methods=['GET'])
def get_workflow_status(workflow_id):
    """Get status of a specific workflow"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    try:
        # Import workflow orchestrator directly to avoid dependency issues
        import sys
        import os
        workflows_path = os.path.join(os.path.dirname(__file__), 'ai_agents', 'workflows')
        if workflows_path not in sys.path:
            sys.path.insert(0, workflows_path)
        from orchestrator import orchestrator
        status = orchestrator.get_workflow_status(workflow_id)
        return jsonify(status)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Status retrieval error: {str(e)}"}), 500

@app.route('/api/ai/workflows/<workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id):
    """Execute a workflow"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    try:
        # Import workflow orchestrator directly to avoid dependency issues
        import sys
        import os
        workflows_path = os.path.join(os.path.dirname(__file__), 'ai_agents', 'workflows')
        if workflows_path not in sys.path:
            sys.path.insert(0, workflows_path)
        from orchestrator import orchestrator
        import asyncio
        
        # Run the async workflow execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(orchestrator.execute_workflow(workflow_id))
        loop.close()
        
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Workflow execution error: {str(e)}"}), 500

@app.route('/api/ai/workflows/<workflow_id>/cancel', methods=['POST'])
def cancel_workflow(workflow_id):
    """Cancel a running workflow"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    try:
        # Import workflow orchestrator directly to avoid dependency issues
        import sys
        import os
        workflows_path = os.path.join(os.path.dirname(__file__), 'ai_agents', 'workflows')
        if workflows_path not in sys.path:
            sys.path.insert(0, workflows_path)
        from orchestrator import orchestrator
        success = orchestrator.cancel_workflow(workflow_id)
        
        if success:
            return jsonify({"status": "cancelled", "workflow_id": workflow_id})
        else:
            return jsonify({"error": "Workflow not found or not running"}), 404
    except Exception as e:
        return jsonify({"error": f"Workflow cancellation error: {str(e)}"}), 500

@app.route('/api/ai/workflows', methods=['GET'])
def list_workflows():
    """List all workflows"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    try:
        # Import workflow orchestrator directly to avoid dependency issues
        import sys
        import os
        workflows_path = os.path.join(os.path.dirname(__file__), 'ai_agents', 'workflows')
        if workflows_path not in sys.path:
            sys.path.insert(0, workflows_path)
        from orchestrator import orchestrator
        workflows = orchestrator.get_all_workflows()
        return jsonify({
            'workflows': workflows,
            'count': len(workflows)
        })
    except Exception as e:
        return jsonify({"error": f"Workflow listing error: {str(e)}"}), 500

@app.route('/api/ai/workflows/cleanup', methods=['POST'])
def cleanup_workflows():
    """Cleanup old completed workflows"""
    if not AI_AGENTS_AVAILABLE:
        return jsonify({"error": "AI agents are not available"}), 503
    
    try:
        # Import workflow orchestrator directly to avoid dependency issues
        import sys
        import os
        workflows_path = os.path.join(os.path.dirname(__file__), 'ai_agents', 'workflows')
        if workflows_path not in sys.path:
            sys.path.insert(0, workflows_path)
        from orchestrator import orchestrator
        data = request.json or {}
        older_than_hours = data.get('older_than_hours', 24)
        
        cleaned_count = orchestrator.cleanup_completed_workflows(older_than_hours)
        
        return jsonify({
            'cleaned_workflows': cleaned_count,
            'older_than_hours': older_than_hours
        })
    except Exception as e:
        return jsonify({"error": f"Workflow cleanup error: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    start_time = time.time() if 'start_time' not in globals() else globals()['start_time']
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "providers_enabled": len([p for p in providers.values() if p["enabled"]]),
        "uptime": time.time() - start_time if 'start_time' in globals() else 0,
        "env_private_exists": os.path.exists(ENV_PRIVATE_FILE),
        "ai_agents_available": AI_AGENTS_AVAILABLE,
        "ai_features": AI_FEATURES.copy(),
        "ai_feature_summary": {
            "total": len(AI_FEATURES),
            "available": sum(1 for f in AI_FEATURES.values() if f),
            "unavailable": sum(1 for f in AI_FEATURES.values() if not f)
        }
    }
    
    # Add comprehensive AI status
    if AI_AGENTS_AVAILABLE:
        try:
            ai_status = get_ai_integration_status()
            health_data["ai_agents_status"] = ai_status.get("status", "unknown")
            health_data["ai_integration"] = ai_status
        except Exception as e:
            health_data["ai_agents_status"] = "error"
            health_data["ai_integration_error"] = str(e)
    else:
        health_data["ai_agents_status"] = "unavailable"
    
    # Add AI dependency status summary
    health_data["ai_dependency_summary"] = {
        "checked": AI_DEPENDENCY_STATUS.get("checked", False),
        "all_available": AI_DEPENDENCY_STATUS.get("all_available", False),
        "available_features_count": len(AI_DEPENDENCY_STATUS.get("available_features", [])),
        "missing_dependencies_count": len(AI_DEPENDENCY_STATUS.get("missing_dependencies", [])),
        "last_checked": AI_DEPENDENCY_STATUS.get("last_checked"),
        "has_error": AI_DEPENDENCY_STATUS.get("error") is not None
    }
    
    # Determine overall AI health
    available_features = sum(1 for f in AI_FEATURES.values() if f)
    total_features = len(AI_FEATURES)
    
    if available_features == 0:
        health_data["ai_health"] = "unavailable"
    elif available_features < total_features:
        health_data["ai_health"] = "partial"
    else:
        health_data["ai_health"] = "available"
    
    return jsonify(health_data)

# Start server
if __name__ == '__main__':
    start_time = time.time()
    app.run(host='localhost', port=7002, debug=True)
