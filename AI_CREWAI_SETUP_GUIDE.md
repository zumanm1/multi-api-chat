# CrewAI Setup Guide for Multi-API Chat Platform

This guide explains how to configure CrewAI with different LLM providers, including Ollama for local AI processing.

## 📋 Prerequisites

### Core Dependencies Installation

Install the AI agent dependencies first:

```bash
# Install AI agent dependencies (optional)
pip install -r requirements-ai-agents.txt
```

This will install:
- `crewai>=0.41.0` - Main CrewAI framework
- `crewai-tools>=0.4.0` - CrewAI tools library  
- `langchain>=0.1.0` - LangChain framework (required by CrewAI)
- `langchain-openai>=0.0.5` - OpenAI integration for LangChain
- `langgraph>=0.0.20` - LangGraph for agent workflow orchestration
- `pydantic>=2.0.0` - Data validation (required by CrewAI)
- `tiktoken>=0.5.0` - Token counting for LLM interactions
- `aiohttp>=3.9.0` - Async HTTP client for API calls
- `chromadb>=0.4.0` - Vector database for agent memory
- `numpy<2.0.0` - Numerical operations (pinned to avoid compatibility issues)

### Environment Configuration

Set up your environment variables in `.env`:

```bash
# Copy the template
cp .env.template .env

# Edit .env with your configuration
ENABLE_AI_AGENTS=true
AI_AGENTS_DEBUG=false
AI_AGENTS_DEFAULT_LLM=gpt-4
AI_AGENTS_MAX_CONCURRENT=3
```

## 🤖 LLM Provider Configuration

### 1. OpenAI (Default)

CrewAI works seamlessly with OpenAI models:

```bash
# Add to .env
OPENAI_API_KEY=sk-your-openai-api-key
AI_AGENTS_DEFAULT_LLM=gpt-4
```

**Recommended Models:**
- `gpt-4` - Best performance for complex agent tasks
- `gpt-4-turbo` - Faster and cheaper alternative
- `gpt-3.5-turbo` - Budget-friendly option

### 2. Ollama (Local AI) - Recommended for Privacy

Ollama provides local AI processing with privacy and cost benefits.

#### Ollama Installation

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Install a model (choose based on your hardware)
ollama pull llama3.2:1b      # Lightweight (1.3GB)
ollama pull llama3.2:3b      # Balanced (2GB)  
ollama pull llama3.2:7b      # High quality (4.1GB)
ollama pull llama3.1:8b      # Very high quality (4.7GB)
```

#### Ollama Configuration for CrewAI

```bash
# Add to .env
AI_AGENTS_DEFAULT_LLM=ollama/llama3.2:3b
OLLAMA_API_BASE=http://localhost:11434/v1
```

#### Python Configuration for Ollama

```python
# In your CrewAI agent setup
from crewai import Agent
from langchain_openai import ChatOpenAI

# Configure Ollama LLM for CrewAI
ollama_llm = ChatOpenAI(
    model="llama3.2:3b",
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Ollama doesn't require a real API key
    temperature=0.7
)

# Create agent with Ollama LLM
agent = Agent(
    role="Chat Assistant",
    goal="Provide helpful responses",
    backstory="You are a helpful AI assistant",
    llm=ollama_llm
)
```

### 3. Groq (Fast Inference)

For high-speed inference with open-source models:

```bash
# Add to .env
GROQ_API_KEY=gsk_your-groq-api-key
AI_AGENTS_DEFAULT_LLM=groq/llama3.1-8b-instant
```

### 4. OpenRouter (Multiple Models)

Access to multiple model providers through one API:

```bash
# Add to .env  
OPENROUTER_API_KEY=sk-or-your-openrouter-key
AI_AGENTS_DEFAULT_LLM=openrouter/anthropic/claude-3.5-sonnet
```

### 5. Anthropic Claude

For advanced reasoning capabilities:

```bash
# Add to .env
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
AI_AGENTS_DEFAULT_LLM=anthropic/claude-3-sonnet-20240229
```

## 🛠️ CrewAI Configuration Examples

### Basic Agent Setup

```python
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

# Configure LLM
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    max_tokens=1500
)

# Create agent
chat_agent = Agent(
    role="Conversational Assistant",
    goal="Provide intelligent conversational responses",
    backstory="You are a helpful AI assistant",
    llm=llm,
    memory=True,
    verbose=True
)

# Create task
task = Task(
    description="Respond to user query about AI capabilities",
    agent=chat_agent,
    expected_output="Helpful and informative response"
)

# Create crew
crew = Crew(
    agents=[chat_agent],
    tasks=[task],
    verbose=True
)
```

### Multi-Agent Setup

```python
# Analytics Agent
analytics_agent = Agent(
    role="Data Analyst",
    goal="Analyze platform usage and provide insights",
    backstory="Expert in data analysis and visualization",
    llm=llm,
    tools=[data_analysis_tool, chart_generator_tool]
)

# Device Management Agent  
device_agent = Agent(
    role="Device Manager",
    goal="Monitor and manage connected devices",
    backstory="Specialist in IoT device management", 
    llm=llm,
    tools=[device_scanner_tool, config_manager_tool]
)

# Create crew with multiple agents
crew = Crew(
    agents=[chat_agent, analytics_agent, device_agent],
    tasks=[chat_task, analytics_task, device_task],
    process="sequential",  # or "hierarchical"
    verbose=True
)
```

### Ollama-Specific Configuration

```python
# Optimized configuration for Ollama
from langchain_openai import ChatOpenAI

ollama_llm = ChatOpenAI(
    model="llama3.2:3b",
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    temperature=0.7,
    max_tokens=1000,  # Adjust based on model capabilities
    request_timeout=60,  # Longer timeout for local processing
)

