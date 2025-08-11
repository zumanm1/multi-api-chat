# Enhanced AI Agent Base Tools

## Overview

The `base_tools.py` file has been significantly enhanced to support actual CrewAI tools with comprehensive fallback implementations. This provides a robust foundation for AI agents with specialized tools for data analysis, device management, automation, and more.

## Key Features

### ✅ CrewAI Integration
- **Actual CrewAI Import**: Attempts to import real CrewAI tools (`crewai_tools.BaseTool`, `crewai.tools.tool`)
- **Fallback Implementation**: Uses custom implementation when CrewAI is not available
- **Seamless Compatibility**: Tools work the same way regardless of CrewAI availability

### ✅ Platform Context & Session Data
- **PlatformContext Class**: Manages platform-wide context and user preferences
- **User Preferences Integration**: Automatically loads user preferences from rules:
  - Connection method: `telnet` (user prefers telnet over SSH)
  - Python version: `3.11` (user's preferred version)
  - Tech stack: Flask, Streamlit, ChromaDB, SQLite, Netmiko, Nornir, etc.
  - Testing framework: `pytest`
  - Deployment: No Docker preference

### ✅ Comprehensive Tool Set

#### Core Tools
1. **AgentContextTool** - User context management across agents
2. **AgentCommunicationTool** - Inter-agent communication and coordination
3. **TaskSchedulerTool** - Task scheduling and management
4. **ChatHistoryTool** - Conversation history management

#### Specialized Tools
5. **DataAnalysisTool** - Statistical analysis, visualization, data insights
6. **DeviceManagementTool** - Network device management with telnet support
7. **AutomationTool** - Workflow automation and orchestration
8. **DatabaseTool** - SQLite/database operations
9. **APIIntegrationTool** - API calls with caching and rate limiting

#### Functional Tools
10. **api_call_tool** - HTTP API calls with error handling
11. **file_operations_tool** - Safe file operations
12. **system_info_tool** - System metrics and information

## User Preference Integration

The tools automatically respect user preferences loaded from rules:

```python
# Device connections use telnet (not SSH)
device_tool._run('connect', device_id='device_1')
# Returns: {"connection_method": "telnet", ...}

# Database operations use SQLite (user's preferred DB)
db_tool._run('connect', db_name='mydb')
# Returns: {"type": "sqlite", ...}

# Tech stack aligns with user preferences
# Python, Flask, Streamlit, ChromaDB, SQLite, Netmiko, Nornir
```

## Tool Categories

Tools are organized into 7 categories:

- **Core** (4 tools): Basic agent functionality
- **API Integration** (3 tools): External API management
- **Data Analysis** (4 tools): Analytics and visualization
- **Device Management** (5 tools): Network device operations
- **Automation** (4 tools): Workflow and task automation
- **Database** (2 tools): Data storage operations
- **System** (3 tools): System monitoring and file operations

## Usage Examples

### Basic Tool Usage

```python
from tools.base_tools import *

# Get available tools
tools = get_agent_tools(['data_analysis_tool', 'device_management_tool'])

# Use data analysis
data_tool = DataAnalysisTool()
result = data_tool._run('analyze', data=[1,2,3,4,5], analysis_type='basic')

# Use device management with telnet
device_tool = DeviceManagementTool()
scan_result = device_tool._run('scan')  # Discover devices
connect_result = device_tool._run('connect', device_id='device_1')  # Uses telnet
```

### Platform Context Access

```python
# Access user preferences
print(platform_context.user_preferences['connection_method'])  # 'telnet'
print(platform_context.user_preferences['python_version'])     # '3.11'

# Set session data
platform_context.set_session_data('current_user', 'admin')
platform_context.set_api_key('openai', 'sk-...')
```

### Tool Information

```python
# List available tools
tools = list_available_tools()  # Returns list of 27+ tools

# Get tool categories
categories = get_tools_by_category()
# Returns: {'core': [...], 'data_analysis': [...], ...}

# Get platform status
status = get_platform_status()
# Returns comprehensive platform and tool status
```

## Error Handling & Fallbacks

- **Import Fallbacks**: Gracefully falls back when CrewAI is unavailable
- **Tool Error Handling**: All tools have try/catch error handling
- **Logging Integration**: Proper logging for debugging and monitoring
- **Validation**: Tool dependencies and configurations are validated

## Testing

The implementation includes comprehensive testing:

```bash
# Run the demo
python3 ai_agents/tools/demo_tools.py

# Test tool functionality
python3 -c "from tools.base_tools import *; print('Tools loaded:', len(AVAILABLE_TOOLS))"
```

## Architecture Benefits

1. **Scalable**: Easy to add new tools to the registry
2. **Configurable**: User preferences automatically applied
3. **Robust**: Works with or without CrewAI dependencies
4. **Integrated**: Platform context shared across all tools
5. **Consistent**: Uniform interface for all tool types
6. **Maintainable**: Clear separation of concerns and documentation

## Future Enhancements

- [ ] Real HTTP requests (currently simulated)
- [ ] Actual database connections
- [ ] Real network device connections via Netmiko
- [ ] Advanced data analysis with pandas/scipy
- [ ] Enhanced visualization capabilities
- [ ] Performance monitoring and metrics
- [ ] Tool usage analytics

This enhanced implementation provides a solid foundation for AI agents that can perform complex tasks while respecting user preferences and maintaining platform integration.
