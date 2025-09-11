#!/usr/bin/env python3
"""
Queue-based LLM API processor for robotic hand control.
Processes object descriptions one at a time, waiting for each response before sending the next.
"""

import asyncio
import subprocess
import json
import re
import time
from collections import deque
from typing import Optional, Dict, List, Tuple
import threading

class LLMQueueProcessor:
    def __init__(self):
        self.request_queue = deque()
        self.is_processing = False
        self.latest_result = None
        self.processing_lock = threading.Lock()
        
    def add_object_description(self, object_identity: str, object_size: str, 
                             object_position: str, object_orientation: str) -> None:
        """Add a new object description to the processing queue"""
        description = {
            'object_identity': object_identity,
            'object_size': object_size,
            'object_position': object_position,
            'object_orientation': object_orientation,
            'timestamp': time.time()
        }
        
        # Only keep the most recent request if queue is getting full
        if len(self.request_queue) > 2:
            self.request_queue.popleft()  # Remove oldest
            print("⚠️ Queue full, removed oldest request")
        
        self.request_queue.append(description)
        print(f"📝 Added to queue: {object_identity} (queue size: {len(self.request_queue)})")
        
    def make_llm_request(self, description: Dict) -> Optional[str]:
        """Make a single LLM API request"""
        prompt = f"""Scene: A single everyday object is visible.
Object identity: {description['object_identity']}.
Object size: {description['object_size']}. Object position: {description['object_position']}. Object orientation: {description['object_orientation']}.
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
        
        print(f"🌐 Processing: {description['object_identity']}")
        
        try:
            result = subprocess.run(['bash', '-c', curl_script], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response = result.stdout.strip()
                print(f"✅ Response received for {description['object_identity']}")
                return response
            else:
                print(f"❌ API error for {description['object_identity']}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout for {description['object_identity']}")
            return None
        except Exception as e:
            print(f"❌ Error for {description['object_identity']}: {e}")
            return None
    
    def parse_response_to_arrays(self, response_text: str) -> Tuple[List[int], List[int]]:
        """Parse LLM response to numeric and servo angle arrays"""
        curl_to_numeric = {
            'full curl': 0, 'half curl': 1, 'no curl': 2
        }
        default_array = [1, 1, 1, 1, 1]
        
        try:
            if response_text and response_text.strip().startswith('{'):
                response_data = json.loads(response_text)
                text = response_data.get('response', response_data.get('text', response_text))
            else:
                text = response_text or ""
            
            finger_pattern = r'(pinky|ring|middle|index|thumb):\s*(no curl|half curl|full curl)'
            matches = re.findall(finger_pattern, text.lower())
            
            if not matches:
                numeric_array = default_array
            else:
                finger_curls = {finger: curl for finger, curl in matches}
                finger_order = ['pinky', 'ring', 'middle', 'index', 'thumb']
                numeric_array = [curl_to_numeric.get(finger_curls.get(finger, 'half curl'), 1) 
                               for finger in finger_order]
            
            servo_angles = self.convert_to_servo_angles(numeric_array)
            return numeric_array, servo_angles
            
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return default_array, self.convert_to_servo_angles(default_array)
    
    def convert_to_servo_angles(self, numeric_array: List[int]) -> List[int]:
        """Convert numeric array to servo angles"""
        numeric_to_curl = {0: "full curl", 1: "half curl", 2: "no curl"}
        curl_states = [numeric_to_curl.get(val, "half curl") for val in numeric_array]
        
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
            finger_angles[finger] = CURL_TO_ANGLE.get(finger, {}).get(curl, 90)
        
        return [
            finger_angles.get('thumb', 90),
            finger_angles.get('index', 90),
            finger_angles.get('middle', 90),
            finger_angles.get('ring', 90),
            finger_angles.get('pinky', 90),
            90  # wrist
        ]
    
    async def process_queue_continuously(self):
        """Continuously process the queue, one request at a time"""
        print("🔄 Starting queue processor...")
        
        while True:
            if self.request_queue and not self.is_processing:
                with self.processing_lock:
                    self.is_processing = True
                    
                try:
                    # Get the next request
                    description = self.request_queue.popleft()
                    print(f"🎯 Processing: {description['object_identity']} (queue: {len(self.request_queue)} remaining)")
                    
                    # Make the API request
                    response = self.make_llm_request(description)
                    
                    if response:
                        # Parse the response
                        numeric_array, servo_angles = self.parse_response_to_arrays(response)
                        
                        # Store the latest result
                        self.latest_result = {
                            'description': description,
                            'response': response,
                            'numeric_array': numeric_array,
                            'servo_angles': servo_angles,
                            'timestamp': time.time()
                        }
                        
                        print(f"✅ Processed {description['object_identity']}")
                        print(f"   Numeric: {numeric_array}")
                        print(f"   Servo: {servo_angles}")
                        
                        # Trigger sending to robotic hand
                        await self.send_to_hand(servo_angles)
                    
                finally:
                    self.is_processing = False
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
    
    async def send_to_hand(self, servo_angles: List[int]):
        """Send servo angles to the robotic hand"""
        try:
            print(f"🤖 Sending to hand: {servo_angles}")
            # You can implement actual BLE sending here
            # For now, we'll just show the command
            cmd = f"python3 ble_pose_sender.py --angles {' '.join(map(str, servo_angles))}"
            print(f"📤 Command: {cmd}")
            
            # Uncomment this to actually send:
            # subprocess.run(['python3', 'ble_pose_sender.py', '--angles'] + [str(x) for x in servo_angles])
            
        except Exception as e:
            print(f"❌ Error sending to hand: {e}")
    
    def get_latest_result(self) -> Optional[Dict]:
        """Get the most recent processing result"""
        return self.latest_result
    
    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        return {
            'queue_size': len(self.request_queue),
            'is_processing': self.is_processing,
            'has_latest_result': self.latest_result is not None
        }

class ObjectDescriptionInput:
    """Helper class to simulate continuous object descriptions"""
    
    def __init__(self, processor: LLMQueueProcessor):
        self.processor = processor
        self.running = False
    
    async def simulate_object_stream(self):
        """Simulate a stream of object descriptions (replace with your actual input)"""
        test_objects = [
            ("080_keyboard", "medium", "several feet away, left, bottom", "rotated counterclockwise around x-axis"),
            ("010_potted_meat_can", "small", "arm's-length, centered, below", "strongly rotated around x-axis"),
            ("025_mug", "medium", "close, right side, table level", "upright, handle facing left"),
            ("035_power_drill", "large", "arm's-length, centered, above", "tilted 45 degrees"),
        ]
        
        for i, (obj_id, size, pos, orient) in enumerate(test_objects):
            if not self.running:
                break
                
            print(f"\n📸 Frame {i+1}: New object detected")
            self.processor.add_object_description(obj_id, size, pos, orient)
            
            # Wait before adding next object (simulating frame rate)
            await asyncio.sleep(3)  # 3 seconds between objects
    
    def start_simulation(self):
        """Start the object detection simulation"""
        self.running = True
    
    def stop_simulation(self):
        """Stop the object detection simulation"""
        self.running = False

async def main():
    """Main function demonstrating the queue-based processing"""
    print("🚀 LLM Queue Processor for Robotic Hand")
    print("=" * 50)
    print("This system processes object descriptions one at a time,")
    print("waiting for each API response before sending the next request.")
    print("=" * 50)
    
    # Create processor
    processor = LLMQueueProcessor()
    
    # Create input simulator
    input_sim = ObjectDescriptionInput(processor)
    
    # Start the queue processor
    processor_task = asyncio.create_task(processor.process_queue_continuously())
    
    # Start object detection simulation
    input_sim.start_simulation()
    simulation_task = asyncio.create_task(input_sim.simulate_object_stream())
    
    try:
        # Run both tasks concurrently
        await asyncio.gather(processor_task, simulation_task)
    except KeyboardInterrupt:
        print("\n👋 Stopping processor...")
        input_sim.stop_simulation()
        processor_task.cancel()
        simulation_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
