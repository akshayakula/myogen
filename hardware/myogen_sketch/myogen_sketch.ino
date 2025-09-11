#include <FastLED.h> //RGB control library (needs to be imported)
#include <Servo.h> //Servo library
#include "tone.h" //Tone library
#include "bluetooth.h" //Bluetooth receiving library

//Tone definitions
const static uint16_t DOC5[] = { TONE_C5 };
const static uint16_t DOC6[] = { TONE_C6 };
const static uint16_t DO_RE_MI[3] = { TONE_C5, TONE_D5, TONE_E5 };
const static uint16_t MI_RE_DO[3] = { TONE_E5, TONE_D5, TONE_C5 };
const static uint16_t MI_RE_MI_RE[4] = { TONE_C7, TONE_C6, TONE_C7, TONE_C6 };

//Button pins
const static uint8_t keyPins[2] = { 8, 9 };
// Servo pins
const static uint8_t servoPins[6] = { 7, 6, 5, 4, 3, 2 };
// Buzzer pin
const static uint8_t buzzerPin = 11;
// RGB LED pin
const static uint8_t rgbPin = 13;


// BLE Protocol constants
#define FRAME_HEADER 0x55

// RGB LED color object
static CRGB rgbs[1];

// Servo angle related variables (servo index corresponds to position: 0-thumb 1-index 2-middle 3-ring 4-pinky 5-wrist)
// Default to fully opened hand: thumb=180°(extended after inversion), fingers=180°(extended), wrist=90°(neutral)
static uint8_t extended_func_angles[6] = { 180, 180, 180, 180, 180, 90 }; /* Angle values used by secondary development routines */
static uint8_t servo_angles[6] = { 180, 180, 180, 180, 180, 90 };  /* Actual servo control angle values */

// Buzzer related variables
static uint16_t tune_num = 0;
static uint32_t tune_beat = 10;
static uint16_t *tune;



// Create servo control objects
Servo servos[6];

// Create bluetooth receiving object
blue_controller blue_ctl;

// Create bluetooth receiving storage variables
struct uHand_Servo uhand_servos;

// Servo control task
static void servo_control(void);
// Buzzer sound function
void play_tune(uint16_t *p, uint32_t beat, uint16_t len);
// Buzzer task
void tune_task(void);
// Bluetooth control task
void blue_task(void);
// Servo range test functions
void thumb_range_test(void);
void all_servos_range_test(void);
void synchronized_servo_test(void);
void individual_servo_test(int servo_index, const char* servo_name, int min_angle, int max_angle);

void setup() {
  // Initialize serial port and set baud rate
  Serial.begin(9600);
  // Set serial port data read timeout
  Serial.setTimeout(500);
  // Initialize button pins
  pinMode(keyPins[0], INPUT_PULLUP);
  pinMode(keyPins[1], INPUT_PULLUP);
  // Initialize buzzer pin
  pinMode(buzzerPin, OUTPUT);
  // Bind servo IO pins
  for (int i = 0; i < 6; ++i) {
    servos[i].attach(servoPins[i]);
  }
  // Initialize RGB control object
  FastLED.addLeds<WS2812, rgbPin, RGB>(rgbs, 1);
  // Initialize color object
  rgbs[0] = CRGB(0, 255, 0);
  // Light up according to color
  FastLED.show();
  // Buzzer sound at 1000Hz frequency
  tone(buzzerPin, 1000);
  // Delay
  delay(100);
  // Stop buzzer
  noTone(buzzerPin); //Configure TOUCH as input (input state is generally to read the state of this pin, i.e., read sensor feedback value)
  
  // Print
  Serial.println("start");
  
  // Run synchronized servo range test on startup
  Serial.println("Starting servo test...");
  synchronized_servo_test();
  Serial.println("Servo test complete");
}

void loop() {
  // Bluetooth receive and parse
  blue_ctl.receiveHandle();
  // Bluetooth control task
  blue_task();
  // Buzzer sound task
  tune_task();
  // Servo control
  servo_control();
}

