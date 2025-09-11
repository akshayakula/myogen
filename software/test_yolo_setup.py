#!/usr/bin/env python3
"""
Test script to verify YOLO and webcam setup.
"""

import cv2
import sys

def test_opencv():
    """Test OpenCV installation."""
    print("Testing OpenCV...")
    try:
        print(f"OpenCV version: {cv2.__version__}")
        return True
    except Exception as e:
        print(f"❌ OpenCV error: {e}")
        return False

def test_webcam():
    """Test webcam access."""
    print("\nTesting webcam...")
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open webcam")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("❌ Could not read from webcam")
            cap.release()
            return False
        
        print(f"✅ Webcam working! Frame shape: {frame.shape}")
        cap.release()
        return True
    except Exception as e:
        print(f"❌ Webcam error: {e}")
        return False

def test_yolo():
    """Test YOLO installation."""
    print("\nTesting YOLO...")
    try:
        from ultralytics import YOLO
        print("✅ YOLO import successful")
        
        # Try to load a small model
        model = YOLO("yolov8n.pt")
        print("✅ YOLO model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ YOLO error: {e}")
        return False

def main():
    print("YOLO Webcam Setup Test")
    print("=" * 30)
    
    tests = [
        ("OpenCV", test_opencv),
        ("Webcam", test_webcam),
        ("YOLO", test_yolo)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 30)
    print("Test Results:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! You're ready to run YOLO webcam detection.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        print("\nTo install missing dependencies:")
        print("pip install ultralytics opencv-python")

if __name__ == "__main__":
    main()
