#!/usr/bin/env python3
"""
BLE Gyro Receiver - Receives 6-axis gyro data via BLE from Arduino
Connects to Hiwonder BLE module and receives gyro/accelerometer data
"""

import asyncio
import struct
import time
from bleak import BleakClient, BleakScanner
from dataclasses import dataclass
from typing import Optional

# Hiwonder BLE Constants
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_MAC = "8EE2E4F9-42E6-5BE3-4E2A-A706CAD38879"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
HIWONDER_NOTIFY_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # Same as write for this module

# Protocol constants
FRAME_HEADER = 0x55
CMD_START_GYRO_STREAM = 0x11
CMD_STOP_GYRO_STREAM = 0x12
CMD_GYRO_DATA = 0x13

@dataclass
class GyroData:
    """6-axis gyro/accelerometer data"""
    gyro_x: int
    gyro_y: int
    gyro_z: int
    accel_x: int
    accel_y: int
    accel_z: int
    timestamp: float

# Global connection variables
ble_client: Optional[BleakClient] = None
is_connected = False
gyro_data_count = 0

def parse_gyro_packet(data: bytearray) -> Optional[GyroData]:
    """Parse BLE gyro data packet"""
    try:
        # Expected format: 0x55 0x55 [length] 0x13 [12 bytes gyro data]
        if len(data) < 16:  # Minimum packet size
            return None
            
        # Check headers
        if data[0] != FRAME_HEADER or data[1] != FRAME_HEADER:
            return None
            
        # Check function code
        if data[3] != CMD_GYRO_DATA:
            return None
            
        # Extract gyro data (12 bytes starting at index 4)
        gyro_bytes = data[4:16]
        
        # Unpack 6 int16_t values (little-endian)
        gyro_x = struct.unpack('<h', gyro_bytes[0:2])[0]
        gyro_y = struct.unpack('<h', gyro_bytes[2:4])[0]
        gyro_z = struct.unpack('<h', gyro_bytes[4:6])[0]
        accel_x = struct.unpack('<h', gyro_bytes[6:8])[0]
        accel_y = struct.unpack('<h', gyro_bytes[8:10])[0]
        accel_z = struct.unpack('<h', gyro_bytes[10:12])[0]
        
        return GyroData(
            gyro_x=gyro_x,
            gyro_y=gyro_y,
            gyro_z=gyro_z,
            accel_x=accel_x,
            accel_y=accel_y,
            accel_z=accel_z,
            timestamp=time.time()
        )
        
    except Exception as e:
        print(f"❌ Error parsing gyro packet: {e}")
        return None

def notification_handler(sender, data):
    """Handle BLE notifications (incoming data)"""
    global gyro_data_count
    
    # Parse the gyro data
    gyro_data = parse_gyro_packet(data)
    
    if gyro_data:
        gyro_data_count += 1
        
        # Print gyro data (every 10th packet to avoid spam)
        if gyro_data_count % 10 == 0:
            print(f"📊 Gyro Data #{gyro_data_count}:")
            print(f"   Gyroscope:    X={gyro_data.gyro_x:6d}  Y={gyro_data.gyro_y:6d}  Z={gyro_data.gyro_z:6d}")
            print(f"   Accelerometer: X={gyro_data.accel_x:6d}  Y={gyro_data.accel_y:6d}  Z={gyro_data.accel_z:6d}")
            print()
        
        # You can add your own processing here:
        # - Save to file
        # - Send to another system
        # - Analyze for gestures
        # - etc.
        
    else:
        # Print raw data for debugging
        hex_data = ' '.join([f'{b:02X}' for b in data])
        print(f"🔍 Raw data: {hex_data}")

async def connect_to_arduino():
    """Connect to Arduino BLE device"""
    global ble_client, is_connected
    
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
        print("💡 Make sure the BLE module is powered and not connected to another device")
        return False
    
    try:
        print(f"📞 Connecting to {target_device.name}...")
        ble_client = BleakClient(target_device)
        await ble_client.connect()
        
        if ble_client.is_connected:
            print("🎉 Connected to Arduino!")
            
            # Find the correct characteristic by handle
            notify_char = None
            for service in ble_client.services:
                if service.uuid.lower() == HIWONDER_SERVICE_UUID.lower():
                    for char in service.characteristics:
                        if char.uuid.lower() == HIWONDER_NOTIFY_CHAR_UUID.lower():
                            # Use the first matching characteristic
                            notify_char = char
                            print(f"🎯 Found notify characteristic: handle {char.handle}")
                            break
                    break
            
            if notify_char:
                # Set up notifications to receive data
                await ble_client.start_notify(notify_char, notification_handler)
                print("📡 Notifications enabled - ready to receive gyro data!")
            else:
                print("❌ Notify characteristic not found")
                return False
            
            is_connected = True
            return True
        else:
            print("❌ Connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

async def send_gyro_command(command: int):
    """Send gyro command to Arduino"""
    if not is_connected or not ble_client:
        return False
        
    try:
        # Build simple command packet
        packet = bytearray([
            FRAME_HEADER,  # 0x55
            FRAME_HEADER,  # 0x55
            1,             # Length (just command)
            command        # Command
        ])
        
        # Find write characteristic
        write_char = None
        for service in ble_client.services:
            if service.uuid.lower() == HIWONDER_SERVICE_UUID.lower():
                for char in service.characteristics:
                    if char.uuid.lower() == HIWONDER_WRITE_CHAR_UUID.lower():
                        write_char = char
                        break
                break
        
        if write_char:
            # Send command
            await ble_client.write_gatt_char(write_char, packet, response=False)
        else:
            print("❌ Write characteristic not found")
            return False
        
        if command == CMD_START_GYRO_STREAM:
            print("✅ Gyro streaming started!")
        elif command == CMD_STOP_GYRO_STREAM:
            print("✅ Gyro streaming stopped!")
            
        return True
        
    except Exception as e:
        print(f"❌ Command send failed: {e}")
        return False

async def main():
    """Main program"""
    print("=== BLE Gyro Receiver ===")
    print("This script receives 6-axis gyro data via BLE from Arduino")
    print()
    
    # Connect to Arduino
    if not await connect_to_arduino():
        return
    
    try:
        # Start gyro streaming
        print("🚀 Starting gyro data stream...")
        await send_gyro_command(CMD_START_GYRO_STREAM)
        
        # Listen for data
        print("👂 Listening for gyro data... (Press Ctrl+C to stop)")
        print("📊 Showing every 10th data packet to avoid spam")
        print()
        
        # Keep running and receiving data
        while True:
            await asyncio.sleep(1)
            
            # Show connection status every 30 seconds
            if gyro_data_count % 300 == 0 and gyro_data_count > 0:
                print(f"📈 Total packets received: {gyro_data_count}")
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping gyro stream...")
        await send_gyro_command(CMD_STOP_GYRO_STREAM)
        
    finally:
        if ble_client and ble_client.is_connected:
            await ble_client.disconnect()
            print("👋 Disconnected from Arduino")

if __name__ == "__main__":
    asyncio.run(main())
