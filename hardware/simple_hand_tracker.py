#!/usr/bin/env python3
"""
Simple Hand Tracker with Servo Control
Non-object-oriented hand tracking that controls robotic hand via serial
Uses the same protocol as simple_servo_control.py
"""

import cv2
import mediapipe as mp
import numpy as np
import serial
import serial.tools.list_ports
import struct
import time
import asyncio
from typing import List, Tuple, Optional

# Screen capture support using Quartz (macOS native)
try:
    import Quartz
    import tkinter as tk
    from tkinter import messagebox
    SCREEN_CAPTURE_AVAILABLE = True
    QUARTZ_AVAILABLE = True
except ImportError:
    try:
        import mss
        import tkinter as tk
        from tkinter import messagebox
        SCREEN_CAPTURE_AVAILABLE = True
        QUARTZ_AVAILABLE = False
    except ImportError:
        SCREEN_CAPTURE_AVAILABLE = False
        QUARTZ_AVAILABLE = False

# Window capture support (cross-platform)
try:
    import subprocess
    import json
    import pygetwindow as gw
    WINDOW_CAPTURE_AVAILABLE = True
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    try:
        import subprocess
        import json
        WINDOW_CAPTURE_AVAILABLE = True
        PYGETWINDOW_AVAILABLE = False
    except ImportError:
        WINDOW_CAPTURE_AVAILABLE = False
        PYGETWINDOW_AVAILABLE = False

# BLE support
try:
    from bleak import BleakClient, BleakScanner
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False

# Official Hiwonder Protocol constants
FRAME_HEADER = 0x55
CMD_SERVO_MOVE = 0x03

# Global variables
serial_connection = None
ble_client = None
ble_write_char = None
is_ble_connected = False
servo_angles = [90, 90, 90, 90, 90, 90]  # Current servo angles (sent to Arduino)
target_angles = [90, 90, 90, 90, 90, 90]  # Target angles (from hand detection)
smoothed_angles = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0]  # Smoothed angles (float for precision)
last_update_time = 0
update_interval = 0.02  # Update servos every 20ms (50Hz)

# Screen capture variables
screen_capture_region = None  # (x, y, width, height) for screen capture
use_screen_capture = False
sct = None
tracked_window_info = None  # Store window info for real-time tracking

# Hiwonder BLE device constants (from our scan)
HIWONDER_DEVICE_NAME = "Hiwonder"
HIWONDER_MAC = "8EE2E4F9-42E6-5BE3-4E2A-A706CAD38879"
HIWONDER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
HIWONDER_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Smoothing parameters
smoothing_factor = 0.225  # How fast to move toward target (0.05 = very slow, 0.15 = fast) - 10% slower
min_change_threshold = 1  # Only send to Arduino if change >= 1 degree

