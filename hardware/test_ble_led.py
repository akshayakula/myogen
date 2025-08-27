#!/usr/bin/env python3
"""
Interactive BLE LED Control

Manual keyboard control of Arduino LED via Hiwonder BLE module.
Press keys to send commands and test BLE communication in real-time.
"""

import asyncio
import sys
import select
import tty
import termios
from bleak import BleakScanner, BleakClient

# Hiwonder BLE Constants
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Global variables for BLE
client = None
write_char = None

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

def get_key():
    """Get a single keypress from stdin (non-blocking)"""
    if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
        return sys.stdin.read(1)
    return None

async def send_command(cmd_byte, description):
    """Send a single command to the Arduino"""
    global client, write_char
    
    try:
        await client.write_gatt_char(write_char, bytes([cmd_byte]))
        print(f"✓ Sent: {description} (0x{cmd_byte:02X})")
        return True
    except Exception as e:
        print(f"❌ Failed to send {description}: {e}")
        return False

async def interactive_control():
    """Interactive keyboard control loop"""
    print("\n🎮 Interactive LED Control")
    print("=" * 40)
    print("Controls:")
    print("  1 - Turn LED ON")
    print("  0 - Turn LED OFF")
    print("  b - Fast Blink")
    print("  s - Slow Blink")
    print("  q - Quit")
    print("=" * 40)
    print("Press keys to control the LED...")
    print()
    
    # Set terminal to raw mode for immediate key detection
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        
        while True:
            await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
            
            key = get_key()
            if key:
                if key == 'q' or key == '\x03':  # 'q' or Ctrl+C
                    print("\n👋 Quitting...")
                    break
                elif key == '1':
                    await send_command(ord('1'), "LED ON")
                elif key == '0':
                    await send_command(ord('0'), "LED OFF")
                elif key == 'b' or key == 'B':
                    await send_command(ord('B'), "Fast Blink")
                elif key == 's' or key == 'S':
                    await send_command(ord('X'), "Slow Blink")
                else:
                    print(f"Unknown key: '{key}' - use 1/0/b/s/q")
    
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

async def main():
    """Main BLE LED test function"""
    global client, write_char
    
    print("=== Interactive BLE LED Control ===")
    print("Manual keyboard control of Arduino LED via BLE")
    print()
    
    # Scan for device
    device = await scan_for_hiwonder()
    if not device:
        print("\nTroubleshooting:")
        print("• Make sure the Hiwonder BLE module is powered on")
        print("• Check that the module is not connected to another device")
        print("• Try moving closer to the module")
        return
    
    print(f"\n🔗 Connecting to {device.address}...")
    
    try:
        async with BleakClient(device) as ble_client:
            client = ble_client  # Set global for other functions
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
                            write_char = char  # Set global for other functions
                            print("✓ Found write characteristic!")
                            break
                    break
            
            if not target_char:
                print("❌ Could not find write characteristic!")
                return
            
            # Start interactive control
            await interactive_control()
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
