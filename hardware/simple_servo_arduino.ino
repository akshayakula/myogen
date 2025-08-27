#include <Servo.h>

// Servo pins
const static uint8_t servoPins[6] = { 7, 6, 5, 4, 3, 2 };

// Protocol constants
const uint8_t CONST_STARTBYTE1 = 0xAA;
const uint8_t CONST_STARTBYTE2 = 0x77;
const uint8_t FUNC_SET_SERVO = 0x01;

// Servo objects and angles
Servo servos[6];
uint8_t servo_angles[6] = { 90, 90, 90, 90, 90, 90 };

// Servo limits
const uint8_t servo_limits[6][2] = {{0,180},{0,180},{0,180},{25,180},{0,180},{0,180}};

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(100);
  
  // Initialize servos
  for (int i = 0; i < 6; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(90); // Start at center position
  }
  
  Serial.println("Simple Servo Control Ready");
  Serial.println("Waiting for commands...");
}

void loop() {
  // Check for serial data
  if (Serial.available() >= 8) { // Minimum packet size
    processSerialCommand();
  }
  
  delay(10);
}

uint8_t calculateChecksum(uint8_t* data, uint8_t len) {
  uint8_t checksum = 0;
  for (int i = 0; i < len; i++) {
    checksum += data[i];
  }
  return ~checksum & 0xFF;
}

void processSerialCommand() {
  uint8_t buffer[15]; // Buffer for complete packet
  
  // Read complete packet: 2 start bytes + function + length + 6 servo bytes + checksum = 11 bytes
  if (Serial.readBytes(buffer, 11) == 11) {
    // Check start bytes
    if (buffer[0] == CONST_STARTBYTE1 && buffer[1] == CONST_STARTBYTE2) {
      uint8_t function = buffer[2];
      uint8_t length = buffer[3];
      
      if (function == FUNC_SET_SERVO && length == 6) {
        // Validate checksum
        uint8_t received_checksum = buffer[10];
        uint8_t calculated_checksum = calculateChecksum(&buffer[2], 8); // function + length + 6 servo bytes
        
        if (received_checksum == calculated_checksum) {
          // Update servo angles
          for (int i = 0; i < 6; i++) {
            uint8_t new_angle = buffer[4 + i]; // Servo data starts at index 4
            
            // Apply servo limits
            uint8_t min_angle = servo_limits[i][0];
            uint8_t max_angle = servo_limits[i][1];
            new_angle = constrain(new_angle, min_angle, max_angle);
            
            // Only update if angle changed significantly (reduce jitter)
            if (abs(servo_angles[i] - new_angle) >= 2) {
              servo_angles[i] = new_angle;
              
              // Write to servo (with inversion for thumb and wrist)
              if (i == 0 || i == 5) {
                servos[i].write(180 - servo_angles[i]);
              } else {
                servos[i].write(servo_angles[i]);
              }
            }
          }
          
          // Debug output
          Serial.print("OK: ");
          for (int i = 0; i < 6; i++) {
            Serial.print(servo_angles[i]);
            if (i < 5) Serial.print(",");
          }
          Serial.println();
        } else {
          Serial.println("Checksum error");
        }
      } else {
        Serial.println("Invalid function or length");
      }
    } else {
      Serial.println("Invalid start bytes");
    }
  }
  
  // Clear any remaining bytes
  while (Serial.available()) {
    Serial.read();
  }
}
