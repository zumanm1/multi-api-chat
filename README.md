# Multi-API Chat Application

A unified chat interface enabling seamless interaction with multiple AI providers through OpenAI-compatible APIs, optimizing performance, cost, and reliability.

## 🎯 Features

- **Multi-Provider Support**: Chat with OpenAI, Groq, Cerebras, SambaNova, Anthropic, OpenRouter, and Ollama (local)
- **Local-First**: No intermediary data transmission - all data stays on your machine
- **Secure Storage**: AES-256 encrypted API key storage
- **Auto-Fallback**: Automatic switching to backup providers on failure
- **Compare Mode**: See responses from multiple providers side-by-side
- **Usage Analytics**: Track API usage and costs locally
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## 🚀 Quick Start

### 1. Install Dependencies

Use Python 3.11 (preferred) in a virtual environment:

```bash
# Create and activate a Python 3.11 virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Optional: Install AI Agent Features (requires additional dependencies)
# These dependencies are optional and the application will work without them
pip install -r requirements-ai-agents.txt
```

### 2. Configure API Keys

The application stores provider configurations in `config.json`. You can:
- Edit `config.json` directly (not recommended for security)
- Use the web interface to configure providers after starting the application

### 3. Start Backend Server

To start the backend server (on port 8002), run:
```bash
python backend_server.py
```

### 4. Start Frontend Server

In a new terminal:
```bash
bash start_frontend.sh # (serves frontend on port 8001)
# For E2E test server use: python3 -m http.server 8180
```

### 5. Access Application

Open your browser to `http://localhost:8001` to use the application.

## 🤖 AI Agent Features (Optional)

The application includes optional AI agent capabilities powered by CrewAI and Ollama.

### AI Features Overview
- **Intelligent Chat Assistance**: Enhanced conversational AI with specialized agents
- **Analytics and Insights**: Automated analysis of usage patterns and performance
- **Device Management**: AI-powered monitoring and management of connected devices
- **Workflow Automation**: Smart automation of repetitive tasks
- **Local AI with Ollama**: Privacy-focused local AI processing

### AI Dependencies Installation

AI features require additional dependencies that are **completely optional**:

```bash
# Install AI agent dependencies (optional)
pip install -r requirements-ai-agents.txt
```

**Note**: The application will work perfectly without AI features. All AI-related functionality gracefully falls back to standard operation if dependencies are not installed.

### Environment Variables for AI Features

Control AI functionality with environment variables:

```bash
# Enable/disable AI agents (default: true if dependencies are installed)
ENABLE_AI_AGENTS=true

# AI debug mode (default: false)
AI_AGENTS_DEBUG=false

# Default LLM for AI agents (default: gpt-4)
AI_AGENTS_DEFAULT_LLM=gpt-4

# Maximum concurrent AI tasks (default: 3)
AI_AGENTS_MAX_CONCURRENT=3
```

## ⚙️ Configuration

### Provider Configuration

All providers are configured through the web interface. The configuration is stored locally in `config.json`:

```json
{
  "providers": {
    "openai": {
      "name": "OpenAI",
      "enabled": false,
      "api_key": "",
      "model": "gpt-4o",
      "base_url": "https://api.openai.com/v1",
      "status": "disconnected",
      "last_checked": ""
    }
    // ... other providers
  },
  "settings": {
    "default_provider": "groq",
    "fallback_provider": null,
    "temperature": 0.7,
    "max_tokens": 1000,
    "system_prompt": "You are a helpful AI assistant.",
    "features": {
      "auto_fallback": true,
      "speed_optimization": false,
      "cost_optimization": false,
      "multi_provider_compare": false,
      "usage_analytics": true
    }
  }
}
```

### Environment Variables

You can configure your API keys and AI features in a `.env` file by copying `.env.template`:

```bash
cp .env.template .env
# Edit .env with your actual API keys (plain ASCII, no quotes)
# Example:
# OPENAI_API_KEY=sk-...
# OPENROUTER_API_KEY=sk-or-...

# AI Agent Configuration (optional)
# ENABLE_AI_AGENTS=true
# AI_AGENTS_DEBUG=false
# AI_AGENTS_DEFAULT_LLM=gpt-4
# AI_AGENTS_MAX_CONCURRENT=3
```

