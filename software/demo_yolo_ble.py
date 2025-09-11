#!/usr/bin/env python3
"""
Demo script showing YOLO + LLM + BLE integration
Simulates the complete pipeline without requiring webcam or Arduino
"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(__file__))

async def demo_complete_pipeline():
    """Demonstrate the complete YOLO → LLM → BLE pipeline"""
    print("🎬 DEMO: Complete YOLO + LLM + BLE Pipeline")
    print("=" * 60)
    
    try:
        from yolo_webcam import YOLOWebcamDetector
        
        # Create detector with LLM enabled
        print("🔧 Creating YOLO detector with LLM integration...")
        detector = YOLOWebcamDetector(
            enable_llm_api=True,
            api_url="https://6kazu8ogvih4cs-8080.proxy.runpod.net/generate"
        )
        
        # Simulate different object detections
        demo_objects = [
            {
                'name': 'apple',
                'description': 'Scene: A single everyday object is visible.\nObject identity: apple.\nObject size: small. Object position: arm\'s-length, centered, middle relative to the camera. Object orientation: not rotated.\n',
                'expected_curl': 'grasping motion for small round object'
            },
            {
                'name': 'keyboard',
                'description': 'Scene: A single everyday object is visible.\nObject identity: keyboard.\nObject size: medium. Object position: arm\'s-length, left, middle relative to the camera. Object orientation: slightly rotated around the y-axis.\n',
                'expected_curl': 'typing motion with extended fingers'
            },
            {
                'name': 'cup',
                'description': 'Scene: A single everyday object is visible.\nObject identity: cup.\nObject size: small. Object position: arm\'s-length, right, middle relative to the camera. Object orientation: upright.\n',
                'expected_curl': 'grasping motion for cylindrical object'
            }
        ]
        
        for i, obj in enumerate(demo_objects, 1):
            print(f"\n🎯 Demo {i}/3: Detecting {obj['name']}")
            print("-" * 40)
            print("📋 Scene Description:")
            print(obj['description'])
            
            print("🧠 Expected LLM behavior:")
            print(f"   {obj['expected_curl']}")
            
            # Simulate LLM response parsing (without actual API call)
            print("🔄 Simulating LLM response parsing...")
            
            # Test different curl patterns for demo
            if obj['name'] == 'apple':
                test_response = "pinky: half curl; ring: half curl; middle: half curl; index: half curl; thumb: half curl"
            elif obj['name'] == 'keyboard':
                test_response = "pinky: no curl; ring: no curl; middle: no curl; index: no curl; thumb: no curl"
            else:  # cup
                test_response = "pinky: full curl; ring: full curl; middle: half curl; index: half curl; thumb: no curl"
            
            servo_angles = detector.parse_llm_response_to_servo_angles(test_response)
            
            print(f"📤 LLM Response: {test_response}")
            print(f"🎯 Servo Angles: {servo_angles}")
            print(f"   [thumb={servo_angles[0]}°, index={servo_angles[1]}°, middle={servo_angles[2]}°, ring={servo_angles[3]}°, pinky={servo_angles[4]}°, wrist={servo_angles[5]}°]")
            
            # Simulate BLE sending
            print("🤖 Simulating BLE send to Arduino...")
            success = await detector.send_pose_to_hand(servo_angles)
            
            if success:
                print("✅ Pose sent successfully!")
            else:
                print("❌ Pose send failed")
            
            print("⏱️ Waiting 2 seconds...")
            await asyncio.sleep(2)
        
        print(f"\n🎉 Demo completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

async def show_usage_examples():
    """Show different ways to use the integrated system"""
    print("\n📚 USAGE EXAMPLES")
    print("=" * 60)
    
    print("🔥 Basic Usage (YOLO only):")
    print("   python3 yolo_webcam.py")
    print()
    
    print("🧠 With LLM Integration:")
    print("   python3 yolo_webcam.py --enable-llm")
    print()
    
    print("⚙️ Advanced Configuration:")
    print("   python3 yolo_webcam.py --enable-llm --api-cooldown 3.0 --confidence 0.7")
    print()
    
    print("💾 Save Images and Logs:")
    print("   python3 yolo_webcam.py --enable-llm --save-images --output scene_log.txt")
    print()
    
    print("🎯 Custom Model:")
    print("   python3 yolo_webcam.py --enable-llm --model yolov8s.pt")
    print()
    
    print("📋 Available Arguments:")
    print("   --enable-llm        Enable LLM API calls")
    print("   --api-url URL       Custom LLM API endpoint")
    print("   --api-cooldown SEC  Seconds between API calls (default: 5.0)")
    print("   --model MODEL       YOLO model (yolov8n.pt, yolov8s.pt, etc.)")
    print("   --confidence FLOAT  Detection confidence threshold")
    print("   --save-images       Save detected frames")
    print("   --output FILE       Save scene descriptions to file")

async def main():
    """Main demo function"""
    print("🚀 YOLO + LLM + BLE Integration Demo")
    print("This demo shows the complete pipeline from object detection to robotic hand control")
    print()
    
    # Run the demo
    await demo_complete_pipeline()
    
    # Show usage examples
    await show_usage_examples()
    
    print("\n🎯 Ready to run the real system!")
    print("Connect your webcam and Arduino, then run:")
    print("   python3 yolo_webcam.py --enable-llm")

if __name__ == "__main__":
    asyncio.run(main())
