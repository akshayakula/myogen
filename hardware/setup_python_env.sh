#!/bin/bash

echo "🐍 Setting up Python environment for Hand Tracker"

# Check if we're in the hardware directory
if [[ ! -f "simple_hand_tracker.py" ]]; then
    echo "❌ Please run this script from the hardware/ directory"
    exit 1
fi

echo "📋 Current Python version:"
python3 --version

echo ""
echo "📦 MediaPipe requires Python 3.8-3.12 (not 3.13+)"
echo "Current Python 3.13 is too new for MediaPipe."
echo ""
echo "🔧 Options to fix this:"
echo "1. Install Python 3.12 using pyenv or Homebrew"
echo "2. Use a different hand tracking library"
echo "3. Wait for MediaPipe to support Python 3.13"
echo ""

# Check if pyenv is available
if command -v pyenv &> /dev/null; then
    echo "✅ pyenv detected! You can install Python 3.12:"
    echo "   pyenv install 3.12.8"
    echo "   pyenv local 3.12.8"
    echo "   python3 -m venv venv_312"
    echo "   source venv_312/bin/activate"
    echo "   pip install -r requirements.txt"
    echo ""
fi

# Check if Homebrew is available  
if command -v brew &> /dev/null; then
    echo "✅ Homebrew detected! You can install Python 3.12:"
    echo "   brew install python@3.12"
    echo "   python3.12 -m venv venv_312"
    echo "   source venv_312/bin/activate"
    echo "   pip install -r requirements.txt"
    echo ""
fi

echo "🚀 Alternative: Try the servo control scripts that don't need MediaPipe:"
echo "   source venv/bin/activate"
echo "   python simple_servo_control_ble.py"
echo ""

echo "📱 Current virtual environment packages:"
if [[ -d "venv" ]]; then
    source venv/bin/activate 2>/dev/null && pip list | grep -E "(opencv|numpy|bleak|pyserial)" || echo "No venv activated"
fi
