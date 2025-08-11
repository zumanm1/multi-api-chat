"""
Advanced AI Integration - Isolated module for complex AI features
This module is separate to avoid circular imports with the core server
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import traceback

logger = logging.getLogger(__name__)

class AdvancedAIIntegration:
    """Advanced AI integration class with isolated dependencies"""
    
    def __init__(self):
        self.initialized = False
        self.available_features = set()
        self.crew_ai = None
        self.langchain = None
        self.langgraph = None
        self.agents = {}
        self.workflows = {}
        self.status = "not_initialized"
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize advanced AI features safely"""
        try:
            logger.info("Initializing Advanced AI Integration...")
            
            # Import modules one by one to identify specific failures
            success_modules = []
            failed_modules = []
            
            # Test CrewAI
            try:
                import crewai
                from crewai import Agent, Task, Crew
                self.crew_ai = crewai
                success_modules.append("crewai")
                self.available_features.add("crew_ai")
                logger.info("✓ CrewAI module loaded successfully")
            except Exception as e:
                failed_modules.append(("crewai", str(e)))
                logger.warning(f"✗ CrewAI module failed: {e}")
            
            # Test LangChain
            try:
                import langchain
                from langchain.schema import BaseMessage
                self.langchain = langchain
                success_modules.append("langchain")
                self.available_features.add("langchain")
                logger.info("✓ LangChain module loaded successfully")
            except Exception as e:
                failed_modules.append(("langchain", str(e)))
                logger.warning(f"✗ LangChain module failed: {e}")
            
            # Test LangGraph (with careful error handling)
            try:
                import langgraph
                # Don't try to initialize complex graph structures yet
                success_modules.append("langgraph")
                self.available_features.add("langgraph")
                logger.info("✓ LangGraph module loaded successfully")
            except Exception as e:
                failed_modules.append(("langgraph", str(e)))
                logger.warning(f"✗ LangGraph module failed: {e}")
            
            # Test LangChain OpenAI
            try:
                import langchain_openai
                success_modules.append("langchain_openai")
                self.available_features.add("langchain_openai")
                logger.info("✓ LangChain OpenAI module loaded successfully")
            except Exception as e:
                failed_modules.append(("langchain_openai", str(e)))
                logger.warning(f"✗ LangChain OpenAI module failed: {e}")
            
            self.initialized = len(success_modules) > 0
            self.status = "partially_initialized" if failed_modules else "fully_initialized"
            
            result = {
                "success": self.initialized,
                "status": self.status,
                "available_features": list(self.available_features),
                "successful_modules": success_modules,
                "failed_modules": failed_modules,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.initialized:
                logger.info(f"✓ Advanced AI Integration initialized with {len(success_modules)} modules")
            else:
                logger.error("✗ Advanced AI Integration failed to initialize any modules")
            
            return result
            
        except Exception as e:
            logger.error(f"Critical error in Advanced AI Integration: {e}")
            logger.debug(traceback.format_exc())
            self.status = "failed"
            return {
                "success": False,
                "status": "failed",
                "error": str(e),
                "available_features": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def create_simple_agent(self, name: str, role: str, goal: str, backstory: str) -> Dict[str, Any]:
        """Create a simple AI agent if CrewAI is available"""
        if "crew_ai" not in self.available_features:
            return {
                "success": False,
                "error": "CrewAI not available",
                "agent_id": None
            }
        
        try:
            from crewai import Agent
            
            agent = Agent(
                role=role,
                goal=goal,
                backstory=backstory,
                verbose=True,
                allow_delegation=False
            )
            
            agent_id = f"agent_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.agents[agent_id] = {
                "agent": agent,
                "name": name,
                "role": role,
                "goal": goal,
                "backstory": backstory,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"✓ Created agent: {name} ({agent_id})")
            
            return {
                "success": True,
                "agent_id": agent_id,
                "name": name,
                "role": role,
                "created_at": self.agents[agent_id]["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to create agent {name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": None
            }
    
    def execute_simple_task(self, agent_id: str, task_description: str) -> Dict[str, Any]:
        """Execute a simple task with an agent"""
        if agent_id not in self.agents:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found",
                "result": None
            }
        
        if "crew_ai" not in self.available_features:
            return {
                "success": False,
                "error": "CrewAI not available for task execution",
                "result": None
            }
        
        try:
            from crewai import Task, Crew
            
            agent_data = self.agents[agent_id]
            agent = agent_data["agent"]
            
            task = Task(
                description=task_description,
                agent=agent,
                expected_output="A detailed response to the task"
            )
            
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True
            )
            
            # Execute the crew
            result = crew.kickoff()
            
            execution_record = {
                "task_description": task_description,
                "agent_name": agent_data["name"],
                "result": str(result),
                "executed_at": datetime.now().isoformat(),
                "success": True
            }
            
            logger.info(f"✓ Task executed successfully by {agent_data['name']}")
            
            return {
                "success": True,
                "result": str(result),
                "execution_record": execution_record
            }
            
        except Exception as e:
            logger.error(f"Failed to execute task with agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of advanced AI integration"""
        return {
            "initialized": self.initialized,
            "status": self.status,
            "available_features": list(self.available_features),
            "agents_count": len(self.agents),
            "workflows_count": len(self.workflows),
            "feature_details": {
                "crew_ai_available": "crew_ai" in self.available_features,
                "langchain_available": "langchain" in self.available_features,
                "langgraph_available": "langgraph" in self.available_features,
                "langchain_openai_available": "langchain_openai" in self.available_features,
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Advanced health check"""
        return {
            "healthy": self.initialized and self.status != "failed",
            "status": self.status,
            "features_available": len(self.available_features),
            "agents_active": len(self.agents),
            "ready_for_tasks": "crew_ai" in self.available_features,
            "timestamp": datetime.now().isoformat()
        }

# Global instance (initialized lazily)
_advanced_ai = None

def get_advanced_ai() -> AdvancedAIIntegration:
    """Get the global AdvancedAIIntegration instance"""
    global _advanced_ai
    if _advanced_ai is None:
        _advanced_ai = AdvancedAIIntegration()
    return _advanced_ai

def initialize_advanced_ai() -> Dict[str, Any]:
    """Initialize advanced AI integration"""
    ai = get_advanced_ai()
    return ai.initialize()

def is_advanced_ai_available() -> bool:
    """Check if advanced AI features are available"""
    ai = get_advanced_ai()
    return ai.initialized

def get_advanced_ai_status() -> Dict[str, Any]:
    """Get advanced AI status"""
    ai = get_advanced_ai()
    return ai.get_status()

# Convenience functions for external use
def create_ai_agent(name: str, role: str, goal: str, backstory: str) -> Dict[str, Any]:
    """Create an AI agent (wrapper function)"""
    ai = get_advanced_ai()
    if not ai.initialized:
        init_result = ai.initialize()
        if not init_result["success"]:
            return init_result
    
    return ai.create_simple_agent(name, role, goal, backstory)

def execute_ai_task(agent_id: str, task_description: str) -> Dict[str, Any]:
    """Execute a task with an AI agent (wrapper function)"""
    ai = get_advanced_ai()
    if not ai.initialized:
        return {
            "success": False,
            "error": "Advanced AI not initialized",
            "result": None
        }
    
    return ai.execute_simple_task(agent_id, task_description)
