#!/usr/bin/env python3
"""
BLE Pose Sender for Robotic Hand
Sends preset hand poses to the robotic hand via BLE connection
Uses the proven BLE implementation from the hand tracker
"""

import asyncio
import time
import sys
import termios
import tty
from typing import Dict, List, Tuple
from bleak import BleakClient, BleakScanner

# Hiwonder BLE Constants (from working hand tracker)
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_MAC = "8EE2E4F9-42E6-5BE3-4E2A-A706CAD38879"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Official Hiwonder Protocol constants
FRAME_HEADER = 0x55
CMD_SERVO_MOVE = 0x03

# Global BLE connection variables
ble_client = None
ble_write_char = None
is_ble_connected = False

# Finger curl mappings for parsing input format
# Format: "pinky: <no curl|half curl|full curl>; ring: <no curl|half curl|full curl>; middle: <no curl|half curl|full curl>; index: <no curl|half curl|full curl>; thumb: <no curl|half curl|full curl>"
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

# Predefined hand poses (servo angles: [thumb, index, middle, ring, pinky, wrist])
# IMPORTANT: These angles account for Arduino's servo inversion logic:
# - Thumb (servo 0): Inverted at hardware level (0° = extended, 180° = closed)
# - Fingers (servos 1-4): Normal mapping (0° = closed, 180° = extended) 
# - Wrist (servo 5): Inverted at hardware level
# Ordered list for numeric selection
HAND_POSES = [
    {
        'name': 'neutral',
        'angles': [90, 90, 90, 90, 90, 90],
        'description': 'Neutral position - all servos at 90°'
    },
    {
        'name': 'open',
        'angles': [0, 180, 180, 180, 180, 90],
        'description': 'Open hand - fingers extended'
    },
    {
        'name': 'closed',
        'angles': [180, 0, 0, 25, 0, 90],
        'description': 'Closed fist - fingers closed (ring min is 25°)'
    },
    {
        'name': 'thumbs_up',
        'angles': [0, 0, 0, 25, 0, 90],
        'description': 'Thumbs up - only thumb extended'
    },
    {
        'name': 'peace',
        'angles': [180, 180, 180, 25, 0, 90],
        'description': 'Peace sign - index and middle fingers extended'
    },
    {
        'name': 'point',
        'angles': [180, 180, 0, 25, 0, 90],
        'description': 'Pointing - only index finger extended'
    },
    {
        'name': 'grasp',
        'angles': [120, 60, 60, 85, 60, 90],
        'description': 'Moderate grasp - partial finger closure'
    },
    {
        'name': 'rock_on',
        'angles': [0, 180, 0, 25, 180, 90],
        'description': 'Rock on sign - thumb, index, and pinky extended'
    },
    {
        'name': 'victory',
        'angles': [180, 180, 180, 25, 0, 90],
        'description': 'Victory/V sign - index and middle fingers extended'
    },
    {
        'name': 'fist',
        'angles': [180, 0, 0, 25, 0, 90],
        'description': 'Tight fist - maximum closure (respecting servo limits)'
    }
]

def parse_finger_curls(curl_string: str) -> List[int]:
    """
    Parse finger curl string and convert to servo angles.
    
    Expected format: "pinky: <no curl|half curl|full curl>; ring: <no curl|half curl|full curl>; middle: <no curl|half curl|full curl>; index: <no curl|half curl|full curl>; thumb: <no curl|half curl|full curl>"
    
    Returns: [thumb, index, middle, ring, pinky, wrist] angles
    """
    # Default wrist angle
    wrist_angle = 90
    
    # Initialize angles dictionary
    finger_angles = {}
    
    try:
        # Split by semicolon and parse each finger
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
        
        # Build servo angles array in correct order: [thumb, index, middle, ring, pinky, wrist]
        servo_angles = [
            finger_angles.get('thumb', 90),    # Default to 90 if not specified
            finger_angles.get('index', 90),
            finger_angles.get('middle', 90),
            finger_angles.get('ring', 90),
            finger_angles.get('pinky', 90),
            wrist_angle
        ]
        
        return servo_angles
        
    except Exception as e:
        print(f"❌ Error parsing finger curls: {e}")
        print(f"Expected format: 'pinky: no curl; ring: half curl; middle: full curl; index: no curl; thumb: half curl'")
        # Return neutral position on error
        return [90, 90, 90, 90, 90, 90]

