#!/usr/bin/env python3
"""
Test script for AI Dependency Checker
Tests the functionality of the dependency checker utility
"""

import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_dependency_checker():
    """Test the dependency checker functionality"""
    print("=" * 50)
    print("AI Dependency Checker Test")
    print("=" * 50)
    
    try:
        # Import the dependency checker
        from ai_agents.utils.dependency_checker import (
            check_ai_dependencies,
            get_missing_dependencies,
            log_dependency_status,
            validate_ai_environment,
            get_installation_command
        )
        
        print("✓ Successfully imported dependency checker")
        
        # Test 1: Check AI dependencies
        print("\n1. Checking AI dependencies...")
        dep_status = check_ai_dependencies()
        print(f"   - Total packages: {dep_status['total_packages']}")
        print(f"   - Installed: {dep_status['installed_count']}")
        print(f"   - All installed: {dep_status['all_installed']}")
        print(f"   - Missing: {len(dep_status['missing_packages'])}")
        print(f"   - Version issues: {len(dep_status['outdated_packages'])}")
        
        # Test 2: Get missing dependencies
        print("\n2. Getting missing dependencies...")
        missing = get_missing_dependencies()
        if missing:
            print(f"   - Found {len(missing)} missing packages:")
            for pkg in missing[:3]:  # Show first 3
                print(f"     * {pkg['package']}: {pkg['description']}")
            if len(missing) > 3:
                print(f"     ... and {len(missing) - 3} more")
        else:
            print("   - No missing packages found")
        
        # Test 3: Validate environment
        print("\n3. Validating AI environment...")
        env_status = validate_ai_environment()
        print(f"   - Environment ready: {env_status['environment_ready']}")
        print(f"   - Python version: {env_status['python_version']}")
        print(f"   - Requirements file exists: {env_status['requirements_file_exists']}")
        
        if env_status['recommendations']:
            print("   - Recommendations:")
            for rec in env_status['recommendations'][:3]:
                print(f"     * {rec}")
            if len(env_status['recommendations']) > 3:
                print(f"     ... and {len(env_status['recommendations']) - 3} more")
        
        # Test 4: Get installation command
        print("\n4. Installation command:")
        install_cmd = get_installation_command()
        print(f"   - {install_cmd}")
        
        # Test 5: Log dependency status
        print("\n5. Logging detailed dependency status:")
        log_dependency_status(logging.INFO)
        
        print("\n" + "=" * 50)
        print("Dependency checker test completed successfully!")
        print("=" * 50)
        
        # Return status for integration testing
        return {
            "success": True,
            "dependency_status": dep_status,
            "environment_status": env_status,
            "missing_count": len(missing)
        }
        
    except ImportError as e:
        print(f"✗ Failed to import dependency checker: {e}")
        print("Make sure the ai_agents.utils.dependency_checker module exists")
        return {"success": False, "error": "Import failed"}
    
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return {"success": False, "error": str(e)}


def test_backend_integration():
    """Test the backend integration with dependency checking"""
    print("\n" + "=" * 50)
    print("Backend AI Integration Dependency Test")
    print("=" * 50)
    
    try:
        from backend_ai_integration import (
            get_ai_dependency_status,
            check_ai_dependencies_sync,
            install_ai_dependencies_sync
        )
        
        print("✓ Successfully imported backend integration functions")
        
        # Test dependency status through backend
        print("\n1. Getting dependency status through backend integration...")
        backend_dep_status = get_ai_dependency_status()
        print(f"   - Status: {backend_dep_status.get('status', 'unknown')}")
        
        # Test direct dependency check
        print("\n2. Direct dependency check...")
        direct_check = check_ai_dependencies_sync()
        if direct_check.get('status') != 'error':
            print(f"   - All installed: {direct_check.get('all_installed', 'unknown')}")
        else:
            print(f"   - Error: {direct_check.get('error')}")
        
        print("\n3. Backend integration dependency test completed!")
        
        return {"success": True}
        
    except ImportError as e:
        print(f"✗ Failed to import backend integration: {e}")
        return {"success": False, "error": "Backend import failed"}
    
    except Exception as e:
        print(f"✗ Error during backend testing: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test the dependency checker
    result1 = test_dependency_checker()
    
    # Test the backend integration
    result2 = test_backend_integration()
    
    # Summary
    print(f"\n{'=' * 50}")
    print("TEST SUMMARY")
    print(f"{'=' * 50}")
    print(f"Dependency Checker: {'✓ PASS' if result1['success'] else '✗ FAIL'}")
    print(f"Backend Integration: {'✓ PASS' if result2['success'] else '✗ FAIL'}")
    
    if result1['success']:
        missing_count = result1.get('missing_count', 0)
        if missing_count > 0:
            print(f"\nNOTE: {missing_count} AI dependencies are missing.")
            print("Run 'pip install -r requirements-ai-agents.txt' to install them.")
        else:
            print(f"\n✓ All AI dependencies are satisfied!")
    
    # Exit with appropriate code
    sys.exit(0 if (result1['success'] and result2['success']) else 1)
