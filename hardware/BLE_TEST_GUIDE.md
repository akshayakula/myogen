# BLE Communication Test Guide

This guide will help you test BLE communication between your computer and the robotic hand Arduino.

## 🎯 What We're Testing

We've created a comprehensive BLE testing system:

1. **`ble_test_arduino.ino`** - Arduino sketch that receives and validates BLE data
2. **`test_ble_send.py`** - Python script that sends test poses via BLE
3. **Visual feedback** - LED colors show connection status and data validation

## 📋 Prerequisites

- Arduino with Hiwonder BLE module connected
- Python virtual environment with `bleak` library
- Arduino IDE or `arduino-cli` installed

## 🔧 Step-by-Step Testing

### Step 1: Upload the BLE Test Sketch

1. **Connect your Arduino via USB**
2. **Upload the test sketch:**
   ```bash
   ./upload_ble_test.sh
   ```

### Step 2: Monitor Arduino Output

**Open serial monitor to see detailed feedback:**
```bash
arduino-cli monitor -p /dev/cu.usbmodem* -c baudrate=115200
```

**You should see:**
```
=== BLE Test Arduino Sketch ===
Ready to receive BLE data...
Expected format: 0xAA 0x77 [Function] [Length] [Data...] [Checksum]

Heartbeat: Arduino is alive and listening...
```

### Step 3: Test BLE Communication

**In a new terminal, run the BLE sender:**
```bash
source venv/bin/activate
python3 test_ble_send.py
```

## 🚦 What to Expect

### LED Indicators:
- **🟢 Green**: Arduino is ready and listening
- **🔵 Blue**: Valid data packet received
- **🔴 Red**: Invalid data or checksum error
- **🟢 Dim Green**: No data received for 10+ seconds

### Serial Monitor Output:
For each valid packet, you'll see:
```
Valid header received: 0xAA 0x77
Function: 0x3, Length: 6
Received checksum: 0x2F, Calculated: 0x2F
✓ VALID PACKET RECEIVED!
Servo control data:
  Servo 0: 0°
  Servo 1: 0°
  Servo 2: 0°
  Servo 3: 25°
  Servo 4: 0°
  Servo 5: 0°
Raw packet: 0xAA 0x77 0x03 0x06 0x00 0x00 0x00 0x19 0x00 0x00 0x2F
```

### Python Script Output:
```
🔍 Scanning for Hiwonder BLE device...
Found 3 BLE devices:
  Hiwonder-BLE (XX:XX:XX:XX:XX:XX) - RSSI: -45
✓ Found Hiwonder device: XX:XX:XX:XX:XX:XX

🔗 Connecting to XX:XX:XX:XX:XX:XX...
✓ Connected!

🚀 Starting BLE test sequence...
📤 Test 1/6: Open Hand
   Description: All servos at minimum angles (fingers extended)
   Angles: [0, 0, 0, 25, 0, 0]
   Packet: 0xAA 0x77 0x03 0x06 0x00 0x00 0x00 0x19 0x00 0x00 0x2F
   ✓ Sent successfully
```

## 🎮 Test Sequences

The script sends 6 different hand poses:

1. **Open Hand** - All fingers extended
2. **Closed Fist** - All fingers closed  
3. **Pointing** - Only index finger extended
4. **Peace Sign** - Index and middle fingers extended
5. **Thumbs Up** - Only thumb extended
6. **Mid Position** - All servos at middle positions

## 🔍 Troubleshooting

### If Arduino Upload Fails:
- Check USB connection
- Press reset button before upload
- Verify port in upload script

### If BLE Device Not Found:
- Ensure Hiwonder module is powered
- Check it's not connected to another device
- Move closer to the module
- Try restarting the BLE module

### If Packets Fail Validation:
- Check for interference
- Verify BLE module firmware
- Try slower transmission rates

### If LEDs Don't Change:
- Verify FastLED library installation
- Check LED wiring (pin 2)
- Monitor serial output for errors

## ✅ Success Criteria

**The test is successful if you see:**
- ✓ BLE device discovered and connected
- ✓ All 6 test poses sent without errors
- ✓ Arduino shows blue LED for each valid packet
- ✓ Serial monitor shows packet validation details
- ✓ No checksum mismatches

## 🚀 Next Steps

Once BLE communication is verified:
1. Switch back to servo control sketch: `./upload_simple_servo.sh`
2. Test the full hand tracker: `python3 simple_hand_tracker.py`
3. Verify wireless hand pose control works end-to-end

## 📊 Protocol Details

**Packet Structure:**
```
[0xAA] [0x77] [0x03] [0x06] [S0] [S1] [S2] [S3] [S4] [S5] [Checksum]
 │      │      │      │      └─── Servo angles (0-180°)
 │      │      │      └─────────── Data length (6 bytes)
 │      │      └────────────────── Function (0x03 = servo control)
 │      └───────────────────────── Header byte 2
 └──────────────────────────────── Header byte 1
```

**Checksum = Sum of all bytes (except checksum) & 0xFF**
