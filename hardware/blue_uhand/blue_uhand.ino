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

// RGB LED color object
static CRGB rgbs[1];

// Servo angle related variables (servo index corresponds to position: 0-thumb 1-index 2-middle 3-ring 4-pinky 5-wrist)
static uint8_t extended_func_angles[6] = { 90, 90, 90, 90, 90, 90 }; /* Angle values used by secondary development routines */
static uint8_t servo_angles[6] = { 90, 90, 90, 90, 90, 90 };  /* Actual servo control angle values */

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
// Thumb range test function
void thumb_range_test(void);

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
  
  // Run thumb range test on startup
  Serial.println("Running thumb range test...");
  thumb_range_test();
  Serial.println("Thumb test complete - ready for normal operation");
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

// Thumb range test function - cycles thumb through full range of motion
void thumb_range_test(void) {
  Serial.println("  Testing thumb servo (index 0)...");
  
  // Test positions: fully open (0°) -> fully closed (180°) -> back to center (90°)
  int test_positions[] = {0, 45, 90, 135, 180, 135, 90, 45, 0, 90};
  int num_positions = sizeof(test_positions) / sizeof(test_positions[0]);
  
  for (int i = 0; i < num_positions; i++) {
    int target_angle = test_positions[i];
    
    // Apply thumb inversion logic (same as in servo_control function)
    int actual_angle = 180 - target_angle;
    
    // Move thumb servo directly
    servos[0].write(actual_angle);
    
    Serial.print("    Position ");
    Serial.print(i + 1);
    Serial.print("/");
    Serial.print(num_positions);
    Serial.print(": Target=");
    Serial.print(target_angle);
    Serial.print("° -> Actual=");
    Serial.print(actual_angle);
    Serial.println("°");
    
    // Wait for movement to complete
    delay(800);
  }
  
  // Return to neutral position (90°)
  servos[0].write(90);
  Serial.println("  Thumb returned to neutral position (90°)");
}

