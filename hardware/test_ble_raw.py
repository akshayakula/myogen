#!/usr/bin/env python3
"""
Raw BLE Test - Send the exact same packet format as the working wired version
"""

import asyncio
from bleak import BleakScanner, BleakClient

# Hiwonder BLE Constants
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

def build_test_packet():
    """Build the exact same packet format as the wired version"""
    # Protocol: 0xAA 0x77 [Function] [Length] [Data...] [Checksum]
    packet = bytearray()
    packet.append(0xAA)  # Start byte 1
    packet.append(0x77)  # Start byte 2
    packet.append(0x01)  # Function (servo control)
    packet.append(0x06)  # Length (6 servos)
    
    # Test servo angles: move all to 45 degrees (visible movement)
    servo_angles = [45, 45, 45, 45, 45, 45]
    packet.extend(servo_angles)
    
    # Calculate checksum (function + length + servo data)
    checksum_data = packet[2:]  # Skip start bytes
    checksum = 0
    for byte in checksum_data:
        checksum += byte
    checksum = ~checksum & 0xFF
    packet.append(checksum)
    
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

async def test_ble_transmission():
    """Test BLE transmission with known working packet"""
    print("=== BLE Raw Transmission Test ===")
    print("Sending exact same packet format as working wired version")
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
                    print("✓ Found target service!")
                    
                    for char in service.characteristics:
                        if char.uuid.lower() == HIWONDER_WRITE_CHAR_UUID.lower():
                            target_char = char
                            print("✓ Found write characteristic!")
                            break
                    break
            
            if not target_char:
                print("❌ Could not find write characteristic!")
                return
            
            # Build and send test packet
            packet = build_test_packet()
            
            print(f"\n📦 Sending packet:")
            print(f"   Raw bytes: {' '.join(f'0x{b:02X}' for b in packet)}")
            print(f"   Length: {len(packet)} bytes")
            print(f"   Expected: All servos move to 45°")
            print()
            
            # Send multiple times to ensure it gets through
            for i in range(3):
                print(f"📤 Attempt {i+1}/3...")
                try:
                    await client.write_gatt_char(target_char, packet)
                    print("   ✓ Sent successfully")
                    await asyncio.sleep(1)  # Wait between sends
                except Exception as e:
                    print(f"   ❌ Send failed: {e}")
            
            print("\n🔍 Check Arduino serial monitor for:")
            print("   • 'Servo angles updated' messages")
            print("   • No 'Invalid start bytes' errors")
            print("   • No 'Checksum error' messages")
            print("   • Actual servo movement to 45°")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_ble_transmission())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
