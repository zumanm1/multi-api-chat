# OpenRouter API Testing Tools

This directory contains two scripts for testing and exploring the OpenRouter API:

1. `test_openrouter_api.py` - Test the OpenRouter API using the OpenAI client library
2. `list_openrouter_models.py` - List available models from OpenRouter, focusing on free models for testing

## Prerequisites

- Python 3.6+
- OpenAI Python library (`pip install openai`)
- Requests library (`pip install requests`)
- Python-dotenv (`pip install python-dotenv`)
- Valid OpenRouter API key (set in `.env` or `config.json`)

## Setting Up Your API Key

To use these scripts, you need a valid OpenRouter API key. You can set it in one of two ways:

1. In your `.env` file:
   ```
   OPENROUTER_API_KEY="your_api_key_here"
   ```

2. In `config.json` under the `providers.openrouter.api_key` field:
   ```json
   {
     "providers": {
       "openrouter": {
         "api_key": "your_api_key_here",
         ...
       }
     }
   }
   ```

## Using the OpenRouter API Test Script

This script demonstrates how to use the OpenRouter API with the OpenAI client library, including proper header configuration for site attribution.

```bash
python3 test_openrouter_api.py [options]
```

### Options:

- `--model MODEL`: Model to use (default: deepseek-ai/deepseek-coder-v2)
- `--prompt PROMPT`: Prompt to send to the model
- `--site-url SITE_URL`: Your site URL for attribution
- `--site-name SITE_NAME`: Your site name for attribution

### Example:

```bash
python3 test_openrouter_api.py --model "meta-llama/llama-3-8b-instruct" --prompt "Explain how to implement error handling in Python" --site-url "https://example.com" --site-name "My App"
```

## Using the OpenRouter Models Listing Script

This script lists available models from the OpenRouter API and highlights free models that can be used for testing without hitting rate limits.

```bash
python3 list_openrouter_models.py [options]
```

### Options:

- `--all`: Show all model details (context length, pricing, etc.)
- `--free`: Show only free models
- `--output OUTPUT`: Path to output file for saving models list

### Example:

```bash
python3 list_openrouter_models.py --all --free --output free_models.json
```

## Recommended Free Models for Testing

Based on our testing, the following models are recommended for free/low-rate-limited testing:

1. `meta-llama/llama-3-8b-instruct`
2. `mistralai/mistral-7b-instruct`
3. `openai/gpt-oss-120b`
4. `openai/gpt-oss-20b`
5. `qwen/qwen3-coder`
6. `deepseek-ai/deepseek-coder-v2`
7. `deepseek-ai/deepseek-coder-33b-instruct`
8. `01-ai/yi-34b-chat`
9. `mistralai/mistral-small-1-1`
10. `mistralai/mistral-7b-instruct-v0.1`

## Important Notes

1. When using the OpenRouter API, it's recommended to include the `HTTP-Referer` and `X-Title` headers for proper attribution.

2. The OpenRouter API uses the same interface as the OpenAI API, so you can use the OpenAI client library with the OpenRouter base URL.

3. The free models may have usage limitations, so it's best to use them for testing purposes only.

4. If you encounter a 401 error, make sure your API key is valid and properly set in `.env` or `config.json`.

## Integration with Multi-API Chat

These scripts are designed to work with the Multi-API Chat application, which supports multiple LLM providers including OpenRouter. The application uses the same configuration from `config.json` for API keys and model selection.
