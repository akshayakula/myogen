# 🚀 Setup Guide: TensorFlow.js Hand Tracking & Robotic Hand Control

## 🎯 What We Built

A **modern, clean hand tracking system** using **TensorFlow.js HandPose** that controls a 6-servo robotic hand via Arduino. This replaces the messy Python implementations with a professional JavaScript solution.

## ✨ Key Features

- **Real-time Hand Tracking**: TensorFlow.js HandPose with 21-point landmark detection
- **Beautiful Web Interface**: Modern, responsive UI with live video feed
- **Arduino Integration**: Direct serial communication for servo control
- **Manual Control**: Individual servo sliders for precise control
- **Auto-calibration**: One-click servo reset
- **Cross-platform**: Works on Windows, macOS, and Linux

## 📁 Project Structure

```
robotic-hand-controller/
├── hand_controller.js          # Main Node.js server (with Arduino)
├── demo.js                     # Demo server (simulated Arduino)
├── test_arduino.js            # Arduino communication tester
├── package.json               # Node.js dependencies
├── public/                    # Web interface
│   ├── index.html            # Main HTML page
│   ├── app.js                # Frontend JavaScript
│   └── styles.css            # Modern CSS styles
├── README.md                 # Comprehensive documentation
└── SETUP_GUIDE.md           # This setup guide
```

## 🛠️ Installation

### 1. Install Node.js Dependencies

```bash
npm install
```

### 2. Test Arduino Communication (Optional)

```bash
npm run test
```

This will:
- Auto-detect your Arduino
- Test each servo movement
- Provide manual control mode

## 🎮 Usage

### Demo Mode (No Arduino Required)

```bash
npm run demo
```

Then open: **http://localhost:3000**

This gives you:
- ✅ Full hand tracking interface
- ✅ Simulated Arduino connection
- ✅ Manual servo control
- ✅ Real-time finger extension display

### Full Mode (With Arduino)

```bash
npm start
```

Then open: **http://localhost:3000**

This gives you:
- ✅ Full hand tracking interface
- ✅ Real Arduino connection
- ✅ Actual servo control
- ✅ Real-time robot control

## 🎯 How It Works

### 1. Hand Pose Detection
- Uses **TensorFlow.js HandPose** in the browser
- Detects 21 hand landmarks in real-time
- Calculates finger extensions (0.0 = closed, 1.0 = extended)

### 2. Servo Control
- Maps finger extensions to servo angles (0-180°)
- Sends commands via serial to Arduino
- Uses custom protocol: `0xAA 0x77 [Function] [Length] [ServoID] [Angle] [Checksum]`

### 3. Web Interface
- Live video feed with hand skeleton overlay
- Real-time finger extension bars
- Manual servo control sliders
- Status indicators for Arduino and model

## 🔧 Arduino Setup

### Required Arduino Program
Your Arduino needs to run one of these programs:
- `read_uhand.ino` - Manual potentiometer control
- `uhand_actions.ino` - Action group sequences
- Any program that accepts the serial protocol

### Serial Protocol
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

## 🎮 Web Interface Controls

### Hand Tracking
1. **Start Tracking**: Click "Start Tracking" button
2. **Show Hand**: Display your hand to the camera
3. **Move Fingers**: Control the robotic hand in real-time
4. **Stop Tracking**: Click "Stop Tracking" to end

### Manual Control
- **Sliders**: Adjust individual servo angles (0-180°)
- **Calibrate**: Reset all servos to center position (90°)
- **Real-time Updates**: See servo angles update as you move

### Status Indicators
- **Arduino**: Green = connected, Red = disconnected
- **Model**: Green = loaded, Red = loading/error

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
Set individual servo:
```bash
curl "http://localhost:3000/api/servo/0/90"
```

### POST `/api/servos`
Set all servos:
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

## 🎯 Next Steps

### For Demo Mode
1. Open http://localhost:3000
2. Click "Start Tracking"
3. Show your hand to the camera
4. Move your fingers to see the interface respond
5. Use manual sliders for precise control

### For Full Arduino Control
1. Connect your Arduino with the robotic hand
2. Upload the appropriate Arduino program
3. Run `npm start` instead of `npm run demo`
4. Follow the same steps as demo mode
5. Watch your robotic hand respond to your movements!

## 🎉 Success!

You now have a **professional-grade hand tracking system** that:
- Uses the latest TensorFlow.js HandPose technology
- Provides a beautiful, modern web interface
- Integrates seamlessly with Arduino
- Offers both automatic and manual control
- Works across all platforms

**Happy robot controlling! 🤖✨**
