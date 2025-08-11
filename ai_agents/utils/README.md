# AI Agents Utilities

This directory contains utility modules for AI agent functionality.

## Dependency Checker

The `dependency_checker.py` module provides comprehensive functionality for checking, validating, and installing AI agent dependencies.

### Features

- ✅ **Dependency Verification**: Check if all required AI packages are installed
- ✅ **Version Validation**: Verify that installed packages meet version requirements
- ✅ **Environment Assessment**: Validate Python version and environment setup
- ✅ **Automatic Installation**: Install missing dependencies via pip
- ✅ **Detailed Logging**: Comprehensive status reporting and recommendations
- ✅ **Integration Support**: Easy integration with backend services

### Dependencies Managed

The dependency checker manages the following AI packages:

1. **Core AI Agent Frameworks**
   - `crewai` (>=0.41.0) - Main CrewAI framework
   - `crewai-tools` (>=0.4.0) - CrewAI tools library
   - `langgraph` (>=0.0.20) - LangGraph for agent workflow orchestration

2. **LangChain Framework**
   - `langchain` (>=0.1.0) - LangChain framework
   - `langchain-openai` (>=0.0.5) - OpenAI integration for LangChain

3. **Core Dependencies**
   - `pydantic` (>=2.0.0) - Data validation
   - `tiktoken` (>=0.5.0) - Token counting for LLM interactions
   - `aiohttp` (>=3.9.0) - Async HTTP client for API calls

4. **Vector Database and Numerical Operations**
   - `chromadb` (>=0.4.0) - Vector database for agent memory
   - `numpy` (<2.0.0) - Numerical operations (pinned for compatibility)

### Usage

#### Programmatic Usage

```python
from ai_agents.utils.dependency_checker import (
    check_ai_dependencies,
    get_missing_dependencies,
    install_ai_dependencies,
    log_dependency_status,
    validate_ai_environment
)

# Check all dependencies
status = check_ai_dependencies()
print(f"All installed: {status['all_installed']}")
print(f"Missing: {len(status['missing_packages'])}")

# Get missing packages
missing = get_missing_dependencies()
for pkg in missing:
    print(f"Missing: {pkg['package']} - {pkg['description']}")

# Validate environment
env_status = validate_ai_environment()
if not env_status['environment_ready']:
    for rec in env_status['recommendations']:
        print(f"Recommendation: {rec}")

# Install dependencies
result = install_ai_dependencies()
if result['success']:
    print("Dependencies installed successfully!")
else:
    print(f"Installation failed: {result['message']}")

# Log detailed status
log_dependency_status()
```

#### Command Line Usage

A CLI tool is provided for easy dependency management:

```bash
# Check dependency status
python check_ai_deps.py check

# Check with verbose output
python check_ai_deps.py check -v

# Show detailed status report
python check_ai_deps.py status

# List all dependencies
python check_ai_deps.py list

# List dependencies with descriptions
python check_ai_deps.py list -d

# Install missing dependencies (with confirmation)
python check_ai_deps.py install

# Install without confirmation
python check_ai_deps.py install -y
```

### Integration with Backend

The dependency checker is integrated into the backend services:

```python
from backend_ai_integration import (
    get_ai_dependency_status,
    check_ai_dependencies_sync,
    install_ai_dependencies_sync
)

# Get dependency status
status = get_ai_dependency_status()

# Check dependencies synchronously
dep_check = check_ai_dependencies_sync()

# Install dependencies synchronously
install_result = install_ai_dependencies_sync()
```

### Application Startup Integration

The dependency checker is automatically run during application startup:

1. **AI Agent Integration**: Checks dependencies when initializing `AIAgentIntegration`
2. **Backend Integration**: Validates dependencies in `AIBackendIntegration`
3. **Detailed Logging**: Provides clear status messages and recommendations
4. **Fallback Mode**: Gracefully handles missing dependencies

### Error Handling

The dependency checker includes robust error handling:

- **Missing packaging library**: Falls back to simple version comparison
- **Import errors**: Gracefully handles unavailable modules
- **Network issues**: Provides helpful error messages for installation failures
- **Permission issues**: Clear guidance for installation problems

### Environment Validation

The system validates:

- ✅ Python version (3.8+ required, 3.11 preferred)
- ✅ pip availability
- ✅ Requirements file existence
- ✅ Package installation status
- ✅ Version compatibility

### Recommendations

Based on the environment assessment, the system provides actionable recommendations:

- Python version upgrade suggestions
- Missing package installation commands
- Version conflict resolution
- Environment optimization tips

### Testing

The dependency checker includes comprehensive tests:

```bash
# Test the dependency checker directly
python ai_agents/utils/dependency_checker.py

# Run standalone tests
python test_dependency_standalone.py

# Test CLI functionality
python check_ai_deps.py check
```

### Files

- `dependency_checker.py` - Main dependency checking module
- `__init__.py` - Module initialization and exports
- `README.md` - This documentation file

### Requirements File

The system uses `requirements-ai-agents.txt` to define all AI dependencies with specific version constraints. This file is separate from the main `requirements.txt` to avoid conflicts with the base application dependencies.
