#!/bin/bash

# Arduino Upload Script
# Requires arduino-cli to be installed

# Check if arduino-cli is installed
if ! command -v arduino-cli &> /dev/null; then
    echo "arduino-cli is not installed. Installing..."
    
    # Install arduino-cli (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install arduino-cli
    # Install arduino-cli (Linux)
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
        export PATH=$PATH:$HOME/bin
    else
        echo "Please install arduino-cli manually from: https://arduino.github.io/arduino-cli/"
        exit 1
    fi
fi

# Initialize arduino-cli
arduino-cli config init

# Update core index
arduino-cli core update-index

# Install Arduino Uno core
arduino-cli core install arduino:avr

# Function to upload sketch
upload_sketch() {
    local sketch_path="$1"
    local sketch_name=$(basename "$sketch_path" .ino)
    
    echo "Uploading $sketch_name..."
    
    # Compile and upload
    arduino-cli compile --fqbn arduino:avr:uno "$sketch_path"
    
    # Try to find the correct port
    PORT=$(ls /dev/tty.* | grep -E "(usb|modem)" | head -1)
    if [ -z "$PORT" ]; then
        echo "❌ No Arduino port found. Please check USB connection."
        exit 1
    fi
    
    echo "Using port: $PORT"
    arduino-cli upload -p "$PORT" --fqbn arduino:avr:uno "$sketch_path"
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully uploaded $sketch_name"
    else
        echo "❌ Failed to upload $sketch_name"
        exit 1
    fi
}

# Main script
echo "Arduino Upload Script"
echo "===================="

# Check if sketch path is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <path_to_sketch.ino>"
    echo ""
    echo "Examples:"
    echo "  $0 arduino_control.ino"
    echo "  $0 read_uhand.ino"
    exit 1
fi

sketch_path="$1"

# Check if file exists
if [ ! -f "$sketch_path" ]; then
    echo "Error: File $sketch_path not found"
    exit 1
fi

# Upload the sketch
upload_sketch "$sketch_path"

echo "Upload complete!"
