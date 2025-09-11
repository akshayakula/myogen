#!/usr/bin/env python3
"""
Test script for finger curl parsing functionality.
Demonstrates the new finger curl input format for the BLE pose sender.
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

def parse_finger_curls(curl_string):
    """
    Parse finger curl string and convert to servo angles.
    
    Expected format: "pinky: <no curl|half curl|full curl>; ring: <no curl|half curl|full curl>; middle: <no curl|half curl|full curl>; index: <no curl|half curl|full curl>; thumb: <no curl|half curl|full curl>"
    
    Returns: [thumb, index, middle, ring, pinky, wrist] angles
    """
    wrist_angle = 90
    finger_angles = {}
    
    try:
        parts = curl_string.split(';')
        
        for part in parts:
            part = part.strip()
            if ':' in part:
                finger, curl = part.split(':', 1)
                finger = finger.strip().lower()
                curl = curl.strip().lower()
                
                if finger in CURL_TO_ANGLE and curl in CURL_TO_ANGLE[finger]:
                    finger_angles[finger] = CURL_TO_ANGLE[finger][curl]
                else:
                    print(f"⚠️ Invalid finger/curl: {finger}: {curl}")
        
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
        print(f"❌ Error parsing finger curls: {e}")
        return [90, 90, 90, 90, 90, 90]

def test_parsing():
    """Test finger curl parsing with various examples"""
    test_cases = [
        {
            'name': 'Example from specification',
            'input': 'pinky: half curl; ring: full curl; middle: half curl; index: half curl; thumb: half curl'
        },
        {
            'name': 'Open hand (no curls)',
            'input': 'pinky: no curl; ring: no curl; middle: no curl; index: no curl; thumb: no curl'
        },
        {
            'name': 'Closed fist (full curls)',
            'input': 'pinky: full curl; ring: full curl; middle: full curl; index: full curl; thumb: full curl'
        },
        {
            'name': 'Mixed curls',
            'input': 'thumb: half curl; index: no curl; middle: full curl; ring: half curl; pinky: no curl'
        },
        {
            'name': 'Peace sign (index and middle extended)',
            'input': 'pinky: full curl; ring: full curl; middle: no curl; index: no curl; thumb: full curl'
        }
    ]
    
    print("🤏 Finger Curl Parsing Test")
    print("=" * 70)
    print("Format: 'pinky: <no curl|half curl|full curl>; ring: <...>; middle: <...>; index: <...>; thumb: <...>'")
    print("Output: [thumb, index, middle, ring, pinky, wrist] servo angles")
    print("=" * 70)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}:")
        print(f"   Input:  {test['input']}")
        
        angles = parse_finger_curls(test['input'])
        print(f"   Output: {angles}")
        print(f"   Detail: [thumb: {angles[0]}°, index: {angles[1]}°, middle: {angles[2]}°, ring: {angles[3]}°, pinky: {angles[4]}°, wrist: {angles[5]}°]")

def interactive_test():
    """Interactive mode for testing custom inputs"""
    print("\n" + "=" * 70)
    print("🎮 Interactive Finger Curl Testing")
    print("=" * 70)
    print("Enter finger curl strings to test parsing.")
    print("Press Enter with empty input to exit.")
    print("=" * 70)
    
    while True:
        try:
            user_input = input("\n🤏 Enter finger curls: ").strip()
            
            if not user_input:
                print("👋 Exiting interactive mode...")
                break
            
            angles = parse_finger_curls(user_input)
            print(f"✅ Parsed: {angles}")
            print(f"   [thumb: {angles[0]}°, index: {angles[1]}°, middle: {angles[2]}°, ring: {angles[3]}°, pinky: {angles[4]}°, wrist: {angles[5]}°]")
            
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test finger curl parsing for BLE pose sender")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run interactive testing mode")
    parser.add_argument("--test", "-t", help="Test a specific finger curl string")
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Testing specific input:")
        print(f"Input: {args.test}")
        angles = parse_finger_curls(args.test)
        print(f"Output: {angles}")
        print(f"Detail: [thumb: {angles[0]}°, index: {angles[1]}°, middle: {angles[2]}°, ring: {angles[3]}°, pinky: {angles[4]}°, wrist: {angles[5]}°]")
    elif args.interactive:
        interactive_test()
    else:
        test_parsing()
        
        response = input("\n🎮 Run interactive mode? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_test()

if __name__ == "__main__":
    main()
