#!/usr/bin/env python3
"""
Gyro Data Reader for Robotic Hand
Reads gyro data stream from Arduino via BLE and detects flick gestures
"""

import asyncio
import struct
import time
import numpy as np
from collections import deque
from typing import Optional, Callable
from bleak import BleakClient, BleakScanner

# Hiwonder BLE Constants (same as pose sender)
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_MAC = "8EE2E4F9-42E6-5BE3-4E2A-A706CAD38879"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Protocol constants
FRAME_HEADER = 0x55
CMD_GYRO_DATA = 0x10
CMD_START_GYRO_STREAM = 0x11
CMD_STOP_GYRO_STREAM = 0x12

# Global connection variables
ble_client = None
is_connected = False

class GyroData:
    """Structure to hold gyro/accel data"""
    def __init__(self, gyro_x=0, gyro_y=0, gyro_z=0, accel_x=0, accel_y=0, accel_z=0, timestamp=0):
        self.gyro_x = gyro_x
        self.gyro_y = gyro_y
        self.gyro_z = gyro_z
        self.accel_x = accel_x
        self.accel_y = accel_y
        self.accel_z = accel_z
        self.timestamp = timestamp
        
    def gyro_magnitude(self):
        """Calculate magnitude of gyro vector"""
        return np.sqrt(self.gyro_x**2 + self.gyro_y**2 + self.gyro_z**2)
    
    def accel_magnitude(self):
        """Calculate magnitude of acceleration vector"""
        return np.sqrt(self.accel_x**2 + self.accel_y**2 + self.accel_z**2)

class FlickDetector:
    """Detects flick gestures from gyro data"""
    
    def __init__(self, 
                 gyro_threshold=15000,    # Gyro magnitude threshold for flick
                 accel_threshold=8000,    # Accel magnitude threshold for flick
                 cooldown_ms=1000,        # Minimum time between flicks
                 history_size=20):        # Number of readings to keep
        
        self.gyro_threshold = gyro_threshold
        self.accel_threshold = accel_threshold
        self.cooldown_ms = cooldown_ms
        self.history_size = history_size
        
        self.gyro_history = deque(maxlen=history_size)
        self.last_flick_time = 0
        self.flick_callback = None
        
        # Statistics
        self.total_readings = 0
        self.flicks_detected = 0
        
    def set_flick_callback(self, callback: Callable):
        """Set callback function to call when flick is detected"""
        self.flick_callback = callback
    
    def process_gyro_data(self, gyro_data: GyroData):
        """Process new gyro data and detect flicks"""
        self.total_readings += 1
        self.gyro_history.append(gyro_data)
        
        # Need at least 3 readings for comparison
        if len(self.gyro_history) < 3:
            return False
            
        # Check cooldown period
        if gyro_data.timestamp - self.last_flick_time < self.cooldown_ms:
            return False
        
        # Calculate current magnitudes
        gyro_mag = gyro_data.gyro_magnitude()
        accel_mag = gyro_data.accel_magnitude()
        
        # Get baseline from recent history (excluding current reading)
        recent_gyro = [g.gyro_magnitude() for g in list(self.gyro_history)[:-1]]
        baseline_gyro = np.mean(recent_gyro[-5:]) if len(recent_gyro) >= 5 else np.mean(recent_gyro)
        
        # Detect sudden spike in gyro activity
        gyro_spike = gyro_mag > self.gyro_threshold and gyro_mag > baseline_gyro * 3
        accel_spike = accel_mag > self.accel_threshold
        
        # Flick detected if both conditions met
        if gyro_spike and accel_spike:
            self.last_flick_time = gyro_data.timestamp
            self.flicks_detected += 1
            
            print(f"🪄 FLICK DETECTED! Gyro: {gyro_mag:.0f}, Accel: {accel_mag:.0f}")
            
            if self.flick_callback:
                self.flick_callback(gyro_data)
                
            return True
            
        return False
    
    def get_stats(self):
        """Get detection statistics"""
        return {
            'total_readings': self.total_readings,
            'flicks_detected': self.flicks_detected,
            'detection_rate': self.flicks_detected / max(1, self.total_readings) * 100,
            'current_threshold_gyro': self.gyro_threshold,
            'current_threshold_accel': self.accel_threshold
        }

