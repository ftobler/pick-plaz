/*
 * AccelStepperExtended.h
 *
 *  Created on: May 30, 2021
 *      Author: ftobler
 */

#ifndef ACCELSTEPPEREXTENDED_H_
#define ACCELSTEPPEREXTENDED_H_

#include "AccelStepper.h"

class AccelStepperExtended : public AccelStepper {
private:
	float speed_multiplier;
	float steps_per_mm;
	float max_speed_cap_mm;
public:
	AccelStepperExtended(int pin1, int pin2);
	void moveTo_mm(float position_mm);
	void setCurrentPosition_mm(float position_mm);
	void setMaxSpeed_mm(float speed_mm);
	void setMaxSpeed_cap_mm(float speed_mm);
	void setMaxSpeed_multiplier_mm(float _speed_multiplier);
	void setAcceleration_mm(float accel_mm);
	void setStepsPer_mm(float steps_per);
	float getMaxSpeed_mm();
};


#endif /* ACCELSTEPPEREXTENDED_H_ */
