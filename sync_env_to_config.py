#!/usr/bin/env python3
"""
Sync API Keys from .env to config.json
This script reads API keys from .env and updates config.json
"""

import json
import os
import sys
import re
from datetime import datetime

# File paths
ENV_FILE = ".env"
CONFIG_FILE = "config.json"

def load_env_file():
    """Load variables from .env file"""
    env_vars = {}
    try:
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
        return env_vars
    except Exception as e:
        print(f"Error loading .env file: {e}")
        return {}

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

def update_provider_config(config, env_vars):
    """Update provider configurations with API keys from env vars"""
    updated = False
    
    # Map of environment variable names to provider IDs and their base URLs
    provider_map = {
        "OPENAI_API_KEY": {
            "provider_id": "openai",
            "base_url": "https://api.openai.com/v1"
        },
        "GROQ_API_KEY": {
            "provider_id": "groq",
            "base_url": "https://api.groq.com/openai/v1"
        },
        "OPENROUTER_API_KEY": {
            "provider_id": "openrouter",
            "base_url": "https://openrouter.ai/api/v1"
        },
        "ANTHROPIC_API_KEY": {
            "provider_id": "anthropic",
            "base_url": "https://api.anthropic.com/v1/openai"
        },
        "CEREBRAS_API_KEY": {
            "provider_id": "cerebras",
            "base_url": "https://inference-docs.cerebras.ai/api"
        }
    }
    
    # Update provider configs with API keys from env vars
    for env_var, provider_info in provider_map.items():
        if env_var in env_vars and env_vars[env_var]:
            provider_id = provider_info["provider_id"]
            
            # Check if provider exists in config
            if provider_id in config["providers"]:
                # Update API key
                if config["providers"][provider_id]["api_key"] != env_vars[env_var]:
                    config["providers"][provider_id]["api_key"] = env_vars[env_var]
                    config["providers"][provider_id]["enabled"] = True
                    config["providers"][provider_id]["status"] = "unknown"
                    config["providers"][provider_id]["last_checked"] = datetime.now().isoformat()
                    
                    # Update base URL if needed
                    if "base_url" in provider_info:
                        config["providers"][provider_id]["base_url"] = provider_info["base_url"]
                    
                    print(f"✅ Updated {provider_id} API key from {env_var}")
                    updated = True
                else:
                    print(f"ℹ️ {provider_id} API key unchanged")
            else:
                print(f"⚠️ Provider {provider_id} not found in config.json")
    
    return config, updated

def main():
    """Main function to sync .env to config.json"""
    print("Syncing API Keys from .env to config.json")
    print("========================================")
    
    # Check if .env file exists
    if not os.path.exists(ENV_FILE):
        print(f"❌ {ENV_FILE} file not found")
        return False
    
    # Load .env variables
    env_vars = load_env_file()
    if not env_vars:
        print("❌ No variables found in .env file")
        return False
    
    # Load config
    config = load_config()
    if not config:
        print("❌ Failed to load config.json")
        return False
    
    # Update provider configs
    config, updated = update_provider_config(config, env_vars)
    
    # Save config if updated
    if updated:
        if save_config(config):
            print("\n✅ Successfully synced API keys from .env to config.json")
            return True
        else:
            print("\n❌ Failed to save updated config")
            return False
    else:
        print("\nℹ️ No changes needed in config.json")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
