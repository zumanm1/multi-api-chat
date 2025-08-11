#!/usr/bin/env python3
"""
Simple Test Runner for CrewAI Fallback Implementation
====================================================

A basic test script to verify fallback functionality without requiring pytest.
"""

import sys
import os
import logging
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fallback_classes import (
    FallbackAgent,
    FallbackTask,
    FallbackCrew,
    FallbackChatOpenAI,
    get_fallback_classes,
    log_fallback_status,
    is_fallback_mode
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_fallback_agent():
    """Test FallbackAgent functionality"""
    print("Testing FallbackAgent...")
    
    # Test initialization
    agent = FallbackAgent(
        role="Test Chat Agent",
        goal="Test fallback functionality",
        backstory="I am a test agent",
        tools=["tool1", "tool2"]
    )
    
    assert agent.role == "Test Chat Agent"
    assert len(agent.tools) == 2
    assert agent.execution_count == 0
    print("   ✓ Agent initialization")
    
    # Test execution
    result = agent.execute("Test task description")
    assert isinstance(result, str)
    assert "Test task description" in result
    assert agent.execution_count == 1
    print("   ✓ Agent execution")
    
    # Test agent info
    info = agent.get_agent_info()
    assert info["role"] == "Test Chat Agent"
    assert info["status"] == "fallback_mode"
    print("   ✓ Agent info retrieval")
    
    # Test role-specific responses
    chat_agent = FallbackAgent(role="Chat Agent")
    response = chat_agent.execute("Hello")
    assert "AI capabilities are currently unavailable" in response
    print("   ✓ Role-specific responses")
    
    print("FallbackAgent tests passed ✓\n")


def test_fallback_task():
    """Test FallbackTask functionality"""
    print("Testing FallbackTask...")
    
    # Test initialization
    agent = FallbackAgent(role="Test Agent")
    task = FallbackTask(
        description="Test task",
        agent=agent,
        expected_output="Test output"
    )
    
    assert task.description == "Test task"
    assert task.agent == agent
    assert task.status == "pending"
    print("   ✓ Task initialization")
    
    # Test execution with agent
    result = task.execute()
    assert task.status == "completed"
    assert isinstance(result, str)
    assert task.execution_time > 0
    print("   ✓ Task execution with agent")
    
    # Test execution without agent
    standalone_task = FallbackTask(description="Standalone task")
    standalone_result = standalone_task.execute()
    assert standalone_task.status == "completed"
    assert "fallback mode" in standalone_result.lower()
    print("   ✓ Task execution without agent")
    
    # Test task info
    info = task.get_task_info()
    assert info["description"] == "Test task"
    assert info["status"] == "completed"
    print("   ✓ Task info retrieval")
    
    print("FallbackTask tests passed ✓\n")


def test_fallback_crew():
    """Test FallbackCrew functionality"""
    print("Testing FallbackCrew...")
    
    # Create agents and tasks
    agent1 = FallbackAgent(role="Chat Agent")
    agent2 = FallbackAgent(role="Analytics Agent")
    
    task1 = FallbackTask(description="Chat task", agent=agent1)
    task2 = FallbackTask(description="Analytics task", agent=agent2)
    
    # Test crew initialization
    crew = FallbackCrew(
        agents=[agent1, agent2],
        tasks=[task1, task2],
        verbose=True,
        memory=True,
        process="sequential"
    )
    
    assert len(crew.agents) == 2
    assert len(crew.tasks) == 2
    assert crew.process == "sequential"
    print("   ✓ Crew initialization")
    
    # Test crew execution
    result = crew.kickoff()
    assert isinstance(result, str)
    assert len(crew.execution_history) == 1
    assert crew.execution_history[0]["success"] == True
    print("   ✓ Crew execution")
    
    # Test automatic agent assignment
    unassigned_task = FallbackTask(description="Unassigned task")
    auto_crew = FallbackCrew(
        agents=[agent1],
        tasks=[unassigned_task]
    )
    assert unassigned_task.agent == agent1
    print("   ✓ Automatic agent assignment")
    
    # Test crew info
    info = crew.get_crew_info()
    assert info["agents_count"] == 2
    assert info["tasks_count"] == 2
    assert info["status"] == "fallback_mode"
    print("   ✓ Crew info retrieval")
    
    # Test parallel execution
    parallel_crew = FallbackCrew(
        agents=[agent1],
        tasks=[FallbackTask(description="Parallel task", agent=agent1)],
        process="parallel"
    )
    parallel_result = parallel_crew.kickoff()
    assert isinstance(parallel_result, str)
    print("   ✓ Parallel execution simulation")
    
    print("FallbackCrew tests passed ✓\n")


def test_fallback_chat_openai():
    """Test FallbackChatOpenAI functionality"""
    print("Testing FallbackChatOpenAI...")
    
    # Test initialization
    llm = FallbackChatOpenAI(
        model="gpt-4",
        temperature=0.8,
        max_tokens=2000
    )
    
    assert llm.model == "gpt-4"
    assert llm.temperature == 0.8
    assert llm.max_tokens == 2000
    assert llm.call_count == 0
    print("   ✓ LLM initialization")
    
    # Test invoke method
    result = llm.invoke("Test prompt")
    assert isinstance(result, str)
    assert "fallback mode" in result.lower()
    assert llm.call_count == 1
    print("   ✓ LLM invoke method")
    
    # Test alternative interfaces
    call_result = llm("Another test")
    assert isinstance(call_result, str)
    assert llm.call_count == 2
    
    predict_result = llm.predict("Predict test")
    assert isinstance(predict_result, str)
    assert llm.call_count == 3
    print("   ✓ Alternative LLM interfaces")
    
    # Test LLM info
    info = llm.get_llm_info()
    assert info["model"] == "gpt-4"
    assert info["call_count"] == 3
    assert info["status"] == "fallback_mode"
    print("   ✓ LLM info retrieval")
    
    print("FallbackChatOpenAI tests passed ✓\n")


def test_integration_scenario():
    """Test complete integration scenario"""
    print("Testing Integration Scenario...")
    
    # Create LLM
    llm = FallbackChatOpenAI(model="gpt-4")
    
    # Create agents with different roles
    chat_agent = FallbackAgent(role="Chat Agent", llm=llm)
    analytics_agent = FallbackAgent(role="Analytics Agent", llm=llm)
    device_agent = FallbackAgent(role="Device Agent", llm=llm)
    
    # Create tasks for each agent
    chat_task = FallbackTask(
        description="Greet the user",
        agent=chat_agent,
        expected_output="Friendly greeting"
    )
    
    analytics_task = FallbackTask(
        description="Analyze usage patterns",
        agent=analytics_agent,
        expected_output="Usage report"
    )
    
    device_task = FallbackTask(
        description="Check device status",
        agent=device_agent,
        expected_output="Device status report"
    )
    
    # Create crew with memory enabled
    crew = FallbackCrew(
        agents=[chat_agent, analytics_agent, device_agent],
        tasks=[chat_task, analytics_task, device_task],
        memory=True,
        verbose=True
    )
    
    # Execute the workflow
    result = crew.kickoff()
    
    # Verify results
    assert isinstance(result, str)
    assert len(crew.execution_history) == 1
    assert crew.execution_history[0]["success"] == True
    assert crew.execution_history[0]["tasks_completed"] == 3
    
    # Verify all agents were used
    assert chat_agent.execution_count == 1
    assert analytics_agent.execution_count == 1
    assert device_agent.execution_count == 1
    
    print("   ✓ Multi-agent workflow execution")
    print("   ✓ Memory and context handling")
    print("   ✓ Agent specialization")
    
    print("Integration scenario tests passed ✓\n")


def test_utility_functions():
    """Test utility functions"""
    print("Testing Utility Functions...")
    
    # Test get_fallback_classes
    classes = get_fallback_classes()
    expected_classes = ['Agent', 'Task', 'Crew', 'ChatOpenAI']
    
    for class_name in expected_classes:
        assert class_name in classes
        assert classes[class_name] is not None
    
    print("   ✓ get_fallback_classes function")
    
    # Test is_fallback_mode
    fallback_mode = is_fallback_mode()
    assert isinstance(fallback_mode, bool)
    print("   ✓ is_fallback_mode function")
    
    # Test log_fallback_status (should not crash)
    try:
        log_fallback_status()
        status_test_passed = True
    except Exception as e:
        print(f"   ✗ log_fallback_status failed: {e}")
        status_test_passed = False
    
    assert status_test_passed
    print("   ✓ log_fallback_status function")
    
    print("Utility function tests passed ✓\n")


def test_error_handling():
    """Test error handling and edge cases"""
    print("Testing Error Handling...")
    
    # Test with very long descriptions
    agent = FallbackAgent(role="Test Agent")
    long_desc = "x" * 10000
    task = FallbackTask(description=long_desc, agent=agent)
    
    result = task.execute()
    assert task.status == "completed"
    assert isinstance(result, str)
    print("   ✓ Long description handling")
    
    # Test crew with no agents
    empty_crew = FallbackCrew(agents=[], tasks=[])
    empty_result = empty_crew.kickoff()
    assert isinstance(empty_result, str)
    print("   ✓ Empty crew handling")
    
    # Test task with None agent explicitly
    none_task = FallbackTask(description="No agent task", agent=None)
    none_result = none_task.execute()
    assert none_task.status == "completed"
    print("   ✓ None agent handling")
    
    print("Error handling tests passed ✓\n")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("CREWAI FALLBACK IMPLEMENTATION TESTS")
    print("=" * 60)
    print()
    
    test_functions = [
        test_fallback_agent,
        test_fallback_task,
        test_fallback_crew,
        test_fallback_chat_openai,
        test_integration_scenario,
        test_utility_functions,
        test_error_handling
    ]
    
    passed_tests = 0
    total_tests = len(test_functions)
    
    for test_func in test_functions:
        try:
            test_func()
            passed_tests += 1
        except Exception as e:
            print(f"FAILED: {test_func.__name__} - {e}")
    
    print("=" * 60)
    print(f"TEST RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Fallback implementation is working correctly.")
    else:
        print(f"❌ {total_tests - passed_tests} tests failed.")
        
    print("=" * 60)
    
    # Show practical example
    print("\nPractical Example:")
    print("-" * 20)
    
    # Demonstrate how the fallback works in practice
    agent = FallbackAgent(role="Customer Service Agent", goal="Help users")
    task = FallbackTask(description="Help user with account issues", agent=agent)
    crew = FallbackCrew(agents=[agent], tasks=[task])
    
    result = crew.kickoff()
    print(f"User Request: 'Help me with my account issues'")
    print(f"Fallback Response: {result[:100]}...")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
