# How to Run Arduino (.ino) Files

## Quick Start Guide

### 🚀 Method 1: Arduino IDE (Easiest)

1. **Install Arduino IDE**:
   - Download from: https://arduino.cc/en/software
   - Install and launch

2. **Open your .ino file**:
   - File → Open → Select your `.ino` file
   - Or drag and drop the file into Arduino IDE

3. **Install Libraries** (if needed):
   - Tools → Manage Libraries
   - Search and install required libraries:
     - `FastLED` (for LED control)
     - `Servo` (for servo motors)

4. **Select Board & Port**:
   - Tools → Board → Arduino Uno
   - Tools → Port → Select your Arduino port

5. **Upload**:
   - Click upload button (→) or press `Ctrl+U` (`Cmd+U` on Mac)

### ⚡ Method 2: Command Line (Advanced)

#### Using the provided script:
```bash
# Make script executable (already done)
chmod +x upload_arduino.sh

# Upload your sketch
./upload_arduino.sh arduino_control.ino
./upload_arduino.sh "02 Brief Control Program/01 Read Action Data Program/read_uhand/read_uhand.ino"
```

#### Using arduino-cli directly:
```bash
# Install arduino-cli
brew install arduino-cli  # macOS
# or download from: https://arduino.github.io/arduino-cli/

# Initialize and install core
arduino-cli config init
arduino-cli core update-index
arduino-cli core install arduino:avr

# Upload sketch
arduino-cli compile --fqbn arduino:avr:uno arduino_control.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno arduino_control.ino
```

## 📁 Your Projects

### 1. Arduino Control System (`arduino_control.ino`)
- **Purpose**: Basic Arduino control with LEDs, sensors, and serial communication
- **Hardware**: LED, button, potentiometer, temperature sensor
- **Usage**: Control via Serial Monitor or Python script

### 2. Robotic Hand Control (`read_uhand.ino`)
- **Purpose**: Control 6 servo motors for robotic hand
- **Hardware**: 6 servos, RGB LED, buzzer, 6 potentiometers
- **Usage**: Analog control via potentiometers

## 🔧 Troubleshooting

### Common Issues:

1. **"Port not found"**:
   - Check USB connection
   - Try different USB cable
   - Restart Arduino IDE

2. **"Board not found"**:
   - Install Arduino Uno board package
   - Tools → Board → Boards Manager → Search "Arduino AVR Boards"

3. **"Library not found"**:
   - Tools → Manage Libraries → Search library name → Install

4. **"Upload failed"**:
   - Check if Arduino IDE Serial Monitor is open (close it)
   - Press reset button on Arduino
   - Try different USB port

### Port Detection:

**macOS/Linux**:
```bash
ls /dev/tty.*
# Look for: /dev/tty.usbmodem* or /dev/ttyUSB*
```

**Windows**:
- Check Device Manager → Ports (COM & LPT)
- Look for "Arduino Uno" or "CH340"

## 🎯 Quick Commands

```bash
# Upload the basic control system
./upload_arduino.sh arduino_control.ino

# Upload the robotic hand control
./upload_arduino.sh "02 Brief Control Program/01 Read Action Data Program/read_uhand/read_uhand.ino"

# Run Python controller (after uploading arduino_control.ino)
python arduino_controller.py --demo

# Run examples
python example_usage.py
```

## 📋 Hardware Setup

### For arduino_control.ino:
- Connect LED to pin 12 with 220Ω resistor
- Connect button to pin 2
- Connect potentiometer to A0
- Connect temperature sensor to A1

### For read_uhand.ino:
- Connect 6 servos to pins 2, 3, 4, 5, 6, 7
- Connect RGB LED to pin 13
- Connect buzzer to pin 11
- Connect 6 potentiometers to A0-A5

## 🎮 Testing

After uploading, you can:

1. **Open Serial Monitor** (Tools → Serial Monitor)
2. **Set baud rate** to 115200 (for read_uhand) or 9600 (for arduino_control)
3. **Send commands** or watch output

For the robotic hand, you should see servo angle data like:
```
{1 ,90 ,90 ,90 ,90 ,90 ,90},
```

For the control system, you can send commands like:
```
led_on
read_pot
status
```
