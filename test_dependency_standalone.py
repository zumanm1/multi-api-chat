#!/usr/bin/env python3
"""
Standalone test for dependency checker
Tests the dependency checker without importing the full ai_agents package
"""

import sys
import os
import importlib.util

def test_dependency_checker_standalone():
    """Test dependency checker by importing it directly"""
    print("=" * 60)
    print("Standalone AI Dependency Checker Test")
    print("=" * 60)
    
    # Load the dependency checker module directly
    spec = importlib.util.spec_from_file_location(
        "dependency_checker", 
        "ai_agents/utils/dependency_checker.py"
    )
    dependency_checker = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(dependency_checker)
        print("✓ Successfully loaded dependency checker module")
    except Exception as e:
        print(f"✗ Failed to load dependency checker: {e}")
        return False
    
    try:
        # Test 1: Basic dependency check
        print("\n1. Testing basic dependency check...")
        status = dependency_checker.check_ai_dependencies()
        print(f"   - All installed: {status['all_installed']}")
        print(f"   - Total packages: {status['total_packages']}")
        print(f"   - Installed: {status['installed_count']}")
        print(f"   - Missing: {len(status['missing_packages'])}")
        print(f"   - Version issues: {len(status['outdated_packages'])}")
        
        # Test 2: Get missing dependencies
        print("\n2. Testing missing dependencies list...")
        missing = dependency_checker.get_missing_dependencies()
        if missing:
            print(f"   - Found {len(missing)} missing packages:")
            for i, pkg in enumerate(missing[:3]):  # Show first 3
                print(f"     {i+1}. {pkg['package']}: {pkg['description']}")
            if len(missing) > 3:
                print(f"     ... and {len(missing) - 3} more")
        else:
            print("   - No missing packages")
        
        # Test 3: Environment validation
        print("\n3. Testing environment validation...")
        env_status = dependency_checker.validate_ai_environment()
        print(f"   - Environment ready: {env_status['environment_ready']}")
        print(f"   - Python version: {env_status['python_version']}")
        print(f"   - Requirements file exists: {env_status['requirements_file_exists']}")
        print(f"   - Recommendations: {len(env_status['recommendations'])}")
        
        if env_status['recommendations']:
            for i, rec in enumerate(env_status['recommendations'][:3]):
                print(f"     {i+1}. {rec}")
        
        # Test 4: Installation command
        print("\n4. Testing installation command...")
        install_cmd = dependency_checker.get_installation_command()
        print(f"   - Command: {install_cmd}")
        
        # Test 5: Log status (at WARNING level to reduce output)
        print("\n5. Testing logging functionality...")
        import logging
        logging.basicConfig(level=logging.WARNING)
        dependency_checker.log_dependency_status(logging.WARNING)
        
        print("\n" + "=" * 60)
        print("✓ All dependency checker tests passed!")
        print("=" * 60)
        
        # Summary
        if not status['all_installed']:
            missing_count = len(status['missing_packages'])
            print(f"\nSUMMARY: {missing_count} AI dependencies are missing.")
            print("To install them, run:")
            print(f"  {install_cmd}")
        else:
            print("\nSUMMARY: All AI dependencies are satisfied!")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during dependency checker test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_requirements_file():
    """Test that the requirements file exists and is readable"""
    print("\n" + "=" * 60)
    print("Requirements File Test")
    print("=" * 60)
    
    req_file = "requirements-ai-agents.txt"
    
    if os.path.exists(req_file):
        print(f"✓ {req_file} exists")
        try:
            with open(req_file, 'r') as f:
                lines = f.readlines()
            print(f"   - Contains {len(lines)} lines")
            
            # Show first few packages
            packages = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
            print(f"   - Defines {len(packages)} packages:")
            for i, pkg in enumerate(packages[:5]):
                print(f"     {i+1}. {pkg}")
            if len(packages) > 5:
                print(f"     ... and {len(packages) - 5} more")
        except Exception as e:
            print(f"✗ Error reading {req_file}: {e}")
            return False
    else:
        print(f"✗ {req_file} does not exist")
        return False
    
    return True


if __name__ == "__main__":
    print("Starting standalone dependency checker tests...\n")
    
    # Test 1: Requirements file
    req_test = test_requirements_file()
    
    # Test 2: Dependency checker
    dep_test = test_dependency_checker_standalone()
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"Requirements file: {'✓ PASS' if req_test else '✗ FAIL'}")
    print(f"Dependency checker: {'✓ PASS' if dep_test else '✗ FAIL'}")
    
    if req_test and dep_test:
        print("\n🎉 All tests completed successfully!")
        print("The dependency checking system is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
