#!/usr/bin/env python3
"""
BLE Test Sender Script

This script sends test data to the Arduino via BLE to verify communication.
It uses the same protocol as the hand tracker but sends predefined test data.
"""

import asyncio
import time
from bleak import BleakScanner, BleakClient

# Hiwonder BLE Constants
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_MAC = None  # Will be discovered
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Test data sets
TEST_POSES = [
    {
        "name": "Open Hand",
        "angles": [0, 0, 0, 25, 0, 0],  # All fingers extended
        "description": "All servos at minimum angles (fingers extended)"
    },
    {
        "name": "Closed Fist",
        "angles": [82, 180, 180, 180, 180, 180],  # All fingers closed
        "description": "All servos at maximum angles (fingers closed)"
    },
    {
        "name": "Pointing",
        "angles": [0, 0, 180, 180, 180, 180],  # Index finger extended
        "description": "Only index finger extended"
    },
    {
        "name": "Peace Sign",
        "angles": [0, 0, 0, 180, 180, 180],  # Index and middle extended
        "description": "Index and middle fingers extended"
    },
    {
        "name": "Thumbs Up",
        "angles": [0, 180, 180, 180, 180, 180],  # Only thumb extended
        "description": "Only thumb extended"
    },
    {
        "name": "Mid Position",
        "angles": [41, 90, 90, 102, 90, 90],  # All at mid positions
        "description": "All servos at middle positions"
    }
]

async def scan_for_hiwonder():
    """Scan for Hiwonder BLE device"""
    print("🔍 Scanning for Hiwonder BLE device...")
    
    devices = await BleakScanner.discover(timeout=10)
    hiwonder_device = None
    
    print(f"Found {len(devices)} BLE devices:")
    for device in devices:
        rssi = getattr(device, 'rssi', 'N/A')
        print(f"  {device.name or 'Unknown'} ({device.address}) - RSSI: {rssi}")
        
        if device.name == HIWONDER_DEVICE_NAME:
            hiwonder_device = device
            print(f"✓ Found Hiwonder device: {device.address}")
    
    return hiwonder_device

def build_servo_packet(angles):
    """Build the servo control packet with checksum"""
    # Protocol: 0xAA 0x77 [Function] [Length] [Data...] [Checksum]
    packet = [0xAA, 0x77, 0x03, 0x06]  # Header + function + length
    packet.extend(angles)  # Add servo angles
    
    # Calculate checksum
    checksum = sum(packet) & 0xFF
    packet.append(checksum)
    
    return bytes(packet)

async def send_test_data(client, write_char):
    """Send all test poses to the Arduino"""
    print("\n🚀 Starting BLE test sequence...")
    print("Watch the Arduino's LED and serial output for feedback!")
    print("=" * 60)
    
    for i, pose in enumerate(TEST_POSES, 1):
        print(f"\n📤 Test {i}/{len(TEST_POSES)}: {pose['name']}")
        print(f"   Description: {pose['description']}")
        print(f"   Angles: {pose['angles']}")
        
        # Build and send packet
        packet = build_servo_packet(pose['angles'])
        print(f"   Packet: {' '.join(f'0x{b:02X}' for b in packet)}")
        
        try:
            await client.write_gatt_char(write_char, packet)
            print("   ✓ Sent successfully")
            
            # Wait between poses
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Send failed: {e}")
    
    print("\n🎉 Test sequence complete!")
    print("\nCheck the Arduino serial monitor for detailed feedback.")

async def main():
    """Main BLE test function"""
    print("=== BLE Test Sender ===")
    print("This script sends test data to the Arduino via BLE")
    print()
    
    # Scan for device
    device = await scan_for_hiwonder()
    if not device:
        print("❌ Hiwonder device not found!")
        print("\nTroubleshooting:")
        print("• Make sure the Hiwonder BLE module is powered on")
        print("• Check that the module is not connected to another device")
        print("• Try moving closer to the module")
        return
    
    print(f"\n🔗 Connecting to {device.address}...")
    
    try:
        async with BleakClient(device) as client:
            print("✓ Connected!")
            
            # Discover services
            services = client.services
            service_count = len(list(services))
            print(f"Found {service_count} services")
            
            # Find our service and characteristic
            target_service = None
            target_char = None
            
            for service in services:
                print(f"  Service: {service.uuid}")
                if service.uuid.lower() == HIWONDER_SERVICE_UUID.lower():
                    target_service = service
                    print("    ✓ Found target service!")
                    
                    for char in service.characteristics:
                        print(f"    Characteristic: {char.uuid}")
                        if char.uuid.lower() == HIWONDER_WRITE_CHAR_UUID.lower():
                            target_char = char
                            print("      ✓ Found write characteristic!")
                            break
                    break
            
            if not target_char:
                print("❌ Could not find write characteristic!")
                return
            
            # Send test data
            await send_test_data(client, target_char)
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\nTroubleshooting:")
        print("• Try restarting the BLE module")
        print("• Check if another device is connected to the module")
        print("• Make sure you're within range")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
