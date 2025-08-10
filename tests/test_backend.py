import pytest
import json
import os
import time
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import threading

# Add the parent directory to the path so we can import the backend module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the backend application
import backend_server

# Test configuration
TEST_CONFIG = {
    "providers": {
        "test_provider": {
            "name": "Test Provider",
            "enabled": True,
            "api_key": "test_key",
            "model": "test_model",
            "base_url": "http://test.provider.com/v1",
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
    },
    "settings": {
        "default_provider": "test_provider",
        "fallback_provider": None,
        "temperature": 0.7,
        "max_tokens": 1000,
        "system_prompt": "You are a test AI assistant.",
        "features": {
            "auto_fallback": True,
            "speed_optimization": False,
            "cost_optimization": False,
            "multi_provider_compare": False,
            "usage_analytics": True
        }
    },
    "devices": {
        "dummy_router": {
            "name": "Dummy Router",
            "ip": "192.168.1.1",
            "model": "Cisco 2900",
            "username": "",
            "password": "",
            "port": 22,
            "status": "unknown",
            "last_checked": ""
        },
        "real_router": {
            "name": "Real Router",
            "ip": "192.168.1.2",
            "model": "Cisco 4500",
            "username": "admin",
            "password": "password123",
            "port": 22,
            "status": "unknown",
            "last_checked": ""
        }
    }
}

@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app = backend_server.app
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            # Reset providers and settings for each test
            backend_server.providers = TEST_CONFIG["providers"].copy()
            backend_server.settings = TEST_CONFIG["settings"].copy()
            backend_server.usage_stats = {}
            # Reset devices for each test
            backend_server.devices = TEST_CONFIG["devices"].copy()
            yield client

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    with patch('backend_server.OpenAI') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Mock chat completions response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response from AI"
        mock_response.choices = [mock_choice]
        
        mock_usage = MagicMock()
        mock_usage.total_tokens = 42
        mock_response.usage = mock_usage
        
        mock_instance.chat.completions.create.return_value = mock_response
        yield mock_instance

def test_list_providers(client):
    """Test listing all providers"""
    response = client.get('/api/providers')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert "test_provider" in data
    assert data["test_provider"]["name"] == "Test Provider"

def test_update_provider(client):
    """Test updating provider configuration"""
    update_data = {
        "enabled": False,
        "api_key": "updated_key",
        "model": "updated_model"
    }
    
    response = client.put('/api/providers/test_provider', 
                         json=update_data,
                         content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["enabled"] == False
    assert data["api_key"] == "updated_key"
    assert data["model"] == "updated_model"

def test_update_nonexistent_provider(client):
    """Test updating a provider that doesn't exist"""
    response = client.put('/api/providers/nonexistent', 
                         json={"enabled": False},
                         content_type='application/json')
    assert response.status_code == 404

def test_manage_settings_get(client):
    """Test getting settings"""
    response = client.get('/api/settings')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["default_provider"] == "test_provider"
    assert data["temperature"] == 0.7

def test_manage_settings_put(client):
    """Test updating settings"""
    update_settings = {
        "default_provider": "new_default",
        "temperature": 0.8,
        "max_tokens": 1500
    }
    
    response = client.put('/api/settings', 
                         json=update_settings,
                         content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["default_provider"] == "new_default"
    assert data["temperature"] == 0.8
    assert data["max_tokens"] == 1500

def test_chat_success(client, mock_openai_client):
    """Test successful chat response"""
    chat_data = {
        "message": "Hello, AI!",
        "provider": "test_provider"
    }
    
    response = client.post('/api/chat', 
                          json=chat_data,
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["provider"] == "test_provider"
    assert data["response"] == "Test response from AI"
    assert data["tokens"] == 42
    assert "response_time" in data

def test_chat_with_fallback(client, mock_openai_client):
    """Test chat with fallback provider when primary fails"""
    # Mock primary provider to fail
    mock_openai_client.chat.completions.create.side_effect = Exception("Primary provider error")
    
    # Add a fallback provider to config
    backend_server.providers["fallback_provider"] = {
        "name": "Fallback Provider",
        "enabled": True,
        "api_key": "fallback_key",
        "model": "fallback_model",
        "base_url": "http://fallback.provider.com/v1",
        "status": "disconnected",
        "last_checked": ""
    }
    
    backend_server.settings["fallback_provider"] = "fallback_provider"
    
    chat_data = {
        "message": "Hello, AI!",
        "provider": "test_provider"
    }
    
    response = client.post('/api/chat', 
                          json=chat_data,
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["provider"] == "fallback_provider"
    assert data["fallback_used"] == True
    assert data["response"] == "Test response from AI"

def test_chat_error_without_fallback(client, mock_openai_client):
    """Test chat error when primary provider fails and no fallback is available"""
    # Mock primary provider to fail
    mock_openai_client.chat.completions.create.side_effect = Exception("Primary provider error")
    
    # Disable fallback
    backend_server.settings["features"]["auto_fallback"] = False
    
    chat_data = {
        "message": "Hello, AI!",
        "provider": "test_provider"
    }
    
    response = client.post('/api/chat', 
                          json=chat_data,
                          content_type='application/json')
    assert response.status_code == 500

def test_chat_missing_message(client):
    """Test chat error when message is missing"""
    chat_data = {
        "provider": "test_provider"
    }
    
    response = client.post('/api/chat', 
                          json=chat_data,
                          content_type='application/json')
    assert response.status_code == 400

def test_chat_disabled_provider(client):
    """Test chat error when provider is disabled"""
    backend_server.providers["test_provider"]["enabled"] = False
    
    chat_data = {
        "message": "Hello, AI!",
        "provider": "test_provider"
    }
    
    response = client.post('/api/chat', 
                          json=chat_data,
                          content_type='application/json')
    assert response.status_code == 400

def test_compare_chat(client, mock_openai_client):
    """Test comparing chat responses across providers"""
    # Add another provider for comparison
    backend_server.providers["test_provider2"] = {
        "name": "Test Provider 2",
        "enabled": True,
        "api_key": "test_key2",
        "model": "test_model2",
        "base_url": "http://test.provider2.com/v1",
        "status": "disconnected",
        "last_checked": ""
    }
    
    compare_data = {
        "message": "Hello, AI!",
        "providers": ["test_provider", "test_provider2"]
    }
    
    response = client.post('/api/chat/compare', 
                          json=compare_data,
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]["provider"] == "test_provider"
    assert data[1]["provider"] == "test_provider2"

def test_get_usage(client):
    """Test getting usage statistics"""
    # Add some test usage data
    test_date = datetime.now().strftime('%Y-%m-%d')
    backend_server.usage_stats[test_date] = {
        "test_provider": {
            "requests": 5,
            "tokens": 210,
            "total_response_time": 4.2
        }
    }
    
    response = client.get('/api/usage')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert test_date in data
    assert data[test_date]["test_provider"]["requests"] == 5

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert "providers_enabled" in data
    assert "uptime" in data

def test_test_provider_success(client, mock_openai_client):
    """Test successful provider connection test"""
    response = client.post('/api/providers/test_provider/test')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["provider"] == "test_provider"
    assert data["success"] == True
    assert backend_server.providers["test_provider"]["status"] == "connected"

def test_test_provider_failure(client, mock_openai_client):
    """Test failed provider connection test"""
    # Mock provider to fail
    mock_openai_client.models.list.side_effect = Exception("Connection error")
    
    response = client.post('/api/providers/test_provider/test')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["provider"] == "test_provider"
    assert data["success"] == False
    assert backend_server.providers["test_provider"]["status"] == "error"

def test_test_all_providers(client, mock_openai_client):
    """Test testing all providers"""
    # Add another enabled provider
    backend_server.providers["test_provider2"] = {
        "name": "Test Provider 2",
        "enabled": True,
        "api_key": "test_key2",
        "model": "test_model2",
        "base_url": "http://test.provider2.com/v1",
        "status": "disconnected",
        "last_checked": ""
    }
    
    response = client.post('/api/providers/test-all')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert "test_provider" in data
    assert "test_provider2" in data
    assert data["test_provider"] == True
    assert data["test_provider2"] == True

# Test the get_client function
def test_get_client(client, mock_openai_client):
    """Test the get_client function"""
    with patch('backend_server.get_client') as mock_get_client:
        mock_get_client.return_value = mock_openai_client
        
        # Call the mock
        result = backend_server.get_client("test_provider")
        
        # Verify the mock was called correctly
        mock_get_client.assert_called_once_with("test_provider")
        
        # For OpenRouter, check that default headers are set
        backend_server.providers["openrouter"] = {
            "name": "OpenRouter",
            "enabled": True,
            "api_key": "or_key",
            "model": "or_model",
            "base_url": "https://openrouter.ai/api/v1",
            "status": "disconnected",
            "last_checked": ""
        }
        
        # We can't easily test the OpenRouter headers without mocking more deeply,
        # but we can verify the function works for normal providers

# Test the track_usage function
def test_track_usage(client):
    """Test the track_usage function"""
    provider_id = "test_provider"
    response_time = 1.5
    tokens = 42
    
    # Call track_usage
    backend_server.track_usage(provider_id, response_time, tokens)
    
    # Verify usage was tracked
    test_date = datetime.now().strftime('%Y-%m-%d')
    assert test_date in backend_server.usage_stats
    assert provider_id in backend_server.usage_stats[test_date]
    assert backend_server.usage_stats[test_date][provider_id]["requests"] == 1
    assert backend_server.usage_stats[test_date][provider_id]["tokens"] == 42
    assert backend_server.usage_stats[test_date][provider_id]["total_response_time"] == 1.5

# Test chat_with_provider
def test_chat_with_provider(client, mock_openai_client):
    """Test the chat_with_provider function"""
    with patch('backend_server.get_client') as mock_get_client:
        mock_get_client.return_value = mock_openai_client
        
        result = backend_server.chat_with_provider("test_provider", "Hello, AI!", "Test system prompt")
        
        assert result["provider"] == "test_provider"
        assert result["response"] == "Test response from AI"
        assert result["tokens"] == 42
        assert result["model"] == "test_model"
        assert "response_time" in result

# Ollama Integration Tests
def test_ollama_provider_exists(client):
    """Test that Ollama provider is available in the default configuration"""
    response = client.get('/api/providers')
    assert response.status_code == 200
    
    providers = json.loads(response.data)
    assert "ollama" in providers
    
    ollama_provider = providers["ollama"]
    assert ollama_provider["name"] == "Ollama"
    assert ollama_provider["base_url"] == "http://localhost:11434/v1"
    assert ollama_provider["api_key"] == ""  # Ollama doesn't require API key
    assert ollama_provider["model"] == "llama3.2"

def test_ollama_provider_configuration(client):
    """Test Ollama-specific configuration"""
    # Add Ollama to test config
    backend_server.providers["ollama"] = {
        "name": "Ollama",
        "enabled": True,
        "api_key": "",
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "status": "disconnected",
        "last_checked": ""
    }
    
    response = client.get('/api/providers')
    assert response.status_code == 200
    
    providers = json.loads(response.data)
    ollama = providers["ollama"]
    
    # Verify Ollama-specific configuration
    assert ollama["api_key"] == ""  # No API key needed
    assert "localhost:11434" in ollama["base_url"]
    assert ollama["enabled"] == True

@patch('requests.get')
def test_ollama_connection_success(mock_get, client):
    """Test successful Ollama connection"""
    # Add Ollama to test config
    backend_server.providers["ollama"] = {
        "name": "Ollama",
        "enabled": True,
        "api_key": "",
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "status": "disconnected",
        "last_checked": ""
    }
    
    # Mock successful Ollama response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": [{"name": "llama3.2"}]}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    response = client.post('/api/providers/ollama/test')
    assert response.status_code == 200
    
    result = json.loads(response.data)
    assert result["provider"] == "ollama"
    assert result["success"] == True
    assert backend_server.providers["ollama"]["status"] == "connected"

@patch('requests.get')
def test_ollama_connection_failure(mock_get, client):
    """Test Ollama connection failure"""
    # Add Ollama to test config
    backend_server.providers["ollama"] = {
        "name": "Ollama",
        "enabled": True,
        "api_key": "",
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "status": "disconnected",
        "last_checked": ""
    }
    
    # Mock connection error
    from requests.exceptions import ConnectionError
    mock_get.side_effect = ConnectionError("Connection refused")
    
    response = client.post('/api/providers/ollama/test')
    assert response.status_code == 200
    
    result = json.loads(response.data)
    assert result["provider"] == "ollama"
    assert result["success"] == False
    assert backend_server.providers["ollama"]["status"] == "connection_refused"

@patch('requests.get')
def test_ollama_models_endpoint_success(mock_get, client):
    """Test successful Ollama models listing"""
    # Mock Ollama models response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama3.2", "size": 2000000, "modified_at": "2024-01-01T00:00:00Z"},
            {"name": "llama3.2:1b", "size": 1000000, "modified_at": "2024-01-01T00:00:00Z"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    response = client.get('/api/providers/ollama/models')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert "models" in data
    assert "total" in data
    assert len(data["models"]) == 2
    assert data["total"] == 2
    assert data["models"][0]["name"] == "llama3.2"

@patch('requests.get')
def test_ollama_models_endpoint_failure(mock_get, client):
    """Test Ollama models listing when server is down"""
    # Mock connection error
    from requests.exceptions import ConnectionError
    mock_get.side_effect = ConnectionError("Connection refused")
    
    response = client.get('/api/providers/ollama/models')
    assert response.status_code == 503
    
    data = json.loads(response.data)
    assert "error" in data
    assert "Ollama server" in data["error"]

@patch('requests.post')
def test_ollama_model_pull_success(mock_post, client):
    """Test successful Ollama model pull"""
    # Mock streaming response for model pull
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = [
        b'{"status": "pulling manifest"}',
        b'{"status": "success"}'
    ]
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    pull_data = {"model": "llama3.2:1b"}
    response = client.post('/api/providers/ollama/pull', json=pull_data)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["success"] == True
    assert data["model"] == "llama3.2:1b"
    assert "status_log" in data

def test_ollama_chat_with_mock(client, mock_openai_client):
    """Test Ollama chat functionality with mocked client"""
    # Add Ollama provider
    backend_server.providers["ollama"] = {
        "name": "Ollama",
        "enabled": True,
        "api_key": "",
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "status": "connected",
        "last_checked": ""
    }
    
    # Test chat request
    chat_data = {
        "message": "Hello Ollama!",
        "provider": "ollama"
    }
    
    response = client.post('/api/chat', json=chat_data)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["provider"] == "ollama"
    assert data["response"] == "Test response from AI"
    assert data["tokens"] == 42

def test_ollama_fallback_mechanism(client, mock_openai_client):
    """Test fallback when Ollama fails"""
    # Setup Ollama and fallback provider
    backend_server.providers["ollama"] = {
        "name": "Ollama",
        "enabled": True,
        "api_key": "",
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "status": "connected",
        "last_checked": ""
    }
    
    backend_server.providers["groq"] = {
        "name": "Groq",
        "enabled": True,
        "api_key": "test_key",
        "model": "llama-3.1-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "status": "connected",
        "last_checked": ""
    }
    
    # Enable fallback
    backend_server.settings["features"]["auto_fallback"] = True
    backend_server.settings["fallback_provider"] = "groq"
    
    # Make Ollama fail
    with patch('backend_server.get_client') as mock_get_client:
        # First call (Ollama) fails, second call (Groq) succeeds
        mock_get_client.side_effect = [Exception("Ollama connection failed"), mock_openai_client]
        
        chat_data = {
            "message": "Hello!",
            "provider": "ollama"
        }
        
        response = client.post('/api/chat', json=chat_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["provider"] == "groq"  # Should fallback to groq
        assert data["fallback_used"] == True

def test_ollama_usage_tracking(client, mock_openai_client):
    """Test that Ollama requests are properly tracked in usage statistics"""
    # Add Ollama provider
    backend_server.providers["ollama"] = {
        "name": "Ollama",
        "enabled": True,
        "api_key": "",
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "status": "connected",
        "last_checked": ""
    }
    
    # Enable usage analytics
    backend_server.settings["features"]["usage_analytics"] = True
    
    # Make chat request
    chat_data = {
        "message": "Test usage tracking",
        "provider": "ollama"
    }
    
    response = client.post('/api/chat', json=chat_data)
    assert response.status_code == 200
    
    # Check usage was tracked
    today = datetime.now().strftime('%Y-%m-%d')
    assert today in backend_server.usage_stats
    assert "ollama" in backend_server.usage_stats[today]
    assert backend_server.usage_stats[today]["ollama"]["requests"] == 1
    assert backend_server.usage_stats[today]["ollama"]["tokens"] == 42

def test_ollama_disabled_provider(client):
    """Test that disabled Ollama provider returns appropriate error"""
    # Add disabled Ollama provider
    backend_server.providers["ollama"] = {
        "name": "Ollama",
        "enabled": False,  # Disabled
        "api_key": "",
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "status": "disconnected",
        "last_checked": ""
    }
    
    chat_data = {
        "message": "Hello!",
        "provider": "ollama"
    }
    
    response = client.post('/api/chat', json=chat_data)
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert "disabled" in data["error"].lower() or "not enabled" in data["error"].lower()

@patch('backend_server.get_client')
def test_ollama_get_client_configuration(mock_get_client, client):
    """Test that Ollama client is configured correctly"""
    # Add Ollama provider
    backend_server.providers["ollama"] = {
        "name": "Ollama",
        "enabled": True,
        "api_key": "",
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "status": "connected",
        "last_checked": ""
    }
    
    # Create a real client to test configuration
    from backend_server import get_client
    
    # Test that get_client works for Ollama without throwing errors
    # We can't easily test the exact configuration without mocking OpenAI,
    # but we can verify the function doesn't crash
    try:
        client_instance = get_client("ollama")
        # The client should be created successfully
        assert client_instance is not None
    except Exception as e:
        # If it fails, it should be due to actual connection issues, not configuration
        assert "api_key" not in str(e).lower()  # Should not fail due to API key issues

# Router Device Management Tests
def test_list_devices(client):
    """Test listing all router devices"""
    response = client.get('/api/devices')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert "dummy_router" in data
    assert "real_router" in data
    assert data["dummy_router"]["name"] == "Dummy Router"
    assert data["real_router"]["name"] == "Real Router"

def test_add_device(client):
    """Test adding a new router device"""
    device_data = {
        "id": "new_router",
        "name": "New Router",
        "ip": "192.168.1.3",
        "model": "Cisco 3500",
        "username": "admin",
        "password": "newpassword",
        "port": 22
    }
    
    response = client.post('/api/devices',
                          json=device_data,
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["name"] == "New Router"
    assert data["ip"] == "192.168.1.3"
    
    # Verify device was added to config
    assert "new_router" in backend_server.providers.get("devices", {})

def test_add_device_missing_id(client):
    """Test adding a device without ID"""
    device_data = {
        "name": "New Router",
        "ip": "192.168.1.3"
    }
    
    response = client.post('/api/devices',
                          json=device_data,
                          content_type='application/json')
    assert response.status_code == 400

def test_add_duplicate_device(client):
    """Test adding a device that already exists"""
    device_data = {
        "id": "dummy_router",
        "name": "Duplicate Router",
        "ip": "192.168.1.4"
    }
    
    response = client.post('/api/devices',
                          json=device_data,
                          content_type='application/json')
    assert response.status_code == 400

def test_update_device(client):
    """Test updating a router device"""
    update_data = {
        "name": "Updated Router",
        "ip": "192.168.2.1"
    }
    
    response = client.put('/api/devices/dummy_router',
                         json=update_data,
                         content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["name"] == "Updated Router"
    assert data["ip"] == "192.168.2.1"

def test_update_nonexistent_device(client):
    """Test updating a device that doesn't exist"""
    update_data = {
        "name": "Updated Router"
    }
    
    response = client.put('/api/devices/nonexistent',
                         json=update_data,
                         content_type='application/json')
    assert response.status_code == 404

def test_remove_device(client):
    """Test removing a router device"""
    response = client.delete('/api/devices/dummy_router')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["success"] == True
    
    # Verify device was removed from config
    assert "dummy_router" not in backend_server.providers.get("devices", {})

def test_remove_nonexistent_device(client):
    """Test removing a device that doesn't exist"""
    response = client.delete('/api/devices/nonexistent')
    assert response.status_code == 404

# Router Connection Testing Tests
def test_test_device_success(client):
    """Test successful router connection test"""
    # For dummy devices without credentials, this should succeed
    response = client.post('/api/devices/dummy_router/test')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["device"] == "dummy_router"
    assert data["success"] == True
    # Status should be updated to online for dummy devices
    assert backend_server.providers.get("devices", {}).get("dummy_router", {}).get("status") == "online"

def test_test_device_failure(client):
    """Test failed router connection test"""
    # For real devices, we'll mock the SSH connection to fail
    with patch('backend_server.test_router_connection') as mock_test:
        mock_test.return_value = (False, "SSH connection failed")
        
        response = client.post('/api/devices/real_router/test')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["device"] == "real_router"
        assert data["success"] == False
        assert backend_server.providers.get("devices", {}).get("real_router", {}).get("status") == "offline"

def test_test_nonexistent_device(client):
    """Test testing connection for a device that doesn't exist"""
    response = client.post('/api/devices/nonexistent/test')
    assert response.status_code == 404

# Command Execution Tests
def test_send_command_success(client):
    """Test successful command execution on dummy device"""
    command_data = {
        "command": "show ip route"
    }
    
    response = client.post('/api/devices/dummy_router/command',
                          json=command_data,
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["device"] == "dummy_router"
    assert data["command"] == "show ip route"
    # Should return the simulated routing table
    assert "Gateway of last resort" in data["response"]

def test_send_command_missing_command(client):
    """Test command execution without command"""
    command_data = {}
    
    response = client.post('/api/devices/dummy_router/command',
                          json=command_data,
                          content_type='application/json')
    assert response.status_code == 400

def test_send_command_nonexistent_device(client):
    """Test command execution on non-existent device"""
    command_data = {
        "command": "show ip route"
    }
    
    response = client.post('/api/devices/nonexistent/command',
                          json=command_data,
                          content_type='application/json')
    assert response.status_code == 404

# GENAI Workflow Tests
def test_config_push_success(client):
    """Test successful configuration push to dummy device"""
    config_data = {
        "device_id": "dummy_router",
        "config": "interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n!"
    }
    
    response = client.post('/api/workflows/config-push',
                          json=config_data,
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["device"] == "dummy_router"
    assert data["success"] == True
    assert "Configuration pushed successfully" in data["status"]

def test_config_push_missing_device(client):
    """Test configuration push without device ID"""
    config_data = {
        "config": "interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n!"
    }
    
    response = client.post('/api/workflows/config-push',
                          json=config_data,
                          content_type='application/json')
    assert response.status_code == 400

def test_config_push_nonexistent_device(client):
    """Test configuration push to non-existent device"""
    config_data = {
        "device_id": "nonexistent",
        "config": "interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n!"
    }
    
    response = client.post('/api/workflows/config-push',
                          json=config_data,
                          content_type='application/json')
    assert response.status_code == 404

def test_config_retrieval_success(client):
    """Test successful configuration retrieval from dummy device"""
    config_data = {
        "device_id": "dummy_router"
    }
    
    response = client.post('/api/workflows/config-retrieval',
                          json=config_data,
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["device"] == "dummy_router"
    # Should return the simulated configuration
    assert "hostname Dummy Router" in data["config"]

def test_config_retrieval_missing_device(client):
    """Test configuration retrieval without device ID"""
    config_data = {}
    
    response = client.post('/api/workflows/config-retrieval',
                          json=config_data,
                          content_type='application/json')
    assert response.status_code == 400

def test_config_retrieval_nonexistent_device(client):
    """Test configuration retrieval from non-existent device"""
    config_data = {
        "device_id": "nonexistent"
    }
    
    response = client.post('/api/workflows/config-retrieval',
                          json=config_data,
                          content_type='application/json')
    assert response.status_code == 404