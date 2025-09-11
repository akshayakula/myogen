#!/usr/bin/env python3
"""
Example showing how to integrate the queue-based LLM processing 
with the BLE pose sender for continuous object detection.
"""

import asyncio
import time
from smart_llm_sender import SmartLLMSender
import subprocess

class ObjectDetectionSimulator:
    """Simulates object detection frames coming in"""
    
    def __init__(self):
        self.objects = [
            ("080_keyboard", "medium", "several feet away, left, bottom", "rotated counterclockwise around x-axis"),
            ("010_potted_meat_can", "small", "arm's-length, centered, below", "strongly rotated around x-axis"),
            ("025_mug", "medium", "close, right side, table level", "upright, handle facing left"),
            ("035_power_drill", "large", "arm's-length, centered, above", "tilted 45 degrees"),
        ]
        self.current_index = 0
    
    def get_next_object(self):
        """Get next object description (simulates new frame)"""
        if self.current_index < len(self.objects):
            obj = self.objects[self.current_index]
            self.current_index += 1
            return obj
        return None

async def main_integration_loop():
    """Main integration loop showing the complete workflow"""
    print("🤖 LLM → BLE Pose Sender Integration")
    print("=" * 60)
    print("This demonstrates:")
    print("1. Object detection frames come in")
    print("2. Queue them for LLM processing") 
    print("3. Process one at a time (wait for response)")
    print("4. Send servo angles to robotic hand")
    print("=" * 60)
    
    # Initialize components
    llm_sender = SmartLLMSender()
    object_detector = ObjectDetectionSimulator()
    
    frame_count = 0
    
    while True:
        try:
            # Simulate new object detection frame every 2 seconds
            await asyncio.sleep(2)
            frame_count += 1
            
            # Get new object (simulates computer vision detection)
            new_object = object_detector.get_next_object()
            if new_object:
                obj_id, size, position, orientation = new_object
                print(f"\n📸 Frame {frame_count}: Detected {obj_id}")
                
                # Add to LLM processing queue
                llm_sender.add_object(obj_id, size, position, orientation)
            
            # Try to process next object in queue (non-blocking)
            processed = await llm_sender.process_next_object()
            
            if processed and llm_sender.latest_servo_angles:
                # Send to robotic hand
                servo_angles = llm_sender.latest_servo_angles
                
                print(f"🚀 Sending to hand: {servo_angles}")
                
                # Method 1: Direct command (uncomment to actually send)
                # cmd = ['python3', 'ble_pose_sender.py', '--angles'] + [str(x) for x in servo_angles]
                # subprocess.run(cmd)
                
                # Method 2: Store in BLE pose sender's LLM mode (preferred)
                print(f"💾 Ready for BLE sender: {','.join(map(str, servo_angles))}")
                print("   Use: python3 ble_pose_sender.py --llm")
                print("   Press 's' and enter the angles above")
                print("   Press Enter to send to hand!")
            
            # Show status
            status = llm_sender.get_status()
            if status['queue_size'] > 0 or status['is_processing']:
                print(f"📊 Queue: {status['queue_size']}, Processing: {status['is_processing']}")
            
            # Stop after processing all objects
            if not new_object and status['queue_size'] == 0 and not status['is_processing']:
                print("\n✅ All objects processed!")
                break
                
        except KeyboardInterrupt:
            print("\n👋 Stopping integration...")
            break

def quick_test():
    """Quick test of the integration"""
    print("🧪 Quick Integration Test")
    print("=" * 40)
    
    # Create sender
    sender = SmartLLMSender()
    
    # Add the keyboard object from your example
    sender.add_object(
        "080_keyboard",
        "medium", 
        "several feet away, left, bottom relative to the camera",
        "significantly rotated counterclockwise around the x-axis"
    )
    
    print("\n📝 Object added to queue")
    print("🔄 To process: run the async main loop")
    print("📤 Integration commands:")
    print("   python3 integration_example.py --async")
    print("   python3 ble_pose_sender.py --llm")

if __name__ == "__main__":
    import sys
    
    if "--async" in sys.argv:
        asyncio.run(main_integration_loop())
    else:
        quick_test()
        print("\n🚀 Run with --async flag for full integration loop")
