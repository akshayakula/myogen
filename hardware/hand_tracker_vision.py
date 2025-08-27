#!/usr/bin/env python3
"""
Hand Tracking with Computer Vision
Tracks hand pose using MediaPipe and controls robotic hand via serial
Shows visualization window with hand landmarks
"""

import cv2
import mediapipe as mp
import numpy as np
import time
from typing import Optional, List, Tuple
from robotic_hand_controller import RoboticHandController
import argparse

class HandTracker:
    """Computer vision based hand tracking with MediaPipe"""
    
    def __init__(self, controller: Optional[RoboticHandController] = None):
        """Initialize hand tracker with MediaPipe"""
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize hand detection
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        self.controller = controller
        self.last_update_time = 0
        self.update_interval = 0.1  # Update servos every 100ms
        self.last_angles = [90, 90, 90, 90, 90, 90]  # Track last sent angles
        
    def calculate_finger_angles(self, hand_landmarks) -> List[int]:
        """
        Calculate servo angles from hand landmarks
        Returns list of 6 servo angles
        """
        # Get landmark positions
        landmarks = hand_landmarks.landmark
        
        # Calculate finger bend angles based on landmark distances and joint angles
        angles = []
        
        # Thumb - DISABLED (kept at safe position within 0-82° limit)
        thumb_angle = 90  # Keep thumb at 90° (disabled position, will be inverted to 90° by Arduino)
        angles.append(thumb_angle)
        
        # Improved finger angle calculation using joint bend ratios
        finger_configs = [
            # (tip_landmark, mcp_landmark, pip_landmark, name, min_angle, max_angle)
            (8, 5, 6, "Index", 0, 180),     # Index finger
            (12, 9, 10, "Middle", 0, 180),  # Middle finger  
            (16, 13, 14, "Ring", 25, 180),  # Ring finger (min 25°)
            (20, 17, 18, "Pinky", 0, 180), # Pinky finger
        ]
        
        for tip_id, mcp_id, pip_id, name, min_angle, max_angle in finger_configs:
            # Get 3D positions
            tip = np.array([landmarks[tip_id].x, landmarks[tip_id].y, landmarks[tip_id].z])
            mcp = np.array([landmarks[mcp_id].x, landmarks[mcp_id].y, landmarks[mcp_id].z])
            pip = np.array([landmarks[pip_id].x, landmarks[pip_id].y, landmarks[pip_id].z])
            
            # Calculate vectors
            mcp_to_pip = pip - mcp
            pip_to_tip = tip - pip
            
            # Calculate bend angle using dot product
            if np.linalg.norm(mcp_to_pip) > 0 and np.linalg.norm(pip_to_tip) > 0:
                cos_angle = np.dot(mcp_to_pip, pip_to_tip) / (np.linalg.norm(mcp_to_pip) * np.linalg.norm(pip_to_tip))
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                bend_angle = np.arccos(cos_angle)
                
                # Convert to servo angle (0° = straight, 180° = fully bent)
                # When finger is straight, bend_angle ≈ 0, so servo should be 0°
                # When finger is bent, bend_angle ≈ π, so servo should be 180°
                servo_angle = int(bend_angle * 180 / np.pi)
                
                # Apply smoothing and sensitivity adjustment
                servo_angle = int(servo_angle * 1.2)  # Increase sensitivity
                
                # Clamp to valid range
                servo_angle = max(min_angle, min(max_angle, servo_angle))
            else:
                # Fallback to distance-based calculation
                distance = np.linalg.norm(tip - mcp)
                servo_angle = int(max(0, min(180, (0.15 - distance) * 1200)))
                servo_angle = max(min_angle, min(max_angle, servo_angle))
            
            angles.append(servo_angle)
        
        # Wrist rotation (based on hand orientation)
        wrist_angle = 90  # Keep neutral for now (will be inverted to 90° by Arduino)
        angles.append(wrist_angle)
        
        return angles
    
    def draw_info_overlay(self, image, angles: List[int], fps: float):
        """Draw information overlay on the image"""
        height, width = image.shape[:2]
        
        # Create semi-transparent overlay
        overlay = image.copy()
        
        # Draw background rectangles
        cv2.rectangle(overlay, (10, 10), (300, 180), (0, 0, 0), -1)
        cv2.rectangle(overlay, (width - 150, 10), (width - 10, 60), (0, 0, 0), -1)
        
        # Blend overlay
        cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
        
        # Draw servo angles
        servo_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Wrist']
        y_pos = 35
        for i, (name, angle) in enumerate(zip(servo_names, angles)):
            if name == 'Thumb':
                # Show thumb as disabled
                text = f"{name}: DISABLED"
                cv2.putText(image, text, (20, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (128, 128, 128), 2)
                # Draw gray bar at disabled position (41° within 0-82° range)
                bar_width = int(41 * 250 / 180)
                cv2.rectangle(image, (20, y_pos + 5), (20 + bar_width, y_pos + 15), 
                             (128, 128, 128), -1)
                cv2.rectangle(image, (20, y_pos + 5), (270, y_pos + 15), 
                             (100, 100, 100), 1)
            else:
                text = f"{name}: {angle}°"
                cv2.putText(image, text, (20, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Draw angle bar
                bar_width = int(angle * 250 / 180)
                cv2.rectangle(image, (20, y_pos + 5), (20 + bar_width, y_pos + 15), 
                             (0, 255, 0), -1)
                cv2.rectangle(image, (20, y_pos + 5), (270, y_pos + 15), 
                             (100, 100, 100), 1)
            y_pos += 25
        
        # Draw FPS
        cv2.putText(image, f"FPS: {fps:.1f}", (width - 140, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw status
        if self.controller and self.controller.is_connected:
            status_text = "Arduino Connected"
            status_color = (0, 255, 0)
        else:
            status_text = "Simulation Mode (No Arduino)"
            status_color = (0, 165, 255)  # Orange color for simulation
        cv2.putText(image, status_text, (10, height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    
    def run(self):
        """Run hand tracking with visualization"""
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("Hand Tracking Started")
        print("Press 'q' to quit")
        print("Press 'c' to calibrate (center all servos)")
        print("Press 'o' to open hand")
        print("Press 'f' to make fist")
        
        prev_time = time.time()
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            
            # Process hand detection
            results = self.hands.process(rgb_frame)
            
            # Convert back to BGR for OpenCV
            rgb_frame.flags.writeable = True
            frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            
            # Calculate FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time)
            prev_time = curr_time
            
            # Default angles (neutral position)
            angles = [90, 90, 90, 90, 90, 90]
            
            # Draw hand landmarks and calculate angles
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks on frame
                    self.mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # Calculate servo angles
                    angles = self.calculate_finger_angles(hand_landmarks)
                    
                    # Send to robotic hand or print (rate limited)
                    if curr_time - self.last_update_time > self.update_interval:
                        if self.controller and self.controller.is_connected:
                            self.controller.set_servo_angles(angles)
                        else:
                            # Print servo commands when no Arduino connected
                            if angles != self.last_angles:
                                print(f"SERVO CMD: [Thumb:OFF Index:{angles[1]:3d}° Middle:{angles[2]:3d}° Ring:{angles[3]:3d}° Pinky:{angles[4]:3d}° Wrist:{angles[5]:3d}°]")
                                self.last_angles = angles.copy()
                        self.last_update_time = curr_time
            
            # Draw info overlay
            self.draw_info_overlay(frame, angles, fps)
            
            # Show frame
            cv2.imshow('Hand Tracking - Robotic Hand Controller', frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                # Calibrate - center all servos (respecting Arduino limits)
                if self.controller and self.controller.is_connected:
                    self.controller.set_servo_angles([90, 90, 90, 90, 90, 90])  # All neutral
                else:
                    print("SERVO CMD: [Thumb:OFF Index: 90° Middle: 90° Ring: 90° Pinky: 90° Wrist: 90°] (CALIBRATE)")
                print("Calibrated - all servos centered")
            elif key == ord('o'):
                # Open hand
                if self.controller and self.controller.is_connected:
                    self.controller.move_to_position('open')
                else:
                    print("SERVO CMD: [Thumb:OFF Index:  0° Middle:  0° Ring:  0° Pinky:  0° Wrist: 90°] (OPEN HAND)")
                print("Hand opened")
            elif key == ord('f'):
                # Make fist
                if self.controller and self.controller.is_connected:
                    self.controller.move_to_position('closed')
                else:
                    print("SERVO CMD: [Thumb:OFF Index:180° Middle:180° Ring:180° Pinky:180° Wrist: 90°] (CLOSED FIST)")
                print("Fist made")
        
        cap.release()
        cv2.destroyAllWindows()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Hand Tracking Vision Controller")
    parser.add_argument("--port", "-p", help="Serial port for Arduino")
    parser.add_argument("--no-arduino", action="store_true", 
                       help="Run without Arduino connection (visualization only)")
    parser.add_argument("--camera", "-c", type=int, default=0,
                       help="Camera index (default: 0)")
    
    args = parser.parse_args()
    
    controller = None
    
    if not args.no_arduino:
        # Initialize robotic hand controller
        controller = RoboticHandController(port=args.port)
        
        # Try to connect to Arduino
        if controller.connect():
            print("✓ Connected to robotic hand on", controller.port)
            print("✓ Sending servo commands to Arduino")
            # Move to neutral position
            controller.move_to_position('neutral')
        else:
            print("⚠ Arduino not detected - Running without hardware")
            print("⚠ Servo commands will be printed to console")
            controller = None
    else:
        print("Running in visualization-only mode (no Arduino)")
        print("Servo commands will be printed to console")
    
    print("\n" + "="*60)
    print("Hand Tracking Active - Controls:")
    print("  Q - Quit  |  C - Calibrate  |  O - Open  |  F - Fist")
    print("="*60 + "\n")
    
    # Create and run hand tracker
    tracker = HandTracker(controller)
    
    try:
        tracker.run()
    finally:
        if controller and controller.is_connected:
            print("\nDisconnecting from robotic hand...")
            controller.move_to_position('neutral')
            controller.disconnect()
        print("\nHand tracking stopped.")

if __name__ == "__main__":
    main()