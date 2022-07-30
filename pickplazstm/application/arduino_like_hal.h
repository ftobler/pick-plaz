/*
 * arduino_like_timer.h
 *
 *  Created on: May 29, 2021
 *      Author: ftobler
 */

#ifndef ARDUINO_LIKE_HAL_H_
#define ARDUINO_LIKE_HAL_H_

#include "stdint.h"
#include "math.h"
#include "stm32f4xx_hal.h"
#include "math.h"


extern TIM_HandleTypeDef htim2;  //counts in 1us interval. until it overflows at 2^32


typedef bool boolean;


enum {
	LOW = 0,
	HIGH = 1
};

enum {
	INPUT = 0,
	INPUT_PULLUP = 1,
	OUTPUT = 2
};



#define NaN ((float)(0x400000))  //floating point NaN
#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))
#define abs(x) ((x)>0?(x):-(x))
#define constrain(amt,low,high) ((amt)<(low)?(low):((amt)>(high)?(high):(amt)))
//#define round(x)     ((x)>=0?(long)((x)+0.5):(long)((x)-0.5))
#define radians(deg) ((deg)*DEG_TO_RAD)
#define degrees(rad) ((rad)*RAD_TO_DEG)
#define sq(x) ((x)*(x))

#define millis() (uwTick)
#define micros() (htim2.Instance->CNT)

#define portpin(port, pin) ((port - 'A') * 16 + pin)


void delay(int delay);
void delayMicroseconds(int delay);
void digitalWrite(int pin, int value);
void digitalPulse(int pin);
uint8_t digitalRead(int pin);
void pinMode(int pin, int mode);


#endif /* ARDUINO_LIKE_HAL_H_ */
