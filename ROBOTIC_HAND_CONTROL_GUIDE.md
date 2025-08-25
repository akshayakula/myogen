# Robotic Hand Control Fundamentals

## 🤖 Overview

The robotic hand control system consists of **6 servo motors** that control different joints of the hand. Each servo can rotate from 0° to 180°, allowing the hand to perform various movements and gestures.

## 🏗️ Hardware Architecture

### Servo Configuration
```
Servo 1 (Pin 2): Base rotation (0-82°)     - Limited range
Servo 2 (Pin 3): Joint 1 (0-180°)          - Full range
Servo 3 (Pin 4): Joint 2 (0-180°)          - Full range
Servo 4 (Pin 5): Joint 3 (25-180°)         - Limited range
Servo 5 (Pin 6): Joint 4 (0-180°)          - Full range
Servo 6 (Pin 7): Joint 5 (0-180°)          - Full range
```

### Control Modes
1. **Manual Control** (`read_uhand.ino`) - Potentiometer-based
2. **Action Groups** (`uhand_actions.ino`) - Predefined movements
3. **Serial Control** - Computer-controlled movements

## 🎮 Control Fundamentals

### 1. Angle Control
Each servo is controlled by setting its angle (0-180°):
```cpp
servos[i].write(angle);  // Direct angle control
```

### 2. Smooth Movement
The system uses **interpolation** for smooth transitions:
```cpp
// Gradual angle change (85% current + 15% target)
servo_angles[i] = servo_angles[i] * 0.85 + target_angle * 0.15;
```

### 3. Angle Limits
Each servo has safety limits to prevent damage:
```cpp
const uint8_t limt_angles[6][2] = {
    {0,82},   // Servo 1: 0-82°
    {0,180},  // Servo 2: 0-180°
    {0,180},  // Servo 3: 0-180°
    {25,180}, // Servo 4: 25-180°
    {0,180},  // Servo 5: 0-180°
    {0,180}   // Servo 6: 0-180°
};
```

## 📊 Action Group System

### Structure
Action groups are **predefined movement sequences** stored in arrays:

```cpp
// Format: {enable, servo1, servo2, servo3, servo4, servo5, servo6}
static uint8_t action[action_count][20][7] = {
    // Action Group 1: Open/Close hand
    {{1,0,0,0,0,0,90},    // Step 1: Open position
     {1,180,180,180,180,180,90},  // Step 2: Closed position
     {1,0,0,0,0,0,90},    // Step 3: Back to open
     {0,0,0,0,0,0,0}},    // End marker
};
```

### Action Execution Process
1. **Set Action**: `action_ctl.action_set(1)` - Start Action Group 1
2. **Execute Steps**: Each step sets target angles for all servos
3. **Smooth Transition**: Servos move gradually to target positions
4. **Wait**: System waits for movement to complete
5. **Next Step**: Move to next step in sequence
6. **Complete**: Action group finishes

## 🔄 Control Flow

### Manual Control (read_uhand.ino)
```
Potentiometer → Analog Read → Angle Mapping → Servo Control
     ↓              ↓              ↓              ↓
   A0-A5 → 0-1023 → 0-180° → Smooth Interpolation → Servo Movement
```

### Action Group Control (uhand_actions.ino)
```
Action Group → Step Selection → Target Angles → Smooth Movement → Next Step
     ↓              ↓              ↓              ↓              ↓
   Predefined → Current Step → All Servos → Gradual Change → Complete Action
```

## 🎯 Key Control Concepts

### 1. **Position Control**
- Each servo has a specific target angle
- System smoothly moves from current to target position
- Movement speed controlled by interpolation factor

### 2. **Synchronization**
- All 6 servos move simultaneously
- Coordinated movement creates hand gestures
- Timing controlled by step delays

### 3. **Safety Limits**
- Angle limits prevent servo damage
- Smooth transitions prevent jerky movements
- Error checking for invalid commands

### 4. **Feedback Systems**
- Serial output shows current positions
- LED indicators show system status
- Buzzer provides audio feedback

## 📝 Programming the Hand

### Basic Servo Control
```cpp
// Set servo to specific angle
servos[0].write(90);  // Servo 1 to 90°

// Smooth movement
float target = 90;
servo_angles[0] = servo_angles[0] * 0.9 + target * 0.1;
servos[0].write(servo_angles[0]);
```

### Creating Custom Actions
```cpp
// Define new action group
uint8_t custom_action[][7] = {
    {1, 90, 90, 90, 90, 90, 90},  // Neutral position
    {1, 0, 180, 0, 180, 0, 180},  // Extended position
    {0, 0, 0, 0, 0, 0, 0}         // End marker
};
```

### Real-time Control
```cpp
// Read potentiometer and control servo
int pot_value = analogRead(A0);
int angle = map(pot_value, 0, 1023, 0, 180);
servos[0].write(angle);
```

## 🔧 Advanced Features

### 1. **Mode Switching**
- Manual control (potentiometers)
- Action group execution
- Serial command control
- Automatic mode detection

### 2. **Interpolation Control**
- Adjustable smoothness (0.85/0.15 ratio)
- Variable movement speed
- Acceleration/deceleration

### 3. **Error Handling**
- Angle limit enforcement
- Invalid command detection
- System status monitoring

## 🎮 Practical Applications

### 1. **Grasping Objects**
- Open hand → Approach object → Close hand
- Adjust grip strength via servo angles
- Maintain hold position

### 2. **Gesture Recognition**
- Predefined hand positions
- Smooth transitions between gestures
- Repeatable movements

### 3. **Interactive Control**
- Real-time potentiometer input
- Serial command interface
- Computer-controlled movements

## 🚀 Getting Started

### 1. **Basic Movement**
```cpp
// Move all servos to 90° (neutral)
for(int i = 0; i < 6; i++) {
    servos[i].write(90);
}
```

### 2. **Test Individual Servos**
```cpp
// Test each servo one by one
servos[0].write(0);   delay(1000);
servos[0].write(90);  delay(1000);
servos[0].write(180); delay(1000);
```

### 3. **Create Simple Gestures**
```cpp
// Thumbs up gesture
servos[0].write(90);   // Base
servos[1].write(180);  // Thumb up
servos[2].write(0);    // Other fingers down
servos[3].write(0);
servos[4].write(0);
servos[5].write(0);
```

This system provides a flexible foundation for robotic hand control, allowing both manual operation and automated sequences for various applications.
