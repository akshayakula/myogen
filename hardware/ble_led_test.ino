/*
 * Simple BLE LED Test
 * 
 * This sketch tests basic communication from Hiwonder BLE module to Arduino
 * Receives single byte commands via serial and controls built-in LED
 * 
 * Commands:
 * '1' or 0x31 - Turn LED ON
 * '0' or 0x30 - Turn LED OFF
 * 'B' or 0x42 - Fast blink (5 times)
 * Any other byte - Slow blink once
 */

#define LED_PIN LED_BUILTIN  // Pin 13 on most Arduinos

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  
  // Start with LED off
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("=== BLE LED Test Ready ===");
  Serial.println("Commands:");
  Serial.println("  '1' - LED ON");
  Serial.println("  '0' - LED OFF"); 
  Serial.println("  'B' - Fast blink");
  Serial.println("  Any other - Slow blink");
  Serial.println("Waiting for BLE commands...");
  Serial.println();
}

void loop() {
  // Check for incoming data
  if (Serial.available()) {
    byte command = Serial.read();
    
    // Echo the received command
    Serial.print("Received: ");
    Serial.print("0x");
    Serial.print(command, HEX);
    Serial.print(" ('");
    if (command >= 32 && command <= 126) {  // Printable ASCII
      Serial.print((char)command);
    } else {
      Serial.print("?");
    }
    Serial.print("') - ");
    
    // Process command
    switch (command) {
      case '1':  // ASCII '1' = 0x31
        digitalWrite(LED_PIN, HIGH);
        Serial.println("LED ON");
        break;
        
      case '0':  // ASCII '0' = 0x30
        digitalWrite(LED_PIN, LOW);
        Serial.println("LED OFF");
        break;
        
      case 'B':  // ASCII 'B' = 0x42
      case 'b':  // ASCII 'b' = 0x62
        Serial.println("Fast blink");
        fastBlink();
        break;
        
      default:
        Serial.print("Unknown command - ignoring (no action taken)");
        // Don't do anything for unknown commands
        break;
    }
    
    // Clear any remaining bytes
    while (Serial.available()) {
      Serial.read();
    }
  }
  
  // Heartbeat every 5 seconds
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 5000) {
    Serial.println("Heartbeat: Arduino listening...");
    lastHeartbeat = millis();
  }
}

void fastBlink() {
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }
}

void slowBlink() {
  digitalWrite(LED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_PIN, LOW);
  delay(500);
}
