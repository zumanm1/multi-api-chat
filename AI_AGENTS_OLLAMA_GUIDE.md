# AI Agents with Ollama - Complete Integration Guide

This guide explains how to use Ollama with the AI agent features in the Multi-API Chat platform, providing local, privacy-focused AI processing.

## 🎯 Overview

Ollama integration with AI agents provides:
- **Complete Privacy**: All AI processing happens locally on your machine
- **Cost-Effective**: No API usage fees after initial setup
- **Offline Capability**: Works without internet connection for AI features
- **Model Flexibility**: Choose from various open-source models based on your hardware
- **Seamless Integration**: Works with existing CrewAI agent architecture

## 🔧 Prerequisites

### System Requirements

**Minimum Requirements:**
- 8GB RAM (for smaller models like llama3.2:1b)
- 4GB free disk space
- CPU with modern instruction set (AVX support recommended)

**Recommended Requirements:**
- 16GB+ RAM (for larger models like llama3.2:7b)
- 8GB+ free disk space
- NVIDIA GPU with 8GB+ VRAM (for faster processing)
- SSD storage for better model loading performance

### Software Dependencies

1. **Ollama Installation**:
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **AI Agent Dependencies**:
   ```bash
   # Install AI agent requirements
   pip install -r requirements-ai-agents.txt
   ```

## 🚀 Quick Start

### 1. Setup Ollama

```bash
# Start Ollama service
ollama serve

# Pull a recommended model for AI agents
ollama pull llama3.2:3b  # Good balance of performance and resource usage
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.template .env

# Add to .env:
ENABLE_AI_AGENTS=true
AI_AGENTS_DEFAULT_LLM=ollama/llama3.2:3b
OLLAMA_API_BASE=http://localhost:11434/v1
```

### 3. Verify Setup

```bash
# Test Ollama is working
curl http://localhost:11434/api/version

# Start the application
python backend_server.py
```

## 🤖 Model Selection Guide

### Lightweight Models (4-8GB RAM)

**llama3.2:1b** (1.3GB)
- Best for: Basic chat, simple tasks
- RAM: 4GB minimum
- Speed: Very fast
- Quality: Good for simple interactions

```bash
ollama pull llama3.2:1b
# Configure in .env: AI_AGENTS_DEFAULT_LLM=ollama/llama3.2:1b
```

### Balanced Models (8-16GB RAM)

**llama3.2:3b** (2GB) - **Recommended**
- Best for: Most AI agent tasks, good balance
- RAM: 8GB recommended  
- Speed: Fast
- Quality: Very good for agent tasks

```bash
ollama pull llama3.2:3b
# Configure in .env: AI_AGENTS_DEFAULT_LLM=ollama/llama3.2:3b
```

### High-Quality Models (16GB+ RAM)

**llama3.2:7b** (4.1GB)
- Best for: Complex reasoning, detailed analysis
- RAM: 16GB recommended
- Speed: Moderate
- Quality: Excellent

```bash
ollama pull llama3.2:7b
# Configure in .env: AI_AGENTS_DEFAULT_LLM=ollama/llama3.2:7b
```

**llama3.1:8b** (4.7GB)
- Best for: Advanced reasoning, creative tasks
- RAM: 16GB+ recommended
- Speed: Moderate
- Quality: Excellent

```bash
ollama pull llama3.1:8b  
# Configure in .env: AI_AGENTS_DEFAULT_LLM=ollama/llama3.1:8b
```

### Specialized Models

**codellama:7b** (3.8GB) - For Code Analysis
```bash
ollama pull codellama:7b
# Good for device management and automation agents
```

**mistral:7b** (4.1GB) - For Analytical Tasks
```bash
ollama pull mistral:7b
# Good for analytics and data processing agents
```

## 🛠️ Configuration Examples

### Basic Ollama Configuration

```python
# ai_agents/configs/ollama_config.py
from langchain_openai import ChatOpenAI

def get_ollama_llm(model="llama3.2:3b"):
    """Configure Ollama LLM for AI agents"""
    return ChatOpenAI(
        model=model,
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # Ollama doesn't require real API key
        temperature=0.7,
        max_tokens=1000,
        request_timeout=60  # Longer timeout for local processing
    )
```

### Agent-Specific Configuration

```python
# Different models for different agent types
from ai_agents.configs.ollama_config import get_ollama_llm

# Fast responses for chat agent
chat_llm = get_ollama_llm("llama3.2:1b")  # Faster model

# Detailed analysis for analytics agent
analytics_llm = get_ollama_llm("llama3.2:7b")  # Better reasoning

# Code analysis for device management
device_llm = get_ollama_llm("codellama:7b")  # Code-focused model
```

