#!/usr/bin/env python3
"""
Port Verification Test Script
Tests that the backend servers are now running on port 7002 instead of 8002
"""

import requests
import time
import sys

def test_port_7002():
    """Test that the backend is running on port 7002"""
    print("Testing new port 7002...")
    try:
        response = requests.get("http://localhost:7002/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Port 7002 is working correctly")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Mode: {data.get('mode', 'unknown')}")
            return True
        else:
            print(f"❌ Port 7002 responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No server responding on port 7002")
        return False
    except Exception as e:
        print(f"❌ Error testing port 7002: {e}")
        return False

def test_port_8002():
    """Test that nothing is running on port 8002 (old port)"""
    print("Testing old port 8002 (should not be in use)...")
    try:
        response = requests.get("http://localhost:8002/api/health", timeout=3)
        print("⚠️  WARNING: Something is still running on old port 8002!")
        print("   This may indicate the old server is still running.")
        return False
    except requests.exceptions.ConnectionError:
        print("✅ Port 8002 is not in use (correct)")
        return True
    except Exception as e:
        print(f"⚠️  Unexpected error testing port 8002: {e}")
        return True  # Assume it's not running

def test_api_endpoints():
    """Test key API endpoints on the new port"""
    print("Testing API endpoints on port 7002...")
    
    endpoints_to_test = [
        ("/api/providers", "Providers endpoint"),
        ("/api/settings", "Settings endpoint"),
        ("/api/usage", "Usage endpoint"),
        ("/api/ai/status", "AI status endpoint")
    ]
    
    success_count = 0
    for endpoint, description in endpoints_to_test:
        try:
            response = requests.get(f"http://localhost:7002{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {description}: OK")
                success_count += 1
            else:
                print(f"   ❌ {description}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {description}: Error - {e}")
    
    print(f"API Endpoints: {success_count}/{len(endpoints_to_test)} working")
    return success_count == len(endpoints_to_test)

def main():
    """Run all port verification tests"""
    print("🧪 Port Migration Verification Test")
    print("=" * 50)
    
    # Test new port
    new_port_working = test_port_7002()
    print()
    
    # Test old port is not in use
    old_port_clear = test_port_8002()
    print()
    
    # Test API endpoints if new port is working
    api_working = False
    if new_port_working:
        api_working = test_api_endpoints()
        print()
    
    # Summary
    print("=" * 50)
    print("📊 Test Summary:")
    print(f"   New Port (7002): {'✅ Working' if new_port_working else '❌ Failed'}")
    print(f"   Old Port (8002): {'✅ Clear' if old_port_clear else '❌ Still in use'}")
    if new_port_working:
        print(f"   API Endpoints: {'✅ Working' if api_working else '❌ Some failed'}")
    
    if new_port_working and old_port_clear:
        print("\n🎉 Port migration successful!")
        print("The backend is now running on port 7002 as intended.")
        return 0
    else:
        print("\n⚠️  Port migration issues detected:")
        if not new_port_working:
            print("   - Backend is not responding on new port 7002")
            print("   - Make sure to start the server with the updated code")
        if not old_port_clear:
            print("   - Old port 8002 is still in use")
            print("   - Stop any processes running on port 8002")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
