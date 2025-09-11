#!/usr/bin/env python3
"""
Script to get finger curl predictions from LLM API and convert to servo angles.
Takes object descriptions and returns finger curl arrays for the robotic hand.
"""

import subprocess
import json
import re
import sys

def make_llm_request(object_identity, object_size, object_position, object_orientation):
    """
    Make a curl request to the LLM API with object description.
    
    Args:
        object_identity: The object name (e.g., "080_keyboard")
        object_size: Size description (e.g., "medium")
        object_position: Position description (e.g., "several feet away, left, bottom relative to the camera")
        object_orientation: Orientation description (e.g., "significantly rotated counterclockwise around the x-axis")
    
    Returns:
        Response text from the API
    """
    
    # Build the prompt
    prompt = f"""Scene: A single everyday object is visible.
Object identity: {object_identity}.
Object size: {object_size}. Object position: {object_position}. Object orientation: {object_orientation}.
Task: Output only the finger curls in this exact format:
pinky: <no curl|half curl|full curl>; ring: <no curl|half curl|full curl>; middle: <no curl|half curl|full curl>; index: <no curl|half curl|full curl>; thumb: <no curl|half curl|full curl>
Do not add any extra words."""

    # Build the curl command
    curl_data = {
        "prompt": prompt,
        "max_new_tokens": 500,
        "temperature": 1.5,
        "top_p": 0.95,
        "top_k": 50,
        "do_sample": True,
        "repetition_penalty": 1.0,
        "stop": ["\n"]
    }
    
    curl_cmd = [
        'curl', '-sS', '-X', 'POST', 
        'https://6kazu8ogvih4cs-8080.proxy.runpod.net/generate',
        '-H', 'Content-Type: application/json',
        '--data-binary', json.dumps(curl_data)
    ]
    
    print("🌐 Making LLM API request...")
    print(f"📝 Object: {object_identity}")
    print(f"📏 Size: {object_size}")
    print(f"📍 Position: {object_position}")
    print(f"🔄 Orientation: {object_orientation}")
    print()
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ LLM API request successful!")
            response = result.stdout.strip()
            print(f"📤 Raw response: {response}")
            return response
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

