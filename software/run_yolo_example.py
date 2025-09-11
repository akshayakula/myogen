#!/usr/bin/env python3
"""
Example script showing how to use the YOLO webcam detector.
"""

import subprocess
import sys
import os

def run_yolo_webcam():
    """Run the YOLO webcam detector with example parameters."""
    
    print("YOLO Continuous Scene Description Generator")
    print("=" * 50)
    print("This will:")
    print("• Run continuous real-time object detection")
    print("• Use mathematical analysis for size, position, and orientation")
    print("• Output scene descriptions in console continuously")
    print("• Show live video with detection boxes and frame counter")
    print("\nControls:")
    print("• Press 'q' to quit")
    print("• Press 's' to manually save current frame")
    print("=" * 50)
    
    # Check if yolo_webcam.py exists
    if not os.path.exists("yolo_webcam.py"):
        print("❌ yolo_webcam.py not found!")
        return
    
    # Example command with different options
    examples = [
        {
            "name": "Basic continuous detection",
            "command": ["python", "yolo_webcam.py"]
        },
        {
            "name": "Higher confidence threshold (0.7)",
            "command": ["python", "yolo_webcam.py", "--confidence", "0.7"]
        },
        {
            "name": "Save images and output to file",
            "command": ["python", "yolo_webcam.py", "--save-images", "--output", "scene_descriptions.txt"]
        },
        {
            "name": "Different YOLO model (more accurate)",
            "command": ["python", "yolo_webcam.py", "--model", "yolov8s.pt"]
        }
    ]
    
    print("\nAvailable examples:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['name']}")
    
    try:
        choice = input("\nSelect example (1-4) or press Enter for basic: ").strip()
        
        if choice == "1" or choice == "":
            cmd = examples[0]["command"]
        elif choice == "2":
            cmd = examples[1]["command"]
        elif choice == "3":
            cmd = examples[2]["command"]
        elif choice == "4":
            cmd = examples[3]["command"]
        else:
            print("Invalid choice, using basic example")
            cmd = examples[0]["command"]
        
        print(f"\nRunning: {' '.join(cmd)}")
        print("Starting in 3 seconds...")
        
        # Run the command
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_help():
    """Show help information."""
    print("YOLO Webcam Scene Description Generator")
    print("=" * 50)
    print("\nUsage:")
    print("python yolo_webcam.py [options]")
    print("\nOptions:")
    print("  --model MODEL        YOLO model (default: yolov8n.pt)")
    print("  --camera INDEX       Camera index (default: 0)")
    print("  --interval SECONDS   Detection interval (default: 5)")
    print("  --confidence FLOAT   Confidence threshold (default: 0.5)")
    print("  --save-images        Save detected frames as images")
    print("  --output FILE        Save scene descriptions to file")
    print("\nExamples:")
    print("  python yolo_webcam.py")
    print("  python yolo_webcam.py --interval 2 --save-images")
    print("  python yolo_webcam.py --confidence 0.7 --output scenes.txt")

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        show_help()
    else:
        run_yolo_webcam()

if __name__ == "__main__":
    main()
