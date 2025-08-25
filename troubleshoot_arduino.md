# Arduino Connection Troubleshooting

## Quick Test: Arduino Blink

The simplest way to test if your Arduino is working:

1. **Upload the blink program** (blink.ino)
2. **Watch the built-in LED** (pin 13) - it should blink every second
3. **No serial communication needed** - just visual confirmation

## Common Upload Issues & Solutions

### 1. "Programmer is not responding"

**Symptoms**: `avrdude: stk500_recv(): programmer is not responding`

**Solutions**:
- **Press the reset button** on Arduino before uploading
- **Try a different USB cable** (some cables are power-only)
- **Check USB port** - try a different USB port
- **Close Serial Monitor** if it's open in Arduino IDE
- **Wait 2-3 seconds** after pressing reset before uploading

### 2. "Port not found"

**Symptoms**: No Arduino port detected

**Solutions**:
- **Check USB connection**
- **Install Arduino drivers** (especially for CH340 chips)
- **Try different USB cable**
- **Restart computer**

### 3. "Board not found"

**Symptoms**: Arduino board not recognized

**Solutions**:
- **Install Arduino AVR Boards** in Arduino IDE
- **Select correct board**: Tools → Board → Arduino Nano
- **Select correct processor**: Tools → Processor → ATmega328P (Old Bootloader)

## Step-by-Step Test Process

### Step 1: Basic Connection Test
```bash
# Check if Arduino is detected
ls /dev/tty.* | grep -E "(usb|modem)"
```

### Step 2: Try Arduino IDE
1. Open Arduino IDE
2. File → Open → blink.ino
3. Tools → Board → Arduino Nano
4. Tools → Processor → ATmega328P (Old Bootloader)
5. Tools → Port → Select your port
6. Upload (→ button)

### Step 3: Visual Test
- **Built-in LED should blink** every second
- **No serial communication needed**
- **If LED blinks = Arduino is working!**

### Step 4: Serial Test (Optional)
If blink works, try the hello_world.ino program:
1. Upload hello_world.ino
2. Open Serial Monitor
3. Set baud rate to 9600
4. Should see "Hello World!" messages

## Hardware Checklist

- [ ] Arduino Nano connected via USB
- [ ] USB cable supports data (not just power)
- [ ] Built-in LED visible (pin 13)
- [ ] No other programs using the serial port
- [ ] Arduino drivers installed (if needed)

## Different Arduino Models

**Arduino Nano (Old Bootloader)**:
- Board: "Arduino Nano"
- Processor: "ATmega328P (Old Bootloader)"

**Arduino Nano (New Bootloader)**:
- Board: "Arduino Nano"
- Processor: "ATmega328P"

**Arduino Uno**:
- Board: "Arduino Uno"

## Command Line Alternative

If Arduino IDE works but command line doesn't:
```bash
# Use Arduino IDE for uploading
# Use command line for monitoring
arduino-cli monitor -p /dev/tty.usbmodem11401 -c baudrate=9600
```

## Success Indicators

✅ **Arduino is working if**:
- Built-in LED blinks after upload
- No error messages during upload
- Port is detected correctly

❌ **Arduino has issues if**:
- LED doesn't blink
- Upload fails repeatedly
- Port not detected
- "Programmer not responding" errors
