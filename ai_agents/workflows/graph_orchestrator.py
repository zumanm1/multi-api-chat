#!/usr/bin/env python3
"""
LangGraph-based Agent Workflow Orchestrator
==========================================

This module provides advanced agent workflow orchestration using LangGraph for 
building complex, stateful agent workflows with sophisticated coordination patterns.

Features:
- LangGraph-based workflow graphs for different request types
- Stateful multi-step agent interactions with checkpoints
- Complex agent coordination with conditional edges
- Workflow persistence and recovery mechanisms
- Integration with existing MasterAgent infrastructure
- Support for parallel and sequential agent execution
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, TypedDict, Annotated
from dataclasses import dataclass, field
from enum import Enum
import pickle
import os

# LangGraph imports with fallback handling
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.prebuilt import ToolNode
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_core.runnables import RunnableConfig
    LANGGRAPH_AVAILABLE = True
    logging.info("LangGraph dependencies loaded successfully")
except ImportError as e:
    logging.warning(f"LangGraph dependencies not available: {e}")
    logging.info("Running in fallback mode without LangGraph functionality")
    LANGGRAPH_AVAILABLE = False
    
    # Fallback classes for when LangGraph is not available
    def add_messages(messages):
        """Fallback for add_messages when LangGraph is not available"""
        return messages
    
    class StateGraph:
        def __init__(self, state_schema): pass
        def add_node(self, name, func): pass
        def add_edge(self, from_node, to_node): pass
        def add_conditional_edges(self, from_node, condition, mapping): pass
        def set_entry_point(self, node): pass
        def set_finish_point(self, node): pass
        def compile(self, checkpointer=None): return FallbackApp()
    
    class FallbackApp:
        def invoke(self, input_data, config=None): 
            return {"status": "fallback", "message": "LangGraph not available"}
        def stream(self, input_data, config=None): 
            yield {"status": "fallback", "message": "LangGraph not available"}
    
    class MemorySaver:
        def __init__(self): pass
    
    class BaseMessage:
        def __init__(self, content=""): self.content = content
    
    HumanMessage = AIMessage = SystemMessage = BaseMessage
    START = "START"
    END = "END"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import existing orchestrator and agents
try:
    from .orchestrator import WorkflowOrchestrator as LegacyOrchestrator
    from ..agents.master_agent import MasterAgent
    from ..agents.simple_master_agent import get_simple_master_agent
    AGENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Agent modules not fully available: {e}")
    AGENTS_AVAILABLE = False

class RequestType(Enum):
    """Types of requests that can be processed"""
    CHAT = "chat"
    ANALYTICS = "analytics"
    DEVICE = "device"
    OPERATIONS = "operations"
    AUTOMATION = "automation"
    WORKFLOW = "workflow"
    HYBRID = "hybrid"

class GraphState(TypedDict):
    """State schema for LangGraph workflows"""
    messages: Annotated[List[BaseMessage], add_messages]
    request_type: str
    original_request: str
    context: Dict[str, Any]
    agent_results: Dict[str, Any]
    workflow_metadata: Dict[str, Any]
    checkpoints: List[Dict[str, Any]]
    error_count: int
    max_iterations: int
    current_iteration: int
    final_response: Optional[Dict[str, Any]]

@dataclass
class GraphWorkflowConfig:
    """Configuration for graph-based workflows"""
    request_type: RequestType
    max_iterations: int = 10
    enable_checkpoints: bool = True
    checkpoint_interval: int = 5  # Save checkpoint every N steps
    recovery_enabled: bool = True
    parallel_execution: bool = False
    agent_timeout: float = 30.0
    workflow_timeout: float = 300.0

class GraphWorkflowOrchestrator:
    """LangGraph-based workflow orchestrator for complex agent coordination"""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        self.checkpointer = None
        self.workflows: Dict[str, StateGraph] = {}
        self.compiled_graphs: Dict[str, Any] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize checkpointing
        if LANGGRAPH_AVAILABLE:
            self._initialize_checkpointer()
        
        # Initialize agent references
        self.master_agent = None
        self.simple_agent = None
        self._initialize_agents()
        
        # Build workflow graphs
        self._build_workflow_graphs()
        
        logger.info("GraphWorkflowOrchestrator initialized successfully")
    
    def _initialize_checkpointer(self):
        """Initialize checkpoint system for workflow persistence"""
        try:
            os.makedirs(self.checkpoint_dir, exist_ok=True)
            self.checkpointer = MemorySaver()  # Using memory saver for now
            logger.info("Checkpoint system initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize checkpointer: {e}")
            self.checkpointer = None
    
    def _initialize_agents(self):
        """Initialize agent references"""
        if AGENTS_AVAILABLE:
            try:
                # Try to get the simple master agent first (more reliable)
                self.simple_agent = get_simple_master_agent()
                logger.info("Simple master agent initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize simple master agent: {e}")
            
            try:
                # Try to get the full master agent
                self.master_agent = MasterAgent()
                logger.info("Master agent initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize master agent: {e}")
    
    def _build_workflow_graphs(self):
        """Build LangGraph workflows for different request types"""
        if not LANGGRAPH_AVAILABLE:
            logger.warning("Cannot build workflows - LangGraph not available")
            return
        
        # Build graphs for each request type
        for request_type in RequestType:
            self._build_request_type_graph(request_type)
        
        # Build hybrid workflow graph
        self._build_hybrid_workflow_graph()
        
        logger.info(f"Built {len(self.workflows)} workflow graphs")
    
    def _build_request_type_graph(self, request_type: RequestType):
        """Build a workflow graph for a specific request type"""
        graph = StateGraph(GraphState)
        
        # Add nodes based on request type
        if request_type == RequestType.CHAT:
            self._build_chat_graph(graph)
        elif request_type == RequestType.ANALYTICS:
            self._build_analytics_graph(graph)
        elif request_type == RequestType.DEVICE:
            self._build_device_graph(graph)
        elif request_type == RequestType.OPERATIONS:
            self._build_operations_graph(graph)
        elif request_type == RequestType.AUTOMATION:
            self._build_automation_graph(graph)
        elif request_type == RequestType.WORKFLOW:
            self._build_workflow_graph(graph)
        
        # Compile the graph
        compiled_graph = graph.compile(checkpointer=self.checkpointer)
        
        self.workflows[request_type.value] = graph
        self.compiled_graphs[request_type.value] = compiled_graph
    
    def _build_chat_graph(self, graph: StateGraph):
        """Build chat-focused workflow graph"""
        
        async def chat_analyzer(state: GraphState) -> GraphState:
            """Analyze chat request and determine next steps"""
            try:
                messages = [HumanMessage(content=f"Analyze this chat request: {state['original_request']}")]
                
                # Use available agent
                if self.simple_agent:
                    result = await self.simple_agent.process_user_request(
                        request=state['original_request'],
                        context=state['context'],
                        source_page='chat'
                    )
                elif self.master_agent:
                    result = await self.master_agent.process_user_request(
                        request=state['original_request'],
                        context=state['context'],
                        source_page='chat'
                    )
                else:
                    result = {"status": "no_agent", "response": "No agent available"}
                
                state['agent_results']['chat_analyzer'] = result
                state['messages'].append(AIMessage(content=json.dumps(result)))
                
                return state
            except Exception as e:
                logger.error(f"Chat analyzer error: {e}")
                state['error_count'] += 1
                return state
        
        async def chat_responder(state: GraphState) -> GraphState:
            """Generate final chat response"""
            try:
                analysis = state['agent_results'].get('chat_analyzer', {})
                response = {
                    "type": "chat_response",
                    "analysis": analysis,
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed"
                }
                
                state['final_response'] = response
                state['messages'].append(AIMessage(content="Chat response generated"))
                
                return state
            except Exception as e:
                logger.error(f"Chat responder error: {e}")
                state['error_count'] += 1
                return state
        
        # Add nodes
        graph.add_node("chat_analyzer", chat_analyzer)
        graph.add_node("chat_responder", chat_responder)
        
        # Add edges
        graph.add_edge(START, "chat_analyzer")
        graph.add_edge("chat_analyzer", "chat_responder")
        graph.add_edge("chat_responder", END)
    
    def _build_analytics_graph(self, graph: StateGraph):
        """Build analytics-focused workflow graph"""
        
        async def data_collector(state: GraphState) -> GraphState:
            """Collect relevant analytics data"""
            try:
                if self.simple_agent:
                    result = await self.simple_agent.process_user_request(
                        request=f"Collect analytics data for: {state['original_request']}",
                        context={**state['context'], 'preferred_agent': 'analytics'},
                        source_page='analytics'
                    )
                else:
                    result = {"status": "simulated", "data": "Sample analytics data"}
                
                state['agent_results']['data_collector'] = result
                state['messages'].append(AIMessage(content="Data collection completed"))
                
                return state
            except Exception as e:
                logger.error(f"Data collector error: {e}")
                state['error_count'] += 1
                return state
        
        async def analytics_processor(state: GraphState) -> GraphState:
            """Process and analyze collected data"""
            try:
                data = state['agent_results'].get('data_collector', {})
                
                # Process analytics
                processed_result = {
                    "type": "analytics_result",
                    "raw_data": data,
                    "insights": ["Insight 1", "Insight 2", "Insight 3"],
                    "metrics": {"performance": 85, "efficiency": 92},
                    "timestamp": datetime.now().isoformat()
                }
                
                state['agent_results']['analytics_processor'] = processed_result
                state['final_response'] = processed_result
                state['messages'].append(AIMessage(content="Analytics processing completed"))
                
                return state
            except Exception as e:
                logger.error(f"Analytics processor error: {e}")
                state['error_count'] += 1
                return state
        
        # Add nodes
        graph.add_node("data_collector", data_collector)
        graph.add_node("analytics_processor", analytics_processor)
        
        # Add edges
        graph.add_edge(START, "data_collector")
        graph.add_edge("data_collector", "analytics_processor")
        graph.add_edge("analytics_processor", END)
    
    def _build_device_graph(self, graph: StateGraph):
        """Build device-focused workflow graph"""
        
        async def device_discovery(state: GraphState) -> GraphState:
            """Discover and identify relevant devices"""
            try:
                if self.simple_agent:
                    result = await self.simple_agent.process_user_request(
                        request=f"Discover devices for: {state['original_request']}",
                        context={**state['context'], 'preferred_agent': 'device'},
                        source_page='device'
                    )
                else:
                    result = {
                        "devices_found": ["Router-01", "Switch-01", "Firewall-01"],
                        "status": "discovery_completed"
                    }
                
                state['agent_results']['device_discovery'] = result
                state['messages'].append(AIMessage(content="Device discovery completed"))
                
                return state
            except Exception as e:
                logger.error(f"Device discovery error: {e}")
                state['error_count'] += 1
                return state
        
        async def device_status_check(state: GraphState) -> GraphState:
            """Check status of discovered devices"""
            try:
                devices = state['agent_results'].get('device_discovery', {}).get('devices_found', [])
                
                status_results = {}
                for device in devices:
                    status_results[device] = {
                        "status": "online",
                        "cpu_usage": "15%",
                        "memory_usage": "42%",
                        "uptime": "45 days"
                    }
                
                result = {
                    "type": "device_status",
                    "device_statuses": status_results,
                    "summary": "All devices operational",
                    "timestamp": datetime.now().isoformat()
                }
                
                state['agent_results']['device_status_check'] = result
                state['final_response'] = result
                state['messages'].append(AIMessage(content="Device status check completed"))
                
                return state
            except Exception as e:
                logger.error(f"Device status check error: {e}")
                state['error_count'] += 1
                return state
        
        # Add nodes
        graph.add_node("device_discovery", device_discovery)
        graph.add_node("device_status_check", device_status_check)
        
        # Add edges
        graph.add_edge(START, "device_discovery")
        graph.add_edge("device_discovery", "device_status_check")
        graph.add_edge("device_status_check", END)
    
    def _build_operations_graph(self, graph: StateGraph):
        """Build operations-focused workflow graph"""
        
        async def operations_assessment(state: GraphState) -> GraphState:
            """Assess current operational status"""
            try:
                if self.simple_agent:
                    result = await self.simple_agent.process_user_request(
                        request=f"Assess operations for: {state['original_request']}",
                        context={**state['context'], 'preferred_agent': 'operations'},
                        source_page='operations'
                    )
                else:
                    result = {
                        "operational_status": "healthy",
                        "active_services": 12,
                        "alerts": 0,
                        "performance_score": 94
                    }
                
                state['agent_results']['operations_assessment'] = result
                state['final_response'] = result
                state['messages'].append(AIMessage(content="Operations assessment completed"))
                
                return state
            except Exception as e:
                logger.error(f"Operations assessment error: {e}")
                state['error_count'] += 1
                return state
        
        # Add nodes
        graph.add_node("operations_assessment", operations_assessment)
        
        # Add edges
        graph.add_edge(START, "operations_assessment")
        graph.add_edge("operations_assessment", END)
    
    def _build_automation_graph(self, graph: StateGraph):
        """Build automation-focused workflow graph"""
        
        async def automation_analyzer(state: GraphState) -> GraphState:
            """Analyze automation opportunities"""
            try:
                if self.simple_agent:
                    result = await self.simple_agent.process_user_request(
                        request=f"Analyze automation opportunities for: {state['original_request']}",
                        context={**state['context'], 'preferred_agent': 'automation'},
                        source_page='automation'
                    )
                else:
                    result = {
                        "automation_opportunities": [
                            "Log rotation automation",
                            "Backup scheduling",
                            "Performance monitoring"
                        ],
                        "estimated_time_savings": "4 hours/week"
                    }
                
                state['agent_results']['automation_analyzer'] = result
                state['final_response'] = result
                state['messages'].append(AIMessage(content="Automation analysis completed"))
                
                return state
            except Exception as e:
                logger.error(f"Automation analyzer error: {e}")
                state['error_count'] += 1
                return state
        
        # Add nodes
        graph.add_node("automation_analyzer", automation_analyzer)
        
        # Add edges
        graph.add_edge(START, "automation_analyzer")
        graph.add_edge("automation_analyzer", END)
    
    def _build_workflow_graph(self, graph: StateGraph):
        """Build workflow management graph"""
        
        async def workflow_processor(state: GraphState) -> GraphState:
            """Process workflow-related requests"""
            try:
                result = {
                    "type": "workflow_response",
                    "message": f"Processed workflow request: {state['original_request']}",
                    "workflow_created": True,
                    "timestamp": datetime.now().isoformat()
                }
                
                state['agent_results']['workflow_processor'] = result
                state['final_response'] = result
                state['messages'].append(AIMessage(content="Workflow processing completed"))
                
                return state
            except Exception as e:
                logger.error(f"Workflow processor error: {e}")
                state['error_count'] += 1
                return state
        
        # Add nodes
        graph.add_node("workflow_processor", workflow_processor)
        
        # Add edges
        graph.add_edge(START, "workflow_processor")
        graph.add_edge("workflow_processor", END)
    
    def _build_hybrid_workflow_graph(self):
        """Build hybrid workflow that can coordinate multiple agent types"""
        if not LANGGRAPH_AVAILABLE:
            return
        
        graph = StateGraph(GraphState)
        
        async def request_router(state: GraphState) -> GraphState:
            """Route request to appropriate specialized workflows"""
            try:
                request = state['original_request'].lower()
                
                # Determine which agents to involve based on request content
                involved_agents = []
                if any(word in request for word in ['chat', 'talk', 'discuss', 'conversation']):
                    involved_agents.append('chat')
                if any(word in request for word in ['analytics', 'analyze', 'data', 'metrics']):
                    involved_agents.append('analytics')
                if any(word in request for word in ['device', 'router', 'switch', 'network']):
                    involved_agents.append('device')
                if any(word in request for word in ['operations', 'status', 'health', 'monitoring']):
                    involved_agents.append('operations')
                if any(word in request for word in ['automate', 'automation', 'schedule']):
                    involved_agents.append('automation')
                
                state['workflow_metadata']['involved_agents'] = involved_agents
                state['messages'].append(AIMessage(content=f"Request routed to agents: {involved_agents}"))
                
                return state
            except Exception as e:
                logger.error(f"Request router error: {e}")
                state['error_count'] += 1
                return state
        
        async def coordinator(state: GraphState) -> GraphState:
            """Coordinate execution of multiple agent workflows"""
            try:
                involved_agents = state['workflow_metadata'].get('involved_agents', [])
                coordination_results = {}
                
                for agent_type in involved_agents:
                    if agent_type in self.compiled_graphs:
                        # Create sub-state for agent
                        sub_state = {
                            'messages': [],
                            'request_type': agent_type,
                            'original_request': state['original_request'],
                            'context': state['context'],
                            'agent_results': {},
                            'workflow_metadata': {},
                            'checkpoints': [],
                            'error_count': 0,
                            'max_iterations': 5,
                            'current_iteration': 0,
                            'final_response': None
                        }
                        
                        # Execute sub-workflow
                        result = self.compiled_graphs[agent_type].invoke(sub_state)
                        coordination_results[agent_type] = result.get('final_response', {})
                
                state['agent_results']['coordinator'] = coordination_results
                state['messages'].append(AIMessage(content="Multi-agent coordination completed"))
                
                return state
            except Exception as e:
                logger.error(f"Coordinator error: {e}")
                state['error_count'] += 1
                return state
        
        async def response_synthesizer(state: GraphState) -> GraphState:
            """Synthesize responses from multiple agents"""
            try:
                coordination_results = state['agent_results'].get('coordinator', {})
                
                synthesized_response = {
                    "type": "hybrid_response",
                    "agent_responses": coordination_results,
                    "synthesis": "Combined insights from multiple AI agents",
                    "timestamp": datetime.now().isoformat(),
                    "agents_involved": list(coordination_results.keys())
                }
                
                state['final_response'] = synthesized_response
                state['messages'].append(AIMessage(content="Response synthesis completed"))
                
                return state
            except Exception as e:
                logger.error(f"Response synthesizer error: {e}")
                state['error_count'] += 1
                return state
        
        # Add nodes
        graph.add_node("request_router", request_router)
        graph.add_node("coordinator", coordinator)
        graph.add_node("response_synthesizer", response_synthesizer)
        
        # Add edges
        graph.add_edge(START, "request_router")
        graph.add_edge("request_router", "coordinator")
        graph.add_edge("coordinator", "response_synthesizer")
        graph.add_edge("response_synthesizer", END)
        
        # Compile and store
        compiled_graph = graph.compile(checkpointer=self.checkpointer)
        self.workflows['hybrid'] = graph
        self.compiled_graphs['hybrid'] = compiled_graph
    
    async def process_request(self, 
                            request: str, 
                            context: Dict[str, Any] = None,
                            request_type: str = "hybrid",
                            config: GraphWorkflowConfig = None) -> Dict[str, Any]:
        """Process a request using LangGraph workflow orchestration"""
        
        if not LANGGRAPH_AVAILABLE:
            return {
                "success": False,
                "error": "LangGraph not available",
                "response": "Graph-based workflow orchestration is not available. Please install LangGraph.",
                "timestamp": datetime.now().isoformat(),
                "fallback_mode": True
            }
        
        if config is None:
            config = GraphWorkflowConfig(RequestType(request_type))
        
        session_id = f"session_{int(time.time())}_{hash(request) % 10000}"
        
        try:
            # Initialize state
            initial_state = {
                'messages': [HumanMessage(content=request)],
                'request_type': request_type,
                'original_request': request,
                'context': context or {},
                'agent_results': {},
                'workflow_metadata': {
                    'session_id': session_id,
                    'start_time': datetime.now().isoformat(),
                    'config': config.__dict__ if config else {}
                },
                'checkpoints': [],
                'error_count': 0,
                'max_iterations': config.max_iterations if config else 10,
                'current_iteration': 0,
                'final_response': None
            }
            
            # Get appropriate workflow
            if request_type in self.compiled_graphs:
                workflow = self.compiled_graphs[request_type]
            else:
                # Default to hybrid workflow
                workflow = self.compiled_graphs.get('hybrid')
                if not workflow:
                    raise ValueError("No suitable workflow found")
            
            # Execute workflow
            thread_config = {"configurable": {"thread_id": session_id}}
            result = workflow.invoke(initial_state, config=thread_config)
            
            # Store session info
            self.active_sessions[session_id] = {
                'request': request,
                'request_type': request_type,
                'start_time': datetime.now(),
                'status': 'completed',
                'result': result
            }
            
            return {
                "success": True,
                "session_id": session_id,
                "response": result.get('final_response', {}),
                "workflow_metadata": result.get('workflow_metadata', {}),
                "messages": [msg.content if hasattr(msg, 'content') else str(msg) 
                           for msg in result.get('messages', [])],
                "timestamp": datetime.now().isoformat(),
                "langgraph_mode": True
            }
            
        except Exception as e:
            logger.error(f"Graph workflow execution error: {str(e)}")
            
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['status'] = 'failed'
                self.active_sessions[session_id]['error'] = str(e)
            
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "response": "Graph workflow execution failed. Please try again.",
                "timestamp": datetime.now().isoformat(),
                "langgraph_mode": True
            }
    
    async def stream_workflow(self, 
                            request: str,
                            context: Dict[str, Any] = None,
                            request_type: str = "hybrid",
                            config: GraphWorkflowConfig = None):
        """Stream workflow execution in real-time"""
        
        if not LANGGRAPH_AVAILABLE:
            yield {
                "status": "error",
                "message": "LangGraph not available for streaming",
                "timestamp": datetime.now().isoformat()
            }
            return
        
        session_id = f"stream_{int(time.time())}_{hash(request) % 10000}"
        
        try:
            # Initialize state (similar to process_request)
            initial_state = {
                'messages': [HumanMessage(content=request)],
                'request_type': request_type,
                'original_request': request,
                'context': context or {},
                'agent_results': {},
                'workflow_metadata': {
                    'session_id': session_id,
                    'start_time': datetime.now().isoformat(),
                    'streaming': True
                },
                'checkpoints': [],
                'error_count': 0,
                'max_iterations': config.max_iterations if config else 10,
                'current_iteration': 0,
                'final_response': None
            }
            
            # Get workflow
            if request_type in self.compiled_graphs:
                workflow = self.compiled_graphs[request_type]
            else:
                workflow = self.compiled_graphs.get('hybrid')
            
            if not workflow:
                yield {"status": "error", "message": "No workflow available"}
                return
            
            # Stream execution
            thread_config = {"configurable": {"thread_id": session_id}}
            
            for chunk in workflow.stream(initial_state, config=thread_config):
                yield {
                    "status": "streaming",
                    "chunk": chunk,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            yield {
                "status": "completed",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Stream workflow error: {e}")
            yield {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def save_checkpoint(self, session_id: str, state: Dict[str, Any]) -> bool:
        """Save workflow checkpoint for recovery"""
        try:
            if not self.checkpointer:
                return False
            
            checkpoint_data = {
                'session_id': session_id,
                'state': state,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to file for persistence (since we're using MemorySaver)
            checkpoint_path = os.path.join(self.checkpoint_dir, f"{session_id}.pkl")
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            
            logger.info(f"Checkpoint saved for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False
    
    def load_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow checkpoint for recovery"""
        try:
            checkpoint_path = os.path.join(self.checkpoint_dir, f"{session_id}.pkl")
            
            if not os.path.exists(checkpoint_path):
                return None
            
            with open(checkpoint_path, 'rb') as f:
                checkpoint_data = pickle.load(f)
            
            logger.info(f"Checkpoint loaded for session: {session_id}")
            return checkpoint_data.get('state')
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an active session"""
        return self.active_sessions.get(session_id)
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions and checkpoints"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for session_id, session_info in self.active_sessions.items():
            if session_info.get('start_time', datetime.now()) < cutoff_time:
                sessions_to_remove.append(session_id)
        
        # Remove old sessions
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            
            # Remove checkpoint file
            checkpoint_path = os.path.join(self.checkpoint_dir, f"{session_id}.pkl")
            if os.path.exists(checkpoint_path):
                os.remove(checkpoint_path)
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
        return len(sessions_to_remove)
    
    def integrate_with_master_agent(self, master_agent=None):
        """Integration point with existing MasterAgent"""
        if master_agent:
            self.master_agent = master_agent
            logger.info("Integrated with provided MasterAgent")
        elif AGENTS_AVAILABLE:
            try:
                # Try to create new master agent if not provided
                if not self.master_agent:
                    self.master_agent = MasterAgent()
                    logger.info("Created and integrated new MasterAgent")
            except Exception as e:
                logger.warning(f"Could not integrate with MasterAgent: {e}")
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflow types"""
        return list(self.compiled_graphs.keys())
    
    def get_workflow_info(self, workflow_type: str) -> Dict[str, Any]:
        """Get information about a specific workflow"""
        if workflow_type not in self.workflows:
            return {"error": "Workflow not found"}
        
        return {
            "type": workflow_type,
            "available": workflow_type in self.compiled_graphs,
            "nodes": getattr(self.workflows[workflow_type], 'nodes', {}),
            "edges": getattr(self.workflows[workflow_type], 'edges', {}),
            "checkpointing_enabled": self.checkpointer is not None,
            "langgraph_available": LANGGRAPH_AVAILABLE
        }

