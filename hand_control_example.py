#!/usr/bin/env python3
"""
Robotic Hand Control Examples
Demonstrates various ways to control the robotic hand
"""

from robotic_hand_controller import RoboticHandController, HandPosition
import time

def basic_control_example():
    """Basic control example"""
    print("=== Basic Control Example ===")
    
    # Create controller (auto-detect port)
    controller = RoboticHandController()
    
    if not controller.connect():
        print("Failed to connect to robotic hand")
        return
    
    try:
        # Move to predefined positions
        print("Moving to neutral position...")
        controller.move_to_position('neutral')
        time.sleep(2)
        
        print("Opening hand...")
        controller.move_to_position('open')
        time.sleep(2)
        
        print("Closing hand...")
        controller.move_to_position('closed')
        time.sleep(2)
        
        # Set specific angles
        print("Setting custom angles...")
        custom_angles = [90, 45, 90, 90, 90, 90]
        controller.set_servo_angles(custom_angles)
        time.sleep(2)
        
    finally:
        controller.disconnect()

def gesture_sequence_example():
    """Gesture sequence example"""
    print("\n=== Gesture Sequence Example ===")
    
    controller = RoboticHandController()
    
    if not controller.connect():
        print("Failed to connect to robotic hand")
        return
    
    try:
        # Perform a sequence of gestures
        gestures = [
            ('neutral', 'Neutral position'),
            ('thumbs_up', 'Thumbs up'),
            ('peace', 'Peace sign'),
            ('point', 'Pointing'),
            ('open', 'Open hand'),
            ('closed', 'Closed hand'),
        ]
        
        for position, description in gestures:
            print(f"Performing: {description}")
            controller.move_to_position(position)
            time.sleep(2)
            
    finally:
        controller.disconnect()

def smooth_movement_example():
    """Smooth movement example"""
    print("\n=== Smooth Movement Example ===")
    
    controller = RoboticHandController()
    
    if not controller.connect():
        print("Failed to connect to robotic hand")
        return
    
    try:
        # Create custom positions
        start_pos = HandPosition(90, 0, 0, 0, 0, 0)    # Open
        end_pos = HandPosition(90, 180, 180, 180, 180, 180)  # Closed
        
        print("Smooth movement from open to closed...")
        controller.smooth_move(end_pos, steps=20, delay=0.1)
        
        print("Smooth movement back to open...")
        controller.smooth_move(start_pos, steps=20, delay=0.1)
        
    finally:
        controller.disconnect()

def interactive_control_example():
    """Interactive control example"""
    print("\n=== Interactive Control Example ===")
    
    controller = RoboticHandController()
    
    if not controller.connect():
        print("Failed to connect to robotic hand")
        return
    
    try:
        # Create custom gesture
        controller.create_gesture('custom_wave', [90, 0, 45, 0, 0, 0])
        
        # Perform waving gesture
        print("Performing custom wave gesture...")
        controller.wave_gesture()
        
        # Grasp object
        print("Grasping object...")
        controller.grasp_object(strength=120)
        
        # Control RGB LED
        print("Setting RGB LED colors...")
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
        ]
        
        for r, g, b in colors:
            controller.set_rgb_led(r, g, b)
            time.sleep(1)
        
        # Control buzzer
        print("Testing buzzer...")
        controller.set_buzzer(1000, 500)  # 1kHz for 500ms
        time.sleep(1)
        controller.set_buzzer(2000, 300)  # 2kHz for 300ms
        
    finally:
        controller.disconnect()

def programmatic_control_example():
    """Programmatic control example"""
    print("\n=== Programmatic Control Example ===")
    
    controller = RoboticHandController()
    
    if not controller.connect():
        print("Failed to connect to robotic hand")
        return
    
    try:
        # Create a complex movement sequence
        print("Executing complex movement sequence...")
        
        # Move to neutral
        controller.move_to_position('neutral')
        time.sleep(1)
        
        # Create a "counting" gesture (1-5 fingers)
        finger_sequences = [
            [90, 180, 0, 0, 0, 0],      # 1 finger
            [90, 180, 180, 0, 0, 0],    # 2 fingers
            [90, 180, 180, 180, 0, 0],  # 3 fingers
            [90, 180, 180, 180, 180, 0], # 4 fingers
            [90, 180, 180, 180, 180, 180], # 5 fingers
        ]
        
        for i, angles in enumerate(finger_sequences, 1):
            print(f"Showing {i} finger(s)...")
            controller.set_servo_angles(angles)
            time.sleep(1)
        
        # Return to neutral
        controller.move_to_position('neutral')
        
    finally:
        controller.disconnect()

def status_monitoring_example():
    """Status monitoring example"""
    print("\n=== Status Monitoring Example ===")
    
    controller = RoboticHandController()
    
    if not controller.connect():
        print("Failed to connect to robotic hand")
        return
    
    try:
        # Get initial status
        status = controller.get_status()
        print(f"Initial status: {status}")
        
        # Move to different positions and monitor
        positions = ['neutral', 'open', 'closed', 'thumbs_up']
        
        for position in positions:
            print(f"\nMoving to {position}...")
            controller.move_to_position(position)
            
            # Get updated status
            status = controller.get_status()
            print(f"Current position: {status['current_position']}")
            
            time.sleep(1)
        
    finally:
        controller.disconnect()

def main():
    """Run all examples"""
    print("Robotic Hand Control Examples")
    print("=" * 50)
    
    # Run examples
    basic_control_example()
    gesture_sequence_example()
    smooth_movement_example()
    interactive_control_example()
    programmatic_control_example()
    status_monitoring_example()
    
    print("\nAll examples completed!")

if __name__ == "__main__":
    main()
