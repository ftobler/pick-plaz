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


static bool is_steppers_on_position();
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
	float steps_per_mm = 25;
	float speed_cap = 500;
	float speed = 500;
	float accel = 3000;
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

	stepperE.setStepsPer_mm(2.222222);
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
	digitalWrite((('E' - 'A') * 16 + 0), 1);
	if (stepperX.isRunning())  stepperX.run();
	if (stepperY0.isRunning()) stepperY0.run();
	if (stepperY1.isRunning()) stepperY1.run();
	if (stepperZ.isRunning())  stepperZ.run();
	if (stepperE.isRunning())  stepperE.run();
	if (stepperA.isRunning())  stepperA.run();
	if (stepperB.isRunning())  stepperB.run();
	if (stepperC.isRunning())  stepperC.run();
	digitalWrite((('E' - 'A') * 16 + 0), 0);
}

/**
 * Slow ISR. Frquency is 1kHz
 */
void systick_isr() {
	job_prelling = true;
//	//digitalWrite(PIN_MOTY1_EN, 1);
//	stepperX.computeNewSpeed();
//	//digitalWrite(PIN_MOTY1_EN, 0);
//	stepperY0.computeNewSpeed();
//	stepperY1.computeNewSpeed();
//	stepperZ.computeNewSpeed();
//	stepperE.computeNewSpeed();
//	stepperA.computeNewSpeed();
//	stepperB.computeNewSpeed();
//	stepperC.computeNewSpeed();
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
	if (uart_command_available() && is_steppers_on_position()) {
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
		} else {
			//unknown command
			uart_message("ERR_COMMAND_NOT_FOUND");
		}
		if (!uart_command_available()) {
			uart_message("EMPTY");
		}
	}

	job_prelling_handle();

}

static bool is_steppers_on_position() {
	if (stepperX.isRunning()) return false;
	if (stepperY0.isRunning()) return false;
	if (stepperY1.isRunning()) return false;
	if (stepperZ.isRunning()) return false;
	if (stepperE.isRunning()) return false;
	if (stepperA.isRunning()) return false;
	if (stepperB.isRunning()) return false;
	if (stepperC.isRunning()) return false;
	return true;
}

