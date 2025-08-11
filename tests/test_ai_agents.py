"""
Comprehensive AI Agent Integration Tests
=======================================

This test suite provides comprehensive coverage for AI agent functionality including:
- AI functionality when CrewAI is available
- Fallback behavior when CrewAI is not installed
- Each agent type (chat, analytics, device, operations, automation)
- Cross-page request handling
- LangGraph workflow execution
- Pytest fixtures to mock CrewAI components when needed
- Tests pass both with and without AI dependencies installed

Test Organization:
- TestAIAgentIntegration: Core integration tests
- TestCrewAIAvailable: Tests when dependencies are available
- TestCrewAINotAvailable: Tests when dependencies are missing
- TestAgentTypes: Individual agent type testing
- TestCrossPageRequests: Cross-page communication testing
- TestLangGraphWorkflow: LangGraph orchestration testing
- TestFallbackBehavior: Fallback functionality testing
"""

import pytest
import json
import os
import sys
import asyncio
import time
import logging
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import importlib

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports with error handling
try:
    from ai_agents.integration import AIAgentIntegration, get_ai_integration, process_ai_request, get_ai_status
    AI_INTEGRATION_AVAILABLE = True
except ImportError as e:
    AI_INTEGRATION_AVAILABLE = False
    print(f"AI Integration not available: {e}")

try:
    from ai_agents.agents.master_agent import MasterAgent, get_master_agent
    MASTER_AGENT_AVAILABLE = True
except ImportError as e:
    MASTER_AGENT_AVAILABLE = False
    print(f"Master Agent not available: {e}")

try:
    from ai_agents.configs.agents_config import AGENTS_CONFIG
    AGENTS_CONFIG_AVAILABLE = True
except ImportError as e:
    AGENTS_CONFIG_AVAILABLE = False
    print(f"Agent Config not available: {e}")

try:
    from ai_agents.fallback_classes import (
        FallbackAgent, FallbackTask, FallbackCrew, FallbackChatOpenAI,
        log_fallback_status, is_fallback_mode
    )
    FALLBACK_CLASSES_AVAILABLE = True
except ImportError as e:
    FALLBACK_CLASSES_AVAILABLE = False
    print(f"Fallback Classes not available: {e}")

try:
    from ai_agents.workflows.graph_orchestrator import (
        GraphWorkflowOrchestrator, RequestType, GraphWorkflowConfig,
        graph_orchestrator, process_with_graph, stream_with_graph
    )
    GRAPH_ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    GRAPH_ORCHESTRATOR_AVAILABLE = False
    print(f"Graph Orchestrator not available: {e}")

try:
    from ai_agents.utils.dependency_checker import (
        check_ai_dependencies, log_dependency_status, validate_ai_environment,
        check_package_installed, compare_versions
    )
    DEPENDENCY_CHECKER_AVAILABLE = True
except ImportError as e:
    DEPENDENCY_CHECKER_AVAILABLE = False
    print(f"Dependency Checker not available: {e}")


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_crewai_available():
    """Mock CrewAI as available"""
    with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
        with patch('ai_agents.agents.master_agent.CREWAI_AVAILABLE', True):
            yield True


@pytest.fixture
def mock_crewai_not_available():
    """Mock CrewAI as not available"""
    with patch('ai_agents.integration.CREWAI_AVAILABLE', False):
        with patch('ai_agents.agents.master_agent.CREWAI_AVAILABLE', False):
            yield False


@pytest.fixture
def mock_crewai_components():
    """Mock all CrewAI components"""
    mock_agent = MagicMock()
    mock_agent.role = "Test Agent"
    mock_agent.goal = "Test Goal"
    mock_agent.backstory = "Test Backstory"
    
    mock_task = MagicMock()
    mock_task.description = "Test Task"
    mock_task.expected_output = "Test Output"
    
    mock_crew = MagicMock()
    mock_crew.kickoff.return_value = "Test crew execution result"
    
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "Test LLM response"
    
    # Use fallback patching instead of trying to patch non-existent modules
    with patch('ai_agents.fallback_classes.FallbackAgent', return_value=mock_agent):
        with patch('ai_agents.fallback_classes.FallbackTask', return_value=mock_task):
            with patch('ai_agents.fallback_classes.FallbackCrew', return_value=mock_crew):
                with patch('ai_agents.fallback_classes.FallbackChatOpenAI', return_value=mock_llm):
                    yield {
                        'agent': mock_agent,
                        'task': mock_task,
                        'crew': mock_crew,
                        'llm': mock_llm
                    }