# Dynamic servo limits (will be set during calibration)
servo_limits = [(0, 180), (0, 180), (0, 180), (25, 180), (0, 180), (0, 180)]  # Default limits - Thumb matches Arduino sketch (0-180°)
servo_names = ["Thumb", "Index", "Middle", "Ring", "Pinky", "Wrist"]

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def get_window_list() -> List[dict]:
    """Get list of all windows using Quartz (macOS native)"""
    if not WINDOW_CAPTURE_AVAILABLE:
        return []
    
    windows = []
    
    # Try Quartz first (macOS native - best performance)
    if QUARTZ_AVAILABLE:
        try:
            # Get all window info using Quartz
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID
            )
            
            for window_info in window_list:
                # Get window properties
                window_id = window_info.get('kCGWindowNumber', 0)
                window_name = window_info.get('kCGWindowName', '')
                app_name = window_info.get('kCGWindowOwnerName', '')
                bounds = window_info.get('kCGWindowBounds', {})
                layer = window_info.get('kCGWindowLayer', 0)
                
                # Filter out system windows and get only user windows
                if (window_name and app_name and 
                    layer == 0 and  # Normal window layer
                    bounds.get('Width', 0) > 50 and bounds.get('Height', 0) > 50 and
                    'Menubar' not in app_name and 'Dock' not in app_name):
                    
                    windows.append({
                        'id': window_id,
                        'title': window_name,
                        'app': app_name,
                        'frame': {
                            'x': int(bounds.get('X', 0)),
                            'y': int(bounds.get('Y', 0)),
                            'w': int(bounds.get('Width', 0)),
                            'h': int(bounds.get('Height', 0))
                        },
                        'quartz_info': window_info
                    })
            
            if windows:
                print(f"✅ Found {len(windows)} windows using Quartz")
                return windows
                
        except Exception as e:
            print(f"Warning: Quartz failed: {e}")
    
    # Fallback to yabai if available
    try:
        result = subprocess.run(['yabai', '-m', 'query', '--windows'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            yabai_windows = json.loads(result.stdout)
            windows = [{'id': w['id'], 'title': w['title'], 'app': w['app'], 
                      'frame': w['frame']} for w in yabai_windows if w.get('title')]
            if windows:
                print(f"✅ Found {len(windows)} windows using yabai")
                return windows
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Final fallback to AppleScript
    try:
        result = subprocess.run(['osascript', '-e', '''
            tell application "System Events"
                set windowList to {}
                repeat with proc in (every process whose background only is false)
                    try
                        repeat with win in (every window of proc)
                            set windowList to windowList & {name of proc & " - " & name of win}
                        end repeat
                    end try
                end repeat
                return windowList
            end tell
        '''], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            window_names = result.stdout.strip().split(', ')
            windows = [{'id': i, 'title': name.strip(), 'app': name.split(' - ')[0], 
                      'frame': None} for i, name in enumerate(window_names) if name.strip()]
            if windows:
                print(f"✅ Found {len(windows)} windows using AppleScript")
                return windows
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ No windows found with any method")
    return []

def find_video_call_window(windows: List[dict]) -> Optional[dict]:
    """Find a video call window automatically"""
    video_call_keywords = [
        'zoom', 'meeting', 'facetime', 'teams', 'skype', 'discord', 'webex',
        'hangouts', 'meet', 'call', 'conference', 'video', 'whatsapp',
        'messenger', 'telegram', 'signal', 'slack call', 'gotomeeting',
        'bluejeans', 'jitsi', 'whereby', 'around', 'mmhmm'
    ]
    
    # Exclude our own window to prevent infinite loops
    excluded_keywords = ['hand tracker', 'simple hand tracker', 'robotic hand control']
    
    for window in windows:
        window_text = f"{window['app']} {window['title']}".lower()
        
        # Skip our own tracking window to prevent feedback loops
        is_excluded = any(excluded in window_text for excluded in excluded_keywords)
        if is_excluded:
            continue
            
        for keyword in video_call_keywords:
            if keyword in window_text:
                return window
    
    return None

def select_window() -> Optional[Tuple[int, int, int, int]]:
    """Allow user to select a specific window for capture"""
    global tracked_window_info
    
    if not WINDOW_CAPTURE_AVAILABLE:
        print("❌ Window capture not available on this system")
        return None
    
    print("\n🪟 Window Selection")
    print("Scanning for windows...")
    
    windows = get_window_list()
    if not windows:
        print("❌ No windows found or window detection failed")
        print("💡 Falling back to manual region selection...")
        return select_screen_region()
    
    # Check for video call windows first
    video_call_window = find_video_call_window(windows)
    if video_call_window:
        print(f"📞 Auto-detected video call: {video_call_window['app']} - {video_call_window['title']}")
        print("🎯 Automatically selecting this window for hand tracking!")
        
        # Store window info for tracking
        tracked_window_info = {
            'app': video_call_window['app'],
            'title': video_call_window['title'], 
            'id': video_call_window.get('id'),
            'track_window': True,
            'frame_count': 0
        }
        
        # If we have frame info (from pygetwindow, yabai, etc), use it
        if video_call_window.get('frame'):
            frame = video_call_window['frame']
            bounds = (int(frame['x']), int(frame['y']), 
                     int(frame['w']), int(frame['h']))
            tracked_window_info['last_bounds'] = bounds
            return bounds
        else:
            # For AppleScript results, we need to get window bounds
            bounds = get_window_bounds(video_call_window['title'])
            if bounds:
                tracked_window_info['last_bounds'] = bounds
            return bounds
    
    print("\n📋 Available Windows:")
    
    # Filter out our own hand tracker window to prevent infinite loops
    excluded_keywords = ['hand tracker', 'simple hand tracker', 'robotic hand control']
    filtered_windows = []
    
    for window in windows[:20]:  # Show max 20 windows
        window_text = f"{window['app']} {window['title']}".lower()
        is_excluded = any(excluded in window_text for excluded in excluded_keywords)
        if not is_excluded:
            filtered_windows.append(window)
    
    if not filtered_windows:
        print("❌ No suitable windows found (excluding hand tracker windows)")
        return select_screen_region()
    
    for i, window in enumerate(filtered_windows):
        title = window['title'][:50] + "..." if len(window['title']) > 50 else window['title']
        print(f"  {i+1:2d}. {window['app']} - {title}")
    
    # Update windows list to use filtered version
    windows = filtered_windows
    
    if len(windows) > 20:
        print(f"     ... and {len(windows)-20} more windows")
    
    try:
        choice = input(f"\nSelect window number (1-{min(20, len(windows))}): ").strip()
        if not choice:
            return None
            
        window_idx = int(choice) - 1
        if 0 <= window_idx < min(20, len(windows)):
            selected_window = windows[window_idx]
            print(f"✅ Selected: {selected_window['app']} - {selected_window['title']}")
            
            # Store window info for tracking
            tracked_window_info = {
                'app': selected_window['app'],
                'title': selected_window['title'],
                'id': selected_window.get('id'),
                'track_window': True,
                'frame_count': 0
            }
            
            # If we have frame info (from pygetwindow, yabai, etc), use it
            if selected_window.get('frame'):
                frame = selected_window['frame']
                bounds = (int(frame['x']), int(frame['y']), 
                         int(frame['w']), int(frame['h']))
                tracked_window_info['last_bounds'] = bounds
                return bounds
            else:
                # For AppleScript results, we need to get window bounds
                bounds = get_window_bounds(selected_window['title'])
                if bounds:
                    tracked_window_info['last_bounds'] = bounds
                return bounds
        else:
            print("❌ Invalid selection")
            return None
            
    except (ValueError, EOFError) as e:
        print(f"❌ Invalid input: {e}")
        return None

def get_window_bounds(window_title: str) -> Optional[Tuple[int, int, int, int]]:
    """Get window bounds using improved AppleScript"""
    try:
        # Extract app name from title
        app_name = window_title.split(' - ')[0]
        window_name = ' - '.join(window_title.split(' - ')[1:]) if ' - ' in window_title else window_title
        
        # More robust AppleScript that searches for the specific window
        script = f'''
        try
            tell application "System Events"
                set frontmostApp to name of first application process whose frontmost is true
                tell application process "{app_name}"
                    try
                        set targetWindow to first window whose name contains "{window_name}"
                        set windowPosition to position of targetWindow
                        set windowSize to size of targetWindow
                        set windowX to item 1 of windowPosition
                        set windowY to item 2 of windowPosition
                        set windowWidth to item 1 of windowSize
                        set windowHeight to item 2 of windowSize
                        return windowX & "," & windowY & "," & windowWidth & "," & windowHeight
                    on error
                        -- Try just the first window of the app
                        set targetWindow to first window
                        set windowPosition to position of targetWindow
                        set windowSize to size of targetWindow
                        set windowX to item 1 of windowPosition
                        set windowY to item 2 of windowPosition
                        set windowWidth to item 1 of windowSize
                        set windowHeight to item 2 of windowSize
                        return windowX & "," & windowY & "," & windowWidth & "," & windowHeight
                    end try
                end tell
            end tell
        on error errMsg
            return "0,0,640,480"
        end try
        '''
        
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            bounds_str = result.stdout.strip()
            print(f"🔍 AppleScript result: '{bounds_str}'")
            
            # Parse bounds: "x,y,width,height" (AppleScript may add extra spaces/commas)
            try:
                # Clean up the string and split properly
                clean_bounds = bounds_str.replace(' ,, ', ',').replace(',,', ',').strip()
                parts = [p.strip() for p in clean_bounds.split(',') if p.strip()]
                
                if len(parts) >= 4:
                    x, y, width, height = [int(parts[i]) for i in range(4)]
                    if width > 0 and height > 0:
                        print(f"✅ Window bounds: x={x}, y={y}, width={width}, height={height}")
                        return (x, y, width, height)
            except (ValueError, IndexError) as e:
                print(f"⚠️ Could not parse bounds '{bounds_str}': {e}")
    
    except Exception as e:
        print(f"Warning: Could not get window bounds: {e}")
    
    print("⚠️ Could not determine window bounds, falling back to manual selection")
    return select_screen_region()

def select_screen_region() -> Optional[Tuple[int, int, int, int]]:
    """Allow user to select a screen region for capture"""
    if not SCREEN_CAPTURE_AVAILABLE:
        print("❌ Screen capture not available (mss or tkinter not installed)")
        return None
    
    print("\n🖥️ Screen Capture Region Selection")
    print("Please enter the screen region coordinates:")
    print("(You can use a tool like 'Digital Color Meter' on Mac to find coordinates)")
    
    try:
        x = int(input("Enter X coordinate (left edge): "))
        y = int(input("Enter Y coordinate (top edge): "))
        width = int(input("Enter width: "))
        height = int(input("Enter height: "))
        
        if width <= 0 or height <= 0:
            print("❌ Width and height must be positive")
            return None
        
        print(f"✅ Selected region: x={x}, y={y}, width={width}, height={height}")
        return (x, y, width, height)
        
    except (ValueError, EOFError) as e:
        print(f"❌ Invalid input: {e}")
        return None

def update_window_position() -> Optional[Tuple[int, int, int, int]]:
    """Update the position of the tracked window using Quartz"""
    global tracked_window_info
    
    if not tracked_window_info:
        return None
    
    try:
        # Try Quartz first for fastest performance
        if QUARTZ_AVAILABLE and tracked_window_info.get('id'):
            window_id = tracked_window_info['id']
            
            # Get window info by ID using Quartz
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionIncludingWindow,
                window_id
            )
            
            if window_list and len(window_list) > 0:
                window_info = window_list[0]
                bounds = window_info.get('kCGWindowBounds', {})
                
                if bounds:
                    x = int(bounds.get('X', 0))
                    y = int(bounds.get('Y', 0))
                    width = int(bounds.get('Width', 0))
                    height = int(bounds.get('Height', 0))
                    
                    if width > 0 and height > 0:
                        tracked_window_info['last_bounds'] = (x, y, width, height)
                        return (x, y, width, height)
        
        # Fallback to AppleScript
        app_name = tracked_window_info['app']
        window_title = tracked_window_info['title']
        
        script = f'''
        try
            tell application "System Events"
                tell application process "{app_name}"
                    set targetWindow to first window
                    set windowPosition to position of targetWindow
                    set windowSize to size of targetWindow
                    set windowX to item 1 of windowPosition
                    set windowY to item 2 of windowPosition
                    set windowWidth to item 1 of windowSize
                    set windowHeight to item 2 of windowSize
                    return windowX & "," & windowY & "," & windowWidth & "," & windowHeight
                end tell
            end tell
        on error
            return "0,0,640,480"
        end try
        '''
        
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, timeout=2)
        
        if result.returncode == 0:
            bounds_str = result.stdout.strip()
            clean_bounds = bounds_str.replace(' ,, ', ',').replace(',,', ',').strip()
            parts = [p.strip() for p in clean_bounds.split(',') if p.strip()]
            
            if len(parts) >= 4:
                x, y, width, height = [int(parts[i]) for i in range(4)]
                if width > 0 and height > 0:
                    tracked_window_info['last_bounds'] = (x, y, width, height)
                    return (x, y, width, height)
    
    except Exception as e:
        # Silently fail and use last known position
        pass
    
    return tracked_window_info.get('last_bounds')

def capture_window_directly(window_id: int) -> Optional[np.ndarray]:
    """Capture a specific window directly using its window ID (Quartz native)"""
    if not QUARTZ_AVAILABLE:
        return None
    
    try:
        # Capture the specific window using its ID
        screenshot = Quartz.CGWindowListCreateImage(
            Quartz.CGRectNull,  # Capture entire window
            Quartz.kCGWindowListOptionIncludingWindow,
            window_id,
            Quartz.kCGWindowImageBoundsIgnoreFraming | Quartz.kCGWindowImageDefault
        )
        
        if screenshot:
            # Convert CGImage to numpy array
            img_width = Quartz.CGImageGetWidth(screenshot)
            img_height = Quartz.CGImageGetHeight(screenshot)
            
            if img_width == 0 or img_height == 0:
                return None
            
            # Create bitmap context
            bytes_per_row = 4 * img_width
            bitmap_data = bytearray(bytes_per_row * img_height)
            
            bitmap_context = Quartz.CGBitmapContextCreate(
                bitmap_data,
                img_width,
                img_height,
                8,  # bits per component
                bytes_per_row,
                Quartz.CGColorSpaceCreateDeviceRGB(),
                Quartz.kCGImageAlphaPremultipliedLast
            )
            
            if bitmap_context:
                # Draw the image into the bitmap context
                Quartz.CGContextDrawImage(
                    bitmap_context,
                    Quartz.CGRectMake(0, 0, img_width, img_height),
                    screenshot
                )
                
                # Convert to numpy array and reshape
                frame = np.frombuffer(bitmap_data, dtype=np.uint8)
                frame = frame.reshape((img_height, img_width, 4))
                
                # Convert from RGBA to BGR for OpenCV
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                
                return frame
        
    except Exception as e:
        print(f"❌ Window capture error: {e}")
        return None
    
    return None

def capture_screen_region(region: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
    """Capture screen content - uses direct window capture if window ID available"""
    global tracked_window_info, screen_capture_region
    
    if not SCREEN_CAPTURE_AVAILABLE:
        return None
    
    # If we have a window ID, capture the window directly
    if tracked_window_info and tracked_window_info.get('id') and QUARTZ_AVAILABLE:
        window_id = tracked_window_info['id']
        
        # Update window info periodically
        frame_count = tracked_window_info.get('frame_count', 0)
        tracked_window_info['frame_count'] = frame_count + 1
        
        if frame_count % 30 == 0:  # Update every 30 frames
            new_bounds = update_window_position()
            if new_bounds:
                screen_capture_region = new_bounds
        
        # Capture the window directly
        return capture_window_directly(window_id)
    
    # Fallback to region capture for compatibility
    current_region = region
    if tracked_window_info and tracked_window_info.get('track_window', False):
        frame_count = tracked_window_info.get('frame_count', 0)
        tracked_window_info['frame_count'] = frame_count + 1
        
        if frame_count % 30 == 0:
            new_bounds = update_window_position()
            if new_bounds and new_bounds != region:
                print(f"🔄 Window moved: {region} → {new_bounds}")
                screen_capture_region = new_bounds
                current_region = new_bounds
    
    x, y, width, height = current_region
    
    try:
        if QUARTZ_AVAILABLE:
            # Use Quartz for screen region capture
            region_rect = Quartz.CGRectMake(x, y, width, height)
            
            screenshot = Quartz.CGWindowListCreateImage(
                region_rect,
                Quartz.kCGWindowListOptionOnScreenOnly,
                Quartz.kCGNullWindowID,
                Quartz.kCGWindowImageDefault
            )
            
            if screenshot:
                img_width = Quartz.CGImageGetWidth(screenshot)
                img_height = Quartz.CGImageGetHeight(screenshot)
                
                bytes_per_row = 4 * img_width
                bitmap_data = bytearray(bytes_per_row * img_height)
                
                bitmap_context = Quartz.CGBitmapContextCreate(
                    bitmap_data,
                    img_width,
                    img_height,
                    8,
                    bytes_per_row,
                    Quartz.CGColorSpaceCreateDeviceRGB(),
                    Quartz.kCGImageAlphaPremultipliedLast
                )
                
                if bitmap_context:
                    Quartz.CGContextDrawImage(
                        bitmap_context,
                        Quartz.CGRectMake(0, 0, img_width, img_height),
                        screenshot
                    )
                    
                    frame = np.frombuffer(bitmap_data, dtype=np.uint8)
                    frame = frame.reshape((img_height, img_width, 4))
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                    
                    return frame
        
        # Final fallback to mss
        if not QUARTZ_AVAILABLE:
            global sct
            if not sct:
                import mss
                sct = mss.mss()
            
            monitor = {"top": y, "left": x, "width": width, "height": height}
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame
            
    except Exception as e:
        print(f"❌ Screen capture error: {e}")
        return None
    
    return None

def list_all_ports():
    """List all available serial ports for debugging"""
    ports = serial.tools.list_ports.comports()
    print("\n🔍 Available Serial Ports:")
    for i, port in enumerate(ports):
        print(f"  {i+1}. {port.device} - {port.description}")
    print()

def select_port_manually():
    """Allow manual port selection"""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("❌ No serial ports found")
        return None
    
    print("\n🔍 Available Serial Ports:")
    for i, port in enumerate(ports):
        print(f"  {i+1}. {port.device} - {port.description}")
    
    try:
        choice = input("\nSelect port number (or press Enter to skip): ").strip()
        if choice:
            port_idx = int(choice) - 1
            if 0 <= port_idx < len(ports):
                selected_port = ports[port_idx].device
                print(f"✅ Selected: {selected_port}")
                return selected_port
    except (ValueError, IndexError):
        print("❌ Invalid selection")
    except EOFError:
        print("(no input available - skipping manual selection)")
    
    return None

def find_arduino():
    """Find Arduino port automatically - USB or BLE-Serial bridge only"""
    ports = serial.tools.list_ports.comports()
    
    # First try USB connections
    usb_ports = [p.device for p in ports if 
                'Arduino' in p.description or 
                'CH340' in p.description or 
                'USB' in p.description or
                'usbmodem' in p.device or
                'usbserial' in p.device]
    
    if usb_ports:
        print(f"🔌 Found USB Arduino on {usb_ports[0]}")
        return usb_ports[0]
    
    # Then try BLE-Serial bridge ports (created by ble-serial tool)
    ble_serial_ports = [p.device for p in ports if 
                       '/tmp/ttyBLE' in p.device or
                       'pty' in p.device or
                       'pts' in p.device]
    
    if ble_serial_ports:
        print(f"📶 Found BLE-Serial bridge on {ble_serial_ports[0]}")
        return ble_serial_ports[0]
    
    print("❌ No Arduino (USB) or BLE-Serial bridge found")
    print("💡 For BLE connection, run: ble-serial -d \"Hiwonder-BLE\" first")
    print("💡 Available ports:")
    list_all_ports()
    return None

async def scan_for_hiwonder():
    """Scan for Hiwonder BLE device"""
    if not BLE_AVAILABLE:
        print("❌ BLE support not available (bleak not installed)")
        return False
    
    print("🔍 Scanning for Hiwonder BLE device...")
    try:
        devices = await BleakScanner.discover(timeout=10.0)
        print(f"📱 Found {len(devices)} BLE devices")
        
        hiwonder_found = False
        for i, device in enumerate(devices):
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

async def connect_to_hiwonder_ble():
    """Connect to Hiwonder BLE device using proven test script logic"""
    global ble_client, ble_write_char, is_ble_connected
    
    # First scan for the device
    print("🔗 Testing connection to Hiwonder BLE device...")
    device_found = await scan_for_hiwonder()
    if not device_found:
        return False
    
    try:
        # Try to connect using MAC address (same as test script)
        print(f"📞 Attempting connection to {HIWONDER_MAC}...")
        ble_client = BleakClient(HIWONDER_MAC)
        await ble_client.connect()
        
        if ble_client.is_connected:
            print("🎉 SUCCESS! Connected to Hiwonder BLE device!")
            
            # List services (same as test script)
            services = ble_client.services
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
                ble_write_char = target_char  # Store the characteristic object
                is_ble_connected = True
                print("🤖 Ready for servo control!")
                return True
            else:
                print("❌ Required services/characteristics not found")
                await ble_client.disconnect()
                return False
        else:
            print("❌ Connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        if ble_client:
            try:
                await ble_client.disconnect()
            except:
                pass
        return False

async def send_ble_servo_angles():
    """Send servo angles via BLE using official Hiwonder protocol"""
    global ble_client, ble_write_char, is_ble_connected
    
    if not is_ble_connected or not ble_client or not ble_client.is_connected:
        return False
    
    try:
        # Build packet using official Hiwonder protocol
        packet = build_hiwonder_servo_packet(servo_angles, time_ms=1000)
        
        # Send via BLE
        await ble_client.write_gatt_char(ble_write_char, packet, response=False)
        return True
        
    except Exception as e:
        print(f"❌ BLE write failed: {e}")
        is_ble_connected = False
        return False

def angle_to_position(angle):
    """Convert 0-180 angle to Hiwonder servo position (1100-1950)"""
    # Map 0-180 to 1100-1950 (standard Hiwonder range)
    return int(1100 + (angle / 180.0) * (1950 - 1100))

def build_hiwonder_servo_packet(servo_angles, time_ms=1000):
    """Build servo control packet using official Hiwonder protocol"""
    packet = bytearray()
    
    # Frame header (2 bytes)
    packet.append(FRAME_HEADER)  # 0x55
    packet.append(FRAME_HEADER)  # 0x55
    
    # Calculate number of bytes (function + servo_count + time + servo_data)
    servo_count = len(servo_angles)
    data_bytes = 1 + 1 + 2 + (servo_count * 3)  # func + count + time + (id+pos_low+pos_high)*6
    packet.append(data_bytes)  # Number
    
    # Function
    packet.append(CMD_SERVO_MOVE)  # 0x03
    
    # Servo count
    packet.append(servo_count)  # 6 servos
    
    # Time (little endian)
    packet.append(time_ms & 0xFF)        # time_low
    packet.append((time_ms >> 8) & 0xFF) # time_high
    
    # Servo data
    for i, angle in enumerate(servo_angles):
        position = angle_to_position(angle)
        packet.append(i + 1)                    # Servo ID (1-6)
        packet.append(position & 0xFF)          # position_low
        packet.append((position >> 8) & 0xFF)   # position_high
    
    return packet

def smooth_servo_angles():
    """Apply exponential smoothing to servo angles"""
    global smoothed_angles, servo_angles, target_angles
    
    angles_changed = False
    
    for i in range(6):
        # Apply exponential smoothing: new = old + factor * (target - old)
        smoothed_angles[i] += smoothing_factor * (target_angles[i] - smoothed_angles[i])
        
        # Convert to integer for servo
        new_angle = int(round(smoothed_angles[i]))
        
        # Apply servo limits
        min_angle, max_angle = servo_limits[i]
        new_angle = max(min_angle, min(max_angle, new_angle))
        
        # Only update if change is significant (reduces jitter)
        if abs(servo_angles[i] - new_angle) >= min_change_threshold:
            servo_angles[i] = new_angle
            angles_changed = True
    
    return angles_changed

def send_servo_angles():
    """Send all servo angles to Arduino (serial fallback - normally BLE handles this)"""
    global serial_connection, is_ble_connected
    
    # Try BLE first if connected
    if is_ble_connected:
        # BLE requires async, so we'll handle this in the main loop
        return True
    
    # Fall back to serial (for USB connections)
    if not serial_connection:
        return False
    
    try:
        # For serial connections, we assume a simple Arduino that expects our old protocol
        # If you have the official Hiwonder Arduino code loaded, this might not work
        # In that case, you'd need to also use the Hiwonder protocol here
        
        # Build packet using official Hiwonder protocol for consistency
        packet = build_hiwonder_servo_packet(servo_angles, time_ms=1000)
        
        # Send packet
        serial_connection.write(packet)
        return True
        
    except Exception as e:
        print(f"Error sending command: {e}")
        return False

def get_raw_finger_values(hand_landmarks) -> List[float]:
    """
    Get raw finger values from hand landmarks (before mapping to servo angles)
    Returns list of 6 raw values for each finger
    """
    landmarks = hand_landmarks.landmark
    raw_values = []
    
    # Thumb - distance from MCP to tip
    thumb_tip = np.array([landmarks[4].x, landmarks[4].y, landmarks[4].z])
    thumb_mcp = np.array([landmarks[2].x, landmarks[2].y, landmarks[2].z])
    thumb_distance = np.linalg.norm(thumb_tip - thumb_mcp)
    raw_values.append(thumb_distance)
    
    # Other fingers - bend angle
    finger_configs = [
        (8, 5, 6),   # Index finger
        (12, 9, 10), # Middle finger  
        (16, 13, 14), # Ring finger
        (20, 17, 18), # Pinky finger
    ]
    
    for tip_id, mcp_id, pip_id in finger_configs:
        tip = np.array([landmarks[tip_id].x, landmarks[tip_id].y, landmarks[tip_id].z])
        mcp = np.array([landmarks[mcp_id].x, landmarks[mcp_id].y, landmarks[mcp_id].z])
        pip = np.array([landmarks[pip_id].x, landmarks[pip_id].y, landmarks[pip_id].z])
        
        mcp_to_pip = pip - mcp
        pip_to_tip = tip - pip
        
        if np.linalg.norm(mcp_to_pip) > 0 and np.linalg.norm(pip_to_tip) > 0:
            cos_angle = np.dot(mcp_to_pip, pip_to_tip) / (np.linalg.norm(mcp_to_pip) * np.linalg.norm(pip_to_tip))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            bend_angle = np.arccos(cos_angle)
            raw_values.append(bend_angle)
        else:
            raw_values.append(0.0)
    
    # Wrist - keep neutral for now
    raw_values.append(0.0)
    
    return raw_values

def calibrate_fingers():
    """
    Calibrate each finger by prompting user to close and open them
    Returns calibrated servo limits
    """
    global servo_limits
    
    print("\n🎯 FINGER CALIBRATION")
    print("=" * 50)
    print("This will calibrate the min/max values for each finger.")
    print("For each finger, you'll be prompted to:")
    print("1. Close the finger completely (min value)")
    print("2. Open the finger completely (max value)")
    print("=" * 50)
    
    input("Press Enter to start calibration...")
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("⚠️ Failed to open camera 0, trying camera 1...")
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("❌ No camera found. Cannot calibrate.")
            return servo_limits
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Initialize MediaPipe
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
    calibrated_limits = []
    
    for finger_idx, finger_name in enumerate(servo_names):
        print(f"\n📏 Calibrating {finger_name}...")
        
        min_values = []
        max_values = []
        
        # Collect min values (closed finger)
        print(f"  🔴 CLOSE your {finger_name} completely and hold for 1.5 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 1.5:
            ret, frame = cap.read()
            if not ret:
                continue
                
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            results = hands.process(rgb_frame)
            rgb_frame.flags.writeable = True
            frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    raw_values = get_raw_finger_values(hand_landmarks)
                    min_values.append(raw_values[finger_idx])
            
            # Draw countdown
            remaining = 1.5 - int(time.time() - start_time)
            cv2.putText(frame, f"CLOSE {finger_name}: {remaining}s", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow('Calibration', frame)
            cv2.waitKey(1)
        
        # Collect max values (open finger)
        print(f"  🟢 OPEN your {finger_name} completely and hold for 1.5 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 1.5:
            ret, frame = cap.read()
            if not ret:
                continue
                
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            results = hands.process(rgb_frame)
            rgb_frame.flags.writeable = True
            frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    raw_values = get_raw_finger_values(hand_landmarks)
                    max_values.append(raw_values[finger_idx])
            
            # Draw countdown
            remaining = 1.5 - int(time.time() - start_time)
            cv2.putText(frame, f"OPEN {finger_name}: {remaining}s", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow('Calibration', frame)
            cv2.waitKey(1)
        
        # Calculate min/max from collected values
        if min_values and max_values:
            min_val = np.percentile(min_values, 25)  # Use 25th percentile to avoid outliers
            max_val = np.percentile(max_values, 75)  # Use 75th percentile to avoid outliers
            
            # Map to servo limits
            if finger_idx == 0:  # Thumb
                servo_min = 0
                servo_max = 180  # Match Arduino sketch range (0-180°)
            elif finger_idx == 3:  # Ring finger
                servo_min = 25
                servo_max = 180
            else:  # Other fingers
                servo_min = 0
                servo_max = 180
            
            calibrated_limits.append((servo_min, servo_max))
            print(f"  ✅ {finger_name}: Raw range {min_val:.3f} - {max_val:.3f} → Servo {servo_min}° - {servo_max}°")
        else:
            print(f"  ⚠️ No data collected for {finger_name}, using defaults")
            calibrated_limits.append(servo_limits[finger_idx])
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n🎉 Calibration complete!")
    print("Calibrated limits:")
    for i, (name, (min_angle, max_angle)) in enumerate(zip(servo_names, calibrated_limits)):
        print(f"  {name}: {min_angle}° - {max_angle}°")
    
    return calibrated_limits

def calculate_finger_angles(hand_landmarks) -> List[int]:
    """
    Calculate servo angles from hand landmarks using calibrated limits
    Returns list of 6 servo angles
    """
    # Get landmark positions
    landmarks = hand_landmarks.landmark
    
    # Calculate finger bend angles based on landmark distances and joint angles
    angles = []
    
    # Thumb - Use distance from tip to middle finger base (MCP) for control
    thumb_tip = np.array([landmarks[4].x, landmarks[4].y, landmarks[4].z])
    middle_mcp = np.array([landmarks[9].x, landmarks[9].y, landmarks[9].z])  # Middle finger MCP joint (base)
    
    # Calculate distance from thumb tip to middle finger base
    thumb_to_middle_distance = np.linalg.norm(thumb_tip - middle_mcp)
    
    # Map distance to servo range (0-180°) with AGGRESSIVE closing
    # When thumb touches middle finger base = fully closed (180°) - inverted mapping
    # When thumb is far from middle finger base = fully open (0°)
    # Use MUCH smaller distance range for aggressive closing: 0.02 to 0.08
    normalized_distance = np.clip((thumb_to_middle_distance - 0.02) / (0.08 - 0.02), 0.0, 1.0)
    
    # Inverted mapping for thumb: close distance = high angle (closed), far distance = low angle (open)
    base_thumb_angle = (1.0 - normalized_distance) * 180  # Match Arduino sketch range (0-180°)
    
    # Add moderate sensitivity for better control
    thumb_angle = int(base_thumb_angle * 5.0)  # 5x sensitivity for balanced responsiveness
    
    # Clamp to Arduino's actual servo range (0-180°)
    thumb_angle = max(0, min(180, thumb_angle))
    
    # VERY aggressive snapping to ensure tight closure
    snap_threshold = 180 * 0.25  # 25% of 180° = 45° for much easier snapping
    if thumb_angle >= (180 - snap_threshold):
        thumb_angle = 180  # Snap to fully closed at 180°
    
    # Also snap to open when very low
    if thumb_angle <= 15:  # Higher threshold for better open detection
        thumb_angle = 0  # Snap to fully open
    
    angles.append(thumb_angle)
    
    # Other fingers - Use simple distance-based calculation (DIRECT mapping for correct movement)
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
        
        # Use simple distance-based calculation
        distance = np.linalg.norm(tip - mcp)
        
        # Map distance to servo range (0.05 to 0.15 typical range)
        normalized_distance = np.clip((distance - 0.05) / (0.15 - 0.05), 0.0, 1.0)
        
        # Pinky gets extra sensitivity (2x)
        if name == "Pinky":
            normalized_distance = normalized_distance * 2.0
            normalized_distance = min(1.0, normalized_distance)  # Clamp to 1.0
        
        # Direct mapping: when finger is extended (large distance) = max angle (open servo)
        # when finger is bent (small distance) = min angle (closed servo)
        servo_angle = int(normalized_distance * (max_angle - min_angle) + min_angle)
        
        # Snap to min/max when within 5% of limits
        range_size = max_angle - min_angle
        snap_threshold = range_size * 0.05  # 5% of range
        
        if servo_angle <= min_angle + snap_threshold:
            servo_angle = min_angle  # Snap to min
        elif servo_angle >= max_angle - snap_threshold:
            servo_angle = max_angle  # Snap to max
        
        # Ensure we can reach 0° for proper closing
        servo_angle = max(min_angle, min(max_angle, servo_angle))
        angles.append(servo_angle)
    
    # Wrist rotation (keep neutral for now)
    wrist_angle = 90
    angles.append(wrist_angle)
    
    return angles

def draw_info_overlay(image, angles: List[int], fps: float, arduino_connected: bool):
    """Draw information overlay on the image"""
    height, width = image.shape[:2]
    
    # Create semi-transparent overlay
    overlay = image.copy()
    
    # Draw background rectangles
    cv2.rectangle(overlay, (10, 10), (350, 200), (0, 0, 0), -1)
    cv2.rectangle(overlay, (width - 180, 10), (width - 10, 80), (0, 0, 0), -1)
    
    # Blend overlay
    cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
    
    # Draw servo angles
    y_pos = 35
    for i, (name, angle) in enumerate(zip(servo_names, angles)):
        min_angle, max_angle = servo_limits[i]
        
        # Color coding
        if arduino_connected:
            color = (0, 255, 0)  # Green when connected
        else:
            color = (0, 165, 255)  # Orange when simulating
        
        text = f"{name}: {angle:3d}°"
        cv2.putText(image, text, (20, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Draw angle bar
        bar_ratio = (angle - min_angle) / (max_angle - min_angle)
        bar_width = int(bar_ratio * 280)
        cv2.rectangle(image, (20, y_pos + 5), (20 + bar_width, y_pos + 15), color, -1)
        cv2.rectangle(image, (20, y_pos + 5), (300, y_pos + 15), (100, 100, 100), 1)
        
        y_pos += 25
    
    # Draw FPS
    cv2.putText(image, f"FPS: {fps:.1f}", (width - 170, 40),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Draw status
    if arduino_connected:
        if is_ble_connected:
            status_text = "BLE Connected"
            status_color = (0, 255, 255)  # Cyan for BLE
        else:
            status_text = "Serial Connected"
            status_color = (0, 255, 0)    # Green for serial
    else:
        status_text = "Simulation Mode"
        status_color = (0, 165, 255)
    
    cv2.putText(image, status_text, (width - 170, 65),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)

async def try_ble_connection():
    """Try to connect via BLE first"""
    if not BLE_AVAILABLE:
        print("💡 BLE support not available, trying serial connections...")
        return False
    
    print("🔍 Trying BLE connection to Hiwonder device...")
    success = await connect_to_hiwonder_ble()
    if success:
        # Send initial position via BLE
        await send_ble_servo_angles()
    return success

def main():
    """Main function"""
    global serial_connection, servo_angles, target_angles, smoothed_angles, last_update_time, servo_limits, is_ble_connected, ble_client, ble_write_char
    global screen_capture_region, use_screen_capture, sct, tracked_window_info
    
    print("Simple Hand Tracker Starting...")
    
    # Ask for input source
    print("\n📹 INPUT SOURCE SELECTION")
    print("Choose your hand tracking input source:")
    print("1. Webcam (default)")
    if SCREEN_CAPTURE_AVAILABLE and WINDOW_CAPTURE_AVAILABLE:
        print("2. Screen capture - Select specific window")
        print("3. Screen capture - Manual region selection")
    elif SCREEN_CAPTURE_AVAILABLE:
        print("2. Screen capture (manual region)")
    else:
        print("2. Screen capture (unavailable - install 'mss' package)")
    
    try:
        max_choice = 3 if (SCREEN_CAPTURE_AVAILABLE and WINDOW_CAPTURE_AVAILABLE) else 2
        input_choice = input(f"Enter choice (1-{max_choice}): ").strip()
    except EOFError:
        print("(no input available - using webcam)")
        input_choice = "1"
    
    if input_choice == "2" and SCREEN_CAPTURE_AVAILABLE:
        if WINDOW_CAPTURE_AVAILABLE:
            print("\n🪟 Setting up window capture...")
            screen_capture_region = select_window()
        else:
            print("\n🖥️ Setting up screen capture...")
            screen_capture_region = select_screen_region()
        
        if screen_capture_region:
            use_screen_capture = True
            if tracked_window_info and tracked_window_info.get('id') and QUARTZ_AVAILABLE:
                print("✅ Direct window capture configured!")
                print(f"🎯 Streaming window ID {tracked_window_info['id']} via Quartz")
            else:
                print("✅ Screen capture configured!")
            print("💡 Tip: To prevent feedback loops, the preview window will be minimized")
        else:
            print("⚠️ Screen capture setup failed, falling back to webcam")
            use_screen_capture = False
    elif input_choice == "3" and SCREEN_CAPTURE_AVAILABLE and WINDOW_CAPTURE_AVAILABLE:
        print("\n🖥️ Setting up manual screen capture...")
        screen_capture_region = select_screen_region()
        if screen_capture_region:
            use_screen_capture = True
            if tracked_window_info and tracked_window_info.get('id') and QUARTZ_AVAILABLE:
                print("✅ Direct window capture configured!")
                print(f"🎯 Streaming window ID {tracked_window_info['id']} via Quartz")
            else:
                print("✅ Screen capture configured!")
        else:
            print("⚠️ Screen capture setup failed, falling back to webcam")
            use_screen_capture = False
    else:
        print("✅ Using webcam input")
        use_screen_capture = False
    
    # Ask if user wants to calibrate
    print("\n🎯 CALIBRATION OPTION")
    print("Would you like to calibrate your finger movements?")
    print("This will improve accuracy by measuring your actual hand range.")
    print("1. Yes - Run calibration (recommended)")
    print("2. No - Use default settings")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
    except EOFError:
        print("(no input available - using default settings)")
        choice = "2"
    
    if choice == "1":
        print("\n🎯 Starting calibration...")
        servo_limits = calibrate_fingers()
        print("✅ Calibration complete! Starting hand tracking...")
    else:
        print("✅ Using default servo limits.")
    
    # Try BLE connection first
    arduino_connected = False
    connection_type = "simulation"
    
    # Try BLE first
    try:
        print("🚀 Attempting BLE connection to Hiwonder device...")
        ble_success = asyncio.run(try_ble_connection())
        if ble_success:
            arduino_connected = True
            connection_type = "BLE"
            print("🎉 Successfully connected via BLE!")
        else:
            print("⚠️ BLE connection failed, trying serial...")
    except Exception as e:
        print(f"⚠️ BLE connection error: {e}, trying serial...")
    
    # Fall back to serial if BLE failed
    if not arduino_connected:
        port = find_arduino()
        
        if not port:
            print("⚠️ No Arduino or Bluetooth device found automatically")
            print("💡 Would you like to select a port manually?")
            try:
                manual_choice = input("Enter 'y' to select manually, or press Enter to run in simulation mode: ").strip().lower()
                if manual_choice == 'y':
                    port = select_port_manually()
            except EOFError:
                print("(no input available - continuing in simulation mode)")
                manual_choice = ""
        
        if port:
            try:
                print(f"🔗 Attempting to connect to {port}...")
                serial_connection = serial.Serial(port, 115200, timeout=1)
                time.sleep(2)  # Wait for Arduino to reset
                arduino_connected = True
                
                # Determine connection type
                if '/tmp/ttyBLE' in port or 'pty' in port or 'pts' in port:
                    connection_type = "BLE-Serial bridge"
                    print(f"✅ Connected to BLE-Serial bridge on {port}")
                else:
                    connection_type = "USB"
                    print(f"✅ Connected to USB Arduino on {port}")
                
                # Send initial position
                send_servo_angles()
            except Exception as e:
                print(f"⚠️ Failed to connect to device: {e}")
                print("⚠️ Running in simulation mode")
        else:
            print("⚠️ No device found - Running in simulation mode")
    
    # Initialize MediaPipe
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
    # Initialize input source
    cap = None
    if not use_screen_capture:
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("⚠️ Failed to open camera 0, trying camera 1...")
            cap = cv2.VideoCapture(1)
            if not cap.isOpened():
                print("❌ No camera found. Please connect a camera and try again.")
                return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print(f"✅ Camera opened successfully")
    else:
        print(f"✅ Screen capture configured for region: {screen_capture_region}")
    
    print("\n🎮 Hand Tracking Started!")
    print("📈 Smoothing enabled:")
    print(f"  - Smoothing factor: {smoothing_factor} (higher = faster)")
    print(f"  - Update rate: {1/update_interval:.0f}Hz")
    print(f"  - Change threshold: {min_change_threshold}°")
    print("Controls:")
    print("  - Show hand to camera for control")
    print("  - Press 'q' to quit")
    print("  - Press 'c' to calibrate (center all servos)")
    print("  - Press 'o' to open hand")
    print("  - Press 'f' to make fist")
    print()
    
    prev_time = time.time()
    
    try:
        while True:
            frame = None
            
            if use_screen_capture:
                # Capture screen region
                frame = capture_screen_region(screen_capture_region)
                if frame is None:
                    print("Failed to capture screen")
                    break
                # No need to flip screen capture
                ret = True
            else:
                # Capture from webcam
                if not cap or not cap.isOpened():
                    print("Camera not available")
                    break
                ret, frame = cap.read()
                if not ret or frame is None:
                    print("Failed to grab frame from camera")
                    # If BLE is connected, disconnect gracefully before breaking
                    if is_ble_connected and ble_client:
                        try:
                            asyncio.run(ble_client.disconnect())
                            print("📶 BLE disconnected due to camera error")
                        except:
                            pass
                    break
                
                # Flip frame horizontally for mirror effect (webcam only)
                frame = cv2.flip(frame, 1)
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            
            # Process hand detection
            results = hands.process(rgb_frame)
            
            # Convert back to BGR for OpenCV
            rgb_frame.flags.writeable = True
            frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            
            # Calculate FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time)
            prev_time = curr_time
            
            # Process hand landmarks
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks on frame
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # Calculate target servo angles from hand pose
                    new_target_angles = calculate_finger_angles(hand_landmarks)
                    target_angles[:] = new_target_angles
            
            # Apply smoothing and send to Arduino (rate limited)
            if curr_time - last_update_time > update_interval:
                # Apply exponential smoothing
                angles_changed = smooth_servo_angles()
                
                # Only send if angles actually changed significantly
                if angles_changed:
                    if arduino_connected:
                        if is_ble_connected:
                            # Send via BLE (async)
                            try:
                                asyncio.run(send_ble_servo_angles())
                            except Exception as e:
                                print(f"BLE send error: {e}")
                                # If BLE fails, mark as disconnected
                                is_ble_connected = False
                        else:
                            # Send via serial
                            send_servo_angles()
                    else:
                        # Print servo commands when no device connected
                        print(f"SIM: Thumb:{servo_angles[0]:3d}° Index:{servo_angles[1]:3d}° Middle:{servo_angles[2]:3d}° Ring:{servo_angles[3]:3d}° Pinky:{servo_angles[4]:3d}° Wrist:{servo_angles[5]:3d}°")
                
                last_update_time = curr_time
            
            # Draw info overlay
            draw_info_overlay(frame, servo_angles, fps, arduino_connected)
            
            # Show frame with appropriate title and size
            if use_screen_capture:
                # For screen capture, use a smaller preview window with unique name
                window_title = "🤖 Hand Tracker Preview (Screen Capture Mode)"
                # Resize frame to smaller preview size to avoid feedback loops
                preview_frame = cv2.resize(frame, (640, 480))
                cv2.imshow(window_title, preview_frame)
                
                # Move window to a safe position
                cv2.moveWindow(window_title, 50, 50)
            else:
                # For webcam, use normal size window
                window_title = "🤖 Simple Hand Tracker - Webcam - Robotic Hand Control"
                cv2.imshow(window_title, frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                # Calibrate - center all servos
                target_angles[:] = [90, 90, 90, 90, 90, 90]
                smoothed_angles[:] = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0]
                servo_angles[:] = [90, 90, 90, 90, 90, 90]
                if arduino_connected:
                    send_servo_angles()
                print("Calibrated - all servos centered")
            elif key == ord('o'):
                # Open hand
                target_angles[:] = [0, 0, 0, 25, 0, 90]  # Min thumb (open), min others (respecting limits)
                print("Opening hand...")
            elif key == ord('f'):
                # Make fist
                target_angles[:] = [180, 180, 180, 180, 180, 90]  # Max thumb (180° to match Arduino), max others
                print("Making fist...")
    
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    
    finally:
        # Cleanup
        if arduino_connected:
            # Return to neutral before closing
            target_angles[:] = [90, 90, 90, 90, 90, 90]
            smoothed_angles[:] = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0]
            servo_angles[:] = [90, 90, 90, 90, 90, 90]
            
            if is_ble_connected:
                try:
                    # Send final position and disconnect
                    async def cleanup_ble():
                        if ble_client and ble_client.is_connected:
                            await send_ble_servo_angles()
                            await ble_client.disconnect()
                    
                    # Create new event loop for cleanup
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(cleanup_ble())
                    finally:
                        loop.close()
                    
                    time.sleep(0.5)
                    print("📶 Disconnected from BLE device")
                except Exception as e:
                    print(f"⚠️ BLE cleanup error: {e}")
                    # Force disconnect if needed
                    try:
                        if ble_client:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(ble_client.disconnect())
                            finally:
                                loop.close()
                    except:
                        pass
            elif serial_connection:
                send_servo_angles()
                time.sleep(0.5)
                serial_connection.close()
                print("🔌 Disconnected from serial device")
        
        # Cleanup input source
        if cap:
            cap.release()
        if sct:
            sct.close()
        cv2.destroyAllWindows()
        print("👋 Hand tracking stopped.")

if __name__ == "__main__":
    main()
