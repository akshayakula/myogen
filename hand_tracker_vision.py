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
        
    def calculate_finger_angles(self, hand_landmarks) -> List[int]:
        """
        Calculate servo angles from hand landmarks
        Returns list of 6 servo angles
        """
        # Get landmark positions
        landmarks = hand_landmarks.landmark
        
        # Calculate finger bend angles based on landmark distances
        angles = []
        
        # Thumb (landmarks 0, 1, 2, 3, 4)
        thumb_tip = np.array([landmarks[4].x, landmarks[4].y, landmarks[4].z])
        thumb_base = np.array([landmarks[2].x, landmarks[2].y, landmarks[2].z])
        thumb_bend = np.linalg.norm(thumb_tip - thumb_base)
        thumb_angle = int(180 - thumb_bend * 500)  # Scale to servo range
        thumb_angle = max(0, min(180, thumb_angle))
        angles.append(thumb_angle)
        
        # Index finger (landmarks 5, 6, 7, 8)
        index_tip = np.array([landmarks[8].x, landmarks[8].y, landmarks[8].z])
        index_base = np.array([landmarks[5].x, landmarks[5].y, landmarks[5].z])
        index_bend = np.linalg.norm(index_tip - index_base)
        index_angle = int(180 - index_bend * 400)
        index_angle = max(0, min(180, index_angle))
        angles.append(index_angle)
        
        # Middle finger (landmarks 9, 10, 11, 12)
        middle_tip = np.array([landmarks[12].x, landmarks[12].y, landmarks[12].z])
        middle_base = np.array([landmarks[9].x, landmarks[9].y, landmarks[9].z])
        middle_bend = np.linalg.norm(middle_tip - middle_base)
        middle_angle = int(180 - middle_bend * 400)
        middle_angle = max(0, min(180, middle_angle))
        angles.append(middle_angle)
        
        # Ring finger (landmarks 13, 14, 15, 16)
        ring_tip = np.array([landmarks[16].x, landmarks[16].y, landmarks[16].z])
        ring_base = np.array([landmarks[13].x, landmarks[13].y, landmarks[13].z])
        ring_bend = np.linalg.norm(ring_tip - ring_base)
        ring_angle = int(180 - ring_bend * 400)
        ring_angle = max(25, min(180, ring_angle))  # Ring finger min is 25
        angles.append(ring_angle)
        
        # Pinky finger (landmarks 17, 18, 19, 20)
        pinky_tip = np.array([landmarks[20].x, landmarks[20].y, landmarks[20].z])
        pinky_base = np.array([landmarks[17].x, landmarks[17].y, landmarks[17].z])
        pinky_bend = np.linalg.norm(pinky_tip - pinky_base)
        pinky_angle = int(180 - pinky_bend * 400)
        pinky_angle = max(0, min(180, pinky_angle))
        angles.append(pinky_angle)
        
        # Wrist rotation (based on hand orientation)
        wrist_angle = 90  # Keep neutral for now
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
        status_text = "Connected" if self.controller and self.controller.is_connected else "Disconnected"
        status_color = (0, 255, 0) if self.controller and self.controller.is_connected else (0, 0, 255)
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
                    
                    # Send to robotic hand (rate limited)
                    if self.controller and self.controller.is_connected:
                        if curr_time - self.last_update_time > self.update_interval:
                            self.controller.set_servo_angles(angles)
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
                # Calibrate - center all servos
                if self.controller and self.controller.is_connected:
                    self.controller.set_servo_angles([90, 90, 90, 90, 90, 90])
                    print("Calibrated - all servos centered")
            elif key == ord('o'):
                # Open hand
                if self.controller and self.controller.is_connected:
                    self.controller.move_to_position('open')
                    print("Hand opened")
            elif key == ord('f'):
                # Make fist
                if self.controller and self.controller.is_connected:
                    self.controller.move_to_position('closed')
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
        
        # Connect to Arduino
        if controller.connect():
            print("Connected to robotic hand")
            # Move to neutral position
            controller.move_to_position('neutral')
        else:
            print("Failed to connect to Arduino")
            print("Running in visualization-only mode")
            controller = None
    else:
        print("Running in visualization-only mode (no Arduino)")
    
    # Create and run hand tracker
    tracker = HandTracker(controller)
    
    try:
        tracker.run()
    finally:
        if controller:
            print("Disconnecting from robotic hand...")
            controller.move_to_position('neutral')
            controller.disconnect()

if __name__ == "__main__":
    main()