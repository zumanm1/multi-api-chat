#!/usr/bin/env python3
"""
Simplified Master AI Agent - Central Orchestrator
Coordinates and manages all AI agents across the Multi-API Chat Platform
No external dependencies for demo/testing purposes
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class SimpleMasterAgent:
    """Simplified Master AI Agent that orchestrates all other agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.task_history: List[Dict] = []
        self.context_memory: Dict[str, Any] = {}
        
        # Agent capabilities mapping
        self.agent_capabilities = {
            "chat_agent": ["conversation", "general_queries", "user_interaction"],
            "analytics_agent": ["data_analysis", "metrics", "reporting", "insights"],
            "device_agent": ["device_management", "iot", "monitoring", "configuration"],
            "operations_agent": ["system_monitoring", "health_checks", "infrastructure"],
            "automation_agent": ["workflow_automation", "process_optimization", "scheduling"]
        }
        
        self.logger.info("Simplified Master AI Agent initialized successfully")
    
    async def process_user_request(self, 
                                 request: str, 
                                 context: Dict[str, Any] = None,
                                 source_page: str = "chat") -> Dict[str, Any]:
        """Process user request and coordinate appropriate agents"""
        try:
            start_time = time.time()
            
            # Analyze user intent
            intent_analysis = self._analyze_user_intent(request, context, source_page)
            
            # Determine which agents to involve
            required_agents = self._determine_required_agents(intent_analysis)
            
            # Execute agent tasks
            results = await self._execute_agent_tasks(request, required_agents, context)
            
            # Synthesize final response
            final_response = self._synthesize_response(results, intent_analysis, request)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Store in task history
            self._store_task_history(request, intent_analysis, results, final_response, execution_time)
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error processing user request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while processing your request. Please try again.",
                "timestamp": datetime.now().isoformat(),
                "agent_type": "master_agent"
            }
    
    def _analyze_user_intent(self, 
                           request: str, 
                           context: Dict[str, Any],
                           source_page: str) -> Dict[str, Any]:
        """Analyze user intent and determine task requirements"""
        
        request_lower = request.lower()
        
        # Determine complexity based on keywords and length
        complexity = "simple"
        if len(request.split()) > 20 or any(word in request_lower for word in ["analyze", "compare", "complex", "detailed"]):
            complexity = "complex"
        elif any(word in request_lower for word in ["how", "what", "why", "explain"]):
            complexity = "moderate"
        
        # Determine urgency
        urgency = "low"
        if any(word in request_lower for word in ["urgent", "emergency", "critical", "immediate"]):
            urgency = "high"
        elif any(word in request_lower for word in ["soon", "quick", "fast"]):
            urgency = "medium"
        
        # Determine primary intent categories
        intents = []
        if any(word in request_lower for word in ["analyze", "data", "metrics", "report", "chart"]):
            intents.append("analytics")
        if any(word in request_lower for word in ["device", "iot", "sensor", "hardware", "monitor"]):
            intents.append("device_management")
        if any(word in request_lower for word in ["system", "operations", "health", "status", "performance"]):
            intents.append("operations")
        if any(word in request_lower for word in ["automate", "workflow", "schedule", "process"]):
            intents.append("automation")
        if not intents:  # Default to conversation
            intents.append("conversation")
        
        return {
            "primary_intent": intents[0] if intents else "conversation",
            "secondary_intents": intents[1:] if len(intents) > 1 else [],
            "complexity": complexity,
            "urgency": urgency,
            "source_page": source_page,
            "timestamp": datetime.now().isoformat(),
            "keywords": [word for word in request_lower.split() if len(word) > 3][:10]
        }
    
    def _determine_required_agents(self, intent_analysis: Dict[str, Any]) -> List[str]:
        """Determine which specialized agents are needed for the task"""
        required_agents = ["chat_agent"]  # Always include chat agent
        
        primary_intent = intent_analysis.get("primary_intent", "conversation")
        secondary_intents = intent_analysis.get("secondary_intents", [])
        
        # Map intents to agents
        intent_to_agent = {
            "analytics": "analytics_agent",
            "device_management": "device_agent", 
            "operations": "operations_agent",
            "automation": "automation_agent"
        }
        
        # Add primary agent
        if primary_intent in intent_to_agent:
            required_agents.append(intent_to_agent[primary_intent])
        
        # Add secondary agents
        for intent in secondary_intents:
            if intent in intent_to_agent and intent_to_agent[intent] not in required_agents:
                required_agents.append(intent_to_agent[intent])
        
        return list(set(required_agents))
    
    async def _execute_agent_tasks(self, 
                                 request: str,
                                 required_agents: List[str], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tasks using appropriate agents"""
        results = {}
        
        # Simulate parallel execution of agent tasks
        agent_tasks = []
        for agent_name in required_agents:
            task = self._create_agent_task(agent_name, request, context)
            agent_tasks.append(task)
        
        # Execute all tasks concurrently
        if agent_tasks:
            task_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(task_results):
                agent_name = required_agents[i]
                if isinstance(result, Exception):
                    results[agent_name] = {
                        "success": False,
                        "error": str(result),
                        "agent_type": agent_name
                    }
                else:
                    results[agent_name] = result
        
        return {
            "success": True,
            "agent_results": results,
            "agents_involved": required_agents,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _create_agent_task(self, 
                               agent_name: str, 
                               request: str, 
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Create and execute a task for a specific agent"""
        
        # Simulate processing time based on agent type
        processing_times = {
            "chat_agent": (0.5, 1.5),
            "analytics_agent": (1.0, 3.0),
            "device_agent": (0.8, 2.0),
            "operations_agent": (1.2, 2.5),
            "automation_agent": (1.5, 3.5)
        }
        
        min_time, max_time = processing_times.get(agent_name, (0.5, 2.0))
        processing_time = random.uniform(min_time, max_time)
        
        # Simulate processing delay
        await asyncio.sleep(processing_time)
        
        # Generate agent-specific response
        capabilities = self.agent_capabilities.get(agent_name, [])
        
        agent_responses = {
            "chat_agent": f"I understand your request: '{request}'. I'm ready to help with any questions or tasks you have.",
            "analytics_agent": f"I've analyzed your request and can provide insights on data patterns, metrics, and reporting for: '{request[:50]}...'",
            "device_agent": f"I can help with device management and IoT monitoring related to: '{request[:50]}...'",
            "operations_agent": f"I'm monitoring system operations and can provide health status and performance insights for: '{request[:50]}...'",
            "automation_agent": f"I can suggest automation workflows and process optimizations for: '{request[:50]}...'"
        }
        
        base_response = agent_responses.get(agent_name, f"Agent {agent_name} processed: {request}")
        
        return {
            "success": True,
            "response": base_response,
            "agent_type": agent_name,
            "capabilities_used": capabilities[:3],  # Limit to first 3 capabilities
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def _synthesize_response(self, 
                           results: Dict[str, Any], 
                           intent_analysis: Dict[str, Any],
                           original_request: str) -> Dict[str, Any]:
        """Synthesize final response from all agent results"""
        
        agent_results = results.get("agent_results", {})
        agents_involved = results.get("agents_involved", [])
        
        # Create comprehensive response
        response_parts = []
        
        # Add primary response (usually from chat agent)
        if "chat_agent" in agent_results and agent_results["chat_agent"].get("success"):
            response_parts.append(agent_results["chat_agent"]["response"])
        
        # Add specialized agent insights
        for agent_name in agents_involved:
            if agent_name != "chat_agent" and agent_name in agent_results:
                agent_result = agent_results[agent_name]
                if agent_result.get("success"):
                    response_parts.append(f"\n**{agent_name.replace('_', ' ').title()}:** {agent_result['response']}")
        
        # Combine responses
        final_response = "\n".join(response_parts) if response_parts else "I'm ready to help with your request."
        
        # Add system context if complex request
        if intent_analysis.get("complexity") == "complex":
            final_response += f"\n\n*This response involved coordination between {len(agents_involved)} specialized agents to provide comprehensive assistance.*"
        
        return {
            "success": True,
            "response": final_response,
            "agents_involved": agents_involved,
            "intent_analysis": intent_analysis,
            "timestamp": datetime.now().isoformat(),
            "agent_type": "master_agent",
            "capabilities_used": ["orchestration", "synthesis", "coordination"]
        }
    
    def _store_task_history(self, 
                          request: str, 
                          intent_analysis: Dict, 
                          results: Dict, 
                          final_response: Dict,
                          execution_time: float):
        """Store task execution history for learning and optimization"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "request": request[:100] + "..." if len(request) > 100 else request,
            "intent_analysis": intent_analysis,
            "agents_involved": results.get("agents_involved", []),
            "success": final_response.get("success", False),
            "response_length": len(final_response.get("response", "")),
            "execution_time": execution_time,
            "complexity": intent_analysis.get("complexity", "unknown"),
            "urgency": intent_analysis.get("urgency", "unknown")
        }
        
        self.task_history.append(history_entry)
        
        # Keep only last 50 entries to manage memory
        if len(self.task_history) > 50:
            self.task_history = self.task_history[-50:]
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        recent_tasks = [task for task in self.task_history if task["timestamp"] >= (datetime.now().isoformat()[:10])]
        
        return {
            "master_agent": {
                "status": "active",
                "tasks_completed_today": len(recent_tasks),
                "total_tasks": len(self.task_history),
                "last_activity": self.task_history[-1]["timestamp"] if self.task_history else None,
                "average_response_time": sum(task.get("execution_time", 0) for task in recent_tasks) / len(recent_tasks) if recent_tasks else 0
            },
            "specialized_agents": {
                agent_name: {
                    "status": "active", 
                    "capabilities": capabilities,
                    "role": agent_name.replace("_", " ").title()
                }
                for agent_name, capabilities in self.agent_capabilities.items()
            },
            "system_status": {
                "enabled": True,
                "demo_mode": True,
                "total_agents": len(self.agent_capabilities) + 1  # +1 for master agent
            },
            "performance_metrics": {
                "success_rate": len([t for t in recent_tasks if t.get("success", False)]) / len(recent_tasks) * 100 if recent_tasks else 100,
                "average_agents_per_task": sum(len(task.get("agents_involved", [])) for task in recent_tasks) / len(recent_tasks) if recent_tasks else 1,
                "complexity_distribution": {
                    level: len([t for t in recent_tasks if t.get("complexity") == level])
                    for level in ["simple", "moderate", "complex"]
                }
            }
        }
    
    async def handle_cross_page_request(self, 
                                      request: str, 
                                      source_page: str, 
                                      target_page: str, 
                                      context: Dict = None) -> Dict[str, Any]:
        """Handle requests that span multiple pages"""
        cross_page_context = {
            "source_page": source_page,
            "target_page": target_page,
            "cross_page_request": True,
            **(context or {})
        }
        
        # Add cross-page coordination message
        enhanced_request = f"[Cross-page request from {source_page} to {target_page}] {request}"
        
        result = await self.process_user_request(enhanced_request, cross_page_context, source_page)
        
        # Add cross-page specific information to response
        if result.get("success"):
            result["cross_page_info"] = {
                "source_page": source_page,
                "target_page": target_page,
                "coordination_successful": True
            }
        
        return result
    
    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task history"""
        return self.task_history[-limit:] if self.task_history else []
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of the master agent"""
        if not self.task_history:
            return {"status": "no_data", "message": "No tasks completed yet"}
        
        recent_tasks = self.task_history[-20:]  # Last 20 tasks
        
        return {
            "total_tasks_completed": len(self.task_history),
            "recent_performance": {
                "tasks_analyzed": len(recent_tasks),
                "average_execution_time": sum(task.get("execution_time", 0) for task in recent_tasks) / len(recent_tasks),
                "success_rate": len([t for t in recent_tasks if t.get("success", False)]) / len(recent_tasks) * 100,
                "most_used_agents": self._get_most_used_agents(recent_tasks)
            },
            "complexity_handled": {
                level: len([t for t in self.task_history if t.get("complexity") == level])
                for level in ["simple", "moderate", "complex"]
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_most_used_agents(self, tasks: List[Dict]) -> Dict[str, int]:
        """Get most frequently used agents from task history"""
        agent_usage = {}
        for task in tasks:
            agents = task.get("agents_involved", [])
            for agent in agents:
                agent_usage[agent] = agent_usage.get(agent, 0) + 1
        return dict(sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)[:5])


# Global master agent instance
_simple_master_agent_instance = None

def get_simple_master_agent() -> SimpleMasterAgent:
    """Get or create simple master agent instance"""
    global _simple_master_agent_instance
    if _simple_master_agent_instance is None:
        _simple_master_agent_instance = SimpleMasterAgent()
    return _simple_master_agent_instance

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_simple_master_agent():
        """Test the simple master agent"""
        print("Testing Simple Master Agent...")
        
        agent = get_simple_master_agent()
        
        # Test different types of requests
        test_requests = [
            "Hello, how are you?",
            "Can you analyze the system performance and provide a detailed report?",
            "I need help with device monitoring and automation workflows",
            "What's the current status of our operations and infrastructure?"
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n--- Test {i}: {request} ---")
            result = await agent.process_user_request(request)
            print(f"Success: {result.get('success')}")
            print(f"Response: {result.get('response', '')[:200]}...")
            print(f"Agents involved: {result.get('agents_involved', [])}")
            print(f"Execution time: {result.get('intent_analysis', {}).get('timestamp', 'N/A')}")
        
        # Show performance summary
        print("\n--- Performance Summary ---")
        summary = agent.get_performance_summary()
        print(json.dumps(summary, indent=2, default=str))
    
    # Run test
    asyncio.run(test_simple_master_agent())
