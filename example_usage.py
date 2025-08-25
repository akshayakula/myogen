#!/usr/bin/env python3
"""
Example usage of Arduino Controller
Demonstrates programmatic control of Arduino Uno
"""

from arduino_controller import ArduinoController
import time

def basic_led_control():
    """Basic LED control example"""
    print("=== Basic LED Control Example ===")
    
    # Create controller (auto-detect port)
    controller = ArduinoController()
    
    if not controller.connect():
        print("Failed to connect to Arduino")
        return
    
    try:
        # Turn on LED
        print("Turning on LED...")
        print(controller.led_on())
        time.sleep(2)
        
        # Turn off LED
        print("Turning off LED...")
        print(controller.led_off())
        time.sleep(1)
        
        # Toggle LED
        print("Toggling LED...")
        print(controller.led_toggle())
        time.sleep(1)
        
    finally:
        controller.disconnect()

def sensor_monitoring():
    """Sensor monitoring example"""
    print("\n=== Sensor Monitoring Example ===")
    
    controller = ArduinoController()
    
    if not controller.connect():
        print("Failed to connect to Arduino")
        return
    
    try:
        # Monitor sensors for 10 seconds
        print("Monitoring sensors for 10 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            # Read potentiometer
            pot_response = controller.read_potentiometer()
            print(f"Potentiometer: {pot_response}")
            
            # Read temperature
            temp_response = controller.read_temperature()
            print(f"Temperature: {temp_response}")
            
            print("-" * 30)
            time.sleep(2)
            
    finally:
        controller.disconnect()

def led_pattern():
    """LED pattern example"""
    print("\n=== LED Pattern Example ===")
    
    controller = ArduinoController()
    
    if not controller.connect():
        print("Failed to connect to Arduino")
        return
    
    try:
        # Create a blinking pattern
        print("Creating LED blinking pattern...")
        
        for i in range(5):
            print(f"Blink {i+1}/5")
            controller.led_on()
            time.sleep(0.5)
            controller.led_off()
            time.sleep(0.5)
            
    finally:
        controller.disconnect()

def status_monitoring():
    """Status monitoring example"""
    print("\n=== Status Monitoring Example ===")
    
    controller = ArduinoController()
    
    if not controller.connect():
        print("Failed to connect to Arduino")
        return
    
    try:
        # Get initial status
        print("Initial status:")
        print(controller.read_status())
        
        # Change some states
        print("\nTurning on external LED...")
        controller.ext_led_on()
        time.sleep(1)
        
        print("\nUpdated status:")
        print(controller.read_status())
        
        # Turn off external LED
        controller.ext_led_off()
        
    finally:
        controller.disconnect()

def custom_command():
    """Custom command example"""
    print("\n=== Custom Command Example ===")
    
    controller = ArduinoController()
    
    if not controller.connect():
        print("Failed to connect to Arduino")
        return
    
    try:
        # Send custom commands
        commands = ["help", "status", "read_pot", "read_temp"]
        
        for cmd in commands:
            print(f"\nSending command: {cmd}")
            response = controller.send_command(cmd)
            print(f"Response: {response}")
            time.sleep(1)
            
    finally:
        controller.disconnect()

def main():
    """Run all examples"""
    print("Arduino Controller Examples")
    print("=" * 50)
    
    # Run examples
    basic_led_control()
    sensor_monitoring()
    led_pattern()
    status_monitoring()
    custom_command()
    
    print("\nAll examples completed!")

if __name__ == "__main__":
    main()

