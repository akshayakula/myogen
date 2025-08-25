# 🤖 Robotic Hand Controller

A modern hand pose tracking and robotic hand control system using **TensorFlow.js HandPose** and **Node.js**. This system provides real-time hand tracking through your webcam and controls a 6-servo robotic hand via Arduino.

## ✨ Features

- **Real-time Hand Tracking**: Uses TensorFlow.js HandPose for accurate 21-point hand landmark detection
- **Web-based Interface**: Beautiful, responsive web UI with live video feed and hand skeleton overlay
- **Arduino Integration**: Direct serial communication with Arduino for servo control
- **Manual Control**: Individual servo control with sliders
- **Auto-calibration**: One-click servo calibration
- **Real-time Feedback**: Live finger extension percentages and servo angle displays
- **Cross-platform**: Works on Windows, macOS, and Linux

## 🛠️ Hardware Requirements

### Arduino Setup
- **Arduino Uno/Nano** with the robotic hand control program uploaded
- **6 Servo Motors** for hand joints
- **USB connection** to your computer

### Arduino Program
Make sure your Arduino is running one of these programs:
- `read_uhand.ino` - Manual potentiometer control
- `uhand_actions.ino` - Action group sequences
- Or any program that accepts the serial protocol: `0xAA 0x77 [FUNC_SET_SERVO] [Length] [ServoID] [Angle] [Checksum]`

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Or if you prefer yarn
yarn install
```

### 2. Connect Arduino

1. Connect your Arduino to your computer via USB
2. Upload the robotic hand control program to your Arduino
3. Note the port (e.g., `/dev/tty.usbmodem11401` on macOS)

### 3. Test Arduino Connection

```bash
# Test Arduino communication
npm run test
```

This will:
- Auto-detect your Arduino
- Test each servo movement
- Provide manual control mode

### 4. Start the Hand Controller

```bash
# Start the main application
npm start
```

### 5. Open Web Interface

Open your browser and go to: **http://localhost:3000**

## 🎮 Usage

### Web Interface

1. **Start Tracking**: Click "Start Tracking" to begin hand pose detection
2. **Hand Detection**: Show your hand to the camera - you'll see the skeleton overlay
3. **Real-time Control**: Move your fingers to control the robotic hand
4. **Manual Control**: Use the sliders for precise servo control
5. **Calibration**: Click "Calibrate" to reset all servos to center position

### Manual Control Mode

When running the test script, you can use:
- **Arrow Keys**: Navigate between servos and adjust angles
- **Up/Down**: Change servo angle (±10°)
- **Left/Right**: Switch between servos (0-5)
- **Q**: Quit the application

## 📁 Project Structure

```
robotic-hand-controller/
├── hand_controller.js          # Main Node.js server
├── test_arduino.js            # Arduino communication tester
├── package.json               # Node.js dependencies
├── public/                    # Web interface files
│   ├── index.html            # Main HTML page
│   ├── app.js                # Frontend JavaScript
│   └── styles.css            # CSS styles
└── README.md                 # This file
```

## 🔧 Configuration

### Arduino Serial Protocol

The system uses a custom serial protocol for Arduino communication:

```
Packet Format: 0xAA 0x77 [Function] [Length] [Data...] [Checksum]

Functions:
- 0x01: Set Servo Angle
- 0x02: Set Buzzer
- 0x03: Set RGB LED
- 0x04: Read Servo Angle

Example (Set Servo 0 to 90°):
0xAA 0x77 0x01 0x02 0x00 0x5A [Checksum]
```

### Servo Mapping

- **Servo 0**: Thumb
- **Servo 1**: Index finger
- **Servo 2**: Middle finger
- **Servo 3**: Ring finger
- **Servo 4**: Pinky
- **Servo 5**: Wrist (fixed at 90°)

## 🎯 Hand Pose Detection

### Finger Extension Calculation

The system calculates finger extensions (0.0 = closed, 1.0 = extended) using:

- **Thumb**: Distance from base (landmark 2) to tip (landmark 4)
- **Other Fingers**: Distance from MCP joint to tip
  - Index: landmarks 5 → 8
  - Middle: landmarks 9 → 12
  - Ring: landmarks 13 → 16
  - Pinky: landmarks 17 → 20

### Mapping to Servo Angles

Finger extensions are mapped to servo angles (0-180°):
```javascript
servoAngle = Math.round(fingerExtension * 180)
```

## 🔌 API Endpoints

### GET `/api/status`
Get system status:
```json
{
  "arduino_connected": true,
  "model_loaded": true,
  "servo_angles": [90, 90, 90, 90, 90, 90]
}
```

### GET `/api/servo/:id/:angle`
Set individual servo angle:
```bash
curl "http://localhost:3000/api/servo/0/90"
```

### POST `/api/servos`
Set all servo angles:
```bash
curl -X POST "http://localhost:3000/api/servos" \
  -H "Content-Type: application/json" \
  -d '{"angles": [90, 90, 90, 90, 90, 90]}'
```

## 🐛 Troubleshooting

### Arduino Not Detected
1. Check USB connection
2. Verify Arduino is powered
3. Check if Arduino IDE can see the port
4. Try different USB cable

### Hand Detection Issues
1. Ensure good lighting
2. Keep hand clearly visible in camera
3. Check camera permissions in browser
4. Try refreshing the page

### Servo Movement Problems
1. Verify Arduino program is uploaded correctly
2. Check servo wiring and power
3. Test with manual control mode first
4. Verify serial protocol compatibility

### Performance Issues
1. Close other applications using the camera
2. Reduce video resolution if needed
3. Use a modern browser (Chrome, Firefox, Safari)
4. Ensure WebGL is enabled

## 📦 Dependencies

### Node.js Packages
- `@tensorflow/tfjs-node`: TensorFlow.js for Node.js
- `@tensorflow-models/handpose`: Hand pose detection model
- `serialport`: Arduino serial communication
- `express`: Web server
- `socket.io`: Real-time communication

### Browser Libraries
- `@tensorflow/tfjs`: TensorFlow.js for browser
- `@tensorflow-models/handpose`: Hand pose detection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **TensorFlow.js** team for the HandPose model
- **Arduino** community for serial communication libraries
- **Socket.io** for real-time web communication

---

**Happy robot controlling! 🤖✨**

# myogen