class GyroDataParser:
    """Parses incoming gyro data packets from Arduino"""
    
    def __init__(self):
        self.buffer = bytearray()
        self.packet_callback = None
        
    def set_packet_callback(self, callback: Callable):
        """Set callback for complete packets"""
        self.packet_callback = callback
    
    def process_data(self, data: bytes):
        """Process incoming data and extract complete packets"""
        self.buffer.extend(data)
        
        while len(self.buffer) >= 4:  # Minimum packet size
            # Look for frame headers
            header_pos = -1
            for i in range(len(self.buffer) - 1):
                if self.buffer[i] == FRAME_HEADER and self.buffer[i + 1] == FRAME_HEADER:
                    header_pos = i
                    break
            
            if header_pos == -1:
                # No header found, clear buffer
                self.buffer.clear()
                break
            
            # Remove data before header
            if header_pos > 0:
                self.buffer = self.buffer[header_pos:]
            
            # Check if we have enough data for packet length
            if len(self.buffer) < 4:
                break
                
            packet_length = self.buffer[2]
            total_length = 3 + packet_length  # headers + length + data
            
            # Check if we have complete packet
            if len(self.buffer) < total_length:
                break
                
            # Extract packet
            packet = self.buffer[:total_length]
            self.buffer = self.buffer[total_length:]
            
            # Process packet
            self._process_packet(packet)
    
    def _process_packet(self, packet: bytearray):
        """Process a complete packet"""
        if len(packet) < 4:
            return
            
        # Parse packet structure
        header1 = packet[0]
        header2 = packet[1] 
        length = packet[2]
        command = packet[3]
        
        if header1 != FRAME_HEADER or header2 != FRAME_HEADER:
            print(f"Invalid headers: {header1:02x} {header2:02x}")
            return
            
        if command == CMD_GYRO_DATA:
            self._parse_gyro_packet(packet[4:])
        else:
            print(f"Unknown command: {command:02x}")
    
    def _parse_gyro_packet(self, data: bytearray):
        """Parse gyro data packet"""
        if len(data) < 14:  # 6 int16 + 1 uint32
            print(f"Gyro packet too short: {len(data)} bytes")
            return
            
        try:
            # Unpack gyro data (little-endian)
            gyro_x, gyro_y, gyro_z = struct.unpack('<hhh', data[0:6])
            accel_x, accel_y, accel_z = struct.unpack('<hhh', data[6:12])
            timestamp = struct.unpack('<I', data[12:16])[0]
            
            gyro_data = GyroData(gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z, timestamp)
            
            if self.packet_callback:
                self.packet_callback(gyro_data)
                
        except struct.error as e:
            print(f"Error parsing gyro packet: {e}")

async def list_ble_characteristics():
    """Debug function to list all BLE services and characteristics"""
    if not ble_client:
        return
        
    print("\n🔍 BLE Services and Characteristics:")
    print("=" * 50)
    
    for service in ble_client.services:
        print(f"📋 Service: {service.uuid}")
        for char in service.characteristics:
            properties = ", ".join(char.properties)
            print(f"  📝 Characteristic: {char.uuid}")
            print(f"     Handle: {char.handle}")
            print(f"     Properties: {properties}")
            
            # Highlight the write characteristic we're looking for
            if char.uuid.lower() == HIWONDER_WRITE_CHAR_UUID.lower():
                print("     ⭐ THIS IS OUR TARGET WRITE CHARACTERISTIC")
        print()
    print("=" * 50)

