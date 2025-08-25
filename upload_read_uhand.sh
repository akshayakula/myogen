#!/bin/bash

echo "Robotic Hand Control Upload Script"
echo "=================================="

# Find Arduino port
PORT=$(ls /dev/tty.* | grep -E "(usb|modem)" | head -1)

if [ -z "$PORT" ]; then
    echo "❌ No Arduino port found!"
    echo "Please check USB connection"
    exit 1
fi

echo "✅ Found Arduino on port: $PORT"

# Check if read_uhand folder exists
if [ ! -d "read_uhand" ]; then
    echo "❌ read_uhand folder not found!"
    echo "Please make sure read_uhand.ino is in the read_uhand folder"
    exit 1
fi

# Compile read_uhand program
echo "📦 Compiling Robotic Hand Control program..."
arduino-cli compile --fqbn arduino:avr:uno read_uhand/

if [ $? -eq 0 ]; then
    echo "✅ Compilation successful!"
    
    echo "📤 Uploading to Arduino Uno..."
    arduino-cli upload -p "$PORT" --fqbn arduino:avr:uno read_uhand/
    
    if [ $? -eq 0 ]; then
        echo "✅ Upload successful!"
        echo ""
        echo "🎉 Robotic Hand Control program uploaded!"
        echo ""
        echo "Hardware Setup Required:"
        echo "======================="
        echo "• 6 Servos connected to pins: 2, 3, 4, 5, 6, 7"
        echo "• RGB LED connected to pin 13"
        echo "• Buzzer connected to pin 11"
        echo "• 6 Potentiometers connected to pins: A0, A1, A2, A3, A4, A5"
        echo ""
        echo "Testing:"
        echo "========"
        echo "1. Watch RGB LED - should be green initially"
        echo "2. Turn potentiometers to control servos"
        echo "3. Open Serial Monitor (115200 baud) to see servo data"
        echo "4. You should see output like: {1 ,90 ,90 ,90 ,90 ,90 ,90},"
        echo ""
        echo "To monitor serial output:"
        echo "arduino-cli monitor -p $PORT -c baudrate=115200"
    else
        echo "❌ Upload failed!"
        echo "Try pressing the reset button on Arduino and try again"
    fi
else
    echo "❌ Compilation failed!"
    echo "Check that FastLED and Servo libraries are installed"
fi
