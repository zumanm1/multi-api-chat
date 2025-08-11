#!/usr/bin/env python3
"""
Test script for CrewAI Fallback Implementation Classes
=====================================================

This test script verifies that the fallback classes work correctly
when CrewAI dependencies are not available, ensuring the application
remains functional in all scenarios.
"""

import pytest
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ai_agents.fallback_classes import (
    FallbackAgent,
    FallbackTask,
    FallbackCrew,
    FallbackChatOpenAI,
    get_fallback_classes,
    log_fallback_status,
    is_fallback_mode
)

# Configure logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFallbackAgent:
    """Test the FallbackAgent class"""
    
    def test_agent_initialization(self):
        """Test agent initialization with various parameters"""
        # Test default initialization
        agent = FallbackAgent()
        assert agent.role == "Fallback Assistant"
        assert agent.goal == "Provide basic assistance when AI is not available"
        assert agent.execution_count == 0
        
        # Test custom initialization
        custom_agent = FallbackAgent(
            role="Test Chat Agent",
            goal="Test goal",
            backstory="Test backstory",
            verbose=False,
            memory=False,
            tools=["tool1", "tool2"],
            max_execution_time=60
        )
        
        assert custom_agent.role == "Test Chat Agent"
        assert custom_agent.goal == "Test goal"
        assert custom_agent.backstory == "Test backstory"
        assert custom_agent.verbose == False
        assert custom_agent.memory == False
        assert len(custom_agent.tools) == 2
        assert custom_agent.max_execution_time == 60
    
    def test_agent_execution(self):
        """Test agent execution functionality"""
        agent = FallbackAgent(role="Chat Assistant")
        
        # Test basic execution
        result = agent.execute("Test task description")
        assert isinstance(result, str)
        assert "Test task description" in result
        assert agent.execution_count == 1
        
        # Test execution with context
        context = {"user_id": "test123", "session": "active"}
        result2 = agent.execute("Another test", context)
        assert isinstance(result2, str)
        assert agent.execution_count == 2
    
    def test_role_specific_responses(self):
        """Test that agents respond differently based on their role"""
        # Test chat agent
        chat_agent = FallbackAgent(role="Chat Agent")
        chat_response = chat_agent.execute("Hello, how are you?")
        assert "AI capabilities are currently unavailable" in chat_response
        
        # Test analytics agent
        analytics_agent = FallbackAgent(role="Analytics Agent")
        analytics_response = analytics_agent.execute("Show me data trends")
        assert "AI-powered data analysis is currently unavailable" in analytics_response
        
        # Test device agent
        device_agent = FallbackAgent(role="Device Management Agent")
        device_response = device_agent.execute("Check device status")
        assert "AI device management features are currently unavailable" in device_response
    
    def test_agent_info(self):
        """Test agent information retrieval"""
        agent = FallbackAgent(role="Test Agent", tools=["tool1", "tool2"])
        info = agent.get_agent_info()
        
        assert info["role"] == "Test Agent"
        assert info["status"] == "fallback_mode"
        assert info["execution_count"] == 0
        assert info["tools_count"] == 2
        assert info["memory_enabled"] == True
        assert "created_at" in info


class TestFallbackTask:
    """Test the FallbackTask class"""
    
    def test_task_initialization(self):
        """Test task initialization"""
        # Test default initialization
        task = FallbackTask()
        assert task.description == "Fallback task"
        assert task.status == "pending"
        assert task.result is None
        
        # Test custom initialization
        agent = FallbackAgent(role="Test Agent")
        custom_task = FallbackTask(
            description="Custom task",
            agent=agent,
            expected_output="Custom output",
            tools=["tool1"]
        )
        
        assert custom_task.description == "Custom task"
        assert custom_task.agent == agent
        assert custom_task.expected_output == "Custom output"
        assert len(custom_task.tools) == 1
    
    def test_task_execution_with_agent(self):
        """Test task execution with an assigned agent"""
        agent = FallbackAgent(role="Test Agent")
        task = FallbackTask(
            description="Test task with agent",
            agent=agent
        )
        
        result = task.execute()
        
        assert task.status == "completed"
        assert isinstance(result, str)
        assert task.result == result
        assert task.execution_time > 0
        assert agent.execution_count == 1
    
    def test_task_execution_without_agent(self):
        """Test task execution without an assigned agent"""
        task = FallbackTask(description="Test task without agent")
        
        result = task.execute()
        
        assert task.status == "completed"
        assert isinstance(result, str)
        assert "fallback mode" in result.lower()
        assert task.execution_time > 0
    
    def test_task_info(self):
        """Test task information retrieval"""
        agent = FallbackAgent(role="Test Agent")
        task = FallbackTask(
            description="Test task",
            agent=agent,
            expected_output="Test output"
        )
        
        # Execute task first
        task.execute()
        
        info = task.get_task_info()
        
        assert info["description"] == "Test task"
        assert info["status"] == "completed"
        assert info["agent"] == "Test Agent"
        assert info["expected_output"] == "Test output"
        assert info["execution_time"] > 0
        assert "created_at" in info


