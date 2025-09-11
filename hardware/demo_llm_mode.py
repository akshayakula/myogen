#!/usr/bin/env python3
"""
Demo script showing how to use the new LLM mode with the BLE pose sender.
This script demonstrates the complete workflow from LLM prediction to hand control.
"""

import asyncio
import subprocess
import json
import sys
import os

# Add the current directory to path so we can import from ble_pose_sender
sys.path.insert(0, os.path.dirname(__file__))

def demo_numeric_arrays():
    """Demonstrate various numeric array examples"""
    examples = [
        {
            'name': 'Open Hand',
            'array': [2, 2, 2, 2, 2],
            'description': 'All fingers extended'
        },
        {
            'name': 'Closed Fist',
            'array': [0, 0, 0, 0, 0],
            'description': 'All fingers closed'
        },
        {
            'name': 'Peace Sign',
            'array': [0, 0, 2, 2, 0],
            'description': 'Index and middle fingers extended'
        },
        {
            'name': 'Thumbs Up',
            'array': [0, 0, 0, 0, 2],
            'description': 'Only thumb extended'
        },
        {
            'name': 'Pointing',
            'array': [0, 0, 0, 2, 0],
            'description': 'Only index finger extended'
        },
        {
            'name': 'Rock On',
            'array': [2, 0, 0, 2, 2],
            'description': 'Thumb, index, and pinky extended'
        },
        {
            'name': 'Neutral/Half',
            'array': [1, 1, 1, 1, 1],
            'description': 'All fingers half-closed'
        },
        {
            'name': 'Grasp Position',
            'array': [1, 1, 1, 1, 0],
            'description': 'Fingers partially closed for grasping'
        }
    ]
    
    print("🤖 LLM Mode Numeric Array Examples")
    print("="*60)
    print("Format: [pinky, ring, middle, index, thumb]")
    print("Values: 0=closed, 1=half, 2=extended")
    print("="*60)
    
    for i, example in enumerate(examples, 1):
        array_str = ','.join(map(str, example['array']))
        print(f"\n{i:2d}. {example['name']:<15} - {example['description']}")
        print(f"    Array: [{array_str}]")
        print(f"    Command: python3 ble_pose_sender.py --numeric {' '.join(map(str, example['array']))}")
    
    return examples

def demo_llm_workflow():
    """Demonstrate the complete LLM workflow"""
    print("\n" + "="*70)
    print("🧠 COMPLETE LLM WORKFLOW DEMONSTRATION")
    print("="*70)
    
    print("\n1. 🌐 LLM API Call:")
    print("   curl -sS -X POST 'https://your-llm-endpoint/generate' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     --data-binary '{\"prompt\": \"Scene description...\", ...}'")
    
    print("\n2. 📤 Example LLM Response:")
    example_response = "pinky: no curl; ring: no curl; middle: no curl; index: no curl; thumb: no curl"
    print(f"   {example_response}")
    
    print("\n3. 🔄 Parse to Numeric Array:")
    print("   no curl → 2 (extended)")
    print("   half curl → 1 (half-closed)")  
    print("   full curl → 0 (closed)")
    print("   Result: [2, 2, 2, 2, 2] (open hand)")
    
    print("\n4. 🤖 Send to Robotic Hand:")
    print("   Method A - Direct command:")
    print("     python3 ble_pose_sender.py --numeric 2 2 2 2 2")
    print()
    print("   Method B - LLM interactive mode:")
    print("     python3 ble_pose_sender.py --llm")
    print("     > Enter numeric array: 2,2,2,2,2")
    print("     > Press Enter to send to hand")
    print()
    print("   Method C - Store and trigger:")
    print("     1. Store array in LLM mode with 'n' key")
    print("     2. Press Enter anytime to send latest array")

def demo_integration_script():
    """Show how to create an integration script"""
    script_content = '''#!/usr/bin/env python3
"""
Example integration script: LLM prediction to hand control
"""
import subprocess
import json
import re

def get_llm_prediction(scene_description):
    """Get finger curl prediction from LLM"""
    curl_cmd = [
        'curl', '-sS', '-X', 'POST', 'https://your-llm-endpoint/generate',
        '-H', 'Content-Type: application/json',
        '--data-binary', json.dumps({
            "prompt": f"Scene: {scene_description}\\nTask: Output finger curls in format: pinky: <curl>; ring: <curl>; ...",
            "max_new_tokens": 100,
            "temperature": 0.7
        })
    ]
    
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    return result.stdout.strip()

def parse_to_numeric(llm_response):
    """Convert LLM response to numeric array"""
    curl_to_numeric = {'full curl': 0, 'half curl': 1, 'no curl': 2}
    pattern = r'(pinky|ring|middle|index|thumb):\\s*(no curl|half curl|full curl)'
    matches = re.findall(pattern, llm_response.lower())
    
    finger_curls = {finger: curl for finger, curl in matches}
    return [finger_curls.get(f, 'half curl') for f in ['pinky', 'ring', 'middle', 'index', 'thumb']]

def send_to_hand(numeric_array):
    """Send numeric array to robotic hand"""
    cmd = ['python3', 'ble_pose_sender.py', '--numeric'] + [str(x) for x in numeric_array]
    subprocess.run(cmd)

# Main workflow
scene = "A small can on the table below the camera"
llm_response = get_llm_prediction(scene)
numeric_array = parse_to_numeric(llm_response)
send_to_hand(numeric_array)
'''
    
    print("\n" + "="*70)
    print("📝 INTEGRATION SCRIPT EXAMPLE")
    print("="*70)
    print("Here's how you can create a complete automation script:")
    print(script_content)

def main():
    """Main demo function"""
    print("🚀 LLM Mode Demo for BLE Pose Sender")
    print("="*50)
    
    print("\nThis demo shows the new LLM mode functionality:")
    print("✅ Numeric array input [0-2] for each finger")
    print("✅ Interactive LLM mode with Enter key trigger")
    print("✅ Command line --llm and --numeric flags")
    print("✅ Integration with curl/API responses")
    
    while True:
        print("\n" + "="*50)
        print("📋 DEMO OPTIONS:")
        print("1. Show numeric array examples")
        print("2. Show complete LLM workflow")
        print("3. Show integration script example")
        print("4. Test BLE pose sender (requires hardware)")
        print("5. Exit")
        
        try:
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                demo_numeric_arrays()
            elif choice == '2':
                demo_llm_workflow()
            elif choice == '3':
                demo_integration_script()
            elif choice == '4':
                print("\n🤖 Testing BLE Pose Sender...")
                print("Choose a test mode:")
                print("a. Start in LLM mode: python3 ble_pose_sender.py --llm")
                print("b. Send specific array: python3 ble_pose_sender.py --numeric 2 2 2 2 2")
                print("c. Test parsing: python3 test_llm_integration.py --parse")
                
                test_choice = input("Select (a/b/c): ").strip().lower()
                if test_choice == 'a':
                    subprocess.run(['python3', 'ble_pose_sender.py', '--llm'])
                elif test_choice == 'b':
                    subprocess.run(['python3', 'ble_pose_sender.py', '--numeric', '2', '2', '2', '2', '2'])
                elif test_choice == 'c':
                    subprocess.run(['python3', 'test_llm_integration.py', '--parse'])
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
