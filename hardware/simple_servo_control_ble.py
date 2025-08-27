#!/usr/bin/env python3
"""
Simple Servo Control Script - BLE Version
Control individual servos with arrow keys and number keys via BLE
Arrow keys: Up/Down to change angle
Number keys: 1-6 to select servo
ESC to quit
"""

import asyncio
import struct
import sys
import termios
import tty
import time
from bleak import BleakClient, BleakScanner

# BLE constants
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Hiwonder protocol constants
FRAME_HEADER = 0x55
CMD_SERVO_MOVE = 0x03

# Current state
current_servo = 0  # 0-5 (servo 1-6)
servo_angles = [90, 90, 90, 90, 90, 90]  # Default angles
ble_client = None
ble_write_char = None

# Servo limits (0-180° for all servos in BLE mode)
servo_limits = [(0, 180), (0, 180), (0, 180), (25, 180), (0, 180), (0, 180)]
servo_names = ["Thumb", "Index", "Middle", "Ring", "Pinky", "Wrist"]

def angle_to_position(angle):
    """Convert 0-180° angle to Hiwonder's 1100-1950 position range"""
    return int(1100 + (angle / 180.0) * (1950 - 1100))

def build_hiwonder_servo_packet(servo_angles, time_ms=1000):
    """Build servo control packet using official Hiwonder protocol"""
    servo_count = 6
    
    packet = bytearray()
    packet.append(FRAME_HEADER)  # 0x55
    packet.append(FRAME_HEADER)  # 0x55
    packet.append(servo_count + 3)  # Number (length of remaining packet)
    packet.append(CMD_SERVO_MOVE)  # Function
    packet.append(servo_count)  # Number of servos
    
    # Time (2 bytes, little endian)
    packet.append(time_ms & 0xFF)        # time_low
    packet.append((time_ms >> 8) & 0xFF) # time_high
    
    # Servo data (3 bytes per servo: ID, pos_low, pos_high)
    for i, angle in enumerate(servo_angles):
        servo_id = i + 1  # Servo IDs are 1-based
        position = angle_to_position(angle)
        
        packet.append(servo_id)
        packet.append(position & 0xFF)        # pos_low
        packet.append((position >> 8) & 0xFF) # pos_high
    
    return packet

async def find_hiwonder_device():
    """Scan for Hiwonder BLE device using working logic from hand tracker"""
    print("🔍 Scanning for Hiwonder BLE device...")
    
    try:
        devices = await BleakScanner.discover(timeout=10.0)
        print(f"📱 Found {len(devices)} BLE devices")
        
        # Look for Hiwonder device (same logic as hand tracker)
        hiwonder_found = False
        device_address = None
        
        for device in devices:
            is_hiwonder = (device.name == "Hiwonder" or 
                          (device.name and "hiwonder" in device.name.lower()))
            
            if is_hiwonder:
                rssi = getattr(device, 'rssi', 'N/A')
                print(f"🎯 Found Hiwonder BLE device: {device.name} ({device.address}) RSSI: {rssi}dBm")
                device_address = device.address
                hiwonder_found = True
                break
        
        if not hiwonder_found:
            print("❌ Hiwonder device not found")
            print("💡 Make sure the Hiwonder BLE device is powered on and nearby")
        
        return device_address
        
    except Exception as e:
        print(f"❌ BLE scan failed: {e}")
        return None

async def connect_ble():
    """Connect to Hiwonder BLE device using exact working logic from hand tracker"""
    global ble_client, ble_write_char
    
    device_address = await find_hiwonder_device()
    if not device_address:
        return False
    
    try:
        print(f"📞 Attempting connection to {device_address}...")
        ble_client = BleakClient(device_address)
        await ble_client.connect()
        
        if ble_client.is_connected:
            print("🎉 SUCCESS! Connected to Hiwonder BLE device!")
            
            # Verify services (exact same as hand tracker)
            services = ble_client.services
            service_list = list(services)
            print(f"📋 Found {len(service_list)} services")
            
            target_service = None
            target_char = None
            
            # Find service and characteristic (exact same logic as hand tracker)
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
        print(f"❌ BLE connection error: {e}")
        if ble_client:
            try:
                await ble_client.disconnect()
            except:
                pass
        return False

