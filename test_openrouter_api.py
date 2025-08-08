#!/usr/bin/env python3
"""
OpenRouter API Test Script
-------------------------
This script demonstrates how to use OpenRouter with the OpenAI client library.
It includes proper header configuration for site attribution and uses environment
variables for API keys.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import argparse

# Load environment variables from .env file
load_dotenv()

def test_openrouter_completion(model=None, prompt=None, site_url=None, site_name=None):
    """
    Test OpenRouter API using the OpenAI client library
    
    Args:
        model (str): Model to use for completion (defaults to a free model)
        prompt (str): Prompt to send to the model
        site_url (str): Your site URL for attribution
        site_name (str): Your site name for attribution
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
    
    # Set default values if not provided
    if not model:
        # Default to a free model to avoid rate limits
        model = "deepseek-ai/deepseek-coder-v2"
    
    if not prompt:
        prompt = "What are the best practices for error handling in Python?"
    
    # Set up extra headers for attribution
    extra_headers = {}
    if site_url:
        extra_headers["HTTP-Referer"] = site_url
    if site_name:
        extra_headers["X-Title"] = site_name
    
    # Initialize OpenAI client with OpenRouter base URL
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    try:
        # Create completion
        completion = client.chat.completions.create(
            extra_headers=extra_headers,
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Print response
        print("\n--- OpenRouter API Response ---")
        print(f"Model: {model}")
        print(f"Response: {completion.choices[0].message.content}")
        print(f"Finish reason: {completion.choices[0].finish_reason}")
        
        # Print usage information if available
        if hasattr(completion, 'usage'):
            print("\n--- Token Usage ---")
            print(f"Prompt tokens: {completion.usage.prompt_tokens}")
            print(f"Completion tokens: {completion.usage.completion_tokens}")
            print(f"Total tokens: {completion.usage.total_tokens}")
        
        return completion
    
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test OpenRouter API with OpenAI client")
    parser.add_argument("--model", help="Model to use (default: deepseek-ai/deepseek-coder-v2)")
    parser.add_argument("--prompt", help="Prompt to send to the model")
    parser.add_argument("--site-url", help="Your site URL for attribution")
    parser.add_argument("--site-name", help="Your site name for attribution")
    
    args = parser.parse_args()
    
    test_openrouter_completion(
        model=args.model,
        prompt=args.prompt,
        site_url=args.site_url,
        site_name=args.site_name
    )
