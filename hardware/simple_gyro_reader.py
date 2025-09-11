#!/usr/bin/env python3
"""
Simple Gyro Reader - Reads gyro data from Arduino serial output
Sends start command via BLE and reads gyro data from serial prints
"""

import asyncio
import time
import re
from bleak import BleakClient, BleakScanner

# Hiwonder BLE Constants
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_MAC = "8EE2E4F9-42E6-5BE3-4E2A-A706CAD38879"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Protocol constants
FRAME_HEADER = 0x55
CMD_START_GYRO_STREAM = 0x11
CMD_STOP_GYRO_STREAM = 0x12

# Global connection variables
ble_client = None
is_connected = False

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
        return False
    
    try:
        print(f"📞 Connecting to {target_device.name}...")
        ble_client = BleakClient(target_device)
        await ble_client.connect()
        
        if ble_client.is_connected:
            print("🎉 Connected to Arduino!")
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
        
        # Find the correct write characteristic (handle 24 in service 0000fff0)
        write_char = None
        target_service_uuid = "0000fff0-0000-1000-8000-00805f9b34fb"
        
        for service in ble_client.services:
            if service.uuid.lower() == target_service_uuid.lower():
                for char in service.characteristics:
                    if char.uuid.lower() == HIWONDER_WRITE_CHAR_UUID.lower():
                        write_char = char
                        break
                break
        
        if write_char:
            await ble_client.write_gatt_char(write_char, packet)
            return True
        else:
            print("❌ Write characteristic not found")
            return False
        
    except Exception as e:
        print(f"❌ Command send failed: {e}")
        return False

def parse_gyro_line(line):
    """Parse gyro data from serial line"""
    # Look for lines like: GYRO:gx,gy,gz,ax,ay,az,timestamp
    if line.startswith("GYRO:"):
        try:
            data_part = line[5:]  # Remove "GYRO:" prefix
            values = [int(x.strip()) for x in data_part.split(',')]
            if len(values) == 7:
                gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z, timestamp = values
                return {
                    'gyro_x': gyro_x,
                    'gyro_y': gyro_y, 
                    'gyro_z': gyro_z,
                    'accel_x': accel_x,
                    'accel_y': accel_y,
                    'accel_z': accel_z,
                    'timestamp': timestamp
                }
        except (ValueError, IndexError):
            pass
    return None

def print_gyro_data(data):
    """Print formatted gyro data"""
    gyro_mag = (data['gyro_x']**2 + data['gyro_y']**2 + data['gyro_z']**2)**0.5
    accel_mag = (data['accel_x']**2 + data['accel_y']**2 + data['accel_z']**2)**0.5
    
    print(f"📊 Gyro: ({data['gyro_x']:6d}, {data['gyro_y']:6d}, {data['gyro_z']:6d}) "
          f"Accel: ({data['accel_x']:6d}, {data['accel_y']:6d}, {data['accel_z']:6d}) "
          f"Mag: G={gyro_mag:7.1f} A={accel_mag:7.1f} T={data['timestamp']}")

async def main():
    """Main function"""
    global ble_client, is_connected
    
    print("🚀 Simple Gyro Reader Starting...")
    
    # Connect to Arduino
    if not await connect_to_arduino():
        return
    
    try:
        print("📡 Starting gyro stream...")
        success = await send_gyro_command(CMD_START_GYRO_STREAM)
        if success:
            print("✅ Gyro stream command sent!")
        else:
            print("❌ Failed to send gyro stream command")
            return
        
        print("\n🎮 Gyro data monitoring active!")
        print("📋 The Arduino will print gyro data to serial monitor.")
        print("💡 To see the data, open Arduino IDE Serial Monitor at 9600 baud")
        print("💡 You should see lines like: GYRO:gx,gy,gz,ax,ay,az,timestamp")
        print("Press Ctrl+C to stop")
        
        # Keep connection alive and show status
        start_time = time.time()
        while True:
            await asyncio.sleep(1)
            
            # Print status every 10 seconds
            if time.time() - start_time > 10:
                print(f"⏱️  Still monitoring... ({int(time.time() - start_time)}s elapsed)")
                print("💡 Check Arduino Serial Monitor for gyro data output")
                start_time = time.time()
    
    except KeyboardInterrupt:
        print("\n👋 Stopping gyro monitoring...")
    
    finally:
        if is_connected:
            try:
                print("📡 Stopping gyro stream...")
                await send_gyro_command(CMD_STOP_GYRO_STREAM)
                await ble_client.disconnect()
                print("📶 Disconnected from Arduino")
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())


