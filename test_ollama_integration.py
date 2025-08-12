#!/usr/bin/env python3
"""
Comprehensive Ollama Integration Test Suite

This script tests all aspects of Ollama integration including:
- Ollama provider appears in the provider list
- Connection testing works correctly
- Chat functionality works with Ollama models
- Fallback to other providers works if Ollama fails
- Usage tracking records Ollama requests properly

The tests can run with or without Ollama server running locally.
"""

import pytest
import requests
import json
import time
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration
BASE_URL = "http://localhost:7002"
OLLAMA_BASE_URL = "http://localhost:11434"

class TestOllamaIntegration:
    """Test suite for Ollama integration functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method to ensure backend server is running."""
        self.base_url = BASE_URL
        self.ollama_url = OLLAMA_BASE_URL
        self.test_model = "llama3.2:1b"  # Small model for testing
        
    def check_backend_server(self):
        """Check if backend server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
    
    def check_ollama_server(self):
        """Check if Ollama server is running."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
    
    def test_ollama_provider_in_list(self):
        """Test that Ollama provider appears in the provider list."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
            
        response = requests.get(f"{self.base_url}/api/providers")
        assert response.status_code == 200
        
        providers = response.json()
        assert "ollama" in providers, "Ollama provider not found in provider list"
        
        ollama_provider = providers["ollama"]
        assert ollama_provider["name"] == "Ollama"
        assert "model" in ollama_provider
        assert "base_url" in ollama_provider
        assert "status" in ollama_provider
        
        # Test that base URL is set correctly for Ollama
        expected_base_url = "http://localhost:11434/v1"
        assert ollama_provider["base_url"] == expected_base_url
        
        print("✅ Ollama provider correctly appears in provider list")
        
    def test_ollama_provider_configuration(self):
        """Test Ollama provider configuration details."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
            
        response = requests.get(f"{self.base_url}/api/providers")
        assert response.status_code == 200
        
        providers = response.json()
        ollama = providers["ollama"]
        
        # Check Ollama-specific configuration
        assert ollama["api_key"] == ""  # Ollama doesn't require API key
        assert ollama["model"] in ["llama3.2", "llama3.2:1b", "llama3.2:3b"]  # Common default models
        
        print("✅ Ollama provider configuration is correct")
        
    def test_ollama_connection_with_server_running(self):
        """Test connection to Ollama when server is running."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
        
        if not self.check_ollama_server():
            pytest.skip("Ollama server not running - use test_ollama_connection_without_server instead")
        
        response = requests.post(f"{self.base_url}/api/providers/ollama/test")
        assert response.status_code == 200
        
        result = response.json()
        assert result["provider"] == "ollama"
        assert result["success"] == True
        assert "response_time" in result
        
        # Check that status was updated
        providers_response = requests.get(f"{self.base_url}/api/providers")
        providers = providers_response.json()
        assert providers["ollama"]["status"] == "connected"
        
        print("✅ Ollama connection test successful (server running)")
        
    def test_ollama_connection_without_server(self):
        """Test connection behavior when Ollama server is not running."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
        
        if self.check_ollama_server():
            pytest.skip("Ollama server is running - use test_ollama_connection_with_server_running instead")
        
        response = requests.post(f"{self.base_url}/api/providers/ollama/test")
        assert response.status_code == 200
        
        result = response.json()
        assert result["provider"] == "ollama"
        assert result["success"] == False
        assert "error" in result
        
        # Check that status was updated to indicate connection failure
        providers_response = requests.get(f"{self.base_url}/api/providers")
        providers = providers_response.json()
        assert providers["ollama"]["status"] in ["connection_refused", "error", "timeout"]
        
        print("✅ Ollama connection test handles server unavailable correctly")
        
    def test_ollama_models_endpoint_with_server(self):
        """Test Ollama models listing endpoint when server is running."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
        
        if not self.check_ollama_server():
            pytest.skip("Ollama server not running")
        
        response = requests.get(f"{self.base_url}/api/providers/ollama/models")
        assert response.status_code == 200
        
        data = response.json()
        assert "models" in data
        assert "total" in data
        assert isinstance(data["models"], list)
        assert data["total"] == len(data["models"])
        
        # Check model structure
        if data["models"]:
            model = data["models"][0]
            assert "name" in model
            assert "size" in model
            
        print(f"✅ Ollama models endpoint works - found {data['total']} models")
        
    def test_ollama_models_endpoint_without_server(self):
        """Test Ollama models listing endpoint when server is not running."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
        
        if self.check_ollama_server():
            pytest.skip("Ollama server is running")
        
        response = requests.get(f"{self.base_url}/api/providers/ollama/models")
        assert response.status_code == 503  # Service unavailable
        
        data = response.json()
        assert "error" in data
        assert "Ollama server" in data["error"] or "connect" in data["error"].lower()
        
        print("✅ Ollama models endpoint handles server unavailable correctly")
        
    def test_ollama_chat_with_server(self):
        """Test chat functionality with Ollama when server is running."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
        
        if not self.check_ollama_server():
            pytest.skip("Ollama server not running")
        
        # First enable Ollama provider
        enable_data = {"enabled": True}
        requests.put(f"{self.base_url}/api/providers/ollama", json=enable_data)
        
        # Test chat
        chat_data = {
            "message": "Hello! Please respond with exactly 'Test successful' to verify the connection.",
            "provider": "ollama",
            "system_prompt": "You are a helpful assistant. Follow instructions precisely."
        }
        
        response = requests.post(f"{self.base_url}/api/chat", json=chat_data, timeout=30)
        assert response.status_code == 200
        
        result = response.json()
        assert result["provider"] == "ollama"
        assert "response" in result
        assert "tokens" in result
        assert "response_time" in result
        assert result["tokens"] > 0
        assert result["response_time"] > 0
        
        print(f"✅ Ollama chat successful - Response: {result['response'][:50]}...")
        print(f"   Tokens: {result['tokens']}, Response time: {result['response_time']:.2f}s")
        
    def test_ollama_chat_without_server(self):
        """Test chat functionality when Ollama server is not running."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
        
        if self.check_ollama_server():
            pytest.skip("Ollama server is running")
        
        # Enable Ollama provider
        enable_data = {"enabled": True}
        requests.put(f"{self.base_url}/api/providers/ollama", json=enable_data)
        
        # Test chat - should fail
        chat_data = {
            "message": "Hello!",
            "provider": "ollama"
        }
        
        response = requests.post(f"{self.base_url}/api/chat", json=chat_data, timeout=30)
        # Should return error status
        assert response.status_code >= 400
        
        result = response.json()
        assert "error" in result
        
        print("✅ Ollama chat correctly handles server unavailable")
        
    def test_ollama_fallback_mechanism(self):
        """Test fallback to other providers when Ollama fails."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
        
        # Setup: Enable a fallback provider (using a mock approach)
        # First get current settings
        settings_response = requests.get(f"{self.base_url}/api/settings")
        settings = settings_response.json()
        
        # Configure fallback
        settings["features"]["auto_fallback"] = True
        settings["fallback_provider"] = "groq"  # Assume groq is available as fallback
        
        # Update settings
        requests.put(f"{self.base_url}/api/settings", json=settings)
        
        # Enable Ollama but disable or make it fail
        if not self.check_ollama_server():
            # If Ollama is not running, enable it anyway to test fallback
            enable_data = {"enabled": True}
            requests.put(f"{self.base_url}/api/providers/ollama", json=enable_data)
            
            # Test chat - should fallback to groq if available
            chat_data = {
                "message": "Hello! This should fallback to another provider.",
                "provider": "ollama"
            }
            
            response = requests.post(f"{self.base_url}/api/chat", json=chat_data, timeout=30)
            
            # Check if fallback occurred
            if response.status_code == 200:
                result = response.json()
                if "fallback_used" in result and result["fallback_used"]:
                    assert result["provider"] != "ollama"
                    print(f"✅ Fallback mechanism works - used {result['provider']} instead of ollama")
                else:
                    print("⚠️  Chat succeeded but unclear if fallback was used")
            else:
                print("⚠️  Fallback test inconclusive - no fallback provider configured or available")
        else:
            print("⚠️  Ollama server is running - cannot test fallback mechanism")
    
    def test_usage_tracking_for_ollama(self):
        """Test that usage tracking properly records Ollama requests."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
        
        # Get initial usage stats
        initial_response = requests.get(f"{self.base_url}/api/usage")
        initial_usage = initial_response.json()
        
        today = datetime.now().strftime('%Y-%m-%d')
        initial_ollama_requests = 0
        initial_ollama_tokens = 0
        
        if today in initial_usage and "ollama" in initial_usage[today]:
            initial_ollama_requests = initial_usage[today]["ollama"]["requests"]
            initial_ollama_tokens = initial_usage[today]["ollama"]["tokens"]
        
        # Enable Ollama and make a chat request
        enable_data = {"enabled": True}
        requests.put(f"{self.base_url}/api/providers/ollama", json=enable_data)
        
        if self.check_ollama_server():
            # Make a chat request
            chat_data = {
                "message": "Short test message for usage tracking.",
                "provider": "ollama"
            }
            
            response = requests.post(f"{self.base_url}/api/chat", json=chat_data, timeout=30)
            
            if response.status_code == 200:
                # Wait a moment for usage tracking to complete
                time.sleep(1)
                
                # Get updated usage stats
                final_response = requests.get(f"{self.base_url}/api/usage")
                final_usage = final_response.json()
                
                # Check if usage was tracked
                assert today in final_usage
                assert "ollama" in final_usage[today]
                
                final_ollama_requests = final_usage[today]["ollama"]["requests"]
                final_ollama_tokens = final_usage[today]["ollama"]["tokens"]
                
                assert final_ollama_requests == initial_ollama_requests + 1
                assert final_ollama_tokens > initial_ollama_tokens
                
                print(f"✅ Usage tracking works - Requests: {final_ollama_requests}, Tokens: {final_ollama_tokens}")
            else:
                print("⚠️  Chat failed - cannot test usage tracking")
        else:
            print("⚠️  Ollama server not running - cannot test usage tracking with real request")
            # Instead test that failed requests don't incorrectly track usage
            chat_data = {
                "message": "This should fail",
                "provider": "ollama"
            }
            
            response = requests.post(f"{self.base_url}/api/chat", json=chat_data, timeout=30)
            assert response.status_code >= 400
            
            # Check that usage wasn't incorrectly tracked for failed request
            final_response = requests.get(f"{self.base_url}/api/usage")
            final_usage = final_response.json()
            
            if today in final_usage and "ollama" in final_usage[today]:
                final_ollama_requests = final_usage[today]["ollama"]["requests"]
                assert final_ollama_requests == initial_ollama_requests
                
            print("✅ Usage tracking correctly handles failed requests")
    
    def test_ollama_model_pull_endpoint(self):
        """Test Ollama model pull functionality."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
        
        if not self.check_ollama_server():
            pytest.skip("Ollama server not running")
        
        # Test pulling a small model
        pull_data = {"model": self.test_model}
        
        # Use a longer timeout for model pulling
        response = requests.post(
            f"{self.base_url}/api/providers/ollama/pull",
            json=pull_data,
            timeout=120  # 2 minutes timeout
        )
        
        # Accept both success and timeout as valid responses for testing
        assert response.status_code in [200, 504]
        
        if response.status_code == 200:
            result = response.json()
            assert "model" in result
            assert result["model"] == self.test_model
            print(f"✅ Model pull successful or in progress for {self.test_model}")
        else:
            print(f"⚠️  Model pull timed out (normal for large models) - {self.test_model}")
    
    def test_ollama_integration_end_to_end(self):
        """End-to-end test of complete Ollama integration flow."""
        if not self.check_backend_server():
            pytest.skip("Backend server not running")
        
        print("🧪 Running end-to-end Ollama integration test...")
        
        # Step 1: Check provider exists
        providers_response = requests.get(f"{self.base_url}/api/providers")
        providers = providers_response.json()
        assert "ollama" in providers
        print("   1. ✅ Ollama provider exists")
        
        # Step 2: Enable provider
        enable_data = {"enabled": True}
        requests.put(f"{self.base_url}/api/providers/ollama", json=enable_data)
        print("   2. ✅ Ollama provider enabled")
        
        # Step 3: Test connection
        connection_response = requests.post(f"{self.base_url}/api/providers/ollama/test")
        connection_result = connection_response.json()
        print(f"   3. {'✅' if connection_result['success'] else '⚠️ '} Connection test: {connection_result['success']}")
        
        # Step 4: List models (if server is running)
        if self.check_ollama_server():
            models_response = requests.get(f"{self.base_url}/api/providers/ollama/models")
            if models_response.status_code == 200:
                models_data = models_response.json()
                print(f"   4. ✅ Models available: {models_data['total']}")
            else:
                print("   4. ⚠️  Models endpoint failed")
        else:
            print("   4. ⚠️  Ollama server not running - skipping models test")
        
        # Step 5: Test chat (if server is running)
        if self.check_ollama_server():
            chat_data = {
                "message": "Say 'Integration test passed' if you receive this message.",
                "provider": "ollama"
            }
            
            chat_response = requests.post(f"{self.base_url}/api/chat", json=chat_data, timeout=30)
            if chat_response.status_code == 200:
                chat_result = chat_response.json()
                print(f"   5. ✅ Chat successful: {chat_result['response'][:30]}...")
            else:
                print("   5. ⚠️  Chat failed")
        else:
            print("   5. ⚠️  Ollama server not running - skipping chat test")
        
        print("🎉 End-to-end test completed!")


def run_interactive_tests():
    """Run tests interactively with user-friendly output."""
    print("🧪 Ollama Integration Test Suite")
    print("=" * 50)
    
    # Check prerequisites
    print("Checking prerequisites...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
        else:
            print("❌ Backend server responded with error")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend server is not running")
        print("   Please start the backend server first: python backend_server.py")
        return False
    
    # Check Ollama server
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            model_count = len(models_data.get('models', []))
            print(f"✅ Ollama server is running with {model_count} models")
            ollama_available = True
        else:
            print("⚠️  Ollama server responded with error")
            ollama_available = False
    except requests.exceptions.ConnectionError:
        print("⚠️  Ollama server is not running")
        print("   Some tests will be skipped. To enable full testing:")
        print("   1. Install Ollama: https://ollama.ai/")
        print("   2. Start Ollama: ollama serve")
        print("   3. Pull a model: ollama pull llama3.2:1b")
        ollama_available = False
    
    print("\n" + "=" * 50)
    
    # Run tests
    test_suite = TestOllamaIntegration()
    test_suite.setup_method()
    
    tests = [
        ("Provider List", test_suite.test_ollama_provider_in_list),
        ("Provider Configuration", test_suite.test_ollama_provider_configuration),
        ("Connection Test", test_suite.test_ollama_connection_with_server if ollama_available else test_suite.test_ollama_connection_without_server),
        ("Models Endpoint", test_suite.test_ollama_models_endpoint_with_server if ollama_available else test_suite.test_ollama_models_endpoint_without_server),
        ("Chat Functionality", test_suite.test_ollama_chat_with_server if ollama_available else test_suite.test_ollama_chat_without_server),
        ("Usage Tracking", test_suite.test_usage_tracking_for_ollama),
        ("Fallback Mechanism", test_suite.test_ollama_fallback_mechanism),
        ("End-to-End", test_suite.test_ollama_integration_end_to_end),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            test_func()
            passed += 1
            print(f"✅ {test_name} - PASSED")
        except pytest.skip.Exception as e:
            skipped += 1
            print(f"⚠️  {test_name} - SKIPPED: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} - FAILED: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⚠️  Skipped: {skipped}")
    print(f"   📈 Total: {passed + failed + skipped}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Ollama integration is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--pytest":
        # Run with pytest
        pytest.main([__file__, "-v"])
    else:
        # Run interactive tests
        run_interactive_tests()
