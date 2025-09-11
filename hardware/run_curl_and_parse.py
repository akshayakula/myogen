#!/usr/bin/env python3
"""
Direct curl command runner that executes the exact curl command and parses the response.
"""

import subprocess
import json
import re
import sys

def run_curl_command_for_object(object_identity, object_size, object_position, object_orientation):
    """
    Run the exact curl command format you provided with the object description.
    """
    
    # Build the prompt exactly as specified
    prompt = f"""Scene: A single everyday object is visible.
Object identity: {object_identity}.
Object size: {object_size}. Object position: {object_position}. Object orientation: {object_orientation}.
Task: Output only the finger curls in this exact format:
pinky: <no curl|half curl|full curl>; ring: <no curl|half curl|full curl>; middle: <no curl|half curl|full curl>; index: <no curl|half curl|full curl>; thumb: <no curl|half curl|full curl>
Do not add any extra words."""

    # Create the JSON data
    json_data = {
        "prompt": prompt,
        "max_new_tokens": 500,
        "temperature": 1.5,
        "top_p": 0.95,
        "top_k": 50,
        "do_sample": True,
        "repetition_penalty": 1.0,
        "stop": ["\n"]
    }
    
    # Create the exact curl command as you specified
    curl_script = f'''curl -sS -X POST "https://6kazu8ogvih4cs-8080.proxy.runpod.net/generate" \\
  -H "Content-Type: application/json" \\
  --data-binary @- << 'JSON'
{json.dumps(json_data, indent=2)}
JSON'''
    
    print("🌐 Running exact curl command:")
    print("=" * 60)
    print(curl_script)
    print("=" * 60)
    print()
    
    try:
        # Execute the curl command
        result = subprocess.run(['bash', '-c', curl_script], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Curl command executed successfully!")
            response = result.stdout.strip()
            print(f"📤 Raw response: {response}")
            return response
        else:
            print(f"❌ Curl command failed with return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Curl command timed out after 30 seconds")
        return None
    except Exception as e:
        print(f"❌ Error running curl command: {e}")
        return None

def parse_response_to_arrays(response_text):
    """Parse the LLM response and return both numeric and servo angle arrays"""
    
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
            numeric_array = default_array
        else:
            # Build finger curl mapping
            finger_curls = {}
            for finger, curl in matches:
                finger_curls[finger] = curl
                print(f"  Found: {finger} → {curl}")
            
            # Convert to numeric array in order: [pinky, ring, middle, index, thumb]
            finger_order = ['pinky', 'ring', 'middle', 'index', 'thumb']
            numeric_array = []
            
            for finger in finger_order:
                if finger in finger_curls:
                    curl_state = finger_curls[finger]
                    numeric_value = curl_to_numeric.get(curl_state, 1)
                    numeric_array.append(numeric_value)
                else:
                    print(f"  ⚠️ Missing {finger}, using half curl (1)")
                    numeric_array.append(1)
        
        # Convert to servo angles
        servo_angles = convert_numeric_to_servo_angles(numeric_array)
        
        return numeric_array, servo_angles
        
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        return default_array, convert_numeric_to_servo_angles(default_array)

def convert_numeric_to_servo_angles(numeric_array):
    """Convert numeric array [0-2] to servo angles [0-180]"""
    
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
        'thumb': {'no curl': 0, 'half curl': 90, 'full curl': 180},
        'index': {'no curl': 180, 'half curl': 90, 'full curl': 0},
        'middle': {'no curl': 180, 'half curl': 90, 'full curl': 0},
        'ring': {'no curl': 180, 'half curl': 100, 'full curl': 25},
        'pinky': {'no curl': 180, 'half curl': 90, 'full curl': 0}
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
    
    # Build servo angles array: [thumb, index, middle, ring, pinky, wrist]
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
    # Use the keyboard object from your terminal selection
    object_identity = "080_keyboard"
    object_size = "medium"
    object_position = "several feet away, left, bottom relative to the camera"
    object_orientation = "significantly rotated counterclockwise around the x-axis"
    
    print("🤖 LLM Finger Curl Prediction - Direct Curl Command")
    print("=" * 60)
    print(f"📝 Object: {object_identity}")
    print(f"📏 Size: {object_size}")
    print(f"📍 Position: {object_position}")
    print(f"🔄 Orientation: {object_orientation}")
    print()
    
    # Run the curl command
    response = run_curl_command_for_object(object_identity, object_size, object_position, object_orientation)
    
    if not response:
        print("❌ No response from API")
        return
    
    print("\n" + "=" * 60)
    print("🔄 Processing Response")
    print("=" * 60)
    
    # Parse the response
    numeric_array, servo_angles = parse_response_to_arrays(response)
    
    print("\n" + "=" * 60)
    print("📊 Final Results")
    print("=" * 60)
    print(f"🧠 Numeric Array: {numeric_array}")
    print(f"   [pinky={numeric_array[0]}, ring={numeric_array[1]}, middle={numeric_array[2]}, index={numeric_array[3]}, thumb={numeric_array[4]}]")
    print(f"   Values: 0=closed, 1=half, 2=extended")
    print()
    print(f"🎯 Servo Angles: {servo_angles}")
    print(f"   [thumb={servo_angles[0]}°, index={servo_angles[1]}°, middle={servo_angles[2]}°, ring={servo_angles[3]}°, pinky={servo_angles[4]}°, wrist={servo_angles[5]}°]")
    
    print("\n" + "=" * 60)
    print("🚀 Ready to Send to Robotic Hand")
    print("=" * 60)
    print("Use these commands:")
    print()
    print("1. Direct servo angles:")
    print(f"   python3 ble_pose_sender.py --angles {' '.join(map(str, servo_angles))}")
    print()
    print("2. LLM mode with servo angles:")
    print("   python3 ble_pose_sender.py --llm")
    print(f"   Press 's' and enter: {','.join(map(str, servo_angles))}")
    print("   Press Enter to send!")
    print()
    print("3. LLM mode with numeric array:")
    print("   python3 ble_pose_sender.py --llm")
    print(f"   Press 'n' and enter: {','.join(map(str, numeric_array))}")
    print("   Press Enter to send!")

if __name__ == "__main__":
    main()
