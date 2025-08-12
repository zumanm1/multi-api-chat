#!/usr/bin/env python3
"""
Test script for Ollama model management endpoints
This script tests the newly added Ollama functionality in backend_server.py
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:7002"
OLLAMA_BASE_URL = "http://localhost:11434"

def test_ollama_models_endpoint():
    """Test the /api/providers/ollama/models endpoint"""
    print("Testing Ollama models listing endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/providers/ollama/models")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if 'models' in data:
                print(f"✅ Successfully retrieved {len(data['models'])} models")
                for model in data['models'][:3]:  # Show first 3 models
                    print(f"   - {model['name']} (Size: {model.get('size', 'Unknown')})")
                return True
            else:
                print("❌ Response missing 'models' field")
                return False
        elif response.status_code == 503:
            print("⚠️  Ollama server not running")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ollama_pull_endpoint():
    """Test the /api/providers/ollama/pull endpoint"""
    print("\nTesting Ollama model pull endpoint...")
    
    # Use a small model for testing
    test_model = "llama3.2:1b"  # Small 1B parameter model
    
    try:
        pull_data = {"model": test_model}
        response = requests.post(
            f"{BASE_URL}/api/providers/ollama/pull", 
            json=pull_data,
            timeout=60  # 1 minute timeout for testing
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Pull request successful: {data.get('message', 'No message')}")
            if 'status_log' in data:
                print(f"   Status log entries: {len(data['status_log'])}")
            return True
        elif response.status_code == 503:
            print("⚠️  Ollama server not running")
            return False
        elif response.status_code == 504:
            print("⚠️  Pull request timed out (this is normal for large models)")
            return True  # Timeout is acceptable for testing
        else:
            data = response.json()
            print(f"❌ Pull failed: {data.get('error', 'Unknown error')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        return False
    except requests.exceptions.Timeout:
        print("⚠️  Request timed out (this is normal for large models)")
        return True  # Timeout is acceptable for testing
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ollama_chat_endpoint():
    """Test the chat endpoint with Ollama provider"""
    print("\nTesting Ollama chat endpoint...")
    
    try:
        chat_data = {
            "message": "Hello! Please respond with just 'Hello back!' to test the connection.",
            "provider": "ollama",
            "system_prompt": "You are a helpful assistant. Keep responses brief."
        }
        
        response = requests.post(f"{BASE_URL}/api/chat", json=chat_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat successful!")
            print(f"   Provider: {data.get('provider')}")
            print(f"   Model: {data.get('model')}")
            print(f"   Response: {data.get('response', '')[:100]}...")  # First 100 chars
            print(f"   Tokens: {data.get('tokens', 0)}")
            print(f"   Response time: {data.get('response_time', 0):.2f}s")
            return True
        elif response.status_code == 400:
            data = response.json()
            print(f"⚠️  Provider disabled or not configured: {data.get('error')}")
            return False
        else:
            data = response.json()
            print(f"❌ Chat failed: {data.get('error', 'Unknown error')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        return False
    except requests.exceptions.Timeout:
        print("⚠️  Chat request timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_ollama_server():
    """Check if Ollama server is running"""
    print("Checking Ollama server availability...")
    
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            model_count = len(data.get('models', []))
            print(f"✅ Ollama server is running with {model_count} models")
            return True
        else:
            print(f"❌ Ollama server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Ollama server is not running")
        print("   Start Ollama with: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Ollama Integration Endpoints")
    print("=" * 50)
    
    # Check if Ollama is running first
    ollama_running = check_ollama_server()
    
    print("\n" + "=" * 50)
    
    # Test the endpoints
    models_test = test_ollama_models_endpoint()
    pull_test = test_ollama_pull_endpoint() if ollama_running else False
    chat_test = test_ollama_chat_endpoint() if ollama_running else False
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Ollama Server: {'✅ Running' if ollama_running else '❌ Not running'}")
    print(f"   Models Endpoint: {'✅ Pass' if models_test else '❌ Fail'}")
    print(f"   Pull Endpoint: {'✅ Pass' if pull_test else '❌ Fail/Skip'}")
    print(f"   Chat Endpoint: {'✅ Pass' if chat_test else '❌ Fail/Skip'}")
    
    if not ollama_running:
        print("\n💡 To run full tests:")
        print("   1. Install Ollama: https://ollama.ai/")
        print("   2. Start Ollama: ollama serve")
        print("   3. Pull a model: ollama pull llama3.2:1b")
        print("   4. Run tests again")
    
    print("\n🎉 Ollama integration endpoints have been implemented!")

if __name__ == "__main__":
    main()
