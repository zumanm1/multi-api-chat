#!/usr/bin/env python3
"""
AI Agent Tests Runner
====================

Simple script to run the AI agent tests and demonstrate functionality
both with and without AI dependencies installed.
"""

import os
import sys
import subprocess
import importlib.util

def check_package_installed(package_name):
    """Check if a package is installed"""
    try:
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    except ImportError:
        return False

def install_pytest_if_needed():
    """Install pytest if not available"""
    if not check_package_installed('pytest'):
        print("Installing pytest...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pytest'], check=True)
            print("pytest installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install pytest")
            return False
    else:
        print("pytest is already installed")
        return True

def run_tests(test_file="tests/test_ai_agents.py", verbose=True):
    """Run the AI agent tests"""
    if not install_pytest_if_needed():
        return False
    
    cmd = [sys.executable, '-m', 'pytest', test_file]
    
    if verbose:
        cmd.extend(['-v', '--tb=short'])
    
    # Add markers to show both success and skip scenarios
    cmd.extend(['-r', 'a'])  # Show all test results
    
    print(f"Running tests: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def check_ai_dependencies():
    """Check AI dependency status"""
    print("Checking AI Dependencies:")
    print("-" * 30)
    
    dependencies = [
        'pytest',
        'crewai', 
        'langchain',
        'langchain_openai',
        'langgraph',
        'chromadb'
    ]
    
    installed = []
    missing = []
    
    for dep in dependencies:
        if check_package_installed(dep):
            installed.append(dep)
            print(f"✓ {dep}")
        else:
            missing.append(dep)
            print(f"✗ {dep}")
    
    print(f"\nInstalled: {len(installed)}/{len(dependencies)}")
    print(f"Missing: {missing}")
    
    return len(missing) == 0

def main():
    """Main test runner"""
    print("AI Agent Integration Test Runner")
    print("=" * 40)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print(f"Working directory: {os.getcwd()}")
    
    # Check dependencies
    all_deps_installed = check_ai_dependencies()
    print()
    
    # Run tests
    if all_deps_installed:
        print("🚀 Running tests with full AI dependencies...")
    else:
        print("⚠️  Running tests in fallback mode (some AI dependencies missing)...")
        print("   The tests are designed to work both ways!")
    
    print()
    
    success = run_tests()
    
    print()
    print("=" * 60)
    
    if success:
        print("✅ Tests completed successfully!")
        if not all_deps_installed:
            print("   Tests passed in fallback mode - this demonstrates")
            print("   that the system gracefully handles missing dependencies.")
    else:
        print("❌ Some tests failed or encountered errors")
        print("   This is expected if you're missing dependencies.")
        print("   To install AI dependencies, run:")
        print("   pip install crewai langchain langchain-openai langgraph chromadb")
    
    # Show test categories that were run
    print("\nTest Categories Covered:")
    print("- Core AI Integration")
    print("- CrewAI Available/Not Available scenarios") 
    print("- Individual Agent Types (chat, analytics, device, operations, automation)")
    print("- Cross-page request handling")
    print("- LangGraph workflow execution")
    print("- Fallback behavior")
    print("- Performance and stress tests")
    print("- Realistic usage scenarios")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