class TestFallbackCrew:
    """Test the FallbackCrew class"""
    
    def test_crew_initialization(self):
        """Test crew initialization"""
        agent1 = FallbackAgent(role="Agent 1")
        agent2 = FallbackAgent(role="Agent 2")
        
        task1 = FallbackTask(description="Task 1")
        task2 = FallbackTask(description="Task 2")
        
        crew = FallbackCrew(
            agents=[agent1, agent2],
            tasks=[task1, task2],
            verbose=True,
            memory=True,
            process="sequential"
        )
        
        assert len(crew.agents) == 2
        assert len(crew.tasks) == 2
        assert crew.verbose == True
        assert crew.memory == True
        assert crew.process == "sequential"
        assert len(crew.execution_history) == 0
    
    def test_crew_agent_task_assignment(self):
        """Test automatic agent assignment to tasks"""
        agent1 = FallbackAgent(role="Agent 1")
        agent2 = FallbackAgent(role="Agent 2")
        
        task1 = FallbackTask(description="Task 1")  # No agent assigned
        task2 = FallbackTask(description="Task 2")  # No agent assigned
        
        crew = FallbackCrew(
            agents=[agent1, agent2],
            tasks=[task1, task2]
        )
        
        # Tasks should be automatically assigned agents
        assert task1.agent is not None
        assert task2.agent is not None
        assert task1.agent in [agent1, agent2]
        assert task2.agent in [agent1, agent2]
    
    def test_crew_sequential_execution(self):
        """Test sequential crew execution"""
        agent1 = FallbackAgent(role="Chat Agent")
        agent2 = FallbackAgent(role="Analytics Agent")
        
        task1 = FallbackTask(description="Chat task", agent=agent1)
        task2 = FallbackTask(description="Analytics task", agent=agent2)
        
        crew = FallbackCrew(
            agents=[agent1, agent2],
            tasks=[task1, task2],
            process="sequential"
        )
        
        result = crew.kickoff()
        
        assert isinstance(result, str)
        assert "fallback mode" in result.lower()
        assert len(crew.execution_history) == 1
        assert crew.execution_history[0]["success"] == True
        assert crew.execution_history[0]["tasks_completed"] == 2
    
    def test_crew_parallel_execution(self):
        """Test parallel crew execution (simulated)"""
        agent1 = FallbackAgent(role="Agent 1")
        task1 = FallbackTask(description="Task 1", agent=agent1)
        
        crew = FallbackCrew(
            agents=[agent1],
            tasks=[task1],
            process="parallel"
        )
        
        result = crew.kickoff()
        
        assert isinstance(result, str)
        assert len(crew.execution_history) == 1
        assert crew.execution_history[0]["success"] == True
    
    def test_crew_info(self):
        """Test crew information retrieval"""
        agent = FallbackAgent(role="Test Agent")
        task = FallbackTask(description="Test Task", agent=agent)
        
        crew = FallbackCrew(
            agents=[agent],
            tasks=[task],
            verbose=False,
            memory=False
        )
        
        info = crew.get_crew_info()
        
        assert info["agents_count"] == 1
        assert info["tasks_count"] == 1
        assert info["process"] == "sequential"
        assert info["execution_count"] == 0
        assert info["memory_enabled"] == False
        assert info["verbose"] == False
        assert info["status"] == "fallback_mode"


