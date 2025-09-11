#!/usr/bin/env python3
"""
Demo script showing the new continuous servo angle input functionality.
This demonstrates how the BLE pose sender now accepts servo angle arrays.
"""

def demo_servo_input():
    """Demonstrate the servo angle input functionality"""
    print("🎯 Servo Angle Input Demo")
    print("=" * 60)
    print("The BLE pose sender now supports continuous servo angle input!")
    print()
    
    print("📋 Array Format: [thumb, index, middle, ring, pinky, wrist]")
    print("📊 Values: 0-180 degrees")
    print()
    
    examples = [
        {
            'name': 'Neutral Position',
            'angles': [90, 90, 90, 90, 90, 90],
            'description': 'All servos at middle position'
        },
        {
            'name': 'Open Hand',
            'angles': [0, 180, 180, 180, 180, 90],
            'description': 'All fingers extended'
        },
        {
            'name': 'Closed Fist',
            'angles': [180, 0, 0, 25, 0, 90],
            'description': 'All fingers closed (ring finger limited to 25°)'
        },
        {
            'name': 'Thumbs Up',
            'angles': [0, 0, 0, 25, 0, 90],
            'description': 'Only thumb extended'
        },
        {
            'name': 'Peace Sign',
            'angles': [180, 180, 180, 25, 0, 90],
            'description': 'Index and middle fingers extended'
        }
    ]
    
    print("🤖 Example Servo Angle Arrays:")
    print("-" * 60)
    
    for i, example in enumerate(examples, 1):
        angles_str = ','.join(map(str, example['angles']))
        print(f"{i}. {example['name']:<15} - {example['description']}")
        print(f"   Array: [{angles_str}]")
        print(f"   Command: python3 ble_pose_sender.py --angles {' '.join(map(str, example['angles']))}")
        print()
    
    print("🚀 How to Use the New Functionality:")
    print("-" * 60)
    print("1. Start LLM mode:")
    print("   python3 ble_pose_sender.py --llm")
    print()
    print("2. Press 's' to enter servo angles mode")
    print()
    print("3. Enter servo angles like: 90,90,90,90,90,90")
    print()
    print("4. Press Enter anytime to send the latest array to the hand")
    print()
    print("5. Keep entering new arrays and pressing Enter to send them!")
    print()
    
    print("💡 Key Features:")
    print("- ✅ Continuous input: Enter multiple arrays")
    print("- ✅ Enter key trigger: Send latest array anytime")
    print("- ✅ Direct servo control: No conversion needed")
    print("- ✅ Real-time feedback: See exactly what angles are sent")
    print("- ✅ Command line support: --angles for one-time sends")

def interactive_demo():
    """Interactive demo of the servo angle parsing"""
    print("\n" + "=" * 60)
    print("🎮 Interactive Servo Angle Demo")
    print("=" * 60)
    print("Try entering servo angle arrays to see how they're parsed!")
    print("Format: [90,90,90,90,90,90] or 90,90,90,90,90,90")
    print("Press Enter with empty input to exit.")
    print()
    
    while True:
        try:
            angles_input = input("🎯 Enter servo angles: ").strip()
            
            if not angles_input:
                print("👋 Exiting demo...")
                break
            
            # Parse the input - handle both [90,90,90,90,90,90] and 90,90,90,90,90,90 formats
            angles_input = angles_input.strip('[]')
            try:
                servo_angles = [int(x.strip()) for x in angles_input.split(',')]
            except ValueError:
                print("❌ Invalid format. Use comma-separated integers like: 90,90,90,90,90,90")
                continue
            
            if len(servo_angles) != 6:
                print(f"❌ Invalid number of elements: {len(servo_angles)}. Expected 6 [thumb, index, middle, ring, pinky, wrist]")
                continue
            
            # Validate values are 0-180
            if not all(0 <= val <= 180 for val in servo_angles):
                print("❌ Invalid values. All values must be 0-180 degrees")
                continue
            
            print(f"✅ Parsed servo angles: {servo_angles}")
            print(f"📋 Mapping: thumb={servo_angles[0]}°, index={servo_angles[1]}°, middle={servo_angles[2]}°, ring={servo_angles[3]}°, pinky={servo_angles[4]}°, wrist={servo_angles[5]}°")
            print(f"📤 Would send: python3 ble_pose_sender.py --angles {' '.join(map(str, servo_angles))}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Exiting demo...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main demo function"""
    print("🚀 BLE Pose Sender - Servo Angle Input Demo")
    print("=" * 50)
    
    demo_servo_input()
    
    response = input("\n🎮 Try interactive demo? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        interactive_demo()
    
    print("\n🎉 Demo completed!")
    print("Now you can use: python3 ble_pose_sender.py --llm")
    print("And press 's' to enter servo angles continuously!")

if __name__ == "__main__":
    main()
