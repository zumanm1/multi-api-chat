"""
AI Backend Integration
Simple integration layer for AI agents with the existing backend server
"""

import asyncio
import logging
from typing import Dict, Any

# Import the simple master agent directly
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_agents', 'agents'))
from simple_master_agent import get_simple_master_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AI Integration class for backend
class AIBackendIntegration:
    """Simple AI integration for the backend server"""
    
    def __init__(self):
        self.enabled = True
        self.logger = logger
        self.logger.info("AI Backend Integration initialized")
    
    async def process_ai_request(self, request_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process AI request based on type using simple master agent"""
        if not self.enabled:
            return {
                "success": False,
                "response": "AI agents are currently disabled",
                "ai_generated": False
            }
        
        try:
            master_agent = get_simple_master_agent()
            message = data.get("message", "")
            context = data.get("context", {})
            session_id = data.get("session_id", "default")
            
            # Add request type to context
            context["request_type"] = request_type.lower()
            context["session_id"] = session_id
            
            # Process with master agent
            result = await master_agent.process_user_request(
                request=message,
                context=context,
                source_page=context.get("source_page", "api")
            )
            
            # Format response for backend compatibility
            return {
                "success": result.get("success", True),
                "response": result.get("response", "No response generated"),
                "agents_involved": result.get("agents_involved", []),
                "ai_generated": True,
                "source": "simple_master_agent",
                "capabilities_used": result.get("capabilities_used", []),
                "timestamp": result.get("timestamp")
            }
        
        except Exception as e:
            self.logger.error(f"Error processing AI request: {str(e)}")
            return {
                "success": False,
                "response": "An error occurred while processing your AI request",
                "error": str(e),
                "ai_generated": False
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get AI integration status"""
        agent_status = None
        if self.enabled:
            try:
                master_agent = get_simple_master_agent()
                agent_status = master_agent.get_agent_status()
            except Exception as e:
                self.logger.error(f"Error getting agent status: {e}")
                agent_status = {"error": str(e)}
        
        return {
            "enabled": self.enabled,
            "status": "active" if self.enabled else "disabled",
            "agent_status": agent_status
        }
    
    def toggle_ai(self, enabled: bool = None) -> Dict[str, Any]:
        """Toggle AI agents on/off"""
        if enabled is not None:
            self.enabled = enabled
        else:
            self.enabled = not self.enabled
        
        status = "enabled" if self.enabled else "disabled"
        self.logger.info(f"AI agents {status}")
        
        return {
            "success": True,
            "message": f"AI agents {status}",
            "enabled": self.enabled
        }

# Global instance
ai_backend_integration = AIBackendIntegration()

# Synchronous wrappers for Flask integration
def process_ai_request_sync(request_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for AI request processing"""
    try:
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                ai_backend_integration.process_ai_request(request_type, data)
            )
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Error in sync AI request: {str(e)}")
        return {
            "success": False,
            "response": "An error occurred processing your request",
            "error": str(e),
            "ai_generated": False
        }

def get_ai_integration_status() -> Dict[str, Any]:
    """Get AI integration status (synchronous)"""
    return ai_backend_integration.get_status()

def toggle_ai_agents(enabled: bool = None) -> Dict[str, Any]:
    """Toggle AI agents on/off (synchronous)"""
    return ai_backend_integration.toggle_ai(enabled)

# Test the integration
if __name__ == "__main__":
    print("=== AI Backend Integration Test ===")
    
    # Test different request types
    test_cases = [
        ("chat", {"message": "Hello, how can you help me?", "session_id": "test123"}),
        ("analytics", {"message": "Show me system performance metrics"}),
        ("device", {"message": "Check device status"}),
        ("operations", {"message": "Analyze recent logs"}),
        ("automation", {"message": "Create a backup workflow"}),
        ("status", {})
    ]
    
    for request_type, data in test_cases:
        print(f"\n--- Testing {request_type.upper()} ---")
        result = process_ai_request_sync(request_type, data)
        print(f"Success: {result.get('success')}")
        print(f"Response: {result.get('response', '')[:100]}{'...' if len(result.get('response', '')) > 100 else ''}")
        if 'agents_involved' in result:
            print(f"Agents: {result['agents_involved']}")
    
    print(f"\n--- Integration Status ---")
    status = get_ai_integration_status()
    print(f"Enabled: {status['enabled']}")
    print(f"Status: {status['status']}")
    
    print(f"\n--- Toggle Test ---")
    toggle_result = toggle_ai_agents(False)
    print(f"Toggle result: {toggle_result}")
    
    # Test with AI disabled
    result = process_ai_request_sync("chat", {"message": "Test with AI disabled"})
    print(f"Disabled AI result: {result}")
    
    # Re-enable
    toggle_ai_agents(True)
    print("AI re-enabled")
