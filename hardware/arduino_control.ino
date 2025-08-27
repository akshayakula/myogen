/*
 * Arduino Uno Control Sketch
 * This sketch provides basic control functionality for Arduino Uno
 * Includes LED control, sensor reading, and serial communication
 */

// Pin definitions
const int LED_PIN = 13;           // Built-in LED
const int EXTERNAL_LED_PIN = 12;  // External LED on pin 12
const int BUTTON_PIN = 2;         // Button on pin 2
const int POTENTIOMETER_PIN = A0; // Potentiometer on analog pin A0
const int TEMP_SENSOR_PIN = A1;   // Temperature sensor on analog pin A1

// Variables
int ledState = LOW;               // Current state of LED
int buttonState = HIGH;           // Current state of button
int lastButtonState = HIGH;       // Previous state of button
unsigned long lastDebounceTime = 0; // Last time button was pressed
unsigned long debounceDelay = 50;   // Debounce delay in milliseconds

// Timing variables
unsigned long previousMillis = 0;
const long interval = 1000;       // Interval for LED blinking (1 second)

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  Serial.println("Arduino Uno Control System Initialized");
  
  // Set pin modes
  pinMode(LED_PIN, OUTPUT);
  pinMode(EXTERNAL_LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Initialize LEDs
  digitalWrite(LED_PIN, LOW);
  digitalWrite(EXTERNAL_LED_PIN, LOW);
  
  Serial.println("Pin setup complete");
  Serial.println("Commands:");
  Serial.println("  'led_on' - Turn on built-in LED");
  Serial.println("  'led_off' - Turn off built-in LED");
  Serial.println("  'led_toggle' - Toggle built-in LED");
  Serial.println("  'ext_led_on' - Turn on external LED");
  Serial.println("  'ext_led_off' - Turn off external LED");
  Serial.println("  'read_pot' - Read potentiometer value");
  Serial.println("  'read_temp' - Read temperature sensor");
  Serial.println("  'status' - Show all sensor values");
}

void loop() {
  // Handle serial commands
  handleSerialCommands();
  
  // Handle button input with debouncing
  handleButtonInput();
  
  // Blink external LED every second
  blinkExternalLED();
  
  // Small delay to prevent overwhelming the system
  delay(10);
}

void handleSerialCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    command.toLowerCase();
    
    if (command == "led_on") {
      digitalWrite(LED_PIN, HIGH);
      ledState = HIGH;
      Serial.println("Built-in LED turned ON");
    }
    else if (command == "led_off") {
      digitalWrite(LED_PIN, LOW);
      ledState = LOW;
      Serial.println("Built-in LED turned OFF");
    }
    else if (command == "led_toggle") {
      ledState = !ledState;
      digitalWrite(LED_PIN, ledState);
      Serial.print("Built-in LED toggled to: ");
      Serial.println(ledState ? "ON" : "OFF");
    }
    else if (command == "ext_led_on") {
      digitalWrite(EXTERNAL_LED_PIN, HIGH);
      Serial.println("External LED turned ON");
    }
    else if (command == "ext_led_off") {
      digitalWrite(EXTERNAL_LED_PIN, LOW);
      Serial.println("External LED turned OFF");
    }
    else if (command == "read_pot") {
      int potValue = analogRead(POTENTIOMETER_PIN);
      float voltage = (potValue * 5.0) / 1024.0;
      Serial.print("Potentiometer: ");
      Serial.print(potValue);
      Serial.print(" (");
      Serial.print(voltage, 2);
      Serial.println("V)");
    }
    else if (command == "read_temp") {
      int tempValue = analogRead(TEMP_SENSOR_PIN);
      float voltage = (tempValue * 5.0) / 1024.0;
      float temperature = (voltage - 0.5) * 100; // LM35 sensor conversion
      Serial.print("Temperature: ");
      Serial.print(temperature, 1);
      Serial.println("°C");
    }
    else if (command == "status") {
      printStatus();
    }
    else if (command == "help") {
      printHelp();
    }
    else {
      Serial.print("Unknown command: ");
      Serial.println(command);
      Serial.println("Type 'help' for available commands");
    }
  }
}

void handleButtonInput() {
  // Read the button state
  int reading = digitalRead(BUTTON_PIN);
  
  // If the button state changed, reset the debouncing timer
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  // If enough time has passed since the last change, consider the button state stable
  if ((millis() - lastDebounceTime) > debounceDelay) {
    // If the button state has changed
    if (reading != buttonState) {
      buttonState = reading;
      
      // If button is pressed (LOW because of INPUT_PULLUP)
      if (buttonState == LOW) {
        // Toggle the built-in LED
        ledState = !ledState;
        digitalWrite(LED_PIN, ledState);
        Serial.print("Button pressed! LED toggled to: ");
        Serial.println(ledState ? "ON" : "OFF");
      }
    }
  }
  
  // Save the reading for next iteration
  lastButtonState = reading;
}

void blinkExternalLED() {
  unsigned long currentMillis = millis();
  
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    // Toggle external LED
    static bool extLedState = false;
    extLedState = !extLedState;
    digitalWrite(EXTERNAL_LED_PIN, extLedState);
  }
}

void printStatus() {
  Serial.println("=== ARDUINO STATUS ===");
  
  // LED states
  Serial.print("Built-in LED: ");
  Serial.println(ledState ? "ON" : "OFF");
  
  Serial.print("External LED: ");
  Serial.println(digitalRead(EXTERNAL_LED_PIN) ? "ON" : "OFF");
  
  // Button state
  Serial.print("Button: ");
  Serial.println(digitalRead(BUTTON_PIN) ? "RELEASED" : "PRESSED");
  
  // Sensor readings
  int potValue = analogRead(POTENTIOMETER_PIN);
  float potVoltage = (potValue * 5.0) / 1024.0;
  Serial.print("Potentiometer: ");
  Serial.print(potValue);
  Serial.print(" (");
  Serial.print(potVoltage, 2);
  Serial.println("V)");
  
  int tempValue = analogRead(TEMP_SENSOR_PIN);
  float tempVoltage = (tempValue * 5.0) / 1024.0;
  float temperature = (tempVoltage - 0.5) * 100;
  Serial.print("Temperature: ");
  Serial.print(temperature, 1);
  Serial.println("°C");
  
  Serial.println("=====================");
}

void printHelp() {
  Serial.println("=== ARDUINO CONTROL COMMANDS ===");
  Serial.println("led_on      - Turn on built-in LED");
  Serial.println("led_off     - Turn off built-in LED");
  Serial.println("led_toggle  - Toggle built-in LED");
  Serial.println("ext_led_on  - Turn on external LED");
  Serial.println("ext_led_off - Turn off external LED");
  Serial.println("read_pot    - Read potentiometer value");
  Serial.println("read_temp   - Read temperature sensor");
  Serial.println("status      - Show all sensor values");
  Serial.println("help        - Show this help message");
  Serial.println("================================");
}