### Performance Optimization

```python
# Optimized Ollama configuration for AI agents
optimized_config = {
    "model": "llama3.2:3b",
    "base_url": "http://localhost:11434/v1", 
    "api_key": "ollama",
    "temperature": 0.7,
    "max_tokens": 800,          # Reduced for faster processing
    "top_p": 0.9,
    "frequency_penalty": 0.1,
    "presence_penalty": 0.1,
    "request_timeout": 45,      # Reasonable timeout
    "max_retries": 2            # Retry on failure
}

ollama_llm = ChatOpenAI(**optimized_config)
```

## 🎛️ Agent Configuration with Ollama

### Master Agent with Ollama

```python
from crewai import Agent
from ai_agents.configs.ollama_config import get_ollama_llm

master_agent = Agent(
    role="Master AI Agent",
    goal="Coordinate all AI agents using local processing",
    backstory="You are the master coordinator for local AI agents",
    llm=get_ollama_llm("llama3.2:3b"),
    memory=True,
    verbose=True,
    max_execution_time=120,  # Allow more time for local processing
    allow_delegation=True
)
```

### Analytics Agent with Specialized Model

```python
analytics_agent = Agent(
    role="Analytics Agent",
    goal="Analyze data using local AI model",
    backstory="You are a data analyst using privacy-focused local AI",
    llm=get_ollama_llm("llama3.2:7b"),  # Better for analysis
    memory=True,
    tools=["data_analysis_tool", "chart_generator_tool"],
    max_execution_time=180  # More time for complex analysis
)
```

### Device Management with Code-Focused Model

```python
device_agent = Agent(
    role="Device Management Agent", 
    goal="Manage devices using code-aware AI",
    backstory="You specialize in device management and configuration",
    llm=get_ollama_llm("codellama:7b"),  # Code-focused model
    memory=True,
    tools=["device_scanner_tool", "config_manager_tool"]
)
```

## 🔧 Advanced Configuration

### Dynamic Model Selection

```python
import os

def get_dynamic_ollama_llm(agent_type="general"):
    """Select Ollama model based on agent type and available resources"""
    
    # Check available memory (simplified)
    import psutil
    available_memory = psutil.virtual_memory().available / (1024**3)  # GB
    
    if agent_type == "chat" or available_memory < 8:
        model = "llama3.2:1b"  # Lightweight
    elif agent_type == "analytics" and available_memory >= 16:
        model = "llama3.2:7b"  # High quality for analysis
    elif agent_type == "device":
        model = "codellama:7b"  # Code-focused
    else:
        model = "llama3.2:3b"  # Balanced default
    
    return get_ollama_llm(model)
```

### Multi-Model Agent Crew

```python
from crewai import Crew

# Different agents with different models
chat_agent = Agent(
    role="Chat Assistant",
    llm=get_ollama_llm("llama3.2:1b")  # Fast responses
)

analytics_agent = Agent(
    role="Data Analyst", 
    llm=get_ollama_llm("llama3.2:7b")  # Detailed analysis
)

automation_agent = Agent(
    role="Automation Specialist",
    llm=get_ollama_llm("codellama:7b")  # Code generation
)

# Create crew with mixed models
crew = Crew(
    agents=[chat_agent, analytics_agent, automation_agent],
    process="sequential",
    verbose=True
)
```

## 📊 Performance Monitoring

### Resource Usage Monitoring

```python
import psutil
import time

def monitor_ollama_performance():
    """Monitor Ollama resource usage"""
    print(f"CPU Usage: {psutil.cpu_percent()}%")
    print(f"Memory Usage: {psutil.virtual_memory().percent}%")
    print(f"Available Memory: {psutil.virtual_memory().available / (1024**3):.1f} GB")

def time_agent_execution(agent, task):
    """Time agent execution with Ollama"""
    start_time = time.time()
    result = agent.execute(task)
    execution_time = time.time() - start_time
    
    print(f"Agent execution time: {execution_time:.2f} seconds")
    return result, execution_time
```

### Model Performance Comparison

```python
def benchmark_models():
    """Compare different Ollama models for agent tasks"""
    models = ["llama3.2:1b", "llama3.2:3b", "llama3.2:7b"]
    test_prompt = "Analyze this data and provide insights"
    
    for model in models:
        llm = get_ollama_llm(model)
        
        start_time = time.time()
        try:
            response = llm.invoke(test_prompt)
            execution_time = time.time() - start_time
            print(f"{model}: {execution_time:.2f}s - {len(response.content)} chars")
        except Exception as e:
            print(f"{model}: Error - {e}")
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Ollama Service Not Running
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama if not running
ollama serve

# Check Ollama status
curl http://localhost:11434/api/version
```

