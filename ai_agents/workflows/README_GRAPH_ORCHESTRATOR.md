# LangGraph Agent Workflow Orchestrator

## Overview

The LangGraph Agent Workflow Orchestrator is an advanced workflow management system that provides sophisticated coordination for multi-agent interactions using LangGraph's state-based workflow capabilities.

## Key Features

### 🔄 Graph-Based Workflows
- **State-driven execution**: Workflows maintain state across multiple execution steps
- **Complex coordination**: Support for conditional edges and branching logic
- **Multi-agent orchestration**: Coordinate multiple specialized agents in a single workflow

### 📊 Request Type Support
- **Chat workflows**: Conversational interactions and help requests
- **Analytics workflows**: Data analysis, metrics generation, and insights
- **Device workflows**: Device discovery, status checking, and management
- **Operations workflows**: System monitoring, health checks, and alerts
- **Automation workflows**: Process automation and workflow optimization
- **Hybrid workflows**: Complex multi-domain requests involving multiple agent types

### 💾 Persistence & Recovery
- **Checkpoint system**: Save workflow state at regular intervals
- **Recovery mechanisms**: Resume interrupted workflows from checkpoints
- **Session management**: Track and manage active workflow sessions

### 🔗 Integration Features
- **MasterAgent integration**: Seamless integration with existing CrewAI-based agents
- **Fallback support**: Graceful degradation when LangGraph is not available
- **Streaming support**: Real-time workflow execution monitoring

## Architecture

### Core Components

1. **GraphWorkflowOrchestrator**: Main orchestrator class
2. **GraphState**: Typed state schema for workflow execution
3. **Request Types**: Enumeration of supported workflow types
4. **Workflow Graphs**: Individual graph definitions for each request type

### Integration Points

- **MasterAgent**: Enhanced with graph orchestration capabilities
- **Traditional Orchestrator**: Fallback when LangGraph is unavailable
- **Agent Systems**: Works with existing CrewAI and simple master agents

## Usage Examples

### Basic Usage

```python
from ai_agents.workflows.graph_orchestrator import graph_orchestrator

# Process a request with graph orchestration
result = await graph_orchestrator.process_request(
    request="Analyze system performance and check device status",
    context={"priority": "high"},
    request_type="hybrid"
)
```

### Streaming Workflow

```python
# Stream workflow execution
async for chunk in graph_orchestrator.stream_workflow(
    request="Comprehensive network analysis",
    context={"detailed": True},
    request_type="analytics"
):
    print(f"Progress: {chunk}")
```

### MasterAgent Integration

```python
from ai_agents.agents.master_agent import get_master_agent

master_agent = get_master_agent()

# Process with automatic orchestration selection
result = await master_agent.process_user_request(
    request="Provide comprehensive analysis and automation suggestions",
    source_page="analytics"
)

# Force graph orchestration
result = await master_agent.process_with_preferred_orchestration(
    request="Complex multi-step analysis",
    prefer_graph=True
)
```

### Checkpoint Management

```python
# Save workflow checkpoint
session_id = "workflow_123"
state = {"progress": 0.5, "results": {...}}
graph_orchestrator.save_checkpoint(session_id, state)

# Load workflow checkpoint
recovered_state = graph_orchestrator.load_checkpoint(session_id)

# Cleanup old checkpoints
cleaned = graph_orchestrator.cleanup_old_sessions(max_age_hours=24)
```

## Workflow Types

### 1. Chat Workflow
- **Purpose**: Handle conversational requests and provide help
- **Nodes**: chat_analyzer → chat_responder
- **Use Cases**: General queries, explanations, guidance

### 2. Analytics Workflow  
- **Purpose**: Data analysis and metrics generation
- **Nodes**: data_collector → analytics_processor
- **Use Cases**: Performance analysis, trend identification, reporting

### 3. Device Workflow
- **Purpose**: Device management and monitoring
- **Nodes**: device_discovery → device_status_check
- **Use Cases**: Device health checks, configuration, troubleshooting

### 4. Operations Workflow
- **Purpose**: System operations and monitoring
- **Nodes**: operations_assessment
- **Use Cases**: System health, alerts, operational status

### 5. Automation Workflow
- **Purpose**: Process automation and optimization
- **Nodes**: automation_analyzer
- **Use Cases**: Workflow optimization, automation suggestions

### 6. Hybrid Workflow
- **Purpose**: Complex multi-domain requests
- **Nodes**: request_router → coordinator → response_synthesizer
- **Use Cases**: Comprehensive analysis, multi-step processes

