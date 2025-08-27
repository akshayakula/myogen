#!/bin/bash

echo "Simple Servo Control Upload Script"
echo "=================================="

# Find Arduino port
ARDUINO_PORT=$(ls /dev/tty.* | grep -E "(usb|modem)" | head -1)

if [ -z "$ARDUINO_PORT" ]; then
    echo "❌ No Arduino found on USB ports"
    echo "Available ports:"
    ls /dev/tty.* 2>/dev/null || echo "No serial ports found"
    exit 1
fi

echo "✅ Found Arduino on port: $ARDUINO_PORT"

# Check if sketch file exists
if [ ! -f "simple_servo_arduino.ino" ]; then
    echo "❌ simple_servo_arduino.ino not found"
    exit 1
fi

echo "✅ Sketch file found"

# Create sketch directory (arduino-cli requirement)
mkdir -p simple_servo_arduino
cp simple_servo_arduino.ino simple_servo_arduino/

echo "📦 Compiling Simple Servo Control..."

# Compile the sketch
if arduino-cli compile --fqbn arduino:avr:uno simple_servo_arduino; then
    echo "✅ Compilation successful!"
else
    echo "❌ Compilation failed!"
    rm -rf simple_servo_arduino
    exit 1
fi

echo "📤 Uploading to Arduino Uno..."

# Upload to Arduino
if arduino-cli upload -p $ARDUINO_PORT --fqbn arduino:avr:uno simple_servo_arduino; then
    echo "✅ Upload successful!"
else
    echo "❌ Upload failed!"
    rm -rf simple_servo_arduino
    exit 1
fi

# Clean up
rm -rf simple_servo_arduino

echo ""
echo "🎉 Simple Servo Control program uploaded!"
echo ""
echo "Program Description:"
echo "==================="
echo "• Accepts serial commands for servo control"
echo "• Uses custom protocol: 0xAA 0x77 [Function] [Length] [Data...]"
echo "• Controls 6 servos with angle limits"
echo "• Servo inversion for thumb (0) and wrist (5)"
echo ""
echo "Hardware Setup:"
echo "==============="
echo "• 6 Servos connected to pins: 2, 3, 4, 5, 6, 7"
echo "• Arduino connected via USB"
echo ""
echo "Usage:"
echo "======"
echo "• Run: python3 simple_servo_control.py"
echo "• Use arrow keys to control servo angles"
echo "• Use number keys 1-6 to select servos"
echo "• Press ESC to quit"
echo ""
echo "To test connection:"
echo "arduino-cli monitor -p $ARDUINO_PORT -c baudrate=115200"
