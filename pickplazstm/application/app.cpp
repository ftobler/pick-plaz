/*
 * app.cpp
 *
 *  Created on: May 29, 2021
 *      Author: ftobler
 */


#include "app.h"
#include "stdint.h"
#include "arduino_like_hal.h"
#include "AccelStepperExtended.h"
#include "uart_handler.h"
#include "io.h"
#include "cmsis_gcc.h"

static void do_cmd_drive_to_position(Gcode_command cmd);
static void do_cmd_home(Gcode_command cmd);
static void homeAxle(AccelStepperExtended* stepper, Prelling_input* endstop, int homDirection, float home_speed = 10.0, int home_timeout = 10000,
		float home_travel_mm = 1000.0, float home_travel_back_mm = 5.0);
static void homeAxleDual(AccelStepperExtended* stepper1, AccelStepperExtended* stepper2, Prelling_input* endstop1, Prelling_input* endstop2,
		int homDirection, float home_speed = 10.0, int home_timeout = 10000, float home_travel_mm = 1000.0, float home_travel_back_mm = 5.0);
static void do_cmd_dwell(Gcode_command cmd);
static void do_cmd_set_position(Gcode_command cmd);
static void do_cmd_vacuum_pump(bool on);
static void do_cmd_vacuum_valve(bool on);
static void do_cmd_io(Gcode_command cmd);
static void do_cmd_stepper_power(bool on);
static void do_cmd_set_max_acceleration(Gcode_command cmd);
static void do_cmd_set_max_speed(Gcode_command cmd);
static void do_cmd_set_max_speed_multiplier(Gcode_command cmd);
static void job_prelling_handle();

//output pin cluster (these have FET driver to either 5V or 12V)
#define PIN_OUTPUT_PUMP  portpin('C', 6)
#define PIN_OUTPUT_VALVE portpin('D', 15)
#define PIN_OUTPUT_BOTUP portpin('D', 14)
#define PIN_OUTPUT_TOPDN portpin('D', 13)
#define PIN_OUTPUT_AUX1  portpin('D', 12)
#define PIN_OUTPUT_AUX2  portpin('D', 11)

//Input pin cluster
#define PIN_INPUT_XEND  portpin('D', 10)
#define PIN_INPUT_YEND0 portpin('D', 9)
#define PIN_INPUT_YEND1 portpin('D', 8)
#define PIN_INPUT_ZEND  portpin('E', 15)
#define PIN_INPUT_RES1  portpin('E', 14)
#define PIN_INPUT_RES2  portpin('E', 13)

//Stepper Motor Drivers
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

//Steper Motor instances
AccelStepperExtended stepperX( PIN_MOTX_STEP,  PIN_MOTX_DIR);
AccelStepperExtended stepperY0(PIN_MOTY0_STEP, PIN_MOTY0_DIR);
AccelStepperExtended stepperY1(PIN_MOTY1_STEP, PIN_MOTY1_DIR);
AccelStepperExtended stepperZ( PIN_MOTZ_STEP,  PIN_MOTZ_DIR);
AccelStepperExtended stepperE( PIN_MOTE_STEP,  PIN_MOTE_DIR);
AccelStepperExtended stepperA( PIN_MOTA_STEP,  PIN_MOTA_DIR);
AccelStepperExtended stepperB( PIN_MOTB_STEP,  PIN_MOTB_DIR);
AccelStepperExtended stepperC( PIN_MOTC_STEP,  PIN_MOTC_DIR);

//Stepper Motor scales (steps per mm)
float scaleX = 100;
float scaleY = 100;
float scaleZ = 100;
float scaleE = 8.888888888888;
float scaleA = 100;
float scaleB = 100;
float scaleC = 100;

//speed multiplier applied to G0/F1 F-Parameter
float speed_multiplierX = 1;
float speed_multiplierY = 1;
float speed_multiplierZ = 1;
float speed_multiplierE = 12;
float speed_multiplierA = 1;
float speed_multiplierB = 1;
float speed_multiplierC = 1;


//output pin cluster
Simple_output output_pump(PIN_OUTPUT_PUMP);
Simple_output output_valve(PIN_OUTPUT_VALVE);
Simple_output output_botup(PIN_OUTPUT_BOTUP);
Simple_output output_topdn(PIN_OUTPUT_TOPDN);
Simple_output output_aux1(PIN_OUTPUT_AUX1);
Simple_output output_aux2(PIN_OUTPUT_AUX2);


