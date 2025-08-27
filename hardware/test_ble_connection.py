#!/usr/bin/env python3
"""
Test BLE Connection to Hiwonder Device
Simple script to test and verify BLE connectivity
"""

import asyncio
from bleak import BleakScanner, BleakClient

# Hiwonder device constants
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_MAC = "8EE2E4F9-42E6-5BE3-4E2A-A706CAD38879"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

async def scan_for_devices():
    """Scan for all BLE devices"""
    print("🔍 Scanning for BLE devices...")
    try:
        devices = await BleakScanner.discover(timeout=10.0)
        print(f"📱 Found {len(devices)} BLE devices:")
        
        hiwonder_found = False
        for i, device in enumerate(devices):
            is_hiwonder = (device.name == HIWONDER_DEVICE_NAME or 
                          device.address == HIWONDER_MAC or 
                          (device.name and "hiwonder" in device.name.lower()))
            
            status = "🎯 HIWONDER!" if is_hiwonder else "  "
            rssi = getattr(device, 'rssi', 'N/A')
            print(f"{status} {i+1:2d}. {device.name or 'Unknown':<20} {device.address} RSSI: {rssi}dBm")
            
            if is_hiwonder:
                hiwonder_found = True
        
        return hiwonder_found
        
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return False

async def test_connection():
    """Test connection to Hiwonder device"""
    print("🔗 Testing connection to Hiwonder BLE device...")
    
    try:
        # Try to connect using MAC address
        print(f"📞 Attempting connection to {HIWONDER_MAC}...")
        client = BleakClient(HIWONDER_MAC)
        await client.connect()
        
        if client.is_connected:
            print("🎉 SUCCESS! Connected to Hiwonder BLE device!")
            
            # List services
            services = client.services
            service_list = list(services)
            print(f"📋 Found {len(service_list)} services:")
            
            target_service = None
            target_char = None
            
            for service in services:
                print(f"   Service: {service.uuid}")
                if service.uuid.lower() == HIWONDER_SERVICE_UUID.lower():
                    target_service = service
                    print("   🎯 TARGET SERVICE FOUND!")
                
                for char in service.characteristics:
                    props = ", ".join(char.properties)
                    print(f"      Char: {char.uuid} [{props}]")
                    if char.uuid.lower() == HIWONDER_WRITE_CHAR_UUID.lower():
                        target_char = char
                        print("      🎯 TARGET CHARACTERISTIC FOUND!")
            
            if target_service and target_char:
                print("✅ All required services and characteristics found!")
                print("🤖 Ready for servo control!")
                
                # Test sending a command (use the first characteristic we found)
                print("📤 Testing servo command...")
                test_packet = bytearray([0xAA, 0x77, 0x01, 0x06, 90, 90, 90, 90, 90, 90, 0x7A])
                await client.write_gatt_char(target_char, test_packet, response=False)
                print("✅ Test command sent successfully!")
                
            else:
                print("❌ Required services/characteristics not found")
            
            await client.disconnect()
            print("👋 Disconnected")
            return True
        else:
            print("❌ Connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

async def main():
    """Main test function"""
    print("🤖 Hiwonder BLE Connection Test")
    print("=" * 40)
    
    # First scan for devices
    found = await scan_for_devices()
    
    print("\n" + "=" * 40)
    
    if found:
        print("✅ Hiwonder device detected in scan!")
        print("🔗 Attempting connection test...")
        success = await test_connection()
        
        if success:
            print("\n🎉 BLE CONNECTION TEST PASSED!")
            print("💡 Your Hiwonder device is ready for hand tracking!")
        else:
            print("\n❌ BLE CONNECTION TEST FAILED!")
            print("💡 Check if device is in pairing/connection mode")
    else:
        print("❌ Hiwonder device not found in scan")
        print("💡 Make sure device is powered on and in discoverable mode")
    
    print("\n👋 Test complete")

if __name__ == "__main__":
    asyncio.run(main())
