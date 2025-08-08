#!/usr/bin/env python3
"""
OpenRouter Models Listing Script
-------------------------------
This script lists available models from OpenRouter API and highlights free models
that can be used for testing without hitting rate limits.
"""

import os
import json
import requests
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
load_dotenv()

# List of known free/less rate-limited models on OpenRouter
FREE_MODELS = [
    "deepseek-ai/deepseek-coder-v2",
    "deepseek-ai/deepseek-coder-33b-instruct",
    "qwen/qwen3",
    "qwen/qwen3-coder",
    "01-ai/yi-34b-chat",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "mistralai/mistral-7b-instruct",
    "mistralai/mistral-small-1-1",
    "meta-llama/llama-3-8b-instruct",
    "deepseek-ai/deepseek-llm-67b-chat"
]

def list_openrouter_models(show_all=False, show_free_only=False, output_file=None):
    """
    List available models from OpenRouter API
    
    Args:
        show_all (bool): Whether to show all model details
        show_free_only (bool): Whether to show only free models
        output_file (str): Path to output file for saving models list
    """
    # Get API key from environment or config
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        # Try to load from config.json if not in environment
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                api_key = config.get('providers', {}).get('openrouter', {}).get('api_key')
        except Exception as e:
            print(f"Error loading API key from config.json: {e}")
    
    if not api_key:
        print("Error: OpenRouter API key not found. Please set OPENROUTER_API_KEY in .env or config.json")
        return
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        # Get models from OpenRouter API
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
        )
        
        # Check response
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            print(response.text)
            return
        
        # Parse response
        models_data = response.json()
        models = models_data.get("data", [])
        
        if not models:
            print("No models found")
            return
        
        # Filter models if requested
        if show_free_only:
            filtered_models = [m for m in models if m.get("id") in FREE_MODELS]
        else:
            filtered_models = models
        
        # Print models
        print(f"\n--- OpenRouter Models ({len(filtered_models)}) ---")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                if show_all:
                    json.dump(filtered_models, f, indent=2)
                else:
                    model_ids = [m.get("id") for m in filtered_models]
                    json.dump(model_ids, f, indent=2)
            print(f"Models saved to {output_file}")
        
        # Print models to console
        for i, model in enumerate(filtered_models):
            model_id = model.get("id")
            is_free = model_id in FREE_MODELS
            
            if show_all:
                print(f"\n{i+1}. {model_id} {'(FREE for testing)' if is_free else ''}")
                print(f"   Context: {model.get('context_length', 'N/A')}")
                print(f"   Created: {model.get('created', 'N/A')}")
                
                # Print pricing if available
                pricing = model.get("pricing")
                if pricing:
                    print(f"   Pricing: ${pricing.get('prompt', 0)} per 1M prompt tokens, ${pricing.get('completion', 0)} per 1M completion tokens")
            else:
                print(f"{i+1}. {model_id} {'(FREE for testing)' if is_free else ''}")
        
        print("\n--- Recommended Free Models for Testing ---")
        for model_id in FREE_MODELS:
            if any(m.get("id") == model_id for m in models):
                print(f"- {model_id}")
        
        return filtered_models
    
    except Exception as e:
        print(f"Error listing OpenRouter models: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List available models from OpenRouter API")
    parser.add_argument("--all", action="store_true", help="Show all model details")
    parser.add_argument("--free", action="store_true", help="Show only free models")
    parser.add_argument("--output", help="Path to output file for saving models list")
    
    args = parser.parse_args()
    
    list_openrouter_models(
        show_all=args.all,
        show_free_only=args.free,
        output_file=args.output
    )
