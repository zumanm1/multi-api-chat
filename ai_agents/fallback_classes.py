"""
CrewAI Fallback Implementation Classes
====================================

This module provides fallback implementations for CrewAI components when the actual
CrewAI library and its dependencies are not installed. These classes maintain the
same interface but provide basic functionality to keep the application running.

Features:
- Same method signatures as real CrewAI classes
- Proper logging when fallback mode is active
- Consistent return types for compatibility
- Graceful degradation of AI functionality
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

# Flag to track if fallback warnings have been shown
_fallback_warnings_shown = set()


def _log_fallback_warning(component_name: str, method_name: str = None):
    """Log a warning about fallback mode usage"""
    warning_key = f"{component_name}.{method_name}" if method_name else component_name
    if warning_key not in _fallback_warnings_shown:
        if method_name:
            logger.warning(f"Using fallback implementation for {component_name}.{method_name}() - AI functionality not available")
        else:
            logger.warning(f"Using fallback implementation for {component_name} - AI functionality not available")
        _fallback_warnings_shown.add(warning_key)


class FallbackAgent:
    """
    Fallback implementation of CrewAI Agent class
    
    Provides the same interface as crewai.Agent but returns appropriate
    default responses when AI features are not available.
    """
    
    def __init__(self, 
                 role: str = None,
                 goal: str = None, 
                 backstory: str = None,
                 verbose: bool = True,
                 memory: bool = True,
                 tools: List = None,
                 llm: Any = None,
                 max_execution_time: Optional[int] = None,
                 **kwargs):
        """Initialize fallback agent with same parameters as CrewAI Agent"""
        _log_fallback_warning("FallbackAgent", "__init__")
        
        self.role = role or "Fallback Assistant"
        self.goal = goal or "Provide basic assistance when AI is not available"
        self.backstory = backstory or "I am a fallback assistant providing basic functionality."
        self.verbose = verbose
        self.memory = memory
        self.tools = tools or []
        self.llm = llm
        self.max_execution_time = max_execution_time
        self.kwargs = kwargs
        
        # Track agent state
        self.agent_id = f"fallback_agent_{id(self)}"
        self.created_at = datetime.now()
        self.execution_count = 0
        
        logger.info(f"Initialized FallbackAgent: {self.role}")
    
    def execute(self, task_description: str, context: Dict[str, Any] = None) -> str:
        """Execute a task - fallback implementation"""
        _log_fallback_warning("FallbackAgent", "execute")
        
        self.execution_count += 1
        
        # Simulate some processing time
        time.sleep(0.1)
        
        # Generate a basic response based on role
        response = self._generate_fallback_response(task_description, context)
        
        logger.debug(f"Agent {self.role} executed task: {task_description[:100]}...")
        
        return response
    
    def _generate_fallback_response(self, task_description: str, context: Dict[str, Any] = None) -> str:
        """Generate a basic response based on agent role"""
        context = context or {}
        
        # Basic responses based on agent role/type
        if "chat" in self.role.lower() or "conversation" in self.role.lower():
            return (f"I understand you're asking about: '{task_description}'. "
                   "Unfortunately, my AI capabilities are currently unavailable. "
                   "Please try again later when full AI functionality is restored.")
        
        elif "analytic" in self.role.lower() or "data" in self.role.lower():
            return (f"Analytics request received: '{task_description}'. "
                   "AI-powered data analysis is currently unavailable. "
                   "Please check your data manually or contact support for assistance.")
        
        elif "device" in self.role.lower() or "iot" in self.role.lower():
            return (f"Device management request: '{task_description}'. "
                   "AI device management features are currently unavailable. "
                   "Please check device status manually through the dashboard.")
        
        elif "operation" in self.role.lower() or "system" in self.role.lower():
            return (f"Operations request received: '{task_description}'. "
                   "AI operations management is currently unavailable. "
                   "Please check system status manually or contact operations team.")
        
        elif "automation" in self.role.lower() or "workflow" in self.role.lower():
            return (f"Automation request: '{task_description}'. "
                   "AI workflow automation is currently unavailable. "
                   "Please configure workflows manually through the interface.")
        
        elif "backend" in self.role.lower() or "api" in self.role.lower():
            return (f"Backend request received: '{task_description}'. "
                   "AI backend optimization features are currently unavailable. "
                   "System is operating with basic functionality.")
        
        else:
            # Generic response for master or unknown agents
            return (f"Request received: '{task_description}'. "
                   "AI processing capabilities are currently unavailable. "
                   "The system is operating in basic mode. Please try again later.")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "goal": self.goal,
            "status": "fallback_mode",
            "execution_count": self.execution_count,
            "created_at": self.created_at.isoformat(),
            "tools_count": len(self.tools),
            "memory_enabled": self.memory,
            "verbose": self.verbose
        }
    
    def __repr__(self):
        return f"FallbackAgent(role='{self.role}', status='fallback_mode')"


class FallbackTask:
    """
    Fallback implementation of CrewAI Task class
    
    Provides the same interface as crewai.Task but handles execution
    through fallback mechanisms when AI is not available.
    """
    
    def __init__(self,
                 description: str = None,
                 agent: FallbackAgent = None,
                 expected_output: str = None,
                 tools: List = None,
                 context: Dict[str, Any] = None,
                 **kwargs):
        """Initialize fallback task with same parameters as CrewAI Task"""
        _log_fallback_warning("FallbackTask", "__init__")
        
        self.description = description or "Fallback task"
        self.agent = agent
        self.expected_output = expected_output or "Basic task output"
        self.tools = tools or []
        self.context = context or {}
        self.kwargs = kwargs
        
        # Task tracking
        self.task_id = f"fallback_task_{id(self)}"
        self.created_at = datetime.now()
        self.status = "pending"
        self.result = None
        self.execution_time = 0.0
        
        logger.debug(f"Initialized FallbackTask: {self.task_id}")
    
    def execute(self) -> str:
        """Execute the task using the assigned agent"""
        _log_fallback_warning("FallbackTask", "execute")
        
        start_time = time.time()
        self.status = "running"
        
        try:
            if self.agent:
                # Use agent to execute the task
                self.result = self.agent.execute(self.description, self.context)
            else:
                # Execute without agent
                self.result = self._execute_without_agent()
            
            self.status = "completed"
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.status = "failed"
            self.result = f"Task execution failed: {str(e)}"
        
        finally:
            self.execution_time = time.time() - start_time
        
        return self.result
    
    def _execute_without_agent(self) -> str:
        """Execute task without an agent"""
        return (f"Task completed in fallback mode: {self.description}. "
               "AI processing is currently unavailable, so this is a basic response. "
               "Please try again when full functionality is restored.")
    
    def get_task_info(self) -> Dict[str, Any]:
        """Get task information"""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status,
            "result": self.result,
            "execution_time": self.execution_time,
            "created_at": self.created_at.isoformat(),
            "agent": self.agent.role if self.agent else None,
            "expected_output": self.expected_output,
            "tools_count": len(self.tools)
        }
    
    def __repr__(self):
        return f"FallbackTask(id='{self.task_id}', status='{self.status}')"


class FallbackCrew:
    """
    Fallback implementation of CrewAI Crew class
    
    Provides the same interface as crewai.Crew but orchestrates fallback
    agents and tasks when AI functionality is not available.
    """
    
    def __init__(self,
                 agents: List[FallbackAgent] = None,
                 tasks: List[FallbackTask] = None,
                 verbose: bool = True,
                 memory: bool = True,
                 process: str = "sequential",
                 **kwargs):
        """Initialize fallback crew with same parameters as CrewAI Crew"""
        _log_fallback_warning("FallbackCrew", "__init__")
        
        self.agents = agents or []
        self.tasks = tasks or []
        self.verbose = verbose
        self.memory = memory
        self.process = process
        self.kwargs = kwargs
        
        # Crew tracking
        self.crew_id = f"fallback_crew_{id(self)}"
        self.created_at = datetime.now()
        self.execution_history = []
        
        # Validate agents and tasks
        self._validate_crew()
        
        logger.info(f"Initialized FallbackCrew with {len(self.agents)} agents and {len(self.tasks)} tasks")
    
    def _validate_crew(self):
        """Validate crew configuration"""
        if not self.agents:
            logger.warning("FallbackCrew initialized without agents")
        
        if not self.tasks:
            logger.warning("FallbackCrew initialized without tasks")
        
        # Assign agents to tasks that don't have them
        for i, task in enumerate(self.tasks):
            if not task.agent and self.agents:
                # Assign the first agent or round-robin assignment
                agent_index = i % len(self.agents)
                task.agent = self.agents[agent_index]
                logger.debug(f"Assigned agent '{task.agent.role}' to task '{task.task_id}'")
    
    def kickoff(self) -> str:
        """Execute the crew tasks - main entry point matching CrewAI interface"""
        _log_fallback_warning("FallbackCrew", "kickoff")
        
        start_time = time.time()
        execution_id = f"execution_{len(self.execution_history)}"
        
        logger.info(f"Starting crew execution: {execution_id}")
        
        try:
            results = []
            
            if self.process.lower() == "sequential":
                results = self._execute_sequential()
            elif self.process.lower() == "parallel":
                results = self._execute_parallel()
            else:
                logger.warning(f"Unknown process type: {self.process}, defaulting to sequential")
                results = self._execute_sequential()
            
            # Combine results
            final_result = self._combine_results(results)
            
            # Record execution
            execution_record = {
                "execution_id": execution_id,
                "start_time": start_time,
                "end_time": time.time(),
                "duration": time.time() - start_time,
                "tasks_completed": len(results),
                "success": True,
                "result": final_result
            }
            
            self.execution_history.append(execution_record)
            
            logger.info(f"Crew execution completed: {execution_id} in {execution_record['duration']:.2f}s")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            
            # Record failed execution
            execution_record = {
                "execution_id": execution_id,
                "start_time": start_time,
                "end_time": time.time(),
                "duration": time.time() - start_time,
                "tasks_completed": 0,
                "success": False,
                "error": str(e)
            }
            
            self.execution_history.append(execution_record)
            
            return f"Crew execution failed in fallback mode: {str(e)}. AI functionality is currently unavailable."
    
    def _execute_sequential(self) -> List[str]:
        """Execute tasks sequentially"""
        results = []
        
        for i, task in enumerate(self.tasks):
            logger.debug(f"Executing task {i+1}/{len(self.tasks)}: {task.task_id}")
            
            # Add context from previous tasks if memory is enabled
            if self.memory and results:
                task.context.update({
                    "previous_results": results,
                    "task_sequence": i + 1,
                    "total_tasks": len(self.tasks)
                })
            
            result = task.execute()
            results.append(result)
        
        return results
    
    def _execute_parallel(self) -> List[str]:
        """Execute tasks in parallel (simulated since we don't have real threading needs)"""
        logger.info("Simulating parallel execution in fallback mode")
        
        results = []
        
        # In fallback mode, we'll still execute sequentially but faster
        for task in self.tasks:
            # Simulate parallel execution with shorter delays
            time.sleep(0.05)  # Shorter delay for "parallel" execution
            result = task.execute()
            results.append(result)
        
        return results
    
    def _combine_results(self, results: List[str]) -> str:
        """Combine task results into final crew output"""
        if not results:
            return "No tasks were executed in fallback mode."
        
        if len(results) == 1:
            return results[0]
        
        # Combine multiple results
        combined = "Crew execution completed in fallback mode. Results:\n\n"
        
        for i, result in enumerate(results, 1):
            combined += f"Task {i} Result:\n{result}\n\n"
        
        combined += ("Note: These results were generated in fallback mode. "
                    "Full AI capabilities are currently unavailable.")
        
        return combined
    
    def get_crew_info(self) -> Dict[str, Any]:
        """Get crew information"""
        return {
            "crew_id": self.crew_id,
            "agents_count": len(self.agents),
            "tasks_count": len(self.tasks),
            "process": self.process,
            "created_at": self.created_at.isoformat(),
            "execution_count": len(self.execution_history),
            "memory_enabled": self.memory,
            "verbose": self.verbose,
            "status": "fallback_mode"
        }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history"""
        return self.execution_history.copy()
    
    def __repr__(self):
        return f"FallbackCrew(agents={len(self.agents)}, tasks={len(self.tasks)}, status='fallback_mode')"


class FallbackChatOpenAI:
    """
    Fallback implementation of langchain_openai.ChatOpenAI class
    
    Provides the same interface but returns basic responses when
    AI language model functionality is not available.
    """
    
    def __init__(self,
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.7,
                 max_tokens: int = 1000,
                 **kwargs):
        """Initialize fallback ChatOpenAI with same parameters"""
        _log_fallback_warning("FallbackChatOpenAI", "__init__")
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        
        # LLM tracking
        self.llm_id = f"fallback_llm_{id(self)}"
        self.created_at = datetime.now()
        self.call_count = 0
        
        logger.info(f"Initialized FallbackChatOpenAI: model={model}, temp={temperature}")
    
    def invoke(self, prompt: str) -> str:
        """Invoke the language model - main interface method"""
        _log_fallback_warning("FallbackChatOpenAI", "invoke")
        
        self.call_count += 1
        
        # Simulate some processing time
        time.sleep(0.2)
        
        # Return a basic response indicating fallback mode
        return ("I'm operating in fallback mode as AI language model capabilities "
               "are currently unavailable. Your request has been noted, but I cannot "
               "provide AI-generated responses at this time. Please try again when "
               "the AI system is fully operational.")
    
    def __call__(self, prompt: str) -> str:
        """Alternative calling interface"""
        return self.invoke(prompt)
    
    def predict(self, prompt: str) -> str:
        """Legacy prediction interface"""
        return self.invoke(prompt)
    
    def get_llm_info(self) -> Dict[str, Any]:
        """Get LLM information"""
        return {
            "llm_id": self.llm_id,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "call_count": self.call_count,
            "created_at": self.created_at.isoformat(),
            "status": "fallback_mode"
        }
    
    def __repr__(self):
        return f"FallbackChatOpenAI(model='{self.model}', status='fallback_mode')"


def get_fallback_classes() -> Dict[str, type]:
    """
    Get dictionary of fallback classes for easy import replacement
    
    Returns:
        Dict mapping original class names to fallback implementations
    """
    return {
        'Agent': FallbackAgent,
        'Task': FallbackTask,
        'Crew': FallbackCrew,
        'ChatOpenAI': FallbackChatOpenAI
    }


def log_fallback_status():
    """Log current fallback status"""
    logger.warning("=" * 60)
    logger.warning("AI AGENTS RUNNING IN FALLBACK MODE")
    logger.warning("=" * 60)
    logger.warning("CrewAI and/or langchain_openai dependencies are not available.")
    logger.warning("The application is running with basic functionality.")
    logger.warning("To enable full AI capabilities, please install the required dependencies:")
    logger.warning("  pip install crewai langchain_openai")
    logger.warning("=" * 60)


# Helper function to check if we're in fallback mode
def is_fallback_mode() -> bool:
    """Check if we're currently running in fallback mode"""
    try:
        import crewai
        import langchain_openai
        return False
    except ImportError:
        return True


# Example usage and testing
if __name__ == "__main__":
    # Test the fallback implementations
    print("Testing CrewAI Fallback Implementations...")
    
    # Create fallback agent
    agent = FallbackAgent(
        role="Test Chat Agent",
        goal="Test fallback functionality",
        backstory="I am a test agent for fallback mode"
    )
    
    # Create fallback task
    task = FallbackTask(
        description="Test the fallback system",
        agent=agent,
        expected_output="Fallback test results"
    )
    
    # Create fallback crew
    crew = FallbackCrew(
        agents=[agent],
        tasks=[task],
        verbose=True
    )
    
    # Execute the crew
    result = crew.kickoff()
    print("\nCrew Execution Result:")
    print(result)
    
    # Test ChatOpenAI fallback
    llm = FallbackChatOpenAI(model="gpt-4", temperature=0.7)
    llm_result = llm.invoke("Test prompt")
    print(f"\nLLM Result: {llm_result}")
    
    # Show status
    log_fallback_status()
