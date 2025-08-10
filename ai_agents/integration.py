"""
AI Agent Integration Module
Connects CrewAI agents with the Multi-API Chat Platform backend
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from .agents.master_agent import get_master_agent, MasterAgent
from .configs.agents_config import AGENTS_CONFIG


class AIAgentIntegration:
    """Integration layer between AI agents and the platform backend"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.master_agent: Optional[MasterAgent] = None
        self.is_initialized = False
        self.integration_status = {
            "enabled": AGENTS_CONFIG.enabled,
            "initialized": False,
            "last_activity": None,
            "total_requests": 0,
            "error_count": 0
        }
        
        # Initialize if enabled
        if AGENTS_CONFIG.enabled:
            self._initialize()
    
    def _initialize(self):
        """Initialize the AI agent system"""
        try:
            self.logger.info("Initializing AI Agent Integration...")
            
            # Create master agent instance
            self.master_agent = get_master_agent()
            
            # Update status
            self.is_initialized = True
            self.integration_status["initialized"] = True
            self.integration_status["last_activity"] = datetime.now().isoformat()
            
            self.logger.info("AI Agent Integration initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Agent Integration: {str(e)}")
            self.integration_status["error_count"] += 1
            raise
    
    async def process_chat_message(self, 
                                 message: str, 
                                 session_id: str = None,
                                 user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a chat message through the AI agent system"""
        if not self._is_ready():
            return self._get_fallback_response("AI agents are not available")
        
        try:
            self.integration_status["total_requests"] += 1
            self.integration_status["last_activity"] = datetime.now().isoformat()
            
            # Prepare context
            context = {
                "session_id": session_id or "default",
                "user_context": user_context or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Process through master agent
            response = await self.master_agent.process_user_request(
                request=message,
                context=context,
                source_page="chat"
            )
            
            # Format response for frontend
            return self._format_agent_response(response)
            
        except Exception as e:
            self.logger.error(f"Error processing chat message: {str(e)}")
            self.integration_status["error_count"] += 1
            return self._get_error_response(str(e))
    
    async def handle_analytics_request(self, 
                                     request: str, 
                                     context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle analytics-specific requests"""
        if not self._is_ready():
            return self._get_fallback_response("Analytics AI agent is not available")
        
        try:
            self.integration_status["total_requests"] += 1
            
            # Add analytics-specific context
            analytics_context = {
                "page_type": "analytics",
                "request_type": "analytics",
                **(context or {})
            }
            
            response = await self.master_agent.process_user_request(
                request=request,
                context=analytics_context,
                source_page="dashboard"
            )
            
            return self._format_agent_response(response)
            
        except Exception as e:
            self.logger.error(f"Error handling analytics request: {str(e)}")
            self.integration_status["error_count"] += 1
            return self._get_error_response(str(e))
    
    async def handle_device_request(self, 
                                  request: str, 
                                  device_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle device management requests"""
        if not self._is_ready():
            return self._get_fallback_response("Device management AI agent is not available")
        
        try:
            self.integration_status["total_requests"] += 1
            
            # Add device-specific context
            device_ctx = {
                "page_type": "devices",
                "request_type": "device_management",
                "device_context": device_context or {},
                "timestamp": datetime.now().isoformat()
            }
            
            response = await self.master_agent.process_user_request(
                request=request,
                context=device_ctx,
                source_page="devices"
            )
            
            return self._format_agent_response(response)
            
        except Exception as e:
            self.logger.error(f"Error handling device request: {str(e)}")
            self.integration_status["error_count"] += 1
            return self._get_error_response(str(e))
    
    async def handle_operations_request(self, 
                                      request: str, 
                                      ops_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle operations management requests"""
        if not self._is_ready():
            return self._get_fallback_response("Operations AI agent is not available")
        
        try:
            self.integration_status["total_requests"] += 1
            
            # Add operations-specific context
            ops_ctx = {
                "page_type": "operations",
                "request_type": "operations_management",
                "ops_context": ops_context or {},
                "timestamp": datetime.now().isoformat()
            }
            
            response = await self.master_agent.process_user_request(
                request=request,
                context=ops_ctx,
                source_page="operations"
            )
            
            return self._format_agent_response(response)
            
        except Exception as e:
            self.logger.error(f"Error handling operations request: {str(e)}")
            self.integration_status["error_count"] += 1
            return self._get_error_response(str(e))
    
    async def handle_automation_request(self, 
                                      request: str, 
                                      automation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle automation workflow requests"""
        if not self._is_ready():
            return self._get_fallback_response("Automation AI agent is not available")
        
        try:
            self.integration_status["total_requests"] += 1
            
            # Add automation-specific context
            automation_ctx = {
                "page_type": "automation",
                "request_type": "automation_workflow",
                "automation_context": automation_context or {},
                "timestamp": datetime.now().isoformat()
            }
            
            response = await self.master_agent.process_user_request(
                request=request,
                context=automation_ctx,
                source_page="automation"
            )
            
            return self._format_agent_response(response)
            
        except Exception as e:
            self.logger.error(f"Error handling automation request: {str(e)}")
            self.integration_status["error_count"] += 1
            return self._get_error_response(str(e))
    
    async def handle_cross_page_request(self, 
                                      request: str,
                                      source_page: str,
                                      target_page: str,
                                      context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle requests that span multiple pages"""
        if not self._is_ready():
            return self._get_fallback_response("Cross-page AI functionality is not available")
        
        try:
            self.integration_status["total_requests"] += 1
            
            response = await self.master_agent.handle_cross_page_request(
                request=request,
                source_page=source_page,
                target_page=target_page,
                context=context
            )
            
            return self._format_agent_response(response)
            
        except Exception as e:
            self.logger.error(f"Error handling cross-page request: {str(e)}")
            self.integration_status["error_count"] += 1
            return self._get_error_response(str(e))
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the AI agent system"""
        if not self._is_ready():
            return {
                "status": "disabled",
                "message": "AI agents are not enabled or initialized",
                "integration_status": self.integration_status
            }
        
        try:
            # Get detailed status from master agent
            detailed_status = self.master_agent.get_agent_status()
            
            return {
                "status": "active",
                "integration_status": self.integration_status,
                "agent_details": detailed_status,
                "capabilities": self._get_system_capabilities(),
                "health_check": self._perform_health_check()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting agent status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "integration_status": self.integration_status
            }
    
    def _is_ready(self) -> bool:
        """Check if the AI agent system is ready for requests"""
        return (AGENTS_CONFIG.enabled and 
                self.is_initialized and 
                self.master_agent is not None)
    
    def _format_agent_response(self, agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format agent response for frontend consumption"""
        return {
            "success": agent_response.get("success", True),
            "response": agent_response.get("response", ""),
            "agents_involved": agent_response.get("agents_involved", []),
            "timestamp": agent_response.get("timestamp", datetime.now().isoformat()),
            "intent_analysis": agent_response.get("intent_analysis", {}),
            "ai_generated": True,
            "source": "ai_agents"
        }
    
    def _get_fallback_response(self, message: str) -> Dict[str, Any]:
        """Get fallback response when AI agents are not available"""
        return {
            "success": False,
            "response": message,
            "ai_generated": False,
            "fallback": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_error_response(self, error: str) -> Dict[str, Any]:
        """Get formatted error response"""
        return {
            "success": False,
            "response": "I encountered an error while processing your request. Please try again.",
            "error": error,
            "ai_generated": False,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_system_capabilities(self) -> Dict[str, Any]:
        """Get system capabilities summary"""
        all_agents = AGENTS_CONFIG.get_all_agents()
        
        capabilities = {
            "total_agents": len(all_agents),
            "agent_types": list(all_agents.keys()),
            "cross_page_communication": True,
            "context_persistence": True,
            "multi_api_support": True,
            "real_time_processing": True
        }
        
        # Aggregate capabilities
        all_capabilities = set()
        for agent_config in all_agents.values():
            all_capabilities.update(agent_config.capabilities)
        
        capabilities["available_capabilities"] = list(all_capabilities)
        
        return capabilities
    
    def _perform_health_check(self) -> Dict[str, Any]:
        """Perform basic health check of the agent system"""
        health = {
            "overall_status": "healthy",
            "checks": {
                "master_agent": "healthy" if self.master_agent else "unhealthy",
                "configuration": "healthy" if AGENTS_CONFIG.enabled else "disabled",
                "memory_usage": "normal",  # Could implement actual memory checking
                "response_time": "normal"   # Could implement actual response time checking
            },
            "last_check": datetime.now().isoformat()
        }
        
        # Determine overall status
        unhealthy_checks = [k for k, v in health["checks"].items() if v != "healthy" and v != "normal"]
        if unhealthy_checks:
            if "configuration" in unhealthy_checks and len(unhealthy_checks) == 1:
                health["overall_status"] = "disabled"
            else:
                health["overall_status"] = "degraded"
        
        return health


# Global integration instance
ai_integration_instance: Optional[AIAgentIntegration] = None


def get_ai_integration() -> AIAgentIntegration:
    """Get or create AI integration instance"""
    global ai_integration_instance
    if ai_integration_instance is None:
        ai_integration_instance = AIAgentIntegration()
    return ai_integration_instance


def is_ai_enabled() -> bool:
    """Check if AI agents are enabled"""
    return AGENTS_CONFIG.enabled


async def process_ai_request(request_type: str, 
                           request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process AI request based on type"""
    integration = get_ai_integration()
    
    request_type = request_type.lower()
    message = request_data.get("message", "")
    context = request_data.get("context", {})
    
    if request_type == "chat":
        return await integration.process_chat_message(
            message=message,
            session_id=request_data.get("session_id"),
            user_context=context
        )
    
    elif request_type == "analytics":
        return await integration.handle_analytics_request(
            request=message,
            context=context
        )
    
    elif request_type == "device":
        return await integration.handle_device_request(
            request=message,
            device_context=context
        )
    
    elif request_type == "operations":
        return await integration.handle_operations_request(
            request=message,
            ops_context=context
        )
    
    elif request_type == "automation":
        return await integration.handle_automation_request(
            request=message,
            automation_context=context
        )
    
    elif request_type == "cross_page":
        return await integration.handle_cross_page_request(
            request=message,
            source_page=request_data.get("source_page", ""),
            target_page=request_data.get("target_page", ""),
            context=context
        )
    
    else:
        return {
            "success": False,
            "response": f"Unknown request type: {request_type}",
            "timestamp": datetime.now().isoformat()
        }


def get_ai_status() -> Dict[str, Any]:
    """Get AI system status"""
    integration = get_ai_integration()
    return integration.get_agent_status()