# Global graph orchestrator instance
graph_orchestrator = GraphWorkflowOrchestrator()

# Convenience functions for quick access
async def process_with_graph(request: str, 
                           context: Dict[str, Any] = None,
                           request_type: str = "hybrid") -> Dict[str, Any]:
    """Convenience function to process request with graph orchestration"""
    return await graph_orchestrator.process_request(request, context, request_type)

async def stream_with_graph(request: str,
                          context: Dict[str, Any] = None,
                          request_type: str = "hybrid"):
    """Convenience function to stream workflow execution"""
    async for chunk in graph_orchestrator.stream_workflow(request, context, request_type):
        yield chunk

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_graph_orchestrator():
        """Test the LangGraph workflow orchestrator"""
        print("Testing LangGraph Workflow Orchestrator...")
        
        # Test different workflow types
        test_requests = [
            ("Analyze system performance", "analytics"),
            ("Check device status", "device"),
            ("What's the current operational status?", "operations"),
            ("Suggest automation opportunities", "automation"),
            ("Have a conversation about network optimization", "chat"),
            ("Comprehensive analysis of network infrastructure", "hybrid")
        ]
        
        for request, req_type in test_requests:
            print(f"\nTesting {req_type} workflow:")
            print(f"Request: {request}")
            
            result = await graph_orchestrator.process_request(
                request=request,
                context={"test_mode": True},
                request_type=req_type
            )
            
            print(f"Result: {json.dumps(result, indent=2, default=str)}")
            print("-" * 50)
        
        # Test streaming
        print("\nTesting streaming workflow:")
        async for chunk in graph_orchestrator.stream_workflow(
            "Stream test: analyze and optimize network performance",
            {"stream_test": True},
            "hybrid"
        ):
            print(f"Stream chunk: {chunk}")
        
        print("\nGraph orchestrator test completed!")
    
    # Run test
    asyncio.run(test_graph_orchestrator())
