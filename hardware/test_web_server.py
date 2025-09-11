#!/usr/bin/env python3
"""
Test script for the BLE web server endpoints.
"""

import requests
import json
import time

def test_web_server(base_url="http://localhost:5000"):
    """Test all web server endpoints"""
    
    print("🧪 Testing BLE Web Server")
    print("=" * 50)
    print(f"🌐 Server URL: {base_url}")
    print()
    
    # Test 1: Health check
    print("1. 🏥 Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    print()
    
    # Test 2: Status endpoint
    print("2. 📊 Testing status endpoint...")
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            print("✅ Status endpoint working")
            status = response.json()
            print(f"   BLE Connected: {status.get('ble_connected', False)}")
            print(f"   Latest Angles: {status.get('latest_servo_angles', 'None')}")
        else:
            print(f"❌ Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status error: {e}")
    
    print()
    
    # Test 3: Send servo angles
    print("3. 🎯 Testing servo angles endpoint...")
    try:
        test_angles = [90, 90, 90, 100, 90, 90]
        response = requests.post(
            f"{base_url}/send_servo_angles",
            json={"angles": test_angles},
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Servo angles sent successfully")
            result = response.json()
            print(f"   Success: {result.get('success', False)}")
            print(f"   Message: {result.get('message', 'No message')}")
            print(f"   Angles: {result.get('servo_angles', [])}")
        else:
            print(f"❌ Servo angles failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Servo angles error: {e}")
    
    print()
    
    # Test 4: Send finger curls
    print("4. 🤏 Testing finger curls endpoint...")
    try:
        test_curls = "pinky: half curl; ring: no curl; middle: no curl; index: half curl; thumb: half curl"
        response = requests.post(
            f"{base_url}/send_finger_curls",
            json={"curls": test_curls},
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Finger curls sent successfully")
            result = response.json()
            print(f"   Success: {result.get('success', False)}")
            print(f"   Original: {result.get('original_curls', 'None')}")
            print(f"   Servo Angles: {result.get('servo_angles', [])}")
        else:
            print(f"❌ Finger curls failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Finger curls error: {e}")
    
    print()
    
    # Test 5: Send numeric array
    print("5. 🧠 Testing numeric array endpoint...")
    try:
        test_array = [1, 1, 2, 2, 1]  # [pinky, ring, middle, index, thumb]
        response = requests.post(
            f"{base_url}/send_numeric_array",
            json={"array": test_array},
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Numeric array sent successfully")
            result = response.json()
            print(f"   Success: {result.get('success', False)}")
            print(f"   Original: {result.get('original_array', [])}")
            print(f"   Meaning: {result.get('array_meaning', 'None')}")
            print(f"   Servo Angles: {result.get('servo_angles', [])}")
        else:
            print(f"❌ Numeric array failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Numeric array error: {e}")
    
    print()
    print("🎉 Testing completed!")
    print()
    print("💡 Web Interface Available:")
    print(f"   Open browser: {base_url}")
    print()
    print("📋 Example curl commands:")
    print(f"   curl -X POST {base_url}/send_servo_angles -H 'Content-Type: application/json' -d '{{\"angles\": [90,90,90,100,90,90]}}'")
    print(f"   curl -X POST {base_url}/send_finger_curls -H 'Content-Type: application/json' -d '{{\"curls\": \"pinky: half curl; ring: no curl; middle: no curl; index: half curl; thumb: half curl\"}}'")
    print(f"   curl -X GET {base_url}/status")

def wait_for_server(base_url="http://localhost:5000", max_wait=10):
    """Wait for server to start"""
    print(f"⏳ Waiting for server at {base_url}...")
    
    for i in range(max_wait):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ Server ready after {i+1} seconds")
                return True
        except:
            pass
        time.sleep(1)
    
    print(f"❌ Server not ready after {max_wait} seconds")
    return False

if __name__ == "__main__":
    import sys
    
    base_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        port = sys.argv[1]
        base_url = f"http://localhost:{port}"
    
    # Wait for server to start
    if wait_for_server(base_url):
        # Run tests
        test_web_server(base_url)
    else:
        print("❌ Could not connect to server")
        print("💡 Make sure to start the server first:")
        print("   python3 ble_web_server.py")
