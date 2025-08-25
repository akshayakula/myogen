#!/usr/bin/env python3
"""
Arduino Uno Controller
Python script to control Arduino Uno via serial communication
"""

import serial
import time
import sys
import threading
from typing import Optional

class ArduinoController:
    def __init__(self, port: str = None, baud_rate: int = 9600):
        """
        Initialize Arduino controller
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0' on Linux, 'COM3' on Windows)
            baud_rate: Serial communication baud rate
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """Connect to Arduino"""
        try:
            if self.port is None:
                # Try to auto-detect port
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                arduino_ports = [p.device for p in ports if 'Arduino' in p.description or 'CH340' in p.description]
                
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
            print(f"Connected to Arduino on {self.port}")
            return True
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.is_connected = False
        print("Disconnected from Arduino")
    
    def send_command(self, command: str) -> str:
        """
        Send command to Arduino and return response
        
        Args:
            command: Command to send
            
        Returns:
            Response from Arduino
        """
        if not self.is_connected:
            return "Not connected to Arduino"
        
        try:
            # Send command with newline
            self.serial_connection.write(f"{command}\n".encode())
            
            # Read response
            response = ""
            time.sleep(0.1)  # Small delay to allow Arduino to respond
            
            while self.serial_connection.in_waiting:
                line = self.serial_connection.readline().decode().strip()
                if line:
                    response += line + "\n"
            
            return response.strip() if response else "No response"
            
        except Exception as e:
            return f"Error sending command: {e}"
    
    def read_status(self) -> str:
        """Get current status from Arduino"""
        return self.send_command("status")
    
    def led_on(self) -> str:
        """Turn on built-in LED"""
        return self.send_command("led_on")
    
    def led_off(self) -> str:
        """Turn off built-in LED"""
        return self.send_command("led_off")
    
    def led_toggle(self) -> str:
        """Toggle built-in LED"""
        return self.send_command("led_toggle")
    
    def ext_led_on(self) -> str:
        """Turn on external LED"""
        return self.send_command("ext_led_on")
    
    def ext_led_off(self) -> str:
        """Turn off external LED"""
        return self.send_command("ext_led_off")
    
    def read_potentiometer(self) -> str:
        """Read potentiometer value"""
        return self.send_command("read_pot")
    
    def read_temperature(self) -> str:
        """Read temperature sensor"""
        return self.send_command("read_temp")
    
    def get_help(self) -> str:
        """Get help information"""
        return self.send_command("help")

def interactive_mode(controller: ArduinoController):
    """Run interactive command mode"""
    print("\n=== Arduino Controller - Interactive Mode ===")
    print("Type 'help' for available commands, 'quit' to exit")
    print("=" * 50)
    
    while True:
        try:
            command = input("arduino> ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                break
            elif command == 'help':
                print_help()
            elif command == 'status':
                print(controller.read_status())
            elif command == 'led_on':
                print(controller.led_on())
            elif command == 'led_off':
                print(controller.led_off())
            elif command == 'led_toggle':
                print(controller.led_toggle())
            elif command == 'ext_led_on':
                print(controller.ext_led_on())
            elif command == 'ext_led_off':
                print(controller.ext_led_off())
            elif command == 'read_pot':
                print(controller.read_potentiometer())
            elif command == 'read_temp':
                print(controller.read_temperature())
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
  led_on      - Turn on built-in LED
  led_off     - Turn off built-in LED
  led_toggle  - Toggle built-in LED
  ext_led_on  - Turn on external LED
  ext_led_off - Turn off external LED
  read_pot    - Read potentiometer value
  read_temp   - Read temperature sensor
  status      - Show all sensor values
  help        - Show this help message
  quit        - Exit the program
"""
    print(help_text)

def demo_mode(controller: ArduinoController):
    """Run demo mode with automatic commands"""
    print("\n=== Arduino Controller - Demo Mode ===")
    print("Running automatic demo sequence...")
    
    commands = [
        ("Turning on built-in LED", "led_on"),
        ("Reading potentiometer", "read_pot"),
        ("Reading temperature", "read_temp"),
        ("Getting status", "status"),
        ("Toggling LED", "led_toggle"),
        ("Turning off built-in LED", "led_off"),
    ]
    
    for description, command in commands:
        print(f"\n{description}...")
        response = controller.send_command(command)
        print(f"Response: {response}")
        time.sleep(1)
    
    print("\nDemo completed!")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Arduino Uno Controller")
    parser.add_argument("--port", "-p", help="Serial port (e.g., /dev/ttyUSB0, COM3)")
    parser.add_argument("--baud", "-b", type=int, default=9600, help="Baud rate (default: 9600)")
    parser.add_argument("--demo", "-d", action="store_true", help="Run demo mode")
    parser.add_argument("--command", "-c", help="Send single command and exit")
    
    args = parser.parse_args()
    
    # Create controller
    controller = ArduinoController(port=args.port, baud_rate=args.baud)
    
    # Connect to Arduino
    if not controller.connect():
        print("Failed to connect to Arduino. Please check:")
        print("1. Arduino is connected via USB")
        print("2. Correct port is specified")
        print("3. Arduino IDE is not using the serial port")
        sys.exit(1)
    
    try:
        if args.command:
            # Single command mode
            print(f"Sending command: {args.command}")
            response = controller.send_command(args.command)
            print(f"Response: {response}")
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

