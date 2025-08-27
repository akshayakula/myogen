/*
 * BLE LED Debug Test
 * 
 * Enhanced debugging version to see exactly what bytes are received
 * and when the LED state changes
 */

#define LED_PIN LED_BUILTIN  // Pin 13 on most Arduinos

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  
  // Start with LED off
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("=== BLE LED Debug Test ===");
  Serial.println("Enhanced debugging - shows all received bytes");
  Serial.println("Commands:");
  Serial.println("  '1' (0x31) - LED ON");
  Serial.println("  '0' (0x30) - LED OFF"); 
  Serial.println("  'B' (0x42) - Fast blink");
  Serial.println("Waiting for BLE commands...");
  Serial.println();
}

void loop() {
  // Check for incoming data
  if (Serial.available()) {
    int bytesAvailable = Serial.available();
    Serial.print("DEBUG: ");
    Serial.print(bytesAvailable);
    Serial.println(" byte(s) available");
    
    // Read and process each byte individually
    while (Serial.available()) {
      byte command = Serial.read();
      
      // Show detailed info about received byte
      Serial.print("RECEIVED: 0x");
      Serial.print(command, HEX);
      Serial.print(" (");
      Serial.print(command, DEC);
      Serial.print(") ");
      
      if (command >= 32 && command <= 126) {  // Printable ASCII
        Serial.print("'");
        Serial.print((char)command);
        Serial.print("' ");
      } else {
        Serial.print("[non-printable] ");
      }
      
      // Process command and show LED state change
      switch (command) {
        case '1':  // ASCII '1' = 0x31 = 49
          digitalWrite(LED_PIN, HIGH);
          Serial.println("-> LED ON *** ONLY '1' COMMAND SHOULD CAUSE THIS ***");
          break;
          
        case '0':  // ASCII '0' = 0x30 = 48
          digitalWrite(LED_PIN, LOW);
          Serial.println("-> LED OFF *** ONLY '0' COMMAND SHOULD CAUSE THIS ***");
          break;
          
        case 'B':  // ASCII 'B' = 0x42 = 66
        case 'b':  // ASCII 'b' = 0x62 = 98
          Serial.println("-> Fast blink starting");
          fastBlink();
          Serial.println("-> Fast blink complete");
          break;
          
        default:
          Serial.println("-> IGNORED (unknown command)");
          break;
      }
      
      // Small delay to see rapid sequences
      delay(10);
    }
    
    Serial.println("--- End of packet ---");
    Serial.println();
  }
  
  // Monitor LED state changes (even if not commanded by us)
  static int lastLedState = -1;
  static unsigned long lastStateCheck = 0;
  
  if (millis() - lastStateCheck > 50) {  // Check every 50ms
    int currentState = digitalRead(LED_PIN);
    if (currentState != lastLedState) {
      Serial.print("!!! LED STATE CHANGED: ");
      Serial.print(lastLedState);
      Serial.print(" -> ");
      Serial.print(currentState);
      Serial.println(" (NOT commanded by serial!)");
      lastLedState = currentState;
    }
    lastStateCheck = millis();
  }
  
  // Heartbeat every 10 seconds (longer to reduce noise)
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 10000) {
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
