#!/usr/bin/env python3
"""
Robotic Hand Controller
Python program to control robotic hand via serial communication
Uses the protocol defined in PC_rec.h and PC_rec.cpp
"""

import serial
import time
import struct
import threading
from typing import List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class HandPosition:
    """Represents a hand position with all 6 servo angles"""
    servo1: int = 90  # Base rotation (0-82°)
    servo2: int = 90  # Joint 1 (0-180°)
    servo3: int = 90  # Joint 2 (0-180°)
    servo4: int = 90  # Joint 3 (25-180°)
    servo5: int = 90  # Joint 4 (0-180°)
    servo6: int = 90  # Joint 5 (0-180°)
    
    def to_array(self) -> List[int]:
        """Convert to array of servo angles"""
        return [self.servo1, self.servo2, self.servo3, self.servo4, self.servo5, self.servo6]
    
    @classmethod
    def from_array(cls, angles: List[int]) -> 'HandPosition':
        """Create from array of servo angles"""
        return cls(*angles)

class RoboticHandController:
    """
    Controller for robotic hand via serial communication
    """
    
    # Protocol constants
    CONST_STARTBYTE1 = 0xAA
    CONST_STARTBYTE2 = 0x77
    
    # Function codes
    FUNC_SET_SERVO = 0x01
    FUNC_SET_BUZZER = 0x02
    FUNC_SET_RGB = 0x03
    FUNC_READ_ANGLE = 0x11
    
    # Predefined hand positions (respecting Arduino limits and servo inversion)
    POSITIONS = {
        'neutral': HandPosition(90, 90, 90, 90, 90, 90),     # All neutral (thumb will be inverted to 90°)
        'open': HandPosition(90, 0, 0, 25, 0, 90),           # Fingers open, ring min is 25°
        'closed': HandPosition(90, 160, 160, 160, 160, 90),  # Fingers mostly closed
        'thumbs_up': HandPosition(0, 160, 0, 25, 0, 90),     # Thumb up (will invert to 180°)
        'peace': HandPosition(90, 0, 160, 25, 160, 90),      # Index/middle open, others closed
        'point': HandPosition(90, 0, 160, 160, 160, 90),     # Only index open
        'grasp': HandPosition(90, 120, 120, 120, 120, 90),   # Moderate grasp
    }
    
    def __init__(self, port: str = None, baud_rate: int = 9600):
        """
        Initialize robotic hand controller
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0' on Linux, 'COM3' on Windows)
            baud_rate: Serial communication baud rate
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.is_connected = False
        self.current_position = HandPosition()
        self.response_thread = None
        self.running = False
        
    def connect(self) -> bool:
        """Connect to robotic hand"""
        try:
            if self.port is None:
                # Try to auto-detect port
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                # Look for Arduino, CH340, USB, or usbmodem devices
                arduino_ports = [p.device for p in ports if 
                               'Arduino' in p.description or 
                               'CH340' in p.description or 
                               'USB' in p.description or
                               'IOUSBHostDevice' in p.description or
                               'usbmodem' in p.device or
                               'usbserial' in p.device]
                
                if arduino_ports:
                    self.port = arduino_ports[0]
                    print(f"Auto-detected Arduino port: {self.port}")
                else:
                    print("No Arduino port detected. Please specify port manually.")
                    return False
            
            self.serial_connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            
            # Clear any initial output
            self.serial_connection.reset_input_buffer()
            
            self.is_connected = True
            print(f"Connected to robotic hand on {self.port}")
            
            # Start response monitoring thread
            self.running = True
            self.response_thread = threading.Thread(target=self._monitor_responses)
            self.response_thread.daemon = True
            self.response_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from robotic hand"""
        self.running = False
        if self.response_thread:
            self.response_thread.join(timeout=1)
        
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.is_connected = False
        print("Disconnected from robotic hand")
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate CRC8 checksum"""
        checksum = 0
        for byte in data:
            checksum += byte
        checksum = ~checksum & 0xFF
        return checksum
    
    def _send_packet(self, function: int, data: bytes) -> bool:
        """Send a packet to the robotic hand"""
        if not self.is_connected:
            print("Not connected to robotic hand")
            return False
        
        try:
            # Build packet
            packet = bytearray()
            packet.append(self.CONST_STARTBYTE1)  # Start byte 1
            packet.append(self.CONST_STARTBYTE2)  # Start byte 2
            packet.append(function)               # Function code
            packet.append(len(data))              # Data length
            packet.extend(data)                   # Data
            
            # Calculate and append checksum
            checksum_data = packet[2:2+len(data)+1]  # Function + length + data
            checksum = self._calculate_checksum(checksum_data)
            packet.append(checksum)
            
            # Send packet
            self.serial_connection.write(packet)
            return True
            
        except Exception as e:
            print(f"Error sending packet: {e}")
            return False
    
    def set_servo_angles(self, angles: List[int]) -> bool:
        """
        Set all servo angles
        
        Args:
            angles: List of 6 servo angles (0-180°)
        """
        if len(angles) != 6:
            print("Error: Must provide exactly 6 servo angles")
            return False
        
        # Validate angles - must match Arduino's limt_angles[6][2]
        limits = [(0, 82), (0, 180), (0, 180), (25, 180), (0, 180), (0, 180)]
        for i, (angle, (min_angle, max_angle)) in enumerate(zip(angles, limits)):
            if angle < min_angle or angle > max_angle:
                print(f"Warning: Servo {i+1} angle {angle}° outside limits ({min_angle}-{max_angle}°)")
        
        # Apply servo inversion logic to match Arduino code
        # servos[i].write(i == 0 || i == 5 ? 180 - servo_angles[i] : servo_angles[i]);
        adjusted_angles = []
        for i, angle in enumerate(angles):
            if i == 0 or i == 5:  # Thumb (servo 0) and wrist (servo 5) are inverted
                adjusted_angles.append(180 - angle)
            else:  # Servos 1-4 (fingers) are normal
                adjusted_angles.append(angle)
        
        # Convert to bytes
        data = struct.pack('6B', *adjusted_angles)
        
        success = self._send_packet(self.FUNC_SET_SERVO, data)
        if success:
            self.current_position = HandPosition.from_array(angles)
            print(f"Set servo angles: {angles} (adjusted: {adjusted_angles})")
        
        return success
    
    def set_hand_position(self, position: HandPosition) -> bool:
        """Set hand to a specific position"""
        return self.set_servo_angles(position.to_array())
    
    def move_to_position(self, position_name: str) -> bool:
        """Move to a predefined position"""
        if position_name not in self.POSITIONS:
            print(f"Unknown position: {position_name}")
            print(f"Available positions: {list(self.POSITIONS.keys())}")
            return False
        
        position = self.POSITIONS[position_name]
        return self.set_hand_position(position)
    
    def set_buzzer(self, frequency: int, duration_ms: int) -> bool:
        """Control buzzer"""
        data = struct.pack('<HH', frequency, duration_ms)
        success = self._send_packet(self.FUNC_SET_BUZZER, data)
        if success:
            print(f"Set buzzer: {frequency}Hz for {duration_ms}ms")
        return success
    
    def set_rgb_led(self, red: int, green: int, blue: int) -> bool:
        """Control RGB LED"""
        data = struct.pack('3B', red, green, blue)
        success = self._send_packet(self.FUNC_SET_RGB, data)
        if success:
            print(f"Set RGB LED: R={red}, G={green}, B={blue}")
        return success
    
    def read_angles(self) -> Optional[List[int]]:
        """Read current servo angles"""
        success = self._send_packet(self.FUNC_READ_ANGLE, b'')
        if success:
            print("Requested angle read")
            # Note: Response will be handled by _monitor_responses
        return None
    
    def _monitor_responses(self):
        """Monitor responses from the robotic hand"""
        while self.running and self.is_connected:
            try:
                if self.serial_connection.in_waiting:
                    response = self.serial_connection.readline().decode().strip()
                    if response:
                        print(f"Hand response: {response}")
                time.sleep(0.01)
            except Exception as e:
                print(f"Error monitoring responses: {e}")
                break
    
    def create_gesture(self, name: str, angles: List[int]):
        """Create a custom gesture"""
        if len(angles) != 6:
            print("Error: Must provide exactly 6 servo angles")
            return
        
        self.POSITIONS[name] = HandPosition.from_array(angles)
        print(f"Created gesture '{name}' with angles: {angles}")
    
    def smooth_move(self, target_position: HandPosition, steps: int = 10, delay: float = 0.1):
        """Smoothly move to target position"""
        start_position = self.current_position
        
        for i in range(steps + 1):
            # Interpolate between start and target
            progress = i / steps
            current_angles = []
            
            for start_angle, target_angle in zip(start_position.to_array(), target_position.to_array()):
                current_angle = int(start_angle + (target_angle - start_angle) * progress)
                current_angles.append(current_angle)
            
            self.set_servo_angles(current_angles)
            time.sleep(delay)
    
    def wave_gesture(self):
        """Perform a waving gesture"""
        print("Performing wave gesture...")
        
        # Move to open position
        self.move_to_position('open')
        time.sleep(1)
        
        # Wave motion
        for _ in range(3):
            self.set_servo_angles([90, 0, 45, 0, 0, 0])  # Wave position
            time.sleep(0.5)
            self.set_servo_angles([90, 0, 0, 0, 0, 0])   # Open position
            time.sleep(0.5)
        
        # Return to neutral
        self.move_to_position('neutral')
    
    def grasp_object(self, strength: int = 90):
        """Grasp an object with specified strength"""
        print(f"Grasping object with strength {strength}...")
        
        # Open hand
        self.move_to_position('open')
        time.sleep(1)
        
        # Close with specified strength
        grasp_angles = [90, strength, strength, strength, strength, strength]
        self.set_servo_angles(grasp_angles)
        time.sleep(1)
        
        # Hold for a moment
        time.sleep(2)
        
        # Release
        self.move_to_position('open')
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            'connected': self.is_connected,
            'port': self.port,
            'current_position': self.current_position.to_array(),
            'available_positions': list(self.POSITIONS.keys())
        }

def interactive_mode(controller: RoboticHandController):
    """Run interactive command mode"""
    print("\n=== Robotic Hand Controller - Interactive Mode ===")
    print("Type 'help' for available commands, 'quit' to exit")
    print("=" * 60)
    
    while True:
        try:
            command = input("hand> ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                break
            elif command == 'help':
                print_help()
            elif command == 'status':
                status = controller.get_status()
                print(f"Status: {status}")
            elif command.startswith('move '):
                position = command[5:]
                controller.move_to_position(position)
            elif command.startswith('angles '):
                try:
                    angles = [int(x) for x in command[7:].split()]
                    controller.set_servo_angles(angles)
                except ValueError:
                    print("Error: Please provide 6 integer angles (0-180)")
            elif command == 'wave':
                controller.wave_gesture()
            elif command.startswith('grasp '):
                try:
                    strength = int(command[6:])
                    controller.grasp_object(strength)
                except ValueError:
                    print("Error: Please provide a strength value (0-180)")
            elif command.startswith('buzzer '):
                try:
                    freq, duration = command[7:].split()
                    controller.set_buzzer(int(freq), int(duration))
                except ValueError:
                    print("Error: Please provide frequency and duration")
            elif command.startswith('rgb '):
                try:
                    r, g, b = command[4:].split()
                    controller.set_rgb_led(int(r), int(g), int(b))
                except ValueError:
                    print("Error: Please provide R G B values (0-255 each)")
            elif command == 'read':
                controller.read_angles()
            elif command == '':
                continue
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            print("\nExiting...")
            break

def print_help():
    """Print help information"""
    help_text = """
