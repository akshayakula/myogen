#!/usr/bin/env python3
"""
YOLO Webcam Scene Description Generator

Captures frames from webcam every 5 seconds, runs YOLO object detection,
and outputs scene descriptions in a specific format for AI training data.
"""

import cv2
import time
import argparse
from datetime import datetime
import numpy as np
from ultralytics import YOLO
import json
import os
import math

class YOLOWebcamDetector:
    def __init__(self, model_name="yolov8n.pt", confidence_threshold=0.5, exclude_classes=None):
        """
        Initialize YOLO webcam detector.
        
        Args:
            model_name: YOLO model to use (yolov8n.pt, yolov8s.pt, etc.)
            confidence_threshold: Minimum confidence for detections
            exclude_classes: Set of class names to exclude from detection
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.cap = None
        self.frame_count = 0
        
        # COCO class names (YOLO default) - excluding 'person' for object-only detection
        self.class_names = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
            'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
            'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
            'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
            'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
            'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
            'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
            'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
        
        # Classes to exclude from detection (default: exclude 'person')
        if exclude_classes is None:
            self.excluded_classes = {'person'}
        else:
            self.excluded_classes = set(exclude_classes)
        
    def load_model(self):
        """Load YOLO model."""
        print(f"Loading YOLO model: {self.model_name}")
        try:
            self.model = YOLO(self.model_name)
            print("✅ Model loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
        return True
    
    def initialize_camera(self, camera_index=0):
        """Initialize webcam."""
        print(f"Initializing camera {camera_index}...")
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            print(f"❌ Error: Could not open camera {camera_index}")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("✅ Camera initialized successfully!")
        return True
    
    def get_object_size(self, bbox, frame_shape):
        """Calculate object size using mathematical analysis."""
        x1, y1, x2, y2 = bbox
        bbox_width = x2 - x1
        bbox_height = y2 - y1
        
        # Calculate bounding box area
        bbox_area = bbox_width * bbox_height
        frame_area = frame_shape[1] * frame_shape[0]  # width x height
        
        # Calculate size ratio
        size_ratio = bbox_area / frame_area
        
        # Calculate diagonal for additional size metric
        diagonal = math.sqrt(bbox_width**2 + bbox_height**2)
        frame_diagonal = math.sqrt(frame_shape[1]**2 + frame_shape[0]**2)
        diagonal_ratio = diagonal / frame_diagonal
        
        # Use combined metrics for more accurate size classification
        combined_ratio = (size_ratio + diagonal_ratio) / 2
        
        if combined_ratio > 0.25:
            return "large"
        elif combined_ratio > 0.08:
            return "medium"
        else:
            return "small"
    
    def get_object_position(self, bbox, frame_shape):
        """Calculate object position using mathematical analysis."""
        x1, y1, x2, y2 = bbox
        
        # Calculate object center
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        frame_width, frame_height = frame_shape[1], frame_shape[0]
        frame_center_x = frame_width / 2
        frame_center_y = frame_height / 2
        
        # Calculate offset from frame center
        offset_x = center_x - frame_center_x
        offset_y = center_y - frame_center_y
        
        # Calculate distance from center using Euclidean distance
        distance_from_center = math.sqrt(offset_x**2 + offset_y**2)
        max_distance = math.sqrt(frame_center_x**2 + frame_center_y**2)
        distance_ratio = distance_from_center / max_distance
        
        # Horizontal position using mathematical thresholds
        h_threshold = frame_width * 0.15  # 15% threshold for center region
        if offset_x < -h_threshold:
            h_pos = "left"
        elif offset_x > h_threshold:
            h_pos = "right"
        else:
            h_pos = "center"
        
        # Vertical position using mathematical thresholds
        v_threshold = frame_height * 0.15  # 15% threshold for middle region
        if offset_y < -v_threshold:
            v_pos = "top"
        elif offset_y > v_threshold:
            v_pos = "bottom"
        else:
            v_pos = "middle"
        
        # Distance estimation using object size and position
        bbox_area = (x2 - x1) * (y2 - y1)
        frame_area = frame_width * frame_height
        size_ratio = bbox_area / frame_area
        
        # Combine size and position for distance estimation
        # Objects that are large and centered are likely close
        # Objects that are small and peripheral are likely far
        distance_score = size_ratio * (1 - distance_ratio * 0.5)
        
        # Use more descriptive distance terms
        if distance_score > 0.15:
            distance = "within reach"
        elif distance_score > 0.08:
            distance = "arm's-length"
        elif distance_score > 0.03:
            distance = "several feet away"
        else:
            distance = "across the room"
        
        return distance, h_pos, v_pos
    
    def get_object_orientation(self, bbox, frame_shape):
        """Calculate object orientation using mathematical analysis with realistic descriptions."""
        x1, y1, x2, y2 = bbox
        bbox_width = x2 - x1
        bbox_height = y2 - y1
        
        # Calculate aspect ratio
        aspect_ratio = bbox_width / bbox_height if bbox_height > 0 else 1
        
        # Calculate center position for context
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        frame_center_x = frame_shape[1] / 2
        frame_center_y = frame_shape[0] / 2
        
        # Calculate offset angles from center
        offset_x = center_x - frame_center_x
        offset_y = center_y - frame_center_y
        
        # Estimate rotation based on position and aspect ratio
        position_angle = math.atan2(offset_y, offset_x)
        position_angle_deg = math.degrees(position_angle)
        
        # Determine rotation intensity based on distance from center
        distance_from_center = math.sqrt(offset_x**2 + offset_y**2)
        max_distance = math.sqrt(frame_center_x**2 + frame_center_y**2)
        rotation_intensity = distance_from_center / max_distance
        
        # Generate realistic orientation descriptions
        rotation_descriptors = []
        
        # Determine rotation amount
        if rotation_intensity < 0.2:
            rotation_amount = "perfectly aligned"
        elif rotation_intensity < 0.4:
            rotation_amount = "slightly rotated"
        elif rotation_intensity < 0.7:
            rotation_amount = "moderately rotated"
        else:
            rotation_amount = "significantly rotated"
        
        # Determine primary axis based on aspect ratio and position
        if aspect_ratio > 1.6:  # Very wide object
            if abs(offset_x) > abs(offset_y):
                axis = "x-axis"
            else:
                axis = "z-axis"
        elif aspect_ratio < 0.6:  # Very tall object  
            if abs(offset_y) > abs(offset_x):
                axis = "y-axis"
            else:
                axis = "z-axis"
        else:  # Roughly square object
            # Use position to determine likely axis
            if abs(offset_x) > abs(offset_y):
                if offset_x > 0:
                    axis = "y-axis"
                else:
                    axis = "x-axis"
            else:
                if offset_y > 0:
                    axis = "x-axis"
                else:
                    axis = "y-axis"
        
        # Add subtle variations based on mathematical properties
        angle_variation = (position_angle_deg % 45) / 45.0
        aspect_factor = min(aspect_ratio, 1/aspect_ratio) if aspect_ratio > 0 else 1
        
        # Create more nuanced descriptions matching the example format
        if rotation_intensity < 0.15:
            orientation_options = ["upright", "perfectly aligned", "centered"]
            orientation = orientation_options[int(angle_variation * len(orientation_options))]
        elif rotation_intensity < 0.35:
            orientation_options = ["slightly rotated", "gently rotated", "subtly rotated"]
            orientation = orientation_options[int(angle_variation * len(orientation_options))]
        elif rotation_intensity < 0.65:
            orientation_options = ["moderately rotated", "rotated", "tilted"]
            orientation = orientation_options[int(angle_variation * len(orientation_options))]
        else:
            orientation_options = ["strongly rotated", "heavily rotated", "significantly rotated"]
            orientation = orientation_options[int(angle_variation * len(orientation_options))]
        
        # Add occasional directional modifiers for more realism
        if rotation_intensity > 0.3 and angle_variation > 0.6:
            direction_modifiers = ["clockwise", "counterclockwise", "diagonally"]
            direction = direction_modifiers[int((position_angle_deg % 120) / 40)]
            if "rotated" in orientation:
                orientation = f"{orientation} {direction}"
        
        return orientation, axis
    
    def format_scene_description(self, detections, frame_shape):
        """Format detections into scene description."""
        if not detections:
            return "Scene: No objects detected in the frame."
        
        descriptions = []
        
        for detection in detections:
            obj_name = detection['class_name']
            bbox = detection['bbox']
            confidence = detection['confidence']
            
            # Get object properties
            size_text = self.get_object_size(bbox, frame_shape)
            obj_dist, obj_lr, obj_ud = self.get_object_position(bbox, frame_shape)
            rot_text, axis_text = self.get_object_orientation(bbox, frame_shape)
            
            # Format description
            description = (
                f"Scene: A single everyday object is visible.\n"
                f"Object identity: {obj_name}.\n"
                f"Object size: {size_text}. Object position: {obj_dist}, {obj_lr}, {obj_ud} relative to the camera. "
                f"Object orientation: {rot_text} around the {axis_text}.\n"
            )
            
            descriptions.append(description)
        
        return "\n".join(descriptions)
    
    def process_frame(self, frame):
        """Process a single frame with YOLO, excluding specified classes."""
        if self.model is None:
            return []
        
        # Run YOLO detection
        results = self.model(frame, conf=self.confidence_threshold)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # Get class and confidence
                    class_id = int(box.cls[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    
                    if class_id < len(self.class_names):
                        class_name = self.class_names[class_id]
                        
                        # Skip excluded classes (like 'person')
                        if class_name not in self.excluded_classes:
                            detections.append({
                                'class_name': class_name,
                                'bbox': [x1, y1, x2, y2],
                                'confidence': confidence
                            })
        
        return detections
    
    def draw_detections(self, frame, detections):
        """Draw bounding boxes and labels on frame."""
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            
            # Draw bounding box
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(frame, label, (int(x1), int(y1) - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame
    
    def run_detection_loop(self, continuous=True, save_images=False, output_file=None):
        """
        Run the main detection loop continuously.
        
        Args:
            continuous: Run continuously (True) or with intervals (False)
            save_images: Whether to save detected frames
            output_file: File to save scene descriptions
        """
        if not self.load_model() or not self.initialize_camera():
            return
        
        print(f"\n🎥 Starting continuous detection loop")
        print("Press 'q' to quit, 's' to save current frame")
        print("=" * 50)
        
        output_lines = []
        frame_count = 0
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to read frame")
                    break
                
                frame_count += 1
                
                # Process every frame for continuous detection
                detections = self.process_frame(frame)
                
                # Only print if we have detections
                if detections:
                    # Get the most confident detection
                    best_detection = max(detections, key=lambda d: d['confidence'])
                    
                    # Calculate properties using math
                    raw_obj_name = best_detection['class_name']
                    bbox = best_detection['bbox']
                    
                    # Format object name with ID number (like 010_potted_meat_can)
                    # Generate a consistent ID based on object name hash
                    name_hash = hash(raw_obj_name) % 100
                    obj_name = f"{name_hash:03d}_{raw_obj_name.replace(' ', '_')}"
                    
                    size_text = self.get_object_size(bbox, frame.shape)
                    obj_dist, obj_lr, obj_ud = self.get_object_position(bbox, frame.shape)
                    rot_text, axis_text = self.get_object_orientation(bbox, frame.shape)
                    
                    # Format in the exact requested format
                    scene_description = (
                        f"Scene: A single everyday object is visible.\n"
                        f"Object identity: {obj_name}.\n"
                        f"Object size: {size_text}. Object position: {obj_dist}, {obj_lr}, {obj_ud} relative to the camera. "
                        f"Object orientation: {rot_text} around the {axis_text}.\n"
                    )
                    
                    # Print to console
                    print(f"\n[Frame {frame_count}] {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                    print(scene_description)
                    
                    # Save to output
                    if output_file:
                        output_lines.append(f"Frame: {frame_count} | Timestamp: {datetime.now().isoformat()}")
                        output_lines.append(scene_description)
                        output_lines.append("-" * 50)
                    
                    # Save image if requested
                    if save_images:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                        filename = f"detection_{timestamp}.jpg"
                        cv2.imwrite(filename, frame)
                
                # Draw detections on frame
                frame = self.draw_detections(frame, detections)
                
                # Add frame counter to display
                cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Show frame
                cv2.imshow('YOLO Continuous Detection', frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    # Save current frame
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"manual_save_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"💾 Manually saved: {filename}")
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.1)  # 100ms delay = ~10 FPS processing
        
        except KeyboardInterrupt:
            print("\n⏹️ Detection stopped by user")
        
        finally:
            # Cleanup
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            
            # Save output if requested
            if output_file and output_lines:
                with open(output_file, 'w') as f:
                    f.write('\n'.join(output_lines))
                print(f"💾 Saved scene descriptions to: {output_file}")
            
            print(f"\n📊 Total frames processed: {frame_count}")

def main():
    parser = argparse.ArgumentParser(description="YOLO Webcam Continuous Scene Description Generator")
    parser.add_argument("--model", default="yolov8n.pt", 
                       help="YOLO model to use (default: yolov8n.pt)")
    parser.add_argument("--camera", type=int, default=0, 
                       help="Camera index (default: 0)")
    parser.add_argument("--confidence", type=float, default=0.5, 
                       help="Confidence threshold (default: 0.5)")
    parser.add_argument("--save-images", action="store_true", 
                       help="Save detected frames as images")
    parser.add_argument("--output", type=str, 
                       help="Output file for scene descriptions")
    parser.add_argument("--exclude", nargs="*", default=["person"],
                       help="Classes to exclude from detection (default: person)")
    parser.add_argument("--include-person", action="store_true",
                       help="Include person detection (overrides --exclude person)")
    
    args = parser.parse_args()
    
    # Handle person inclusion/exclusion
    excluded_classes = set(args.exclude) if args.exclude else set()
    if args.include_person and "person" in excluded_classes:
        excluded_classes.remove("person")
    
    print("🎯 YOLO Continuous Scene Description Generator")
    print("=" * 50)
    print("Features:")
    print("• Continuous real-time object detection")
    print("• Mathematical analysis of size, position, and orientation")
    print("• Live console output in specified format")
    print("• Frame counter and timestamp")
    print(f"• Using model: {args.model}")
    print(f"• Confidence threshold: {args.confidence}")
    print(f"• Excluded classes: {', '.join(excluded_classes) if excluded_classes else 'None'}")
    print("=" * 50)
    
    # Create detector
    detector = YOLOWebcamDetector(
        model_name=args.model,
        confidence_threshold=args.confidence,
        exclude_classes=excluded_classes
    )
    
    # Run continuous detection loop
    detector.run_detection_loop(
        continuous=True,
        save_images=args.save_images,
        output_file=args.output
    )

if __name__ == "__main__":
    main()
