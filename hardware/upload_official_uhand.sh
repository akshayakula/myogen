#!/bin/bash

# Upload Official Hiwonder uHand Code
echo "=== Official Hiwonder uHand Upload ==="

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

# Check if the official code exists
if [[ ! -f "blue_uhand/blue_uhand.ino" ]]; then
    echo "❌ Error: Official uHand code not found!"
    echo "Expected: blue_uhand/blue_uhand.ino"
    exit 1
fi

echo "🔨 Compiling and uploading official uHand code..."

# Compile and upload
arduino-cli compile --fqbn arduino:avr:uno blue_uhand
compile_result=$?

if [ $compile_result -eq 0 ]; then
    echo "✓ Compilation successful"
    echo "📤 Uploading to $ARDUINO_PORT..."
    
    arduino-cli upload -p "$ARDUINO_PORT" --fqbn arduino:avr:uno blue_uhand
    upload_result=$?
    
    if [ $upload_result -eq 0 ]; then
        echo ""
        echo "🎉 Official uHand code uploaded!"
        echo ""
        echo "✅ Now Arduino uses official Hiwonder protocol:"
        echo "   • Header: 0x55 0x55"
        echo "   • Function: 0x03 for servo control"
        echo "   • Servo range: 1100-1950 (not 0-180°)"
        echo ""
        echo "🧪 Test with:"
        echo "   python3 test_ble_official.py"
        echo ""
    else
        echo "❌ Upload failed!"
        exit 1
    fi
else
    echo "❌ Compilation failed!"
    echo "Check if FastLED library is installed:"
    echo "  arduino-cli lib install FastLED"
    exit 1
fi
