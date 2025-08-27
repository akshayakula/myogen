#!/usr/bin/env python3
"""
Simple Servo Control Script
Control individual servos with arrow keys and number keys
Arrow keys: Up/Down to change angle
Number keys: 1-6 to select servo
ESC to quit
"""

import serial
import serial.tools.list_ports
import struct
import sys
import termios
import tty
import time

# Protocol constants
CONST_STARTBYTE1 = 0xAA
CONST_STARTBYTE2 = 0x77
FUNC_SET_SERVO = 0x01

# Current state
current_servo = 0  # 0-5 (servo 1-6)
servo_angles = [90, 90, 90, 90, 90, 90]  # Default angles
serial_connection = None

# Servo limits from Arduino code
servo_limits = [(0, 82), (0, 180), (0, 180), (25, 180), (0, 180), (0, 180)]
servo_names = ["Thumb", "Index", "Middle", "Ring", "Pinky", "Wrist"]

def find_arduino():
    """Find Arduino port automatically"""
    ports = serial.tools.list_ports.comports()
    arduino_ports = [p.device for p in ports if 
                   'Arduino' in p.description or 
                   'CH340' in p.description or 
                   'USB' in p.description or
                   'usbmodem' in p.device or
                   'usbserial' in p.device]
    
    if arduino_ports:
        return arduino_ports[0]
    return None

def calculate_checksum(data):
    """Calculate checksum for packet"""
    checksum = 0
    for byte in data:
        checksum += byte
    checksum = ~checksum & 0xFF
    return checksum

def send_servo_command(servo_id, angle):
    """Send servo command to Arduino"""
    global serial_connection
    
    if not serial_connection:
        return False
    
    try:
        # Build packet: 0xAA 0x77 [Function] [Length] [Data...] [Checksum]
        packet = bytearray()
        packet.append(CONST_STARTBYTE1)  # 0xAA
        packet.append(CONST_STARTBYTE2)  # 0x77
        packet.append(FUNC_SET_SERVO)    # Function code
        packet.append(6)                 # Data length (6 servos)
        
        # Send all current servo angles (NO inversion here - let Arduino handle it)
        packet.extend(servo_angles)
        
        # Calculate checksum (function + length + all servo data)
        checksum_data = packet[2:]  # Everything after start bytes
        checksum = calculate_checksum(checksum_data)
        packet.append(checksum)
        
        # Send packet
        serial_connection.write(packet)
        print(f"Sent: Servo {servo_id+1} = {angle}°, All angles: {servo_angles}")
        return True
        
    except Exception as e:
        print(f"Error sending command: {e}")
        return False

def get_key():
    """Get a single keypress without Enter"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1)
        
        # Handle escape sequences (arrow keys)
        if ch == '\x1b':  # ESC sequence
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                return f'\x1b[{ch3}'
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def print_status():
    """Print current status"""
    print("\033[2J\033[H")  # Clear screen and move to top
    print("=" * 60)
    print("           SIMPLE SERVO CONTROL")
    print("=" * 60)
    print()
    
    # Show all servo angles
    for i in range(6):
        min_angle, max_angle = servo_limits[i]
        if i == current_servo:
            marker = ">>> "
            color = "\033[92m"  # Green
            reset = "\033[0m"
        else:
            marker = "    "
            color = ""
            reset = ""
        
        # Show angle bar
        bar_width = 30
        angle_ratio = (servo_angles[i] - min_angle) / (max_angle - min_angle)
        filled_width = int(angle_ratio * bar_width)
        bar = "█" * filled_width + "░" * (bar_width - filled_width)
        
        print(f"{marker}{color}Servo {i+1} ({servo_names[i]:>6}): {servo_angles[i]:3d}° [{bar}] ({min_angle}-{max_angle}°){reset}")
    
    print()
    print("Controls:")
    print("  ↑ / ↓     - Increase/Decrease angle")
    print("  1-6       - Select servo")
    print("  ESC       - Quit")
    print()
    print(f"Currently controlling: Servo {current_servo + 1} ({servo_names[current_servo]})")

def main():
    global current_servo, servo_angles, serial_connection
    
    print("Simple Servo Control Starting...")
    
    # Find and connect to Arduino
    port = find_arduino()
    if not port:
        print("❌ No Arduino found!")
        print("Please connect Arduino and try again.")
        return
    
    try:
        serial_connection = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset
        print(f"✅ Connected to Arduino on {port}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Send initial position (all servos to default)
    for i in range(6):
        send_servo_command(i, servo_angles[i])
    
    print("🎮 Starting control interface...")
    time.sleep(1)
    
    try:
        while True:
            print_status()
            
            key = get_key()
            
            if key == '\x1b':  # ESC key
                print("\n👋 Exiting...")
                break
            elif key == '\x1b[A':  # Up arrow
                min_angle, max_angle = servo_limits[current_servo]
                if servo_angles[current_servo] < max_angle:
                    servo_angles[current_servo] += 5
                    if servo_angles[current_servo] > max_angle:
                        servo_angles[current_servo] = max_angle
                    send_servo_command(current_servo, servo_angles[current_servo])
            elif key == '\x1b[B':  # Down arrow
                min_angle, max_angle = servo_limits[current_servo]
                if servo_angles[current_servo] > min_angle:
                    servo_angles[current_servo] -= 5
                    if servo_angles[current_servo] < min_angle:
                        servo_angles[current_servo] = min_angle
                    send_servo_command(current_servo, servo_angles[current_servo])
            elif key in '123456':  # Number keys
                servo_num = int(key) - 1
                if 0 <= servo_num < 6:
                    current_servo = servo_num
            elif key == 'q':  # Alternative quit
                print("\n👋 Exiting...")
                break
            
            time.sleep(0.05)  # Small delay
            
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    
    finally:
        if serial_connection:
            # Return all servos to neutral before closing
            for i in range(6):
                servo_angles[i] = 90
                send_servo_command(i, 90)
            time.sleep(0.5)
            serial_connection.close()
            print("🔌 Disconnected from Arduino")

if __name__ == "__main__":
    main()
