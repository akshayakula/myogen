#!/usr/bin/env python3
"""
Test script for LLM integration with BLE pose sender.
Demonstrates how to convert LLM curl predictions to numeric arrays.
"""

import re
import subprocess
import json
import sys

def parse_llm_curl_response(curl_response: str) -> list:
    """
    Parse LLM curl response and convert to numeric array.
    
    Expected format from LLM:
    "pinky: <no curl|half curl|full curl>; ring: <no curl|half curl|full curl>; middle: <no curl|half curl|full curl>; index: <no curl|half curl|full curl>; thumb: <no curl|half curl|full curl>"
    
    Returns: [pinky, ring, middle, index, thumb] numeric array where 0=closed, 1=half, 2=extended
    """
    # Mapping from curl states to numeric values
    curl_to_numeric = {
        'full curl': 0,    # Closed
        'half curl': 1,    # Half way
        'no curl': 2       # Extended
    }
    
    # Default values (neutral position)
    default_array = [1, 1, 1, 1, 1]  # All half curl
    
    try:
        # Extract the response text from JSON if needed
        if curl_response.strip().startswith('{'):
            # Parse JSON response
            response_data = json.loads(curl_response)
            if 'response' in response_data:
                text = response_data['response']
            elif 'text' in response_data:
                text = response_data['text']
            else:
                text = curl_response
        else:
            text = curl_response
        
        print(f"🔍 Parsing LLM response: {text}")
        
        # Look for the finger curl pattern
        finger_pattern = r'(pinky|ring|middle|index|thumb):\s*(no curl|half curl|full curl)'
        matches = re.findall(finger_pattern, text.lower())
        
        if not matches:
            print("⚠️ No finger curl pattern found in response, using default")
            return default_array
        
        # Build finger curl mapping
        finger_curls = {}
        for finger, curl in matches:
            finger_curls[finger] = curl
        
        # Convert to numeric array in order: [pinky, ring, middle, index, thumb]
        finger_order = ['pinky', 'ring', 'middle', 'index', 'thumb']
        numeric_array = []
        
        for finger in finger_order:
            if finger in finger_curls:
                curl_state = finger_curls[finger]
                numeric_value = curl_to_numeric.get(curl_state, 1)  # Default to half curl
                numeric_array.append(numeric_value)
            else:
                print(f"⚠️ Missing {finger} in response, using half curl")
                numeric_array.append(1)  # Default to half curl
        
        print(f"✅ Converted to numeric array: {numeric_array}")
        print(f"📋 Mapping: pinky={numeric_array[0]}, ring={numeric_array[1]}, middle={numeric_array[2]}, index={numeric_array[3]}, thumb={numeric_array[4]}")
        return numeric_array
        
    except Exception as e:
        print(f"❌ Error parsing LLM response: {e}")
        print(f"Using default array: {default_array}")
        return default_array

def test_curl_command():
    """Test the curl command and parse the response"""
    curl_cmd = [
        'curl', '-sS', '-X', 'POST', 
        'https://6kazu8ogvih4cs-8080.proxy.runpod.net/generate',
        '-H', 'Content-Type: application/json',
        '--data-binary', json.dumps({
            "prompt": "Scene: A single everyday object is visible.\nObject identity: 010_potted_meat_can.\nObject size: small. Object position: arm's-length, centered, below relative to the camera. Object orientation: strongly rotated around the x-axis.\nTask: Output only the finger curls in this exact format:\npinky: <no curl|half curl|full curl>; ring: <no curl|half curl|full curl>; middle: <no curl|half curl|full curl>; index: <no curl|half curl|full curl>; thumb: <no curl|half curl|full curl>\nDo not add any extra words.",
            "max_new_tokens": 500,
            "temperature": 1.5,
            "top_p": 0.95,
            "top_k": 50,
            "do_sample": True,
            "repetition_penalty": 1.0,
            "stop": ["\n"]
        })
    ]
    
    try:
        print("🌐 Making curl request to LLM API...")
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Curl request successful!")
            response = result.stdout.strip()
            print(f"📤 Raw response: {response}")
            
            # Parse the response
            numeric_array = parse_llm_curl_response(response)
            
            # Show how to use with BLE pose sender
            print("\n" + "="*60)
            print("🤖 BLE POSE SENDER INTEGRATION")
            print("="*60)
            print("To use this numeric array with the BLE pose sender:")
            print()
            print("1. Command line (one-time):")
            print(f"   python3 ble_pose_sender.py --numeric {' '.join(map(str, numeric_array))}")
            print()
            print("2. LLM mode (interactive):")
            print("   python3 ble_pose_sender.py --llm")
            print(f"   Then enter: {','.join(map(str, numeric_array))}")
            print("   Press Enter to send to hand")
            print()
            print("3. Programmatic integration:")
            print("   # Store the array globally")
            print(f"   latest_llm_array = {numeric_array}")
            print("   # Then press Enter in LLM mode to send")
            
            return numeric_array
            
        else:
            print(f"❌ Curl request failed with return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Curl request timed out after 30 seconds")
        return None
    except Exception as e:
        print(f"❌ Error running curl command: {e}")
        return None

def test_parsing_examples():
    """Test parsing with various example responses"""
    test_cases = [
        {
            'name': 'Perfect format',
            'response': 'pinky: no curl; ring: no curl; middle: no curl; index: no curl; thumb: no curl'
        },
        {
            'name': 'JSON wrapped',
            'response': '{"response": "pinky: full curl; ring: full curl; middle: full curl; index: no curl; thumb: no curl"}'
        },
        {
            'name': 'Mixed curls',
            'response': 'pinky: half curl; ring: full curl; middle: no curl; index: half curl; thumb: full curl'
        },
        {
            'name': 'Extra text (should still work)',
            'response': 'The hand position would be: pinky: no curl; ring: half curl; middle: full curl; index: no curl; thumb: half curl for this object.'
        },
        {
            'name': 'Invalid format (should use defaults)',
            'response': 'I cannot determine the finger positions from this description.'
        }
    ]
    
    print("🧪 Testing LLM response parsing:")
    print("="*60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}:")
        print(f"   Input: {test['response']}")
        numeric_array = parse_llm_curl_response(test['response'])
        print(f"   Result: {numeric_array}")
        print(f"   Meaning: pinky={numeric_array[0]}, ring={numeric_array[1]}, middle={numeric_array[2]}, index={numeric_array[3]}, thumb={numeric_array[4]}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LLM integration with BLE pose sender")
    parser.add_argument("--curl", action="store_true", help="Test actual curl command")
    parser.add_argument("--parse", action="store_true", help="Test parsing examples")
    parser.add_argument("--response", "-r", help="Test parsing a specific response string")
    
    args = parser.parse_args()
    
    if args.curl:
        test_curl_command()
    elif args.parse:
        test_parsing_examples()
    elif args.response:
        numeric_array = parse_llm_curl_response(args.response)
        print(f"Result: {numeric_array}")
    else:
        print("🚀 LLM Integration Test Suite")
        print("="*40)
        print("Choose an option:")
        print("  --curl   : Test actual curl command")
        print("  --parse  : Test parsing examples")
        print("  --response 'text' : Test specific response")
        print()
        
        choice = input("Run curl test? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            test_curl_command()
        else:
            test_parsing_examples()

if __name__ == "__main__":
    main()
