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
#include "uart_handler.h"


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


void setup() {
	int speed = 1000;
	int accel = 2000;
	stepperX.setAcceleration(accel);
	stepperX.setMaxSpeed(speed);
	stepperY0.setAcceleration(accel);
	stepperY0.setMaxSpeed(speed);
	stepperY1.setAcceleration(accel);
	stepperY1.setMaxSpeed(speed);
	stepperZ.setAcceleration(accel);
	stepperZ.setMaxSpeed(speed);
	stepperE.setAcceleration(accel);
	stepperE.setMaxSpeed(speed);
	stepperA.setAcceleration(accel);
	stepperA.setMaxSpeed(speed);
	stepperB.setAcceleration(accel);
	stepperB.setMaxSpeed(speed);
	stepperC.setAcceleration(accel);
	stepperC.setMaxSpeed(speed);
	uart_init();
}

void timer_isr() {
	stepperX.run();
	stepperY0.run();
	stepperY1.run();
	stepperZ.run();
	stepperE.run();
	stepperA.run();
	stepperB.run();
	stepperC.run();
}

void systick_isr() {

}

void loop() {

	/*digitalWrite(PIN_OUTPUT_PUMP, millis() % 700 > 100);
	digitalWrite(PIN_OUTPUT_VALVE, millis() % 700 > 200);
	digitalWrite(PIN_OUTPUT_BOTUP, millis() % 700 > 300);
	digitalWrite(PIN_OUTPUT_TOPDN, millis() % 700 > 400);
	digitalWrite(PIN_OUTPUT_AUX1, millis() % 700 > 500);
	digitalWrite(PIN_OUTPUT_AUX2, millis() % 700 > 600);*/

	uart_loop();

}