async def connect_to_arduino():
    """Connect to Arduino BLE device"""
    global ble_client, is_connected
    
    print("🔍 Scanning for Hiwonder BLE device...")
    devices = await BleakScanner.discover(timeout=10.0)
    
    hiwonder_found = False
    for device in devices:
        if (device.name == HIWONDER_DEVICE_NAME or 
            device.address == HIWONDER_MAC or 
            (device.name and "hiwonder" in device.name.lower())):
            print(f"🎯 Found device: {device.name} ({device.address})")
            hiwonder_found = True
            break
    
    if not hiwonder_found:
        print("❌ Hiwonder device not found")
        return False
    
    try:
        print(f"📞 Connecting to {HIWONDER_MAC}...")
        ble_client = BleakClient(HIWONDER_MAC)
        await ble_client.connect()
        
        if ble_client.is_connected:
            print("🎉 Connected to Arduino!")
            
            # Debug: List all services and characteristics
            await list_ble_characteristics()
            
            is_connected = True
            return True
        else:
            print("❌ Connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

async def send_command(command: int):
    """Send command to Arduino"""
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
        
        # Find the correct write characteristic by service and UUID
        # We want handle 24 in service 0000fff0-0000-1000-8000-00805f9b34fb
        write_char = None
        target_service_uuid = "0000fff0-0000-1000-8000-00805f9b34fb"
        
        for service in ble_client.services:
            if service.uuid.lower() == target_service_uuid.lower():
                for char in service.characteristics:
                    if char.uuid.lower() == HIWONDER_WRITE_CHAR_UUID.lower():
                        write_char = char
                        print(f"🎯 Found correct characteristic: handle {char.handle} in service {service.uuid}")
                        break
                break
        
        if write_char:
            await ble_client.write_gatt_char(write_char, packet)
            print(f"✅ Command sent successfully to handle {write_char.handle}")
            return True
        else:
            print("❌ Correct write characteristic not found")
            return False
        
    except Exception as e:
        print(f"❌ Command send failed: {e}")
        return False

def on_flick_detected(gyro_data: GyroData):
    """Callback when flick is detected"""
    print(f"⚡ FLICK! Time: {gyro_data.timestamp}, "
          f"Gyro: ({gyro_data.gyro_x}, {gyro_data.gyro_y}, {gyro_data.gyro_z}), "
          f"Accel: ({gyro_data.accel_x}, {gyro_data.accel_y}, {gyro_data.accel_z})")

async def main():
    """Main function"""
    global ble_client, is_connected
    
    print("🚀 Gyro Data Reader Starting...")
    
    # Connect to Arduino
    if not await connect_to_arduino():
        return
    
    # Setup data processing
    parser = GyroDataParser()
    flick_detector = FlickDetector()
    flick_detector.set_flick_callback(on_flick_detected)
    
    def on_gyro_data(gyro_data: GyroData):
        """Process received gyro data"""
        # Display current readings
        print(f"📊 Gyro: ({gyro_data.gyro_x:6d}, {gyro_data.gyro_y:6d}, {gyro_data.gyro_z:6d}) "
              f"Accel: ({gyro_data.accel_x:6d}, {gyro_data.accel_y:6d}, {gyro_data.accel_z:6d}) "
              f"Mag: {gyro_data.gyro_magnitude():.0f}", end='\r')
        
        # Check for flicks
        flick_detector.process_gyro_data(gyro_data)
    
    parser.set_packet_callback(on_gyro_data)
    
    # Setup serial data handler
    def notification_handler(sender, data):
        parser.process_data(data)
    
    # This would need to be adapted for your BLE setup
    # For now, we'll simulate with serial data reading
    
    try:
        print("📡 Starting gyro stream...")
        await send_command(CMD_START_GYRO_STREAM)
        
        print("🎮 Gyro monitoring active - make flick gestures!")
        print("Press Ctrl+C to stop")
        
        # Main monitoring loop
        start_time = time.time()
        while True:
            await asyncio.sleep(0.1)
            
            # Print stats every 10 seconds
            if time.time() - start_time > 10:
                stats = flick_detector.get_stats()
                print(f"\n📈 Stats: {stats['total_readings']} readings, "
                      f"{stats['flicks_detected']} flicks detected "
                      f"({stats['detection_rate']:.1f}% rate)")
                start_time = time.time()
    
    except KeyboardInterrupt:
        print("\n👋 Stopping gyro monitoring...")
    
    finally:
        if is_connected:
            await send_command(CMD_STOP_GYRO_STREAM)
            await ble_client.disconnect()
            print("📶 Disconnected from Arduino")

if __name__ == "__main__":
    asyncio.run(main())
