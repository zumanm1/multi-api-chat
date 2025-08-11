"""
Base Tools for AI Agents
Provides shared functionality and tools that can be used by different agents
Supports both CrewAI tools and fallback implementations
"""

import json
import logging
import asyncio
import sqlite3
import requests
import subprocess
import os
import sys
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

# Try to import actual CrewAI tools, fall back to our implementation
try:
    from crewai_tools import BaseTool, Tool
    from crewai.tools import tool
    CREWAI_AVAILABLE = True
    print("CrewAI tools imported successfully")
except ImportError:
    from .crewai_tools import BaseTool, tool
    Tool = BaseTool  # Alias for compatibility
    CREWAI_AVAILABLE = False
    print("Using fallback tool implementations")

# Platform context and session data
class PlatformContext:
    """Manages platform context and session data"""
    
    def __init__(self):
        self.session_data = {}
        self.user_preferences = {}
        self.api_keys = {}
        self.database_connections = {}
        self.device_inventory = {}
        self.automation_rules = {}
        
    def get_session_data(self, key: str, default=None):
        return self.session_data.get(key, default)
    
    def set_session_data(self, key: str, value: Any):
        self.session_data[key] = value
    
    def get_api_key(self, service: str) -> Optional[str]:
        return self.api_keys.get(service)
    
    def set_api_key(self, service: str, key: str):
        self.api_keys[service] = key

# Global platform context instance
platform_context = PlatformContext()


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


class DataAnalysisTool(BaseTool):
    """Tool for analyzing data with various statistical and ML methods"""
    
    name: str = "data_analysis_tool"
    description: str = "Analyze data using statistical methods, create visualizations, and generate insights"
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
    def _run(self, action: str, data: Any = None, analysis_type: str = "basic", parameters: Dict = None) -> str:
        """Execute data analysis operations"""
        try:
            if action == "analyze":
                if not data:
                    return "Error: data is required for analyze action"
                
                result = self._perform_analysis(data, analysis_type, parameters or {})
                return json.dumps(result, indent=2)
            
            elif action == "visualize":
                if not data:
                    return "Error: data is required for visualize action"
                
                chart_path = self._generate_visualization(data, parameters or {})
                return f"Visualization generated: {chart_path}"
            
            elif action == "summary":
                if not data:
                    return "Error: data is required for summary action"
                
                summary = self._generate_summary(data)
                return json.dumps(summary, indent=2)
            
            elif action == "correlation":
                if not data:
                    return "Error: data is required for correlation action"
                
                correlations = self._calculate_correlations(data)
                return json.dumps(correlations, indent=2)
            
            else:
                return f"Unknown action: {action}. Available actions: analyze, visualize, summary, correlation"
        
        except Exception as e:
            self.logger.error(f"Data analysis tool error: {str(e)}")
            return f"Error: {str(e)}"
    
    def _perform_analysis(self, data, analysis_type: str, parameters: Dict) -> Dict:
        """Perform statistical analysis on data"""
        # Simulate data analysis (in real implementation, use pandas, scipy, etc.)
        return {
            "analysis_type": analysis_type,
            "data_points": len(data) if hasattr(data, '__len__') else 1,
            "timestamp": datetime.now().isoformat(),
            "results": f"Analysis completed using {analysis_type} method",
            "parameters": parameters
        }
    
    def _generate_visualization(self, data, parameters: Dict) -> str:
        """Generate data visualization"""
        # Simulate chart generation
        chart_type = parameters.get('chart_type', 'line')
        filename = f"chart_{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        return f"/tmp/{filename}"
    
    def _generate_summary(self, data) -> Dict:
        """Generate data summary statistics"""
        return {
            "count": len(data) if hasattr(data, '__len__') else 1,
            "timestamp": datetime.now().isoformat(),
            "data_type": str(type(data).__name__),
            "summary": "Basic statistical summary generated"
        }
    
    def _calculate_correlations(self, data) -> Dict:
        """Calculate correlations in dataset"""
        return {
            "correlation_method": "pearson",
            "timestamp": datetime.now().isoformat(),
            "correlations": "Correlation matrix calculated"
        }


