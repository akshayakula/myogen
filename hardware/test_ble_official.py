#!/usr/bin/env python3
"""
Official Hiwonder BLE Protocol Test

Uses the correct protocol format from the official Hiwonder code:
0x55 0x55 [Number] [Function] [...Data...]
"""

import asyncio
from bleak import BleakScanner, BleakClient

# Hiwonder BLE Constants
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Official Protocol Constants
FRAME_HEADER = 0x55
CMD_SERVO_MOVE = 0x03

def angle_to_position(angle):
    """Convert 0-180 angle to Hiwonder servo position (1100-1950)"""
    # Map 0-180 to 1100-1950
    return int(1100 + (angle / 180.0) * (1950 - 1100))

def build_official_servo_packet(servo_angles, time_ms=1000):
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

async def scan_for_hiwonder():
    """Scan for Hiwonder BLE device"""
    print("🔍 Scanning for Hiwonder BLE device...")
    
    devices = await BleakScanner.discover(timeout=10)
    
    for device in devices:
        if device.name == HIWONDER_DEVICE_NAME:
            print(f"✓ Found Hiwonder device: {device.address}")
            return device
    
    print("❌ Hiwonder device not found!")
    return None

async def test_official_protocol():
    """Test with official Hiwonder protocol"""
    print("=== Official Hiwonder BLE Protocol Test ===")
    print("Using the correct protocol format from official code")
    print()
    
    # Scan for device
    device = await scan_for_hiwonder()
    if not device:
        return
    
    print(f"\n🔗 Connecting to {device.address}...")
    
    try:
        async with BleakClient(device) as client:
            print("✓ Connected!")
            
            # Find our service and characteristic
            services = client.services
            target_char = None
            
            for service in services:
                if service.uuid.lower() == HIWONDER_SERVICE_UUID.lower():
                    for char in service.characteristics:
                        if char.uuid.lower() == HIWONDER_WRITE_CHAR_UUID.lower():
                            target_char = char
                            break
                    break
            
            if not target_char:
                print("❌ Could not find write characteristic!")
                return
            
            # Test poses
            test_poses = [
                ([90, 90, 90, 90, 90, 90], "Neutral position"),
                ([0, 0, 0, 25, 0, 0], "Open hand"),
                ([82, 180, 180, 180, 180, 180], "Closed fist"),
                ([0, 0, 180, 180, 180, 180], "Pointing"),
            ]
            
            for angles, description in test_poses:
                print(f"\n📤 Testing: {description}")
                print(f"   Angles: {angles}")
                
                # Build packet with official protocol
                packet = build_official_servo_packet(angles, time_ms=1000)
                
                print(f"   Packet: {' '.join(f'0x{b:02X}' for b in packet)}")
                print(f"   Length: {len(packet)} bytes")
                
                try:
                    await client.write_gatt_char(target_char, packet)
                    print("   ✓ Sent successfully")
                    await asyncio.sleep(2)  # Wait to see movement
                except Exception as e:
                    print(f"   ❌ Send failed: {e}")
            
            print(f"\n🎉 Official protocol test complete!")
            print(f"📋 Check if servos moved correctly with each pose")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_official_protocol())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
