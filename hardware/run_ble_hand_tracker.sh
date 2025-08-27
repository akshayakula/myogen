#!/bin/bash

# Script to run hand tracker with BLE-Serial bridge for Hiwonder BLE module

echo "🤖 Starting BLE Hand Tracker with Hiwonder BLE module"
echo "======================================================"

# Check if ble-serial is installed
if ! command -v ble-serial &> /dev/null; then
    echo "❌ ble-serial not found!"
    echo "💡 Install it with: pip install ble-serial"
    echo "💡 Or: brew install ble-serial"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo -e "\n🛑 Cleaning up..."
    if [ ! -z "$BLE_PID" ]; then
        kill $BLE_PID 2>/dev/null
        echo "   Stopped BLE-Serial bridge"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "📶 Starting BLE-Serial bridge for Hiwonder-BLE..."
echo "💡 Make sure your Hiwonder BLE module is powered on and discoverable"

# Start ble-serial in background
ble-serial -d "Hiwonder-BLE" &
BLE_PID=$!

# Wait a moment for the bridge to establish
echo "⏳ Waiting for BLE connection to establish..."
sleep 5

# Check if ble-serial is still running
if ! kill -0 $BLE_PID 2>/dev/null; then
    echo "❌ BLE-Serial bridge failed to start"
    echo "💡 Check if 'Hiwonder-BLE' device is discoverable"
    echo "💡 You can also try scanning first: ble-serial -s"
    exit 1
fi

echo "✅ BLE-Serial bridge started (PID: $BLE_PID)"
echo "📱 Starting hand tracker..."
echo "💡 Press Ctrl+C to stop both the hand tracker and BLE bridge"

# Activate virtual environment and run hand tracker
source venv/bin/activate
python3 simple_hand_tracker.py

# Cleanup will be called automatically on exit