Available Commands:
  move <position>     - Move to predefined position (neutral, open, closed, etc.)
  angles <a1 a2 a3 a4 a5 a6> - Set specific servo angles
  wave               - Perform waving gesture
  grasp <strength>   - Grasp object with specified strength (0-180)
  buzzer <freq> <ms> - Control buzzer (frequency, duration)
  rgb <r> <g> <b>    - Control RGB LED (0-255 each)
  read               - Read current servo angles
  status             - Show current status
  help               - Show this help message
  quit               - Exit the program

Predefined Positions:
  neutral, open, closed, thumbs_up, peace, point, grasp
"""
    print(help_text)

def demo_mode(controller: RoboticHandController):
    """Run demo mode with automatic gestures"""
    print("\n=== Robotic Hand Demo Mode ===")
    print("Running automatic gesture sequence...")
    
    gestures = [
        ("Moving to neutral", lambda: controller.move_to_position('neutral')),
        ("Opening hand", lambda: controller.move_to_position('open')),
        ("Closing hand", lambda: controller.move_to_position('closed')),
        ("Thumbs up", lambda: controller.move_to_position('thumbs_up')),
        ("Peace sign", lambda: controller.move_to_position('peace')),
        ("Waving", controller.wave_gesture),
        ("Grasping object", lambda: controller.grasp_object(120)),
        ("Setting RGB to red", lambda: controller.set_rgb_led(255, 0, 0)),
        ("Setting RGB to green", lambda: controller.set_rgb_led(0, 255, 0)),
        ("Setting RGB to blue", lambda: controller.set_rgb_led(0, 0, 255)),
        ("Buzzer test", lambda: controller.set_buzzer(1000, 500)),
    ]
    
    for description, action in gestures:
        print(f"\n{description}...")
        action()
        time.sleep(1)
    
    print("\nDemo completed!")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Robotic Hand Controller")
    parser.add_argument("--port", "-p", help="Serial port (e.g., /dev/ttyUSB0, COM3)")
    parser.add_argument("--baud", "-b", type=int, default=9600, help="Baud rate (default: 9600)")
    parser.add_argument("--demo", "-d", action="store_true", help="Run demo mode")
    parser.add_argument("--position", help="Move to specific position")
    parser.add_argument("--angles", help="Set servo angles (comma-separated)")
    
    args = parser.parse_args()
    
    # Create controller
    controller = RoboticHandController(port=args.port, baud_rate=args.baud)
    
    # Connect to robotic hand
    if not controller.connect():
        print("Failed to connect to robotic hand. Please check:")
        print("1. Arduino is connected via USB")
        print("2. Correct port is specified")
        print("3. Robotic hand program is uploaded")
        return
    
    try:
        if args.position:
            # Move to specific position
            controller.move_to_position(args.position)
        elif args.angles:
            # Set specific angles
            try:
                angles = [int(x.strip()) for x in args.angles.split(',')]
                controller.set_servo_angles(angles)
            except ValueError:
                print("Error: Please provide 6 comma-separated angles")
        elif args.demo:
            # Demo mode
            demo_mode(controller)
        else:
            # Interactive mode
            interactive_mode(controller)
    
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()