//input pin cluster
Prelling_input input_endX(PIN_INPUT_XEND);
Prelling_input input_endY0(PIN_INPUT_YEND0);
Prelling_input input_endY1(PIN_INPUT_YEND1);
Prelling_input input_endZ(PIN_INPUT_ZEND);
Prelling_input input_res1(PIN_INPUT_RES1);
Prelling_input input_res2(PIN_INPUT_RES2);


bool job_prelling = false;

/**
 * Program setup
 * Does run once
 */
void setup() {
	float steps_per_mm = 100;
	float speed_cap = 500;
	float speed = 100;
	float accel = 200;
	stepperX.setStepsPer_mm(steps_per_mm);
	stepperX.setAcceleration_mm(accel);
	stepperX.setMaxSpeed_cap_mm(speed_cap);
	stepperX.setMaxSpeed_mm(speed);

	stepperY0.setStepsPer_mm(steps_per_mm);
	stepperY0.setAcceleration_mm(accel);
	stepperY0.setMaxSpeed_cap_mm(speed_cap);
	stepperY0.setMaxSpeed_mm(speed);

	stepperY1.setStepsPer_mm(steps_per_mm);
	stepperY1.setAcceleration_mm(accel);
	stepperY1.setMaxSpeed_cap_mm(speed_cap);
	stepperY1.setMaxSpeed_mm(speed);

	stepperZ.setStepsPer_mm(steps_per_mm);
	stepperZ.setAcceleration_mm(accel);
	stepperZ.setMaxSpeed_cap_mm(speed_cap);
	stepperZ.setMaxSpeed_mm(speed);

	stepperE.setStepsPer_mm(8.88888);
	stepperE.setMaxSpeed_multiplier_mm(12.0);
	stepperE.setAcceleration_mm(accel);
	stepperE.setMaxSpeed_cap_mm(speed_cap);
	stepperE.setMaxSpeed_mm(speed);

	stepperA.setStepsPer_mm(steps_per_mm);
	stepperA.setAcceleration_mm(accel);
	stepperA.setMaxSpeed_cap_mm(speed_cap);
	stepperA.setMaxSpeed_mm(speed);

	stepperB.setStepsPer_mm(steps_per_mm);
	stepperB.setAcceleration_mm(accel);
	stepperB.setMaxSpeed_cap_mm(speed_cap);
	stepperB.setMaxSpeed_mm(speed);

	stepperC.setStepsPer_mm(steps_per_mm);
	stepperC.setAcceleration_mm(accel);
	stepperC.setMaxSpeed_cap_mm(speed_cap);
	stepperC.setMaxSpeed_mm(speed);

	uart_init();
}

/**
 * Fast timer ISR. Frequency is around multiple kHz
 */
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

/**
 * Slow ISR. Frquency is 1kHz
 */
void systick_isr() {
	job_prelling = true;
}


/**
 * Background loop
 */
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
			do_cmd_drive_to_position(cmd);
		} else if (cmd.id == 'G' && (cmd.num == 28)) {
			//home
			do_cmd_home(cmd);
		} else if (cmd.id == 'G' && (cmd.num == 4)) {
			//dwell
			do_cmd_dwell(cmd);
		} else if (cmd.id == 'G' && (cmd.num == 92)) {
			//set position
			do_cmd_set_position(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 6)) {
			//tool change
			//????????
		} else if (cmd.id == 'M' && (cmd.num == 10)) {
			//vacuum on
			do_cmd_vacuum_pump(true);
		} else if (cmd.id == 'M' && (cmd.num == 11)) {
			//vacuum off
			do_cmd_vacuum_pump(false);
		} else if (cmd.id == 'M' && (cmd.num == 17)) {
			//steppers ON
			do_cmd_stepper_power(true);
		} else if (cmd.id == 'M' && (cmd.num == 18)) {
			//steppers OFF
			do_cmd_stepper_power(false);
		} else if (cmd.id == 'M' && (cmd.num == 126)) {
			//open valve
			do_cmd_vacuum_valve(true);
		} else if (cmd.id == 'M' && (cmd.num == 127)) {
			//close valve
			do_cmd_vacuum_valve(false);
		} else if (cmd.id == 'M' && (cmd.num == 42)) {
			//switch io pin
			do_cmd_io(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 201)) {
			//set max acceleration
			do_cmd_set_max_acceleration(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 203)) {
			//set max feedrate
			do_cmd_set_max_speed(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 204)) {
			//set max feedrate multiplier
			//this factor is normally 1.0000
			//it will be applied on G0/G1 commands when the F-Parameter is given
			//the given speed is multiplied with this factor before setting it.
			//this allows slow rotating axies to kind of ignore the F-Parameter
			do_cmd_set_max_speed_multiplier(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 1000)) {
			//send sync back to uart
			uart_message("SYNC");
		}
	}

	job_prelling_handle();

}



