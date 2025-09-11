# BLE Pose Sender for Robotic Hand

A Python script that sends preset hand poses to the robotic hand via BLE connection. This script uses the proven BLE implementation from the hand tracker and provides an easy way to control the robotic hand with predefined gestures using simple keyboard input.

## 🚀 Features

- **10 Predefined Poses**: neutral, open, closed, thumbs_up, peace, point, grasp, rock_on, victory, fist
- **Continuous Keyboard Mode**: Press number keys (1-9, 0) to instantly send poses
- **BLE Connection**: Uses the same reliable BLE protocol as the hand tracker
- **Multiple Modes**: Continuous keyboard, single pose, demo, and list modes
- **Real-time Interface**: Clear screen display with instant feedback
- **Error Handling**: Robust error handling and connection management
- **Auto-cleanup**: Returns hand to neutral position on exit

## 📋 Available Poses

| Pose | Description | Servo Angles |
|------|-------------|--------------|
| `neutral` | Neutral position - all servos at 90° | [90, 90, 90, 90, 90, 90] |
| `open` | Open hand - fingers extended | [0, 180, 180, 180, 180, 90] |
| `closed` | Closed fist - fingers closed | [180, 0, 0, 25, 0, 90] |
| `thumbs_up` | Thumbs up - only thumb extended | [0, 0, 0, 25, 0, 90] |
| `peace` | Peace sign - index and middle extended | [180, 180, 180, 25, 0, 90] |
| `point` | Pointing - only index finger extended | [180, 180, 0, 25, 0, 90] |
| `grasp` | Moderate grasp - partial finger closure | [120, 60, 60, 85, 60, 90] |
| `rock_on` | Rock on sign - thumb, index, and pinky extended | [0, 180, 0, 25, 180, 90] |
| `victory` | Victory/V sign - index and middle extended | [180, 180, 180, 25, 0, 90] |
| `fist` | Tight fist - maximum closure | [180, 0, 0, 25, 0, 90] |

**Note**: These angles are corrected to account for the Arduino's servo inversion logic where the thumb (servo 0) and wrist (servo 5) are inverted at the hardware level.

## 🛠️ Prerequisites

1. **Hardware Setup**: Hiwonder BLE robotic hand powered on and nearby
2. **Python Environment**: Virtual environment with required packages
3. **BLE Support**: System with Bluetooth Low Energy support

## 📦 Installation

The script uses the existing virtual environment in the `hardware` directory:

```bash
cd hardware
source venv/bin/activate  # Activate virtual environment
```

Required packages (already installed in venv):
- `bleak` - BLE communication
- `asyncio` - Async programming

## 🎮 Usage

### Command Line Options

```bash
# Show help
python3 ble_pose_sender.py --help

# List all available poses
python3 ble_pose_sender.py --list

# Send a specific pose and exit
python3 ble_pose_sender.py --pose open

# Run demo mode (cycles through all poses)
python3 ble_pose_sender.py --demo

# Continuous keyboard mode (default)
python3 ble_pose_sender.py
```

### Continuous Keyboard Mode

When run without arguments, the script enters continuous keyboard mode with a real-time interface:

```
======================================================================
           🤖 BLE ROBOTIC HAND POSE CONTROLLER 🤖
======================================================================
📡 BLE Status: 🟢 CONNECTED
📱 Device: Hiwonder
======================================================================

🎯 SELECT A POSE (Press number key):
========================================
  1. neutral      - Neutral position - all servos at 90°
  2. open         - Open hand - fingers extended (ring min is 25°)
  3. closed       - Closed fist - fingers mostly closed
  4. thumbs_up    - Thumbs up - only thumb extended
  5. peace        - Peace sign - index and middle fingers extended
  6. point        - Pointing - only index finger extended
  7. grasp        - Moderate grasp - partial finger closure
  8. rock_on      - Rock on sign - thumb, index, and pinky extended
  9. victory      - Victory/V sign - index and middle fingers extended
  0. fist         - Tight fist - maximum closure (respecting servo limits)
========================================

⌨️  CONTROLS:
  1-9, 0  - Select pose by number
  'l'     - List poses again
  'd'     - Run demo mode
  'q'     - Quit

🎮 Press a key to select pose...
```

**Usage**: Simply press a number key (1-9, 0) to instantly send that pose to the robotic hand. The interface refreshes automatically and provides immediate feedback.

## 🎪 Demo Mode

Demo mode cycles through all poses with 2-second delays:

```bash
source venv/bin/activate
python3 ble_pose_sender.py --demo
```

