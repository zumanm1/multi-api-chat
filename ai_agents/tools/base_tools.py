"""
Base Tools for AI Agents
Provides shared functionality and tools that can be used by different agents
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .crewai_tools import BaseTool, tool


class AgentContextTool(BaseTool):
    """Tool for managing and accessing user context across agents"""
    
    name: str = "user_context_tool"
    description: str = "Access and manage user context information across the platform"
    
    def __init__(self):
        super().__init__()
        self.context_store: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
    
    def _run(self, action: str, key: str = None, value: Any = None, user_id: str = "default") -> str:
        """Execute context operations"""
        try:
            user_context = self.context_store.get(user_id, {})
            
            if action == "get":
                if key:
                    result = user_context.get(key, "No data found")
                else:
                    result = user_context
                return json.dumps(result, indent=2)
            
            elif action == "set":
                if key and value is not None:
                    user_context[key] = value
                    user_context["last_updated"] = datetime.now().isoformat()
                    self.context_store[user_id] = user_context
                    return f"Context updated: {key} = {value}"
                return "Error: Both key and value required for set operation"
            
            elif action == "append":
                if key and value is not None:
                    if key not in user_context:
                        user_context[key] = []
                    if isinstance(user_context[key], list):
                        user_context[key].append(value)
                        self.context_store[user_id] = user_context
                        return f"Added to {key}: {value}"
                    return f"Error: {key} is not a list"
                return "Error: Both key and value required for append operation"
            
            elif action == "clear":
                if key:
                    user_context.pop(key, None)
                    self.context_store[user_id] = user_context
                    return f"Cleared context key: {key}"
                else:
                    self.context_store[user_id] = {}
                    return "Cleared all context"
            
            else:
                return f"Unknown action: {action}. Available actions: get, set, append, clear"
        
        except Exception as e:
            self.logger.error(f"Context tool error: {str(e)}")
            return f"Error: {str(e)}"


class AgentCommunicationTool(BaseTool):
    """Tool for inter-agent communication and coordination"""
    
    name: str = "agent_communication_tool"
    description: str = "Facilitate communication and data sharing between different agents"
    
    def __init__(self):
        super().__init__()
        self.message_queue: Dict[str, List[Dict]] = {}
        self.logger = logging.getLogger(__name__)
    
    def _run(self, action: str, from_agent: str, to_agent: str = None, message: str = None, data: Any = None) -> str:
        """Execute agent communication operations"""
        try:
            if action == "send":
                if not all([to_agent, message]):
                    return "Error: to_agent and message are required for send action"
                
                if to_agent not in self.message_queue:
                    self.message_queue[to_agent] = []
                
                msg = {
                    "timestamp": datetime.now().isoformat(),
                    "from": from_agent,
                    "message": message,
                    "data": data
                }
                
                self.message_queue[to_agent].append(msg)
                return f"Message sent from {from_agent} to {to_agent}"
            
            elif action == "receive":
                messages = self.message_queue.get(from_agent, [])
                if messages:
                    # Return most recent message and remove it
                    msg = messages.pop(0)
                    return json.dumps(msg, indent=2)
                return "No messages"
            
            elif action == "check":
                count = len(self.message_queue.get(from_agent, []))
                return f"Messages waiting for {from_agent}: {count}"
            
            elif action == "broadcast":
                if not message:
                    return "Error: message required for broadcast action"
                
                broadcast_msg = {
                    "timestamp": datetime.now().isoformat(),
                    "from": from_agent,
                    "message": message,
                    "data": data,
                    "broadcast": True
                }
                
                # Send to all agents except sender
                for agent in self.message_queue:
                    if agent != from_agent:
                        self.message_queue[agent].append(broadcast_msg)
                
                return f"Broadcast sent from {from_agent} to all agents"
            
            else:
                return f"Unknown action: {action}. Available actions: send, receive, check, broadcast"
        
        except Exception as e:
            self.logger.error(f"Communication tool error: {str(e)}")
            return f"Error: {str(e)}"


class TaskSchedulerTool(BaseTool):
    """Tool for scheduling and managing tasks across agents"""
    
    name: str = "task_scheduler_tool"
    description: str = "Schedule, manage, and track tasks across the agent system"
    
    def __init__(self):
        super().__init__()
        self.scheduled_tasks: Dict[str, Dict] = {}
        self.task_history: List[Dict] = []
        self.logger = logging.getLogger(__name__)
    
    def _run(self, action: str, task_id: str = None, task_data: Dict = None, schedule_time: str = None) -> str:
        """Execute task scheduling operations"""
        try:
            if action == "schedule":
                if not all([task_id, task_data]):
                    return "Error: task_id and task_data are required for schedule action"
                
                task = {
                    "id": task_id,
                    "data": task_data,
                    "scheduled_time": schedule_time or datetime.now().isoformat(),
                    "status": "scheduled",
                    "created_at": datetime.now().isoformat()
                }
                
                self.scheduled_tasks[task_id] = task
                return f"Task {task_id} scheduled successfully"
            
            elif action == "get":
                if task_id:
                    task = self.scheduled_tasks.get(task_id, {})
                    return json.dumps(task, indent=2)
                else:
                    return json.dumps(list(self.scheduled_tasks.keys()))
            
            elif action == "update":
                if not all([task_id, task_data]):
                    return "Error: task_id and task_data are required for update action"
                
                if task_id in self.scheduled_tasks:
                    self.scheduled_tasks[task_id].update(task_data)
                    self.scheduled_tasks[task_id]["updated_at"] = datetime.now().isoformat()
                    return f"Task {task_id} updated successfully"
                return f"Task {task_id} not found"
            
            elif action == "complete":
                if task_id and task_id in self.scheduled_tasks:
                    task = self.scheduled_tasks.pop(task_id)
                    task["status"] = "completed"
                    task["completed_at"] = datetime.now().isoformat()
                    self.task_history.append(task)
                    return f"Task {task_id} marked as completed"
                return f"Task {task_id} not found"
            
            elif action == "cancel":
                if task_id and task_id in self.scheduled_tasks:
                    task = self.scheduled_tasks.pop(task_id)
                    task["status"] = "cancelled"
                    task["cancelled_at"] = datetime.now().isoformat()
                    self.task_history.append(task)
                    return f"Task {task_id} cancelled"
                return f"Task {task_id} not found"
            
            elif action == "history":
                return json.dumps(self.task_history[-10:], indent=2)  # Last 10 tasks
            
            else:
                return f"Unknown action: {action}. Available actions: schedule, get, update, complete, cancel, history"
        
        except Exception as e:
            self.logger.error(f"Scheduler tool error: {str(e)}")
            return f"Error: {str(e)}"


class ChatHistoryTool(BaseTool):
    """Tool for managing chat conversation history"""
    
    name: str = "chat_history_tool"
    description: str = "Access and manage chat conversation history and context"
    
    def __init__(self):
        super().__init__()
        self.conversations: Dict[str, List[Dict]] = {}
        self.logger = logging.getLogger(__name__)
    
    def _run(self, action: str, session_id: str = "default", message: Dict = None, limit: int = 10) -> str:
        """Execute chat history operations"""
        try:
            if action == "add":
                if not message:
                    return "Error: message is required for add action"
                
                if session_id not in self.conversations:
                    self.conversations[session_id] = []
                
                message["timestamp"] = datetime.now().isoformat()
                self.conversations[session_id].append(message)
                
                # Keep only last 100 messages per session
                if len(self.conversations[session_id]) > 100:
                    self.conversations[session_id] = self.conversations[session_id][-100:]
                
                return "Message added to chat history"
            
            elif action == "get":
                conversation = self.conversations.get(session_id, [])
                recent_messages = conversation[-limit:] if conversation else []
                return json.dumps(recent_messages, indent=2)
            
            elif action == "search":
                if not message or "query" not in message:
                    return "Error: query is required in message for search action"
                
                query = message["query"].lower()
                conversation = self.conversations.get(session_id, [])
                matching_messages = []
                
                for msg in conversation:
                    if query in msg.get("content", "").lower():
                        matching_messages.append(msg)
                
                return json.dumps(matching_messages[-limit:], indent=2)
            
            elif action == "clear":
                if session_id in self.conversations:
                    del self.conversations[session_id]
                    return f"Chat history cleared for session {session_id}"
                return f"No history found for session {session_id}"
            
            elif action == "stats":
                conversation = self.conversations.get(session_id, [])
                stats = {
                    "total_messages": len(conversation),
                    "session_start": conversation[0]["timestamp"] if conversation else None,
                    "last_message": conversation[-1]["timestamp"] if conversation else None,
                    "message_types": {}
                }
                
                for msg in conversation:
                    msg_type = msg.get("type", "unknown")
                    stats["message_types"][msg_type] = stats["message_types"].get(msg_type, 0) + 1
                
                return json.dumps(stats, indent=2)
            
            else:
                return f"Unknown action: {action}. Available actions: add, get, search, clear, stats"
        
        except Exception as e:
            self.logger.error(f"Chat history tool error: {str(e)}")
            return f"Error: {str(e)}"


class APIIntegrationTool(BaseTool):
    """Tool for managing API integrations and calls"""
    
    name: str = "api_integration_tool"
    description: str = "Manage API integrations and make external API calls"
    
    def __init__(self):
        super().__init__()
        self.api_cache: Dict[str, Dict] = {}
        self.rate_limits: Dict[str, List] = {}
        self.logger = logging.getLogger(__name__)
    
    def _run(self, action: str, api_name: str = None, endpoint: str = None, params: Dict = None, cache_duration: int = 300) -> str:
        """Execute API integration operations"""
        try:
            if action == "call":
                if not all([api_name, endpoint]):
                    return "Error: api_name and endpoint are required for call action"
                
                # Check rate limiting
                if self._is_rate_limited(api_name):
                    return f"Rate limit exceeded for {api_name}. Please wait before retrying."
                
                # Check cache
                cache_key = f"{api_name}:{endpoint}:{str(params)}"
                cached_result = self._get_cached_result(cache_key, cache_duration)
                if cached_result:
                    return f"Cached result: {json.dumps(cached_result, indent=2)}"
                
                # Simulate API call (in real implementation, make actual HTTP request)
                result = self._simulate_api_call(api_name, endpoint, params)
                
                # Cache result
                self._cache_result(cache_key, result)
                
                # Update rate limit
                self._update_rate_limit(api_name)
                
                return json.dumps(result, indent=2)
            
            elif action == "list_apis":
                # Return list of available APIs (mock data)
                apis = {
                    "openai": {"status": "active", "rate_limit": "100/hour"},
                    "anthropic": {"status": "active", "rate_limit": "50/hour"},
                    "google": {"status": "active", "rate_limit": "200/hour"},
                    "ollama": {"status": "active", "rate_limit": "unlimited"}
                }
                return json.dumps(apis, indent=2)
            
            elif action == "status":
                if api_name:
                    rate_limit_info = self._get_rate_limit_info(api_name)
                    return json.dumps({
                        "api": api_name,
                        "rate_limit_info": rate_limit_info,
                        "cache_entries": len([k for k in self.api_cache.keys() if k.startswith(f"{api_name}:")])
                    }, indent=2)
                return "Error: api_name is required for status action"
            
            elif action == "clear_cache":
                if api_name:
                    keys_to_remove = [k for k in self.api_cache.keys() if k.startswith(f"{api_name}:")]
                    for key in keys_to_remove:
                        del self.api_cache[key]
                    return f"Cache cleared for {api_name}"
                else:
                    self.api_cache.clear()
                    return "All cache cleared"
            
            else:
                return f"Unknown action: {action}. Available actions: call, list_apis, status, clear_cache"
        
        except Exception as e:
            self.logger.error(f"API integration tool error: {str(e)}")
            return f"Error: {str(e)}"
    
    def _simulate_api_call(self, api_name: str, endpoint: str, params: Dict = None) -> Dict:
        """Simulate an API call (replace with real implementation)"""
        return {
            "api": api_name,
            "endpoint": endpoint,
            "params": params or {},
            "response": f"Mock response from {api_name} {endpoint}",
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    
    def _is_rate_limited(self, api_name: str) -> bool:
        """Check if API is rate limited"""
        if api_name not in self.rate_limits:
            return False
        
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Remove old entries
        self.rate_limits[api_name] = [
            timestamp for timestamp in self.rate_limits[api_name]
            if datetime.fromisoformat(timestamp) > hour_ago
        ]
        
        # Check if limit exceeded (assume 100 calls per hour)
        return len(self.rate_limits[api_name]) >= 100
    
    def _update_rate_limit(self, api_name: str):
        """Update rate limit tracking"""
        if api_name not in self.rate_limits:
            self.rate_limits[api_name] = []
        
        self.rate_limits[api_name].append(datetime.now().isoformat())
    
    def _get_rate_limit_info(self, api_name: str) -> Dict:
        """Get rate limit information"""
        calls = self.rate_limits.get(api_name, [])
        return {
            "calls_last_hour": len(calls),
            "remaining": max(0, 100 - len(calls)),
            "reset_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
    
    def _get_cached_result(self, cache_key: str, cache_duration: int) -> Optional[Dict]:
        """Get cached result if valid"""
        if cache_key in self.api_cache:
            cached_data = self.api_cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data["cached_at"])
            
            if (datetime.now() - cache_time).total_seconds() < cache_duration:
                return cached_data["result"]
            else:
                # Remove expired cache
                del self.api_cache[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: Dict):
        """Cache API result"""
        self.api_cache[cache_key] = {
            "result": result,
            "cached_at": datetime.now().isoformat()
        }


# Tool registry for easy access
AVAILABLE_TOOLS = {
    "user_context_tool": AgentContextTool,
    "agent_communication_tool": AgentCommunicationTool,
    "task_scheduler_tool": TaskSchedulerTool,
    "chat_history_tool": ChatHistoryTool,
    "api_integration_tool": APIIntegrationTool,
    "context_memory_tool": AgentContextTool,  # Alias
    
    # Placeholder tools for agents (to be implemented)
    "data_analysis_tool": None,
    "chart_generator_tool": None,
    "metrics_collector_tool": None,
    "device_scanner_tool": None,
    "config_manager_tool": None,
    "health_monitor_tool": None,
    "system_monitor_tool": None,
    "log_analyzer_tool": None,
    "alert_manager_tool": None,
    "workflow_builder_tool": None,
    "scheduler_tool": TaskSchedulerTool,  # Alias
    "trigger_manager_tool": None,
    "api_manager_tool": APIIntegrationTool,  # Alias
    "db_optimizer_tool": None,
    "security_scanner_tool": None
}


def get_agent_tools(tool_names: List[str]) -> List[BaseTool]:
    """Get list of tool instances for an agent"""
    tools = []
    
    for tool_name in tool_names:
        if tool_name in AVAILABLE_TOOLS:
            tool_class = AVAILABLE_TOOLS[tool_name]
            if tool_class:
                tools.append(tool_class())
            else:
                logging.warning(f"Tool {tool_name} is not yet implemented")
        else:
            logging.warning(f"Unknown tool: {tool_name}")
    
    return tools


def register_tool(name: str, tool_class):
    """Register a new tool"""
    AVAILABLE_TOOLS[name] = tool_class


def list_available_tools() -> List[str]:
    """List all available tool names"""
    return list(AVAILABLE_TOOLS.keys())