static void do_cmd_drive_to_position(Gcode_command cmd) {
	if (cmd.valueF != NAN) {
		float speed = cmd.valueF;
		stepperX.setMaxSpeed_mm(speed);
		stepperY0.setMaxSpeed_mm(speed);
		stepperY1.setMaxSpeed_mm(speed);
		stepperZ.setMaxSpeed_mm(speed);
		stepperE.setMaxSpeed_mm(speed);
		stepperA.setMaxSpeed_mm(speed);
		stepperB.setMaxSpeed_mm(speed);
		stepperC.setMaxSpeed_mm(speed);
	}

	if (cmd.valueX != NAN) {
		stepperX.moveTo_mm(cmd.valueX * scaleX);
	}
	if (cmd.valueY != NAN) {
		stepperY0.moveTo_mm(cmd.valueY * scaleY);
		stepperY1.moveTo_mm(cmd.valueY * scaleY);
	}
	if (cmd.valueZ != NAN) {
		stepperZ.moveTo_mm(cmd.valueZ * scaleZ);
	}
	if (cmd.valueA != NAN) {
		stepperA.moveTo_mm(cmd.valueA * scaleA);
	}
	if (cmd.valueB != NAN) {
		stepperB.moveTo_mm(cmd.valueB * scaleB);
	}
	if (cmd.valueC != NAN) {
		stepperC.moveTo_mm(cmd.valueC * scaleC);
	}
	if (cmd.valueE != NAN) {
		stepperE.moveTo_mm(cmd.valueE * scaleE);
	}
}


static void do_cmd_home(Gcode_command cmd) {
	homeAxle(&stepperZ, &input_endZ, -1, 10.0, 5000, 500.0, 5.0);
	homeAxle(&stepperX, &input_endX, -1, 10.0, 10000, 1000.0, 5.0);
	homeAxleDual(&stepperY0, &stepperY1, &input_endY0, &input_endY1, 10.0, 10000, 1000.0, 5.0);
}

static void homeAxle(AccelStepperExtended* stepper, Prelling_input* endstop, int homDirection, float home_speed, int home_timeout,
		float home_travel_mm, float home_travel_back_mm) {
	uint32_t endtime;

	float tmpSpeed = stepper->getMaxSpeed_mm();                  //save current motor speed for later
	stepper->setMaxSpeed_mm(home_speed);                         //set homing fast speed for 1st travel
	stepper->setCurrentPosition_mm(0.0);                         //reset position to 0
	stepper->moveTo_mm(home_travel_mm * homDirection);           //run to endstop
	endtime = millis() + home_timeout;
	while (!endstop->get() && (millis() < endtime)) {              //block until endstop or timeout reached
		__WFI();
		job_prelling_handle();
	}
	stepper->move(0);                                            //stepper shoud stop immediately
	stepper->setCurrentPosition_mm(0.0);                         //reset position to 0
	stepper->moveTo_mm(home_travel_back_mm * homDirection * -1); //go back a bit
	while (stepper->isRunning()) {                               //block until stepper reached position
		__WFI();
	    job_prelling_handle();
	}
	stepper->setMaxSpeed_mm(home_speed / 2);                     //set slow speed for 2nd forward motion
	stepper->moveTo_mm(home_travel_back_mm * 2 * homDirection);  //move to endstop 2nd time
	endtime = millis() + home_timeout / 2;
	while (!endstop->get() && (millis() < endtime)) {              //block until endstop or timeout reached
		__WFI();
		job_prelling_handle();
	}
	stepper->move(0);                                            //stepper shoud stop immediately
	stepper->setCurrentPosition_mm(0.0);                         //homing finished
	stepper->setMaxSpeed_mm(tmpSpeed);                           //restore motor speed
}