class TestFallbackChatOpenAI:
    """Test the FallbackChatOpenAI class"""
    
    def test_llm_initialization(self):
        """Test LLM initialization"""
        # Test default initialization
        llm = FallbackChatOpenAI()
        assert llm.model == "gpt-3.5-turbo"
        assert llm.temperature == 0.7
        assert llm.max_tokens == 1000
        assert llm.call_count == 0
        
        # Test custom initialization
        custom_llm = FallbackChatOpenAI(
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000
        )
        
        assert custom_llm.model == "gpt-4"
        assert custom_llm.temperature == 0.5
        assert custom_llm.max_tokens == 2000
    
    def test_llm_invoke(self):
        """Test LLM invoke method"""
        llm = FallbackChatOpenAI()
        
        result = llm.invoke("Test prompt")
        
        assert isinstance(result, str)
        assert "fallback mode" in result.lower()
        assert llm.call_count == 1
    
    def test_llm_alternative_interfaces(self):
        """Test alternative LLM calling interfaces"""
        llm = FallbackChatOpenAI()
        
        # Test __call__ interface
        result1 = llm("Test prompt 1")
        assert isinstance(result1, str)
        assert llm.call_count == 1
        
        # Test predict interface
        result2 = llm.predict("Test prompt 2")
        assert isinstance(result2, str)
        assert llm.call_count == 2
    
    def test_llm_info(self):
        """Test LLM information retrieval"""
        llm = FallbackChatOpenAI(model="gpt-4", temperature=0.8)
        
        # Make a call to increment counter
        llm.invoke("Test")
        
        info = llm.get_llm_info()
        
        assert info["model"] == "gpt-4"
        assert info["temperature"] == 0.8
        assert info["call_count"] == 1
        assert info["status"] == "fallback_mode"
        assert "created_at" in info


class TestIntegrationScenarios:
    """Test integration scenarios with fallback classes"""
    
    def test_complete_workflow_simulation(self):
        """Test a complete workflow using all fallback classes"""
        # Create LLM
        llm = FallbackChatOpenAI(model="gpt-4")
        
        # Create agents with LLM
        chat_agent = FallbackAgent(
            role="Chat Agent",
            goal="Handle conversations",
            llm=llm
        )
        
        analytics_agent = FallbackAgent(
            role="Analytics Agent",
            goal="Analyze data",
            llm=llm
        )
        
        # Create tasks
        chat_task = FallbackTask(
            description="Respond to user greeting",
            agent=chat_agent,
            expected_output="Friendly response"
        )
        
        analytics_task = FallbackTask(
            description="Analyze user behavior",
            agent=analytics_agent,
            expected_output="Usage statistics"
        )
        
        # Create crew
        crew = FallbackCrew(
            agents=[chat_agent, analytics_agent],
            tasks=[chat_task, analytics_task],
            verbose=True,
            memory=True
        )
        
        # Execute workflow
        result = crew.kickoff()
        
        # Verify results
        assert isinstance(result, str)
        assert len(crew.execution_history) == 1
        assert crew.execution_history[0]["success"] == True
        assert chat_agent.execution_count == 1
        assert analytics_agent.execution_count == 1
    
    def test_error_handling(self):
        """Test error handling in fallback implementations"""
        # Create an agent that might encounter errors
        agent = FallbackAgent(role="Test Agent")
        
        # Create a task with very long description to test edge cases
        long_description = "x" * 10000
        task = FallbackTask(description=long_description, agent=agent)
        
        # Execute task - should handle gracefully
        result = task.execute()
        
        assert task.status == "completed"
        assert isinstance(result, str)
        assert agent.execution_count == 1
    
    def test_memory_and_context_handling(self):
        """Test memory and context handling across tasks"""
        agent = FallbackAgent(role="Memory Test Agent")
        
        task1 = FallbackTask(
            description="First task",
            agent=agent,
            context={"step": 1}
        )
        
        task2 = FallbackTask(
            description="Second task",
            agent=agent,
            context={"step": 2}
        )
        
        crew = FallbackCrew(
            agents=[agent],
            tasks=[task1, task2],
            memory=True
        )
        
        result = crew.kickoff()
        
        # Verify that context was passed between tasks
        assert isinstance(result, str)
        assert agent.execution_count == 2
        
        # Check task context was updated with memory
        assert "previous_results" in task2.context
        assert task2.context["task_sequence"] == 2


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_get_fallback_classes(self):
        """Test get_fallback_classes function"""
        classes = get_fallback_classes()
        
        assert "Agent" in classes
        assert "Task" in classes
        assert "Crew" in classes
        assert "ChatOpenAI" in classes
        
        assert classes["Agent"] == FallbackAgent
        assert classes["Task"] == FallbackTask
        assert classes["Crew"] == FallbackCrew
        assert classes["ChatOpenAI"] == FallbackChatOpenAI
    
    def test_is_fallback_mode(self):
        """Test is_fallback_mode function"""
        # This test depends on whether CrewAI is actually installed
        fallback_mode = is_fallback_mode()
        assert isinstance(fallback_mode, bool)
    
    def test_log_fallback_status(self):
        """Test log_fallback_status function"""
        # This should not raise any exceptions
        try:
            log_fallback_status()
            success = True
        except Exception as e:
            success = False
            print(f"Error in log_fallback_status: {e}")
        
        assert success == True


