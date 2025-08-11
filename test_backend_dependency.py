#!/usr/bin/env python3
"""
Simple test for backend dependency integration
Tests just the dependency checking functionality without full AI agent import
"""

import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_backend_dependency_functions():
    """Test the dependency functions from backend integration"""
    print("=" * 50)
    print("Backend Dependency Functions Test")
    print("=" * 50)
    
    try:
        # Test importing individual functions without triggering full AI agent imports
        sys.path.insert(0, '.')
        
        # Import backend integration
        from backend_ai_integration import (
            check_ai_dependencies_sync,
            get_ai_dependency_status,
            install_ai_dependencies_sync
        )
        
        print("✓ Successfully imported backend dependency functions")
        
        # Test 1: Direct dependency check
        print("\n1. Testing direct dependency check...")
        dep_check = check_ai_dependencies_sync()
        if dep_check.get('status') != 'error':
            print(f"   - All installed: {dep_check.get('all_installed')}")
            print(f"   - Total packages: {dep_check.get('total_packages')}")
            print(f"   - Installed: {dep_check.get('installed_count')}")
            print(f"   - Missing: {len(dep_check.get('missing_packages', []))}")
        else:
            print(f"   - Error: {dep_check.get('error')}")
        
        # Test 2: Get dependency status through backend
        print("\n2. Testing backend dependency status...")
        backend_status = get_ai_dependency_status()
        print(f"   - Status: {backend_status.get('status')}")
        if backend_status.get('status') == 'complete':
            dep_info = backend_status.get('dependency_check', {})
            print(f"   - Dependencies satisfied: {dep_info.get('all_installed')}")
            print(f"   - Installation command: {backend_status.get('installation_command')}")
        
        # Test 3: Installation command (don't actually install)
        print("\n3. Testing installation function availability...")
        # Note: We don't actually run install to avoid changing the system
        print("   - install_ai_dependencies_sync function is available")
        
        print("\n" + "=" * 50)
        print("Backend dependency test completed successfully!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"✗ Error during backend dependency test: {e}")
        return False


if __name__ == "__main__":
    success = test_backend_dependency_functions()
    
    if success:
        print("\n✓ All backend dependency tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Backend dependency tests failed!")
        sys.exit(1)
