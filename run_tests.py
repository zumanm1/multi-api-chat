#!/usr/bin/env python3
"""
Simple Test Runner for Multi-API Chat Application
================================================
Run backend pytest tests and display results immediately.
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path

def run_backend_tests():
    """Run backend tests with pytest"""
    print("🚀 Starting backend tests...")
    print("-" * 60)
    
    # Ensure virtual environment is activated
    venv_path = Path(".venv/bin/activate")
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_comprehensive_backend.py",
        "-v",
        "--tb=short",
        "--maxfail=5",
        "--durations=10",
        "--cov=backend_server",
        "--cov-report=term-missing",
        "--junit-xml=test-reports/backend/junit.xml"
    ]
    
    # Run the tests
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    end_time = time.time()
    
    print("-" * 60)
    print(f"⏱️  Total test time: {end_time - start_time:.2f} seconds")
    
    if result.returncode == 0:
        print("✅ All backend tests passed!")
    else:
        print("❌ Some backend tests failed.")
    
    # Generate simple report
    try:
        from generate_test_report import parse_pytest_junit_xml
        
        junit_file = "test-reports/backend/junit.xml"
        if os.path.exists(junit_file):
            results = parse_pytest_junit_xml(junit_file)
            
            if not results.get('error'):
                print("\n📊 TEST SUMMARY:")
                print(f"   Total Tests: {results['total']}")
                print(f"   Passed: {results['passed']} ✅")
                print(f"   Failed: {results['failed']} ❌")
                print(f"   Errors: {results['errors']} 💥")
                print(f"   Skipped: {results['skipped']} ⏭️")
                print(f"   Success Rate: {(results['passed']/results['total']*100):.1f}%")
                
                # Show failed tests
                if results['failed'] > 0 or results['errors'] > 0:
                    print("\n❌ FAILED TESTS:")
                    for test in results['test_cases']:
                        if test['status'] in ['failed', 'error']:
                            print(f"   - {test['name']} ({test['status']})")
                            if test.get('message'):
                                print(f"     {test['message']}")
    except ImportError:
        pass
    
    return result.returncode

def main():
    """Main function"""
    print("🧪 Multi-API Chat Test Runner")
    print("=" * 60)
    
    # Create test reports directory
    os.makedirs("test-reports/backend", exist_ok=True)
    
    # Run backend tests
    exit_code = run_backend_tests()
    
    print("\n🎯 NEXT STEPS:")
    if exit_code == 0:
        print("   - All tests passed! ✨")
        print("   - Coverage report: test-reports/backend/coverage/index.html")
    else:
        print("   - Fix failing tests and run again")
        print("   - Check detailed JUnit XML: test-reports/backend/junit.xml")
    
    print("   - Generate full report: python3 generate_test_report.py")
    print("=" * 60)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