async def send_servo_command():
    """Send servo command via BLE using exact working logic from hand tracker"""
    global ble_client, ble_write_char
    
    if not ble_client or not ble_client.is_connected or not ble_write_char:
        return False
    
    try:
        # Build packet using official Hiwonder protocol (same as hand tracker)
        packet = build_hiwonder_servo_packet(servo_angles, time_ms=1000)
        
        # Send via BLE using characteristic object (same method as hand tracker)
        await ble_client.write_gatt_char(ble_write_char, packet, response=False)
        return True
        
    except Exception as e:
        print(f"❌ BLE write failed: {e}")
        return False

def get_key():
    """Get a single keypress without Enter"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1)
        
        # Handle escape sequences (arrow keys)
        if ch == '\x1b':  # ESC sequence
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                return f'\x1b[{ch3}'
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def print_status():
    """Print current status"""
    print("\033[2J\033[H")  # Clear screen and move to top
    print("=" * 60)
    print("       SIMPLE SERVO CONTROL - BLE VERSION")
    print("=" * 60)
    print()
    
    # Show connection status
    if ble_client and ble_client.is_connected:
        print("📡 BLE Status: 🟢 CONNECTED")
    else:
        print("📡 BLE Status: 🔴 DISCONNECTED")
    print()
    
    # Show all servo angles
    for i in range(6):
        min_angle, max_angle = servo_limits[i]
        if i == current_servo:
            marker = ">>> "
            color = "\033[92m"  # Green
            reset = "\033[0m"
        else:
            marker = "    "
            color = ""
            reset = ""
        
        # Show angle bar
        bar_width = 30
        angle_ratio = (servo_angles[i] - min_angle) / (max_angle - min_angle)
        filled_width = int(angle_ratio * bar_width)
        bar = "█" * filled_width + "░" * (bar_width - filled_width)
        
        # Show position value for debugging
        position = angle_to_position(servo_angles[i])
        print(f"{marker}{color}Servo {i+1} ({servo_names[i]:>6}): {servo_angles[i]:3d}° [{bar}] ({min_angle}-{max_angle}°) pos={position}{reset}")
    
    print()
    print("Controls:")
    print("  ↑ / ↓     - Increase/Decrease angle")
    print("  1-6       - Select servo")
    print("  ESC       - Quit")
    print()
    print(f"Currently controlling: Servo {current_servo + 1} ({servo_names[current_servo]})")

async def main():
    global current_servo, servo_angles, ble_client
    
    print("Simple Servo Control (BLE) Starting...")
    
    # Connect to BLE device
    if not await connect_ble():
        print("❌ Failed to connect to BLE device!")
        return
    
    # Send initial position (all servos to default)
    await send_servo_command()
    print(f"✅ Sent initial positions: {servo_angles}")
    
    print("🎮 Starting control interface...")
    await asyncio.sleep(1)
    
    try:
        while True:
            print_status()
            
            # Get key input (blocking)
            key = await asyncio.get_event_loop().run_in_executor(None, get_key)
            
            if key == '\x1b':  # ESC key
                print("\n👋 Exiting...")
                break
            elif key == '\x1b[A':  # Up arrow
                min_angle, max_angle = servo_limits[current_servo]
                if servo_angles[current_servo] < max_angle:
                    servo_angles[current_servo] += 5
                    if servo_angles[current_servo] > max_angle:
                        servo_angles[current_servo] = max_angle
                    await send_servo_command()
                    print(f"📤 Sent: Servo {current_servo+1} = {servo_angles[current_servo]}°")
            elif key == '\x1b[B':  # Down arrow
                min_angle, max_angle = servo_limits[current_servo]
                if servo_angles[current_servo] > min_angle:
                    servo_angles[current_servo] -= 5
                    if servo_angles[current_servo] < min_angle:
                        servo_angles[current_servo] = min_angle
                    await send_servo_command()
                    print(f"📤 Sent: Servo {current_servo+1} = {servo_angles[current_servo]}°")
            elif key in '123456':  # Number keys
                servo_num = int(key) - 1
                if 0 <= servo_num < 6:
                    current_servo = servo_num
            elif key == 'q':  # Alternative quit
                print("\n👋 Exiting...")
                break
            
            await asyncio.sleep(0.05)  # Small delay
            
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    
    finally:
        if ble_client and ble_client.is_connected:
            # Return all servos to neutral before closing
            for i in range(6):
                servo_angles[i] = 90
            await send_servo_command()
            print("🔄 Reset all servos to 90°")
            await asyncio.sleep(0.5)
            
            await ble_client.disconnect()
            print("🔌 Disconnected from BLE device")

if __name__ == "__main__":
    asyncio.run(main())