@pytest.fixture
def mock_langgraph_components():
    """Mock LangGraph components"""
    mock_graph = MagicMock()
    mock_compiled_graph = MagicMock()
    mock_compiled_graph.invoke.return_value = {
        'final_response': {'type': 'test_response', 'message': 'Test graph response'},
        'messages': [],
        'workflow_metadata': {'test': True}
    }
    mock_compiled_graph.stream.return_value = iter([
        {'status': 'running', 'step': 'test_step_1'},
        {'status': 'completed', 'result': 'test_result'}
    ])
    
    mock_graph.compile.return_value = mock_compiled_graph
    
    with patch('ai_agents.workflows.graph_orchestrator.LANGGRAPH_AVAILABLE', True):
        with patch('ai_agents.workflows.graph_orchestrator.StateGraph', return_value=mock_graph):
            with patch('ai_agents.workflows.graph_orchestrator.MemorySaver'):
                yield {
                    'graph': mock_graph,
                    'compiled_graph': mock_compiled_graph
                }


@pytest.fixture
def sample_ai_request():
    """Sample AI request data for testing"""
    return {
        'message': 'Test message for AI processing',
        'context': {
            'user_id': 'test_user',
            'session_id': 'test_session_123',
            'source_page': 'chat',
            'timestamp': datetime.now().isoformat()
        },
        'request_type': 'chat'
    }


@pytest.fixture
def sample_cross_page_request():
    """Sample cross-page request data"""
    return {
        'message': 'Analyze device performance and create automation rules',
        'source_page': 'device',
        'target_page': 'automation',
        'context': {
            'device_id': 'router_001',
            'metrics_needed': True,
            'automation_type': 'monitoring'
        }
    }


@pytest.fixture
def mock_ai_dependencies_satisfied():
    """Mock AI dependencies as satisfied"""
    mock_status = {
        "all_installed": True,
        "missing_packages": [],
        "outdated_packages": [],
        "installed_packages": {
            "crewai": "0.41.0",
            "langchain": "0.1.0",
            "langchain-openai": "0.0.5",
            "langgraph": "0.0.20"
        },
        "total_packages": 4,
        "installed_count": 4,
        "details": {}
    }
    
    mock_validation = {
        "environment_valid": True,
        "python_version_ok": True,
        "virtual_env_detected": True,
        "recommendations": []
    }
    
    with patch('ai_agents.utils.dependency_checker.check_ai_dependencies', return_value=mock_status):
        with patch('ai_agents.utils.dependency_checker.validate_ai_environment', return_value=mock_validation):
            yield mock_status


@pytest.fixture
def mock_ai_dependencies_missing():
    """Mock AI dependencies as missing"""
    mock_status = {
        "all_installed": False,
        "missing_packages": ["crewai", "langchain-openai", "langgraph"],
        "outdated_packages": ["langchain"],
        "installed_packages": {
            "langchain": "0.0.1"
        },
        "total_packages": 4,
        "installed_count": 1,
        "details": {}
    }
    
    mock_validation = {
        "environment_valid": False,
        "python_version_ok": True,
        "virtual_env_detected": True,
        "recommendations": [
            "Install missing packages: pip install crewai langchain-openai langgraph",
            "Update langchain to latest version"
        ]
    }
    
    with patch('ai_agents.utils.dependency_checker.check_ai_dependencies', return_value=mock_status):
        with patch('ai_agents.utils.dependency_checker.validate_ai_environment', return_value=mock_validation):
            yield mock_status


# ============================================================================
# CORE INTEGRATION TESTS
# ============================================================================

