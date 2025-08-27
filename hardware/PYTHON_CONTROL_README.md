# Python Robotic Hand Controller

A comprehensive Python library for controlling the robotic hand via serial communication. This controller implements the serial protocol defined in the Arduino code and provides an easy-to-use interface for controlling all aspects of the robotic hand.

## 🚀 Features

- **Full Hand Control**: Control all 6 servo motors independently
- **Predefined Gestures**: Built-in hand positions (neutral, open, closed, thumbs up, etc.)
- **Smooth Movements**: Interpolated movements for natural hand motion
- **RGB LED Control**: Control the RGB LED for visual feedback
- **Buzzer Control**: Control the buzzer for audio feedback
- **Real-time Monitoring**: Monitor hand responses and status
- **Custom Gestures**: Create and save custom hand positions
- **Multiple Control Modes**: Interactive, programmatic, and command-line control

## 📋 Requirements

- Python 3.7+
- pyserial library
- Arduino with robotic hand program uploaded

## 🔧 Installation

1. **Install Python dependencies**:
   ```bash
   pip install pyserial
   ```

2. **Upload Arduino program**: Make sure you have the serial communication program uploaded to your Arduino

3. **Connect hardware**: Ensure the robotic hand is properly connected

## 🎮 Quick Start

### Basic Usage

```python
from robotic_hand_controller import RoboticHandController

# Create controller (auto-detects port)
controller = RoboticHandController()

# Connect to hand
if controller.connect():
    # Move to predefined positions
    controller.move_to_position('open')
    controller.move_to_position('closed')
    controller.move_to_position('thumbs_up')
    
    # Set specific angles
    controller.set_servo_angles([90, 45, 90, 90, 90, 90])
    
    # Control RGB LED
    controller.set_rgb_led(255, 0, 0)  # Red
    
    # Control buzzer
    controller.set_buzzer(1000, 500)  # 1kHz for 500ms
    
    controller.disconnect()
```

### Command Line Usage

```bash
# Interactive mode
python robotic_hand_controller.py

# Demo mode
python robotic_hand_controller.py --demo

# Move to specific position
python robotic_hand_controller.py --position open

# Set specific angles
python robotic_hand_controller.py --angles "90,45,90,90,90,90"
```

## 📖 API Reference

### RoboticHandController Class

#### Initialization
```python
controller = RoboticHandController(port=None, baud_rate=9600)
```

#### Connection Methods
```python
controller.connect() -> bool          # Connect to robotic hand
controller.disconnect()               # Disconnect from hand
```

#### Servo Control
```python
controller.set_servo_angles(angles: List[int]) -> bool
controller.set_hand_position(position: HandPosition) -> bool
controller.move_to_position(position_name: str) -> bool
controller.smooth_move(target_position: HandPosition, steps=10, delay=0.1)
```

#### Predefined Positions
- `'neutral'`: Neutral position (90° for all servos)
- `'open'`: Open hand (0° for fingers)
- `'closed'`: Closed hand (180° for fingers)
- `'thumbs_up'`: Thumbs up gesture
- `'peace'`: Peace sign
- `'point'`: Pointing gesture
- `'grasp'`: Grasping position

#### Accessory Control
```python
controller.set_rgb_led(red: int, green: int, blue: int) -> bool
controller.set_buzzer(frequency: int, duration_ms: int) -> bool
controller.read_angles() -> Optional[List[int]]
```

#### Gesture Methods
```python
controller.wave_gesture()                    # Perform waving gesture
controller.grasp_object(strength: int = 90)  # Grasp object with specified strength
controller.create_gesture(name: str, angles: List[int])  # Create custom gesture
```

#### Status and Monitoring
```python
controller.get_status() -> dict              # Get current status
```

### HandPosition Class

```python
position = HandPosition(servo1=90, servo2=90, servo3=90, servo4=90, servo5=90, servo6=90)
position.to_array() -> List[int]             # Convert to angle array
HandPosition.from_array(angles: List[int])   # Create from angle array
```

## 🎯 Usage Examples

### Interactive Control
```python
# Start interactive mode
python robotic_hand_controller.py

# Available commands:
# move open          - Move to open position
# move closed        - Move to closed position
# angles 90 45 90 90 90 90  - Set specific angles
# wave               - Perform wave gesture
# grasp 120          - Grasp with strength 120
# rgb 255 0 0        - Set RGB to red
# buzzer 1000 500    - Buzzer at 1kHz for 500ms
# read               - Read current angles
# status             - Show status
# quit               - Exit
```

