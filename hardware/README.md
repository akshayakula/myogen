# 🤖 Robotic Hand Controller - Python Vision System

A Python-based hand pose tracking and robotic hand control system using **MediaPipe** and **OpenCV**. This system provides real-time hand tracking through your webcam with a visualization window and controls a 6-servo robotic hand via Arduino.

## ✨ Features

- **Real-time Hand Tracking**: Uses MediaPipe for accurate 21-point hand landmark detection
- **Computer Vision Interface**: OpenCV-based visualization window with hand skeleton overlay
- **Arduino Integration**: Direct serial communication with Arduino for servo control
- **Visual Feedback**: Live finger extension percentages and servo angle displays
- **Keyboard Controls**: Quick calibration and preset positions
- **Cross-platform**: Works on Windows, macOS, and Linux

## 🛠️ Hardware Requirements

### Arduino Setup
- **Arduino Uno/Nano** with the robotic hand control program uploaded
- **6 Servo Motors** for hand joints
- **USB connection** to your computer

### Arduino Programs Available
- `uhand_actions.ino` - Action group sequences with full servo control
- `read_uhand.ino` - Manual potentiometer control
- Uses serial protocol: `0xAA 0x77 [Function] [Length] [Data...] [Checksum]`

## 🚀 Quick Start

### 1. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Connect Arduino

1. Connect your Arduino to your computer via USB
2. Upload `uhand_actions.ino` to your Arduino
3. Note the port (e.g., `/dev/tty.usbmodem11401` on macOS)

### 3. Run Hand Tracker with Visualization

```bash
# Run with Arduino connection
./run_hand_tracker.sh

# Or run in visualization-only mode (no Arduino)
./run_hand_tracker.sh --no-arduino

# Or directly with Python
python3 hand_tracker_vision.py
```

## 🎮 Usage

### Visualization Window Controls

- **Q**: Quit the application
- **C**: Calibrate - center all servos to 90°
- **O**: Open hand completely
- **F**: Make a fist

### Hand Tracking

1. **Start the application** - The camera will open automatically
2. **Show your hand** - Keep it clearly visible in the camera view
3. **Move your fingers** - The robotic hand will mirror your movements
4. **Monitor feedback** - See real-time servo angles and FPS

## 📁 Project Structure

```
myogen/
├── hand_tracker_vision.py     # Main hand tracking with visualization
├── robotic_hand_controller.py # Arduino communication controller
├── arduino_controller.py       # Alternative Arduino controller
├── requirements.txt           # Python dependencies
├── run_hand_tracker.sh        # Startup script
├── uhand_actions/             # Arduino servo control program
│   ├── uhand_actions.ino
│   ├── uhand_servo.cpp
│   └── uhand_servo.h
├── read_uhand/                # Arduino manual control
│   └── read_uhand.ino
└── README.md                  # This file
```

## 🔧 Python Scripts

### hand_tracker_vision.py
Main application that:
- Captures video from webcam
- Detects hand using MediaPipe
- Calculates finger angles from landmarks
- Sends servo commands to Arduino
- Displays visualization window

### robotic_hand_controller.py
Arduino communication module with:
- Serial protocol implementation
- Predefined hand positions
- Smooth movement transitions
- Interactive command mode
- Auto-detection of Arduino port

## 🎯 Hand Pose Detection

### Finger Extension Calculation

The system calculates servo angles from MediaPipe hand landmarks:

- **Thumb**: DISABLED - Kept at neutral position (90°)
- **Index**: Distance from MCP (landmark 5) to tip (landmark 8)
- **Middle**: Distance from MCP (landmark 9) to tip (landmark 12)
- **Ring**: Distance from MCP (landmark 13) to tip (landmark 16)
- **Pinky**: Distance from MCP (landmark 17) to tip (landmark 20)

### Servo Mapping

- **Servo 0**: Thumb (DISABLED - fixed at 41° within 0-82° Arduino limit)
- **Servo 1**: Index finger (0-180°)
- **Servo 2**: Middle finger (0-180°)
- **Servo 3**: Ring finger (25-180°)
- **Servo 4**: Pinky (0-180°)
- **Servo 5**: Wrist (fixed at 90°)

## 🔌 Command Line Options

### hand_tracker_vision.py
```bash
python3 hand_tracker_vision.py [options]
  --port PORT          Serial port for Arduino
  --no-arduino         Run without Arduino (visualization only)
  --camera INDEX       Camera index (default: 0)
```

### robotic_hand_controller.py
```bash
python3 robotic_hand_controller.py [options]
  --port PORT          Serial port for Arduino
  --baud RATE          Baud rate (default: 9600)
  --demo               Run demo mode
  --position NAME      Move to specific position
  --angles A1,A2,...   Set specific servo angles
```

## 🐛 Troubleshooting

### Camera Issues
1. Check camera permissions
2. Try different camera index (0, 1, 2...)
3. Ensure no other app is using the camera

### Arduino Connection
1. Check USB connection
2. Verify correct port in command
3. Ensure Arduino program is uploaded
4. Try different USB cable

### Hand Detection Problems
1. Ensure good lighting
2. Keep hand clearly visible
3. Avoid busy backgrounds
4. Keep hand at moderate distance from camera

### Performance Issues
1. Close other applications
2. Reduce processing load
3. Check CPU usage
4. Update graphics drivers

## 📦 Dependencies

### Python Packages
- `mediapipe>=0.10.13` - Hand pose detection
- `opencv-python>=4.9.0.80` - Computer vision and visualization
- `numpy>=1.24.3` - Numerical computations
- `pyserial>=3.5` - Arduino serial communication

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

**Happy robot controlling! 🤖✋**