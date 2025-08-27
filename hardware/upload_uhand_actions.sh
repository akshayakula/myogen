#!/bin/bash

echo "Robotic Hand Action Groups Upload Script"
echo "======================================="

# Find Arduino port
PORT=$(ls /dev/tty.* | grep -E "(usb|modem)" | head -1)

if [ -z "$PORT" ]; then
    echo "❌ No Arduino port found!"
    echo "Please check USB connection"
    exit 1
fi

echo "✅ Found Arduino on port: $PORT"

# Check if uhand_actions folder exists
if [ ! -d "uhand_actions" ]; then
    echo "❌ uhand_actions folder not found!"
    echo "Please make sure uhand_actions.ino and uhand_servo.h are in the uhand_actions folder"
    exit 1
fi

# Check if required files exist
if [ ! -f "uhand_actions/uhand_actions.ino" ]; then
    echo "❌ uhand_actions.ino not found!"
    exit 1
fi

if [ ! -f "uhand_actions/uhand_servo.h" ]; then
    echo "❌ uhand_servo.h not found!"
    exit 1
fi

echo "✅ All required files found"

# Compile uhand_actions program
echo "📦 Compiling Action Groups program..."
arduino-cli compile --fqbn arduino:avr:uno uhand_actions/

if [ $? -eq 0 ]; then
    echo "✅ Compilation successful!"
    
    echo "📤 Uploading to Arduino Uno..."
    arduino-cli upload -p "$PORT" --fqbn arduino:avr:uno uhand_actions/
    
    if [ $? -eq 0 ]; then
        echo "✅ Upload successful!"
        echo ""
        echo "🎉 Action Groups program uploaded!"
        echo ""
        echo "Program Description:"
        echo "==================="
        echo "• Runs predefined action groups for robotic hand"
        echo "• Executes Action Group 1 automatically"
        echo "• Provides smooth servo control with angle limits"
        echo "• Serial output shows action execution progress"
        echo ""
        echo "Hardware Setup Required:"
        echo "======================="
        echo "• 6 Servos connected to pins: 2, 3, 4, 5, 6, 7"
        echo "• Servo angle limits:"
        echo "  - Servo 1: 0-82°"
        echo "  - Servo 2: 0-180°"
        echo "  - Servo 3: 0-180°"
        echo "  - Servo 4: 25-180°"
        echo "  - Servo 5: 0-180°"
        echo "  - Servo 6: 0-180°"
        echo ""
        echo "Expected Behavior:"
        echo "=================="
        echo "1. 2-second delay on startup"
        echo "2. Prints 'start' to serial"
        echo "3. Executes Action Group 1"
        echo "4. Shows progress with dots: 'action run....'"
        echo "5. Prints 'The action group is running successfully!' when complete"
        echo ""
        echo "To monitor serial output:"
        echo "arduino-cli monitor -p $PORT -c baudrate=115200"
    else
        echo "❌ Upload failed!"
        echo "Try pressing the reset button on Arduino and try again"
    fi
else
    echo "❌ Compilation failed!"
    echo "Check that Servo library is installed"
fi