def angle_to_position(angle: int) -> int:
    """Convert 0-180 angle to Hiwonder servo position (1100-1950)"""
    return int(1100 + (angle / 180.0) * (1950 - 1100))

def build_hiwonder_servo_packet(servo_angles: List[int], time_ms: int = 1000) -> bytearray:
    """Build servo control packet using official Hiwonder protocol"""
    packet = bytearray()
    
    # Frame header (2 bytes)
    packet.append(FRAME_HEADER)  # 0x55
    packet.append(FRAME_HEADER)  # 0x55
    
    # Calculate number of bytes (function + servo_count + time + servo_data)
    servo_count = len(servo_angles)
    data_bytes = 1 + 1 + 2 + (servo_count * 3)  # func + count + time + (id+pos_low+pos_high)*6
    packet.append(data_bytes)  # Number
    
    # Function
    packet.append(CMD_SERVO_MOVE)  # 0x03
    
    # Servo count
    packet.append(servo_count)  # 6 servos
    
    # Time (little endian)
    packet.append(time_ms & 0xFF)        # time_low
    packet.append((time_ms >> 8) & 0xFF) # time_high
    
    # Servo data
    for i, angle in enumerate(servo_angles):
        position = angle_to_position(angle)
        packet.append(i + 1)                    # Servo ID (1-6)
        packet.append(position & 0xFF)          # position_low
        packet.append((position >> 8) & 0xFF)   # position_high
    
    return packet

async def scan_for_hiwonder() -> bool:
    """Scan for Hiwonder BLE device"""
    print("🔍 Scanning for Hiwonder BLE device...")
    try:
        devices = await BleakScanner.discover(timeout=10.0)
        print(f"📱 Found {len(devices)} BLE devices")
        
        hiwonder_found = False
        for device in devices:
            is_hiwonder = (device.name == HIWONDER_DEVICE_NAME or 
                          device.address == HIWONDER_MAC or 
                          (device.name and "hiwonder" in device.name.lower()))
            
            if is_hiwonder:
                rssi = getattr(device, 'rssi', 'N/A')
                print(f"🎯 Found Hiwonder BLE device: {device.name} ({device.address}) RSSI: {rssi}dBm")
                hiwonder_found = True
                break
        
        if not hiwonder_found:
            print(f"❌ Hiwonder device not found in scan")
            print(f"💡 Scanned {len(devices)} devices")
        
        return hiwonder_found
        
    except Exception as e:
        print(f"❌ BLE scan failed: {e}")
        return False