### Programmatic Control
```python
from robotic_hand_controller import RoboticHandController, HandPosition
import time

controller = RoboticHandController()
controller.connect()

try:
    # Create custom gesture
    controller.create_gesture('custom_wave', [90, 0, 45, 0, 0, 0])
    
    # Perform sequence
    controller.move_to_position('neutral')
    time.sleep(1)
    
    controller.move_to_position('open')
    time.sleep(1)
    
    controller.wave_gesture()
    time.sleep(1)
    
    controller.grasp_object(strength=120)
    time.sleep(2)
    
    # Smooth movement
    start_pos = HandPosition(90, 0, 0, 0, 0, 0)
    end_pos = HandPosition(90, 180, 180, 180, 180, 180)
    controller.smooth_move(end_pos, steps=20, delay=0.1)
    
finally:
    controller.disconnect()
```

### Complex Gestures
```python
# Counting gesture (1-5 fingers)
finger_sequences = [
    [90, 180, 0, 0, 0, 0],      # 1 finger
    [90, 180, 180, 0, 0, 0],    # 2 fingers
    [90, 180, 180, 180, 0, 0],  # 3 fingers
    [90, 180, 180, 180, 180, 0], # 4 fingers
    [90, 180, 180, 180, 180, 180], # 5 fingers
]

for i, angles in enumerate(finger_sequences, 1):
    print(f"Showing {i} finger(s)...")
    controller.set_servo_angles(angles)
    time.sleep(1)
```

## 🔧 Hardware Setup

### Servo Connections
- **Servo 1** (Pin 2): Base rotation (0-82°)
- **Servo 2** (Pin 3): Joint 1 (0-180°)
- **Servo 3** (Pin 4): Joint 2 (0-180°)
- **Servo 4** (Pin 5): Joint 3 (25-180°)
- **Servo 5** (Pin 6): Joint 4 (0-180°)
- **Servo 6** (Pin 7): Joint 5 (0-180°)

### Accessories
- **RGB LED** (Pin 13): Visual feedback
- **Buzzer** (Pin 11): Audio feedback

## 📊 Protocol Details

The controller uses a custom serial protocol:

### Packet Format
```
[0xAA] [0x77] [Function] [Length] [Data...] [Checksum]
```

### Function Codes
- `0x01`: Set servo angles
- `0x02`: Set buzzer
- `0x03`: Set RGB LED
- `0x11`: Read angles

### Data Formats
- **Servo Control**: 6 bytes (one per servo angle)
- **Buzzer Control**: 4 bytes (frequency, duration)
- **RGB Control**: 3 bytes (red, green, blue)

## 🚨 Safety Features

- **Angle Limits**: Automatic validation of servo angles
- **Smooth Movements**: Prevents jerky motion and servo stress
- **Error Handling**: Robust error checking and recovery
- **Connection Monitoring**: Automatic detection of connection issues

## 🎮 Advanced Features

### Custom Gestures
```python
# Create and save custom gestures
controller.create_gesture('victory', [90, 0, 180, 0, 180, 0])
controller.create_gesture('rock_on', [90, 180, 0, 180, 0, 180])

# Use custom gestures
controller.move_to_position('victory')
```

### Smooth Movements
```python
# Smooth movement with custom parameters
controller.smooth_move(target_position, steps=30, delay=0.05)
```

### Status Monitoring
```python
# Get detailed status
status = controller.get_status()
print(f"Connected: {status['connected']}")
print(f"Current position: {status['current_position']}")
print(f"Available positions: {status['available_positions']}")
```

## 🔍 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check USB connection
   - Verify correct port
   - Ensure Arduino program is uploaded

2. **Servo Not Moving**
   - Check servo connections
   - Verify power supply
   - Check angle limits

3. **Communication Errors**
   - Check baud rate (default: 9600)
   - Verify serial port is not in use
   - Restart Arduino

### Debug Mode
```python
# Enable debug output
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Examples

See `hand_control_example.py` for comprehensive examples including:
- Basic control
- Gesture sequences
- Smooth movements
- Interactive control
- Programmatic control
- Status monitoring

## 🤝 Contributing

Feel free to contribute by:
- Adding new gestures
- Improving error handling
- Adding new features
- Fixing bugs

## 📄 License

This project is open source and available under the MIT License.