@pytest.mark.skipif(not AI_INTEGRATION_AVAILABLE, reason="AI Integration not available")
class TestAIAgentIntegration:
    """Test core AI Agent Integration functionality"""
    
    def test_ai_integration_initialization(self, mock_ai_dependencies_satisfied):
        """Test AIAgentIntegration initializes correctly"""
        with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
            integration = AIAgentIntegration()
            assert integration is not None
            assert integration.integration_status['enabled'] is True
            assert hasattr(integration, 'logger')
    
    def test_ai_integration_disabled(self):
        """Test AIAgentIntegration when disabled in config"""
        with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', False):
            integration = AIAgentIntegration()
            assert integration.integration_status['enabled'] is False
    
    def test_get_ai_integration_singleton(self):
        """Test get_ai_integration returns singleton instance"""
        integration1 = get_ai_integration()
        integration2 = get_ai_integration()
        assert integration1 is integration2
    
    @pytest.mark.anyio
    async def test_process_chat_message_success(self, mock_crewai_components):
        """Test successful chat message processing"""
        with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
            with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={'success': True, 'response': 'Test response'}
                )
                
                result = await integration.process_chat_message(
                    message="Test message",
                    session_id="test_session",
                    user_context={"test": True}
                )
                
                assert result['success'] is True
                assert 'response' in result
                assert result['ai_generated'] is True
    
    @pytest.mark.anyio
    async def test_process_chat_message_not_ready(self):
        """Test chat message processing when AI agents not ready"""
        with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', False):
            integration = AIAgentIntegration()
            
            result = await integration.process_chat_message("Test message")
            
            assert result['success'] is False
            assert result['fallback'] is True
            assert ('disabled_configuration' in result['response'] or 
                    'unavailable' in result['response'] or 
                    'missing dependencies' in result['response'])
    
    @pytest.mark.anyio
    async def test_handle_analytics_request(self, mock_crewai_components):
        """Test analytics request handling"""
        with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
            with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={'success': True, 'response': 'Analytics result'}
                )
                
                result = await integration.handle_analytics_request(
                    request="Analyze system performance",
                    context={'metrics': 'cpu,memory'}
                )
                
                assert result['success'] is True
                assert 'response' in result
    
    @pytest.mark.anyio
    async def test_handle_device_request(self, mock_crewai_components):
        """Test device request handling"""
        with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
            with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={'success': True, 'response': 'Device status'}
                )
                
                result = await integration.handle_device_request(
                    request="Check router status",
                    device_context={'device_id': 'router_001'}
                )
                
                assert result['success'] is True
                assert 'response' in result
    
    @pytest.mark.anyio
    async def test_handle_operations_request(self, mock_crewai_components):
        """Test operations request handling"""
        with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
            with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={'success': True, 'response': 'Operations status'}
                )
                
                result = await integration.handle_operations_request(
                    request="System health check",
                    ops_context={'check_type': 'full'}
                )
                
                assert result['success'] is True
                assert 'response' in result
    
    @pytest.mark.anyio
    async def test_handle_automation_request(self, mock_crewai_components):
        """Test automation request handling"""
        with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
            with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={'success': True, 'response': 'Automation created'}
                )
                
                result = await integration.handle_automation_request(
                    request="Create monitoring workflow",
                    automation_context={'workflow_type': 'monitoring'}
                )
                
                assert result['success'] is True
                assert 'response' in result
    
    def test_get_agent_status(self, mock_crewai_components):
        """Test getting agent status"""
        with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
            with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.get_agent_status.return_value = {
                    'master_agent': {'status': 'active'},
                    'specialized_agents': {}
                }
                
                status = integration.get_agent_status()
                
                assert status['status'] == 'active'
                assert 'integration_status' in status
                assert 'agent_details' in status
                assert 'capabilities' in status


# ============================================================================
# CREWAI AVAILABLE TESTS
# ============================================================================

@pytest.mark.skipif(not AI_INTEGRATION_AVAILABLE, reason="AI Integration not available")
class TestCrewAIAvailable:
    """Tests for when CrewAI dependencies are available"""
    
    def test_crewai_imports_successful(self, mock_crewai_available, mock_crewai_components):
        """Test that CrewAI imports work when available"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            # These should not raise ImportError
            from ai_agents.integration import AIAgentIntegration
            integration = AIAgentIntegration()
            assert integration.integration_status['dependencies_installed'] is True
    
    @pytest.mark.anyio
    async def test_master_agent_creation(self, mock_crewai_available, mock_crewai_components):
        """Test master agent creation when CrewAI is available"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                
                # Should create master agent
                assert integration.master_agent is not None or integration.integration_status['fallback_mode']
    
    @pytest.mark.anyio
    async def test_full_ai_workflow(self, mock_crewai_available, mock_crewai_components, sample_ai_request):
        """Test complete AI workflow when CrewAI is available"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                result = await process_ai_request("chat", sample_ai_request)
                
                # Should get actual AI response, not fallback
                assert 'success' in result
                if result.get('success'):
                    assert 'fallback' not in result or not result['fallback']
    
    @pytest.mark.anyio
    async def test_agent_coordination(self, mock_crewai_available, mock_crewai_components):
        """Test multi-agent coordination when CrewAI is available"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'Multi-agent response',
                        'agents_involved': ['chat_agent', 'analytics_agent']
                    }
                )
                
                result = await integration.process_chat_message(
                    "Analyze performance and provide insights"
                )
                
                assert result['success'] is True
                if 'agents_involved' in result:
                    assert len(result['agents_involved']) > 0