// Bluetooth control task
void blue_task(void)
{
  // Get bluetooth information
  bool rt = blue_ctl.get_servos(&uhand_servos);
  // If successful
  if(rt)
  {
    // Assign received servo positions to corresponding uHand servos
    for(int i = 0; i < uhand_servos.num ; i++)
    {
      // Assign values according to ID number
      // Note: ID numbers start from 1, while servo angle array index starts from 0, assignment requires (ID-1)
      switch(uhand_servos.servos[i].ID)
      {
        case 1: //Thumb, rotation angle is opposite
          extended_func_angles[uhand_servos.servos[i].ID - 1] = map(uhand_servos.servos[i].Position , 1100 , 1950 , 180 , 0);
          break;

        case 2: //Index finger ~ Pinky finger
        case 3:
        case 4:
        case 5:
          // Map corresponding threshold range to [0,180] range, assign to servo
          extended_func_angles[uhand_servos.servos[i].ID - 1] = map(uhand_servos.servos[i].Position , 1100 , 1950 , 0, 180);
          break;

        case 6: //Wrist rotation
          // Map corresponding threshold range to [0,180] range, assign to servo
          extended_func_angles[uhand_servos.servos[i].ID - 1] = map(uhand_servos.servos[i].Position , 600 , 2400 , 0, 180);
          break;
      }
    }
  }
}


// Servo control task
void servo_control(void) {
  static uint32_t last_tick = 0;
  // 25 millisecond interval
  if (millis() - last_tick < 25) {
    return;
  }
  last_tick = millis();
  // Assign values to 6 servos respectively
  for (int i = 0; i < 6; ++i) {
    servo_angles[i] = servo_angles[i] * 0.85 + extended_func_angles[i] * 0.15;
    servos[i].write(i == 0 || i == 5 ? 180 - servo_angles[i] : servo_angles[i]);
  }
}

// Buzzer task
void tune_task(void) {
  static uint32_t l_tune_beat = 0;
  static uint32_t last_tick = 0;
  // If not yet reached timer time and sound time is same as last time
  if (millis() - last_tick < l_tune_beat && tune_beat == l_tune_beat) {
    return;
  }
  l_tune_beat = tune_beat;
  last_tick = millis();
  // If there are still tones
  if (tune_num > 0) {
    tune_num -= 1;
    tone(buzzerPin, *tune++);
  } else { //If none, pause
    noTone(buzzerPin);
    tune_beat = 10;
    l_tune_beat = 10;
  }
}

// Buzzer sound function Parameter 1: tone group, Parameter 2: tone sound time, Parameter 3: number of tone group elements
void play_tune(uint16_t *p, uint32_t beat, uint16_t len) {
  tune = p;
  tune_beat = beat;
  tune_num = len;
}

// Comprehensive servo range test - tests all servos through their full range
void all_servos_range_test(void) {
  Serial.println("🤖 COMPREHENSIVE SERVO RANGE TEST");
  Serial.println("==================================");
  Serial.println("Testing all 6 servos through their full range of motion...");
  Serial.println();
  
  // Servo configurations: {index, name, min_angle, max_angle}
  struct ServoConfig {
    int index;
    const char* name;
    int min_angle;
    int max_angle;
  };
  
  ServoConfig servo_configs[6] = {
    {0, "Thumb", 0, 180},      // Servo 0: Thumb (inverted)
    {1, "Index", 0, 180},      // Servo 1: Index finger
    {2, "Middle", 0, 180},     // Servo 2: Middle finger
    {3, "Ring", 25, 180},      // Servo 3: Ring finger (limited min)
    {4, "Pinky", 0, 180},      // Servo 4: Pinky finger
    {5, "Wrist", 0, 180}       // Servo 5: Wrist rotation (inverted)
  };
  
  // Test each servo individually
  for (int i = 0; i < 6; i++) {
    Serial.print("🔧 Testing Servo ");
    Serial.print(i);
    Serial.print(" (");
    Serial.print(servo_configs[i].name);
    Serial.println("):");
    
    individual_servo_test(servo_configs[i].index, 
                         servo_configs[i].name,
                         servo_configs[i].min_angle, 
                         servo_configs[i].max_angle);
    
    Serial.println();
    delay(1000); // Pause between servos
  }
  
  // Final synchronized movement - all to neutral
  Serial.println("🎯 FINAL TEST: Moving all servos to neutral position...");
  for (int i = 0; i < 6; i++) {
    // Apply inversion logic for thumb (0) and wrist (5)
    int target_angle = 90;
    int actual_angle = (i == 0 || i == 5) ? 180 - target_angle : target_angle;
    servos[i].write(actual_angle);
    
    Serial.print("  Servo ");
    Serial.print(i);
    Serial.print(" (");
    Serial.print(servo_configs[i].name);
    Serial.print("): ");
    Serial.print(target_angle);
    Serial.print("° -> ");
    Serial.print(actual_angle);
    Serial.println("°");
  }
  
  Serial.println("✅ All servos at neutral position (90°)");
  Serial.println("==================================");
}