# Agent optimized for local processing
local_agent = Agent(
    role="Local AI Assistant",
    goal="Provide responses using local AI model",
    backstory="You are a privacy-focused local AI assistant",
    llm=ollama_llm,
    memory=True,
    max_execution_time=120,  # Allow more time for local processing
    allow_delegation=False   # Keep processing local
)
```

## 🔧 Advanced Configuration

### Custom LLM Selection Per Agent

```python
# Different LLMs for different agents
fast_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
smart_llm = ChatOpenAI(model="gpt-4", temperature=0.7)
local_llm = ChatOpenAI(
    model="llama3.2:3b",
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# Quick response agent
quick_agent = Agent(
    role="Quick Responder",
    goal="Provide fast responses",
    llm=fast_llm
)

# Deep analysis agent
analysis_agent = Agent(
    role="Deep Analyst", 
    goal="Provide detailed analysis",
    llm=smart_llm
)

# Privacy-focused agent
private_agent = Agent(
    role="Privacy Assistant",
    goal="Handle sensitive information locally",
    llm=local_llm
)
```

### Dynamic LLM Configuration

```python
import os

def get_llm_config():
    """Dynamically configure LLM based on environment"""
    default_llm = os.getenv('AI_AGENTS_DEFAULT_LLM', 'gpt-4')
    
    if default_llm.startswith('ollama/'):
        model_name = default_llm.replace('ollama/', '')
        return ChatOpenAI(
            model=model_name,
            base_url="http://localhost:11434/v1", 
            api_key="ollama",
            temperature=0.7
        )
    elif default_llm.startswith('groq/'):
        model_name = default_llm.replace('groq/', '')
        return ChatOpenAI(
            model=model_name,
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv('GROQ_API_KEY'),
            temperature=0.7
        )
    else:
        return ChatOpenAI(
            model=default_llm,
            api_key=os.getenv('OPENAI_API_KEY'),
            temperature=0.7
        )

# Use dynamic configuration
llm = get_llm_config()
```

## 🚀 Performance Optimization

### For Ollama (Local AI)

```python
# Optimized settings for local processing
ollama_config = {
    "model": "llama3.2:3b",  # Balance of speed and quality
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "temperature": 0.7,
    "max_tokens": 800,      # Reduce for faster processing
    "top_p": 0.9,
    "frequency_penalty": 0.1,
    "presence_penalty": 0.1,
    "request_timeout": 45    # Reasonable timeout
}

ollama_llm = ChatOpenAI(**ollama_config)
```

### For Cloud Providers

```python
# Optimized settings for cloud APIs
cloud_config = {
    "model": "gpt-4-turbo",
    "temperature": 0.7,
    "max_tokens": 1500,
    "top_p": 1.0,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "request_timeout": 30
}

cloud_llm = ChatOpenAI(**cloud_config)
```

## 🔍 Testing Configuration

Test your CrewAI setup:

```python
def test_crewai_setup():
    """Test CrewAI configuration"""
    try:
        # Test LLM connection
        llm = get_llm_config()
        response = llm.invoke("Hello, are you working?")
        print(f"LLM Response: {response.content}")
        
        # Test basic agent
        test_agent = Agent(
            role="Test Agent",
            goal="Test the setup",
            backstory="Testing agent functionality",
            llm=llm
        )
        
        test_task = Task(
            description="Say hello and confirm you're working",
            agent=test_agent,
            expected_output="Confirmation message"
        )
        
        crew = Crew(
            agents=[test_agent],
            tasks=[test_task]
        )
        
        result = crew.kickoff()
        print(f"Crew Result: {result}")
        print("✅ CrewAI setup successful!")
        
    except Exception as e:
        print(f"❌ CrewAI setup failed: {e}")

# Run test
test_crewai_setup()
```

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements-ai-agents.txt
   ```

2. **Ollama Connection Issues**:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/version
   
   # Restart Ollama if needed
   ollama serve
   ```

3. **API Key Issues**: Verify environment variables are set correctly
   ```bash
   echo $OPENAI_API_KEY
   echo $ENABLE_AI_AGENTS
   ```

4. **Memory Issues with Ollama**: Reduce model size or max_tokens
   ```python
   ollama_llm = ChatOpenAI(
       model="llama3.2:1b",  # Smaller model
       max_tokens=500        # Reduce token limit
   )
   ```

### Debugging

Enable debug mode for detailed logging:

```bash
# In .env
AI_AGENTS_DEBUG=true
```

```python
# In Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Monitoring

Monitor CrewAI performance:

```python
import time
from crewai import Crew

def timed_crew_execution(crew):
    """Execute crew with timing"""
    start_time = time.time()
    result = crew.kickoff()
    end_time = time.time()
    
    print(f"Execution time: {end_time - start_time:.2f} seconds")
    return result
```

## 🔗 Integration with Multi-API Chat

The CrewAI agents integrate seamlessly with the existing Multi-API Chat platform:

1. **Fallback Behavior**: If CrewAI dependencies are missing, the platform continues to work normally
2. **Dynamic Enabling**: Control AI agents via the `ENABLE_AI_AGENTS` environment variable
3. **Provider Integration**: CrewAI agents can use the same LLM providers as the main chat interface
4. **Resource Sharing**: Shared configuration and logging infrastructure

## 📚 Additional Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [LangChain Documentation](https://python.langchain.com/)
- [Multi-API Chat Ollama Guide](OLLAMA_SETUP_GUIDE.md)

---

This setup guide enables you to configure CrewAI with various LLM providers while maintaining the optional nature of AI features in the Multi-API Chat platform.
