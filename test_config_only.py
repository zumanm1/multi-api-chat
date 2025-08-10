"""
Standalone test for AI agent configuration and tools
Tests without importing CrewAI dependencies
"""

import sys
import os

print("=== AI Agents Configuration Test ===")

try:
    # Direct import of configuration
    sys.path.insert(0, '.')
    
    print("\n1. Testing Configuration Direct Import:")
    from ai_agents.configs.agents_config import AGENTS_CONFIG
    
    print(f"AI Agents Enabled: {AGENTS_CONFIG.enabled}")
    print(f"Debug Mode: {AGENTS_CONFIG.debug_mode}")
    print(f"Default LLM: {AGENTS_CONFIG.default_llm}")
    print(f"Max Concurrent Tasks: {AGENTS_CONFIG.max_concurrent_tasks}")
    
    agents = AGENTS_CONFIG.get_all_agents()
    print(f"Total Configured Agents: {len(agents)}")
    
    for agent_name, config in agents.items():
        print(f"\n  Agent: {agent_name}")
        print(f"    Role: {config.role}")
        print(f"    Goal: {config.goal[:100]}...")
        print(f"    Capabilities: {len(config.capabilities)} - {config.capabilities}")
        print(f"    Tools: {config.tools}")
        print(f"    Memory: {config.memory}")
        print(f"    Verbose: {config.verbose}")
        print(f"    LLM Config: {config.llm_config}")
    
    print("\n2. Testing Tools Direct Import:")
    from ai_agents.tools.base_tools import (
        list_available_tools, 
        AVAILABLE_TOOLS,
        AgentContextTool,
        AgentCommunicationTool,
        TaskSchedulerTool,
        ChatHistoryTool,
        APIIntegrationTool
    )
    
    available_tools = list_available_tools()
    print(f"Total Available Tools: {len(available_tools)}")
    
    implemented_tools = [name for name, tool_class in AVAILABLE_TOOLS.items() if tool_class is not None]
    placeholder_tools = [name for name, tool_class in AVAILABLE_TOOLS.items() if tool_class is None]
    
    print(f"Implemented Tools ({len(implemented_tools)}): {implemented_tools}")
    print(f"Placeholder Tools ({len(placeholder_tools)}): {placeholder_tools}")
    
    print("\n3. Testing Individual Tools:")
    
    # Test Context Tool
    print("\n  Context Tool:")
    context_tool = AgentContextTool()
    print(f"    Name: {context_tool.name}")
    print(f"    Description: {context_tool.description}")
    
    # Test operations
    result = context_tool._run("set", "test_key", "test_value", "test_user")
    print(f"    Set operation: {result}")
    
    result = context_tool._run("get", "test_key", user_id="test_user")
    print(f"    Get operation: {result}")
    
    result = context_tool._run("append", "test_list", "item1", "test_user")
    print(f"    Append operation: {result}")
    
    result = context_tool._run("get", user_id="test_user")
    print(f"    Get all context: {result}")
    
    # Test Communication Tool
    print("\n  Communication Tool:")
    comm_tool = AgentCommunicationTool()
    print(f"    Name: {comm_tool.name}")
    
    result = comm_tool._run("send", "agent1", "agent2", "Hello from agent1", {"test": "data"})
    print(f"    Send message: {result}")
    
    result = comm_tool._run("receive", "agent2")
    print(f"    Receive message: {result}")
    
    result = comm_tool._run("broadcast", "agent1", message="Broadcasting test message")
    print(f"    Broadcast message: {result}")
    
    # Test Task Scheduler Tool
    print("\n  Task Scheduler Tool:")
    scheduler_tool = TaskSchedulerTool()
    print(f"    Name: {scheduler_tool.name}")
    
    result = scheduler_tool._run("schedule", "task1", {"description": "Test task", "priority": "high"})
    print(f"    Schedule task: {result}")
    
    result = scheduler_tool._run("get", "task1")
    print(f"    Get task: {result}")
    
    result = scheduler_tool._run("update", "task1", {"status": "in_progress"})
    print(f"    Update task: {result}")
    
    result = scheduler_tool._run("get")
    print(f"    Get all tasks: {result}")
    
    # Test Chat History Tool
    print("\n  Chat History Tool:")
    chat_tool = ChatHistoryTool()
    print(f"    Name: {chat_tool.name}")
    
    result = chat_tool._run("add", "test_session", {"content": "Hello world", "type": "user"})
    print(f"    Add message: {result}")
    
    result = chat_tool._run("get", "test_session", limit=5)
    print(f"    Get messages: {result}")
    
    result = chat_tool._run("stats", "test_session")
    print(f"    Get stats: {result}")
    
    # Test API Integration Tool
    print("\n  API Integration Tool:")
    api_tool = APIIntegrationTool()
    print(f"    Name: {api_tool.name}")
    
    result = api_tool._run("list_apis")
    print(f"    List APIs: {result}")
    
    result = api_tool._run("call", "openai", "chat/completions", {"model": "gpt-4", "messages": []})
    print(f"    API Call: {result}")
    
    result = api_tool._run("status", "openai")
    print(f"    API Status: {result}")
    
    print("\n4. Environment and Dependencies Check:")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Check for required environment variables
    env_vars = ["OPENAI_API_KEY", "AI_AGENTS_ENABLED", "AI_AGENTS_DEBUG"]
    for var in env_vars:
        value = os.getenv(var, "Not set")
        print(f"  {var}: {'Set (****)' if value != 'Not set' else 'Not set'}")
    
    # Check dependencies
    dependencies = ["crewai", "langchain", "langchain-openai"]
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  {dep}: Available")
        except ImportError:
            print(f"  {dep}: Not installed")
    
    print("\n=== Configuration Test PASSED ===")
    print("\nNext Steps:")
    print("1. Set up environment variables (especially OPENAI_API_KEY)")
    print("2. Install missing dependencies if needed")
    print("3. Test full CrewAI integration")
    
except Exception as e:
    print(f"Configuration test FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