## 📊 Usage Analytics

Usage data is stored locally in `usage.json` with the following structure:

```json
{
  "2025-08-07": {
    "groq": {
      "requests": 5,
      "tokens": 2450,
      "total_response_time": 4.2
    }
  }
}
```

Analytics can be disabled in the settings interface.

## 🧪 Testing Providers

You can test provider connections through the web interface:
1. Enter your API key for a provider
2. Click the "Test" button next to the provider
3. The status indicator will update to show if the connection was successful

You can also test all enabled providers at once using the "Test All Providers" button.

## 🔒 Security

- API keys are stored locally in `config.json`
- All communication between frontend and backend happens over localhost (no network transmission)
- All production communications should use HTTPS
- Keys are never transmitted to external servers

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/providers` | List all providers |
| PUT | `/api/providers/{id}` | Update provider config |
| POST | `/api/providers/{id}/test` | Test connection |
| POST | `/api/providers/test-all` | Test all providers |
| GET/PUT | `/api/settings` | Manage settings |
| POST | `/api/chat` | Send message |
| POST | `/api/chat/compare` | Compare providers |
| GET | `/api/usage` | Usage statistics |
| GET | `/api/health` | Health check |

## 🐳 Docker Deployment

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["python", "backend_server.py"]
```

### Frontend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY index.html .

EXPOSE 8001

CMD ["python", "-m", "http.server", "8001"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8002:8002"
    volumes:
      - ./config.json:/app/config.json
      - ./usage.json:/app/usage.json
  frontend:
    build: .
    ports:
      - "8001:8001"
    depends_on:
      - backend
```

## 📈 Performance Targets

- Response time: <3s average
- Provider connection success: >95%
- Test coverage: >90% for critical paths

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Troubleshooting

### Backend won't start
- Check Python version (3.8+)
- Ensure all dependencies are installed
- Check if port 8002 is already in use

### Frontend connection fails
- Ensure backend is running on port 8002
- Check browser console for errors

### API key errors
- Verify keys are valid and correctly formatted
- Check provider dashboard for rate limits or account issues

### Provider tests fail
- Check network connectivity
- Verify API key format and permissions
- Check provider status pages for service interruptions

### Ollama (Local AI) setup
- **Quick setup**: Run `bash setup_ollama.sh` for automatic installation and configuration
- **Manual setup**: For detailed instructions, see [`OLLAMA_SETUP_GUIDE.md`](OLLAMA_SETUP_GUIDE.md)
- **Status check**: Run `bash setup_ollama.sh --status` to check current setup

Quick manual steps:
- Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
- Start service: `ollama serve`
- Install a model: `ollama pull llama3.2:1b`
- Enable in application settings with base URL: `http://localhost:11434/v1`

## 📚 Documentation

### Setup Guides
- **[Ollama Setup Guide](OLLAMA_SETUP_GUIDE.md)**: Complete guide for setting up local AI with Ollama
- **[CrewAI Setup Guide](AI_CREWAI_SETUP_GUIDE.md)**: Configure CrewAI with different LLM providers (OpenAI, Ollama, Groq, etc.)
- **[AI Agents with Ollama Guide](AI_AGENTS_OLLAMA_GUIDE.md)**: Complete integration guide for using Ollama with AI agents
- **[OpenRouter Setup Guide](README_OPENROUTER.md)**: Configure OpenRouter for access to multiple models

### Technical Documentation
- **[Ollama Implementation Details](OLLAMA_IMPLEMENTATION.md)**: Technical details of Ollama integration
- **[Ollama Integration Features](OLLAMA_INTEGRATION.md)**: API endpoints and model management
- **[Testing Summary](OLLAMA_TESTING_SUMMARY.md)**: Test coverage and validation results

### Other Features
- **[Accessibility Features](ACCESSIBILITY_FEATURES.md)**: Accessibility and usability enhancements
- **[Responsive Testing Report](RESPONSIVE_TESTING_REPORT.md)**: Mobile and responsive design validation
- **[Operations Summary](OPERATIONS_SUMMARY.md)**: Deployment and operational considerations