def run_comprehensive_test():
    """Run a comprehensive test of all fallback functionality"""
    print("=" * 60)
    print("COMPREHENSIVE FALLBACK CLASSES TEST")
    print("=" * 60)
    
    # Test basic functionality
    print("\n1. Testing Agent Creation and Execution...")
    agent = FallbackAgent(role="Test Agent", goal="Test fallback functionality")
    result = agent.execute("Test task")
    print(f"   ✓ Agent executed task: {result[:50]}...")
    
    # Test task functionality
    print("\n2. Testing Task Creation and Execution...")
    task = FallbackTask(description="Test task", agent=agent)
    task_result = task.execute()
    print(f"   ✓ Task completed with status: {task.status}")
    
    # Test crew functionality
    print("\n3. Testing Crew Creation and Execution...")
    crew = FallbackCrew(agents=[agent], tasks=[task])
    crew_result = crew.kickoff()
    print(f"   ✓ Crew executed successfully: {len(crew.execution_history)} execution(s)")
    
    # Test LLM functionality
    print("\n4. Testing LLM Fallback...")
    llm = FallbackChatOpenAI(model="gpt-4")
    llm_result = llm.invoke("Test prompt")
    print(f"   ✓ LLM responded: {llm_result[:50]}...")
    
    # Test integration scenario
    print("\n5. Testing Complete Integration Scenario...")
    
    # Create multiple agents for different roles
    agents = [
        FallbackAgent(role="Chat Agent", goal="Handle conversations"),
        FallbackAgent(role="Analytics Agent", goal="Analyze data"),
        FallbackAgent(role="Device Agent", goal="Manage devices")
    ]
    
    # Create tasks for each agent
    tasks = [
        FallbackTask(description="Greet the user", agent=agents[0]),
        FallbackTask(description="Analyze user behavior", agent=agents[1]),
        FallbackTask(description="Check device status", agent=agents[2])
    ]
    
    # Create and execute crew
    integration_crew = FallbackCrew(agents=agents, tasks=tasks, memory=True)
    integration_result = integration_crew.kickoff()
    
    print(f"   ✓ Integration test completed with {len(integration_crew.execution_history)} execution(s)")
    
    # Show status summary
    print("\n6. Final Status Summary...")
    print(f"   - Total agents created: {len(agents) + 1}")
    print(f"   - Total tasks executed: {sum(agent.execution_count for agent in agents) + agent.execution_count}")
    print(f"   - Total crew executions: {len(integration_crew.execution_history)}")
    print(f"   - LLM calls made: {llm.call_count}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("Fallback implementation is working correctly.")
    print("=" * 60)


if __name__ == "__main__":
    # Run the comprehensive test
    run_comprehensive_test()
    
    # Also run pytest if available
    try:
        import pytest
        print("\n\nRunning detailed pytest tests...")
        pytest.main([__file__, "-v"])
    except ImportError:
        print("\npytest not available, skipping detailed tests")
        print("Install pytest to run detailed test suite: pip install pytest")
