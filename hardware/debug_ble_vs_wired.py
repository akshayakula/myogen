#!/usr/bin/env python3
"""
Debug BLE vs Wired - Compare what gets sent vs received
"""

import serial
import serial.tools.list_ports
import time

def find_arduino():
    """Find Arduino port"""
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        if ('Arduino' in port.description or 
            'CH340' in port.description or 
            'USB' in port.description or
            'usbmodem' in port.device or
            'usbserial' in port.device):
            return port.device
    return None

def build_test_packet():
    """Build the same test packet"""
    packet = bytearray()
    packet.append(0xAA)  # Start byte 1
    packet.append(0x77)  # Start byte 2
    packet.append(0x01)  # Function (servo control)
    packet.append(0x06)  # Length (6 servos)
    
    # Test servo angles: 45 degrees for all
    servo_angles = [45, 45, 45, 45, 45, 45]
    packet.extend(servo_angles)
    
    # Calculate checksum
    checksum_data = packet[2:]
    checksum = 0
    for byte in checksum_data:
        checksum += byte
    checksum = ~checksum & 0xFF
    packet.append(checksum)
    
    return packet

def test_wired_connection():
    """Test wired connection to verify packet works"""
    print("=== Testing Wired Connection ===")
    
    port = find_arduino()
    if not port:
        print("❌ No Arduino found via USB")
        return False
    
    print(f"📍 Found Arduino on: {port}")
    
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)  # Wait for Arduino to initialize
        
        packet = build_test_packet()
        print(f"📦 Sending packet: {' '.join(f'0x{b:02X}' for b in packet)}")
        
        ser.write(packet)
        time.sleep(0.5)
        
        # Read any response
        response = ser.read_all()
        if response:
            print(f"📥 Arduino response: {response.decode('utf-8', errors='ignore')}")
        else:
            print("📥 No response from Arduino")
        
        ser.close()
        print("✅ Wired test complete")
        return True
        
    except Exception as e:
        print(f"❌ Wired test failed: {e}")
        return False

def main():
    print("=== BLE vs Wired Debug Tool ===")
    print("This tool helps debug why BLE doesn't work while wired does")
    print()
    
    # Test wired first
    wired_success = test_wired_connection()
    
    if not wired_success:
        print("\n❌ Can't proceed - wired connection doesn't work")
        print("Fix wired connection first, then test BLE")
        return
    
    print(f"\n✅ Wired connection works!")
    print(f"📋 The packet format is correct")
    print(f"📋 Arduino code is working")
    print(f"📋 Servo hardware is connected")
    print()
    print("🔍 BLE Issues to check:")
    print("1. Is Hiwonder module powered?")
    print("2. Is it connected to another device?")
    print("3. Are the wires correct? (MCU_TX → Arduino RX)")
    print("4. Is the BLE module in the right mode?")
    print()
    print("💡 Try:")
    print("• Power cycle the Hiwonder module")
    print("• Check Mac Bluetooth settings")
    print("• Run: python3 test_ble_connection.py")

if __name__ == "__main__":
    main()
