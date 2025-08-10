"""
Test AI Agents System
Basic tests for the CrewAI agent integration
"""

import asyncio
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ai_agents import (
    get_ai_integration, 
    is_ai_enabled, 
    process_ai_request,
    get_ai_status
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_integration():
    """Test basic AI integration functionality"""
    
    print("=== AI Agents System Test ===")
    print(f"AI Enabled: {is_ai_enabled()}")
    
    # Test status
    print("\n1. Testing AI Status:")
    status = get_ai_status()
    print(f"Status: {status}")
    
    # Test integration instance
    print("\n2. Testing AI Integration Instance:")
    integration = get_ai_integration()
    print(f"Integration initialized: {integration.is_initialized}")
    print(f"Integration ready: {integration._is_ready()}")
    
    if not integration._is_ready():
        print("AI agents are not ready. Skipping request tests.")
        return
    
    # Test chat request
    print("\n3. Testing Chat Request:")
    chat_response = await process_ai_request("chat", {
        "message": "Hello, can you help me with API integration?",
        "session_id": "test_session",
        "context": {"user_id": "test_user"}
    })
    print(f"Chat Response: {chat_response}")
    
    # Test analytics request
    print("\n4. Testing Analytics Request:")
    analytics_response = await process_ai_request("analytics", {
        "message": "Show me usage trends from the last week",
        "context": {"dashboard_type": "usage"}
    })
    print(f"Analytics Response: {analytics_response}")
    
    # Test device request
    print("\n5. Testing Device Request:")
    device_response = await process_ai_request("device", {
        "message": "Check the status of all IoT devices",
        "context": {"device_filter": "all"}
    })
    print(f"Device Response: {device_response}")
    
    # Test cross-page request
    print("\n6. Testing Cross-Page Request:")
    cross_page_response = await process_ai_request("cross_page", {
        "message": "Transfer analytics data to the automation dashboard",
        "source_page": "dashboard",
        "target_page": "automation",
        "context": {"data_type": "analytics"}
    })
    print(f"Cross-Page Response: {cross_page_response}")
    
    print("\n=== Test Complete ===")

def test_configuration():
    """Test agent configuration"""
    print("\n=== Configuration Test ===")
    
    from ai_agents.configs.agents_config import AGENTS_CONFIG
    
    print(f"Total agents configured: {len(AGENTS_CONFIG.get_all_agents())}")
    
    for agent_name, config in AGENTS_CONFIG.get_all_agents().items():
        print(f"\nAgent: {agent_name}")
        print(f"  Role: {config.role}")
        print(f"  Capabilities: {len(config.capabilities)}")
        print(f"  Tools: {config.tools}")
        print(f"  LLM Config: {config.llm_config}")

def test_tools():
    """Test agent tools"""
    print("\n=== Tools Test ===")
    
    from ai_agents.tools.base_tools import list_available_tools, get_agent_tools
    
    available_tools = list_available_tools()
    print(f"Available tools: {len(available_tools)}")
    print(f"Tools: {available_tools}")
    
    # Test getting tools for master agent
    master_tools = get_agent_tools(["user_context_tool", "agent_communication_tool"])
    print(f"Master agent tools: {len(master_tools)}")
    
    # Test a tool
    if master_tools:
        context_tool = master_tools[0]
        print(f"Testing context tool: {context_tool.name}")
        result = context_tool._run("set", "test_key", "test_value")
        print(f"Tool result: {result}")

if __name__ == "__main__":
    print("Starting AI Agents Test Suite")
    
    # Test configuration
    test_configuration()
    
    # Test tools
    test_tools()
    
    # Test integration (async)
    try:
        asyncio.run(test_ai_integration())
    except Exception as e:
        print(f"Integration test failed: {str(e)}")
        logger.exception("Integration test error")
    
    print("\nTest suite completed!")