static void homeAxleDual(AccelStepperExtended* stepper1, AccelStepperExtended* stepper2, Prelling_input* endstop1, Prelling_input* endstop2,
		int homDirection, float home_speed, int home_timeout, float home_travel_mm, float home_travel_back_mm) {
	uint32_t endtime;

	float tmpSpeed = stepper1->getMaxSpeed_mm();                  //save current motor speed for later
	stepper1->setMaxSpeed_mm(home_speed);                         //set homing fast speed for 1st travel
	stepper2->setMaxSpeed_mm(home_speed);                         //set homing fast speed for 1st travel
	stepper1->setCurrentPosition_mm(0.0);                         //reset position to 0
	stepper2->setCurrentPosition_mm(0.0);                         //reset position to 0
	stepper1->moveTo_mm(home_travel_mm * homDirection);           //run to endstop
	stepper2->moveTo_mm(home_travel_mm * homDirection);           //run to endstop
	endtime = millis() + home_timeout;
	while (!(endstop1->get() && endstop2->get()) && (millis() < endtime)) {              //block until endstop or timeout reached
		__WFI();
		job_prelling_handle();
	}
	stepper1->move(0);                                            //stepper shoud stop immediately
	stepper2->move(0);                                            //stepper shoud stop immediately
	stepper1->setCurrentPosition_mm(0.0);                         //reset position to 0
	stepper2->setCurrentPosition_mm(0.0);                         //reset position to 0
	stepper1->moveTo_mm(home_travel_back_mm * homDirection * -1); //go back a bit
	stepper2->moveTo_mm(home_travel_back_mm * homDirection * -1); //go back a bit
	while (stepper1->isRunning() || stepper2->isRunning()) {                               //block until stepper reached position
		__WFI();
	    job_prelling_handle();
	}
	stepper1->setMaxSpeed_mm(home_speed / 2);                     //set slow speed for 2nd forward motion
	stepper2->setMaxSpeed_mm(home_speed / 2);                     //set slow speed for 2nd forward motion
	stepper1->moveTo_mm(home_travel_back_mm * 2 * homDirection);  //move to endstop 2nd time
	stepper2->moveTo_mm(home_travel_back_mm * 2 * homDirection);  //move to endstop 2nd time
	endtime = millis() + home_timeout / 2;
	while (!(endstop1->get() && endstop2->get()) && (millis() < endtime)) {              //block until endstop or timeout reached
		__WFI();
		job_prelling_handle();
	}
	stepper1->move(0);                                            //stepper shoud stop immediately
	stepper2->move(0);                                            //stepper shoud stop immediately
	stepper1->setCurrentPosition_mm(0.0);                         //homing finished
	stepper2->setCurrentPosition_mm(0.0);                         //homing finished
	stepper1->setMaxSpeed_mm(tmpSpeed);                           //restore motor speed
	stepper2->setMaxSpeed_mm(tmpSpeed);                           //restore motor speed
}

static void do_cmd_dwell(Gcode_command cmd) {
	if (cmd.valueT != NAN) {
		int milliseconds = round(cmd.valueT * 1000.0);
		delay(milliseconds);
	}
}


static void do_cmd_set_position(Gcode_command cmd) {
	if (cmd.valueX != NAN) {
		stepperX.setCurrentPosition_mm(cmd.valueX);
	}
	if (cmd.valueY != NAN) {
		stepperY0.setCurrentPosition_mm(cmd.valueY);
		stepperY1.setCurrentPosition_mm(cmd.valueY);
	}
	if (cmd.valueZ != NAN) {
		stepperZ.setCurrentPosition_mm(cmd.valueZ);
	}
	if (cmd.valueA != NAN) {
		stepperA.setCurrentPosition_mm(cmd.valueA);
	}
	if (cmd.valueB != NAN) {
		stepperB.setCurrentPosition_mm(cmd.valueB);
	}
	if (cmd.valueC != NAN) {
		stepperC.setCurrentPosition_mm(cmd.valueC);
	}
	if (cmd.valueE != NAN) {
		stepperE.setCurrentPosition_mm(cmd.valueE);
	}
}


