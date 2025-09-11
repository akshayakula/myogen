#!/usr/bin/env python3
"""
Test script for curl array functionality.
Demonstrates the new curl array input format for the BLE pose sender.
"""

# Finger curl mappings for parsing input format
CURL_TO_ANGLE = {
    'thumb': {
        'no curl': 0,      # Extended (inverted at hardware level)
        'half curl': 90,   # Half closed
        'full curl': 180   # Fully closed
    },
    'index': {
        'no curl': 180,    # Extended (normal mapping)
        'half curl': 90,   # Half closed
        'full curl': 0     # Fully closed
    },
    'middle': {
        'no curl': 180,    # Extended (normal mapping)
        'half curl': 90,   # Half closed
        'full curl': 0     # Fully closed
    },
    'ring': {
        'no curl': 180,    # Extended (normal mapping, but min is 25°)
        'half curl': 100,  # Half closed
        'full curl': 25    # Fully closed (hardware minimum)
    },
    'pinky': {
        'no curl': 180,    # Extended (normal mapping)
        'half curl': 90,   # Half closed
        'full curl': 0     # Fully closed
    }
}

def parse_curl_array(curl_array):
    """
    Parse array of curl states and convert to servo angles.
    
    Expected format: ["pinky_curl", "ring_curl", "middle_curl", "index_curl", "thumb_curl"]
    Where each curl is: "no curl", "half curl", or "full curl"
    
    Returns: [thumb, index, middle, ring, pinky, wrist] angles
    """
    # Default wrist angle
    wrist_angle = 90
    
    # Finger names in the order they appear in the input array
    finger_names = ['pinky', 'ring', 'middle', 'index', 'thumb']
    
    # Validate input array length
    if len(curl_array) != 5:
        print(f"❌ Invalid curl array length: {len(curl_array)}. Expected 5 elements [pinky, ring, middle, index, thumb]")
        return [90, 90, 90, 90, 90, 90]  # Return neutral position
    
    try:
        finger_angles = {}
        
        # Process each finger curl
        for i, curl in enumerate(curl_array):
            finger = finger_names[i]
            curl = curl.strip().lower()
            
            if finger in CURL_TO_ANGLE and curl in CURL_TO_ANGLE[finger]:
                finger_angles[finger] = CURL_TO_ANGLE[finger][curl]
            else:
                print(f"⚠️ Invalid curl for {finger}: '{curl}'. Using neutral (90°)")
                finger_angles[finger] = 90
        
        # Build servo angles array in correct order: [thumb, index, middle, ring, pinky, wrist]
        servo_angles = [
            finger_angles.get('thumb', 90),
            finger_angles.get('index', 90),
            finger_angles.get('middle', 90),
            finger_angles.get('ring', 90),
            finger_angles.get('pinky', 90),
            wrist_angle
        ]
        
        return servo_angles
        
    except Exception as e:
        print(f"❌ Error parsing curl array: {e}")
        print(f"Expected format: ['pinky_curl', 'ring_curl', 'middle_curl', 'index_curl', 'thumb_curl']")
        print(f"Valid curls: 'no curl', 'half curl', 'full curl'")
        # Return neutral position on error
        return [90, 90, 90, 90, 90, 90]

def test_curl_arrays():
    """Test curl array parsing with various examples"""
    test_cases = [
        {
            'name': 'Open hand (all no curl)',
            'input': ['no curl', 'no curl', 'no curl', 'no curl', 'no curl']
        },
        {
            'name': 'Closed fist (all full curl)',
            'input': ['full curl', 'full curl', 'full curl', 'full curl', 'full curl']
        },
        {
            'name': 'Half closed (all half curl)',
            'input': ['half curl', 'half curl', 'half curl', 'half curl', 'half curl']
        },
        {
            'name': 'Mixed curls',
            'input': ['no curl', 'half curl', 'full curl', 'no curl', 'half curl']
        },
        {
            'name': 'Peace sign (pinky and ring closed, others open)',
            'input': ['full curl', 'full curl', 'no curl', 'no curl', 'full curl']
        },
        {
            'name': 'Thumbs up (all closed except thumb)',
            'input': ['full curl', 'full curl', 'full curl', 'full curl', 'no curl']
        }
    ]
    
    print("🤏 Curl Array Parsing Test")
    print("=" * 70)
    print("Format: [pinky, ring, middle, index, thumb] curl states")
    print("Output: [thumb, index, middle, ring, pinky, wrist] servo angles")
    print("=" * 70)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}:")
        print(f"   Input:  {test['input']}")
        print(f"   Order:  [pinky='{test['input'][0]}', ring='{test['input'][1]}', middle='{test['input'][2]}', index='{test['input'][3]}', thumb='{test['input'][4]}']")
        
        angles = parse_curl_array(test['input'])
        print(f"   Output: {angles}")
        print(f"   Detail: [thumb: {angles[0]}°, index: {angles[1]}°, middle: {angles[2]}°, ring: {angles[3]}°, pinky: {angles[4]}°, wrist: {angles[5]}°]")

def interactive_test():
    """Interactive mode for testing custom curl arrays"""
    print("\n" + "=" * 70)
    print("🎮 Interactive Curl Array Testing")
    print("=" * 70)
    print("Enter curl arrays to test parsing.")
    print("Format: comma-separated list of 5 curl states")
    print("Example: no curl, half curl, full curl, no curl, half curl")
    print("Press Enter with empty input to exit.")
    print("=" * 70)
    
    while True:
        try:
            user_input = input("\n🤏 Enter curl array: ").strip()
            
            if not user_input:
                print("👋 Exiting interactive mode...")
                break
            
            # Parse the input
            curl_array = [item.strip() for item in user_input.split(',')]
            
            if len(curl_array) != 5:
                print(f"❌ Invalid number of elements: {len(curl_array)}. Expected 5 [pinky, ring, middle, index, thumb]")
                continue
            
            angles = parse_curl_array(curl_array)
            print(f"✅ Parsed: {angles}")
            print(f"   Order: [pinky='{curl_array[0]}', ring='{curl_array[1]}', middle='{curl_array[2]}', index='{curl_array[3]}', thumb='{curl_array[4]}']")
            print(f"   Result: [thumb: {angles[0]}°, index: {angles[1]}°, middle: {angles[2]}°, ring: {angles[3]}°, pinky: {angles[4]}°, wrist: {angles[5]}°]")
            
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test curl array parsing for BLE pose sender")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run interactive testing mode")
    parser.add_argument("--test", "-t", nargs=5, metavar=('PINKY', 'RING', 'MIDDLE', 'INDEX', 'THUMB'), 
                       help="Test a specific curl array: --test 'no curl' 'half curl' 'full curl' 'no curl' 'half curl'")
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Testing specific curl array:")
        print(f"Input: {args.test}")
        print(f"Order: [pinky='{args.test[0]}', ring='{args.test[1]}', middle='{args.test[2]}', index='{args.test[3]}', thumb='{args.test[4]}']")
        angles = parse_curl_array(args.test)
        print(f"Output: {angles}")
        print(f"Detail: [thumb: {angles[0]}°, index: {angles[1]}°, middle: {angles[2]}°, ring: {angles[3]}°, pinky: {angles[4]}°, wrist: {angles[5]}°]")
    elif args.interactive:
        interactive_test()
    else:
        test_curl_arrays()
        
        response = input("\n🎮 Run interactive mode? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_test()

if __name__ == "__main__":
    main()

