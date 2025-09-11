#!/bin/bash

# Upload Myogen Sketch with Gyro BLE Support
echo "=== Myogen Sketch Upload ==="

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

# Check if the myogen sketch exists
if [[ ! -f "myogen_sketch/myogen_sketch.ino" ]]; then
    echo "❌ Error: myogen_sketch/myogen_sketch.ino not found!"
    exit 1
fi

echo "🔨 Compiling and uploading myogen sketch..."

# Compile and upload
arduino-cli compile --fqbn arduino:avr:uno myogen_sketch
compile_result=$?

if [ $compile_result -eq 0 ]; then
    echo "✓ Compilation successful"
    echo "📤 Uploading to $ARDUINO_PORT..."
    
    arduino-cli upload -p "$ARDUINO_PORT" --fqbn arduino:avr:uno myogen_sketch
    upload_result=$?
    
    if [ $upload_result -eq 0 ]; then
        echo ""
        echo "🎉 Myogen sketch uploaded!"
        echo ""
        echo "✅ Features enabled:"
        echo "   • 6-axis gyro/accelerometer reading (MPU6050)"
        echo "   • BLE gyro data transmission"
        echo "   • Servo control via BLE"
        echo "   • Startup finger movement test"
        echo ""
        echo "🧪 Test gyro data reception:"
        echo "   python3 ble_gyro_receiver.py"
        echo ""
        echo "📊 Or monitor serial output:"
        echo "   arduino-cli monitor -p $ARDUINO_PORT -c baudrate=9600"
        echo ""
    else
        echo "❌ Upload failed!"
        exit 1
    fi
else
    echo "❌ Compilation failed!"
    echo "Check if required libraries are installed:"
    echo "  arduino-cli lib install FastLED"
    echo "  arduino-cli lib install Servo"
    exit 1
fi
