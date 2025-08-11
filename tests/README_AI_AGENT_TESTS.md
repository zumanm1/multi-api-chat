# AI Agent Integration Test Suite

This comprehensive test suite provides complete coverage for the AI agent functionality in the Multi-API Chat Platform.

## Overview

The test suite (`test_ai_agents.py`) is designed to work **both with and without AI dependencies installed**, demonstrating the robust fallback behavior of the system.

## Features Tested

### ✅ Core Integration
- AI agent initialization and configuration
- Singleton pattern for integration instances
- Status reporting and health checks
- Error handling and recovery

### ✅ CrewAI Availability Scenarios
- **When CrewAI is available**: Full AI functionality, agent coordination, workflow execution
- **When CrewAI is NOT available**: Graceful fallback behavior, informative error messages

### ✅ Individual Agent Types
- **Chat Agent**: Conversational AI responses
- **Analytics Agent**: Data analysis and insights
- **Device Agent**: Network device management 
- **Operations Agent**: System operations and monitoring
- **Automation Agent**: Workflow automation and scheduling

### ✅ Cross-Page Request Handling
- Device → Analytics integration
- Operations → Automation coordination
- Multi-page workflow orchestration
- Context preservation across pages

### ✅ LangGraph Workflow Execution
- Graph-based workflow orchestration
- Streaming workflow execution
- Complex multi-step agent coordination
- Checkpoint and recovery mechanisms

### ✅ Fallback Behavior
- Dependency checking and validation
- Graceful degradation when components fail
- Informative fallback messages
- System stability without AI dependencies

### ✅ Performance and Reliability
- Response time monitoring
- Memory usage stability
- Concurrent request handling
- Error recovery mechanisms

## Test Organization

```
TestAIAgentIntegration          # Core integration functionality
TestCrewAIAvailable            # Tests when dependencies available
TestCrewAINotAvailable         # Tests when dependencies missing
TestAgentTypes                 # Individual agent testing
TestCrossPageRequests          # Cross-page communication
TestLangGraphWorkflow          # LangGraph orchestration
TestFallbackBehavior           # Comprehensive fallback testing
TestRealisticScenarios         # Real-world usage scenarios
TestPerformanceAndStress       # Performance validation
TestUtilities                  # Helper functions and utilities
```

## Running the Tests

### Option 1: Use the Test Runner (Recommended)
```bash
python run_ai_agent_tests.py
```

This script will:
- Install pytest if needed
- Check AI dependency status
- Run tests with appropriate expectations
- Provide detailed results and recommendations

### Option 2: Direct pytest Execution
```bash
# Install pytest first if needed
pip install pytest

# Run all AI agent tests
pytest tests/test_ai_agents.py -v

# Run specific test classes
pytest tests/test_ai_agents.py::TestAgentTypes -v

# Run tests with detailed output
pytest tests/test_ai_agents.py -v --tb=short -r a
```

## Test Fixtures and Mocking

The test suite includes comprehensive mocking capabilities:

### 🔧 CrewAI Component Mocking
- `mock_crewai_components`: Mocks Agent, Task, Crew, and LLM classes
- `mock_crewai_available/not_available`: Controls dependency availability
- Ensures tests work regardless of actual CrewAI installation

### 🔧 LangGraph Component Mocking  
- `mock_langgraph_components`: Mocks StateGraph and workflow execution
- Stream simulation for testing async workflows
- Graph compilation and execution testing

### 🔧 Dependency Status Mocking
- `mock_ai_dependencies_satisfied/missing`: Simulates different dependency states
- Environment validation testing
- Installation recommendation testing

### 🔧 Test Data Fixtures
- `sample_ai_request`: Standard AI request format
- `sample_cross_page_request`: Cross-page communication scenarios
- Realistic test data for various scenarios

## Expected Test Results

### With AI Dependencies Installed ✅
- All integration tests should pass
- Agent coordination tests succeed
- LangGraph workflow tests execute
- Performance tests validate response times

### Without AI Dependencies Installed ✅  
- Fallback behavior tests pass
- System remains stable and functional
- Clear error messages and guidance provided
- Graceful degradation demonstrated

## Test Coverage Areas

1. **Initialization and Configuration**
   - System startup with/without dependencies
   - Configuration validation
   - Agent registration and setup

2. **Request Processing**
   - Chat message handling
   - Analytics request processing  
   - Device management operations
   - Operations and monitoring tasks
   - Automation workflow creation

3. **Error Handling**
   - Missing dependency scenarios
   - Network/service failures
   - Invalid request handling
   - Recovery mechanisms

4. **Performance**
   - Response time validation
   - Memory usage monitoring
   - Concurrent request handling
   - Load testing scenarios

5. **Integration**
   - Cross-agent communication
   - Multi-page workflows
   - Context preservation
   - State management

## Continuous Integration Support

The test suite is designed for CI/CD environments:

- **No external dependencies required** for basic functionality testing
- **Graceful handling** of missing AI components
- **Clear pass/fail criteria** based on available components
- **Comprehensive reporting** of test results and system status

## Maintenance and Extension

### Adding New Tests
1. Follow existing test class patterns
2. Use appropriate `@pytest.mark.skipif` decorators for conditional tests
3. Mock external dependencies appropriately
4. Include both success and failure scenarios

### Updating for New Agent Types
1. Add agent-specific test methods to `TestAgentTypes`
2. Include cross-page integration tests if relevant
3. Update mock fixtures as needed
4. Document new functionality in this README

## Dependencies

### Required (Automatically Installed)
- `pytest` - Test framework
- Standard library modules (`unittest.mock`, `asyncio`, etc.)

### Optional (Gracefully Handled if Missing)
- `crewai` - AI agent framework
- `langchain` - LangChain framework
- `langchain-openai` - OpenAI integration
- `langgraph` - Graph workflow orchestration
- `chromadb` - Vector database

The test suite demonstrates that the application works robustly with or without these optional dependencies installed.

## Key Benefits

1. **Comprehensive Coverage**: Tests all major AI agent functionality
2. **Dependency Resilience**: Works with or without AI dependencies
3. **Real-world Scenarios**: Includes practical usage examples
4. **Performance Validation**: Ensures system responsiveness
5. **Maintainability**: Well-organized, documented, and extensible
6. **CI/CD Ready**: Suitable for automated testing environments

## Example Test Output

```
=============================== test session starts ================================
platform linux -- Python 3.11, pytest-8.4.1, pluggy-1.6.0 -- /usr/bin/python
cachedir: .pytest_cache
rootdir: /path/to/project

tests/test_ai_agents.py::TestAIAgentIntegration::test_ai_integration_initialization PASSED
tests/test_ai_agents.py::TestCrewAINotAvailable::test_fallback_chat_response PASSED  
tests/test_ai_agents.py::TestAgentTypes::test_chat_agent_functionality PASSED
tests/test_ai_agents.py::TestCrossPageRequests::test_cross_page_request_handling PASSED
tests/test_ai_agents.py::TestFallbackBehavior::test_complete_fallback_workflow PASSED

========================== 85 passed, 12 skipped in 2.45s ===========================
```

This comprehensive test suite ensures the AI agent integration is robust, reliable, and ready for production use.
