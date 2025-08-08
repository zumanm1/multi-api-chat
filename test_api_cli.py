#!/usr/bin/env python3
"""
CLI Test Script for Multi-API Chat Providers
This script tests API connections to various LLM providers using real API keys
"""

import json
import os
import sys
import requests
import time
from datetime import datetime

# Load config
CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from config.json"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def save_config(config):
    """Save configuration back to config.json"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Config saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving config: {e}")

def test_openai(api_key, model="gpt-3.5-turbo", base_url="https://api.openai.com/v1"):
    """Test OpenAI API connection"""
    print(f"\nTesting OpenAI with model: {model}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello world"}],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ OpenAI API test successful!")
            print(f"Response: {content}")
            return True, "connected", content
        else:
            print(f"❌ OpenAI API test failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False, "error", response.text
    except Exception as e:
        print(f"❌ OpenAI API test failed with exception: {e}")
        return False, "error", str(e)

def test_groq(api_key, model="llama-3.1-8b-instant", base_url="https://api.groq.com/openai/v1"):
    """Test Groq API connection"""
    print(f"\nTesting Groq with model: {model}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello world"}],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ Groq API test successful!")
            print(f"Response: {content}")
            return True, "connected", content
        else:
            print(f"❌ Groq API test failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False, "error", response.text
    except Exception as e:
        print(f"❌ Groq API test failed with exception: {e}")
        return False, "error", str(e)

def test_openrouter(api_key, model="openai/gpt-3.5-turbo", base_url="https://openrouter.ai/api/v1"):
    """Test OpenRouter API connection"""
    print(f"\nTesting OpenRouter with model: {model}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://multi-api-chat.local", # Required by OpenRouter
        "X-Title": "Multi-API Chat Test"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello world"}],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ OpenRouter API test successful!")
            print(f"Response: {content}")
            return True, "connected", content
        else:
            print(f"❌ OpenRouter API test failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False, "error", response.text
    except Exception as e:
        print(f"❌ OpenRouter API test failed with exception: {e}")
        return False, "error", str(e)

def update_provider_status(config, provider_id, status, response=None):
    """Update provider status in config"""
    if provider_id in config["providers"]:
        config["providers"][provider_id]["status"] = status
        config["providers"][provider_id]["last_checked"] = datetime.now().isoformat()
        if response:
            config["providers"][provider_id]["last_response"] = response[:200]  # Truncate long responses
    return config

def main():
    """Main function to test all providers"""
    print("Multi-API Chat Provider CLI Test")
    print("===============================")
    
    # Load configuration
    config = load_config()
    if not config:
        print("Failed to load configuration. Exiting.")
        sys.exit(1)
    
    # Check if API keys are provided
    print("\nChecking API keys in config...")
    
    # Test OpenAI if API key exists
    if "openai" in config["providers"] and config["providers"]["openai"]["api_key"]:
        success, status, response = test_openai(
            config["providers"]["openai"]["api_key"],
            config["providers"]["openai"]["model"],
            config["providers"]["openai"]["base_url"]
        )
        config = update_provider_status(config, "openai", status, response)
    else:
        print("\nSkipping OpenAI test - no API key found")
    
    # Test Groq if API key exists
    if "groq" in config["providers"] and config["providers"]["groq"]["api_key"]:
        success, status, response = test_groq(
            config["providers"]["groq"]["api_key"],
            config["providers"]["groq"]["model"],
            config["providers"]["groq"]["base_url"]
        )
        config = update_provider_status(config, "groq", status, response)
    else:
        print("\nSkipping Groq test - no API key found")
    
    # Test OpenRouter if API key exists
    if "openrouter" in config["providers"] and config["providers"]["openrouter"]["api_key"]:
        success, status, response = test_openrouter(
            config["providers"]["openrouter"]["api_key"],
            config["providers"]["openrouter"]["model"],
            config["providers"]["openrouter"]["base_url"]
        )
        config = update_provider_status(config, "openrouter", status, response)
    else:
        print("\nSkipping OpenRouter test - no API key found")
    
    # Save updated config
    save_config(config)
    
    print("\nAPI testing complete!")

if __name__ == "__main__":
    main()
