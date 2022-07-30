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


static void default_settings();
static bool is_steppers_on_position();
static void do_cmd_drive_to_position(Gcode_command cmd);
static void do_cmd_home(Gcode_command cmd);
static void homeAxle(AccelStepperExtended* stepper, Prelling_input* endstop, int homDirection, float home_speed = 10.0f, int home_timeout = 10000,
		float home_travel_mm = 1000.0f, float home_travel_back_mm = 5.0f, float sensor_position = -1.0f);
static void homeAxleDual(AccelStepperExtended* stepper1, AccelStepperExtended* stepper2, Prelling_input* endstop1, Prelling_input* endstop2,
		int homDirection, float home_speed = 10.0f, int home_timeout = 10000, float home_travel_mm = 1000.0f, float home_travel_back_mm = 5.0f, float sensor_position = -1.0f);
static void do_cmd_dwell(Gcode_command cmd);
static void do_cmd_set_position(Gcode_command cmd);
static void do_cmd_vacuum_pump(bool on);
static void do_cmd_vacuum_valve(bool on);
static void do_cmd_io(Gcode_command cmd);
static void do_cmd_stepper_power(bool on);
static void do_cmd_set_max_acceleration(Gcode_command cmd);
static void do_cmd_set_max_speed(Gcode_command cmd);
static void do_cmd_set_max_speed_multiplier(Gcode_command cmd);
static void do_cmd_feeder(Gcode_command cmd);
static void job_prelling_handle();


//output pin cluster (these have FET driver to either 5V or 12V)
#define PIN_OUTPUT_PUMP  portpin('C', 6)  //12V
#define PIN_OUTPUT_AUX1  portpin('D', 15) //written as VALVE on PCB on early revision. 5V
#define PIN_OUTPUT_BOTUP portpin('D', 14) //12V
#define PIN_OUTPUT_TOPDN portpin('D', 13) //12V
#define PIN_OUTPUT_VALVE portpin('D', 12) //written as AUX1 on PCB on early revision. 12V
#define PIN_OUTPUT_TRAY  portpin('D', 11) //written as AUX2 on PCB on early revision. 12V

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

//debug leds
#define PIN_DEBUG0     portpin('B', 1)
#define PIN_DEBUG1     portpin('B', 2)
#define PIN_DEBUG2     portpin('B', 13)
#define PIN_DEBUG3     portpin('B', 14)

//microstep setting
#define PIN_MOT_MS1    portpin('E', 10)
#define PIN_MOT_MS2    portpin('E', 11)
#define PIN_MOT_MS3    portpin('E', 12)

//feeder pins
#define PIN_FEEDER0    portpin('A', 4)
#define PIN_FEEDER1    portpin('C', 4)
#define PIN_FEEDER2    portpin('C', 5)
#define PIN_FEEDER3    portpin('B', 0)

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
Simple_output output_tray(PIN_OUTPUT_TRAY);

//input pin cluster
Prelling_input input_endX(PIN_INPUT_XEND);
Prelling_input input_endY0(PIN_INPUT_YEND0);
Prelling_input input_endY1(PIN_INPUT_YEND1);
Prelling_input input_endZ(PIN_INPUT_ZEND);
Prelling_input input_res1(PIN_INPUT_RES1);
Prelling_input input_res2(PIN_INPUT_RES2);

//feeder cluster
Feeder_automatic feeder0(PIN_FEEDER0);
Feeder_automatic feeder1(PIN_FEEDER1);
Feeder_automatic feeder2(PIN_FEEDER2);
Feeder_automatic feeder3(PIN_FEEDER3);


static bool job_prelling = false;
static float target_completeness = NaN;
static float current_speed = 175.0f;


/**
 * Program setup
 * Does run once
 */
void setup() {

	//set microstepping to 4x
	//works only on board v1e or later
	digitalWrite(PIN_MOT_MS1, 0);
	digitalWrite(PIN_MOT_MS2, 1);
	digitalWrite(PIN_MOT_MS3, 0);

	default_settings();

	uart_init();

	do_cmd_stepper_power(false);
}


/*
 * apply defaultl settings on the controller
 * This is used as a revert back to normal
 */
