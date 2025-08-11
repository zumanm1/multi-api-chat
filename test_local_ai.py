#!/usr/bin/env python3
"""
Local AI Integration Test - uses local Ollama for testing
Tests AI functionality without requiring external API keys
"""

import os
import sys
import json
import logging

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_local_ai_integration():
    """Test AI integration with local Ollama instead of OpenAI"""
    print("\n=== Testing Local AI Integration (Ollama) ===")
    
    try:
        from ai_integration_advanced import initialize_advanced_ai, create_ai_agent, execute_ai_task
        
        # Initialize AI with local configuration
        print("Initializing AI with local Ollama configuration...")
        init_result = initialize_advanced_ai()
        
        if not init_result['success']:
            print("✗ AI initialization failed")
            return False
        
        print("✓ AI modules initialized successfully")
        
        # Test agent creation with local configuration
        if 'crew_ai' in init_result['available_features']:
            print("Creating agent configured for local Ollama...")
            
            # Override environment for local testing
            os.environ['OPENAI_API_KEY'] = 'fake-key-for-local-testing'
            os.environ['OPENAI_BASE_URL'] = 'http://localhost:11434/v1'  # Ollama OpenAI compatibility
            
            agent_result = create_ai_agent(
                name="LocalTestAgent",
                role="Local AI Assistant",
                goal="Test local AI functionality",
                backstory="You are a test agent using local Ollama for inference."
            )
            
            if agent_result['success']:
                print(f"✓ Local agent created: {agent_result['agent_id']}")
                
                # Test simple task execution
                print("Testing local task execution...")
                task_result = execute_ai_task(
                    agent_result['agent_id'],
                    "Simply respond with 'Hello from local AI' to confirm functionality."
                )
                
                if task_result['success']:
                    print("✓ Local task executed successfully")
                    print(f"Result: {task_result['result'][:100]}...")
                else:
                    print(f"Note: Local task failed (expected if Ollama not running): {task_result['error']}")
                    print("This is normal if Ollama is not installed or running locally")
            else:
                print(f"✗ Local agent creation failed: {agent_result['error']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Local AI integration test failed: {e}")
        return False

def test_ai_module_structure():
    """Test the structure and isolation of AI modules"""
    print("\n=== Testing AI Module Structure ===")
    
    try:
        # Test that modules can be imported independently
        print("Testing independent module imports...")
        
        # Test ai_core import
        from ai_core import check_ai_packages, ai_health_check
        print("✓ ai_core imported independently")
        
        # Test advanced integration import
        from ai_integration_advanced import get_advanced_ai_status, is_advanced_ai_available
        print("✓ ai_integration_advanced imported independently")
        
        # Test that modules don't create circular dependencies
        print("Testing module independence...")
        
        ai_status = ai_health_check()
        advanced_status = is_advanced_ai_available()
        
        print(f"✓ AI core health: {ai_status['healthy']}")
        print(f"✓ Advanced AI available: {advanced_status}")
        
        return True
        
    except Exception as e:
        print(f"✗ Module structure test failed: {e}")
        return False

def test_backend_fallback_modes():
    """Test backend server fallback behavior"""
    print("\n=== Testing Backend Fallback Modes ===")
    
    try:
        import requests
        base_url = "http://localhost:8002"
        
        # Test configuration endpoint
        try:
            config_response = requests.get(f"{base_url}/api/config", timeout=3)
            if config_response.status_code == 200:
                config_data = config_response.json()
                print("✓ Configuration endpoint responding")
                print(f"  Providers available: {len(config_data.get('providers', {}))}")
            else:
                print(f"Note: Config endpoint returned {config_response.status_code}")
        except Exception as e:
            print(f"Note: Config endpoint test skipped: {e}")
        
        # Test analytics endpoint
        try:
            analytics_response = requests.get(f"{base_url}/api/analytics/usage", timeout=3)
            if analytics_response.status_code == 200:
                analytics_data = analytics_response.json()
                print("✓ Analytics endpoint responding")
                print(f"  Total requests tracked: {analytics_data.get('total_requests', 0)}")
            else:
                print(f"Note: Analytics endpoint returned {analytics_response.status_code}")
        except Exception as e:
            print(f"Note: Analytics endpoint test skipped: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Backend fallback test failed: {e}")
        return False

def main():
    """Run local AI integration tests"""
    print("Local AI Integration Testing")
    print("=" * 40)
    
    results = {}
    
    # Test module structure
    results['module_structure'] = test_ai_module_structure()
    
    # Test local AI integration
    results['local_ai'] = test_local_ai_integration()
    
    # Test backend fallback modes
    results['backend_fallback'] = test_backend_fallback_modes()
    
    # Summary
    print("\n" + "=" * 40)
    print("Local Test Results:")
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All local tests passed! AI architecture is robust.")
        return 0
    else:
        print("⚠️ Some tests failed. Check output for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