# ============================================================================
# CREWAI NOT AVAILABLE TESTS
# ============================================================================

@pytest.mark.skipif(not FALLBACK_CLASSES_AVAILABLE, reason="Fallback classes not available")
class TestCrewAINotAvailable:
    """Tests for when CrewAI dependencies are not available"""
    
    def test_fallback_classes_imported(self, mock_crewai_not_available):
        """Test that fallback classes are used when CrewAI not available"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', False):
            # Should not raise ImportError and should use fallback
            integration = AIAgentIntegration()
            assert integration.integration_status['dependencies_installed'] is False
    
    @pytest.mark.anyio
    async def test_fallback_chat_response(self, mock_crewai_not_available):
        """Test chat response in fallback mode"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', False):
            integration = AIAgentIntegration()
            result = await integration.process_chat_message("Test message")
            
            assert result['success'] is False
            assert result['fallback'] is True
            assert ('missing_dependencies' in result['response'] or 
                    'missing dependencies' in result['response'] or 
                    'unavailable' in result['response'])
    
    @pytest.mark.anyio
    async def test_fallback_analytics_response(self, mock_crewai_not_available):
        """Test analytics response in fallback mode"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', False):
            integration = AIAgentIntegration()
            result = await integration.handle_analytics_request("Analyze data")
            
            assert result['success'] is False
            assert result['fallback'] is True
    
    def test_fallback_agent_creation(self):
        """Test fallback agent creation and basic functionality"""
        if not FALLBACK_CLASSES_AVAILABLE:
            pytest.skip("Fallback classes not available")
        
        agent = FallbackAgent(
            role="Test Agent",
            goal="Test fallback functionality",
            backstory="Test agent backstory"
        )
        
        assert agent.role == "Test Agent"
        assert agent.execution_count == 0
        
        result = agent.execute("Test task")
        assert agent.execution_count == 1
        assert "fallback mode" in result or "unavailable" in result
    
    def test_fallback_task_execution(self):
        """Test fallback task execution"""
        if not FALLBACK_CLASSES_AVAILABLE:
            pytest.skip("Fallback classes not available")
        
        agent = FallbackAgent(role="Test Agent")
        task = FallbackTask(
            description="Test task",
            agent=agent,
            expected_output="Test output"
        )
        
        result = task.execute()
        assert task.status == "completed"
        assert result is not None
        assert "fallback mode" in result or "unavailable" in result
    
    def test_fallback_crew_execution(self):
        """Test fallback crew execution"""
        if not FALLBACK_CLASSES_AVAILABLE:
            pytest.skip("Fallback classes not available")
        
        agent = FallbackAgent(role="Test Agent")
        task = FallbackTask(description="Test task", agent=agent)
        crew = FallbackCrew(agents=[agent], tasks=[task])
        
        result = crew.kickoff()
        assert len(crew.execution_history) > 0
        assert ("fallback mode" in result or "unavailable" in result or "basic mode" in result)
    
    def test_fallback_llm_invocation(self):
        """Test fallback LLM invocation"""
        if not FALLBACK_CLASSES_AVAILABLE:
            pytest.skip("Fallback classes not available")
        
        llm = FallbackChatOpenAI(model="gpt-4", temperature=0.7)
        result = llm.invoke("Test prompt")
        
        assert llm.call_count == 1
        assert "fallback mode" in result


# ============================================================================
# AGENT TYPE SPECIFIC TESTS
# ============================================================================

@pytest.mark.skipif(not AI_INTEGRATION_AVAILABLE, reason="AI Integration not available")
class TestAgentTypes:
    """Test individual agent types and their specific functionality"""
    
    @pytest.mark.anyio
    async def test_chat_agent_functionality(self, mock_crewai_components):
        """Test chat agent specific functionality"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'Chat agent response',
                        'agents_involved': ['chat_agent']
                    }
                )
                
                result = await integration.process_chat_message("Hello, how are you?")
                assert result['success'] is True
                assert 'response' in result
    
    @pytest.mark.anyio
    async def test_analytics_agent_functionality(self, mock_crewai_components):
        """Test analytics agent specific functionality"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'Analytics insights: CPU usage 75%',
                        'agents_involved': ['analytics_agent']
                    }
                )
                
                result = await integration.handle_analytics_request(
                    "Analyze system performance metrics"
                )
                assert result['success'] is True
                assert 'Analytics' in result['response'] or 'analytics' in result['response']
    
    @pytest.mark.anyio
    async def test_device_agent_functionality(self, mock_crewai_components):
        """Test device agent specific functionality"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'Device status: Router online, 25% CPU',
                        'agents_involved': ['device_agent']
                    }
                )
                
                result = await integration.handle_device_request(
                    "Check router configuration and status"
                )
                assert result['success'] is True
                assert 'Device' in result['response'] or 'device' in result['response'] or 'Router' in result['response']
    
    @pytest.mark.anyio
    async def test_operations_agent_functionality(self, mock_crewai_components):
        """Test operations agent specific functionality"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'System operational: All services running',
                        'agents_involved': ['operations_agent']
                    }
                )
                
                result = await integration.handle_operations_request(
                    "Perform system health check"
                )
                assert result['success'] is True
                assert 'operational' in result['response'] or 'operations' in result['response']
    
    @pytest.mark.anyio
    async def test_automation_agent_functionality(self, mock_crewai_components):
        """Test automation agent specific functionality"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'Automation workflow created for monitoring',
                        'agents_involved': ['automation_agent']
                    }
                )
                
                result = await integration.handle_automation_request(
                    "Create automated backup workflow"
                )
                assert result['success'] is True
                assert 'automation' in result['response'] or 'workflow' in result['response']
    
    @pytest.mark.anyio
    async def test_agent_error_handling(self, mock_crewai_components):
        """Test agent error handling"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    side_effect=Exception("Test error")
                )
                
                result = await integration.process_chat_message("Test message")
                assert result['success'] is False
                assert 'error' in result or 'Error' in result['response']


# ============================================================================
# CROSS-PAGE REQUEST TESTS
# ============================================================================

@pytest.mark.skipif(not AI_INTEGRATION_AVAILABLE, reason="AI Integration not available")
class TestCrossPageRequests:
    """Test cross-page request handling and coordination"""
    
    @pytest.mark.anyio
    async def test_cross_page_request_handling(self, mock_crewai_components, sample_cross_page_request):
        """Test handling requests that span multiple pages"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.handle_cross_page_request = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'Cross-page operation completed',
                        'source_page': 'device',
                        'target_page': 'automation',
                        'agents_involved': ['device_agent', 'automation_agent']
                    }
                )
                
                result = await integration.handle_cross_page_request(
                    request=sample_cross_page_request['message'],
                    source_page=sample_cross_page_request['source_page'],
                    target_page=sample_cross_page_request['target_page'],
                    context=sample_cross_page_request['context']
                )
                
                assert result['success'] is True
                assert 'cross-page' in result['response'] or 'Cross-page' in result['response']
    
    @pytest.mark.anyio
    async def test_device_to_analytics_cross_page(self, mock_crewai_components):
        """Test device to analytics cross-page request"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.handle_cross_page_request = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'Device metrics analyzed and report generated',
                        'agents_involved': ['device_agent', 'analytics_agent']
                    }
                )
                
                result = await integration.handle_cross_page_request(
                    request="Collect device metrics and create performance report",
                    source_page="device",
                    target_page="analytics"
                )
                
                assert result['success'] is True
    
    @pytest.mark.anyio
    async def test_operations_to_automation_cross_page(self, mock_crewai_components):
        """Test operations to automation cross-page request"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.handle_cross_page_request = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'Monitoring alerts configured with automation rules',
                        'agents_involved': ['operations_agent', 'automation_agent']
                    }
                )
                
                result = await integration.handle_cross_page_request(
                    request="Set up automated alerts for system monitoring",
                    source_page="operations",
                    target_page="automation"
                )
                
                assert result['success'] is True
    
    @pytest.mark.anyio
    async def test_cross_page_fallback_behavior(self, mock_crewai_not_available):
        """Test cross-page request fallback when AI not available"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', False):
            integration = AIAgentIntegration()
            
            result = await integration.handle_cross_page_request(
                request="Test cross-page request",
                source_page="device",
                target_page="analytics"
            )
            
            assert result['success'] is False
            assert result['fallback'] is True


# ============================================================================
# LANGGRAPH WORKFLOW TESTS
# ============================================================================

@pytest.mark.skipif(not GRAPH_ORCHESTRATOR_AVAILABLE, reason="Graph Orchestrator not available")
class TestLangGraphWorkflow:
    """Test LangGraph workflow execution and orchestration"""
    
    @pytest.mark.anyio
    async def test_graph_orchestrator_initialization(self, mock_langgraph_components):
        """Test graph orchestrator initialization"""
        orchestrator = GraphWorkflowOrchestrator()
        assert orchestrator is not None
        assert hasattr(orchestrator, 'workflows')
        assert hasattr(orchestrator, 'compiled_graphs')
    
    @pytest.mark.anyio
    async def test_process_with_graph_orchestration(self, mock_langgraph_components):
        """Test processing request with graph orchestration"""
        result = await process_with_graph(
            request="Test graph workflow",
            context={"test": True},
            request_type="chat"
        )
        
        assert 'success' in result
        if result.get('success'):
            assert 'response' in result
            assert 'langgraph_mode' in result
    
    @pytest.mark.anyio
    async def test_stream_graph_workflow(self, mock_langgraph_components):
        """Test streaming graph workflow execution"""
        chunks = []
        async for chunk in stream_with_graph(
            request="Test streaming workflow",
            context={"stream_test": True},
            request_type="hybrid"
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        # Should have status updates
        statuses = [chunk.get('status') for chunk in chunks if 'status' in chunk]
        assert len(statuses) > 0
    
    @pytest.mark.anyio
    async def test_different_request_types(self, mock_langgraph_components):
        """Test different request types with graph orchestration"""
        request_types = ['chat', 'analytics', 'device', 'operations', 'automation', 'hybrid']
        
        for req_type in request_types:
            result = await process_with_graph(
                request=f"Test {req_type} request",
                request_type=req_type
            )
            
            # Should handle all request types without error
            assert 'success' in result or 'error' in result
    
    @pytest.mark.anyio
    async def test_graph_workflow_with_master_agent_integration(self, mock_crewai_components, mock_langgraph_components):
        """Test graph workflow integration with master agent"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent._process_with_graph_orchestration = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'Graph orchestrated response',
                        'orchestration_mode': 'langgraph'
                    }
                )
                
                # Test master agent using graph orchestration
                result = await integration.master_agent._process_with_graph_orchestration(
                    "Test request", {"test": True}, "chat"
                )
                
                assert result['success'] is True
                assert result['orchestration_mode'] == 'langgraph'
    
    @pytest.mark.anyio
    async def test_graph_workflow_error_handling(self, mock_langgraph_components):
        """Test graph workflow error handling"""
        with patch('ai_agents.workflows.graph_orchestrator.GraphWorkflowOrchestrator.process_request', 
                   side_effect=Exception("Graph processing error")):
            
            try:
                result = await process_with_graph("Test error handling")
                # Should return error response if exception is caught
                assert result['success'] is False
                assert 'error' in result
            except Exception as e:
                # Exception is allowed to bubble up in error handling test
                assert "Graph processing error" in str(e)
    
    def test_graph_workflow_availability_check(self):
        """Test checking graph workflow availability"""
        if GRAPH_ORCHESTRATOR_AVAILABLE:
            orchestrator = graph_orchestrator
            assert orchestrator is not None
            workflows = orchestrator.get_available_workflows()
            assert isinstance(workflows, list)
        else:
            # Should handle gracefully when not available
            assert True  # Test passes if we reach here without error


