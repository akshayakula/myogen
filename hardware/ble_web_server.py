#!/usr/bin/env python3
"""
Web server that exposes BLE pose sender functionality via HTTP endpoints.
Allows sending finger curls and servo angles via HTTP requests to localhost.
"""

from flask import Flask, request, jsonify, render_template_string
import asyncio
import json
import re
import threading
import time
from typing import List, Dict, Optional
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Global variables for BLE connection (simulated for now)
latest_servo_angles = None
latest_curl_response = None
ble_connected = False
processing_queue = []

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 BLE Pose Sender Web Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
        input, textarea, button { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007bff; color: white; cursor: pointer; }
        button:hover { background: #0056b3; }
        .result { background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0; font-family: monospace; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 BLE Pose Sender Web Interface</h1>
        
        <div id="status" class="status disconnected">
            📡 BLE Status: <span id="ble-status">Disconnected</span>
        </div>
        
        <div class="grid">
            <div class="section">
                <h3>🎯 Send Servo Angles</h3>
                <p>Format: [thumb, index, middle, ring, pinky, wrist] (0-180°)</p>
                <input type="text" id="servo-angles" placeholder="90,90,90,100,90,90" style="width: 100%;">
                <br>
                <button onclick="sendServoAngles()">Send Servo Angles</button>
                <div id="servo-result" class="result" style="display: none;"></div>
            </div>
            
            <div class="section">
                <h3>🤏 Send Finger Curls</h3>
                <p>Format: "pinky: half curl; ring: no curl; ..."</p>
                <textarea id="finger-curls" placeholder="pinky: half curl; ring: no curl; middle: no curl; index: half curl; thumb: half curl" style="width: 100%; height: 60px;"></textarea>
                <br>
                <button onclick="sendFingerCurls()">Send Finger Curls</button>
                <div id="curls-result" class="result" style="display: none;"></div>
            </div>
        </div>
        
        <div class="section">
            <h3>🧠 Send Numeric Array</h3>
            <p>Format: [pinky, ring, middle, index, thumb] where 0=closed, 1=half, 2=extended</p>
            <input type="text" id="numeric-array" placeholder="1,1,2,2,1" style="width: 100%;">
            <button onclick="sendNumericArray()">Send Numeric Array</button>
            <div id="numeric-result" class="result" style="display: none;"></div>
        </div>
        
        <div class="section">
            <h3>📊 Latest Status</h3>
            <div id="latest-status" class="result">
                <strong>Latest Servo Angles:</strong> <span id="latest-angles">None</span><br>
                <strong>Queue Size:</strong> <span id="queue-size">0</span><br>
                <strong>Last Updated:</strong> <span id="last-updated">Never</span>
            </div>
            <button onclick="refreshStatus()">Refresh Status</button>
        </div>
        
        <div class="section">
            <h3>📋 API Endpoints</h3>
            <div class="result">
                <strong>POST /send_servo_angles</strong><br>
                Body: {"angles": [90, 90, 90, 100, 90, 90]}<br><br>
                
                <strong>POST /send_finger_curls</strong><br>
                Body: {"curls": "pinky: half curl; ring: no curl; ..."}<br><br>
                
                <strong>POST /send_numeric_array</strong><br>
                Body: {"array": [1, 1, 2, 2, 1]}<br><br>
                
                <strong>GET /status</strong><br>
                Returns current system status
            </div>
        </div>
    </div>

    <script>
        async function sendServoAngles() {
            const angles = document.getElementById('servo-angles').value;
            const result = document.getElementById('servo-result');
            
            try {
                const angleArray = angles.split(',').map(x => parseInt(x.trim()));
                const response = await fetch('/send_servo_angles', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ angles: angleArray })
                });
                
                const data = await response.json();
                result.innerHTML = JSON.stringify(data, null, 2);
                result.style.display = 'block';
                refreshStatus();
            } catch (error) {
                result.innerHTML = 'Error: ' + error.message;
                result.style.display = 'block';
            }
        }
        
        async function sendFingerCurls() {
            const curls = document.getElementById('finger-curls').value;
            const result = document.getElementById('curls-result');
            
            try {
                const response = await fetch('/send_finger_curls', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ curls: curls })
                });
                
                const data = await response.json();
                result.innerHTML = JSON.stringify(data, null, 2);
                result.style.display = 'block';
                refreshStatus();
            } catch (error) {
                result.innerHTML = 'Error: ' + error.message;
                result.style.display = 'block';
            }
        }
        
        async function sendNumericArray() {
            const array = document.getElementById('numeric-array').value;
            const result = document.getElementById('numeric-result');
            
            try {
                const numArray = array.split(',').map(x => parseInt(x.trim()));
                const response = await fetch('/send_numeric_array', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ array: numArray })
                });
                
                const data = await response.json();
                result.innerHTML = JSON.stringify(data, null, 2);
                result.style.display = 'block';
                refreshStatus();
            } catch (error) {
                result.innerHTML = 'Error: ' + error.message;
                result.style.display = 'block';
            }
        }
        
        async function refreshStatus() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                
                document.getElementById('latest-angles').textContent = 
                    data.latest_servo_angles ? JSON.stringify(data.latest_servo_angles) : 'None';
                document.getElementById('queue-size').textContent = data.queue_size || 0;
                document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
                
                const statusEl = document.getElementById('status');
                const bleStatusEl = document.getElementById('ble-status');
                if (data.ble_connected) {
                    statusEl.className = 'status connected';
                    bleStatusEl.textContent = 'Connected';
                } else {
                    statusEl.className = 'status disconnected';
                    bleStatusEl.textContent = 'Disconnected (Simulated)';
                }
            } catch (error) {
                console.error('Status refresh error:', error);
            }
        }
        
        // Auto-refresh status every 5 seconds
        setInterval(refreshStatus, 5000);
        
        // Initial status load
        refreshStatus();
    </script>
