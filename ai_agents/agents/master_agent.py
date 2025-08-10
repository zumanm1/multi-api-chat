"""
Master AI Agent - Central Orchestrator
Coordinates and manages all AI agents across the Multi-API Chat Platform
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# CrewAI imports replaced with mock implementations for demo
# from crewai import Agent, Task, Crew
# from langchain_openai import ChatOpenAI

from ..configs.agents_config import AGENTS_CONFIG, AgentConfig
from ..tools.base_tools import get_agent_tools


class MasterAgent:
    """Master AI Agent that orchestrates all other agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = AGENTS_CONFIG.get_agent_config("master_agent")
        self.active_agents: Dict[str, Agent] = {}
        self.active_crews: Dict[str, Crew] = {}
        self.task_history: List[Dict] = []
        self.context_memory: Dict[str, Any] = {}
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=AGENTS_CONFIG.default_llm,
            temperature=self.config.llm_config.get("temperature", 0.7),
            max_tokens=self.config.llm_config.get("max_tokens", 2000)
        )
        
        # Create master agent
        self.agent = self._create_master_agent()
        
        # Initialize specialized agents
        self._initialize_specialized_agents()
        
        self.logger.info("Master AI Agent initialized successfully")
    
    def _create_master_agent(self) -> Agent:
        """Create the master orchestrator agent"""
        tools = get_agent_tools(self.config.tools)
        
        return Agent(
            role=self.config.role,
            goal=self.config.goal,
            backstory=self.config.backstory,
            verbose=self.config.verbose,
            memory=self.config.memory,
            tools=tools,
            llm=self.llm,
            max_execution_time=self.config.max_execution_time
        )
    
    def _initialize_specialized_agents(self):
        """Initialize all specialized agents"""
        for agent_name, agent_config in AGENTS_CONFIG.get_all_agents().items():
            if agent_name != "master_agent":  # Don't create master agent twice
                self.active_agents[agent_name] = self._create_specialized_agent(agent_config)
        
        self.logger.info(f"Initialized {len(self.active_agents)} specialized agents")
    
    def _create_specialized_agent(self, config: AgentConfig) -> Agent:
        """Create a specialized agent based on configuration"""
        tools = get_agent_tools(config.tools)
        
        # Create LLM with agent-specific config
        llm = ChatOpenAI(
            model=AGENTS_CONFIG.default_llm,
            temperature=config.llm_config.get("temperature", 0.7),
            max_tokens=config.llm_config.get("max_tokens", 1500)
        )
        
        return Agent(
            role=config.role,
            goal=config.goal, 
            backstory=config.backstory,
            verbose=config.verbose,
            memory=config.memory,
            tools=tools,
            llm=llm,
            max_execution_time=config.max_execution_time
        )
    
    async def process_user_request(self, 
                                 request: str, 
                                 context: Dict[str, Any] = None,
                                 source_page: str = "chat") -> Dict[str, Any]:
        """Process user request and coordinate appropriate agents"""
        try:
            # Analyze user intent
            intent_analysis = await self._analyze_user_intent(request, context, source_page)
            
            # Determine which agents to involve
            required_agents = self._determine_required_agents(intent_analysis)
            
            # Create tasks for involved agents
            tasks = await self._create_agent_tasks(request, intent_analysis, required_agents, context)
            
            # Execute tasks with appropriate crew
            results = await self._execute_agent_tasks(tasks, required_agents)
            
            # Synthesize final response
            final_response = await self._synthesize_response(results, intent_analysis)
            
            # Store in task history
            self._store_task_history(request, intent_analysis, results, final_response)
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error processing user request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while processing your request. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_user_intent(self, 
                                 request: str, 
                                 context: Dict[str, Any],
                                 source_page: str) -> Dict[str, Any]:
        """Analyze user intent and determine task requirements"""
        
        analysis_task = Task(
            description=f"""
            Analyze the following user request and determine the intent, complexity, and required actions:
            
            User Request: {request}
            Source Page: {source_page}
            Context: {json.dumps(context or {}, indent=2)}
            
            Provide analysis in the following format:
            1. Primary Intent: [main goal of the request]
            2. Secondary Intents: [additional goals if any]
            3. Complexity Level: [simple/moderate/complex]
            4. Required Capabilities: [list of needed capabilities]
            5. Cross-Page Requirements: [if interaction with other pages needed]
            6. Urgency Level: [low/medium/high]
            7. Expected Response Type: [text/data/action/mixed]
            """,
            agent=self.agent,
            expected_output="Structured analysis of user intent and requirements"
        )
        
        # Create temporary crew for analysis
        analysis_crew = Crew(
            agents=[self.agent],
            tasks=[analysis_task],
            verbose=AGENTS_CONFIG.debug_mode
        )
        
        result = analysis_crew.kickoff()
        
        # Parse the result (in real implementation, you might want more structured parsing)
        return {
            "analysis": str(result),
            "timestamp": datetime.now().isoformat(),
            "source_page": source_page,
            "complexity": self._extract_complexity_level(str(result)),
            "urgency": self._extract_urgency_level(str(result))
        }
    
    def _determine_required_agents(self, intent_analysis: Dict[str, Any]) -> List[str]:
        """Determine which specialized agents are needed for the task"""
        required_agents = ["chat_agent"]  # Always include chat agent
        
        analysis_text = intent_analysis.get("analysis", "").lower()
        
        # Map keywords to agents
        agent_keywords = {
            "analytics_agent": ["analyze", "data", "metrics", "report", "chart", "statistics", "trends"],
            "device_agent": ["device", "iot", "sensor", "hardware", "configuration", "monitoring"],
            "operations_agent": ["system", "operations", "deployment", "monitoring", "logs", "alerts"],
            "automation_agent": ["automate", "workflow", "schedule", "trigger", "process", "rule"],
            "backend_agent": ["api", "database", "backend", "integration", "service", "performance"]
        }
        
        for agent_name, keywords in agent_keywords.items():
            if any(keyword in analysis_text for keyword in keywords):
                required_agents.append(agent_name)
        
        # Remove duplicates and ensure we have valid agents
        required_agents = list(set(required_agents))
        return [agent for agent in required_agents if agent in self.active_agents]
    
    async def _create_agent_tasks(self, 
                                request: str,
                                intent_analysis: Dict[str, Any], 
                                required_agents: List[str],
                                context: Dict[str, Any]) -> List[Task]:
        """Create specific tasks for each required agent"""
        tasks = []
        
        for agent_name in required_agents:
            if agent_name in self.active_agents:
                agent = self.active_agents[agent_name]
                agent_config = AGENTS_CONFIG.get_agent_config(agent_name)
                
                # Create agent-specific task description
                task_description = self._create_task_description(
                    agent_name, agent_config, request, intent_analysis, context
                )
                
                task = Task(
                    description=task_description,
                    agent=agent,
                    expected_output=f"Specialized response from {agent_config.name}"
                )
                
                tasks.append(task)
        
        return tasks
    
    def _create_task_description(self, 
                               agent_name: str,
                               agent_config: AgentConfig,
                               request: str,
                               intent_analysis: Dict[str, Any],
                               context: Dict[str, Any]) -> str:
        """Create detailed task description for specific agent"""
        
        base_description = f"""
        As the {agent_config.name}, handle the following user request according to your specialized role:
        
        User Request: {request}
        Your Role: {agent_config.role}
        Your Capabilities: {', '.join(agent_config.capabilities)}
        
        Intent Analysis: {intent_analysis.get('analysis', 'No analysis available')}
        Context: {json.dumps(context or {}, indent=2)}
        
        Please provide a response that leverages your specific expertise and capabilities.
        If this request is outside your domain, clearly state that and suggest which other agent might be better suited.
        """
        
        # Add agent-specific instructions
        if agent_name == "chat_agent":
            base_description += "\nFocus on providing a conversational, helpful response that directly addresses the user's query."
        elif agent_name == "analytics_agent":
            base_description += "\nFocus on data analysis, metrics, and insights. If data visualization is needed, describe what charts or reports would be helpful."
        elif agent_name == "device_agent":
            base_description += "\nFocus on device management, IoT systems, and hardware-related aspects of the request."
        elif agent_name == "operations_agent":
            base_description += "\nFocus on system operations, monitoring, and infrastructure aspects."
        elif agent_name == "automation_agent":
            base_description += "\nFocus on automation opportunities, workflow optimization, and process improvements."
        elif agent_name == "backend_agent":
            base_description += "\nFocus on backend systems, API integrations, and technical implementation aspects."
        
        return base_description
    
    async def _execute_agent_tasks(self, tasks: List[Task], required_agents: List[str]) -> Dict[str, Any]:
        """Execute tasks using appropriate crew configuration"""
        if not tasks:
            return {"error": "No tasks to execute"}
        
        # Get agents for the crew
        crew_agents = [self.active_agents[agent_name] for agent_name in required_agents if agent_name in self.active_agents]
        
        # Create crew for execution
        execution_crew = Crew(
            agents=crew_agents,
            tasks=tasks,
            verbose=AGENTS_CONFIG.debug_mode,
            memory=True
        )
        
        # Execute tasks
        try:
            results = execution_crew.kickoff()
            return {
                "success": True,
                "results": str(results),
                "agents_involved": required_agents,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error executing agent tasks: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agents_involved": required_agents,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _synthesize_response(self, results: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize final response from all agent results"""
        
        synthesis_task = Task(
            description=f"""
            Synthesize the following agent results into a cohesive, user-friendly response:
            
            Agent Results: {results.get('results', 'No results available')}
            Original Intent Analysis: {intent_analysis.get('analysis', '')}
            
            Create a response that:
            1. Directly addresses the user's original request
            2. Integrates insights from all involved agents
            3. Is clear, helpful, and actionable
            4. Maintains appropriate tone and context
            5. Suggests next steps if relevant
            
            Provide the synthesis in a structured format with clear sections if multiple aspects were addressed.
            """,
            agent=self.agent,
            expected_output="Synthesized, user-friendly response"
        )
        
        # Create synthesis crew
        synthesis_crew = Crew(
            agents=[self.agent],
            tasks=[synthesis_task],
            verbose=AGENTS_CONFIG.debug_mode
        )
        
        final_result = synthesis_crew.kickoff()
        
        return {
            "success": results.get("success", True),
            "response": str(final_result),
            "agents_involved": results.get("agents_involved", []),
            "timestamp": datetime.now().isoformat(),
            "intent_analysis": intent_analysis
        }
    
    def _store_task_history(self, request: str, intent_analysis: Dict, results: Dict, final_response: Dict):
        """Store task execution history for learning and optimization"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "request": request,
            "intent_analysis": intent_analysis,
            "agents_involved": results.get("agents_involved", []),
            "success": final_response.get("success", False),
            "response_length": len(final_response.get("response", "")),
            "execution_time": None  # Could be calculated if needed
        }
        
        self.task_history.append(history_entry)
        
        # Keep only last 100 entries to manage memory
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]
    
    def _extract_complexity_level(self, analysis: str) -> str:
        """Extract complexity level from analysis text"""
        analysis_lower = analysis.lower()
        if "complex" in analysis_lower:
            return "complex"
        elif "moderate" in analysis_lower:
            return "moderate"
        else:
            return "simple"
    
    def _extract_urgency_level(self, analysis: str) -> str:
        """Extract urgency level from analysis text"""
        analysis_lower = analysis.lower()
        if "high" in analysis_lower:
            return "high"
        elif "medium" in analysis_lower:
            return "medium"
        else:
            return "low"
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "master_agent": {
                "status": "active",
                "tasks_completed": len(self.task_history),
                "last_activity": self.task_history[-1]["timestamp"] if self.task_history else None
            },
            "specialized_agents": {
                name: {"status": "active", "capabilities": config.capabilities}
                for name, config in AGENTS_CONFIG.get_all_agents().items()
                if name in self.active_agents
            },
            "system_status": {
                "enabled": AGENTS_CONFIG.enabled,
                "debug_mode": AGENTS_CONFIG.debug_mode,
                "max_concurrent_tasks": AGENTS_CONFIG.max_concurrent_tasks
            }
        }
    
    async def handle_cross_page_request(self, request: str, source_page: str, target_page: str, context: Dict = None) -> Dict[str, Any]:
        """Handle requests that span multiple pages"""
        cross_page_context = {
            "source_page": source_page,
            "target_page": target_page,
            "cross_page_request": True,
            **(context or {})
        }
        
        return await self.process_user_request(request, cross_page_context, source_page)

# Global master agent instance
master_agent_instance = None

def get_master_agent() -> MasterAgent:
    """Get or create master agent instance"""
    global master_agent_instance
    if master_agent_instance is None:
        master_agent_instance = MasterAgent()
    return master_agent_instance