def parse_finger_curls_to_numeric(response_text):
    """
    Parse LLM response and convert finger curls to numeric array.
    
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
        if response_text and response_text.strip().startswith('{'):
            # Parse JSON response
            response_data = json.loads(response_text)
            if 'response' in response_data:
                text = response_data['response']
            elif 'text' in response_data:
                text = response_data['text']
            else:
                text = response_text
        else:
            text = response_text or ""
        
        print(f"🔍 Parsing finger curls from: {text}")
        
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
                print(f"  {finger}: {curl_state} → {numeric_value}")
            else:
                print(f"  ⚠️ Missing {finger} in response, using half curl (1)")
                numeric_array.append(1)  # Default to half curl
        
        print(f"✅ Final numeric array: {numeric_array}")
        return numeric_array
        
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        print(f"Using default array: {default_array}")
        return default_array

def convert_to_servo_angles(numeric_array):
    """Convert numeric array to servo angles using the existing conversion logic"""
    
    # Mapping from numeric values to curl states
    numeric_to_curl = {
        0: "full curl",    # Closed
        1: "half curl",    # Half way
        2: "no curl"       # Extended
    }
    
    # Convert to curl states
    curl_states = [numeric_to_curl.get(val, "half curl") for val in numeric_array]
    
    # Finger curl mappings (from ble_pose_sender.py)
    CURL_TO_ANGLE = {
        'thumb': {
            'no curl': 0,      # Extended (inverted at hardware level)
            'half curl': 90,   # Half closed
            'full curl': 180   # Fully closed
        },
        'index': {
            'no curl': 180,    # Extended (normal mapping)
            'half curl': 90,   # Half closed
            'full curl': 0     # Fully closed
        },
        'middle': {
            'no curl': 180,    # Extended (normal mapping)
            'half curl': 90,   # Half closed
            'full curl': 0     # Fully closed
        },
        'ring': {
            'no curl': 180,    # Extended (normal mapping, but min is 25°)
            'half curl': 100,  # Half closed
            'full curl': 25    # Fully closed (hardware minimum)
        },
        'pinky': {
            'no curl': 180,    # Extended (normal mapping)
            'half curl': 90,   # Half closed
            'full curl': 0     # Fully closed
        }
    }
    
    # Finger names in the order they appear in the numeric array
    finger_names = ['pinky', 'ring', 'middle', 'index', 'thumb']
    
    finger_angles = {}
    for i, curl in enumerate(curl_states):
        finger = finger_names[i]
        if finger in CURL_TO_ANGLE and curl in CURL_TO_ANGLE[finger]:
            finger_angles[finger] = CURL_TO_ANGLE[finger][curl]
        else:
            finger_angles[finger] = 90  # Default to neutral
    
    # Build servo angles array in correct order: [thumb, index, middle, ring, pinky, wrist]
    servo_angles = [
        finger_angles.get('thumb', 90),
        finger_angles.get('index', 90),
        finger_angles.get('middle', 90),
        finger_angles.get('ring', 90),
        finger_angles.get('pinky', 90),
        90  # wrist
    ]
    
    return servo_angles

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Get finger curl predictions from LLM API")
    parser.add_argument("--object", "-o", default="080_keyboard", help="Object identity (e.g., '080_keyboard')")
    parser.add_argument("--size", "-s", default="medium", help="Object size (e.g., 'medium')")
    parser.add_argument("--position", "-p", default="several feet away, left, bottom relative to the camera", 
                       help="Object position description")
    parser.add_argument("--orientation", "-r", default="significantly rotated counterclockwise around the x-axis",
                       help="Object orientation description")
    parser.add_argument("--send", action="store_true", help="Send result to BLE pose sender")
    
    args = parser.parse_args()
    
    print("🤖 LLM Finger Curl Prediction")
    print("=" * 50)
    
    # Make the LLM request
    response = make_llm_request(args.object, args.size, args.position, args.orientation)
    
    if not response:
        print("❌ Failed to get response from LLM API")
        return
    
    print("\n" + "=" * 50)
    print("🔄 Processing Response")
    print("=" * 50)
    
    # Parse finger curls to numeric array
    numeric_array = parse_finger_curls_to_numeric(response)
    
    # Convert to servo angles
    servo_angles = convert_to_servo_angles(numeric_array)
    
    print("\n" + "=" * 50)
    print("📊 Results")
    print("=" * 50)
    print(f"🧠 LLM Numeric Array: {numeric_array}")
    print(f"   [pinky={numeric_array[0]}, ring={numeric_array[1]}, middle={numeric_array[2]}, index={numeric_array[3]}, thumb={numeric_array[4]}]")
    print()
    print(f"🎯 Servo Angles: {servo_angles}")
    print(f"   [thumb={servo_angles[0]}°, index={servo_angles[1]}°, middle={servo_angles[2]}°, ring={servo_angles[3]}°, pinky={servo_angles[4]}°, wrist={servo_angles[5]}°]")
    
    print("\n" + "=" * 50)
    print("🚀 Usage Commands")
    print("=" * 50)
    print("1. Send numeric array to BLE pose sender:")
    print(f"   python3 ble_pose_sender.py --numeric {' '.join(map(str, numeric_array))}")
    print()
    print("2. Send servo angles directly:")
    print(f"   python3 ble_pose_sender.py --angles {' '.join(map(str, servo_angles))}")
    print()
    print("3. Use in LLM mode:")
    print("   python3 ble_pose_sender.py --llm")
    print(f"   Press 'n' and enter: {','.join(map(str, numeric_array))}")
    print(f"   Or press 's' and enter: {','.join(map(str, servo_angles))}")
    print("   Then press Enter to send!")
    
    if args.send:
        print("\n📤 Sending to BLE pose sender...")
        try:
            send_cmd = ['python3', 'ble_pose_sender.py', '--angles'] + [str(x) for x in servo_angles]
            result = subprocess.run(send_cmd, cwd='/Users/akshayakula/Developer/myogen/hardware')
            if result.returncode == 0:
                print("✅ Successfully sent to BLE pose sender!")
            else:
                print("❌ Failed to send to BLE pose sender")
        except Exception as e:
            print(f"❌ Error sending to BLE pose sender: {e}")

if __name__ == "__main__":
    main()
