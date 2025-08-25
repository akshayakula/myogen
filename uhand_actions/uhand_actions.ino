#include <Servo.h> //导入舵机库
#include "uhand_servo.h" //导入动作组控制库

/* 引脚定义 */
const static uint8_t servoPins[6] = { 7, 6, 5, 4, 3, 2 };//舵机引脚定义

//动作组控制对象
HW_ACTION_CTL action_ctl;
//舵机控制对象
Servo servos[6];

const uint8_t limt_angles[6][2] = {{0,82},{0,180},{0,180},{25,180},{0,180},{0,180}}; /* 各个关节角度的限制 */
static float servo_angles[6] = { 0,0,0,0,0, 90 };  /* 舵机实际控制的角度数值 */

static void servo_control(void); /* 舵机控制 */
void user_task(void);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  // 设置串行端口读取数据的超时时间
  Serial.setTimeout(500);
  
  // 绑定舵机IO口
  for (int i = 0; i < 6; ++i) {
    servos[i].attach(servoPins[i]);
  }

  delay(2000);
  Serial.println("start");
}

void loop() {
  // 用户任务
  user_task();
  // Action group executing tasks
  action_ctl.action_task();
  //Servo control
  servo_control();
}

void user_task(void)
{
  static uint32_t last_tick = 0;
  if (millis() - last_tick < 100) {
    return;
  }
  last_tick = millis();

  static uint32_t step = 0;
  switch(step)
  {
    case 0:
      //Action group control
      action_ctl.action_set(1);//Execute Action Group 1
      Serial.print("action run.");
      step = 1;
      break;
    case 1:
      if(action_ctl.action_state_get() == 0)
      {
        Serial.println("");
        Serial.println("The action group is running successfully!");
      }else{
        Serial.print(" .");
      }
      break;
  }
}

// 舵机控制任务（不需修改）
void servo_control(void) {
  static uint32_t last_tick = 0;
  if (millis() - last_tick < 20) {
    return;
  }
  last_tick = millis();

  for (int i = 0; i < 6; ++i) {
    if(servo_angles[i] > action_ctl.extended_func_angles[i])
    {
      servo_angles[i] = servo_angles[i] * 0.9 + action_ctl.extended_func_angles[i] * 0.1;
      if(servo_angles[i] < action_ctl.extended_func_angles[i])
        servo_angles[i] = action_ctl.extended_func_angles[i];
    }else if(servo_angles[i] < action_ctl.extended_func_angles[i])
    {
      servo_angles[i] = servo_angles[i] * 0.9 + (action_ctl.extended_func_angles[i] * 0.1 + 1);
      if(servo_angles[i] > action_ctl.extended_func_angles[i])
        servo_angles[i] = action_ctl.extended_func_angles[i];
    }

    servo_angles[i] = servo_angles[i] < limt_angles[i][0] ? limt_angles[i][0] : servo_angles[i];
    servo_angles[i] = servo_angles[i] > limt_angles[i][1] ? limt_angles[i][1] : servo_angles[i];
    servos[i].write(i == 0 || i == 5 ? 180 - servo_angles[i] : servo_angles[i]);
  }
}
