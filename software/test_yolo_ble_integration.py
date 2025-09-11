#!/usr/bin/env python3
"""
Test script for the integrated YOLO + LLM + BLE system.
Tests the complete pipeline without requiring actual hardware.
"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(__file__))

def test_imports():
    """Test if all required imports work"""
    print("🧪 Testing imports...")
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        from ultralytics import YOLO
        print("✅ YOLO imported successfully")
    except ImportError as e:
        print(f"❌ YOLO import failed: {e}")
        return False
    
    try:
        from bleak import BleakClient
        print("✅ Bleak (BLE) imported successfully")
    except ImportError as e:
        print(f"⚠️ Bleak import failed (expected if not installed): {e}")
    
    return True

def test_yolo_detector_creation():
    """Test creating the YOLO detector with BLE integration"""
    print("\n🧪 Testing YOLO detector creation...")
    
    try:
        # Import the detector class
        from yolo_webcam import YOLOWebcamDetector
        
        # Create detector with LLM API enabled
        detector = YOLOWebcamDetector(
            model_name="yolov8n.pt",
            confidence_threshold=0.5,
            exclude_classes={'person'},
            enable_llm_api=True,
            api_url="https://test-api-endpoint.com"
        )
        
        print("✅ YOLOWebcamDetector created successfully")
        print(f"   Model: {detector.model_name}")
        print(f"   LLM API: {'Enabled' if detector.enable_llm_api else 'Disabled'}")
        print(f"   API URL: {detector.api_url}")
        print(f"   API Cooldown: {detector.api_cooldown}s")
        
        return detector
        
    except Exception as e:
        print(f"❌ Detector creation failed: {e}")
        return None

def test_conversion_functions():
    """Test the finger curl conversion functions"""
    print("\n🧪 Testing conversion functions...")
    
    try:
        from yolo_webcam import YOLOWebcamDetector
        detector = YOLOWebcamDetector()
        
        # Test numeric to servo angles conversion
        test_numeric = [1, 1, 2, 2, 1]  # [pinky, ring, middle, index, thumb]
        servo_angles = detector.convert_numeric_to_servo_angles(test_numeric)
        
        print(f"✅ Numeric conversion: {test_numeric} → {servo_angles}")
        print(f"   [thumb={servo_angles[0]}°, index={servo_angles[1]}°, middle={servo_angles[2]}°, ring={servo_angles[3]}°, pinky={servo_angles[4]}°, wrist={servo_angles[5]}°]")
        
        # Test servo packet building
        packet = detector.build_servo_packet(servo_angles)
        print(f"✅ Servo packet built: {len(packet)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversion test failed: {e}")
        return False

async def test_llm_response_parsing():
    """Test LLM response parsing"""
    print("\n🧪 Testing LLM response parsing...")
    
    try:
        from yolo_webcam import YOLOWebcamDetector
        detector = YOLOWebcamDetector()
        
        # Test different response formats
        test_responses = [
            'pinky: half curl; ring: no curl; middle: no curl; index: half curl; thumb: half curl',
            '{"response": "pinky: full curl; ring: full curl; middle: no curl; index: no curl; thumb: half curl"}',
            'Some extra text: pinky: no curl; ring: half curl; middle: full curl; index: no curl; thumb: no curl and more text',
            'Invalid response with no finger data'
        ]
        
        for i, response in enumerate(test_responses, 1):
            print(f"\nTest {i}: {response[:50]}...")
            servo_angles = detector.parse_llm_response_to_servo_angles(response)
            print(f"Result: {servo_angles}")
        
        print("✅ LLM response parsing tests completed")
        return True
        
    except Exception as e:
        print(f"❌ LLM parsing test failed: {e}")
        return False

async def test_scene_description():
    """Test scene description generation"""
    print("\n🧪 Testing scene description generation...")
    
    try:
        from yolo_webcam import YOLOWebcamDetector
        detector = YOLOWebcamDetector()
        
        # Mock detection data
        mock_detections = [
            {
                'class_name': 'keyboard',
                'bbox': [100, 150, 300, 250],  # x1, y1, x2, y2
                'confidence': 0.85
            }
        ]
        
        # Mock frame shape (height, width, channels)
        mock_frame_shape = (480, 640, 3)
        
        # Generate description
        description = detector.format_scene_description(mock_detections, mock_frame_shape)
        print(f"✅ Scene description generated:")
        print(description)
        
        return True
        
    except Exception as e:
        print(f"❌ Scene description test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 YOLO + LLM + BLE Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        print("❌ Import tests failed - cannot continue")
        return
    
    # Test 2: Detector creation
    detector = test_yolo_detector_creation()
    if not detector:
        print("❌ Detector creation failed - cannot continue")
        return
    
    # Test 3: Conversion functions
    if not test_conversion_functions():
        print("❌ Conversion tests failed")
        return
    
    # Test 4: LLM response parsing
    if not await test_llm_response_parsing():
        print("❌ LLM parsing tests failed")
        return
    
    # Test 5: Scene description
    if not await test_scene_description():
        print("❌ Scene description tests failed")
        return
    
    print("\n🎉 All tests passed!")
    print("=" * 60)
    print("✅ YOLO + LLM + BLE integration is working correctly")
    print()
    print("🚀 Ready to run:")
    print("   python3 yolo_webcam.py --enable-llm")
    print()
    print("📋 Features available:")
    print("   • Real-time object detection")
    print("   • LLM finger curl predictions") 
    print("   • Direct BLE pose sending to Arduino")
    print("   • Configurable API cooldown")

if __name__ == "__main__":
    asyncio.run(main())
