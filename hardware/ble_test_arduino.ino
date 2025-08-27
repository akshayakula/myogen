/*
 * BLE Test Arduino Sketch
 * 
 * This sketch tests BLE communication with the Hiwonder module
 * It receives data via serial (USB or BLE) and provides feedback
 * 
 * Expected data format: 0xAA 0x77 [Function] [Length] [Data...] [Checksum]
 * 
 * LED Indicators:
 * - Green: Ready/Idle
 * - Blue: Data received
 * - Red: Error/Invalid data
 */

#include <FastLED.h>

// LED Configuration
#define LED_PIN 2
#define NUM_LEDS 1
CRGB leds[NUM_LEDS];

// Serial Protocol Constants
#define HEADER1 0xAA
#define HEADER2 0x77
#define FUNCTION_SERVO_CONTROL 0x03

// Timing
unsigned long lastDataTime = 0;
unsigned long ledChangeTime = 0;
bool dataReceived = false;

void setup() {
  Serial.begin(115200);
  
  // Initialize LED
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(50);
  
  // Start with green (ready)
  leds[0] = CRGB::Green;
  FastLED.show();
  
  Serial.println("=== BLE Test Arduino Sketch ===");
  Serial.println("Ready to receive BLE data...");
  Serial.println("Expected format: 0xAA 0x77 [Function] [Length] [Data...] [Checksum]");
  Serial.println();
}

void loop() {
  // Check for incoming serial data
  if (Serial.available() >= 4) {  // Minimum packet size
    processSerialData();
  }
  
  // Handle LED timing
  handleLEDStatus();
  
  // Send periodic heartbeat
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 5000) {  // Every 5 seconds
    Serial.println("Heartbeat: Arduino is alive and listening...");
    lastHeartbeat = millis();
  }
}

void processSerialData() {
  uint8_t buffer[64];
  int bytesRead = 0;
  
  // Read first byte and check for header
  if (Serial.read() == HEADER1) {
    buffer[bytesRead++] = HEADER1;
    
    // Wait for more data with timeout
    unsigned long timeout = millis() + 100;
    while (Serial.available() < 1 && millis() < timeout) {
      delay(1);
    }
    
    if (Serial.available() >= 1) {
      uint8_t secondByte = Serial.read();
      buffer[bytesRead++] = secondByte;
      
      if (secondByte == HEADER2) {
        Serial.print("Valid header received: 0x");
        Serial.print(HEADER1, HEX);
        Serial.print(" 0x");
        Serial.println(HEADER2, HEX);
        
        // Read function and length
        timeout = millis() + 100;
        while (Serial.available() < 2 && millis() < timeout) {
          delay(1);
        }
        
        if (Serial.available() >= 2) {
          uint8_t function = Serial.read();
          uint8_t length = Serial.read();
          buffer[bytesRead++] = function;
          buffer[bytesRead++] = length;
          
          Serial.print("Function: 0x");
          Serial.print(function, HEX);
          Serial.print(", Length: ");
          Serial.println(length);
          
          // Read data bytes
          timeout = millis() + 100;
          while (Serial.available() < length + 1 && millis() < timeout) {  // +1 for checksum
            delay(1);
          }
          
          if (Serial.available() >= length + 1) {
            // Read data
            for (int i = 0; i < length; i++) {
              buffer[bytesRead++] = Serial.read();
            }
            
            // Read checksum
            uint8_t receivedChecksum = Serial.read();
            buffer[bytesRead++] = receivedChecksum;
            
            // Calculate expected checksum
            uint8_t calculatedChecksum = 0;
            for (int i = 0; i < bytesRead - 1; i++) {
              calculatedChecksum += buffer[i];
            }
            
            Serial.print("Received checksum: 0x");
            Serial.print(receivedChecksum, HEX);
            Serial.print(", Calculated: 0x");
            Serial.println(calculatedChecksum, HEX);
            
            if (receivedChecksum == calculatedChecksum) {
              Serial.println("✓ VALID PACKET RECEIVED!");
              
              if (function == FUNCTION_SERVO_CONTROL && length == 6) {
                Serial.println("Servo control data:");
                for (int i = 0; i < 6; i++) {
                  Serial.print("  Servo ");
                  Serial.print(i);
                  Serial.print(": ");
                  Serial.print(buffer[4 + i]);
                  Serial.println("°");
                }
              }
              
              // Flash blue for success
              leds[0] = CRGB::Blue;
              FastLED.show();
              dataReceived = true;
              ledChangeTime = millis();
              
            } else {
              Serial.println("✗ CHECKSUM MISMATCH!");
              // Flash red for error
              leds[0] = CRGB::Red;
              FastLED.show();
              ledChangeTime = millis();
            }
            
            lastDataTime = millis();
            
            // Print raw packet for debugging
            Serial.print("Raw packet: ");
            for (int i = 0; i < bytesRead; i++) {
              Serial.print("0x");
              if (buffer[i] < 16) Serial.print("0");
              Serial.print(buffer[i], HEX);
              Serial.print(" ");
            }
            Serial.println();
            Serial.println();
            
          } else {
            Serial.println("✗ Timeout waiting for data/checksum");
          }
        } else {
          Serial.println("✗ Timeout waiting for function/length");
        }
      } else {
        Serial.print("✗ Invalid second header byte: 0x");
        Serial.println(secondByte, HEX);
      }
    } else {
      Serial.println("✗ Timeout waiting for second header byte");
    }
  }
  
  // Clear any remaining bytes
  while (Serial.available()) {
    Serial.read();
  }
}

void handleLEDStatus() {
  // Return to green after showing status
  if (millis() - ledChangeTime > 500) {  // Show status for 500ms
    if (dataReceived || leds[0].r > 0) {  // If blue or red was shown
      leds[0] = CRGB::Green;
      FastLED.show();
      dataReceived = false;
    }
  }
  
  // Dim green if no data for a while
  if (millis() - lastDataTime > 10000) {  // 10 seconds
    leds[0] = CRGB(0, 20, 0);  // Dim green
    FastLED.show();
  }
}
