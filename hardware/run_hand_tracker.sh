#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "=========================================="
echo "  HAND TRACKING VISION CONTROLLER"
echo "=========================================="
echo ""

# Check if --no-arduino flag is passed
if [ "$1" == "--no-arduino" ]; then
    python3 hand_tracker_vision.py --no-arduino
else
    # Try to run with Arduino, will fall back to simulation if not connected
    python3 hand_tracker_vision.py
fi