"""
Master AI Agent - Central Orchestrator
Coordinates and manages all AI agents across the Multi-API Chat Platform
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# CrewAI imports with error handling for optional AI functionality
try:
    from crewai import Agent, Task, Crew
    from langchain_openai import ChatOpenAI
    CREWAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CrewAI dependencies not available: {e}")
    logging.info("Running in fallback mode without AI agent functionality")
    CREWAI_AVAILABLE = False
    
    # Import fallback classes for robust fallback functionality
    from ..fallback_classes import (
        FallbackAgent as Agent,
        FallbackTask as Task, 
        FallbackCrew as Crew,
        FallbackChatOpenAI as ChatOpenAI,
        log_fallback_status
    )
    
    # Log fallback status on first import
    log_fallback_status()

from ..configs.agents_config import AGENTS_CONFIG, AgentConfig
from ..tools.base_tools import get_agent_tools

# Import LangGraph orchestrator for advanced workflow management
try:
    from ..workflows.graph_orchestrator import graph_orchestrator, GraphWorkflowConfig, RequestType
    LANGGRAPH_ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LangGraph orchestrator not available: {e}")
    LANGGRAPH_ORCHESTRATOR_AVAILABLE = False
    graph_orchestrator = None


class MasterAgent:
    """Master AI Agent that orchestrates all other agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = AGENTS_CONFIG.get_agent_config("master_agent")
        self.active_agents: Dict[str, Agent] = {}
        self.active_crews: Dict[str, Crew] = {}
        self.task_history: List[Dict] = []
        self.context_memory: Dict[str, Any] = {}
        
        if not CREWAI_AVAILABLE:
            self.logger.warning("CrewAI not available - running in fallback mode")
            self.llm = None
            self.agent = None
            return
        
        # Initialize LLM
        try:
            self.llm = ChatOpenAI(
                model=AGENTS_CONFIG.default_llm,
                temperature=self.config.llm_config.get("temperature", 0.7),
                max_tokens=self.config.llm_config.get("max_tokens", 2000)
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize ChatOpenAI: {e}")
            self.llm = None
            self.agent = None
            return
        
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
                                 source_page: str = "chat",
                                 use_graph_orchestration: bool = None) -> Dict[str, Any]:
        """Process user request and coordinate appropriate agents"""
        # Auto-determine graph orchestration usage if not specified
        if use_graph_orchestration is None:
            use_graph_orchestration = self._should_use_graph_orchestration(request, context, source_page)
        
        # Try graph-based orchestration first if available and requested
        if use_graph_orchestration and LANGGRAPH_ORCHESTRATOR_AVAILABLE:
            try:
                return await self._process_with_graph_orchestration(request, context, source_page)
            except Exception as e:
                self.logger.warning(f"Graph orchestration failed, falling back to CrewAI: {e}")
                # Fall through to CrewAI processing
        
        # Fallback response when CrewAI is not available
        if not CREWAI_AVAILABLE:
            return {
                "success": False,
                "error": "AI agent functionality not available",
                "response": "The AI agent system is currently unavailable due to missing dependencies. Please ensure CrewAI and langchain_openai are installed to enable advanced AI functionality.",
                "timestamp": datetime.now().isoformat(),
                "fallback_mode": True
            }
        
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
                "status": "active" if CREWAI_AVAILABLE else "fallback_mode",
                "tasks_completed": len(self.task_history),
                "last_activity": self.task_history[-1]["timestamp"] if self.task_history else None
            },
            "specialized_agents": {
                name: {"status": "active" if CREWAI_AVAILABLE else "unavailable", "capabilities": config.capabilities}
                for name, config in AGENTS_CONFIG.get_all_agents().items()
                if name in self.active_agents or not CREWAI_AVAILABLE
            },
            "system_status": {
                "enabled": AGENTS_CONFIG.enabled,
                "debug_mode": AGENTS_CONFIG.debug_mode,
                "max_concurrent_tasks": AGENTS_CONFIG.max_concurrent_tasks,
                "crewai_available": CREWAI_AVAILABLE,
                "fallback_mode": not CREWAI_AVAILABLE
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
    
    def _should_use_graph_orchestration(self, request: str, context: Dict[str, Any], source_page: str) -> bool:
        """Determine if graph orchestration should be used for this request"""
        if not LANGGRAPH_ORCHESTRATOR_AVAILABLE:
            return False
        
        # Use graph orchestration for complex multi-agent workflows
        request_lower = request.lower()
        
        # Keywords that suggest complex workflows
        complex_keywords = [
            'analyze and', 'comprehensive', 'multi-step', 'workflow', 'coordinate',
            'automation and', 'monitor and', 'both', 'also', 'additionally',
            'full analysis', 'complete assessment', 'end-to-end'
        ]
        
        # Check if request seems complex or involves multiple domains
        if any(keyword in request_lower for keyword in complex_keywords):
            return True
        
        # Count potential agent domains mentioned
        domain_keywords = {
            'analytics': ['analyze', 'data', 'metrics', 'report', 'statistics'],
            'device': ['device', 'router', 'switch', 'hardware', 'network'],
            'operations': ['operations', 'monitor', 'system', 'logs', 'alerts'],
            'automation': ['automate', 'schedule', 'workflow', 'process'],
            'chat': ['explain', 'help', 'what', 'how', 'why']
        }
        
        domains_mentioned = 0
        for domain, keywords in domain_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                domains_mentioned += 1
        
        # Use graph orchestration for multi-domain requests
        if domains_mentioned >= 2:
            return True
        
        # Use for specific pages that benefit from graph workflows
        if source_page in ['analytics', 'workflow', 'automation']:
            return True
        
        # Default to CrewAI for simpler requests
        return False
    
    async def _process_with_graph_orchestration(self, request: str, context: Dict[str, Any], source_page: str) -> Dict[str, Any]:
        """Process request using LangGraph orchestration"""
        try:
            # Determine request type based on source page and content
            request_type = self._determine_graph_request_type(request, source_page)
            
            # Create graph workflow configuration
            config = GraphWorkflowConfig(
                request_type=RequestType(request_type),
                max_iterations=10,
                enable_checkpoints=True,
                recovery_enabled=True,
                agent_timeout=30.0
            )
            
            # Integrate with graph orchestrator
            if graph_orchestrator:
                graph_orchestrator.integrate_with_master_agent(self)
            
            # Process with graph orchestration
            result = await graph_orchestrator.process_request(
                request=request,
                context=context or {},
                request_type=request_type,
                config=config
            )
            
            # Enhance result with MasterAgent metadata
            result["orchestration_mode"] = "langgraph"
            result["master_agent_integrated"] = True
            
            return result
            
        except Exception as e:
            self.logger.error(f"Graph orchestration error: {e}")
            raise e
    
    def _determine_graph_request_type(self, request: str, source_page: str) -> str:
        """Determine the appropriate graph workflow type for the request"""
        request_lower = request.lower()
        
        # Page-based determination
        page_mapping = {
            'analytics': 'analytics',
            'device': 'device', 
            'operations': 'operations',
            'automation': 'automation',
            'workflow': 'workflow',
            'chat': 'chat'
        }
        
        if source_page in page_mapping:
            primary_type = page_mapping[source_page]
        else:
            primary_type = 'chat'
        
        # Content-based refinement
        if any(word in request_lower for word in ['comprehensive', 'full analysis', 'complete', 'multi', 'both']):
            return 'hybrid'
        
        # Specific keyword mapping
        if any(word in request_lower for word in ['analyze', 'data', 'metrics', 'statistics']):
            return 'analytics'
        elif any(word in request_lower for word in ['device', 'router', 'switch', 'network']):
            return 'device'
        elif any(word in request_lower for word in ['operations', 'system', 'monitor', 'health']):
            return 'operations'
        elif any(word in request_lower for word in ['automate', 'workflow', 'schedule', 'process']):
            return 'automation'
        
        return primary_type
    
    async def stream_graph_workflow(self, request: str, context: Dict[str, Any] = None, source_page: str = "chat"):
        """Stream a graph-based workflow execution"""
        if not LANGGRAPH_ORCHESTRATOR_AVAILABLE:
            yield {
                "status": "error",
                "message": "Graph orchestration not available",
                "timestamp": datetime.now().isoformat()
            }
            return
        
        try:
            request_type = self._determine_graph_request_type(request, source_page)
            
            # Integrate with graph orchestrator
            if graph_orchestrator:
                graph_orchestrator.integrate_with_master_agent(self)
            
            async for chunk in graph_orchestrator.stream_workflow(
                request=request,
                context=context or {},
                request_type=request_type
            ):
                chunk["master_agent_integrated"] = True
                yield chunk
                
        except Exception as e:
            self.logger.error(f"Stream graph workflow error: {e}")
            yield {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get status of orchestration capabilities"""
        status = {
            "crewai_available": CREWAI_AVAILABLE,
            "langgraph_available": LANGGRAPH_ORCHESTRATOR_AVAILABLE,
            "default_mode": "crewai" if CREWAI_AVAILABLE else "fallback",
            "graph_workflows_available": [],
            "timestamp": datetime.now().isoformat()
        }
        
        if LANGGRAPH_ORCHESTRATOR_AVAILABLE and graph_orchestrator:
            try:
                status["graph_workflows_available"] = graph_orchestrator.get_available_workflows()
                status["default_mode"] = "hybrid"  # Can use both
            except Exception as e:
                status["graph_orchestrator_error"] = str(e)
        
        return status
    
    async def process_with_preferred_orchestration(self, 
                                                 request: str,
                                                 context: Dict[str, Any] = None,
                                                 source_page: str = "chat",
                                                 prefer_graph: bool = True) -> Dict[str, Any]:
        """Process request with preferred orchestration method"""
        if prefer_graph and LANGGRAPH_ORCHESTRATOR_AVAILABLE:
            try:
                result = await self._process_with_graph_orchestration(request, context, source_page)
                if result.get("success", False):
                    return result
            except Exception as e:
                self.logger.warning(f"Preferred graph orchestration failed: {e}")
        
        # Fallback to standard processing
        return await self.process_user_request(request, context, source_page, use_graph_orchestration=False)

# Global master agent instance
master_agent_instance = None

def get_master_agent() -> MasterAgent:
    """Get or create master agent instance"""
    global master_agent_instance
    if master_agent_instance is None:
        master_agent_instance = MasterAgent()
    return master_agent_instance
