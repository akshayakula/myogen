#!/bin/bash

# Upload Simple BLE LED Test
echo "=== Simple BLE LED Test Upload ==="
echo "Uploading ble_led_test.ino..."

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
    echo "Please connect your Arduino via USB."
    exit 1
fi

echo "📍 Using Arduino port: $ARDUINO_PORT"

# Check if arduino-cli is installed
if ! command -v arduino-cli &> /dev/null; then
    echo "❌ Error: arduino-cli not found!"
    echo "Please install arduino-cli first:"
    echo "  brew install arduino-cli"
    exit 1
fi

echo "🔨 Compiling and uploading..."

# Create a temporary directory for the sketch
SKETCH_DIR="ble_led_test"
mkdir -p "$SKETCH_DIR"
cp ble_led_test.ino "$SKETCH_DIR/"

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
        echo "🎉 Upload successful!"
        echo ""
        echo "💡 What this sketch does:"
        echo "• Listens for single-byte commands via serial/BLE"
        echo "• Controls built-in LED (Pin 13)"
        echo "• '1' = LED ON, '0' = LED OFF, 'B' = Fast blink"
        echo ""
        echo "🧪 Next steps:"
        echo "1. Open serial monitor: arduino-cli monitor -p $ARDUINO_PORT -c baudrate=115200"
        echo "2. Run Python test: python3 test_ble_led.py"
        echo "3. Watch the LED respond to BLE commands!"
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
