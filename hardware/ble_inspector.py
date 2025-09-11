#!/usr/bin/env python3
"""
BLE Inspector - Debug BLE characteristics on Hiwonder device
"""

import asyncio
from bleak import BleakClient, BleakScanner

# Hiwonder BLE Constants
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_MAC = "8EE2E4F9-42E6-5BE3-4E2A-A706CAD38879"

async def inspect_ble_device():
    """Connect and inspect BLE device characteristics"""
    
    print("🔍 Scanning for Hiwonder BLE device...")
    devices = await BleakScanner.discover(timeout=10.0)
    
    target_device = None
    for device in devices:
        if (device.name == HIWONDER_DEVICE_NAME or 
            device.address == HIWONDER_MAC or 
            (device.name and "hiwonder" in device.name.lower())):
            print(f"🎯 Found device: {device.name} ({device.address})")
            target_device = device
            break
    
    if not target_device:
        print("❌ Hiwonder device not found")
        return
    
    print(f"📞 Connecting to {target_device.name} ({target_device.address})...")
    
    try:
        async with BleakClient(target_device) as client:
            print("🎉 Connected!")
            
            print("\n🔍 BLE Services and Characteristics:")
            print("=" * 70)
            
            for service in client.services:
                print(f"📋 Service: {service.uuid}")
                print(f"   Description: {service.description}")
                
                for char in service.characteristics:
                    properties = ", ".join(char.properties)
                    print(f"  📝 Characteristic: {char.uuid}")
                    print(f"     Handle: {char.handle}")
                    print(f"     Properties: {properties}")
                    print(f"     Description: {char.description}")
                    
                    # Check for duplicates
                    if char.uuid.lower() == "0000ffe1-0000-1000-8000-00805f9b34fb":
                        print("     ⭐ THIS IS A TARGET WRITE CHARACTERISTIC")
                        
                    # List descriptors
                    if char.descriptors:
                        for desc in char.descriptors:
                            print(f"       🔖 Descriptor: {desc.uuid} (handle: {desc.handle})")
                    print()
                print()
            
            print("=" * 70)
            
            # Count characteristics with same UUID
            uuid_counts = {}
            for service in client.services:
                for char in service.characteristics:
                    uuid = char.uuid.lower()
                    if uuid in uuid_counts:
                        uuid_counts[uuid] += 1
                    else:
                        uuid_counts[uuid] = 1
            
            print("📊 UUID Usage Summary:")
            for uuid, count in uuid_counts.items():
                if count > 1:
                    print(f"⚠️  {uuid}: {count} characteristics (DUPLICATE)")
                else:
                    print(f"✅ {uuid}: {count} characteristic")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_ble_device())
