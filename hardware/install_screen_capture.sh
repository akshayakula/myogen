#!/bin/bash

# Install Screen Capture Dependencies for Hand Tracker
echo "=== Installing Screen Capture Dependencies ==="

echo "📦 Installing mss (Multi-Screen Shot) for screen capture..."
pip3 install mss

echo "📦 Installing Pillow for image processing..."
pip3 install Pillow

echo "✅ Screen capture dependencies installed!"
echo ""
echo "💡 Usage:"
echo "  - Run: python3 simple_hand_tracker.py"
echo "  - Choose option 2 for screen capture"
echo "  - Enter screen region coordinates"
echo ""
echo "🔧 Tips for finding coordinates:"
echo "  - macOS: Use 'Digital Color Meter' app"
echo "  - Linux: Use 'xwininfo' command"
echo "  - Windows: Use built-in Snipping Tool with ruler"
echo ""