Example output:
```
🎪 Demo Mode - Cycling through all poses...
Press Ctrl+C to stop demo

📤 Demo 1/10: neutral
   Description: Neutral position - all servos at 90°
   Angles: [90, 90, 90, 90, 90, 90]
✅ Sent successfully!

📤 Demo 2/10: open
   Description: Open hand - fingers extended (ring min is 25°)
   Angles: [90, 0, 0, 25, 0, 90]
✅ Sent successfully!

...

🎉 Demo completed!
🔄 Returning to neutral position...
```

## 🔧 Examples

### Quick Pose Commands

```bash
# Activate environment (run once per terminal session)
source venv/bin/activate

# Continuous keyboard mode (default) - most convenient!
python3 ble_pose_sender.py
# Then press: 1=neutral, 2=open, 3=closed, 4=thumbs_up, 5=peace, etc.

# Send specific poses from command line
python3 ble_pose_sender.py --pose neutral
python3 ble_pose_sender.py --pose thumbs_up
python3 ble_pose_sender.py --pose peace
python3 ble_pose_sender.py --pose fist

# Run full demo
python3 ble_pose_sender.py --demo
```

### Scripted Pose Sequences

You can create simple bash scripts to send pose sequences:

```bash
#!/bin/bash
# pose_sequence.sh
cd hardware
source venv/bin/activate

echo "Starting pose sequence..."
python3 ble_pose_sender.py --pose neutral
sleep 1
python3 ble_pose_sender.py --pose open
sleep 1
python3 ble_pose_sender.py --pose peace
sleep 1
python3 ble_pose_sender.py --pose thumbs_up
sleep 1
python3 ble_pose_sender.py --pose neutral
echo "Sequence complete!"
```

## 🔍 Troubleshooting

### Connection Issues

1. **Device Not Found**:
   ```
   ❌ Hiwonder device not found in scan
   ```
   - Ensure the robotic hand is powered on
   - Check that BLE is enabled on your system
   - Move closer to the device (within 10 meters)

2. **Connection Failed**:
   ```
   ❌ Connection error: [WinError 10054]
   ```
   - Restart the robotic hand
   - Try running the script again
   - Check if another device is already connected

3. **Module Not Found**:
   ```
   ModuleNotFoundError: No module named 'bleak'
   ```
   - Make sure to activate the virtual environment:
     ```bash
     source venv/bin/activate
     ```

### BLE Write Failures

1. **Write Failed**:
   ```
   ❌ BLE write failed: characteristic not found
   ```
   - Reconnect to the device
   - Restart the script
   - Check BLE device compatibility

## 🔌 Integration

The script can be easily integrated into other applications:

```python
import asyncio
from ble_pose_sender import connect_to_hiwonder_ble, send_pose, HAND_POSES

async def my_hand_control():
    # Connect to hand
    if await connect_to_hiwonder_ble():
        # Send poses
        await send_pose('open', HAND_POSES['open']['angles'])
        await asyncio.sleep(1)
        await send_pose('peace', HAND_POSES['peace']['angles'])
    
asyncio.run(my_hand_control())
```

## 📊 Technical Details

- **Protocol**: Official Hiwonder BLE servo control protocol
- **Packet Format**: Frame header + command + servo data + checksum
- **Servo Range**: 0-180° (mapped to 1100-1950 position values)
- **Connection**: Uses proven MAC address and service UUIDs from hand tracker
- **Async**: Full async/await support for non-blocking operation

### Servo Mapping Logic

The robotic hand uses specific servo inversion logic at the Arduino level:

```cpp
// Arduino servo control (from blue_uhand.ino)
servos[i].write(i == 0 || i == 5 ? 180 - servo_angles[i] : servo_angles[i]);
```

This means:
- **Thumb (Servo 0)**: Inverted - 0° = extended, 180° = closed
- **Index (Servo 1)**: Normal - 0° = closed, 180° = extended  
- **Middle (Servo 2)**: Normal - 0° = closed, 180° = extended
- **Ring (Servo 3)**: Normal - 25° = closed, 180° = extended (limited range)
- **Pinky (Servo 4)**: Normal - 0° = closed, 180° = extended
- **Wrist (Servo 5)**: Inverted - 0° = one direction, 180° = other direction

The pose angles in this script are already corrected to account for this inversion, so they will produce the expected hand movements.

## 🤝 Related Scripts

- `simple_hand_tracker.py` - Real-time hand tracking with BLE control
- `simple_servo_control_ble.py` - Manual servo control via BLE
- `test_ble_send.py` - BLE communication testing
- `robotic_hand_controller.py` - Serial-based hand control with poses

## 📝 License

Part of the Myogen robotic hand control system.
