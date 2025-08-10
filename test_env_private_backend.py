"""
Enhanced Backend Tests for .env.private functionality and provider testing
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import sys
sys.path.append('.')

from backend_server import app, load_config, save_config, load_private_env, save_private_env, providers, settings

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def temp_env_file():
    """Create temporary .env.private file for testing"""
    fd, path = tempfile.mkstemp(suffix='.env.private')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)

class TestEnvPrivateManagement:
    """Test .env.private file management functionality"""
    
    def test_get_private_env_status_nonexistent(self, client):
        """Test getting status when .env.private doesn't exist"""
        with patch('backend_server.os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            response = client.get('/api/env/private')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['exists'] is False
            assert data['enabled_providers'] == []
            assert data['file_size'] == 0
    
    def test_get_private_env_status_existing(self, client):
        """Test getting status when .env.private exists"""
        with patch('backend_server.os.path.exists') as mock_exists, \
             patch('backend_server.os.path.getsize') as mock_getsize:
            
            mock_exists.return_value = True
            mock_getsize.return_value = 256
            
            # Mock enabled providers
            with patch('backend_server.providers', {
                'groq': {'name': 'Groq', 'enabled': True, 'api_key': 'test-key'},
                'cerebras': {'name': 'Cerebras', 'enabled': True, 'api_key': ''},
                'openai': {'name': 'OpenAI', 'enabled': False, 'api_key': 'inactive-key'}
            }):
                response = client.get('/api/env/private')
                assert response.status_code == 200
                
                data = response.get_json()
                assert data['exists'] is True
                assert data['file_size'] == 256
                assert len(data['enabled_providers']) == 2  # Only enabled providers
                
                # Check provider details
                provider_names = [p['provider'] for p in data['enabled_providers']]
                assert 'groq' in provider_names
                assert 'cerebras' in provider_names
                assert 'openai' not in provider_names  # Not enabled
    
    def test_refresh_private_env(self, client):
        """Test refreshing .env.private file"""
        with patch('backend_server.save_private_env') as mock_save:
            response = client.post('/api/env/private/refresh')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
            assert 'updated successfully' in data['message']
            mock_save.assert_called_once()
    
    def test_refresh_private_env_error(self, client):
        """Test refresh error handling"""
        with patch('backend_server.save_private_env') as mock_save:
            mock_save.side_effect = Exception('Write permission denied')
            
            response = client.post('/api/env/private/refresh')
            assert response.status_code == 500
            
            data = response.get_json()
            assert data['success'] is False
            assert 'Write permission denied' in data['error']
    
    def test_clear_private_env(self, client):
        """Test clearing .env.private file"""
        with patch('backend_server.os.path.exists') as mock_exists, \
             patch('backend_server.os.remove') as mock_remove:
            
            mock_exists.return_value = True
            
            response = client.post('/api/env/private/clear')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
            assert 'cleared successfully' in data['message']
            mock_remove.assert_called_once()
    
    def test_clear_private_env_nonexistent(self, client):
        """Test clearing non-existent .env.private file"""
        with patch('backend_server.os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            response = client.post('/api/env/private/clear')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True

class TestProviderTesting:
    """Test enhanced provider testing functionality"""
    
    def test_provider_test_with_raw_data(self, client):
        """Test provider testing with raw data included"""
        with patch('backend_server.providers', {
            'groq': {
                'name': 'Groq', 'enabled': True, 'api_key': 'test-key',
                'model': 'llama-3.1-70b-versatile', 'base_url': 'https://api.groq.com/openai/v1',
                'status': 'connected', 'last_checked': ''
            }
        }), \
        patch('backend_server.test_provider_connection') as mock_test, \
        patch('backend_server.chat_with_provider') as mock_chat:
            
            mock_test.return_value = True
            mock_chat.return_value = {
                'provider': 'groq',
                'response': 'Test response successful',
                'tokens': 15,
                'model': 'llama-3.1-70b-versatile',
                'response_time': 1.2
            }
            
            response = client.post('/api/providers/groq/test', 
                                   json={
                                       'test_message': 'Hello test',
                                       'include_raw_data': True
                                   })
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Check connection test
            assert data['provider'] == 'groq'
            assert data['connection_test']['success'] is True
            assert 'response_time' in data['connection_test']
            
            # Check chat test
            assert data['chat_test']['success'] is True
            assert data['chat_test']['tokens_used'] == 15
            assert data['chat_test']['model'] == 'llama-3.1-70b-versatile'
            
            # Check raw data
            assert 'raw_data' in data
            assert 'request' in data['raw_data']
            assert 'response' in data['raw_data']
            assert data['raw_data']['request']['message'] == 'Hello test'
            assert data['raw_data']['request']['provider'] == 'groq'
            assert data['raw_data']['request']['has_api_key'] is True
            assert data['raw_data']['response']['full_response'] == 'Test response successful'
    
    def test_provider_test_chat_failure_with_raw_data(self, client):
        """Test provider testing when chat fails but includes raw data"""
        with patch('backend_server.providers', {
            'cerebras': {
                'name': 'Cerebras', 'enabled': True, 'api_key': 'invalid-key',
                'model': 'llama-4-scout-wse-3', 'base_url': 'https://api.cerebras.ai/v1',
                'status': 'connected', 'last_checked': ''
            }
        }), \
        patch('backend_server.test_provider_connection') as mock_test, \
        patch('backend_server.chat_with_provider') as mock_chat:
            
            mock_test.return_value = True
            mock_chat.side_effect = Exception('Authentication failed: Invalid API key')
            
            response = client.post('/api/providers/cerebras/test', 
                                   json={'include_raw_data': True})
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Connection should pass
            assert data['connection_test']['success'] is True
            
            # Chat should fail
            assert data['chat_test']['success'] is False
            assert 'Authentication failed' in data['chat_test']['error']
            
            # Raw data should include error details
            assert 'raw_data' in data
            assert 'error_details' in data['raw_data']
            assert 'Authentication failed' in data['raw_data']['error_details']['error_message']
    
    def test_provider_test_without_api_key(self, client):
        """Test provider testing when no API key is present"""
        with patch('backend_server.providers', {
            'openrouter': {
                'name': 'OpenRouter', 'enabled': True, 'api_key': '',
                'model': 'openrouter/auto', 'base_url': 'https://openrouter.ai/api/v1',
                'status': 'connected', 'last_checked': ''
            }
        }), \
        patch('backend_server.test_provider_connection') as mock_test:
            
            mock_test.return_value = True
            
            response = client.post('/api/providers/openrouter/test')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Should have connection test but no chat test
            assert data['connection_test']['success'] is True
            assert 'chat_test' not in data
    
    def test_provider_test_ollama_special_case(self, client):
        """Test provider testing for Ollama which doesn't need API key"""
        with patch('backend_server.providers', {
            'ollama': {
                'name': 'Ollama', 'enabled': True, 'api_key': '',
                'model': 'llama3.2', 'base_url': 'http://localhost:11434/v1',
                'status': 'connected', 'last_checked': ''
            }
        }), \
        patch('backend_server.test_provider_connection') as mock_test, \
        patch('backend_server.chat_with_provider') as mock_chat:
            
            mock_test.return_value = True
            mock_chat.return_value = {
                'provider': 'ollama',
                'response': 'Ollama test response',
                'tokens': 12,
                'model': 'llama3.2',
                'response_time': 0.8
            }
            
            response = client.post('/api/providers/ollama/test')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Should still perform chat test even without explicit API key
            assert data['connection_test']['success'] is True
            # Note: Ollama uses dummy API key internally, so has_api_key check passes
    
    def test_provider_update_saves_to_env_private(self, client):
        """Test that updating an enabled provider saves to .env.private"""
        with patch('backend_server.providers', {
            'groq': {'name': 'Groq', 'enabled': False, 'api_key': ''}
        }), \
        patch('backend_server.save_config') as mock_save_config, \
        patch('backend_server.save_private_env') as mock_save_env:
            
            # Enable provider with API key
            response = client.put('/api/providers/groq', 
                                  json={
                                      'enabled': True,
                                      'api_key': 'new-groq-key-12345'
                                  })
            
            assert response.status_code == 200
            mock_save_config.assert_called_once()
            mock_save_env.assert_called_once()

class TestEnvPrivateFunctions:
    """Test .env.private helper functions"""
    
    def test_save_private_env_only_enabled_providers(self):
        """Test that only enabled providers are saved to .env.private"""
        test_providers = {
            'groq': {'enabled': True, 'api_key': 'groq-key-123'},
            'cerebras': {'enabled': True, 'api_key': ''},  # Empty key
            'openai': {'enabled': False, 'api_key': 'openai-key-456'},  # Disabled
            'ollama': {'enabled': True, 'api_key': ''}  # Empty key for local service
        }
        
        with patch('backend_server.providers', test_providers), \
             patch('builtins.open', create=True) as mock_open:
            
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            save_private_env()
            
            # Should only write GROQ_API_KEY (has key and enabled)
            mock_file.write.assert_called_once_with('GROQ_API_KEY=groq-key-123')
    
    def test_load_private_env_updates_providers(self):
        """Test that loading .env.private updates provider API keys"""
        test_providers = {
            'groq': {'enabled': True, 'api_key': ''},
            'cerebras': {'enabled': True, 'api_key': ''},
            'openai': {'enabled': False, 'api_key': ''}
        }
        
        with patch('backend_server.providers', test_providers), \
             patch('backend_server.os.path.exists') as mock_exists, \
             patch('backend_server.load_dotenv') as mock_load, \
             patch('backend_server.os.environ', {
                 'GROQ_API_KEY': 'loaded-groq-key',
                 'CEREBRAS_API_KEY': 'loaded-cerebras-key',
                 'OPENAI_API_KEY': 'loaded-openai-key'
             }):
            
            mock_exists.return_value = True
            
            load_private_env()
            
            mock_load.assert_called_once()
            
            # Only enabled providers should get updated
            assert test_providers['groq']['api_key'] == 'loaded-groq-key'
            assert test_providers['cerebras']['api_key'] == 'loaded-cerebras-key'
            assert test_providers['openai']['api_key'] == ''  # Disabled, shouldn't update

class TestHealthEndpointEnhancements:
    """Test enhanced health endpoint with .env.private status"""
    
    def test_health_includes_env_private_status(self, client):
        """Test that health endpoint includes .env.private file status"""
        with patch('backend_server.os.path.exists') as mock_exists, \
             patch('backend_server.providers', {
                 'groq': {'enabled': True},
                 'cerebras': {'enabled': False}
             }):
            
            mock_exists.return_value = True
            
            response = client.get('/api/health')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert data['providers_enabled'] == 1
            assert data['env_private_exists'] is True
            assert 'timestamp' in data
            assert 'uptime' in data

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
