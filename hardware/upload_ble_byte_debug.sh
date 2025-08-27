#!/bin/bash

# Upload BLE Byte Debug
echo "=== BLE Byte Debug Upload ==="

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
SKETCH_DIR="ble_byte_debug"
mkdir -p "$SKETCH_DIR"
cp ble_byte_debug.ino "$SKETCH_DIR/"

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
        echo "🔍 This will show exactly what bytes arrive via BLE"
        echo "📊 Expected: 0xAA 0x77 0x01 0x06 0x2D 0x2D 0x2D 0x2D 0x2D 0x2D 0xEA"
        echo ""
        echo "📋 Next steps:"
        echo "1. Monitor: arduino-cli monitor -p $ARDUINO_PORT -c baudrate=115200"
        echo "2. Send BLE: python3 test_ble_raw.py"
        echo "3. Compare expected vs actual bytes"
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