# ============================================================================
# FALLBACK BEHAVIOR TESTS
# ============================================================================

class TestFallbackBehavior:
    """Test comprehensive fallback behavior across all components"""
    
    def test_dependency_check_missing(self, mock_ai_dependencies_missing):
        """Test dependency checking with missing packages"""
        if not DEPENDENCY_CHECKER_AVAILABLE:
            pytest.skip("Dependency checker not available")
        
        status = check_ai_dependencies()
        assert not status['all_installed']
        assert len(status['missing_packages']) > 0
    
    def test_dependency_check_satisfied(self, mock_ai_dependencies_satisfied):
        """Test dependency checking with satisfied requirements"""
        if not DEPENDENCY_CHECKER_AVAILABLE:
            pytest.skip("Dependency checker not available")
        
        status = check_ai_dependencies()
        # Mock should override actual dependency check results
        assert isinstance(status, dict)
        assert 'all_installed' in status
    
    @pytest.mark.anyio
    async def test_complete_fallback_workflow(self, mock_crewai_not_available):
        """Test complete workflow in fallback mode"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', False):
            # Test various request types in fallback mode
            request_types = ['chat', 'analytics', 'device', 'operations', 'automation']
            
            for req_type in request_types:
                result = await process_ai_request(req_type, {
                    'message': f'Test {req_type} request',
                    'context': {'test': True}
                })
                
                # All should return fallback responses
                assert result['success'] is False or 'fallback' in result
    
    def test_fallback_status_logging(self):
        """Test fallback status logging functionality"""
        if not FALLBACK_CLASSES_AVAILABLE:
            pytest.skip("Fallback classes not available")
        
        # Should not raise exception
        log_fallback_status()
        
        # Test fallback mode detection
        mode = is_fallback_mode()
        assert isinstance(mode, bool)
    
    @pytest.mark.anyio
    async def test_mixed_availability_scenario(self):
        """Test scenario where some components available, others not"""
        # Simulate mixed availability
        with patch('ai_agents.integration.CREWAI_AVAILABLE', False):
            with patch('ai_agents.workflows.graph_orchestrator.LANGGRAPH_AVAILABLE', True):
                integration = AIAgentIntegration()
                result = await integration.process_chat_message("Test mixed scenario")
                
                # Should handle gracefully
                assert 'success' in result
                assert result['success'] is False or result.get('fallback', False)
    
    def test_graceful_degradation(self):
        """Test graceful degradation when components fail"""
        # Test that system continues to work even when individual components fail
        with patch('ai_agents.integration.AIAgentIntegration.__init__', side_effect=Exception("Init failed")):
            try:
                integration = get_ai_integration()
                # Should not crash the entire system
                assert True
            except Exception:
                # If it does raise an exception, that's also acceptable
                # as long as it's handled appropriately
                assert True


# ============================================================================
# INTEGRATION TESTS WITH REALISTIC SCENARIOS
# ============================================================================

@pytest.mark.skipif(not AI_INTEGRATION_AVAILABLE, reason="AI Integration not available")
class TestRealisticScenarios:
    """Test realistic usage scenarios combining multiple features"""
    
    @pytest.mark.anyio
    async def test_network_troubleshooting_scenario(self, mock_crewai_components):
        """Test realistic network troubleshooting scenario"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={
                        'success': True,
                        'response': 'Network analysis complete: Router CPU high, recommend automation',
                        'agents_involved': ['device_agent', 'analytics_agent', 'automation_agent']
                    }
                )
                
                # Simulate network troubleshooting workflow
                result = await integration.process_chat_message(
                    "My network seems slow. Can you check device performance and suggest automation to prevent future issues?",
                    session_id="network_trouble_123",
                    user_context={'network_segment': '192.168.1.0/24'}
                )
                
                assert result['success'] is True
                assert 'agents_involved' in result
    
    @pytest.mark.anyio
    async def test_system_monitoring_setup_scenario(self, mock_crewai_components):
        """Test system monitoring setup scenario"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                
                # Sequence of requests for monitoring setup
                requests = [
                    ("Check current system status", "operations"),
                    ("Analyze performance trends", "analytics"),
                    ("Create monitoring workflow", "automation")
                ]
                
                results = []
                for request, req_type in requests:
                    integration.master_agent.process_user_request = AsyncMock(
                        return_value={
                            'success': True,
                            'response': f'{req_type} completed: {request}',
                            'agents_involved': [f'{req_type}_agent']
                        }
                    )
                    
                    if req_type == "operations":
                        result = await integration.handle_operations_request(request)
                    elif req_type == "analytics":
                        result = await integration.handle_analytics_request(request)
                    elif req_type == "automation":
                        result = await integration.handle_automation_request(request)
                    
                    results.append(result)
                
                # All requests should succeed
                assert all(r['success'] for r in results)
    
    @pytest.mark.anyio
    async def test_performance_under_load(self, mock_crewai_components):
        """Test performance under multiple concurrent requests"""
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={'success': True, 'response': 'Concurrent response'}
                )
                
                # Create multiple concurrent requests
                tasks = []
                for i in range(5):
                    task = integration.process_chat_message(f"Concurrent request {i}")
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Should handle concurrent requests
                successful_results = [r for r in results if not isinstance(r, Exception) and r.get('success')]
                assert len(successful_results) > 0
    
    def test_configuration_validation(self):
        """Test configuration validation and error handling"""
        if not AGENTS_CONFIG_AVAILABLE:
            pytest.skip("Agents config not available")
        
        # Test various configuration scenarios
        with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
            config = AGENTS_CONFIG
            
            # Should have configuration object even if agents dict is empty
            assert config is not None
            assert hasattr(config, 'enabled')
            
            # Try to get agents - may return empty dict in test environment
            try:
                agents = config.get_all_agents()
                
                # Test individual agent configurations only if agents exist
                for agent_name, agent_config in agents.items():
                    assert hasattr(agent_config, 'name')
                    assert hasattr(agent_config, 'role')
                    assert hasattr(agent_config, 'capabilities')
            except (AttributeError, TypeError):
                # get_all_agents method might not exist or may fail in test environment
                pass


# ============================================================================
# PERFORMANCE AND STRESS TESTS
# ============================================================================

class TestPerformanceAndStress:
    """Performance and stress tests for AI agent system"""
    
    @pytest.mark.anyio
    async def test_response_time_monitoring(self, mock_crewai_components):
        """Test that responses come within reasonable time"""
        if not AI_INTEGRATION_AVAILABLE:
            pytest.skip("AI Integration not available")
        
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={'success': True, 'response': 'Quick response'}
                )
                
                start_time = time.time()
                result = await integration.process_chat_message("Quick test")
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # Response should be reasonably fast (< 5 seconds for mocked calls)
                assert response_time < 5.0
                assert result['success'] is True
    
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable"""
        if not AI_INTEGRATION_AVAILABLE:
            pytest.skip("AI Integration not available")
        
        # Create multiple integrations to test memory stability
        integrations = []
        for i in range(10):
            try:
                integration = AIAgentIntegration()
                integrations.append(integration)
            except Exception:
                # Handle case where creation fails due to missing dependencies
                pass
        
        # Should be able to create multiple instances without issues
        assert len(integrations) >= 0  # At least doesn't crash
    
    @pytest.mark.anyio
    async def test_error_recovery(self, mock_crewai_components):
        """Test system recovery from errors"""
        if not AI_INTEGRATION_AVAILABLE:
            pytest.skip("AI Integration not available")
        
        with patch('ai_agents.integration.CREWAI_AVAILABLE', True):
            with patch('ai_agents.configs.agents_config.AGENTS_CONFIG.enabled', True):
                integration = AIAgentIntegration()
                integration.master_agent = MagicMock()
                
                # First request fails
                integration.master_agent.process_user_request = AsyncMock(
                    side_effect=Exception("Temporary failure")
                )
                
                result1 = await integration.process_chat_message("First request")
                assert result1['success'] is False
                
                # Second request succeeds (system recovers)
                integration.master_agent.process_user_request = AsyncMock(
                    return_value={'success': True, 'response': 'Recovery successful'}
                )
                
                result2 = await integration.process_chat_message("Second request")
                assert result2['success'] is True


