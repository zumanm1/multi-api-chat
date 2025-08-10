"""
AI Agents Demo Backend Integration
Demonstrates the AI agent concept without full CrewAI dependencies
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

# Mock AI agent responses for demonstration
class MockAIAgent:
    """Mock AI agent for demonstration purposes"""
    
    def __init__(self, name: str, role: str, capabilities: List[str]):
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.memory = {}
    
    async def process_request(self, request: str, context: Dict = None) -> Dict[str, Any]:
        """Mock processing of user request"""
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        # Generate mock response based on agent type
        if "chat" in self.name.lower():
            response = self._generate_chat_response(request, context)
        elif "analytics" in self.name.lower():
            response = self._generate_analytics_response(request, context)
        elif "device" in self.name.lower():
            response = self._generate_device_response(request, context)
        elif "operations" in self.name.lower():
            response = self._generate_operations_response(request, context)
        elif "automation" in self.name.lower():
            response = self._generate_automation_response(request, context)
        else:
            response = self._generate_generic_response(request, context)
        
        return {
            "agent": self.name,
            "role": self.role,
            "response": response,
            "capabilities_used": self._get_relevant_capabilities(request),
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_chat_response(self, request: str, context: Dict) -> str:
        """Generate chat-specific response"""
        if "help" in request.lower():
            return f"I'm your AI assistant specializing in {self.role}. I can help you with various tasks across the platform."
        elif "api" in request.lower():
            return "I can help you integrate with multiple AI APIs including OpenAI, Anthropic, Google, and local models like Ollama."
        elif "status" in request.lower():
            return "All systems are running smoothly. I'm ready to assist you with any questions or tasks."
        else:
            return f"I understand you're asking about: {request}. As a {self.role}, I can provide intelligent assistance and route your request to specialized agents if needed."
    
    def _generate_analytics_response(self, request: str, context: Dict) -> str:
        """Generate analytics-specific response"""
        if "usage" in request.lower() or "trends" in request.lower():
            return "Based on recent data analysis: API usage is up 25% this week, with GPT-4 being the most popular model. Peak usage occurs between 9-11 AM."
        elif "performance" in request.lower():
            return "System performance metrics: Average response time: 0.8s, Success rate: 99.2%, Most active endpoints: /chat, /analytics"
        elif "report" in request.lower():
            return "Generated comprehensive analytics report covering user engagement, API performance, and system health metrics."
        else:
            return f"Analytics insight: {request} - I've analyzed the relevant data and can provide detailed metrics and visualizations."
    
    def _generate_device_response(self, request: str, context: Dict) -> str:
        """Generate device management response"""
        if "status" in request.lower():
            return "Device status check: 15 devices online, 2 devices require attention, 1 firmware update available."
        elif "configuration" in request.lower():
            return "Device configuration updated successfully. All IoT sensors are properly calibrated and reporting."
        elif "health" in request.lower():
            return "Device health monitoring: All critical systems operational, temperature sensors within normal range."
        else:
            return f"Device management action for: {request} - I'm monitoring and managing all connected IoT devices and systems."
    
    def _generate_operations_response(self, request: str, context: Dict) -> str:
        """Generate operations-specific response"""
        if "deployment" in request.lower():
            return "Deployment status: Latest version deployed successfully across all environments. No issues detected."
        elif "logs" in request.lower():
            return "Log analysis complete: Found 3 warnings, 0 errors. System stability is excellent."
        elif "monitoring" in request.lower():
            return "System monitoring active: CPU usage: 35%, Memory: 2.1GB, Disk: 78% free. All metrics within normal parameters."
        else:
            return f"Operations management for: {request} - I'm ensuring system reliability and handling infrastructure operations."
    
    def _generate_automation_response(self, request: str, context: Dict) -> str:
        """Generate automation-specific response"""
        if "workflow" in request.lower():
            return "Workflow automation: Created new workflow with 4 stages, estimated 70% time savings on this process."
        elif "schedule" in request.lower():
            return "Automated scheduling: Set up recurring tasks for system maintenance and data backups."
        elif "trigger" in request.lower():
            return "Automation triggers configured: Will automatically respond to system alerts and scale resources as needed."
        else:
            return f"Automation setup for: {request} - I'm creating efficient workflows to streamline your processes."
    
    def _generate_generic_response(self, request: str, context: Dict) -> str:
        """Generate generic response"""
        return f"As the {self.role}, I'm processing your request: {request}. I'll coordinate with other specialized agents to provide the best assistance."
    
    def _get_relevant_capabilities(self, request: str) -> List[str]:
        """Determine which capabilities are relevant to the request"""
        relevant = []
        request_lower = request.lower()
        
        for capability in self.capabilities:
            if any(word in request_lower for word in capability.split('_')):
                relevant.append(capability)
        
        return relevant[:3]  # Limit to 3 most relevant


class MockMasterAgent:
    """Mock master agent for coordinating other agents"""
    
    def __init__(self):
        self.specialized_agents = {
            "chat_agent": MockAIAgent("Chat Agent", "Conversational Assistant", [
                "natural_language_processing", "conversation_management", "context_retention", 
                "multi_api_integration", "response_optimization"
            ]),
            "analytics_agent": MockAIAgent("Analytics Agent", "Data Analyst", [
                "data_analysis", "pattern_recognition", "predictive_modeling", 
                "report_generation", "visualization_creation"
            ]),
            "device_agent": MockAIAgent("Device Agent", "IoT Device Manager", [
                "device_monitoring", "configuration_management", "health_diagnostics",
                "automatic_remediation", "security_monitoring"
            ]),
            "operations_agent": MockAIAgent("Operations Agent", "System Operations Manager", [
                "system_monitoring", "incident_management", "deployment_automation",
                "log_analysis", "alerting_management"
            ]),
            "automation_agent": MockAIAgent("Automation Agent", "Workflow Automation Specialist", [
                "workflow_design", "process_automation", "trigger_management",
                "schedule_optimization", "integration_orchestration"
            ])
        }
        self.task_history = []
    
    async def process_user_request(self, request: str, context: Dict = None, source_page: str = "chat") -> Dict[str, Any]:
        """Coordinate processing of user request"""
        
        # Analyze intent and determine required agents
        required_agents = self._determine_required_agents(request, source_page)
        
        # Process with relevant agents
        agent_responses = {}
        for agent_name in required_agents:
            if agent_name in self.specialized_agents:
                agent = self.specialized_agents[agent_name]
                response = await agent.process_request(request, context)
                agent_responses[agent_name] = response
        
        # Synthesize final response
        final_response = self._synthesize_responses(request, agent_responses, context)
        
        # Store in history
        self._store_task_history(request, agent_responses, final_response)
        
        return final_response
    
    def _determine_required_agents(self, request: str, source_page: str) -> List[str]:
        """Determine which agents should handle the request"""
        required = ["chat_agent"]  # Always include chat agent
        
        request_lower = request.lower()
        
        # Map keywords to agents
        if any(word in request_lower for word in ["analyze", "data", "metrics", "report", "trends", "usage"]):
            required.append("analytics_agent")
        
        if any(word in request_lower for word in ["device", "iot", "sensor", "hardware", "configuration"]):
            required.append("device_agent")
        
        if any(word in request_lower for word in ["system", "operations", "deployment", "logs", "monitoring"]):
            required.append("operations_agent")
        
        if any(word in request_lower for word in ["automate", "workflow", "schedule", "trigger", "process"]):
            required.append("automation_agent")
        
        # Consider source page
        if source_page == "dashboard":
            if "analytics_agent" not in required:
                required.append("analytics_agent")
        elif source_page == "devices":
            if "device_agent" not in required:
                required.append("device_agent")
        elif source_page == "operations":
            if "operations_agent" not in required:
                required.append("operations_agent")
        elif source_page == "automation":
            if "automation_agent" not in required:
                required.append("automation_agent")
        
        return list(set(required))
    
    def _synthesize_responses(self, request: str, agent_responses: Dict, context: Dict) -> Dict[str, Any]:
        """Synthesize responses from multiple agents"""
        
        # Primary response from chat agent
        primary_response = agent_responses.get("chat_agent", {}).get("response", "")
        
        # Additional insights from specialized agents
        additional_insights = []
        for agent_name, response_data in agent_responses.items():
            if agent_name != "chat_agent":
                agent_name_clean = agent_name.replace("_agent", "").title()
                insight = f"**{agent_name_clean} Analysis:** {response_data['response']}"
                additional_insights.append(insight)
        
        # Combine responses
        if additional_insights:
            full_response = f"{primary_response}\n\n" + "\n\n".join(additional_insights)
        else:
            full_response = primary_response
        
        return {
            "success": True,
            "response": full_response,
            "agents_involved": list(agent_responses.keys()),
            "capabilities_used": self._aggregate_capabilities(agent_responses),
            "timestamp": datetime.now().isoformat(),
            "ai_generated": True,
            "source": "mock_ai_agents"
        }
    
    def _aggregate_capabilities(self, agent_responses: Dict) -> List[str]:
        """Aggregate capabilities used across all agents"""
        all_capabilities = []
        for response_data in agent_responses.values():
            all_capabilities.extend(response_data.get("capabilities_used", []))
        return list(set(all_capabilities))
    
    def _store_task_history(self, request: str, agent_responses: Dict, final_response: Dict):
        """Store task in history"""
        self.task_history.append({
            "request": request,
            "agents_involved": list(agent_responses.keys()),
            "timestamp": datetime.now().isoformat(),
            "success": final_response["success"]
        })
        
        # Keep only last 50 tasks
        if len(self.task_history) > 50:
            self.task_history = self.task_history[-50:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "status": "active",
            "total_agents": len(self.specialized_agents),
            "agents": {name: {"role": agent.role, "capabilities": len(agent.capabilities)} 
                     for name, agent in self.specialized_agents.items()},
            "tasks_completed": len(self.task_history),
            "last_activity": self.task_history[-1]["timestamp"] if self.task_history else None,
            "demo_mode": True
        }


# Global instance
mock_master_agent = MockMasterAgent()

# Flask integration functions
async def handle_ai_chat(message: str, session_id: str = None) -> Dict[str, Any]:
    """Handle AI chat request"""
    context = {"session_id": session_id or "demo", "source": "chat_interface"}
    return await mock_master_agent.process_user_request(message, context, "chat")

async def handle_ai_analytics(request: str) -> Dict[str, Any]:
    """Handle AI analytics request"""
    context = {"source": "analytics_dashboard"}
    return await mock_master_agent.process_user_request(request, context, "dashboard")

async def handle_ai_device(request: str) -> Dict[str, Any]:
    """Handle AI device management request"""
    context = {"source": "device_management"}
    return await mock_master_agent.process_user_request(request, context, "devices")

async def handle_ai_operations(request: str) -> Dict[str, Any]:
    """Handle AI operations request"""
    context = {"source": "operations_panel"}
    return await mock_master_agent.process_user_request(request, context, "operations")

async def handle_ai_automation(request: str) -> Dict[str, Any]:
    """Handle AI automation request"""
    context = {"source": "automation_dashboard"}
    return await mock_master_agent.process_user_request(request, context, "automation")

def get_ai_status() -> Dict[str, Any]:
    """Get AI system status"""
    return mock_master_agent.get_status()


if __name__ == "__main__":
    # Demo the system
    async def demo():
        print("=== AI Agents Demo ===")
        
        # Test different types of requests
        test_requests = [
            ("Hello, can you help me with API integration?", "chat"),
            ("Show me usage trends from this week", "dashboard"),
            ("Check the status of all IoT devices", "devices"),
            ("Analyze system performance logs", "operations"),
            ("Create an automated workflow for data backup", "automation"),
            ("Cross-page request: Transfer analytics data to automation", "chat")
        ]
        
        for request, source in test_requests:
            print(f"\n--- Request: {request} (from {source}) ---")
            response = await mock_master_agent.process_user_request(request, {}, source)
            print(f"Success: {response['success']}")
            print(f"Agents involved: {response['agents_involved']}")
            print(f"Capabilities used: {response['capabilities_used']}")
            print(f"Response: {response['response'][:200]}...")
        
        print(f"\n--- System Status ---")
        status = mock_master_agent.get_status()
        print(json.dumps(status, indent=2))
    
    # Run demo
    asyncio.run(demo())
