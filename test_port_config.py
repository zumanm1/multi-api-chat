#!/usr/bin/env python3
"""
Comprehensive Port Configuration Test for Multi-API Chat
========================================================

This test verifies that all ports have been properly updated from 8001/8002 to 7001/7002
and that no hardcoded port references remain in the codebase.
"""

import os
import re
import requests
import subprocess
import time
from pathlib import Path


def test_backend_port_7002():
    """Test that backend is running on port 7002"""
    print("🔍 Testing backend on port 7002...")
    try:
        response = requests.get("http://localhost:7002/api/health", timeout=3)
        if response.status_code == 200:
            print("✅ Backend is running correctly on port 7002")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Backend is not responding on port 7002")
        return False


def test_frontend_port_7001():
    """Test that frontend is running on port 7001"""
    print("🔍 Testing frontend on port 7001...")
    try:
        response = requests.get("http://localhost:7001", timeout=3)
        if response.status_code == 200:
            print("✅ Frontend is running correctly on port 7001")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Frontend is not responding on port 7001")
        return False


def test_old_ports_not_in_use():
    """Test that old ports 8001 and 8002 are not in use"""
    print("🔍 Testing that old ports 8001/8002 are not in use...")
    old_ports_clear = True
    
    # Test port 8001
    try:
        response = requests.get("http://localhost:8001", timeout=3)
        print("⚠️  WARNING: Something is still running on old port 8001!")
        old_ports_clear = False
    except requests.exceptions.RequestException:
        print("✅ Port 8001 is not in use (correct)")
    
    # Test port 8002
    try:
        response = requests.get("http://localhost:8002/api/health", timeout=3)
        print("⚠️  WARNING: Something is still running on old port 8002!")
        old_ports_clear = False
    except requests.exceptions.RequestException:
        print("✅ Port 8002 is not in use (correct)")
    
    return old_ports_clear


def scan_for_hardcoded_ports():
    """Scan for hardcoded port references in code files"""
    print("🔍 Scanning for hardcoded port references...")
    
    # Files to exclude from scanning
    exclude_patterns = [
        '__pycache__',
        '.venv',
        'venv',
        'node_modules',
        '.git',
        'logs',
        'test_reports',
        'test_port_config.py',  # Exclude this test file itself
        'port_verification_test.py'  # Exclude the port verification test
    ]
    
    # File extensions to scan
    extensions = ['.py', '.js', '.html', '.md', '.sh', '.json']
    
    found_issues = []
    project_root = Path('.')
    
    for file_path in project_root.rglob('*'):
        # Skip excluded directories and files
        if any(exclude in str(file_path) for exclude in exclude_patterns):
            continue
        
        # Only scan relevant file types
        if not any(str(file_path).endswith(ext) for ext in extensions):
            continue
            
        if file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Look for port references (but exclude this test and port verification test)
                port_8001_matches = re.finditer(r'8001', content)
                port_8002_matches = re.finditer(r'8002', content)
                
                for match in port_8001_matches:
                    line_num = content[:match.start()].count('\n') + 1
                    found_issues.append(f"Port 8001 found in {file_path}:{line_num}")
                
                for match in port_8002_matches:
                    line_num = content[:match.start()].count('\n') + 1
                    found_issues.append(f"Port 8002 found in {file_path}:{line_num}")
                    
            except Exception as e:
                print(f"Warning: Could not scan {file_path}: {e}")
    
    if found_issues:
        print("❌ Found hardcoded port references:")
        for issue in found_issues:
            print(f"  • {issue}")
        return False
    else:
        print("✅ No hardcoded port references found in scanned files")
        return True


def test_start_script_configuration():
    """Test that start_app.sh uses correct ports"""
    print("🔍 Checking start_app.sh configuration...")
    
    try:
        with open('start_app.sh', 'r') as f:
            content = f.read()
        
        issues = []
        
        # Check for port 7001 and 7002 usage
        if 'kill_port_processes 7002' not in content:
            issues.append("start_app.sh should clean port 7002")
        
        if 'kill_port_processes 7001' not in content:
            issues.append("start_app.sh should clean port 7001")
        
        if 'port 7002' not in content:
            issues.append("start_app.sh should reference port 7002 for backend")
            
        if 'port 7001' not in content:
            issues.append("start_app.sh should reference port 7001 for frontend")
        
        # Check for old port references
        if '8001' in content or '8002' in content:
            issues.append("start_app.sh still contains old port references (8001/8002)")
        
        if issues:
            print("❌ Start script issues found:")
            for issue in issues:
                print(f"  • {issue}")
            return False
        else:
            print("✅ start_app.sh correctly configured for new ports")
            return True
            
    except FileNotFoundError:
        print("❌ start_app.sh not found")
        return False


def run_port_config_tests():
    """Run all port configuration tests"""
    print("=" * 60)
    print("Multi-API Chat Port Configuration Test")
    print("=" * 60)
    print()
    
    test_results = []
    
    # Test 1: Backend on port 7002
    test_results.append(("Backend Port 7002", test_backend_port_7002()))
    
    # Test 2: Frontend on port 7001  
    test_results.append(("Frontend Port 7001", test_frontend_port_7001()))
    
    # Test 3: Old ports not in use
    test_results.append(("Old Ports Clear", test_old_ports_not_in_use()))
    
    # Test 4: No hardcoded port references
    test_results.append(("No Hardcoded Ports", scan_for_hardcoded_ports()))
    
    # Test 5: Start script configuration
    test_results.append(("Start Script Config", test_start_script_configuration()))
    
    print()
    print("=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print()
    print(f"Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All port configuration tests passed!")
        print("   The application is correctly configured for ports 7001/7002")
        return True
    else:
        print("⚠️  Some port configuration issues found")
        print("   Please review and fix the issues above")
        return False


if __name__ == "__main__":
    success = run_port_config_tests()
    exit(0 if success else 1)
