"""
AI Agents Workflows Package
===========================

Advanced workflow orchestration for multi-agent systems.
Includes both traditional workflow orchestration and LangGraph-based 
graph orchestration for complex multi-agent interactions.
"""

# Traditional orchestrator
try:
    from .orchestrator import (
        WorkflowOrchestrator,
        WorkflowDefinition,
        WorkflowTask,
        TaskStatus,
        TaskPriority,
        orchestrator,
        create_simple_workflow,
        create_analysis_workflow
    )
    TRADITIONAL_ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    TRADITIONAL_ORCHESTRATOR_AVAILABLE = False
    print(f"Traditional orchestrator not available: {e}")

# LangGraph orchestrator
try:
    from .graph_orchestrator import (
        graph_orchestrator,
        GraphWorkflowOrchestrator,
        GraphState,
        GraphWorkflowConfig,
        RequestType,
        process_with_graph,
        stream_with_graph
    )
    LANGGRAPH_ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_ORCHESTRATOR_AVAILABLE = False
    print(f"LangGraph orchestrator not available: {e}")

# Convenience functions for workflow selection
async def process_workflow(request: str,
                          context: dict = None,
                          request_type: str = "hybrid",
                          prefer_graph: bool = True):
    """
    Process a workflow using the best available orchestrator.
    
    Args:
        request: The user request to process
        context: Optional context dictionary
        request_type: Type of request (chat, analytics, device, etc.)
        prefer_graph: Whether to prefer LangGraph orchestration
    
    Returns:
        Dict containing the workflow result
    """
    if prefer_graph and LANGGRAPH_ORCHESTRATOR_AVAILABLE:
        try:
            return await process_with_graph(request, context, request_type)
        except Exception as e:
            print(f"Graph orchestration failed, falling back: {e}")
    
    if TRADITIONAL_ORCHESTRATOR_AVAILABLE:
        # Fallback to traditional orchestrator
        workflow = create_analysis_workflow(request)
        workflow_id = orchestrator.create_workflow(workflow)
        return await orchestrator.execute_workflow(workflow_id)
    
    # Ultimate fallback
    return {
        "success": False,
        "error": "No workflow orchestrator available",
        "response": "Workflow processing is not available due to missing dependencies."
    }

def get_orchestration_capabilities():
    """Get information about available orchestration capabilities"""
    return {
        "traditional_available": TRADITIONAL_ORCHESTRATOR_AVAILABLE,
        "langgraph_available": LANGGRAPH_ORCHESTRATOR_AVAILABLE,
        "recommended_mode": "langgraph" if LANGGRAPH_ORCHESTRATOR_AVAILABLE else "traditional" if TRADITIONAL_ORCHESTRATOR_AVAILABLE else "none",
        "workflow_types": [
            "chat", "analytics", "device", "operations", 
            "automation", "workflow", "hybrid"
        ] if LANGGRAPH_ORCHESTRATOR_AVAILABLE else ["general"]
    }

# Build __all__ list based on availability
__all__ = [
    # Convenience functions (always available)
    'process_workflow',
    'get_orchestration_capabilities',
    'TRADITIONAL_ORCHESTRATOR_AVAILABLE',
    'LANGGRAPH_ORCHESTRATOR_AVAILABLE'
]

# Add traditional orchestrator items if available
if TRADITIONAL_ORCHESTRATOR_AVAILABLE:
    __all__.extend([
        'WorkflowOrchestrator',
        'WorkflowDefinition', 
        'WorkflowTask',
        'TaskStatus',
        'TaskPriority',
        'orchestrator',
        'create_simple_workflow',
        'create_analysis_workflow'
    ])

# Add LangGraph orchestrator items if available
if LANGGRAPH_ORCHESTRATOR_AVAILABLE:
    __all__.extend([
        'graph_orchestrator',
        'GraphWorkflowOrchestrator',
        'GraphState',
        'GraphWorkflowConfig',
        'RequestType',
        'process_with_graph',
        'stream_with_graph'
    ])
