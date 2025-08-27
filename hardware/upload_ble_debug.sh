#!/bin/bash

# Upload BLE LED Debug Test
echo "=== BLE LED Debug Upload ==="
echo "Uploading ble_led_debug.ino..."

# Function to detect Arduino port
detect_arduino_port() {
    local ports=(
        "/dev/cu.usbmodem*"
        "/dev/cu.usbserial*" 
        "/dev/cu.wchusbserial*"
        "/dev/ttyUSB*"
        "/dev/ttyACM*"
    )
    
    for pattern in "${ports[@]}"; do
        for port in $pattern; do
            if [[ -e "$port" ]]; then
                echo "$port"
                return 0
            fi
        done
    done
    
    return 1
}

# Detect the Arduino port
ARDUINO_PORT=$(detect_arduino_port)

if [[ -z "$ARDUINO_PORT" ]]; then
    echo "❌ Error: No Arduino found!"
    exit 1
fi

echo "📍 Using Arduino port: $ARDUINO_PORT"

# Create a temporary directory for the sketch
SKETCH_DIR="ble_led_debug"
mkdir -p "$SKETCH_DIR"
cp ble_led_debug.ino "$SKETCH_DIR/"

echo "🔨 Compiling and uploading..."

# Compile and upload
arduino-cli compile --fqbn arduino:avr:uno "$SKETCH_DIR"
compile_result=$?

if [ $compile_result -eq 0 ]; then
    echo "✓ Compilation successful"
    echo "📤 Uploading to $ARDUINO_PORT..."
    
    arduino-cli upload -p "$ARDUINO_PORT" --fqbn arduino:avr:uno "$SKETCH_DIR"
    upload_result=$?
    
    if [ $upload_result -eq 0 ]; then
        echo ""
        echo "🎉 Debug sketch uploaded!"
        echo ""
        echo "🔍 This debug version will show:"
        echo "• Exact bytes received (hex, decimal, character)"
        echo "• Number of bytes in each packet"
        echo "• LED state changes"
        echo "• Timing of events"
        echo ""
        echo "📊 Monitor output with:"
        echo "  arduino-cli monitor -p $ARDUINO_PORT -c baudrate=115200"
        echo ""
        echo "🧪 Then test with:"
        echo "  python3 test_ble_led.py"
        echo ""
    else
        echo "❌ Upload failed!"
        rm -rf "$SKETCH_DIR"
        exit 1
    fi
else
    echo "❌ Compilation failed!"
    rm -rf "$SKETCH_DIR"
    exit 1
fi

# Clean up temporary directory
rm -rf "$SKETCH_DIR"