</body>
</html>
"""

def convert_numeric_to_servo_angles(numeric_array: List[int]) -> List[int]:
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

def parse_finger_curls_to_servo_angles(curl_string: str) -> List[int]:
    """Parse finger curl string to servo angles"""
    curl_to_numeric = {'full curl': 0, 'half curl': 1, 'no curl': 2}
    default_array = [1, 1, 1, 1, 1]
    
    try:
        finger_pattern = r'(pinky|ring|middle|index|thumb):\s*(no curl|half curl|full curl)'
        matches = re.findall(finger_pattern, curl_string.lower())
        
        if matches:
            finger_curls = {finger: curl for finger, curl in matches}
            finger_order = ['pinky', 'ring', 'middle', 'index', 'thumb']
            numeric_array = [curl_to_numeric.get(finger_curls.get(finger, 'half curl'), 1) 
                           for finger in finger_order]
        else:
            numeric_array = default_array
        
        return convert_numeric_to_servo_angles(numeric_array)
        
    except Exception as e:
        print(f"Parse error: {e}")
        return convert_numeric_to_servo_angles(default_array)

async def send_to_ble_pose_sender(servo_angles: List[int]) -> Dict:
    """Send servo angles to BLE pose sender (simulated for now)"""
    global latest_servo_angles, ble_connected
    
    try:
        latest_servo_angles = servo_angles
        
        # Try to call actual BLE pose sender
        try:
            import subprocess
            cmd = ['python3', 'ble_pose_sender.py', '--angles'] + [str(x) for x in servo_angles]
            
            # Check if bleak is available
            result = subprocess.run(['python3', '-c', 'import bleak'], 
                                  capture_output=True, timeout=2)
            
            if result.returncode == 0:
                # BLE available - actually send to device
                print(f"📤 Sending to actual BLE device: {servo_angles}")
                
                # Actually call the BLE pose sender
                try:
                    ble_result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    
                    if ble_result.returncode == 0:
                        ble_connected = True
                        return {
                            'success': True,
                            'message': f'Servo angles sent to BLE device: {servo_angles}',
                            'servo_angles': servo_angles,
                            'method': 'BLE',
                            'ble_output': ble_result.stdout[:200] if ble_result.stdout else 'No output'
                        }
                    else:
                        ble_connected = False
                        return {
                            'success': False,
                            'message': f'BLE send failed: {ble_result.stderr[:200]}',
                            'servo_angles': servo_angles,
                            'method': 'BLE_Failed',
                            'error': ble_result.stderr
                        }
                        
                except subprocess.TimeoutExpired:
                    return {
                        'success': False,
                        'message': f'BLE send timed out after 10 seconds',
                        'servo_angles': servo_angles,
                        'method': 'BLE_Timeout'
                    }
                except Exception as ble_error:
                    return {
                        'success': False,
                        'message': f'BLE execution error: {str(ble_error)}',
                        'servo_angles': servo_angles,
                        'method': 'BLE_Error'
                    }
            else:
                # BLE not available - simulate
                print(f"📤 Simulated send: {servo_angles}")
                ble_connected = False
                return {
                    'success': True,
                    'message': f'Servo angles processed (BLE simulated): {servo_angles}',
                    'servo_angles': servo_angles,
                    'method': 'Simulated',
                    'command': f"python3 ble_pose_sender.py --angles {' '.join(map(str, servo_angles))}"
                }
                
        except Exception as e:
            print(f"BLE send error: {e}")
            return {
                'success': False,
                'message': f'BLE send failed: {str(e)}',
                'servo_angles': servo_angles
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Processing error: {str(e)}'
        }

# Web routes
@app.route('/')
def index():
    """Main web interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_servo_angles', methods=['POST'])
