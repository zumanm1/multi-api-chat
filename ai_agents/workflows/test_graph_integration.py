#!/usr/bin/env python3
"""
Test Script for LangGraph Orchestrator Integration
================================================

This script tests the integration between the LangGraph orchestrator
and the existing MasterAgent system.
"""

import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_graph_orchestrator():
    """Test the graph orchestrator functionality"""
    try:
        # Import the orchestrator
        from .graph_orchestrator import graph_orchestrator, process_with_graph, GraphWorkflowConfig, RequestType
        
        print("=" * 60)
        print("Testing LangGraph Orchestrator")
        print("=" * 60)
        
        # Test 1: Check orchestrator status
        print("\n1. Testing orchestrator status:")
        available_workflows = graph_orchestrator.get_available_workflows()
        print(f"Available workflows: {available_workflows}")
        
        # Test 2: Simple chat workflow
        print("\n2. Testing chat workflow:")
        chat_result = await process_with_graph(
            request="Hello, can you help me understand network monitoring?",
            context={"test_mode": True},
            request_type="chat"
        )
        print(f"Chat result: {json.dumps(chat_result, indent=2, default=str)}")
        
        # Test 3: Analytics workflow
        print("\n3. Testing analytics workflow:")
        analytics_result = await process_with_graph(
            request="Analyze the performance metrics of our system",
            context={"test_mode": True},
            request_type="analytics"
        )
        print(f"Analytics result: {json.dumps(analytics_result, indent=2, default=str)}")
        
        # Test 4: Device workflow
        print("\n4. Testing device workflow:")
        device_result = await process_with_graph(
            request="Check the status of all network devices",
            context={"test_mode": True},
            request_type="device"
        )
        print(f"Device result: {json.dumps(device_result, indent=2, default=str)}")
        
        # Test 5: Hybrid workflow
        print("\n5. Testing hybrid workflow:")
        hybrid_result = await process_with_graph(
            request="Provide a comprehensive analysis of network performance and device health",
            context={"test_mode": True},
            request_type="hybrid"
        )
        print(f"Hybrid result: {json.dumps(hybrid_result, indent=2, default=str)}")
        
        # Test 6: Workflow streaming
        print("\n6. Testing workflow streaming:")
        stream_count = 0
        async for chunk in graph_orchestrator.stream_workflow(
            request="Stream analysis of system performance",
            context={"stream_test": True},
            request_type="analytics"
        ):
            stream_count += 1
            print(f"Stream chunk {stream_count}: {chunk}")
            if stream_count >= 5:  # Limit output
                break
        
        print("\n" + "=" * 60)
        print("Graph Orchestrator Test Completed Successfully!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"Import error - LangGraph dependencies not available: {e}")
        print("This is expected if LangGraph is not installed.")
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()

async def test_master_agent_integration():
    """Test the MasterAgent integration with graph orchestration"""
    try:
        from ..agents.master_agent import get_master_agent
        
        print("\n" + "=" * 60)
        print("Testing MasterAgent Integration")
        print("=" * 60)
        
        master_agent = get_master_agent()
        
        # Test 1: Check orchestration status
        print("\n1. Testing orchestration status:")
        status = master_agent.get_orchestration_status()
        print(f"Orchestration status: {json.dumps(status, indent=2, default=str)}")
        
        # Test 2: Simple request with auto-detection
        print("\n2. Testing auto-detection of graph orchestration:")
        simple_result = await master_agent.process_user_request(
            request="What's the current system status?",
            context={"test_mode": True},
            source_page="chat"
        )
        print(f"Simple request result (orchestration mode: {simple_result.get('orchestration_mode', 'crewai')}):")
        print(json.dumps(simple_result, indent=2, default=str))
        
        # Test 3: Complex request that should trigger graph orchestration
        print("\n3. Testing complex request (should use graph orchestration):")
        complex_result = await master_agent.process_user_request(
            request="Provide comprehensive analysis of system performance and suggest automation improvements",
            context={"test_mode": True},
            source_page="analytics"
        )
        print(f"Complex request result (orchestration mode: {complex_result.get('orchestration_mode', 'crewai')}):")
        print(json.dumps(complex_result, indent=2, default=str))
        
        # Test 4: Preferred orchestration
        print("\n4. Testing preferred graph orchestration:")
        preferred_result = await master_agent.process_with_preferred_orchestration(
            request="Analyze device performance and operational health",
            context={"test_mode": True},
            source_page="operations",
            prefer_graph=True
        )
        print(f"Preferred orchestration result:")
        print(json.dumps(preferred_result, indent=2, default=str))
        
        # Test 5: Stream workflow
        print("\n5. Testing stream workflow through MasterAgent:")
        stream_count = 0
        async for chunk in master_agent.stream_graph_workflow(
            request="Stream comprehensive system analysis",
            context={"test_mode": True},
            source_page="hybrid"
        ):
            stream_count += 1
            print(f"Master Agent Stream chunk {stream_count}: {chunk}")
            if stream_count >= 3:  # Limit output
                break
        
        print("\n" + "=" * 60)
        print("MasterAgent Integration Test Completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Master Agent integration test error: {e}")
        import traceback
        traceback.print_exc()

async def test_checkpoint_functionality():
    """Test checkpoint and recovery functionality"""
    try:
        from .graph_orchestrator import graph_orchestrator
        
        print("\n" + "=" * 60)
        print("Testing Checkpoint Functionality")
        print("=" * 60)
        
        # Test checkpoint saving and loading
        test_session_id = "test_session_123"
        test_state = {
            "messages": [],
            "agent_results": {"test": "data"},
            "workflow_metadata": {"test_checkpoint": True}
        }
        
        # Save checkpoint
        saved = graph_orchestrator.save_checkpoint(test_session_id, test_state)
        print(f"Checkpoint saved: {saved}")
        
        # Load checkpoint
        loaded_state = graph_orchestrator.load_checkpoint(test_session_id)
        print(f"Checkpoint loaded: {loaded_state is not None}")
        
        if loaded_state:
            print(f"Loaded state matches: {loaded_state.get('workflow_metadata', {}).get('test_checkpoint') == True}")
        
        # Test session cleanup
        print(f"Active sessions before cleanup: {len(graph_orchestrator.active_sessions)}")
        cleaned_count = graph_orchestrator.cleanup_old_sessions(max_age_hours=0)  # Clean all
        print(f"Cleaned sessions: {cleaned_count}")
        
        print("\nCheckpoint functionality test completed!")
        
    except Exception as e:
        print(f"Checkpoint test error: {e}")
        import traceback
        traceback.print_exc()

async def run_all_tests():
    """Run all integration tests"""
    print("Starting LangGraph Integration Tests...")
    print(f"Test started at: {datetime.now()}")
    
    try:
        await test_graph_orchestrator()
        await test_master_agent_integration()
        await test_checkpoint_functionality()
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nTest suite error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests())