## Configuration

### GraphWorkflowConfig

```python
from ai_agents.workflows.graph_orchestrator import GraphWorkflowConfig, RequestType

config = GraphWorkflowConfig(
    request_type=RequestType.HYBRID,
    max_iterations=10,
    enable_checkpoints=True,
    checkpoint_interval=5,
    recovery_enabled=True,
    parallel_execution=False,
    agent_timeout=30.0,
    workflow_timeout=300.0
)
```

### Configuration Options

- **max_iterations**: Maximum workflow iterations (default: 10)
- **enable_checkpoints**: Enable checkpoint saving (default: True)
- **checkpoint_interval**: Save checkpoint every N steps (default: 5)
- **recovery_enabled**: Enable workflow recovery (default: True)
- **parallel_execution**: Enable parallel node execution (default: False)
- **agent_timeout**: Timeout for individual agents (default: 30.0s)
- **workflow_timeout**: Total workflow timeout (default: 300.0s)

## State Management

### GraphState Schema

```python
class GraphState(TypedDict):
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
```

### State Features

- **Message tracking**: Full conversation history
- **Result accumulation**: Aggregate results from all agents
- **Error handling**: Track and manage execution errors
- **Metadata**: Workflow execution information
- **Persistence**: Checkpoint and recovery support

## Error Handling

### Fallback Mechanisms

1. **LangGraph unavailable**: Falls back to CrewAI orchestration
2. **Workflow failure**: Graceful error responses with details
3. **Agent failures**: Continue workflow with error tracking
4. **Timeout handling**: Controlled workflow termination

### Error Recovery

- **Checkpoint recovery**: Resume from last successful state
- **Retry logic**: Configurable retry attempts for failed operations
- **Circuit breaker**: Prevent cascade failures

## Monitoring & Debugging

### Session Management

```python
# Get session status
status = graph_orchestrator.get_session_status(session_id)

# Get all active sessions
all_sessions = graph_orchestrator.active_sessions

# Get orchestration capabilities
capabilities = graph_orchestrator.get_orchestration_capabilities()
```

### Workflow Information

```python
# List available workflows
workflows = graph_orchestrator.get_available_workflows()

# Get workflow details
info = graph_orchestrator.get_workflow_info("hybrid")
```

## Best Practices

### When to Use Graph Orchestration

1. **Complex multi-step workflows** requiring state management
2. **Multi-agent coordination** with dependencies between agents
3. **Long-running processes** that benefit from checkpointing
4. **Conditional workflow execution** based on intermediate results

### When to Use Traditional Orchestration

1. **Simple single-step tasks** without complex dependencies
2. **High-performance scenarios** requiring minimal overhead
3. **Legacy compatibility** with existing CrewAI workflows

### Performance Optimization

1. **Configure appropriate timeouts** for your use case
2. **Use parallel execution** for independent operations
3. **Set reasonable checkpoint intervals** to balance persistence and performance
4. **Clean up old sessions** regularly to prevent memory bloat

## Dependencies

### Required Dependencies
- **LangGraph**: Core graph orchestration framework
- **langchain-core**: Message and runnable abstractions

### Optional Dependencies
- **CrewAI**: For agent integration and fallback
- **langchain-openai**: For LLM-powered agents

### Installation

```bash
# Install LangGraph
pip install langgraph langchain-core

# Optional: Install CrewAI for full integration
pip install crewai langchain-openai
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure LangGraph is installed
2. **Agent initialization failures**: Check agent dependencies
3. **Checkpoint errors**: Verify filesystem permissions
4. **Memory issues**: Configure session cleanup

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing

Run the integration test suite:

```bash
python -m ai_agents.workflows.test_graph_integration
```

## Future Enhancements

### Planned Features

1. **Conditional edges**: Dynamic workflow routing
2. **Parallel execution**: True parallel agent coordination  
3. **Workflow templates**: Pre-built workflow patterns
4. **Performance metrics**: Detailed execution analytics
5. **Visual workflow designer**: GUI for workflow creation

### Extension Points

- **Custom workflow types**: Add domain-specific workflows
- **External integrations**: Connect to external systems
- **Advanced persistence**: Database-backed checkpointing
- **Monitoring integrations**: Metrics and alerting systems

## Contributing

To contribute to the graph orchestrator:

1. Follow the existing code patterns
2. Add comprehensive tests for new features
3. Update documentation for new capabilities
4. Consider backward compatibility

## License

This module is part of the Multi-API Chat Platform and follows the same licensing terms.