static void default_settings() {
	float steps_per_mm =   50.0f*2.0f;
	//this is stable speed, but it seems a bit slow
	float speed_cap =     120.0f;
	float speed =         120.0f;
	float accel =         600.0f;

	//this was too fast
	// float speed_cap =     175.0f;
	// float speed =         175.0f;
	// float accel =        1000.0f;
	current_speed = speed;
	//note:
	//Trinamic drivers seem to 'wander' slowly, could have to do with
	//their interpolation and the fact that the step pin
	//might be stuck at high.

	stepperX.setStepsPer_mm(steps_per_mm);
	stepperX.setAcceleration_mm(accel);
	stepperX.setMaxSpeed_cap_mm(speed_cap);
	stepperX.setMaxSpeed_mm(speed);
	stepperX.setMaxSpeed_multiplier_mm(1.0);
//	stepperX._isTrinamic = true;

	stepperY0.setStepsPer_mm(steps_per_mm);
	stepperY0.setAcceleration_mm(accel);
	stepperY0.setMaxSpeed_cap_mm(speed_cap);
	stepperY0.setMaxSpeed_mm(speed);
	stepperY0.setMaxSpeed_multiplier_mm(1.0);

	stepperY1.setStepsPer_mm(steps_per_mm);
	stepperY1.setAcceleration_mm(accel);
	stepperY1.setMaxSpeed_cap_mm(speed_cap);
	stepperY1.setMaxSpeed_mm(speed);
	stepperY1.setMaxSpeed_multiplier_mm(1.0);

	stepperZ.setStepsPer_mm(steps_per_mm/2.0f);
	stepperZ.setAcceleration_mm(accel);
	stepperZ.setMaxSpeed_cap_mm(speed_cap*2.0f);
	stepperZ.setMaxSpeed_mm(speed*2.0f);
	stepperZ.setMaxSpeed_multiplier_mm(1.0);

	stepperE.setStepsPer_mm(2.222222f*2.0f);
	stepperE.setAcceleration_mm(15000.0f);
	stepperE.setMaxSpeed_cap_mm(2000.0f);
	stepperE.setMaxSpeed_mm(2000.0f);
	stepperE.setMaxSpeed_multiplier_mm(12.0);

	stepperA.setStepsPer_mm(steps_per_mm);
	stepperA.setAcceleration_mm(accel);
	stepperA.setMaxSpeed_cap_mm(speed_cap);
	stepperA.setMaxSpeed_mm(speed);
	stepperA.setMaxSpeed_multiplier_mm(1.0);

	stepperB.setStepsPer_mm(steps_per_mm);
	stepperB.setAcceleration_mm(accel);
	stepperB.setMaxSpeed_cap_mm(speed_cap);
	stepperB.setMaxSpeed_mm(speed);
	stepperB.setMaxSpeed_multiplier_mm(1.0);

	stepperC.setStepsPer_mm(steps_per_mm);
	stepperC.setAcceleration_mm(accel);
	stepperC.setMaxSpeed_cap_mm(speed_cap);
	stepperC.setMaxSpeed_mm(speed);
	stepperC.setMaxSpeed_multiplier_mm(1.0);
}


/**
 * Fast timer ISR. Frequency is around multiple kHz
 */
void timer_isr() {
	if (stepperX.isRunning())  stepperX.run();
	if (stepperY0.isRunning()) stepperY0.run();
	if (stepperY1.isRunning()) stepperY1.run();
	if (stepperZ.isRunning())  stepperZ.run();
	if (stepperE.isRunning())  stepperE.run();
	if (stepperA.isRunning())  stepperA.run();
	if (stepperB.isRunning())  stepperB.run();
	if (stepperC.isRunning())  stepperC.run();
}


/**
 * Slow ISR. Frquency is 1kHz
 */
void systick_isr() {
	job_prelling = true;
}


/**
 * Background loop of Microcontroller
 */
