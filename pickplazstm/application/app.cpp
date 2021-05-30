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

#define PIN_INPUT_XEND  portpin('D', 10)
#define PIN_INPUT_YEND1 portpin('D', 9)
#define PIN_INPUT_YEND2 portpin('D', 8)
#define PIN_INPUT_ZEND  portpin('E', 15)
#define PIN_INPUT_RES1  portpin('E', 14)
#define PIN_INPUT_RES2  portpin('E', 13)


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
float scaleX = 100;
float scaleY = 100;
float scaleZ = 100;
float scaleE = 100;
float scaleA = 8.888888888888;
float scaleB = 100;
float scaleC = 100;

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
	if (uart_command_available()) {
		Gcode_command cmd = uart_command_get();
		if (cmd.id == 'G' && (cmd.num == 0 || cmd.num == 1)) {
			//drive to position
			//there is no difference between G0 and G1
			if (cmd.valueX != NAN) {
				stepperX.moveTo(cmd.valueX * scaleX);
			}
			if (cmd.valueY != NAN) {
				stepperY0.moveTo(cmd.valueY * scaleY);
				stepperY1.moveTo(cmd.valueY * scaleY);
			}
			if (cmd.valueZ != NAN) {
				stepperZ.moveTo(cmd.valueZ * scaleZ);
			}
			if (cmd.valueA != NAN) {
				stepperA.moveTo(cmd.valueA * scaleA);
			}
			if (cmd.valueB != NAN) {
				stepperB.moveTo(cmd.valueB * scaleB);
			}
			if (cmd.valueC != NAN) {
				stepperC.moveTo(cmd.valueC * scaleC);
			}
			if (cmd.valueE != NAN) {
				stepperE.moveTo(cmd.valueE * scaleE);
			}
		} else if (cmd.id == 'G' && (cmd.num == 28)) {
			//home
		} else if (cmd.id == 'G' && (cmd.num == 4)) {
			//dwell
		} else if (cmd.id == 'G' && (cmd.num == 92)) {
			//set position
		} else if (cmd.id == 'M' && (cmd.num == 6)) {
			//tool change
		} else if (cmd.id == 'M' && (cmd.num == 10)) {
			//vacuum on
		} else if (cmd.id == 'M' && (cmd.num == 11)) {
			//vacuum off
		} else if (cmd.id == 'M' && (cmd.num == 17)) {
			//steppers ON
		} else if (cmd.id == 'M' && (cmd.num == 18)) {
			//steppers OFF
		} else if (cmd.id == 'M' && (cmd.num == 126)) {
			//open valve
		} else if (cmd.id == 'M' && (cmd.num == 127)) {
			//close valve
		}
	}

}

