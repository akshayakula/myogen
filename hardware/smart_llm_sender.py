#!/usr/bin/env python3
"""
Smart LLM sender that queues object descriptions and processes them one at a time.
Integrates directly with the BLE pose sender's LLM mode.
"""

import asyncio
import subprocess
import json
import re
import time
from collections import deque
import sys
import os

class SmartLLMSender:
    def __init__(self):
        self.pending_objects = deque()
        self.is_processing = False
        self.latest_servo_angles = None
        
    def add_object(self, object_identity: str, object_size: str, object_position: str, object_orientation: str):
        """Add object description to processing queue"""
        # Only keep the most recent object if queue is building up
        if len(self.pending_objects) > 1:
            old_obj = self.pending_objects.popleft()
            print(f"⚠️ Replacing queued object: {old_obj['object_identity']} → {object_identity}")
        
        obj_desc = {
            'object_identity': object_identity,
            'object_size': object_size,
            'object_position': object_position,
            'object_orientation': object_orientation,
            'timestamp': time.time()
        }
        
        self.pending_objects.append(obj_desc)
        print(f"📝 Queued: {object_identity} (queue size: {len(self.pending_objects)})")
    
    async def process_next_object(self) -> bool:
        """Process the next object in queue, return True if processed"""
        if not self.pending_objects or self.is_processing:
            return False
        
        self.is_processing = True
        
        try:
            obj_desc = self.pending_objects.popleft()
            print(f"\n🎯 Processing: {obj_desc['object_identity']}")
            
            # Make LLM request
            response = await self.make_llm_request(obj_desc)
            
            if response:
                # Parse and convert to servo angles
                servo_angles = self.parse_to_servo_angles(response)
                self.latest_servo_angles = servo_angles
                
                print(f"✅ Ready to send: {servo_angles}")
                print(f"   [thumb={servo_angles[0]}°, index={servo_angles[1]}°, middle={servo_angles[2]}°, ring={servo_angles[3]}°, pinky={servo_angles[4]}°, wrist={servo_angles[5]}°]")
                
                return True
            else:
                print(f"❌ No response for {obj_desc['object_identity']}")
                return False
                
        finally:
            self.is_processing = False
    
    async def make_llm_request(self, obj_desc: dict) -> str:
        """Make async LLM API request"""
        prompt = f"""Scene: A single everyday object is visible.
Object identity: {obj_desc['object_identity']}.
Object size: {obj_desc['object_size']}. Object position: {obj_desc['object_position']}. Object orientation: {obj_desc['object_orientation']}.
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
        
        try:
            # Run curl command asynchronously
            process = await asyncio.create_subprocess_shell(
                curl_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if process.returncode == 0:
                response = stdout.decode().strip()
                print(f"📤 API response: {response[:100]}...")
                return response
            else:
                print(f"❌ API error: {stderr.decode()}")
                return None
                
        except asyncio.TimeoutError:
            print("⏰ API request timed out")
            return None
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None
    
    def parse_to_servo_angles(self, response: str) -> list:
        """Parse LLM response directly to servo angles"""
        # Parse finger curls
        curl_to_numeric = {'full curl': 0, 'half curl': 1, 'no curl': 2}
        default_array = [1, 1, 1, 1, 1]
        
        try:
            if response and response.strip().startswith('{'):
                response_data = json.loads(response)
                text = response_data.get('response', response_data.get('text', response))
            else:
                text = response or ""
            
            finger_pattern = r'(pinky|ring|middle|index|thumb):\s*(no curl|half curl|full curl)'
            matches = re.findall(finger_pattern, text.lower())
            
            if matches:
                finger_curls = {finger: curl for finger, curl in matches}
                finger_order = ['pinky', 'ring', 'middle', 'index', 'thumb']
                numeric_array = [curl_to_numeric.get(finger_curls.get(finger, 'half curl'), 1) 
                               for finger in finger_order]
                print(f"🔄 Parsed: {numeric_array} [pinky, ring, middle, index, thumb]")
            else:
                numeric_array = default_array
                print("⚠️ Using default array")
            
            # Convert to servo angles
            return self.numeric_to_servo_angles(numeric_array)
            
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return self.numeric_to_servo_angles(default_array)
    
    def numeric_to_servo_angles(self, numeric_array: list) -> list:
        """Convert [0-2] numeric array to servo angles"""
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
    
    def get_status(self) -> dict:
        """Get current processor status"""
        return {
            'queue_size': len(self.pending_objects),
            'is_processing': self.is_processing,
            'latest_angles': self.latest_servo_angles
        }

# Global processor instance
llm_processor = SmartLLMSender()

async def interactive_mode():
    """Interactive mode for testing"""
    print("🎮 Interactive LLM Processor Mode")
    print("=" * 50)
    print("Commands:")
    print("  add <object_id> <size> <position> <orientation>")
    print("  process - Process next object in queue")
    print("  send - Send latest angles to BLE pose sender")
    print("  status - Show queue status")
    print("  auto - Start auto-processing mode")
    print("  quit - Exit")
    print("=" * 50)
    
    auto_mode = False
    
    while True:
        try:
            if auto_mode:
                # Auto-process mode
                processed = await llm_processor.process_next_object()
                if processed and llm_processor.latest_servo_angles:
                    # Auto-send to BLE pose sender
                    angles = llm_processor.latest_servo_angles
                    cmd = ['python3', 'ble_pose_sender.py', '--angles'] + [str(x) for x in angles]
                    print(f"🚀 Auto-sending: {' '.join(cmd)}")
                    # Uncomment to actually send:
                    # subprocess.run(cmd)
                
                await asyncio.sleep(1)  # Check every second
                continue
            
            command = input("\n> ").strip().lower()
            
            if command.startswith('add '):
                parts = command.split(' ', 4)
                if len(parts) >= 5:
                    _, obj_id, size, position, orientation = parts
                    llm_processor.add_object(obj_id, size, position, orientation)
                else:
                    print("❌ Usage: add <object_id> <size> <position> <orientation>")
            
            elif command == 'process':
                processed = await llm_processor.process_next_object()
                if not processed:
                    print("⚠️ Nothing to process or already processing")
            
            elif command == 'send':
                if llm_processor.latest_servo_angles:
                    angles = llm_processor.latest_servo_angles
                    cmd = f"python3 ble_pose_sender.py --angles {' '.join(map(str, angles))}"
                    print(f"📤 Command: {cmd}")
                    # Uncomment to actually send:
                    # subprocess.run(['python3', 'ble_pose_sender.py', '--angles'] + [str(x) for x in angles])
                else:
                    print("⚠️ No servo angles available")
            
            elif command == 'status':
                status = llm_processor.get_status()
                print(f"📊 Queue: {status['queue_size']}, Processing: {status['is_processing']}")
                if status['latest_angles']:
                    print(f"   Latest: {status['latest_angles']}")
            
            elif command == 'auto':
                auto_mode = True
                print("🔄 Starting auto-processing mode... (Ctrl+C to stop)")
            
            elif command == 'quit':
                break
            
            else:
                print("❌ Unknown command")
                
        except KeyboardInterrupt:
            if auto_mode:
                auto_mode = False
                print("\n⏹️ Stopped auto-processing mode")
            else:
                break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("🚀 Smart LLM Sender - Queue-Based Processing")
    print("=" * 50)
    print("This processes object descriptions one at a time,")
    print("waiting for each API response before processing the next.")
    print("=" * 50)
    
    # Example usage
    print("\n📝 Example: Adding keyboard object...")
    llm_processor.add_object(
        "080_keyboard", 
        "medium", 
        "several feet away, left, bottom relative to the camera",
        "significantly rotated counterclockwise around the x-axis"
    )
    
    # Run interactive mode
    asyncio.run(interactive_mode())

if __name__ == "__main__":
    main()
