#!/usr/bin/env python3
"""
YOLO Webcam Scene Description Generator with BLE Pose Sending

Captures frames from webcam, runs YOLO object detection,
generates scene descriptions, sends to LLM API for finger curl predictions,
and sends poses directly to robotic hand via BLE.
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
import asyncio
import subprocess
import re
from typing import List, Dict, Optional

# BLE and pose sending imports
try:
    from bleak import BleakClient, BleakScanner
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False
    print("⚠️ BLE not available - poses will be simulated")

# BLE Constants from ble_pose_sender.py
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_MAC = "8EE2E4F9-42E6-5BE3-4E2A-A706CAD38879"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Protocol constants
FRAME_HEADER = 0x55
CMD_SERVO_MOVE = 0x03

class YOLOWebcamDetector:
    def __init__(self, model_name="yolov8n.pt", confidence_threshold=0.5, exclude_classes=None, 
                 enable_llm_api=False, api_url=None):
        """
        Initialize YOLO webcam detector with BLE pose sending capability.
        
        Args:
            model_name: YOLO model to use (yolov8n.pt, yolov8s.pt, etc.)
            confidence_threshold: Minimum confidence for detections
            exclude_classes: Set of class names to exclude from detection
            enable_llm_api: Enable LLM API calls for finger curl predictions
            api_url: LLM API endpoint URL
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.cap = None
        self.frame_count = 0
        
        # LLM API settings
        self.enable_llm_api = enable_llm_api
        self.api_url = api_url or "https://6kazu8ogvih4cs-8080.proxy.runpod.net/generate"
        
        # BLE connection variables
        self.ble_client = None
        self.ble_write_char = None
        self.is_ble_connected = False
        self.last_api_call_time = 0
        self.api_cooldown = 5.0  # 5 seconds between API calls
        self.api_request_active = False  # Flag to prevent concurrent API requests
        self.current_object = None  # Track the current object being processed
        
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
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        
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
    
    # BLE and pose sending methods
    async def scan_for_hiwonder(self) -> bool:
        """Scan for Hiwonder BLE device"""
        print("🔍 Scanning for Hiwonder BLE device...")
        try:
            devices = await BleakScanner.discover(timeout=10.0)
            print(f"📱 Found {len(devices)} BLE devices")
            
            hiwonder_found = False
            for device in devices:
                is_hiwonder = (device.name == HIWONDER_DEVICE_NAME or 
                              device.address == HIWONDER_MAC or 
                              (device.name and "hiwonder" in device.name.lower()))
                
                if is_hiwonder:
                    rssi = getattr(device, 'rssi', 'N/A')
                    print(f"🎯 Found Hiwonder BLE device: {device.name} ({device.address}) RSSI: {rssi}dBm")
                    hiwonder_found = True
                    break
            
            if not hiwonder_found:
                print(f"❌ Hiwonder device not found in scan")
                print(f"💡 Scanned {len(devices)} devices")
            
            return hiwonder_found
            
        except Exception as e:
            print(f"❌ BLE scan failed: {e}")
            return False

    async def connect_to_ble(self):
        """Connect to Hiwonder BLE device using proven logic from ble_pose_sender"""
        if not BLE_AVAILABLE:
            print("⚠️ BLE not available, poses will be simulated")
            return False
        
        # First scan for the device
        print("🔗 Testing connection to Hiwonder BLE device...")
        device_found = await self.scan_for_hiwonder()
        if not device_found:
            return False
            
        try:
            # Try to connect using MAC address (same as ble_pose_sender)
            print(f"📞 Attempting connection to {HIWONDER_MAC}...")
            self.ble_client = BleakClient(HIWONDER_MAC)
            await self.ble_client.connect()
            
            if self.ble_client.is_connected:
                print("🎉 SUCCESS! Connected to Hiwonder BLE device!")
                
                # List services (same as ble_pose_sender)
                services = self.ble_client.services
                service_list = list(services)
                print(f"📋 Found {len(service_list)} services")
                
                target_service = None
                target_char = None
                
                for service in services:
                    if service.uuid.lower() == HIWONDER_SERVICE_UUID.lower():
                        target_service = service
                        print(f"✅ Found target service: {service.uuid}")
                    
                    for char in service.characteristics:
                        if char.uuid.lower() == HIWONDER_WRITE_CHAR_UUID.lower():
                            target_char = char
                            print(f"✅ Found write characteristic: {char.uuid}")
                            break
                
                if target_service and target_char:
                    self.ble_write_char = target_char  # Store the characteristic object
                    self.is_ble_connected = True
                    print("🤖 Ready for servo control!")
                    return True
                else:
                    print("❌ Required services/characteristics not found")
                    await self.ble_client.disconnect()
                    return False
            else:
                print("❌ Connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            if self.ble_client:
                try:
                    await self.ble_client.disconnect()
                except:
                    pass
            return False
    
    def angle_to_position(self, angle: int) -> int:
        """Convert 0-180 angle to Hiwonder servo position (1100-1950)"""
        return int(1100 + (angle / 180.0) * (1950 - 1100))
    
    def build_servo_packet(self, servo_angles: List[int], time_ms: int = 1000) -> bytearray:
        """Build servo control packet using Hiwonder protocol"""
        packet = bytearray()
        
        # Frame header
        packet.append(FRAME_HEADER)
        packet.append(FRAME_HEADER)
        
        # Data length
        servo_count = len(servo_angles)
        data_bytes = 1 + 1 + 2 + (servo_count * 3)
        packet.append(data_bytes)
        
        # Function and servo count
        packet.append(CMD_SERVO_MOVE)
        packet.append(servo_count)
        
        # Time (little endian)
        packet.append(time_ms & 0xFF)
        packet.append((time_ms >> 8) & 0xFF)
        
        # Servo data
        for i, angle in enumerate(servo_angles):
            position = self.angle_to_position(angle)
            packet.append(i + 1)  # Servo ID (1-6)
            packet.append(position & 0xFF)
            packet.append((position >> 8) & 0xFF)
        
        return packet
    
    async def send_pose_to_hand(self, servo_angles: List[int]) -> bool:
        """Send servo angles to robotic hand via BLE"""
        print(f"🤖 Sending to Arduino: {servo_angles}")
        
        if not self.is_ble_connected or not self.ble_client or not self.ble_client.is_connected:
            if not BLE_AVAILABLE:
                print("   (BLE library not available)")
            else:
                print("   (BLE not connected - check if Arduino is powered on)")
            return True
        
        try:
            packet = self.build_servo_packet(servo_angles)
            await self.ble_client.write_gatt_char(self.ble_write_char, packet, response=False)
            print("   ✅ Sent via BLE")
            return True
        except Exception as e:
            print(f"   ❌ BLE error: {e}")
            self.is_ble_connected = False
            return False
    
    async def get_llm_prediction(self, scene_description: str) -> Optional[List[int]]:
        """Get finger curl prediction from LLM API"""
        if not self.enable_llm_api:
            return None
        
        try:
            # Set flag to indicate API request is active
            self.api_request_active = True
            
            # Prepare API request
            json_data = {
                "prompt": f"{scene_description}\nTask: Output only the finger curls in this exact format:\npinky: <no curl|half curl|full curl>; ring: <no curl|half curl|full curl>; middle: <no curl|half curl|full curl>; index: <no curl|half curl|full curl>; thumb: <no curl|half curl|full curl>\nDo not add any extra words.",
                "max_new_tokens": 500,
                "temperature": 1.5,
                "top_p": 0.95,
                "top_k": 50,
                "do_sample": True,
                "repetition_penalty": 1.0,
                "stop": ["\n"]
            }
            
            # Show what prompt we're sending to LLM
            print(f"📝 Prompt sent to LLM:")
            print(f"   {scene_description.strip()}")
            
            # Make curl request
            curl_script = f'''curl -sS -X POST "{self.api_url}" -H "Content-Type: application/json" --data '{json.dumps(json_data)}' '''
            
            process = await asyncio.create_subprocess_shell(
                curl_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            self.last_api_call_time = time.time()
            
            if process.returncode == 0:
                response = stdout.decode().strip()
                print(f"📤 API Response: {response}")
                # Parse response to servo angles
                servo_angles = self.parse_llm_response_to_servo_angles(response)
                return servo_angles
            else:
                # API failed - clear current object so we can retry
                self.current_object = None
                return None
                
        except asyncio.TimeoutError:
            # Timeout - clear current object so we can retry
            self.current_object = None
            return None
        except Exception as e:
            # Error - clear current object so we can retry
            self.current_object = None
            return None
        finally:
            # Always clear the flag when request completes (success or failure)
            self.api_request_active = False
    
    def parse_llm_response_to_servo_angles(self, response: str) -> List[int]:
        """Parse LLM response to servo angles"""
        curl_to_numeric = {'full curl': 0, 'half curl': 1, 'no curl': 2}
        default_array = [1, 1, 1, 1, 1]  # Default neutral
        
        try:
            # Handle JSON response
            if response and response.strip().startswith('{'):
                response_data = json.loads(response)
                text = response_data.get('response', response_data.get('text', response))
            else:
                text = response or ""
            
            # Parse finger curls
            finger_pattern = r'(pinky|ring|middle|index|thumb):\s*(no curl|half curl|full curl)'
            matches = re.findall(finger_pattern, text.lower())
            
            if matches:
                finger_curls = {finger: curl for finger, curl in matches}
                finger_order = ['pinky', 'ring', 'middle', 'index', 'thumb']
                numeric_array = [curl_to_numeric.get(finger_curls.get(finger, 'half curl'), 1) 
                               for finger in finger_order]
                pass  # Successfully parsed
            else:
                numeric_array = default_array
            
            # Convert to servo angles using the same logic as ble_pose_sender.py
            servo_angles = self.convert_numeric_to_servo_angles(numeric_array)
            return servo_angles
            
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return self.convert_numeric_to_servo_angles(default_array)
    
    def convert_numeric_to_servo_angles(self, numeric_array: List[int]) -> List[int]:
        """Convert numeric array [0-2] to servo angles"""
        numeric_to_curl = {0: "full curl", 1: "half curl", 2: "no curl"}
        curl_states = [numeric_to_curl.get(val, "half curl") for val in numeric_array]
        
        CURL_TO_ANGLE = {
            'thumb': {'no curl': 0, 'half curl': 90, 'full curl': 180},
            'index': {'no curl': 180, 'half curl': 90, 'full curl': 0},
            'middle': {'no curl': 180, 'half curl': 90, 'full curl': 0},
            'ring': {'no curl': 180, 'half curl': 100, 'full curl': 25},
            'pinky': {'no curl': 180, 'half curl': 90, 'full curl': 0}
        }
        
        finger_names = ['pinky', 'ring', 'middle', 'index', 'thumb']
        finger_angles = {}
        
        for i, curl in enumerate(curl_states):
            finger = finger_names[i]
            finger_angles[finger] = CURL_TO_ANGLE[finger][curl]
        
        return [
            finger_angles['thumb'],
            finger_angles['index'], 
            finger_angles['middle'],
            finger_angles['ring'],
            finger_angles['pinky'],
            90  # wrist
        ]
    
    async def disconnect_ble(self):
        """Disconnect from BLE device"""
        if self.ble_client and self.ble_client.is_connected:
            try:
                await self.ble_client.disconnect()
                print("📶 Disconnected from BLE device")
            except Exception as e:
                print(f"⚠️ BLE disconnect error: {e}")
        self.is_ble_connected = False
    
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
    
    async def run_detection_loop(self, continuous=True, save_images=False, output_file=None):
        """
        Run the main detection loop continuously with LLM API integration and BLE pose sending.
        
        Args:
            continuous: Run continuously (True) or with intervals (False)
            save_images: Whether to save detected frames
            output_file: File to save scene descriptions
        """
        if not self.load_model() or not self.initialize_camera():
            return
        
        # Connect to BLE device if LLM API is enabled
        if self.enable_llm_api:
            await self.connect_to_ble()
        
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
                    
                    # Get LLM prediction and send to robotic hand
                    if self.enable_llm_api:
                        # Check if object has changed or if no API request is active
                        if not self.api_request_active and raw_obj_name != self.current_object:
                            self.current_object = raw_obj_name
                            servo_angles = await self.get_llm_prediction(scene_description)
                            if servo_angles:
                                await self.send_pose_to_hand(servo_angles)
                    
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
            
            # Disconnect BLE
            if self.enable_llm_api:
                await self.disconnect_ble()
            
            # Save output if requested
            if output_file and output_lines:
                with open(output_file, 'w') as f:
                    f.write('\n'.join(output_lines))
                print(f"💾 Saved scene descriptions to: {output_file}")
            
            print(f"\n📊 Total frames processed: {frame_count}")

async def main():
    parser = argparse.ArgumentParser(description="YOLO Webcam Scene Description Generator with BLE Pose Sending")
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
    parser.add_argument("--enable-llm", action="store_true",
                       help="Enable LLM API calls for finger curl predictions")
    parser.add_argument("--api-url", type=str,
                       help="LLM API endpoint URL (default: RunPod endpoint)")
    parser.add_argument("--api-cooldown", type=float, default=5.0,
                       help="Seconds between API calls (default: 5.0)")
    
    args = parser.parse_args()
    
    # Handle person inclusion/exclusion
    excluded_classes = set(args.exclude) if args.exclude else set()
    if args.include_person and "person" in excluded_classes:
        excluded_classes.remove("person")
    
    print("🎯 YOLO Scene Description Generator with BLE Pose Sending")
    print("=" * 60)
    print("Features:")
    print("• Continuous real-time object detection")
    print("• Mathematical analysis of size, position, and orientation")
    print("• Minimal console logging (only shows detections and poses)")
    print("• Frame counter and timestamp")
    print(f"• Using model: {args.model}")
    print(f"• Confidence threshold: {args.confidence}")
    print(f"• Excluded classes: {', '.join(excluded_classes) if excluded_classes else 'None'}")
    if args.enable_llm:
        print("• ✅ LLM API integration enabled")
        print("• ✅ BLE pose sending to robotic hand")
        print(f"• API cooldown: {args.api_cooldown} seconds")
    else:
        print("• ❌ LLM API integration disabled")
    print("=" * 60)
    
    # Create detector
    detector = YOLOWebcamDetector(
        model_name=args.model,
        confidence_threshold=args.confidence,
        exclude_classes=excluded_classes,
        enable_llm_api=args.enable_llm,
        api_url=args.api_url
    )
    
    # Set API cooldown
    detector.api_cooldown = args.api_cooldown
    
    # Run continuous detection loop
    await detector.run_detection_loop(
        continuous=True,
        save_images=args.save_images,
        output_file=args.output
    )

if __name__ == "__main__":
    asyncio.run(main())