void loop() {

	uart_loop();
	if (uart_command_available() && is_steppers_on_position()) {
		Gcode_command cmd = uart_command_get();
		target_completeness = NaN; //initialize default
		if (cmd.id == 'G' && (cmd.num == 0 || cmd.num == 1)) {
			//drive to position
			//there is no difference between G0 and G1
			//Each motor drives at its own max speed. Some axies might reach the target
			//before others
			//eg:  G0 X10 Y20 => drive X to 10 and Y to 20. All other motors are not changed in position
			//axies are: X, Y, Z, E, A, B, C
			do_cmd_drive_to_position(cmd);
		} else if (cmd.id == 'G' && (cmd.num == 28)) {
			//home all axies. They are homed in an order which is safe for the machine
			//eg:  G28
			//axies which are homed are: Z, X, Y (in that order)
			do_cmd_stepper_power(true);  //switch it on first.
			do_cmd_home(cmd);
		} else if (cmd.id == 'G' && (cmd.num == 4)) {
			//dwell / wait for a given amount of time
			//eg: G4 T5.5 => wait for 5.5s
			do_cmd_dwell(cmd);
		} else if (cmd.id == 'G' && (cmd.num == 92)) {
			//set position ot the motors without driving them
			//eg:  G0 X10 Y20 => set X to 10 and Y to 20
			do_cmd_set_position(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 6)) {
			//tool change command
			//not implemented
		} else if (cmd.id == 'M' && (cmd.num == 10)) {
			//vacuum pump on
			//eg: M10
			do_cmd_vacuum_pump(true);
		} else if (cmd.id == 'M' && (cmd.num == 11)) {
			//vacuum pump off
			//eg: M11
			do_cmd_vacuum_pump(false);
		} else if (cmd.id == 'M' && (cmd.num == 17)) {
			//steppers ON
			//eg: M17
			do_cmd_stepper_power(true);
		} else if (cmd.id == 'M' && (cmd.num == 18)) {
			//steppers OFF
			//eg: M18
			do_cmd_stepper_power(false);
		} else if (cmd.id == 'M' && (cmd.num == 126)) {
			//open valve (powers it)
			//eg: M126
			do_cmd_vacuum_valve(true);
		} else if (cmd.id == 'M' && (cmd.num == 127)) {
			//close valve (un-powers it)
			//eg: M127
			do_cmd_vacuum_valve(false);
		} else if (cmd.id == 'M' && (cmd.num == 42)) {
			//switch io pin
			//eg M42 P0 S1 => turns output 0 on
			//the outputs are driven by a low side FET and either 5V or 12V
			do_cmd_io(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 201)) {
			//set max acceleration
			//eg: M201 X500 => sets only X-axies to 500mm/s^2
			do_cmd_set_max_acceleration(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 203)) {
			//set max feedrate
			//set max acceleration
			//eg: M203 X50 => sets only X-axies to 50mm/s
			do_cmd_set_max_speed(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 204)) {
			//set max feedrate multiplier
			//this factor is normally 1.0000
			//it will be applied on G0/G1 commands when the F-Parameter is given
			//the given speed is multiplied with this factor before setting it.
			//this allows slow rotating axies to kind of ignore the F-Parameter
			//eg: M204 X1.00
			do_cmd_set_max_speed_multiplier(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 205)) {
			//control feeders (all of them)
			//feeder number is specified on 'P'    - P = 0..3
			//feeder direction is specified on 'S' - (S > 0.5) => forward, (s <= 0.5) => backward
			//eg: M205 P2 S1 => will advance feeder 2 to the next part
			do_cmd_feeder(cmd);
		} else if (cmd.id == 'M' && (cmd.num == 512)) {
			//set default state for feedrate & accelerations
			//eg: M512
			default_settings();
		} else if (cmd.id == 'M' && (cmd.num == 1000)) {
			//send sync back to uart
			//use this to detect when the machine has successfully cleared the queue to this point.
			//eg: M1000
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
	if (target_completeness == NaN) {
		if (stepperX.isRunning()) return false;
		if (stepperY0.isRunning()) return false;
		if (stepperY1.isRunning()) return false;
		if (stepperZ.isRunning()) return false;
		if (stepperE.isRunning()) return false;
		if (stepperA.isRunning()) return false;
		if (stepperB.isRunning()) return false;
		if (stepperC.isRunning()) return false;
	} else {
		float complete = target_completeness; //buffer float
		if (stepperX.getRemainingMoveLength() > complete) return false;
		if (stepperY0.getRemainingMoveLength() > complete) return false;
		if (stepperY1.getRemainingMoveLength() > complete) return false;
		if (stepperZ.getRemainingMoveLength() > complete) return false;
		if (stepperE.getRemainingMoveLength() > complete) return false;
		if (stepperA.getRemainingMoveLength() > complete) return false;
		if (stepperB.getRemainingMoveLength() > complete) return false;
		if (stepperC.getRemainingMoveLength() > complete) return false;
	}
	return true;
}


static void do_cmd_drive_to_position(Gcode_command cmd) {
	if (cmd.valueF != NaN) {
		current_speed = cmd.valueF;
	}
	float speed = current_speed;
	stepperX.setMaxSpeed_mm(speed);
	stepperY0.setMaxSpeed_mm(speed);
	stepperY1.setMaxSpeed_mm(speed);
	stepperZ.setMaxSpeed_mm(speed);
	stepperE.setMaxSpeed_mm(speed);
	stepperA.setMaxSpeed_mm(speed);
	stepperB.setMaxSpeed_mm(speed);
	stepperC.setMaxSpeed_mm(speed);

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
	if (cmd.valueR != NaN) {
		if (cmd.valueR < 0.0f) {
			target_completeness = 0.0f;
		} else {
			target_completeness = cmd.valueR;
		}
	}
}


static void do_cmd_home(Gcode_command cmd) {
	target_completeness = NaN; //can't have that here

	//home all axles if no extra parameters given
	if (cmd.valueX == NaN && cmd.valueX == NaN && cmd.valueZ == NaN) {
		cmd.valueX = 0;
		cmd.valueY = 0;
		cmd.valueZ = 0;
	}
	if (cmd.valueZ != NaN) {
		float tmpSpeed = stepperZ.getMaxSpeed_mm();
		       //motor      endstop     dir  speed     timeout  travel backtravel
		homeAxle(&stepperZ, &input_endZ,  1, 80.0f/4.0f, 5000,   15.0f, 7.5f, 9.0f);
		stepperZ.setMaxSpeed_mm(tmpSpeed);
	}
	if (cmd.valueX != NaN) {
		float tmpSpeed = stepperX.getMaxSpeed_mm();
	           //motor      endstop     dir  speed     timeout  travel backtravel
		homeAxle(&stepperX, &input_endX, -1, 80.0f/4.0f, 30000, 400.0f, 3.0f, -1.0f);
		stepperX.setMaxSpeed_mm(tmpSpeed);
	}
	if (cmd.valueY != NaN) {
		float tmpSpeed = stepperY0.getMaxSpeed_mm();
	                //motor1     motor2      endstop1      endstop2     dir  speed     timeout  travel backtravel
		homeAxleDual(&stepperY0, &stepperY1, &input_endY0, &input_endY1, -1, 80.0f/4.0f, 30000, 400.0f, 3.0f, -1.0f);
		stepperY0.setMaxSpeed_mm(tmpSpeed);
		stepperY1.setMaxSpeed_mm(tmpSpeed);
	}
}


static void homeAxle(AccelStepperExtended* stepper, Prelling_input* endstop, int homDirection, float home_speed, int home_timeout,
		float home_travel_mm, float home_travel_back_mm, float sensor_position) {
	uint32_t endtime;
	target_completeness = NaN; //can't have that here


	stepper->setMaxSpeed_mm(home_speed);                         //set homing fast speed for 1st travel
	stepper->setCurrentPosition_mm(0.0f);                         //reset position to 0
	stepper->moveTo_mm(home_travel_mm * homDirection);           //run to endstop
	endtime = millis() + home_timeout;
	while (endstop->get() && (millis() < endtime)) {              //block until endstop or timeout reached
		__WFI();
		job_prelling_handle();
	}
	if (millis() >= endtime) return;
	stepper->move(0);                                            //stepper shoud stop immediately
	stepper->setCurrentPosition_mm(0.0f);                         //reset position to 0
	stepper->moveTo_mm(home_travel_back_mm * homDirection * -1.0f); //go back a bit
	while (stepper->isRunning()) {                               //block until stepper reached position
		__WFI();
	    job_prelling_handle();
	}
	stepper->setMaxSpeed_mm(home_speed / 6.0f);                     //set slow speed for 2nd forward motion
	stepper->moveTo_mm(home_travel_back_mm * 2.0f * homDirection);  //move to endstop 2nd time
	endtime = millis() + home_timeout / 2.0f;
	while (endstop->get() && (millis() < endtime)) {              //block until endstop or timeout reached
		__WFI();
		job_prelling_handle();
	}
	if (millis() >= endtime) return;
	stepper->move(0);                                            //stepper shoud stop immediately
	stepper->setCurrentPosition_mm(sensor_position);                       //homing finished
	stepper->moveTo_mm(0.0f);
}


static void homeAxleDual(AccelStepperExtended* stepper1, AccelStepperExtended* stepper2, Prelling_input* endstop1, Prelling_input* endstop2,
		int homDirection, float home_speed, int home_timeout, float home_travel_mm, float home_travel_back_mm, float sensor_position) {
	uint32_t endtime;

	target_completeness = NaN; //can't have that here

	float tmpSpeed = stepper1->getMaxSpeed_mm();                  //save current motor speed for later
	stepper1->setMaxSpeed_mm(home_speed);                         //set homing fast speed for 1st travel
	stepper2->setMaxSpeed_mm(home_speed);                         //set homing fast speed for 1st travel
	stepper1->setCurrentPosition_mm(0.0f);                         //reset position to 0
	stepper2->setCurrentPosition_mm(0.0f);                         //reset position to 0
	stepper1->moveTo_mm(home_travel_mm * homDirection);           //run to endstop
	stepper2->moveTo_mm(home_travel_mm * homDirection);           //run to endstop
	endtime = millis() + home_timeout;
	bool endstop1_reach = false;
	bool endstop2_reach = false;
	while (!(endstop1_reach && endstop2_reach) && (millis() < endtime)) {              //block until endstop or timeout reached
		__WFI();
		if (!endstop1->get()) {
			stepper1->move(0);                                     //stepper shoud stop immediately
			endstop1_reach = true;
		}
		if (!endstop2->get()) {
			stepper2->move(0);                                     //stepper shoud stop immediately
			endstop2_reach = true;
		}
		job_prelling_handle();
	}
	if (millis() >= endtime) return;
	stepper1->move(0);                                            //stepper shoud stop immediately
	stepper2->move(0);                                            //stepper shoud stop immediately
	stepper1->setCurrentPosition_mm(0.0f);                         //reset position to 0
	stepper2->setCurrentPosition_mm(0.0f);                         //reset position to 0
	stepper1->moveTo_mm(home_travel_back_mm * homDirection * -1.0f); //go back a bit
	stepper2->moveTo_mm(home_travel_back_mm * homDirection * -1.0f); //go back a bit
	while (stepper1->isRunning() || stepper2->isRunning()) {                               //block until stepper reached position
		__WFI();
	    job_prelling_handle();
	}
	stepper1->setMaxSpeed_mm(home_speed / 6.0f);                     //set slow speed for 2nd forward motion
	stepper2->setMaxSpeed_mm(home_speed / 6.0f);                     //set slow speed for 2nd forward motion
	stepper1->moveTo_mm(home_travel_back_mm * 2.0f * homDirection);  //move to endstop 2nd time
	stepper2->moveTo_mm(home_travel_back_mm * 2.0f * homDirection);  //move to endstop 2nd time
	endtime = millis() + home_timeout / 2.0f;
	endstop1_reach = false;
	endstop2_reach = false;
	while (!(endstop1_reach && endstop2_reach) && (millis() < endtime)) {              //block until endstop or timeout reached
		__WFI();
		if (!endstop1->get()) {
			stepper1->move(0);                                     //stepper shoud stop immediately
			endstop1_reach = true;
		}
		if (!endstop2->get()) {
			stepper2->move(0);                                     //stepper shoud stop immediately
			endstop2_reach = true;
		}
		job_prelling_handle();
	}
	if (millis() >= endtime) return;
	stepper1->move(0);                                            //stepper shoud stop immediately
	stepper2->move(0);                                            //stepper shoud stop immediately
	stepper1->setCurrentPosition_mm(sensor_position);                         //homing finished
	stepper2->setCurrentPosition_mm(sensor_position);                         //homing finished
	stepper1->moveTo_mm(0.0f);
	stepper2->moveTo_mm(0.0f);
	stepper1->setMaxSpeed_mm(tmpSpeed);                           //restore motor speed
	stepper2->setMaxSpeed_mm(tmpSpeed);                           //restore motor speed
}


static void do_cmd_dwell(Gcode_command cmd) {
	if (cmd.valueT != NaN) {
		int milliseconds = round(cmd.valueT * 1000.0f);
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
		case 0:	output_pump.set(ioValue); break;
		case 1:	output_aux1.set(ioValue); break;
		case 2:	output_botup.set(ioValue); break;
		case 3:	output_topdn.set(ioValue); break;
		case 4:	output_valve.set(ioValue); break;
		case 5:	output_tray.set(ioValue); break;
		}
	}
}


static void do_cmd_stepper_power(bool on) {
	on = !on;
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


static void do_cmd_feeder(Gcode_command cmd) {
	if (cmd.valueP != NaN && cmd.valueS != NaN) {
	    uint32_t feeder_nr = round(cmd.valueP);
		uint32_t is_direction_forward = cmd.valueS > 0.5f;
		switch (feeder_nr) {
			case 0: feeder0.feed(is_direction_forward); break;
			case 1: feeder1.feed(is_direction_forward); break;
			case 2: feeder2.feed(is_direction_forward); break;
			case 3: feeder3.feed(is_direction_forward); break;
	    }
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