def send_servo_angles():
    """Send servo angles directly"""
    try:
        data = request.get_json()
        angles = data.get('angles', [])
        
        if not angles or len(angles) != 6:
            return jsonify({
                'success': False,
                'message': 'Invalid angles. Expected 6 values [thumb, index, middle, ring, pinky, wrist]'
            }), 400
        
        if not all(0 <= angle <= 180 for angle in angles):
            return jsonify({
                'success': False,
                'message': 'All angles must be between 0-180 degrees'
            }), 400
        
        # Send to BLE pose sender
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_to_ble_pose_sender(angles))
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/send_finger_curls', methods=['POST'])
def send_finger_curls():
    """Send finger curls string"""
    try:
        data = request.get_json()
        curls = data.get('curls', '')
        
        if not curls:
            return jsonify({
                'success': False,
                'message': 'No finger curls provided'
            }), 400
        
        # Convert to servo angles
        servo_angles = parse_finger_curls_to_servo_angles(curls)
        
        # Send to BLE pose sender
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_to_ble_pose_sender(servo_angles))
        loop.close()
        
        result['original_curls'] = curls
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/send_numeric_array', methods=['POST'])
def send_numeric_array():
    """Send numeric array [0-2] for each finger"""
    try:
        data = request.get_json()
        array = data.get('array', [])
        
        if not array or len(array) != 5:
            return jsonify({
                'success': False,
                'message': 'Invalid array. Expected 5 values [pinky, ring, middle, index, thumb]'
            }), 400
        
        if not all(0 <= val <= 2 for val in array):
            return jsonify({
                'success': False,
                'message': 'All values must be 0-2 (0=closed, 1=half, 2=extended)'
            }), 400
        
        # Convert to servo angles
        servo_angles = convert_numeric_to_servo_angles(array)
        
        # Send to BLE pose sender
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_to_ble_pose_sender(servo_angles))
        loop.close()
        
        result['original_array'] = array
        result['array_meaning'] = f"[pinky={array[0]}, ring={array[1]}, middle={array[2]}, index={array[3]}, thumb={array[4]}]"
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get current system status"""
    return jsonify({
        'success': True,
        'ble_connected': ble_connected,
        'latest_servo_angles': latest_servo_angles,
        'queue_size': len(processing_queue),
        'timestamp': time.time(),
        'endpoints': [
            'POST /send_servo_angles',
            'POST /send_finger_curls', 
            'POST /send_numeric_array',
            'GET /status'
        ]
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'BLE Pose Sender Web Server',
        'timestamp': time.time()
    })

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BLE Pose Sender Web Server")
    parser.add_argument("--port", "-p", type=int, default=5000, help="Port to run on (default: 5000)")
    parser.add_argument("--host", default="localhost", help="Host to bind to (default: localhost)")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    print("🚀 BLE Pose Sender Web Server")
    print("=" * 50)
    print(f"🌐 Starting server on http://{args.host}:{args.port}")
    print(f"📱 Web interface: http://{args.host}:{args.port}")
    print("=" * 50)
    print("📋 Available endpoints:")
    print(f"  GET  http://{args.host}:{args.port}/")
    print(f"  POST http://{args.host}:{args.port}/send_servo_angles")
    print(f"  POST http://{args.host}:{args.port}/send_finger_curls")
    print(f"  POST http://{args.host}:{args.port}/send_numeric_array")
    print(f"  GET  http://{args.host}:{args.port}/status")
    print("=" * 50)
    
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()
