#!/bin/bash

# Upload BLE Test Arduino Sketch
# This script compiles and uploads the BLE test sketch to Arduino

echo "=== BLE Test Arduino Upload Script ==="
echo "Uploading ble_test_arduino.ino..."

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
    echo "Please check that your Arduino is connected via USB."
    echo ""
    echo "Available ports:"
    ls /dev/cu.* /dev/tty* 2>/dev/null | grep -E "(usb|ACM|USB)" || echo "No USB/serial ports found"
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

# Install required libraries if not already installed
echo "📦 Checking required libraries..."

# Check and install FastLED
if ! arduino-cli lib list | grep -q "FastLED"; then
    echo "Installing FastLED library..."
    arduino-cli lib install "FastLED"
else
    echo "✓ FastLED library already installed"
fi

echo ""
echo "🔨 Compiling and uploading..."

# Compile and upload
arduino-cli compile --fqbn arduino:avr:uno ble_test_arduino.ino
compile_result=$?

if [ $compile_result -eq 0 ]; then
    echo "✓ Compilation successful"
    echo "📤 Uploading to $ARDUINO_PORT..."
    
    arduino-cli upload -p "$ARDUINO_PORT" --fqbn arduino:avr:uno ble_test_arduino.ino
    upload_result=$?
    
    if [ $upload_result -eq 0 ]; then
        echo ""
        echo "🎉 Upload successful!"
        echo ""
        echo "The BLE test sketch is now running on your Arduino."
        echo ""
        echo "What this sketch does:"
        echo "• Listens for BLE data on serial port"
        echo "• Validates the custom protocol format"
        echo "• Shows LED status (Green=Ready, Blue=Data received, Red=Error)"
        echo "• Prints detailed debugging information"
        echo ""
        echo "Next steps:"
        echo "1. Open Serial Monitor at 115200 baud to see output"
        echo "2. Run the Python BLE test script to send data"
        echo "3. Watch for validation messages and LED changes"
        echo ""
        echo "Monitor serial output with:"
        echo "  arduino-cli monitor -p $ARDUINO_PORT -c baudrate=115200"
    else
        echo "❌ Upload failed!"
        echo ""
        echo "Troubleshooting:"
        echo "• Try pressing the reset button on Arduino before upload"
        echo "• Check that no other programs are using the serial port"
        echo "• Verify the Arduino is properly connected"
        exit 1
    fi
else
    echo "❌ Compilation failed!"
    echo "Please check the code for errors."
    exit 1
fi
