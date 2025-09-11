#!/usr/bin/env python3
"""
Master script to run the complete LLM → Robotic Hand pipeline.
This coordinates object detection, LLM processing, and BLE pose sending.
"""

import asyncio
import subprocess
import json
import re
import time
import sys
import os
from pathlib import Path

class MasterController:
    def __init__(self):
        self.latest_servo_angles = None
        self.is_processing = False
        self.ble_process = None
        
    async def get_llm_prediction(self, object_identity, object_size, object_position, object_orientation):
        """Get LLM prediction for object"""
        prompt = f"""Scene: A single everyday object is visible.
Object identity: {object_identity}.
Object size: {object_size}. Object position: {object_position}. Object orientation: {object_orientation}.
Task: Output only the finger curls in this exact format:
pinky: <no curl|half curl|full curl>; ring: <no curl|half curl|full curl>; middle: <no curl|half curl|full curl>; index: <no curl|half curl|full curl>; thumb: <no curl|half curl|full curl>
Do not add any extra words."""

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
        
        curl_script = f'''curl -sS -X POST "https://6kazu8ogvih4cs-8080.proxy.runpod.net/generate" \\
  -H "Content-Type: application/json" \\
  --data-binary @- << 'JSON'
{json.dumps(json_data, indent=2)}
JSON'''
        
        print(f"🌐 Getting LLM prediction for: {object_identity}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                curl_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if process.returncode == 0:
                response = stdout.decode().strip()
                print(f"✅ LLM Response: {response[:100]}...")
                return response
            else:
                print(f"❌ LLM API Error: {stderr.decode()}")
                return None
                
        except asyncio.TimeoutError:
            print("⏰ LLM API timeout")
            return None
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return None
    
    def parse_to_servo_angles(self, response):
        """Parse LLM response to servo angles"""
        curl_to_numeric = {'full curl': 0, 'half curl': 1, 'no curl': 2}
        default_array = [1, 1, 1, 1, 1]
        
        try:
            # Handle JSON response
            if response and response.strip().startswith('{'):
                response_data = json.loads(response)
                text = response_data.get('response', response_data.get('text', response))
            else:
                text = response or ""
            
            # Parse finger curls
            finger_pattern = r'(pinky|ring|middle|index|thumb):\s*(no curl|half curl|full curl)'
            matches = re.findall(finger_pattern, text.lower())
            
            if matches:
                finger_curls = {finger: curl for finger, curl in matches}
                finger_order = ['pinky', 'ring', 'middle', 'index', 'thumb']
                numeric_array = [curl_to_numeric.get(finger_curls.get(finger, 'half curl'), 1) 
                               for finger in finger_order]
                print(f"🔄 Parsed curls: {numeric_array} [pinky, ring, middle, index, thumb]")
            else:
                numeric_array = default_array
                print("⚠️ No curls found, using default")
            
            # Convert to servo angles
            servo_angles = self.numeric_to_servo_angles(numeric_array)
            return servo_angles
            
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return self.numeric_to_servo_angles(default_array)
    
    def numeric_to_servo_angles(self, numeric_array):
        """Convert numeric array to servo angles"""
        numeric_to_curl = {0: "full curl", 1: "half curl", 2: "no curl"}
        curl_states = [numeric_to_curl[val] for val in numeric_array]
        
        CURL_TO_ANGLE = {
            'thumb': {'no curl': 0, 'half curl': 90, 'full curl': 180},
            'index': {'no curl': 180, 'half curl': 90, 'full curl': 0},
            'middle': {'no curl': 180, 'half curl': 90, 'full curl': 0},
            'ring': {'no curl': 180, 'half curl': 100, 'full curl': 25},
            'pinky': {'no curl': 180, 'half curl': 90, 'full curl': 0}
        }
        
        finger_names = ['pinky', 'ring', 'middle', 'index', 'thumb']
        finger_angles = {}
        
        for i, curl in enumerate(curl_states):
            finger = finger_names[i]
            finger_angles[finger] = CURL_TO_ANGLE[finger][curl]
        
        return [
            finger_angles['thumb'],
            finger_angles['index'], 
            finger_angles['middle'],
            finger_angles['ring'],
            finger_angles['pinky'],
            90  # wrist
        ]
    
    async def send_to_ble_pose_sender(self, servo_angles):
        """Send servo angles to BLE pose sender"""
        try:
            print(f"🤖 Sending to robotic hand: {servo_angles}")
            cmd = ['python3', 'ble_pose_sender.py', '--angles'] + [str(x) for x in servo_angles]
            
            # Check if BLE dependencies are available
            try:
                result = subprocess.run(['python3', '-c', 'import bleak'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    # BLE available, send directly
                    print(f"📤 Executing: {' '.join(cmd)}")
                    process = await asyncio.create_subprocess_exec(*cmd)
                    await process.wait()
                    print("✅ Sent to robotic hand!")
                else:
                    # BLE not available, show command
                    print(f"⚠️ BLE not available, use this command:")
                    print(f"   {' '.join(cmd)}")
            except:
                print(f"💡 Manual command: {' '.join(cmd)}")
                
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    async def process_object(self, object_identity, object_size, object_position, object_orientation):
        """Process a single object through the complete pipeline"""
        if self.is_processing:
            print("⚠️ Already processing, skipping...")
            return False
        
        self.is_processing = True
        
        try:
            print(f"\n🎯 Processing Object: {object_identity}")
            print(f"   Size: {object_size}")
            print(f"   Position: {object_position}")
            print(f"   Orientation: {object_orientation}")
            
            # Step 1: Get LLM prediction
            response = await self.get_llm_prediction(object_identity, object_size, object_position, object_orientation)
            
            if not response:
                print("❌ No LLM response, using default pose")
                servo_angles = [90, 90, 90, 100, 90, 90]  # Default neutral
            else:
                # Step 2: Parse to servo angles
                servo_angles = self.parse_to_servo_angles(response)
            
            # Step 3: Send to robotic hand
            self.latest_servo_angles = servo_angles
            print(f"🎯 Final servo angles: {servo_angles}")
            print(f"   [thumb={servo_angles[0]}°, index={servo_angles[1]}°, middle={servo_angles[2]}°, ring={servo_angles[3]}°, pinky={servo_angles[4]}°, wrist={servo_angles[5]}°]")
            
            await self.send_to_ble_pose_sender(servo_angles)
            
            return True
            
        finally:
            self.is_processing = False

async def demo_mode():
    """Run demo with sample objects"""
    controller = MasterController()
    
    print("🚀 Running Complete LLM → Robotic Hand Pipeline")
    print("=" * 60)
    
    # Sample objects to process
    objects = [
        ("080_keyboard", "medium", "several feet away, left, bottom relative to the camera", "significantly rotated counterclockwise around the x-axis"),
        ("010_potted_meat_can", "small", "arm's-length, centered, below relative to the camera", "strongly rotated around the x-axis"),
        ("025_mug", "medium", "close, right side, table level relative to the camera", "upright, handle facing left"),
    ]
    
    for i, (obj_id, size, position, orientation) in enumerate(objects, 1):
        print(f"\n📸 Processing Object {i}/{len(objects)}")
        print("=" * 40)
        
        success = await controller.process_object(obj_id, size, position, orientation)
        
        if success:
            print("✅ Object processed successfully!")
        else:
            print("❌ Object processing failed")
        
        # Wait between objects
        if i < len(objects):
            print("\n⏳ Waiting 3 seconds before next object...")
            await asyncio.sleep(3)
    
    print("\n🎉 Demo completed!")
    print("=" * 60)
    
    if controller.latest_servo_angles:
        angles = controller.latest_servo_angles
        print(f"🎯 Latest servo angles: {angles}")
        print(f"\n💡 Manual commands you can use:")
        print(f"   python3 ble_pose_sender.py --angles {' '.join(map(str, angles))}")
        print(f"   python3 ble_pose_sender.py --llm")
        print(f"   (then press 's' and enter: {','.join(map(str, angles))})")

async def interactive_mode():
    """Interactive mode for custom objects"""
    controller = MasterController()
    
    print("🎮 Interactive Mode")
    print("=" * 40)
    print("Enter object descriptions to process through the pipeline.")
    print("Type 'quit' to exit.")
    print()
    
    while True:
        try:
            print("📝 Enter object details:")
            obj_id = input("  Object ID (e.g., '080_keyboard'): ").strip()
            if obj_id.lower() == 'quit':
                break
            
            size = input("  Size (small/medium/large): ").strip() or "medium"
            position = input("  Position: ").strip() or "arm's-length, centered"
            orientation = input("  Orientation: ").strip() or "upright"
            
            print("\n🔄 Processing...")
            success = await controller.process_object(obj_id, size, position, orientation)
            
            if success:
                print("✅ Processing complete!")
            else:
                print("❌ Processing failed")
            
            print("\n" + "="*40)
            
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except EOFError:
            print("\n👋 Exiting...")
            break

def main():
    """Main function"""
    print("🤖 Master LLM → Robotic Hand Controller")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            asyncio.run(demo_mode())
        elif sys.argv[1] == "--interactive":
            asyncio.run(interactive_mode())
        elif sys.argv[1] == "--keyboard":
            # Quick test with keyboard object
            async def quick_test():
                controller = MasterController()
                await controller.process_object(
                    "080_keyboard",
                    "medium",
                    "several feet away, left, bottom relative to the camera",
                    "significantly rotated counterclockwise around the x-axis"
                )
            asyncio.run(quick_test())
        else:
            print("❌ Unknown option. Use --demo, --interactive, or --keyboard")
    else:
        print("Choose a mode:")
        print("  --demo        : Run with sample objects")
        print("  --interactive : Enter custom objects")
        print("  --keyboard    : Quick test with keyboard object")
        print()
        print("Example:")
        print("  python3 run_everything.py --demo")

if __name__ == "__main__":
    main()
