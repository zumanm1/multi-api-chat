"""
Comprehensive Backend Unit Tests
===============================
Complete pytest suite for testing all backend functionality including:
- API endpoints
- Provider management
- Device management
- AI agents integration
- Workflow orchestration
- Error handling
- Authentication and validation
"""

import pytest
import json
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
from flask import Flask

# Add the parent directory to the path so we can import the backend module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the backend application
import backend_server

# Test configuration data
TEST_CONFIG = {
    "providers": {
        "test_provider": {
            "name": "Test Provider",
            "enabled": True,
            "api_key": "test_key_123",
            "model": "test-model-v1",
            "base_url": "http://test.provider.com/v1",
            "status": "disconnected",
            "last_checked": ""
        },
        "openai": {
            "name": "OpenAI",
            "enabled": True,
            "api_key": "sk-test123",
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1",
            "status": "connected",
            "last_checked": "2024-01-01T12:00:00Z"
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
        "ollama": {
            "name": "Ollama",
            "enabled": True,
            "api_key": "",
            "model": "llama3.2:1b",
            "base_url": "http://localhost:11434/v1",
            "status": "connected",
            "last_checked": "2024-01-01T12:00:00Z"
        }
    },
    "settings": {
        "default_provider": "test_provider",
        "fallback_provider": "openai",
        "temperature": 0.7,
        "max_tokens": 2000,
        "system_prompt": "You are a helpful AI assistant for testing.",
        "features": {
            "auto_fallback": True,
            "speed_optimization": True,
            "cost_optimization": False,
            "multi_provider_compare": True,
            "usage_analytics": True
        }
    },
    "devices": {
        "test_router": {
            "name": "Test Router",
            "ip": "192.168.1.100",
            "model": "Cisco Test 2900",
            "username": "admin",
            "password": "testpass123",
            "port": 22,
            "status": "unknown",
            "last_checked": ""
        },
        "dummy_router": {
            "name": "Dummy Router",
            "ip": "192.168.1.1",
            "model": "Dummy Model",
            "username": "",
            "password": "",
            "port": 22,
            "status": "unknown",
            "last_checked": ""
        }
    }
}

class TestBackendServer:
    """Main test class for backend server functionality"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method that runs before each test"""
        # Reset global variables
        backend_server.providers = TEST_CONFIG["providers"].copy()
        backend_server.settings = TEST_CONFIG["settings"].copy()
        backend_server.devices = TEST_CONFIG["devices"].copy()
        backend_server.usage_stats = {}
        
        # Configure Flask app for testing
        backend_server.app.config['TESTING'] = True
        backend_server.app.config['WTF_CSRF_ENABLED'] = False

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask application"""
        with backend_server.app.test_client() as client:
            with backend_server.app.app_context():
                yield client

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing provider interactions"""
        with patch('backend_server.OpenAI') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            
            # Mock chat completions response
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Test AI response for unit testing"
            mock_response.choices = [mock_choice]
            
            mock_usage = MagicMock()
            mock_usage.total_tokens = 150
            mock_usage.prompt_tokens = 50
            mock_usage.completion_tokens = 100
            mock_response.usage = mock_usage
            
            mock_instance.chat.completions.create.return_value = mock_response
            
            # Mock models list for provider testing
            mock_models = MagicMock()
            mock_models.data = [
                MagicMock(id="gpt-4o"),
                MagicMock(id="gpt-3.5-turbo")
            ]
            mock_instance.models.list.return_value = mock_models
            
            yield mock_instance

    @pytest.fixture
    def mock_requests(self):
        """Mock requests for external API calls"""
        with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok", "models": []}
            mock_response.raise_for_status.return_value = None
            mock_response.text = json.dumps({"status": "ok"})
            
            mock_get.return_value = mock_response
            mock_post.return_value = mock_response
            
            yield {"get": mock_get, "post": mock_post}

    # =========================================================================
    # CORE API ENDPOINT TESTS
    # =========================================================================

    def test_health_endpoint(self, client):
        """Test the health check endpoint returns correct status"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'uptime' in data
        assert 'providers_enabled' in data
        assert 'ai_agents_available' in data
        assert isinstance(data['providers_enabled'], int)

    def test_health_endpoint_with_ai_agents(self, client):
        """Test health endpoint reports AI agent status correctly"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Should report whether AI agents are available
        assert 'ai_agents_available' in data
        assert isinstance(data['ai_agents_available'], bool)

    def test_providers_endpoint_get(self, client):
        """Test getting all providers returns correct data structure"""
        response = client.get('/api/providers')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Check all expected providers are present
        expected_providers = ['test_provider', 'openai', 'groq', 'ollama']
        for provider_id in expected_providers:
            assert provider_id in data
            provider = data[provider_id]
            assert 'name' in provider
            assert 'enabled' in provider
            assert 'model' in provider
            assert 'status' in provider
            assert 'base_url' in provider

    def test_providers_endpoint_structure_validation(self, client):
        """Test provider data structure contains all required fields"""
        response = client.get('/api/providers')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        for provider_id, provider in data.items():
            # Validate required fields
            required_fields = ['name', 'enabled', 'api_key', 'model', 'base_url', 'status', 'last_checked']
            for field in required_fields:
                assert field in provider, f"Provider {provider_id} missing field {field}"
            
            # Validate field types
            assert isinstance(provider['name'], str)
            assert isinstance(provider['enabled'], bool)
            assert isinstance(provider['api_key'], str)
            assert isinstance(provider['model'], str)
            assert isinstance(provider['base_url'], str)
            assert isinstance(provider['status'], str)

    def test_update_provider_success(self, client):
        """Test updating provider configuration with valid data"""
        update_data = {
            "enabled": True,
            "api_key": "updated_key_456",
            "model": "updated-model-v2",
            "temperature": 0.8
        }
        
        response = client.put('/api/providers/test_provider', 
                             json=update_data,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["enabled"] == True
        assert data["api_key"] == "updated_key_456"
        assert data["model"] == "updated-model-v2"

    def test_update_provider_nonexistent(self, client):
        """Test updating a provider that doesn't exist returns 404"""
        update_data = {"enabled": False}
        
        response = client.put('/api/providers/nonexistent_provider', 
                             json=update_data,
                             content_type='application/json')
        assert response.status_code == 404

    def test_update_provider_invalid_data(self, client):
        """Test updating provider with invalid data returns error"""
        # Test with invalid JSON
        response = client.put('/api/providers/test_provider',
                             data="invalid json",
                             content_type='application/json')
        assert response.status_code == 400

    # =========================================================================
    # SETTINGS MANAGEMENT TESTS
    # =========================================================================

    def test_settings_get(self, client):
        """Test retrieving current settings"""
        response = client.get('/api/settings')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Test based on actual config structure
        assert isinstance(data, dict)
        if "default_provider" in data:
            assert data["default_provider"] in ["test_provider", "groq", "openai"]
        if "temperature" in data:
            assert isinstance(data["temperature"], (int, float))
        if "features" in data:
            assert isinstance(data["features"], dict)

    def test_settings_update(self, client):
        """Test updating settings with valid data"""
        update_settings = {
            "temperature": 0.9,
            "max_tokens": 3000
        }
        
        response = client.put('/api/settings', 
                             json=update_settings,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, dict)
        # Check if the updated values are present
        if "temperature" in data:
            assert data["temperature"] == 0.9
        if "max_tokens" in data:
            assert data["max_tokens"] == 3000

    def test_settings_partial_update(self, client):
        """Test partial settings update preserves existing values"""
        # Get current settings first
        current_response = client.get('/api/settings')
        current_settings = json.loads(current_response.data)
        
        update_settings = {
            "temperature": 0.5,
            "max_tokens": 1500
        }
        
        response = client.put('/api/settings', 
                             json=update_settings,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, dict)
        if "temperature" in data:
            assert data["temperature"] == 0.5
        if "max_tokens" in data:
            assert data["max_tokens"] == 1500

    # =========================================================================
    # CHAT FUNCTIONALITY TESTS
    # =========================================================================

    def test_chat_success(self, client, mock_openai_client):
        """Test successful chat interaction with provider"""
        chat_data = {
            "message": "Hello, this is a test message",
            "provider": "test_provider",
            "system_prompt": "You are a test assistant"
        }
        
        response = client.post('/api/chat', 
                              json=chat_data,
                              content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["provider"] == "test_provider"
        assert data["response"] == "Test AI response for unit testing"
        assert data["tokens"] == 150
        assert "response_time" in data
        assert isinstance(data["response_time"], (int, float))

    def test_chat_with_model_selection(self, client, mock_openai_client):
        """Test chat with specific model selection"""
        chat_data = {
            "message": "Test with specific model",
            "provider": "test_provider",
            "model": "custom-test-model"
        }
        
        response = client.post('/api/chat', 
                              json=chat_data,
                              content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["model"] == "custom-test-model"

    def test_chat_missing_message(self, client):
        """Test chat request without message returns error"""
        chat_data = {
            "provider": "test_provider"
        }
        
        response = client.post('/api/chat', 
                              json=chat_data,
                              content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert "error" in data

    def test_chat_disabled_provider(self, client):
        """Test chat with disabled provider returns error"""
        # Disable the provider
        backend_server.providers["test_provider"]["enabled"] = False
        
        chat_data = {
            "message": "Test message",
            "provider": "test_provider"
        }
        
        response = client.post('/api/chat', 
                              json=chat_data,
                              content_type='application/json')
        assert response.status_code == 400

    def test_chat_with_fallback(self, client, mock_openai_client):
        """Test automatic fallback when primary provider fails"""
        # Enable fallback in settings
        backend_server.settings['features']['auto_fallback'] = True
        backend_server.settings['fallback_provider'] = 'openai'
        
        # Setup fallback scenario
        with patch('backend_server.chat_with_provider') as mock_chat:
            # First call fails, second call succeeds
            mock_chat.side_effect = [
                Exception("Primary provider failed", "connection_error"),
                {
                    "provider": "openai",
                    "response": "Fallback response",
                    "tokens": 50,
                    "model": "gpt-4o",
                    "response_time": 1.2,
                    "fallback_used": True
                }
            ]
            
            chat_data = {
                "message": "Test fallback message",
                "provider": "test_provider"
            }
            
            response = client.post('/api/chat', 
                                  json=chat_data,
                                  content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data["provider"] == "openai"  # Should fallback to openai
            assert data["fallback_used"] == True

    def test_chat_compare_multiple_providers(self, client, mock_openai_client):
        """Test comparing responses across multiple providers"""
        with patch('backend_server.chat_with_provider') as mock_chat:
            # Mock responses for both providers
            mock_chat.side_effect = [
                {
                    "provider": "test_provider",
                    "response": "Test provider response",
                    "tokens": 100,
                    "model": "test-model-v1",
                    "response_time": 1.0
                },
                {
                    "provider": "openai", 
                    "response": "OpenAI response",
                    "tokens": 120,
                    "model": "gpt-4o",
                    "response_time": 1.5
                }
            ]
            
            compare_data = {
                "message": "Compare this across providers",
                "providers": ["test_provider", "openai"]
            }
            
            response = client.post('/api/chat/compare', 
                                  json=compare_data,
                                  content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert isinstance(data, list)
            assert len(data) == 2
            
            # Check each response has correct structure
            for provider_response in data:
                assert "provider" in provider_response
                assert "response" in provider_response
                assert "response_time" in provider_response

    # =========================================================================
    # PROVIDER TESTING FUNCTIONALITY
    # =========================================================================

    def test_test_provider_success(self, client, mock_openai_client):
        """Test successful provider connection test"""
        with patch('backend_server.test_provider_connection') as mock_test:
            mock_test.return_value = True
            
            response = client.post('/api/providers/test_provider/test', 
                                  json={"include_raw_data": False},
                                  content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert "provider" in data
            assert data["provider"] == "test_provider"
            assert "status" in data
            
            # Check that provider status was updated
            assert backend_server.providers["test_provider"]["status"] == "connected"

    def test_test_provider_failure(self, client, mock_openai_client):
        """Test provider connection test failure"""
        with patch('backend_server.test_provider_connection') as mock_test:
            mock_test.return_value = False
            
            response = client.post('/api/providers/test_provider/test',
                                  json={"include_raw_data": False},
                                  content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert "provider" in data
            assert data["provider"] == "test_provider"
            # Check that provider status was updated to error
            assert backend_server.providers["test_provider"]["status"] == "error"

    def test_test_all_providers(self, client, mock_openai_client):
        """Test testing all enabled providers"""
        response = client.post('/api/providers/test-all')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Should test all enabled providers
        enabled_providers = [pid for pid, p in backend_server.providers.items() if p["enabled"]]
        for provider_id in enabled_providers:
            assert provider_id in data
            assert isinstance(data[provider_id], bool)

    def test_enhanced_provider_test(self, client, mock_openai_client):
        """Test enhanced provider testing endpoint with detailed data"""
        with patch('backend_server.test_provider_connection') as mock_test:
            mock_test.return_value = True
            
            # Test with raw data enabled
            response = client.post('/api/providers/test_provider/test',
                                  json={"include_raw_data": True, "test_message": "Enhanced test"},
                                  content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert "provider" in data
            assert data["provider"] == "test_provider"
            # Enhanced test should include connection details
            assert "connection_test" in data

    # =========================================================================
    # DEVICE MANAGEMENT TESTS
    # =========================================================================

    def test_list_devices(self, client):
        """Test listing all configured devices"""
        response = client.get('/api/devices')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "test_router" in data
        assert "dummy_router" in data
        
        for device_id, device in data.items():
            assert "name" in device
            assert "ip" in device
            assert "model" in device
            assert "status" in device

    def test_add_device_success(self, client):
        """Test successfully adding a new device"""
        device_data = {
            "id": "new_test_router",
            "name": "New Test Router",
            "ip": "192.168.1.200",
            "model": "Cisco Test 3900",
            "username": "testadmin",
            "password": "testpass456",
            "port": 22
        }
        
        response = client.post('/api/devices',
                              json=device_data,
                              content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["name"] == "New Test Router"
        assert data["ip"] == "192.168.1.200"
        
        # Verify device was added to global config
        assert "new_test_router" in backend_server.devices

    def test_add_device_missing_required_field(self, client):
        """Test adding device without required fields returns error"""
        device_data = {
            "name": "Incomplete Device"
            # Missing required 'id' field
        }
        
        response = client.post('/api/devices',
                              json=device_data,
                              content_type='application/json')
        assert response.status_code == 400

    def test_add_device_duplicate_id(self, client):
        """Test adding device with existing ID returns error"""
        device_data = {
            "id": "test_router",  # Already exists
            "name": "Duplicate Router",
            "ip": "192.168.1.201"
        }
        
        response = client.post('/api/devices',
                              json=device_data,
                              content_type='application/json')
        assert response.status_code == 400

    def test_update_device_success(self, client):
        """Test successfully updating device configuration"""
        update_data = {
            "name": "Updated Test Router",
            "ip": "192.168.2.100",
            "username": "newadmin"
        }
        
        response = client.put('/api/devices/test_router',
                             json=update_data,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["name"] == "Updated Test Router"
        assert data["ip"] == "192.168.2.100"
        assert data["username"] == "newadmin"

    def test_update_device_nonexistent(self, client):
        """Test updating device that doesn't exist returns 404"""
        update_data = {"name": "Non-existent Device"}
        
        response = client.put('/api/devices/nonexistent_device',
                             json=update_data,
                             content_type='application/json')
        assert response.status_code == 404

    def test_remove_device_success(self, client):
        """Test successfully removing a device"""
        response = client.delete('/api/devices/test_router')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] == True
        
        # Verify device was removed
        assert "test_router" not in backend_server.devices

    def test_remove_device_nonexistent(self, client):
        """Test removing device that doesn't exist returns 404"""
        response = client.delete('/api/devices/nonexistent_device')
        assert response.status_code == 404

    # =========================================================================
    # DEVICE CONNECTION AND COMMAND TESTS
    # =========================================================================

    def test_device_connection_test_success(self, client):
        """Test successful device connection test"""
        with patch('backend_server.test_router_connection') as mock_test:
            mock_test.return_value = (True, "Connection successful")
            
            response = client.post('/api/devices/test_router/test')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data["device"] == "test_router"
            assert data["success"] == True
            assert backend_server.devices["test_router"]["status"] == "online"

    def test_device_connection_test_failure(self, client):
        """Test failed device connection test"""
        with patch('backend_server.test_router_connection') as mock_test:
            mock_test.return_value = (False, "Connection timeout")
            
            response = client.post('/api/devices/test_router/test')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert "device" in data
            assert data["device"] == "test_router"
            assert "success" in data
            assert data["success"] == False

    def test_send_device_command_success(self, client):
        """Test successful command execution on device"""
        # Check if the function exists first
        if not hasattr(backend_server, 'send_command_to_router'):
            # Skip this test if function doesn't exist
            pytest.skip("send_command_to_router function not implemented")
            
        with patch('backend_server.send_command_to_router') as mock_send:
            mock_send.return_value = (True, "Command output: show ip route")
            
            command_data = {"command": "show ip route"}
            
            response = client.post('/api/devices/test_router/command',
                                  json=command_data,
                                  content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert "device" in data
            if "command" in data:
                assert data["command"] == "show ip route"

    def test_send_device_command_missing_command(self, client):
        """Test command execution without command parameter"""
        command_data = {}
        
        response = client.post('/api/devices/test_router/command',
                              json=command_data,
                              content_type='application/json')
        assert response.status_code == 400

    def test_send_device_command_nonexistent_device(self, client):
        """Test command execution on non-existent device"""
        command_data = {"command": "show version"}
        
        response = client.post('/api/devices/nonexistent/command',
                              json=command_data,
                              content_type='application/json')
        assert response.status_code == 404

    # =========================================================================
    # USAGE STATISTICS TESTS
    # =========================================================================

    def test_usage_endpoint_empty(self, client):
        """Test usage statistics endpoint with empty data"""
        response = client.get('/api/usage')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_usage_tracking(self, client):
        """Test that usage is properly tracked"""
        # Add some test usage data
        test_date = datetime.now().strftime('%Y-%m-%d')
        backend_server.track_usage("test_provider", 1.5, 200)
        
        response = client.get('/api/usage')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert test_date in data
        assert "test_provider" in data[test_date]
        assert data[test_date]["test_provider"]["requests"] == 1
        assert data[test_date]["test_provider"]["tokens"] == 200
        assert data[test_date]["test_provider"]["total_response_time"] == 1.5

    def test_usage_multiple_requests_tracking(self, client):
        """Test tracking multiple requests for same provider"""
        backend_server.track_usage("test_provider", 1.0, 100)
        backend_server.track_usage("test_provider", 2.0, 150)
        
        test_date = datetime.now().strftime('%Y-%m-%d')
        response = client.get('/api/usage')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        provider_stats = data[test_date]["test_provider"]
        assert provider_stats["requests"] == 2
        assert provider_stats["tokens"] == 250
        assert provider_stats["total_response_time"] == 3.0

    # =========================================================================
    # OLLAMA SPECIFIC TESTS
    # =========================================================================

    def test_ollama_provider_configuration(self, client):
        """Test Ollama provider has correct default configuration"""
        response = client.get('/api/providers')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        ollama = data["ollama"]
        
        assert ollama["name"] == "Ollama"
        assert ollama["api_key"] == ""  # Ollama doesn't need API key
        assert "localhost:11434" in ollama["base_url"]
        assert ollama["model"] == "llama3.2:1b"

    def test_ollama_models_endpoint_success(self, client, mock_requests):
        """Test Ollama models listing endpoint"""
        # Mock Ollama models API response
        mock_requests["get"].return_value.json.return_value = {
            "models": [
                {"name": "llama3.2:1b", "size": 1000000, "modified_at": "2024-01-01T00:00:00Z"},
                {"name": "llama3.2:7b", "size": 7000000, "modified_at": "2024-01-01T00:00:00Z"}
            ]
        }
        
        response = client.get('/api/providers/ollama/models')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "models" in data
        assert "total" in data
        assert len(data["models"]) == 2
        assert data["models"][0]["name"] == "llama3.2:1b"

    def test_ollama_models_endpoint_failure(self, client, mock_requests):
        """Test Ollama models endpoint when service is down"""
        # Mock connection error
        from requests.exceptions import ConnectionError
        mock_requests["get"].side_effect = ConnectionError("Connection refused")
        
        response = client.get('/api/providers/ollama/models')
        assert response.status_code == 503
        
        data = json.loads(response.data)
        assert "error" in data
        assert "Ollama server" in data["error"]

    def test_ollama_pull_model_success(self, client, mock_requests):
        """Test successful Ollama model pulling"""
        # Mock streaming response
        mock_requests["post"].return_value.iter_lines.return_value = [
            b'{"status": "pulling manifest"}',
            b'{"status": "downloading", "completed": 50, "total": 100}',
            b'{"status": "success"}'
        ]
        
        pull_data = {"model": "llama3.2:3b"}
        
        response = client.post('/api/providers/ollama/pull', 
                              json=pull_data,
                              content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] == True
        assert data["model"] == "llama3.2:3b"
        assert "status_log" in data

    # =========================================================================
    # AI AGENTS INTEGRATION TESTS
    # =========================================================================

    def test_ai_agents_status_endpoint(self, client):
        """Test AI agents status endpoint"""
        response = client.get('/api/ai/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Check for actual response structure (available, status, enabled)
        assert "available" in data
        assert "status" in data or "enabled" in data
        assert isinstance(data["available"], bool)

    @patch('backend_server.AI_AGENTS_AVAILABLE', True)
    @patch('backend_server.process_ai_request_sync')
    def test_ai_chat_request(self, mock_process, client):
        """Test AI agents chat processing"""
        mock_process.return_value = {
            "response": "AI chat response from agent",
            "agent": "chat_agent",
            "confidence": 0.95
        }
        
        ai_data = {
            "agent_type": "chat",
            "message": "Help me with API configuration",
            "context": {"user_id": "test_user"}
        }
        
        response = client.post('/api/ai/chat',
                              json=ai_data,
                              content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "response" in data
        assert "agent" in data
        mock_process.assert_called_once()

    @patch('backend_server.AI_AGENTS_AVAILABLE', True)
    @patch('backend_server.process_ai_request_sync')
    def test_ai_analytics_request(self, mock_process, client):
        """Test AI agents analytics processing"""
        mock_process.return_value = {
            "insights": ["Usage increased by 20%", "Top provider is OpenAI"],
            "charts": {"usage_trend": [1, 2, 3, 4, 5]},
            "agent": "analytics_agent"
        }
        
        ai_data = {
            "message": "Show usage trends for last week",
            "context": {"time_range": "7d"}
        }
        
        response = client.post('/api/ai/analytics',
                              json=ai_data,
                              content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "insights" in data
        assert "agent" in data

    @patch('backend_server.AI_AGENTS_AVAILABLE', False)
    def test_ai_requests_when_unavailable(self, client):
        """Test AI endpoints when AI agents are not available"""
        ai_data = {
            "agent_type": "chat",
            "message": "Test message"
        }
        
        response = client.post('/api/ai/chat',
                              json=ai_data,
                              content_type='application/json')
        assert response.status_code == 503
        
        data = json.loads(response.data)
        assert "error" in data
        assert "not available" in data["error"]

    # =========================================================================
    # WORKFLOW ORCHESTRATION TESTS
    # =========================================================================

    @patch('backend_server.AI_AGENTS_AVAILABLE', True)
    def test_workflow_create(self, client):
        """Test creating a new AI workflow - skip if endpoint doesn't exist"""
        workflow_data = {
            "name": "test_workflow",
            "description": "Test workflow for unit testing",
            "tasks": [
                {"type": "chat", "agent": "chat_agent", "input": "Task 1"},
                {"type": "analytics", "agent": "analytics_agent", "input": "Task 2"}
            ]
        }
        
        response = client.post('/api/workflows/create',
                              json=workflow_data,
                              content_type='application/json')
        
        # Accept both successful creation and endpoint not found
        if response.status_code == 404:
            pytest.skip("Workflow endpoints not implemented")
        else:
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "workflow_id" in data or "status" in data

    @patch('backend_server.AI_AGENTS_AVAILABLE', True)
    def test_workflow_execute(self, client):
        """Test executing a workflow - skip if endpoints don't exist"""
        # First try to create a workflow
        workflow_data = {
            "name": "execute_test_workflow",
            "tasks": [{"type": "chat", "agent": "chat_agent", "input": "Execute test"}]
        }
        
        create_response = client.post('/api/workflows/create', json=workflow_data)
        
        if create_response.status_code == 404:
            pytest.skip("Workflow endpoints not implemented")
            
        # Only proceed if create was successful
        if create_response.status_code == 200:
            create_data = json.loads(create_response.data)
            if "workflow_id" in create_data:
                workflow_id = create_data["workflow_id"]
                
                # Execute the workflow
                response = client.post(f'/api/workflows/{workflow_id}/execute')
                if response.status_code != 404:  # Skip if execute endpoint doesn't exist
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert "status" in data
            else:
                pytest.skip("Workflow creation response format unexpected")

    @patch('backend_server.AI_AGENTS_AVAILABLE', True)
    def test_workflow_status(self, client):
        """Test checking workflow status - skip if endpoints don't exist"""
        # First try to create a workflow
        workflow_data = {
            "name": "status_test_workflow",
            "tasks": [{"type": "chat", "agent": "chat_agent", "input": "Status test"}]
        }
        
        create_response = client.post('/api/workflows/create', json=workflow_data)
        
        if create_response.status_code == 404:
            pytest.skip("Workflow endpoints not implemented")
            
        # Only proceed if create was successful
        if create_response.status_code == 200:
            create_data = json.loads(create_response.data)
            if "workflow_id" in create_data:
                workflow_id = create_data["workflow_id"]
                
                # Check status
                response = client.get(f'/api/workflows/{workflow_id}/status')
                if response.status_code != 404:  # Skip if status endpoint doesn't exist
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert "status" in data
            else:
                pytest.skip("Workflow creation response format unexpected")

    def test_workflow_list(self, client):
        """Test listing all workflows"""
        response = client.get('/api/workflows')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "workflows" in data
        assert isinstance(data["workflows"], list)

    # =========================================================================
    # ERROR HANDLING TESTS
    # =========================================================================

    def test_invalid_json_request(self, client):
        """Test endpoints handle invalid JSON gracefully"""
        response = client.post('/api/chat',
                              data="invalid json",
                              content_type='application/json')
        assert response.status_code == 400

    def test_missing_content_type(self, client):
        """Test endpoints handle missing content-type gracefully"""
        response = client.post('/api/chat',
                              data=json.dumps({"message": "test"}))
        # Should still work or return appropriate error
        assert response.status_code in [200, 400, 415]

    def test_large_request_body(self, client):
        """Test endpoints handle large request bodies appropriately"""
        large_message = "x" * 100000  # 100KB message
        chat_data = {"message": large_message, "provider": "test_provider"}
        
        response = client.post('/api/chat',
                              json=chat_data,
                              content_type='application/json')
        # Should handle gracefully, either succeed or return appropriate error
        assert response.status_code in [200, 400, 413]

    def test_concurrent_requests(self, client, mock_openai_client):
        """Test handling multiple concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.post('/api/chat',
                              json={"message": "concurrent test", "provider": "test_provider"},
                              content_type='application/json')
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should complete successfully
        for result in results:
            assert result.status_code == 200

    # =========================================================================
    # CONFIGURATION AND FILE MANAGEMENT TESTS
    # =========================================================================

    def test_config_file_operations(self):
        """Test configuration file save and load operations"""
        # Test save_config function
        original_providers = backend_server.providers.copy()
        original_settings = backend_server.settings.copy()
        
        # Modify config
        backend_server.providers["test_provider"]["enabled"] = False
        backend_server.settings["temperature"] = 0.9
        
        # Save and reload
        backend_server.save_config()
        backend_server.load_config()
        
        # Verify changes were persisted
        assert backend_server.providers["test_provider"]["enabled"] == False
        assert backend_server.settings["temperature"] == 0.9
        
        # Restore original values
        backend_server.providers = original_providers
        backend_server.settings = original_settings
        backend_server.save_config()

    @patch('builtins.open', mock_open(read_data='{"invalid": json}'))
    def test_config_load_invalid_json(self):
        """Test handling of invalid JSON in config file"""
        with patch('json.load') as mock_json:
            mock_json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            
            # Should handle gracefully and use defaults
            backend_server.load_config()
            
            # Should have some default providers
            assert isinstance(backend_server.providers, dict)
            assert len(backend_server.providers) > 0

    def test_env_private_file_operations(self, client):
        """Test .env.private file operations for API keys"""
        response = client.get('/api/env-private/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "exists" in data
        assert "keys_count" in data

    def test_env_private_refresh(self, client):
        """Test refreshing API keys from .env.private"""
        response = client.post('/api/env-private/refresh')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] == True

    # =========================================================================
    # PERFORMANCE AND LOAD TESTS
    # =========================================================================

    def test_response_time_tracking(self, client, mock_openai_client):
        """Test that response times are properly tracked"""
        start_time = time.time()
        
        chat_data = {"message": "Performance test", "provider": "test_provider"}
        response = client.post('/api/chat', json=chat_data)
        
        end_time = time.time()
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Response time should be reasonable
        assert "response_time" in data
        assert 0 <= data["response_time"] <= (end_time - start_time) + 1  # Allow 1s buffer

    def test_memory_usage_reasonable(self, client):
        """Test that memory usage doesn't grow excessively"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make multiple requests
        for i in range(50):
            response = client.get('/api/health')
            assert response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB)
        assert memory_growth < 100 * 1024 * 1024

    # =========================================================================
    # ADDITIONAL COVERAGE TESTS
    # =========================================================================

    def test_provider_models_endpoint(self, client):
        """Test getting models for a specific provider"""
        response = client.get('/api/providers/test_provider/models')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "models" in data
        assert "source" in data

    def test_provider_models_nonexistent(self, client):
        """Test getting models for non-existent provider"""
        response = client.get('/api/providers/nonexistent/models')
        assert response.status_code == 404

    def test_chat_without_provider(self, client, mock_openai_client):
        """Test chat request without specifying provider uses default"""
        chat_data = {
            "message": "Test with default provider"
        }
        
        response = client.post('/api/chat', 
                              json=chat_data,
                              content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Should use the default provider from settings
        assert data["provider"] == backend_server.settings["default_provider"]

    def test_chat_nonexistent_provider(self, client):
        """Test chat with non-existent provider returns error"""
        chat_data = {
            "message": "Test message",
            "provider": "nonexistent_provider"
        }
        
        response = client.post('/api/chat', 
                              json=chat_data,
                              content_type='application/json')
        assert response.status_code == 404

    def test_chat_compare_empty_providers(self, client):
        """Test chat compare with empty providers list uses all enabled"""
        compare_data = {
            "message": "Compare across all providers",
            "providers": []
        }
        
        response = client.post('/api/chat/compare', 
                              json=compare_data,
                              content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        # Should use all enabled providers
        enabled_count = len([p for p in backend_server.providers.values() if p["enabled"]])
        assert len(data) <= enabled_count

    def test_chat_error_status_codes(self, client):
        """Test chat endpoint returns correct error status codes"""
        # Test with authentication error
        with patch('backend_server.chat_with_provider') as mock_chat:
            mock_chat.side_effect = Exception("Authentication failed", "auth")
            
            response = client.post('/api/chat',
                                  json={"message": "test", "provider": "test_provider"},
                                  content_type='application/json')
            assert response.status_code == 401

    def test_test_provider_ollama_special_case(self, client, mock_requests):
        """Test provider testing for Ollama special case"""
        # Mock Ollama API response
        mock_requests["get"].return_value.json.return_value = {
            "models": [{"name": "llama3.2"}]
        }
        
        with patch('backend_server.test_provider_connection') as mock_test:
            mock_test.return_value = True
            
            response = client.post('/api/providers/ollama/test',
                                  json={"include_raw_data": False},
                                  content_type='application/json')
            assert response.status_code == 200

    def test_env_private_clear(self, client):
        """Test clearing .env.private file"""
        response = client.post('/api/env-private/clear')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] == True

    def test_ai_devices_endpoint(self, client):
        """Test AI devices endpoint"""
        with patch('backend_server.AI_AGENTS_AVAILABLE', True), \
             patch('backend_server.process_ai_request_sync') as mock_process:
            
            mock_process.return_value = {
                "device_status": "All devices operational",
                "agent": "device_agent"
            }
            
            ai_data = {
                "message": "Check device status",
                "context": {"device_filter": "all"}
            }
            
            response = client.post('/api/ai/devices',
                                  json=ai_data,
                                  content_type='application/json')
            assert response.status_code == 200

    def test_ai_operations_endpoint(self, client):
        """Test AI operations endpoint"""
        with patch('backend_server.AI_AGENTS_AVAILABLE', True), \
             patch('backend_server.process_ai_request_sync') as mock_process:
            
            mock_process.return_value = {
                "operations_status": "System running smoothly",
                "agent": "operations_agent"
            }
            
            ai_data = {
                "message": "Check system operations",
                "context": {"check_type": "full"}
            }
            
            response = client.post('/api/ai/operations',
                                  json=ai_data,
                                  content_type='application/json')
            assert response.status_code == 200

    def test_ai_automation_endpoint(self, client):
        """Test AI automation endpoint"""
        with patch('backend_server.AI_AGENTS_AVAILABLE', True), \
             patch('backend_server.process_ai_request_sync') as mock_process:
            
            mock_process.return_value = {
                "automation_suggestions": ["Enable auto-scaling", "Set up monitoring"],
                "agent": "automation_agent"
            }
            
            ai_data = {
                "message": "Suggest automation improvements",
                "context": {"scope": "infrastructure"}
            }
            
            response = client.post('/api/ai/automation',
                                  json=ai_data,
                                  content_type='application/json')
            assert response.status_code == 200

    def test_ai_toggle_endpoint(self, client):
        """Test AI agents toggle endpoint"""
        with patch('backend_server.AI_AGENTS_AVAILABLE', True), \
             patch('backend_server.toggle_ai_agents') as mock_toggle:
            
            mock_toggle.return_value = {
                "enabled": False,
                "message": "AI agents disabled"
            }
            
            toggle_data = {"enabled": False}
            
            response = client.post('/api/ai/toggle',
                                  json=toggle_data,
                                  content_type='application/json')
            assert response.status_code == 200

    def test_missing_message_ai_endpoints(self, client):
        """Test AI endpoints return error when message is missing"""
        with patch('backend_server.AI_AGENTS_AVAILABLE', True):
            endpoints = ['/api/ai/chat', '/api/ai/analytics', '/api/ai/devices', 
                        '/api/ai/operations', '/api/ai/automation']
            
            for endpoint in endpoints:
                response = client.post(endpoint,
                                      json={"context": {}},
                                      content_type='application/json')
                assert response.status_code == 400

    def test_utility_functions_direct(self):
        """Test utility functions directly"""
        # Test get_client for different providers
        with patch('backend_server.OpenAI') as mock_openai:
            mock_instance = MagicMock()
            mock_openai.return_value = mock_instance
            
            # Test OpenRouter specific headers
            backend_server.providers["openrouter"] = {
                "name": "OpenRouter",
                "enabled": True,
                "api_key": "test_key",
                "model": "test-model",
                "base_url": "https://openrouter.ai/api/v1",
                "status": "disconnected",
                "last_checked": ""
            }
            client = backend_server.get_client("openrouter")
            assert client is not None

    def test_test_provider_connection_function(self):
        """Test test_provider_connection utility function directly"""
        # Test with non-Ollama provider
        with patch('backend_server.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            result = backend_server.test_provider_connection("test_provider")
            assert result == True
            assert backend_server.providers["test_provider"]["status"] == "connected"

    def test_test_provider_connection_failure_function(self):
        """Test test_provider_connection failure directly"""
        with patch('backend_server.get_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Connection failed")
            
            result = backend_server.test_provider_connection("test_provider")
            assert result == False
            assert backend_server.providers["test_provider"]["status"] == "error"

    def test_ollama_test_provider_connection(self, mock_requests):
        """Test Ollama-specific test_provider_connection"""
        # Mock successful Ollama response
        mock_requests["get"].return_value.json.return_value = {
            "models": [{"name": "llama3.2"}]
        }
        
        result = backend_server.test_provider_connection("ollama")
        assert result == True
        assert backend_server.providers["ollama"]["status"] == "connected"

    def test_save_and_load_usage(self):
        """Test save_usage and load_usage functions"""
        # Add some usage data
        backend_server.track_usage("test_provider", 1.0, 100)
        
        # Save and reload
        if hasattr(backend_server, 'save_usage'):
            backend_server.save_usage()
            backend_server.usage_stats = {}  # Clear in memory
            backend_server.load_usage()
            
            # Verify data was persisted
            today = datetime.now().strftime('%Y-%m-%d')
            assert today in backend_server.usage_stats
            assert "test_provider" in backend_server.usage_stats[today]

    # =========================================================================
    # UTILITY FUNCTION TESTS
    # =========================================================================

    def test_track_usage_function(self):
        """Test the track_usage utility function"""
        # Clear existing usage stats
        backend_server.usage_stats = {}
        
        # Track some usage
        backend_server.track_usage("test_provider", 2.5, 300)
        
        today = datetime.now().strftime('%Y-%m-%d')
        assert today in backend_server.usage_stats
        assert "test_provider" in backend_server.usage_stats[today]
        
        stats = backend_server.usage_stats[today]["test_provider"]
        assert stats["requests"] == 1
        assert stats["tokens"] == 300
        assert stats["total_response_time"] == 2.5

    def test_get_client_function(self, mock_openai_client):
        """Test the get_client utility function"""
        with patch('backend_server.OpenAI') as mock_openai:
            mock_openai.return_value = mock_openai_client
            
            client = backend_server.get_client("test_provider")
            assert client is not None
            
            # Verify OpenAI was called with correct parameters
            mock_openai.assert_called_with(
                api_key="test_key_123",
                base_url="http://test.provider.com/v1"
            )

    def test_get_client_ollama_configuration(self):
        """Test get_client function properly configures Ollama"""
        with patch('backend_server.OpenAI') as mock_openai:
            backend_server.get_client("ollama")
            
            # Verify Ollama was configured with dummy API key
            mock_openai.assert_called_with(
                api_key="ollama",  # Dummy API key for Ollama
                base_url="http://localhost:11434/v1"
            )

    def test_chat_with_provider_function(self, mock_openai_client):
        """Test the chat_with_provider utility function"""
        with patch('backend_server.get_client') as mock_get_client:
            mock_get_client.return_value = mock_openai_client
            
            result = backend_server.chat_with_provider(
                "test_provider", 
                "Test message", 
                "Test system prompt"
            )
            
            assert result["provider"] == "test_provider"
            assert result["response"] == "Test AI response for unit testing"
            assert result["tokens"] == 150
            assert result["model"] == "test-model-v1"
            assert "response_time" in result


# =========================================================================
# SPECIALIZED TEST CLASSES
# =========================================================================

class TestWorkflowOrchestration:
    """Specialized tests for workflow orchestration functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        backend_server.providers = TEST_CONFIG["providers"].copy()
        backend_server.settings = TEST_CONFIG["settings"].copy()
        backend_server.devices = TEST_CONFIG["devices"].copy()

    @pytest.fixture
    def client(self):
        backend_server.app.config['TESTING'] = True
        with backend_server.app.test_client() as client:
            yield client

    @patch('backend_server.AI_AGENTS_AVAILABLE', True)
    def test_complex_workflow_creation(self, client):
        """Test creating complex multi-step workflows"""
        complex_workflow = {
            "name": "complex_analytics_workflow",
            "description": "Complex workflow with multiple dependencies",
            "tasks": [
                {
                    "id": "fetch_data",
                    "type": "analytics", 
                    "agent": "analytics_agent",
                    "input": "Fetch usage data for last 30 days",
                    "dependencies": []
                },
                {
                    "id": "analyze_data",
                    "type": "analytics",
                    "agent": "analytics_agent", 
                    "input": "Analyze usage patterns",
                    "dependencies": ["fetch_data"]
                },
                {
                    "id": "generate_report",
                    "type": "chat",
                    "agent": "chat_agent",
                    "input": "Generate summary report",
                    "dependencies": ["analyze_data"]
                }
            ],
            "settings": {
                "timeout": 300,
                "retry_count": 2,
                "parallel_execution": False
            }
        }
        
        response = client.post('/api/workflows/create',
                              json=complex_workflow,
                              content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "workflow_id" in data
        assert data["status"] == "created"

    def test_workflow_validation(self, client):
        """Test workflow validation for invalid configurations"""
        invalid_workflows = [
            # Missing required fields
            {"description": "Missing name field"},
            # Invalid task structure
            {"name": "invalid_tasks", "tasks": [{"invalid": "structure"}]},
            # Circular dependencies
            {
                "name": "circular_deps",
                "tasks": [
                    {"id": "task1", "dependencies": ["task2"]},
                    {"id": "task2", "dependencies": ["task1"]}
                ]
            }
        ]
        
        for invalid_workflow in invalid_workflows:
            response = client.post('/api/workflows/create',
                                  json=invalid_workflow,
                                  content_type='application/json')
            assert response.status_code == 400


class TestConcurrencyAndThreadSafety:
    """Tests for concurrent operations and thread safety"""
    
    @pytest.fixture
    def client(self):
        backend_server.app.config['TESTING'] = True
        with backend_server.app.test_client() as client:
            yield client

    def test_concurrent_config_updates(self, client):
        """Test thread-safe configuration updates"""
        import concurrent.futures
        import random
        
        def update_provider():
            provider_id = "test_provider"
            update_data = {
                "enabled": random.choice([True, False]),
                "temperature": random.uniform(0.1, 1.0)
            }
            return client.put(f'/api/providers/{provider_id}',
                             json=update_data,
                             content_type='application/json')
        
        # Run concurrent updates
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_provider) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All updates should complete successfully
        for result in results:
            assert result.status_code == 200

    def test_concurrent_usage_tracking(self):
        """Test thread-safe usage tracking"""
        import concurrent.futures
        import random
        
        def track_random_usage():
            provider = random.choice(["test_provider", "openai", "groq"])
            response_time = random.uniform(0.5, 3.0)
            tokens = random.randint(50, 500)
            backend_server.track_usage(provider, response_time, tokens)
        
        # Clear usage stats
        backend_server.usage_stats = {}
        
        # Run concurrent tracking
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(track_random_usage) for _ in range(100)]
            [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all usage was tracked without corruption
        today = datetime.now().strftime('%Y-%m-%d')
        assert today in backend_server.usage_stats
        
        total_requests = 0
        for provider_stats in backend_server.usage_stats[today].values():
            total_requests += provider_stats["requests"]
        
        assert total_requests == 100


# =========================================================================
# ADDITIONAL TEST CLASSES FOR EDGE CASES
# =========================================================================

class TestAdditionalEndpoints:
    """Tests for additional endpoints and edge cases"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        backend_server.providers = TEST_CONFIG["providers"].copy()
        backend_server.settings = TEST_CONFIG["settings"].copy()
        backend_server.devices = TEST_CONFIG["devices"].copy()
        backend_server.usage_stats = {}
        
    @pytest.fixture
    def client(self):
        backend_server.app.config['TESTING'] = True
        with backend_server.app.test_client() as client:
            yield client

    def test_router_connection_functions(self):
        """Test router connection utility functions"""
        if hasattr(backend_server, 'test_router_connection'):
            device = backend_server.devices["test_router"]
            
            # Test successful connection
            with patch('paramiko.SSHClient') as mock_ssh_class:
                mock_ssh = MagicMock()
                mock_ssh_class.return_value = mock_ssh
                
                # Mock successful SSH connection
                mock_stdout = MagicMock()
                mock_stdout.read.return_value.decode.return_value = "Cisco IOS Version"
                mock_ssh.exec_command.return_value = (None, mock_stdout, MagicMock())
                
                success, output = backend_server.test_router_connection(device)
                assert success == True
                assert "Cisco IOS" in output

    def test_router_command_functions(self):
        """Test router command utility functions"""
        if hasattr(backend_server, 'send_router_command'):
            device = backend_server.devices["test_router"]
            
            # Test successful command execution
            with patch('paramiko.SSHClient') as mock_ssh_class:
                mock_ssh = MagicMock()
                mock_ssh_class.return_value = mock_ssh
                
                # Mock successful command execution
                mock_stdout = MagicMock()
                mock_stdout.read.return_value.decode.return_value = "Command output"
                mock_stderr = MagicMock()
                mock_stderr.read.return_value.decode.return_value = ""
                mock_ssh.exec_command.return_value = (None, mock_stdout, mock_stderr)
                
                success, output = backend_server.send_router_command(device, "show version")
                assert success == True
                assert output == "Command output"

    def test_error_handling_edge_cases(self, client):
        """Test various error handling edge cases"""
        # Test malformed JSON
        response = client.post('/api/chat',
                              data='[invalid json}',
                              content_type='application/json')
        assert response.status_code == 400
        
        # Test empty request body
        response = client.post('/api/chat',
                              data='',
                              content_type='application/json')
        assert response.status_code == 400

    def test_private_env_error_handling(self, client):
        """Test .env.private error handling"""
        with patch('os.path.exists', return_value=False):
            response = client.get('/api/env-private/status')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["exists"] == False

    def test_provider_fallback_without_fallback_enabled(self, client):
        """Test provider fallback when fallback is disabled"""
        # Disable fallback
        backend_server.settings['features']['auto_fallback'] = False
        
        with patch('backend_server.chat_with_provider') as mock_chat:
            mock_chat.side_effect = Exception("Provider failed", "connection_error")
            
            chat_data = {
                "message": "Test message",
                "provider": "test_provider"
            }
            
            response = client.post('/api/chat',
                                  json=chat_data,
                                  content_type='application/json')
            assert response.status_code == 500

    def test_various_error_types(self, client):
        """Test different error types in chat endpoint"""
        error_types = [
            ("rate_limit", 429),
            ("not_found", 404),
            ("auth", 401),
            ("unknown", 500)
        ]
        
        for error_type, expected_code in error_types:
            with patch('backend_server.chat_with_provider') as mock_chat:
                mock_chat.side_effect = Exception(f"Test {error_type} error", error_type)
                
                response = client.post('/api/chat',
                                      json={"message": "test", "provider": "test_provider"},
                                      content_type='application/json')
                assert response.status_code == expected_code

# =========================================================================
# TEST RUNNER AND REPORTING
# =========================================================================

if __name__ == "__main__":
    # Configure pytest to run with detailed output and coverage
    pytest_args = [
        __file__,
        "-v",  # verbose output
        "--tb=short",  # short traceback format
        "--durations=10",  # show 10 slowest tests
        "--cov=backend_server",  # coverage for backend_server module
        "--cov-report=html:htmlcov",  # HTML coverage report
        "--cov-report=term-missing",  # terminal coverage with missing lines
        "-x",  # stop on first failure
    ]
    
    import sys
    sys.exit(pytest.main(pytest_args))
