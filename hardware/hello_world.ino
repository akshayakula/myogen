/*
 * Arduino Hello World
 * Simple test program to verify Arduino is working
 */

// Built-in LED pin (most Arduino boards use pin 13)
const int LED_PIN = 13;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Set LED pin as output
  pinMode(LED_PIN, OUTPUT);
  
  // Turn on LED initially
  digitalWrite(LED_PIN, HIGH);
  
  // Send hello message
  Serial.println("Hello World! Arduino is working!");
  Serial.println("Built-in LED will blink every second");
  Serial.println("Send any character to see a response");
}

void loop() {
  // Blink the LED
  digitalWrite(LED_PIN, HIGH);
  delay(1000);
  digitalWrite(LED_PIN, LOW);
  delay(1000);
  
  // Check for serial input
  if (Serial.available() > 0) {
    char input = Serial.read();
    Serial.print("You sent: ");
    Serial.println(input);
    Serial.println("Arduino is responding correctly!");
  }
}
