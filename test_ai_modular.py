#!/usr/bin/env python3
"""
Test script for modular AI integration
Tests the separated AI modules without circular import issues
"""

import os
import sys
import json
import time
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ai_core():
    """Test the basic AI core module"""
    print("\n=== Testing AI Core Module ===")
    try:
        from ai_core import (
            initialize_ai_core,
            get_cached_ai_status,
            ai_health_check,
            check_ai_packages
        )
        
        print("✓ AI core module imported successfully")
        
        # Test package checking
        package_status = check_ai_packages()
        print(f"Package availability: {package_status['available_count']}/{package_status['total_count']} packages")
        
        for pkg_name, pkg_info in package_status['packages_available'].items():
            status = "✓" if pkg_info['available'] else "✗"
            print(f"  {status} {pkg_name}: {pkg_info['description']}")
        
        # Test health check
        health = ai_health_check()
        print(f"AI Health: {'✓ Healthy' if health['healthy'] else '✗ Unhealthy'}")
        
        return True
        
    except Exception as e:
        print(f"✗ AI core module test failed: {e}")
        return False

def test_advanced_ai_integration():
    """Test the advanced AI integration module"""
    print("\n=== Testing Advanced AI Integration ===")
    try:
        from ai_integration_advanced import (
            initialize_advanced_ai,
            get_advanced_ai_status,
            create_ai_agent,
            execute_ai_task,
            is_advanced_ai_available
        )
        
        print("✓ Advanced AI integration module imported successfully")
        
        # Initialize advanced AI
        print("Initializing advanced AI integration...")
        init_result = initialize_advanced_ai()
        
        print(f"Initialization success: {init_result['success']}")
        print(f"Status: {init_result['status']}")
        print(f"Available features: {init_result['available_features']}")
        
        if init_result['failed_modules']:
            print("Failed modules:")
            for module, error in init_result['failed_modules']:
                print(f"  ✗ {module}: {error}")
        
        # Test status retrieval
        status = get_advanced_ai_status()
        print(f"Features available: {status['feature_details']}")
        
        # Test agent creation if CrewAI is available
        if is_advanced_ai_available() and 'crew_ai' in init_result['available_features']:
            print("\nTesting AI agent creation...")
            agent_result = create_ai_agent(
                name="TestAgent",
                role="AI Assistant",
                goal="Help with testing AI integration",
                backstory="You are a testing assistant created to verify AI functionality."
            )
            
            if agent_result['success']:
                print(f"✓ Created agent: {agent_result['agent_id']}")
                
                # Test task execution
                print("Testing task execution...")
                task_result = execute_ai_task(
                    agent_result['agent_id'],
                    "Say hello and confirm that the AI integration is working correctly."
                )
                
                if task_result['success']:
                    print("✓ Task executed successfully")
                    print(f"Result: {task_result['result'][:200]}...")  # First 200 chars
                else:
                    print(f"✗ Task execution failed: {task_result['error']}")
            else:
                print(f"✗ Agent creation failed: {agent_result['error']}")
        else:
            print("Skipping agent tests - CrewAI not available")
        
        return True
        
    except Exception as e:
        print(f"✗ Advanced AI integration test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_backend_core_interaction():
    """Test interaction with backend core server"""
    print("\n=== Testing Backend Core Server Interaction ===")
    try:
        import requests
        import time
        
        # Test if server is running
        base_url = "http://localhost:7002"
        
        # Test health endpoint
        try:
            health_response = requests.get(f"{base_url}/api/health", timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print("✓ Backend server is responding")
                print(f"  Status: {health_data['status']}")
                print(f"  Mode: {health_data.get('mode', 'unknown')}")
                print(f"  AI packages available: {health_data.get('ai_packages_available', False)}")
            else:
                print(f"✗ Backend health check failed: {health_response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("✗ Backend server is not running on port 7002")
            return False
        
        # Test AI status endpoint
        try:
            ai_status_response = requests.get(f"{base_url}/api/ai/status", timeout=5)
            if ai_status_response.status_code == 200:
                ai_data = ai_status_response.json()
                print("✓ AI status endpoint working")
                print(f"  AI available: {ai_data['ai_status']['ai_available']}")
                print(f"  Features enabled: {list(ai_data['ai_status']['features_enabled'].keys())}")
            else:
                print(f"✗ AI status endpoint failed: {ai_status_response.status_code}")
        except Exception as e:
            print(f"✗ AI status endpoint error: {e}")
        
        # Test fallback AI chat
        try:
            chat_data = {
                "message": "Hello, this is a test message",
                "context": {"test": True}
            }
            chat_response = requests.post(f"{base_url}/api/ai/chat", json=chat_data, timeout=5)
            if chat_response.status_code == 200:
                chat_result = chat_response.json()
                print("✓ AI chat endpoint responding")
                print(f"  Fallback mode: {chat_result.get('fallback', False)}")
            else:
                print(f"✗ AI chat endpoint failed: {chat_response.status_code}")
        except Exception as e:
            print(f"✗ AI chat endpoint error: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Backend interaction test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting Modular AI Integration Tests")
    print("=" * 50)
    
    results = {}
    
    # Test AI core
    results['ai_core'] = test_ai_core()
    
    # Test advanced AI integration
    results['advanced_ai'] = test_advanced_ai_integration()
    
    # Test backend server interaction
    results['backend_interaction'] = test_backend_core_interaction()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Modular AI integration is working.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