static void do_cmd_drive_to_position(Gcode_command cmd) {
	if (cmd.valueF != NaN) {
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

	if (cmd.valueX != NaN) {
		stepperX.moveTo_mm(cmd.valueX);
	}
	if (cmd.valueY != NaN) {
		stepperY0.moveTo_mm(cmd.valueY);
		stepperY1.moveTo_mm(cmd.valueY);
	}
	if (cmd.valueZ != NaN) {
		stepperZ.moveTo_mm(cmd.valueZ);
	}
	if (cmd.valueE != NaN) {
		stepperE.moveTo_mm(cmd.valueE);
	}
	if (cmd.valueA != NaN) {
		stepperA.moveTo_mm(cmd.valueA);
	}
	if (cmd.valueB != NaN) {
		stepperB.moveTo_mm(cmd.valueB);
	}
	if (cmd.valueC != NaN) {
		stepperC.moveTo_mm(cmd.valueC);
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
	if (cmd.valueT != NaN) {
		int milliseconds = round(cmd.valueT * 1000.0);
		delay(milliseconds);
	}
}


static void do_cmd_set_position(Gcode_command cmd) {
	if (cmd.valueX != NaN) {
		stepperX.setCurrentPosition_mm(cmd.valueX);
	}
	if (cmd.valueY != NaN) {
		stepperY0.setCurrentPosition_mm(cmd.valueY);
		stepperY1.setCurrentPosition_mm(cmd.valueY);
	}
	if (cmd.valueZ != NaN) {
		stepperZ.setCurrentPosition_mm(cmd.valueZ);
	}
	if (cmd.valueE != NaN) {
		stepperE.setCurrentPosition_mm(cmd.valueE);
	}
	if (cmd.valueA != NaN) {
		stepperA.setCurrentPosition_mm(cmd.valueA);
	}
	if (cmd.valueB != NaN) {
		stepperB.setCurrentPosition_mm(cmd.valueB);
	}
	if (cmd.valueC != NaN) {
		stepperC.setCurrentPosition_mm(cmd.valueC);
	}
}


static void do_cmd_vacuum_pump(bool on) {
    output_pump.set(on);
}


static void do_cmd_vacuum_valve(bool on) {
	output_valve.set(on);
}


static void do_cmd_io(Gcode_command cmd) {
	if (cmd.valueP != NaN && cmd.valueS != NaN) {
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
	digitalWrite(PIN_MOTX_EN,  on);
	digitalWrite(PIN_MOTY0_EN, on);
	digitalWrite(PIN_MOTY1_EN, on);
	digitalWrite(PIN_MOTZ_EN,  on);
	digitalWrite(PIN_MOTE_EN,  on);
	digitalWrite(PIN_MOTA_EN,  on);
	digitalWrite(PIN_MOTB_EN,  on);
	digitalWrite(PIN_MOTC_EN,  on);
}

static void do_cmd_set_max_acceleration(Gcode_command cmd) {
	if (cmd.valueX != NaN) {
		stepperX.setAcceleration_mm(cmd.valueX);
	}
	if (cmd.valueY != NaN) {
		stepperY0.setAcceleration_mm(cmd.valueY);
		stepperY1.setAcceleration_mm(cmd.valueY);
	}
	if (cmd.valueZ != NaN) {
		stepperZ.setAcceleration_mm(cmd.valueZ);
	}
	if (cmd.valueE != NaN) {
		stepperE.setAcceleration_mm(cmd.valueE);
	}
	if (cmd.valueA != NaN) {
		stepperA.setAcceleration_mm(cmd.valueA);
	}
	if (cmd.valueB != NaN) {
		stepperB.setAcceleration_mm(cmd.valueB);
	}
	if (cmd.valueC != NaN) {
		stepperC.setAcceleration_mm(cmd.valueC);
	}
}


static void do_cmd_set_max_speed(Gcode_command cmd) {
	if (cmd.valueX != NaN) {
		stepperX.setMaxSpeed_cap_mm(cmd.valueX);
	}
	if (cmd.valueY != NaN) {
		stepperY0.setMaxSpeed_cap_mm(cmd.valueY);
		stepperY1.setMaxSpeed_cap_mm(cmd.valueY);
	}
	if (cmd.valueZ != NaN) {
		stepperZ.setMaxSpeed_cap_mm(cmd.valueZ);
	}
	if (cmd.valueE != NaN) {
		stepperE.setMaxSpeed_cap_mm(cmd.valueE);
	}
	if (cmd.valueA != NaN) {
		stepperA.setMaxSpeed_cap_mm(cmd.valueA);
	}
	if (cmd.valueB != NaN) {
		stepperB.setMaxSpeed_cap_mm(cmd.valueB);
	}
	if (cmd.valueC != NaN) {
		stepperC.setMaxSpeed_cap_mm(cmd.valueC);
	}
}


static void do_cmd_set_max_speed_multiplier(Gcode_command cmd) {
	if (cmd.valueX != NaN) {
		stepperX.setMaxSpeed_multiplier_mm(cmd.valueX);
	}
	if (cmd.valueY != NaN) {
		stepperY0.setMaxSpeed_multiplier_mm(cmd.valueY);
		stepperY1.setMaxSpeed_multiplier_mm(cmd.valueY);
	}
	if (cmd.valueZ != NaN) {
		stepperZ.setMaxSpeed_multiplier_mm(cmd.valueZ);
	}
	if (cmd.valueE != NaN) {
		stepperE.setMaxSpeed_multiplier_mm(cmd.valueE);
	}
	if (cmd.valueA != NaN) {
		stepperA.setMaxSpeed_multiplier_mm(cmd.valueA);
	}
	if (cmd.valueB != NaN) {
		stepperB.setMaxSpeed_multiplier_mm(cmd.valueB);
	}
	if (cmd.valueC != NaN) {
		stepperC.setMaxSpeed_multiplier_mm(cmd.valueC);
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