static void do_cmd_vacuum_pump(bool on) {
    output_pump.set(on);
}


static void do_cmd_vacuum_valve(bool on) {
	output_valve.set(on);
}


static void do_cmd_io(Gcode_command cmd) {
	if (cmd.valueP != NAN && cmd.valueS != NAN) {
		int ioNumber = round(cmd.valueP);
		int ioValue  = round(cmd.valueS);
		switch (ioNumber) {
		case 0:	output_pump.set(ioValue);
		case 1:	output_valve.set(ioValue);
		case 2:	output_botup.set(ioValue);
		case 3:	output_topdn.set(ioValue);
		case 4:	output_aux1.set(ioValue);
		case 5:	output_aux2.set(ioValue);
		}
	}
}


static void do_cmd_stepper_power(bool on) {

}

static void do_cmd_set_max_acceleration(Gcode_command cmd) {
	if (cmd.valueX != NAN) {
		stepperX.setAcceleration_mm(cmd.valueX);
	}
	if (cmd.valueY != NAN) {
		stepperY0.setAcceleration_mm(cmd.valueY);
		stepperY1.setAcceleration_mm(cmd.valueY);
	}
	if (cmd.valueZ != NAN) {
		stepperZ.setAcceleration_mm(cmd.valueZ);
	}
	if (cmd.valueA != NAN) {
		stepperA.setAcceleration_mm(cmd.valueA);
	}
	if (cmd.valueB != NAN) {
		stepperB.setAcceleration_mm(cmd.valueB);
	}
	if (cmd.valueC != NAN) {
		stepperC.setAcceleration_mm(cmd.valueC);
	}
	if (cmd.valueE != NAN) {
		stepperE.setAcceleration_mm(cmd.valueE);
	}
}


static void do_cmd_set_max_speed(Gcode_command cmd) {
	if (cmd.valueX != NAN) {
		stepperX.setMaxSpeed_cap_mm(cmd.valueX);
	}
	if (cmd.valueY != NAN) {
		stepperY0.setMaxSpeed_cap_mm(cmd.valueY);
		stepperY1.setMaxSpeed_cap_mm(cmd.valueY);
	}
	if (cmd.valueZ != NAN) {
		stepperZ.setMaxSpeed_cap_mm(cmd.valueZ);
	}
	if (cmd.valueA != NAN) {
		stepperA.setMaxSpeed_cap_mm(cmd.valueA);
	}
	if (cmd.valueB != NAN) {
		stepperB.setMaxSpeed_cap_mm(cmd.valueB);
	}
	if (cmd.valueC != NAN) {
		stepperC.setMaxSpeed_cap_mm(cmd.valueC);
	}
	if (cmd.valueE != NAN) {
		stepperE.setMaxSpeed_cap_mm(cmd.valueE);
	}
}


static void do_cmd_set_max_speed_multiplier(Gcode_command cmd) {
	if (cmd.valueX != NAN) {
		stepperX.setMaxSpeed_multiplier_mm(cmd.valueX);
	}
	if (cmd.valueY != NAN) {
		stepperY0.setMaxSpeed_multiplier_mm(cmd.valueY);
		stepperY1.setMaxSpeed_multiplier_mm(cmd.valueY);
	}
	if (cmd.valueZ != NAN) {
		stepperZ.setMaxSpeed_multiplier_mm(cmd.valueZ);
	}
	if (cmd.valueA != NAN) {
		stepperA.setMaxSpeed_multiplier_mm(cmd.valueA);
	}
	if (cmd.valueB != NAN) {
		stepperB.setMaxSpeed_multiplier_mm(cmd.valueB);
	}
	if (cmd.valueC != NAN) {
		stepperC.setMaxSpeed_multiplier_mm(cmd.valueC);
	}
	if (cmd.valueE != NAN) {
		stepperE.setMaxSpeed_multiplier_mm(cmd.valueE);
	}
}

static void job_prelling_handle() {
	if (job_prelling) {
		input_endX.update();
		input_endY0.update();
		input_endY1.update();
		input_endZ.update();
		input_res1.update();
		input_res2.update();
		job_prelling = false;
	}
}


