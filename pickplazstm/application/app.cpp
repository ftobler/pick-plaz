/*
 * app.cpp
 *
 *  Created on: May 29, 2021
 *      Author: ftobler
 */


#include "app.h"
#include "stdint.h"
#include "arduino_like_hal.h"
#include "AccelStepper.h"

//#define PIN_OUTPUT_PUMP (('C' - 'A') * 16 + 6)

#define PIN_OUTPUT_PUMP  portpin('C', 6)
#define PIN_OUTPUT_VALVE portpin('D', 15)
#define PIN_OUTPUT_BOTUP portpin('D', 14)
#define PIN_OUTPUT_TOPDN portpin('D', 13)
#define PIN_OUTPUT_AUX1  portpin('D', 12)
#define PIN_OUTPUT_AUX2  portpin('D', 11)


#define PIN_MOTX_STEP  portpin('E', 5)
#define PIN_MOTX_DIR   portpin('E', 4)
#define PIN_MOTX_EN    portpin('E', 6)

#define PIN_MOTY0_STEP portpin('E', 2)
#define PIN_MOTY0_DIR  portpin('E', 1)
#define PIN_MOTY0_EN   portpin('E', 3)

#define PIN_MOTY1_STEP portpin('B', 9)
#define PIN_MOTY1_DIR  portpin('B', 8)
#define PIN_MOTY1_EN   portpin('E', 0)

#define PIN_MOTZ_STEP  portpin('B', 4)
#define PIN_MOTZ_DIR   portpin('D', 7)
#define PIN_MOTZ_EN    portpin('B', 5)

#define PIN_MOTE_STEP  portpin('D', 5)
#define PIN_MOTE_DIR   portpin('D', 4)
#define PIN_MOTE_EN    portpin('D', 6)

#define PIN_MOTA_STEP  portpin('D', 2)
#define PIN_MOTA_DIR   portpin('D', 1)
#define PIN_MOTA_EN    portpin('D', 6)

#define PIN_MOTB_STEP  portpin('C', 8)
#define PIN_MOTB_DIR   portpin('C', 7)
#define PIN_MOTB_EN    portpin('C', 9)

#define PIN_MOTC_STEP  portpin('C', 12)
#define PIN_MOTC_DIR   portpin('C', 11)
#define PIN_MOTC_EN    portpin('D', 0)


AccelStepper stepperX( AccelStepper::DRIVER, PIN_MOTX_STEP,  PIN_MOTX_DIR);
AccelStepper stepperY0(AccelStepper::DRIVER, PIN_MOTY0_STEP, PIN_MOTY0_DIR);
AccelStepper stepperY1(AccelStepper::DRIVER, PIN_MOTY1_STEP, PIN_MOTY1_DIR);
AccelStepper stepperZ( AccelStepper::DRIVER, PIN_MOTZ_STEP,  PIN_MOTZ_DIR);
AccelStepper stepperE( AccelStepper::DRIVER, PIN_MOTE_STEP,  PIN_MOTE_DIR);
AccelStepper stepperA( AccelStepper::DRIVER, PIN_MOTA_STEP,  PIN_MOTA_DIR);
AccelStepper stepperB( AccelStepper::DRIVER, PIN_MOTB_STEP,  PIN_MOTB_DIR);
AccelStepper stepperC( AccelStepper::DRIVER, PIN_MOTC_STEP,  PIN_MOTC_DIR);


#define millis() millis_count

void setup() {
	int speed = 2000;
	int accel = 10000;
	stepperX.setAcceleration(10000);
	stepperX.setMaxSpeed(2000);
	stepperY0.setAcceleration(10000);
	stepperY0.setMaxSpeed(2000);
	stepperY1.setAcceleration(10000);
	stepperY1.setMaxSpeed(2000);
	stepperZ.setAcceleration(10000);
	stepperZ.setMaxSpeed(2000);
	stepperE.setAcceleration(10000);
	stepperE.setMaxSpeed(2000);
	stepperA.setAcceleration(10000);
	stepperA.setMaxSpeed(2000);
	stepperB.setAcceleration(10000);
	stepperB.setMaxSpeed(2000);
	stepperC.setAcceleration(10000);
	stepperC.setMaxSpeed(2000);
}


static volatile int32_t millis_count = 1;
static volatile int32_t micros_count = 1;
static volatile float frequency = 0;


void timer_isr() {
	digitalWrite(PIN_OUTPUT_TOPDN, 1);

	static int32_t counter = 0;
	counter++;
	frequency = (float)counter / millis_count * 1000;
	micros_count = micros();
	digitalWrite(PIN_OUTPUT_PUMP, counter & 0x01);

	stepperX.run();
	stepperY0.run();
	stepperY1.run();
	stepperZ.run();
	stepperE.run();
	stepperA.run();
	stepperB.run();
	stepperC.run();
	digitalWrite(PIN_OUTPUT_TOPDN, 0);
}

void systick_isr() {
	//digitalWrite(PIN_OUTPUT_TOPDN, 0);
	millis_count++;
	digitalWrite(PIN_OUTPUT_VALVE, millis_count & 0x01);

	int i = millis_count;
	if (millis_count % 16 == 0)		    stepperX.moveTo(micros() % i);
	if (millis_count % 16 == 1)			stepperY0.moveTo(micros() % i);
	if (millis_count % 16 == 2)			stepperY1.moveTo(micros() % i);
	if (millis_count % 16 == 3)			stepperZ.moveTo(micros() % i);
	if (millis_count % 16 == 4)			stepperE.moveTo(micros() % i);
	if (millis_count % 16 == 5)			stepperA.moveTo(micros() % i);
	if (millis_count % 16 == 6)			stepperB.moveTo(micros() % i);
	if (millis_count % 16 == 7)			stepperC.moveTo(micros() % i);
}

void loop() {
    //digitalWrite(PIN_OUTPUT_TOPDN, 0);
	static int loopCount = 0;






	loopCount++;
	digitalWrite(PIN_OUTPUT_BOTUP, loopCount & 0x01);
	/*digitalWrite(PIN_OUTPUT_PUMP, millis() % 700 > 100);
	digitalWrite(PIN_OUTPUT_VALVE, millis() % 700 > 200);
	digitalWrite(PIN_OUTPUT_BOTUP, millis() % 700 > 300);
	digitalWrite(PIN_OUTPUT_TOPDN, millis() % 700 > 400);
	digitalWrite(PIN_OUTPUT_AUX1, millis() % 700 > 500);
	digitalWrite(PIN_OUTPUT_AUX2, millis() % 700 > 600);*/
}

