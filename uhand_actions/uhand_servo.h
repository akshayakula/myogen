#ifndef _HW_ACTION_CTL_
#define _HW_ACTION_CTL_
#include "actions.h"



class HW_ACTION_CTL{
  public:
    uint8_t extended_func_angles[6] = { 0,0,0,0,0, 90 }; /* 二次开发例程使用的角度数值 */
    //控制执行动作组
    void action_set(int num);
    int action_state_get(void);
    void action_task(void);
    
  private:
    //动作组控制变量
    int action_num = 0;
};

#endif //_HW_ACTION_CTL_
