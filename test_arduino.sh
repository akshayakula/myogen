#!/bin/bash

echo "Arduino Nano Test Script"
echo "======================="

# Create proper sketch folder structure
mkdir -p hello_world
cp hello_world.ino hello_world/

# Find Arduino port
PORT=$(ls /dev/tty.* | grep -E "(usb|modem)" | head -1)

if [ -z "$PORT" ]; then
    echo "❌ No Arduino port found!"
    echo "Please check:"
    echo "1. Arduino is connected via USB"
    echo "2. USB cable is working"
    echo "3. Arduino drivers are installed"
    exit 1
fi

echo "✅ Found Arduino on port: $PORT"

# Compile and upload
echo "📦 Compiling Hello World program..."
arduino-cli compile --fqbn arduino:avr:uno hello_world/

if [ $? -eq 0 ]; then
    echo "✅ Compilation successful!"
    
    echo "📤 Uploading to Arduino Uno..."
    arduino-cli upload -p "$PORT" --fqbn arduino:avr:uno hello_world/
    
    if [ $? -eq 0 ]; then
        echo "✅ Upload successful!"
        echo ""
        echo "🎉 Arduino Nano is working correctly!"
        echo ""
        echo "To test:"
        echo "1. Watch the built-in LED blink (pin 13)"
        echo "2. Open Serial Monitor in Arduino IDE"
        echo "3. Set baud rate to 9600"
        echo "4. You should see 'Hello World!' messages"
        echo "5. Type any character to test serial communication"
        echo ""
        echo "Or run: arduino-cli monitor -p $PORT -c baudrate=9600"
    else
        echo "❌ Upload failed!"
        echo "Try pressing the reset button on Arduino and try again"
    fi
else
    echo "❌ Compilation failed!"
fi