#### 2. Model Loading Errors
```bash
# List available models
ollama list

# Pull model if missing
ollama pull llama3.2:3b

# Check model status
ollama show llama3.2:3b
```

#### 3. Memory Issues
```python
# Check available memory
import psutil
print(f"Available RAM: {psutil.virtual_memory().available / (1024**3):.1f} GB")

# If memory is low, use smaller model:
# AI_AGENTS_DEFAULT_LLM=ollama/llama3.2:1b
```

#### 4. Slow Performance
```python
# Optimize settings for speed
fast_config = {
    "model": "llama3.2:1b",      # Smaller model
    "max_tokens": 500,           # Fewer tokens
    "temperature": 0.3,          # Lower temperature
    "request_timeout": 30        # Shorter timeout
}
```

#### 5. Connection Issues
```bash
# Test Ollama API directly
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:3b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Debug Mode

```bash
# Enable debug logging in .env
AI_AGENTS_DEBUG=true

# View Ollama logs
ollama logs
```

```python
# Enable detailed logging in Python
import logging
logging.basicConfig(level=logging.DEBUG)

# Test configuration
from ai_agents.configs.agents_config import AGENTS_CONFIG
print(AGENTS_CONFIG.get_status())
```

## 🔐 Security and Privacy

### Privacy Benefits
- **No Data Transmission**: All processing happens locally
- **No API Keys**: No external API keys required for Ollama
- **Full Control**: Complete control over data and model access
- **Offline Operation**: Works without internet connection

### Security Configuration

```python
# Secure Ollama configuration
secure_config = {
    "model": "llama3.2:3b",
    "base_url": "http://127.0.0.1:11434/v1",  # Bind to localhost only
    "api_key": "ollama",
    "request_timeout": 60,
    "max_retries": 1
}
```

### Network Security

```bash
# Ensure Ollama only binds to localhost
# Check Ollama binding
netstat -tulpn | grep 11434

# Should show: 127.0.0.1:11434 (not 0.0.0.0:11434)
```

## 📈 Optimization Tips

### Hardware Optimization

1. **SSD Storage**: Install models on SSD for faster loading
2. **RAM**: More RAM allows larger models and better performance
3. **CPU**: Modern CPUs with AVX support improve inference speed
4. **GPU**: NVIDIA GPUs can significantly accelerate inference

### Software Optimization

1. **Model Selection**: Choose the smallest model that meets your needs
2. **Token Limits**: Reduce max_tokens for faster responses
3. **Temperature**: Lower temperature (0.3-0.5) for faster, more focused responses
4. **Concurrent Limits**: Limit concurrent AI tasks to avoid resource contention

```bash
# In .env - optimize for performance
AI_AGENTS_MAX_CONCURRENT=1    # Reduce concurrent tasks
AI_AGENTS_DEFAULT_LLM=ollama/llama3.2:3b  # Balanced model
```

## 🔄 Integration Examples

### Full Integration Example

```python
# Complete example of Ollama integration with AI agents
from crewai import Agent, Task, Crew
from ai_agents.configs.ollama_config import get_ollama_llm

# Configure agents with Ollama
agents = {
    "chat": Agent(
        role="Chat Assistant",
        goal="Provide helpful responses using local AI",
        llm=get_ollama_llm("llama3.2:3b")
    ),
    "analytics": Agent(
        role="Analytics Specialist", 
        goal="Analyze data privately using local models",
        llm=get_ollama_llm("llama3.2:7b")
    )
}

# Create tasks
tasks = [
    Task(
        description="Respond to user chat message",
        agent=agents["chat"]
    ),
    Task(
        description="Analyze usage patterns",
        agent=agents["analytics"]
    )
]

# Create and execute crew
crew = Crew(
    agents=list(agents.values()),
    tasks=tasks,
    process="parallel"  # Can process tasks simultaneously
)

result = crew.kickoff()
```

## 📚 Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/README.md)
- [Ollama Model Library](https://ollama.ai/library)
- [CrewAI Documentation](https://docs.crewai.com/)
- [LangChain Ollama Integration](https://python.langchain.com/docs/integrations/chat/ollama)
- [Main Ollama Setup Guide](OLLAMA_SETUP_GUIDE.md)

---

This guide provides everything needed to run AI agents with Ollama for complete local AI processing in the Multi-API Chat platform, maintaining privacy while delivering powerful AI capabilities.
