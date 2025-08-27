/*
 * BLE Byte Debug - Show exactly what bytes are received via BLE
 * 
 * This will help us see what's happening to our data during BLE transmission
 */

void setup() {
  Serial.begin(115200);
  Serial.println("=== BLE Byte Debug ===");
  Serial.println("Waiting for BLE data...");
  Serial.println("Expected: 0xAA 0x77 0x01 0x06 0x2D 0x2D 0x2D 0x2D 0x2D 0x2D 0xEA");
  Serial.println();
}

void loop() {
  if (Serial.available()) {
    int bytesAvailable = Serial.available();
    Serial.print("📦 Received ");
    Serial.print(bytesAvailable);
    Serial.println(" bytes:");
    
    // Read and display each byte
    int byteCount = 0;
    while (Serial.available() && byteCount < 20) {  // Limit to prevent overflow
      uint8_t receivedByte = Serial.read();
      
      Serial.print("  Byte ");
      Serial.print(byteCount);
      Serial.print(": 0x");
      if (receivedByte < 16) Serial.print("0");
      Serial.print(receivedByte, HEX);
      Serial.print(" (");
      Serial.print(receivedByte, DEC);
      Serial.print(")");
      
      if (receivedByte >= 32 && receivedByte <= 126) {
        Serial.print(" '");
        Serial.print((char)receivedByte);
        Serial.print("'");
      }
      
      Serial.println();
      byteCount++;
      
      delay(1);  // Small delay to catch rapid bytes
    }
    
    Serial.println("--- End of packet ---");
    Serial.println();
  }
  
  // Heartbeat
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 10000) {
    Serial.println("❤️ Still listening for BLE data...");
    lastHeartbeat = millis();
  }
}