async def connect_to_hiwonder_ble() -> bool:
    """Connect to Hiwonder BLE device using proven logic from hand tracker"""
    global ble_client, ble_write_char, is_ble_connected
    
    # First scan for the device
    print("🔗 Testing connection to Hiwonder BLE device...")
    device_found = await scan_for_hiwonder()
    if not device_found:
        return False
    
    try:
        # Try to connect using MAC address (same as hand tracker)
        print(f"📞 Attempting connection to {HIWONDER_MAC}...")
        ble_client = BleakClient(HIWONDER_MAC)
        await ble_client.connect()
        
        if ble_client.is_connected:
            print("🎉 SUCCESS! Connected to Hiwonder BLE device!")
            
            # List services (same as hand tracker)
            services = ble_client.services
            service_list = list(services)
            print(f"📋 Found {len(service_list)} services")
            
            target_service = None
            target_char = None
            
            for service in services:
                if service.uuid.lower() == HIWONDER_SERVICE_UUID.lower():
                    target_service = service
                    print(f"✅ Found target service: {service.uuid}")
                
                for char in service.characteristics:
                    if char.uuid.lower() == HIWONDER_WRITE_CHAR_UUID.lower():
                        target_char = char
                        print(f"✅ Found write characteristic: {char.uuid}")
                        break
            
            if target_service and target_char:
                ble_write_char = target_char  # Store the characteristic object
                is_ble_connected = True
                print("🤖 Ready for servo control!")
                return True
            else:
                print("❌ Required services/characteristics not found")
                await ble_client.disconnect()
                return False
        else:
            print("❌ Connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        if ble_client:
            try:
                await ble_client.disconnect()
            except:
                pass
        return False

def get_key():
    """Get a single keypress without Enter (Unix/macOS only)"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

async def send_pose(pose_name: str, angles: List[int]) -> bool:
    """Send a pose to the robotic hand via BLE"""
    global ble_client, ble_write_char, is_ble_connected
    
    if not is_ble_connected or not ble_client or not ble_client.is_connected:
        print("❌ Not connected to BLE device")
        return False
    
    try:
        # Build packet using official Hiwonder protocol
        packet = build_hiwonder_servo_packet(angles, time_ms=1000)
        
        # Send via BLE
        await ble_client.write_gatt_char(ble_write_char, packet, response=False)
        print(f"📤 Sent pose '{pose_name}': {angles}")
        return True
        
    except Exception as e:
        print(f"❌ BLE write failed: {e}")
        is_ble_connected = False
        return False

def print_available_poses():
    """Print all available poses"""
    print("\n📋 Available Hand Poses:")
    print("=" * 60)
    for i, pose in enumerate(HAND_POSES, 1):
        name = pose['name']
        angles = pose['angles']
        description = pose['description']
        print(f"{i:2d}. {name:<12} - {description}")
        print(f"    Angles: {angles}")
    print("=" * 60)

def print_status():
    """Print current connection status"""
    print("\n" + "=" * 60)
    print("           BLE POSE SENDER FOR ROBOTIC HAND")
    print("=" * 60)
    
    # Connection status
    if is_ble_connected and ble_client and ble_client.is_connected:
        print("📡 BLE Status: 🟢 CONNECTED")
    else:
        print("📡 BLE Status: 🔴 DISCONNECTED")
    
    print(f"📱 Device: {HIWONDER_DEVICE_NAME} ({HIWONDER_MAC})")
    print(f"🤖 Available Poses: {len(HAND_POSES)}")
    print("=" * 60)

def print_pose_menu():
    """Print the pose menu with clear screen"""
    print("\033[2J\033[H")  # Clear screen and move to top
    print("=" * 70)
    print("           🤖 BLE ROBOTIC HAND POSE CONTROLLER 🤖")
    print("=" * 70)
    
    # Connection status
    if is_ble_connected and ble_client and ble_client.is_connected:
        print("📡 BLE Status: 🟢 CONNECTED")
    else:
        print("📡 BLE Status: 🔴 DISCONNECTED")
    
    print(f"📱 Device: {HIWONDER_DEVICE_NAME}")
    print("=" * 70)
    print()
    
    # Pose options
    print("🎯 SELECT A POSE (Press number key):")
    print("=" * 40)
    
    # Display poses in two columns for better layout
    for i, pose in enumerate(HAND_POSES):
        name = pose['name']
        description = pose['description']
        print(f"  {i+1}. {name:<12} - {description}")
    
    print("=" * 40)
    print()
    print("⌨️  CONTROLS:")
    print("  1-9, 0  - Select pose by number")
    print("  'c'     - Enter finger curl mode")
    print("  'l'     - List poses again")
    print("  'd'     - Run demo mode")
    print("  'q'     - Quit")
    print()
    print("🎮 Press a key to select pose...")

async def interactive_curl_mode():
    """Interactive mode for entering finger curls"""
    print("\n" + "=" * 70)
    print("           🤏 FINGER CURL INPUT MODE 🤏")
    print("=" * 70)
    print()
    print("📝 Enter finger curls in this format:")
    print("   pinky: <no curl|half curl|full curl>; ring: <no curl|half curl|full curl>; middle: <no curl|half curl|full curl>; index: <no curl|half curl|full curl>; thumb: <no curl|half curl|full curl>")
    print()
    print("📋 Example:")
    print("   pinky: half curl; ring: full curl; middle: half curl; index: half curl; thumb: half curl")
    print()
    print("💡 Valid curl types: 'no curl', 'half curl', 'full curl'")
    print("💡 Press Enter with empty input to return to main menu")
    print("=" * 70)
    print()
    
    while True:
        try:
            curl_input = input("🤏 Enter finger curls: ").strip()
            
            if not curl_input:
                print("👋 Returning to main menu...")
                break
            
            # Test parsing first
            test_angles = parse_finger_curls(curl_input)
            print(f"🎯 Parsed angles: [thumb: {test_angles[0]}°, index: {test_angles[1]}°, middle: {test_angles[2]}°, ring: {test_angles[3]}°, pinky: {test_angles[4]}°, wrist: {test_angles[5]}°]")
            
            # Confirm before sending
            confirm = input("📤 Send this pose to the hand? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                success = await finger_curl_mode(curl_input)
                if success:
                    print("✅ Finger curls sent successfully!")
                else:
                    print("❌ Failed to send finger curls")
            else:
                print("❌ Cancelled")
            
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Returning to main menu...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def test_finger_curl_parsing():
    """Test function to verify finger curl parsing"""
    test_cases = [
        "pinky: half curl; ring: full curl; middle: half curl; index: half curl; thumb: half curl",
        "pinky: no curl; ring: no curl; middle: no curl; index: no curl; thumb: no curl",
        "pinky: full curl; ring: full curl; middle: full curl; index: full curl; thumb: full curl",
        "thumb: half curl; index: no curl; middle: full curl; ring: half curl; pinky: no curl"
    ]
    
    print("🧪 Testing finger curl parsing:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case}")
        angles = parse_finger_curls(test_case)
        print(f"Result: {angles}")
        print(f"[thumb: {angles[0]}°, index: {angles[1]}°, middle: {angles[2]}°, ring: {angles[3]}°, pinky: {angles[4]}°, wrist: {angles[5]}°]")

async def continuous_keyboard_mode():
    """Run continuous keyboard-driven pose selection"""
    current_pose_index = 0  # Track current pose for display
    
    while True:
        try:
            # Display menu
            print_pose_menu()
            
            # Get single keypress
            key = await asyncio.get_event_loop().run_in_executor(None, get_key)
            
            if key == 'q' or key == '\x03':  # 'q' or Ctrl+C
                print("\n👋 Exiting...")
                break
            elif key == 'l':
                # List poses (menu will refresh on next loop)
                continue
            elif key == 'c':
                # Finger curl mode
                await interactive_curl_mode()
                continue
            elif key == 'd':
                # Demo mode
                await demo_mode()
                input("\nPress Enter to return to pose menu...")
                continue
            elif key.isdigit():
                # Numeric selection
                num = int(key)
                
                # Handle 0 as 10
                if num == 0:
                    num = 10
                
                # Check if valid pose number
                if 1 <= num <= len(HAND_POSES):
                    pose_index = num - 1
                    pose = HAND_POSES[pose_index]
                    current_pose_index = pose_index
                    
                    print(f"\n🎯 Sending pose {num}: {pose['name']}")
                    print(f"   Description: {pose['description']}")
                    print(f"   Angles: {pose['angles']}")
                    
                    success = await send_pose(pose['name'], pose['angles'])
                    if success:
                        print(f"✅ Pose '{pose['name']}' sent successfully!")
                    else:
                        print(f"❌ Failed to send pose '{pose['name']}'")
                    
                    # Brief pause to show result
                    await asyncio.sleep(1)
                else:
                    print(f"\n❌ Invalid pose number: {num}")
                    print(f"   Valid range: 1-{len(HAND_POSES)}")
                    await asyncio.sleep(1)
            else:
                # Invalid key
                print(f"\n⚠️  Invalid key: '{key}'")
                print("   Use number keys (1-9, 0) or 'l', 'd', 'q'")
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await asyncio.sleep(1)

async def demo_mode():
    """Run demo mode - cycle through all poses"""
    print("\n🎪 Demo Mode - Cycling through all poses...")
    print("Press Ctrl+C to stop demo")
    
    try:
        for i, pose in enumerate(HAND_POSES, 1):
            pose_name = pose['name']
            pose_angles = pose['angles']
            pose_description = pose['description']
            
            print(f"\n📤 Demo {i}/{len(HAND_POSES)}: {pose_name}")
            print(f"   Description: {pose_description}")
            print(f"   Angles: {pose_angles}")
            
            success = await send_pose(pose_name, pose_angles)
            if success:
                print(f"✅ Sent successfully!")
            else:
                print(f"❌ Failed to send")
                break
            
            # Wait between poses
            await asyncio.sleep(2)
        
        print("\n🎉 Demo completed!")
        
        # Return to neutral
        print("\n🔄 Returning to neutral position...")
        neutral_pose = HAND_POSES[0]  # First pose is neutral
        await send_pose(neutral_pose['name'], neutral_pose['angles'])
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo stopped by user")
        # Return to neutral on interrupt
        print("🔄 Returning to neutral position...")
        neutral_pose = HAND_POSES[0]  # First pose is neutral
        await send_pose(neutral_pose['name'], neutral_pose['angles'])

async def finger_curl_mode(curl_string: str):
    """Send finger curls from parsed string"""
    print(f"🤏 Parsing finger curl input: {curl_string}")
    
    # Parse the finger curl string
    servo_angles = parse_finger_curls(curl_string)
    
    print(f"🎯 Converted to servo angles: {servo_angles}")
    print(f"   [thumb: {servo_angles[0]}°, index: {servo_angles[1]}°, middle: {servo_angles[2]}°, ring: {servo_angles[3]}°, pinky: {servo_angles[4]}°, wrist: {servo_angles[5]}°]")
    
    success = await send_pose("finger_curls", servo_angles)
    if success:
        print(f"✅ Finger curls sent successfully!")
        return True
    else:
        print(f"❌ Failed to send finger curls")
        return False

async def single_pose_mode(pose_name: str):
    """Send a single pose and exit"""
    # Find pose by name
    pose = None
    for p in HAND_POSES:
        if p['name'] == pose_name:
            pose = p
            break
    
    if pose is None:
        print(f"❌ Unknown pose: '{pose_name}'")
        available_poses = [p['name'] for p in HAND_POSES]
        print("Available poses:", ', '.join(available_poses))
        return False
    
    print(f"🎯 Sending pose: {pose_name}")
    print(f"   Description: {pose['description']}")
    print(f"   Angles: {pose['angles']}")
    
    success = await send_pose(pose_name, pose['angles'])
    if success:
        print(f"✅ Pose '{pose_name}' sent successfully!")
        return True
    else:
        print(f"❌ Failed to send pose '{pose_name}'")
        return False

async def cleanup():
    """Cleanup BLE connection"""
    global ble_client, is_ble_connected
    
    if is_ble_connected and ble_client and ble_client.is_connected:
        try:
            # Return to neutral position before disconnecting
            print("🔄 Returning to neutral position...")
            neutral_pose = HAND_POSES[0]  # First pose is neutral
            await send_pose(neutral_pose['name'], neutral_pose['angles'])
            await asyncio.sleep(0.5)
            
            # Disconnect
            await ble_client.disconnect()
            print("📶 Disconnected from BLE device")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
        finally:
            is_ble_connected = False

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BLE Pose Sender for Robotic Hand")
    parser.add_argument("--pose", "-p", help="Send specific pose and exit")
    parser.add_argument("--curls", "-c", help="Send finger curls in format: 'pinky: no curl; ring: half curl; middle: full curl; index: no curl; thumb: half curl'")
    parser.add_argument("--demo", "-d", action="store_true", help="Run demo mode")
    parser.add_argument("--list", "-l", action="store_true", help="List available poses and exit")
    parser.add_argument("--test", "-t", action="store_true", help="Test finger curl parsing without BLE connection")
    
    args = parser.parse_args()
    
    # Handle list command
    if args.list:
        print_available_poses()
        return
    
    # Handle test command
    if args.test:
        test_finger_curl_parsing()
        return
    
    print("🚀 BLE Pose Sender for Robotic Hand")
    print_status()
    
    # Connect to BLE device
    print("\n🔗 Connecting to Hiwonder BLE device...")
    if not await connect_to_hiwonder_ble():
        print("❌ Failed to connect to BLE device!")
        print("💡 Make sure the Hiwonder device is powered on and nearby")
        return
    
    try:
        if args.pose:
            # Single pose mode
            await single_pose_mode(args.pose)
        elif args.curls:
            # Finger curl mode
            await finger_curl_mode(args.curls)
        elif args.demo:
            # Demo mode
            await demo_mode()
        else:
            # Continuous keyboard mode (default)
            await continuous_keyboard_mode()
    
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    
    finally:
        await cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Program interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