// Individual servo test function
void individual_servo_test(int servo_index, const char* servo_name, int min_angle, int max_angle) {
  // Create test sequence: min -> 25% -> 50% -> 75% -> max -> 75% -> 50% -> 25% -> min -> neutral
  int test_positions[10];
  int range = max_angle - min_angle;
  
  test_positions[0] = min_angle;                    // Minimum
  test_positions[1] = min_angle + (range * 25 / 100); // 25%
  test_positions[2] = min_angle + (range * 50 / 100); // 50%
  test_positions[3] = min_angle + (range * 75 / 100); // 75%
  test_positions[4] = max_angle;                    // Maximum
  test_positions[5] = min_angle + (range * 75 / 100); // 75% (return)
  test_positions[6] = min_angle + (range * 50 / 100); // 50% (return)
  test_positions[7] = min_angle + (range * 25 / 100); // 25% (return)
  test_positions[8] = min_angle;                    // Minimum (return)
  test_positions[9] = 90;                           // Neutral
  
  int num_positions = 10;
  
  for (int i = 0; i < num_positions; i++) {
    int target_angle = test_positions[i];
    
    // Apply inversion logic for thumb (0) and wrist (5)
    int actual_angle;
    if (servo_index == 0 || servo_index == 5) {
      actual_angle = 180 - target_angle; // Inverted servos
    } else {
      actual_angle = target_angle; // Normal servos
    }
    
    // Move servo
    servos[servo_index].write(actual_angle);
    
    // Print status
    Serial.print("    Step ");
    Serial.print(i + 1);
    Serial.print("/");
    Serial.print(num_positions);
    Serial.print(": Target=");
    Serial.print(target_angle);
    Serial.print("° -> Actual=");
    Serial.print(actual_angle);
    Serial.print("°");
    
    // Add description for key positions
    if (i == 0) Serial.print(" (MIN)");
    else if (i == 4) Serial.print(" (MAX)");
    else if (i == 9) Serial.print(" (NEUTRAL)");
    
    Serial.println();
    
    // Wait for movement to complete
    delay(700);
  }
  
  Serial.print("  ✅ ");
  Serial.print(servo_name);
  Serial.println(" test complete");
}

// Simple finger range test - all 5 fingers move through full range once
void synchronized_servo_test(void) {
  Serial.println("FINGER RANGE TEST");
  Serial.println("Open->Close->Neutral");
  
  // Finger configurations (excluding wrist)
  struct FingerConfig {
    int index;
    const char* name;
    int min_angle;
    int max_angle;
  };
  
  FingerConfig finger_configs[5] = {
    {0, "Thumb", 0, 180},      // Servo 0: Thumb (inverted)
    {1, "Index", 0, 180},      // Servo 1: Index finger
    {2, "Middle", 0, 180},     // Servo 2: Middle finger
    {3, "Ring", 25, 180},      // Servo 3: Ring finger (limited min)
    {4, "Pinky", 0, 180}       // Servo 4: Pinky finger
  };
  
  // Keep wrist at neutral (90°) throughout test
  servos[5].write(90);
  
  // Test sequence: 3 simple positions
  const char* step_names[3] = {
    "OPEN",
    "CLOSED", 
    "NEUTRAL"
  };
  
  for (int step = 0; step < 3; step++) {
    Serial.print("Step ");
    Serial.print(step + 1);
    Serial.print(": ");
    Serial.println(step_names[step]);
    
    // Move all 5 fingers to target position
    for (int i = 0; i < 5; i++) {
      int target_angle;
      
      switch(step) {
        case 0: target_angle = finger_configs[i].min_angle; break;  // Open (min angles)
        case 1: target_angle = finger_configs[i].max_angle; break;  // Closed (max angles)
        case 2: target_angle = 90; break;                           // Neutral
      }
      
      // Apply inversion logic for thumb (0) only
      int actual_angle;
      if (i == 0) {
        actual_angle = 180 - target_angle; // Inverted thumb
      } else {
        actual_angle = target_angle; // Normal fingers
      }
      
      // Move finger
      servos[i].write(actual_angle);
      
      // Print finger status
      Serial.print("  ");
      Serial.print(finger_configs[i].name);
      Serial.print(": ");
      Serial.print(target_angle);
      Serial.print("° -> ");
      Serial.print(actual_angle);
      Serial.print("°");
      if (i < 4) Serial.print(", ");
    }
    Serial.println();
    Serial.println();
    
    // Wait for all fingers to reach position
    delay(2000); // 2 second delay to see the movement clearly
  }
  
  // Final status
  Serial.println("Test complete");
}

// Legacy thumb test function (kept for compatibility)
void thumb_range_test(void) {
  Serial.println("🔧 Legacy thumb test (use synchronized_servo_test() for comprehensive testing)");
  individual_servo_test(0, "Thumb", 0, 180);
}