class DeviceManagementTool(BaseTool):
    """Tool for managing network devices and infrastructure"""
    
    name: str = "device_management_tool"
    description: str = "Manage network devices, perform configuration tasks, and monitor device health"
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.device_inventory = platform_context.device_inventory
        
    def _run(self, action: str, device_id: str = None, command: str = None, config: Dict = None) -> str:
        """Execute device management operations"""
        try:
            if action == "scan":
                devices = self._scan_devices()
                return json.dumps(devices, indent=2)
            
            elif action == "connect":
                if not device_id:
                    return "Error: device_id is required for connect action"
                
                result = self._connect_device(device_id)
                return json.dumps(result, indent=2)
            
            elif action == "execute":
                if not all([device_id, command]):
                    return "Error: device_id and command are required for execute action"
                
                result = self._execute_command(device_id, command)
                return json.dumps(result, indent=2)
            
            elif action == "configure":
                if not all([device_id, config]):
                    return "Error: device_id and config are required for configure action"
                
                result = self._apply_configuration(device_id, config)
                return json.dumps(result, indent=2)
            
            elif action == "health_check":
                if not device_id:
                    return "Error: device_id is required for health_check action"
                
                health = self._check_device_health(device_id)
                return json.dumps(health, indent=2)
            
            elif action == "backup_config":
                if not device_id:
                    return "Error: device_id is required for backup_config action"
                
                result = self._backup_configuration(device_id)
                return json.dumps(result, indent=2)
            
            else:
                return f"Unknown action: {action}. Available actions: scan, connect, execute, configure, health_check, backup_config"
        
        except Exception as e:
            self.logger.error(f"Device management tool error: {str(e)}")
            return f"Error: {str(e)}"
    
    def _scan_devices(self) -> List[Dict]:
        """Scan network for devices"""
        # Simulate device scanning
        return [
            {"id": "device_1", "ip": "192.168.1.10", "type": "switch", "status": "online"},
            {"id": "device_2", "ip": "192.168.1.11", "type": "router", "status": "online"},
            {"id": "device_3", "ip": "192.168.1.12", "type": "firewall", "status": "offline"}
        ]
    
    def _connect_device(self, device_id: str) -> Dict:
        """Connect to a device using telnet (per user preference)"""
        # Simulate device connection using telnet
        return {
            "device_id": device_id,
            "connection_method": "telnet",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_command(self, device_id: str, command: str) -> Dict:
        """Execute command on device"""
        return {
            "device_id": device_id,
            "command": command,
            "output": f"Command '{command}' executed successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    def _apply_configuration(self, device_id: str, config: Dict) -> Dict:
        """Apply configuration to device"""
        return {
            "device_id": device_id,
            "config_applied": config,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_device_health(self, device_id: str) -> Dict:
        """Check device health status"""
        return {
            "device_id": device_id,
            "cpu_usage": "25%",
            "memory_usage": "60%",
            "uptime": "7 days, 14 hours",
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    
    def _backup_configuration(self, device_id: str) -> Dict:
        """Backup device configuration"""
        backup_file = f"backup_{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cfg"
        return {
            "device_id": device_id,
            "backup_file": backup_file,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }


class AutomationTool(BaseTool):
    """Tool for workflow automation and task orchestration"""
    
    name: str = "automation_tool"
    description: str = "Create, manage, and execute automated workflows and tasks"
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.workflows = {}
        self.automation_rules = platform_context.automation_rules
        
    def _run(self, action: str, workflow_id: str = None, workflow_data: Dict = None, trigger: Dict = None) -> str:
        """Execute automation operations"""
        try:
            if action == "create_workflow":
                if not all([workflow_id, workflow_data]):
                    return "Error: workflow_id and workflow_data are required for create_workflow action"
                
                result = self._create_workflow(workflow_id, workflow_data)
                return json.dumps(result, indent=2)
            
            elif action == "execute_workflow":
                if not workflow_id:
                    return "Error: workflow_id is required for execute_workflow action"
                
                result = self._execute_workflow(workflow_id)
                return json.dumps(result, indent=2)
            
            elif action == "schedule_workflow":
                if not all([workflow_id, trigger]):
                    return "Error: workflow_id and trigger are required for schedule_workflow action"
                
                result = self._schedule_workflow(workflow_id, trigger)
                return json.dumps(result, indent=2)
            
            elif action == "list_workflows":
                return json.dumps(list(self.workflows.keys()), indent=2)
            
            elif action == "get_workflow":
                if not workflow_id:
                    return "Error: workflow_id is required for get_workflow action"
                
                workflow = self.workflows.get(workflow_id, {})
                return json.dumps(workflow, indent=2)
            
            elif action == "delete_workflow":
                if not workflow_id:
                    return "Error: workflow_id is required for delete_workflow action"
                
                if workflow_id in self.workflows:
                    del self.workflows[workflow_id]
                    return f"Workflow {workflow_id} deleted successfully"
                return f"Workflow {workflow_id} not found"
            
            elif action == "create_rule":
                if not all([workflow_id, trigger]):
                    return "Error: workflow_id and trigger are required for create_rule action"
                
                result = self._create_automation_rule(workflow_id, trigger)
                return json.dumps(result, indent=2)
            
            else:
                return f"Unknown action: {action}. Available actions: create_workflow, execute_workflow, schedule_workflow, list_workflows, get_workflow, delete_workflow, create_rule"
        
        except Exception as e:
            self.logger.error(f"Automation tool error: {str(e)}")
            return f"Error: {str(e)}"
    
    def _create_workflow(self, workflow_id: str, workflow_data: Dict) -> Dict:
        """Create a new automation workflow"""
        workflow = {
            "id": workflow_id,
            "name": workflow_data.get("name", workflow_id),
            "description": workflow_data.get("description", ""),
            "steps": workflow_data.get("steps", []),
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }
        
        self.workflows[workflow_id] = workflow
        return workflow
    
    def _execute_workflow(self, workflow_id: str) -> Dict:
        """Execute an automation workflow"""
        if workflow_id not in self.workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        workflow = self.workflows[workflow_id]
        
        # Simulate workflow execution
        execution_result = {
            "workflow_id": workflow_id,
            "execution_id": f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "steps_executed": len(workflow.get("steps", [])),
            "results": "All workflow steps completed successfully"
        }
        
        return execution_result
    
    def _schedule_workflow(self, workflow_id: str, trigger: Dict) -> Dict:
        """Schedule a workflow for execution"""
        if workflow_id not in self.workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        schedule_info = {
            "workflow_id": workflow_id,
            "trigger": trigger,
            "scheduled_at": datetime.now().isoformat(),
            "next_execution": trigger.get("next_run", "Not specified"),
            "status": "scheduled"
        }
        
        return schedule_info
    
    def _create_automation_rule(self, workflow_id: str, trigger: Dict) -> Dict:
        """Create an automation rule"""
        rule_id = f"rule_{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        rule = {
            "id": rule_id,
            "workflow_id": workflow_id,
            "trigger": trigger,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.automation_rules[rule_id] = rule
        return rule


class DatabaseTool(BaseTool):
    """Tool for database operations with SQLite and other databases"""
    
    name: str = "database_tool"
    description: str = "Perform database operations including queries, updates, and schema management"
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.connections = platform_context.database_connections
        
    def _run(self, action: str, db_name: str = "default", query: str = None, params: Dict = None) -> str:
        """Execute database operations"""
        try:
            if action == "connect":
                if not db_name:
                    return "Error: db_name is required for connect action"
                
                result = self._connect_database(db_name)
                return json.dumps(result, indent=2)
            
            elif action == "query":
                if not query:
                    return "Error: query is required for query action"
                
                result = self._execute_query(db_name, query, params or {})
                return json.dumps(result, indent=2)
            
            elif action == "execute":
                if not query:
                    return "Error: query is required for execute action"
                
                result = self._execute_statement(db_name, query, params or {})
                return json.dumps(result, indent=2)
            
            elif action == "create_table":
                if not all([query]):
                    return "Error: query (CREATE TABLE statement) is required"
                
                result = self._create_table(db_name, query)
                return json.dumps(result, indent=2)
            
            elif action == "backup":
                result = self._backup_database(db_name)
                return json.dumps(result, indent=2)
            
            elif action == "optimize":
                result = self._optimize_database(db_name)
                return json.dumps(result, indent=2)
            
            else:
                return f"Unknown action: {action}. Available actions: connect, query, execute, create_table, backup, optimize"
        
        except Exception as e:
            self.logger.error(f"Database tool error: {str(e)}")
            return f"Error: {str(e)}"
    
    def _connect_database(self, db_name: str) -> Dict:
        """Connect to database"""
        # Simulate database connection (SQLite for simplicity)
        db_path = f"{db_name}.db" if not db_name.endswith('.db') else db_name
        
        connection_info = {
            "database": db_name,
            "type": "sqlite",
            "path": db_path,
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        }
        
        self.connections[db_name] = connection_info
        return connection_info
    
    def _execute_query(self, db_name: str, query: str, params: Dict) -> Dict:
        """Execute SELECT query"""
        return {
            "database": db_name,
            "query": query,
            "parameters": params,
            "rows_returned": 10,  # Simulated
            "execution_time": "0.05s",
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_statement(self, db_name: str, query: str, params: Dict) -> Dict:
        """Execute INSERT/UPDATE/DELETE statement"""
        return {
            "database": db_name,
            "query": query,
            "parameters": params,
            "rows_affected": 5,  # Simulated
            "execution_time": "0.02s",
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_table(self, db_name: str, create_statement: str) -> Dict:
        """Create database table"""
        return {
            "database": db_name,
            "statement": create_statement,
            "status": "table_created",
            "timestamp": datetime.now().isoformat()
        }
    
    def _backup_database(self, db_name: str) -> Dict:
        """Backup database"""
        backup_file = f"backup_{db_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        return {
            "database": db_name,
            "backup_file": backup_file,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    
    def _optimize_database(self, db_name: str) -> Dict:
        """Optimize database performance"""
        return {
            "database": db_name,
            "optimization": "VACUUM and ANALYZE completed",
            "status": "optimized",
            "timestamp": datetime.now().isoformat()
        }


# Enhanced functional tools using decorators
@tool
def api_call_tool(url: str, method: str = "GET", headers: Dict = None, data: Dict = None) -> str:
    """Make HTTP API calls with proper error handling and caching"""
    try:
        # Get API key from platform context if needed
        auth_headers = headers or {}
        
        # Simulate HTTP request (in real implementation, use requests library)
        response_data = {
            "url": url,
            "method": method,
            "headers": auth_headers,
            "data": data,
            "status_code": 200,
            "response": f"Mock response from {url}",
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response_data, indent=2)
    except Exception as e:
        return f"API call error: {str(e)}"


@tool
def file_operations_tool(action: str, file_path: str, content: str = None) -> str:
    """Perform file operations safely within the platform context"""
    try:
        if action == "read":
            # Simulate file reading
            return f"Content of {file_path}: Mock file content"
        
        elif action == "write":
            if not content:
                return "Error: content is required for write action"
            # Simulate file writing
            return f"Successfully wrote {len(content)} characters to {file_path}"
        
        elif action == "exists":
            # Simulate file existence check
            return f"File {file_path} exists: True"
        
        elif action == "delete":
            # Simulate file deletion
            return f"File {file_path} deleted successfully"
        
        else:
            return f"Unknown action: {action}. Available actions: read, write, exists, delete"
    
    except Exception as e:
        return f"File operation error: {str(e)}"


@tool
def system_info_tool(info_type: str = "general") -> str:
    """Get system information and metrics"""
    try:
        if info_type == "general":
            system_info = {
                "platform": sys.platform,
                "python_version": sys.version,
                "timestamp": datetime.now().isoformat()
            }
        
        elif info_type == "resources":
            system_info = {
                "cpu_count": os.cpu_count(),
                "current_directory": os.getcwd(),
                "environment_variables": len(os.environ),
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            system_info = {"error": f"Unknown info_type: {info_type}"}
        
        return json.dumps(system_info, indent=2)
    
    except Exception as e:
        return f"System info error: {str(e)}"


# Tool registry for easy access
AVAILABLE_TOOLS = {
    "user_context_tool": AgentContextTool,
    "agent_communication_tool": AgentCommunicationTool,
    "task_scheduler_tool": TaskSchedulerTool,
    "chat_history_tool": ChatHistoryTool,
    "api_integration_tool": APIIntegrationTool,
    "context_memory_tool": AgentContextTool,  # Alias
    
    # New specialized tools
    "data_analysis_tool": DataAnalysisTool,
    "device_management_tool": DeviceManagementTool,
    "automation_tool": AutomationTool,
    "database_tool": DatabaseTool,
    
    # Functional tools
    "api_call_tool": api_call_tool,
    "file_operations_tool": file_operations_tool,
    "system_info_tool": system_info_tool,
    
    # Aliases and additional tool mappings
    "chart_generator_tool": DataAnalysisTool,  # Alias
    "metrics_collector_tool": DataAnalysisTool,  # Alias
    "device_scanner_tool": DeviceManagementTool,  # Alias
    "config_manager_tool": DeviceManagementTool,  # Alias
    "health_monitor_tool": DeviceManagementTool,  # Alias
    "system_monitor_tool": system_info_tool,
    "log_analyzer_tool": DataAnalysisTool,  # Alias
    "alert_manager_tool": AutomationTool,  # Alias
    "workflow_builder_tool": AutomationTool,  # Alias
    "scheduler_tool": TaskSchedulerTool,  # Alias
    "trigger_manager_tool": AutomationTool,  # Alias
    "api_manager_tool": APIIntegrationTool,  # Alias
    "db_optimizer_tool": DatabaseTool,  # Alias
    "security_scanner_tool": DeviceManagementTool,  # Alias
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


def get_tool_info(tool_name: str) -> Dict[str, Any]:
    """Get information about a specific tool"""
    if tool_name not in AVAILABLE_TOOLS:
        return {"error": f"Tool {tool_name} not found"}
    
    tool_class = AVAILABLE_TOOLS[tool_name]
    if tool_class is None:
        return {
            "name": tool_name,
            "status": "not_implemented",
            "description": "Tool placeholder - not yet implemented"
        }
    
    # For class-based tools
    if hasattr(tool_class, 'name') and hasattr(tool_class, 'description'):
        return {
            "name": getattr(tool_class, 'name', tool_name),
            "description": getattr(tool_class, 'description', 'No description available'),
            "status": "available",
            "type": "class_based",
            "crewai_compatible": CREWAI_AVAILABLE
        }
    
    # For function-based tools
    if callable(tool_class):
        return {
            "name": tool_name,
            "description": getattr(tool_class, '__doc__', 'No description available'),
            "status": "available", 
            "type": "function_based",
            "crewai_compatible": CREWAI_AVAILABLE
        }
    
    return {
        "name": tool_name,
        "status": "unknown",
        "description": "Unable to determine tool information"
    }


def get_tools_by_category() -> Dict[str, List[str]]:
    """Get tools organized by category"""
    categories = {
        "core": [
            "user_context_tool", "agent_communication_tool", 
            "task_scheduler_tool", "chat_history_tool"
        ],
        "api_integration": [
            "api_integration_tool", "api_call_tool", "api_manager_tool"
        ],
        "data_analysis": [
            "data_analysis_tool", "chart_generator_tool", 
            "metrics_collector_tool", "log_analyzer_tool"
        ],
        "device_management": [
            "device_management_tool", "device_scanner_tool", 
            "config_manager_tool", "health_monitor_tool", "security_scanner_tool"
        ],
        "automation": [
            "automation_tool", "workflow_builder_tool", 
            "alert_manager_tool", "trigger_manager_tool"
        ],
        "database": [
            "database_tool", "db_optimizer_tool"
        ],
        "system": [
            "system_info_tool", "system_monitor_tool", "file_operations_tool"
        ]
    }
    
    return categories


def initialize_platform_context():
    """Initialize platform context with default values"""
    global platform_context
    
    # Set default user preferences based on rules
    platform_context.user_preferences.update({
        "connection_method": "telnet",  # User prefers telnet over SSH
        "python_version": "3.11",      # User prefers Python 3.11
        "testing_framework": "pytest", # User uses pytest for testing
        "tech_stack": {
            "backend": ["Python", "Flask", "Streamlit"],
            "frontend": ["Bootstrap", "Jinja2"],
            "networking": ["Netmiko", "Nornir"],
            "ai": ["Ollama", "CrewAI"],
            "database": ["ChromaDB", "SQLite"]
        },
        "deployment": "no_docker"  # User prefers not to use Docker
    })
    
    # Initialize API keys placeholders
    platform_context.api_keys.update({
        "openai": None,
        "anthropic": None, 
        "google": None,
        "ollama": "local"  # Local Ollama instance
    })
    
    logging.info("Platform context initialized successfully")


def create_crewai_compatible_tool(tool_class_or_func, tool_name: str = None):
    """Create a CrewAI-compatible tool wrapper"""
    
    if CREWAI_AVAILABLE:
        # If CrewAI is available, create proper CrewAI tool
        if isinstance(tool_class_or_func, type) and issubclass(tool_class_or_func, BaseTool):
            # For class-based tools, create wrapper
            class CrewAIToolWrapper(Tool):
                name = tool_name or getattr(tool_class_or_func, 'name', 'unnamed_tool')
                description = getattr(tool_class_or_func, 'description', 'Tool description')
                
                def _run(self, *args, **kwargs):
                    tool_instance = tool_class_or_func()
                    return tool_instance._run(*args, **kwargs)
            
            return CrewAIToolWrapper()
        
        elif callable(tool_class_or_func):
            # For function-based tools, use as-is with CrewAI decorator
            return tool(tool_class_or_func)
    
    # Fallback to our implementation
    return tool_class_or_func


def validate_tool_dependencies() -> Dict[str, Any]:
    """Validate that all required dependencies are available"""
    dependencies = {
        "crewai": CREWAI_AVAILABLE,
        "json": True,  # Built-in
        "logging": True,  # Built-in
        "datetime": True,  # Built-in
        "os": True,  # Built-in
        "sys": True,  # Built-in
    }
    
    optional_dependencies = {}
    
    # Check optional dependencies
    try:
        import requests
        optional_dependencies["requests"] = True
    except ImportError:
        optional_dependencies["requests"] = False
    
    try:
        import sqlite3
        optional_dependencies["sqlite3"] = True
    except ImportError:
        optional_dependencies["sqlite3"] = False
    
    try:
        import pandas
        optional_dependencies["pandas"] = True
    except ImportError:
        optional_dependencies["pandas"] = False
    
    try:
        import netmiko
        optional_dependencies["netmiko"] = True
    except ImportError:
        optional_dependencies["netmiko"] = False
    
    return {
        "required": dependencies,
        "optional": optional_dependencies,
        "crewai_available": CREWAI_AVAILABLE,
        "total_tools": len(AVAILABLE_TOOLS),
        "implemented_tools": len([t for t in AVAILABLE_TOOLS.values() if t is not None])
    }


def get_platform_status() -> Dict[str, Any]:
    """Get comprehensive platform and tools status"""
    return {
        "platform_context": {
            "session_data_keys": len(platform_context.session_data),
            "api_keys_configured": len([k for k, v in platform_context.api_keys.items() if v]),
            "database_connections": len(platform_context.database_connections),
            "device_inventory": len(platform_context.device_inventory),
            "automation_rules": len(platform_context.automation_rules)
        },
        "tools": {
            "total_available": len(AVAILABLE_TOOLS),
            "implemented": len([t for t in AVAILABLE_TOOLS.values() if t is not None]),
            "categories": len(get_tools_by_category())
        },
        "dependencies": validate_tool_dependencies(),
        "user_preferences": platform_context.user_preferences,
        "timestamp": datetime.now().isoformat()
    }


# Initialize platform context on module load
initialize_platform_context()
