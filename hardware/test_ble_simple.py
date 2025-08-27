#!/usr/bin/env python3
"""
Simple BLE Test - Send single bytes to see if BLE transmission works at all
"""

import asyncio
from bleak import BleakScanner, BleakClient

# Hiwonder BLE Constants
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

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

async def test_simple_transmission():
    """Test simple BLE transmission"""
    print("=== Simple BLE Transmission Test ===")
    print("Sending simple test bytes to check basic BLE functionality")
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
            
            # Test with simple bytes
            test_bytes = [
                ([0xAA], "Start byte 1"),
                ([0x77], "Start byte 2"),
                ([0xAA, 0x77], "Both start bytes"),
                ([0x01, 0x02, 0x03], "Simple sequence"),
                ([0xFF, 0x00, 0x55], "Pattern bytes"),
            ]
            
            for test_data, description in test_bytes:
                print(f"\n📤 Sending: {description}")
                print(f"   Bytes: {' '.join(f'0x{b:02X}' for b in test_data)}")
                
                try:
                    await client.write_gatt_char(target_char, bytes(test_data))
                    print("   ✓ Sent successfully")
                    await asyncio.sleep(0.5)  # Wait between sends
                except Exception as e:
                    print(f"   ❌ Send failed: {e}")
            
            print(f"\n🔍 Check Arduino serial monitor to see what was received")
            print(f"📋 Look for patterns in the received bytes")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_simple_transmission())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
