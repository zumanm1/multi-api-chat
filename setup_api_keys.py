#!/usr/bin/env python3
"""
API Key Setup Script for Multi-API Chat
This script helps set up API keys for various providers in config.json
"""

import json
import os
import sys
import getpass

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
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def update_provider(config, provider_id, api_key, model=None, base_url=None):
    """Update provider configuration"""
    if provider_id in config["providers"]:
        config["providers"][provider_id]["api_key"] = api_key
        config["providers"][provider_id]["enabled"] = True
        
        if model:
            config["providers"][provider_id]["model"] = model
        
        if base_url:
            config["providers"][provider_id]["base_url"] = base_url
            
        return True
    return False

def main():
    """Main function to set up API keys"""
    print("Multi-API Chat API Key Setup")
    print("===========================")
    
    # Load configuration
    config = load_config()
    if not config:
        print("Failed to load configuration. Exiting.")
        sys.exit(1)
    
    # Setup Groq
    print("\nSetting up Groq API")
    groq_key = getpass.getpass("Enter your Groq API key (press Enter to skip): ")
    if groq_key:
        # Fix the Groq base URL if needed
        groq_base_url = "https://api.groq.com/openai/v1"
        groq_model = "llama-3.1-8b-instant"
        
        if update_provider(config, "groq", groq_key, groq_model, groq_base_url):
            print("✅ Groq API key configured")
    
    # Setup OpenRouter
    print("\nSetting up OpenRouter API")
    openrouter_key = getpass.getpass("Enter your OpenRouter API key (press Enter to skip): ")
    if openrouter_key:
        # Fix the OpenRouter base URL if needed
        openrouter_base_url = "https://openrouter.ai/api/v1"
        openrouter_model = "openai/gpt-3.5-turbo"
        
        if update_provider(config, "openrouter", openrouter_key, openrouter_model, openrouter_base_url):
            print("✅ OpenRouter API key configured")
    
    # Setup OpenAI (optional)
    print("\nSetting up OpenAI API")
    openai_key = getpass.getpass("Enter your OpenAI API key (press Enter to skip): ")
    if openai_key:
        if update_provider(config, "openai", openai_key):
            print("✅ OpenAI API key configured")
    
    # Save updated config
    if save_config(config):
        print("\nAPI keys have been configured successfully!")
        print("You can now run test_api_cli.py to test the providers")
    
if __name__ == "__main__":
    main()
