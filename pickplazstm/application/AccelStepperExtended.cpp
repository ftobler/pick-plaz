/*
 * AccelStepperExtended.cpp
 *
 *  Created on: May 30, 2021
 *      Author: ftobler
 */


#include "AccelStepperextended.h"


AccelStepperExtended::AccelStepperExtended(int pin1, int pin2)
  : AccelStepper(AccelStepper::DRIVER, pin1, pin2) {
	speed_multiplier = 1.000f;
	steps_per_mm = 100;
	max_speed_cap_mm = 10000;
}


void AccelStepperExtended::moveTo_mm(float position_mm) {
	moveTo(position_mm * steps_per_mm);
	move_start_pos = _currentPos;
	move_length = _targetPos - _currentPos;
}


void AccelStepperExtended::setCurrentPosition_mm(float position_mm) {
	setCurrentPosition(position_mm * steps_per_mm);
}



void AccelStepperExtended::setMaxSpeed_mm(float speed_mm) {
	float newSpeed_mm = speed_mm * speed_multiplier;
	if (newSpeed_mm > max_speed_cap_mm) {
		newSpeed_mm = max_speed_cap_mm;
	}
	setMaxSpeed(newSpeed_mm * steps_per_mm);
}


void AccelStepperExtended::setMaxSpeed_cap_mm(float speed_mm) {
	max_speed_cap_mm = speed_mm;
	setMaxSpeed_mm(speed_mm);
}



void AccelStepperExtended::setMaxSpeed_multiplier_mm(float _speed_multiplier) {
	speed_multiplier = _speed_multiplier;
}



void AccelStepperExtended::setAcceleration_mm(float accel_mm) {
	setAcceleration(accel_mm * steps_per_mm);
}


void AccelStepperExtended::setStepsPer_mm(float steps_per) {
	steps_per_mm = steps_per;
}


float AccelStepperExtended::getMaxSpeed_mm() {
	return maxSpeed() / steps_per_mm;
}

float AccelStepperExtended::getMovementProgress() {
    long travelled = _currentPos - move_start_pos;
    return (float)travelled / move_length;
}