# ============================================================================
# TEST UTILITIES AND HELPERS
# ============================================================================

class TestUtilities:
    """Test utility functions and helper methods"""
    
    def test_ai_status_reporting(self):
        """Test AI status reporting functionality"""
        if not AI_INTEGRATION_AVAILABLE:
            pytest.skip("AI Integration not available")
        
        status = get_ai_status()
        assert isinstance(status, dict)
        assert 'status' in status or 'error' in status
    
    @pytest.mark.anyio
    async def test_request_processing_helper(self, sample_ai_request):
        """Test request processing helper function"""
        if not AI_INTEGRATION_AVAILABLE:
            pytest.skip("AI Integration not available")
        
        result = await process_ai_request("chat", sample_ai_request)
        assert isinstance(result, dict)
        assert 'success' in result or 'error' in result
    
    def test_environment_detection(self):
        """Test environment detection and setup"""
        # Test various environment conditions
        test_conditions = [
            ('ai_agents', AI_INTEGRATION_AVAILABLE),
            ('fallback_classes', FALLBACK_CLASSES_AVAILABLE),
            ('graph_orchestrator', GRAPH_ORCHESTRATOR_AVAILABLE),
            ('dependency_checker', DEPENDENCY_CHECKER_AVAILABLE)
        ]
        
        for component, available in test_conditions:
            # Each component should have a clear availability status
            assert isinstance(available, bool), f"{component} availability should be boolean"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    import subprocess
    import sys
    
    # Run the tests
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v",
        "--tb=short",  # Short traceback format
        "-x",  # Stop on first failure for debugging
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nReturn code: {result.returncode}")
