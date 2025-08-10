"""
Basic Setup Test for AI Agents
Tests configuration and tools without full CrewAI integration
"""

import sys
import os

print("=== AI Agents Basic Setup Test ===")

try:
    # Test configuration
    print("\n1. Testing Configuration:")
    from ai_agents.configs.agents_config import AGENTS_CONFIG
    
    print(f"AI Agents Enabled: {AGENTS_CONFIG.enabled}")
    print(f"Debug Mode: {AGENTS_CONFIG.debug_mode}")
    print(f"Default LLM: {AGENTS_CONFIG.default_llm}")
    print(f"Max Concurrent Tasks: {AGENTS_CONFIG.max_concurrent_tasks}")
    
    agents = AGENTS_CONFIG.get_all_agents()
    print(f"Total Configured Agents: {len(agents)}")
    
    for agent_name, config in agents.items():
        print(f"  - {agent_name}: {config.role}")
        print(f"    Capabilities: {len(config.capabilities)}")
        print(f"    Tools: {config.tools}")
    
    print("\n2. Testing Tools Registry:")
    from ai_agents.tools.base_tools import list_available_tools, AVAILABLE_TOOLS
    
    available_tools = list_available_tools()
    print(f"Total Available Tools: {len(available_tools)}")
    
    implemented_tools = [name for name, tool_class in AVAILABLE_TOOLS.items() if tool_class is not None]
    placeholder_tools = [name for name, tool_class in AVAILABLE_TOOLS.items() if tool_class is None]
    
    print(f"Implemented Tools ({len(implemented_tools)}): {implemented_tools}")
    print(f"Placeholder Tools ({len(placeholder_tools)}): {placeholder_tools}")
    
    print("\n3. Testing Individual Tools:")
    from ai_agents.tools.base_tools import AgentContextTool, AgentCommunicationTool, TaskSchedulerTool
    
    # Test Context Tool
    context_tool = AgentContextTool()
    print(f"Context Tool: {context_tool.name}")
    result = context_tool._run("set", "test_key", "test_value", "test_user")
    print(f"  Set operation: {result}")
    result = context_tool._run("get", "test_key", user_id="test_user")
    print(f"  Get operation: {result}")
    
    # Test Communication Tool
    comm_tool = AgentCommunicationTool()
    print(f"Communication Tool: {comm_tool.name}")
    result = comm_tool._run("send", "agent1", "agent2", "Hello from agent1", {"test": "data"})
    print(f"  Send message: {result}")
    result = comm_tool._run("receive", "agent2")
    print(f"  Receive message: {result}")
    
    # Test Scheduler Tool
    scheduler_tool = TaskSchedulerTool()
    print(f"Scheduler Tool: {scheduler_tool.name}")
    result = scheduler_tool._run("schedule", "task1", {"description": "Test task", "priority": "high"})
    print(f"  Schedule task: {result}")
    result = scheduler_tool._run("get", "task1")
    print(f"  Get task: {result}")
    
    print("\n4. Environment Check:")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Check for required environment variables
    env_vars = ["OPENAI_API_KEY", "AI_AGENTS_ENABLED", "AI_AGENTS_DEBUG"]
    for var in env_vars:
        value = os.getenv(var, "Not set")
        print(f"  {var}: {'Set' if value != 'Not set' else 'Not set'}")
    
    print("\n=== Basic Setup Test PASSED ===")
    
except Exception as e:
    print(f"Basic setup test FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
