/*
 * io.cpp
 *
 *  Created on: May 30, 2021
 *      Author: ftobler
 */

#include "io.h"
#include "stdint.h"
#include "arduino_like_hal.h"


Simple_output::Simple_output(int a_pin) {
	pin = a_pin;
	state = 0;
}


void Simple_output::set(bool on) {
    state = on;
    digitalWrite(pin, state);
}


bool Simple_output::get() {
	return state;
}


Overloading_output::Overloading_output(int a_pin, int a_max_heat) {
	pin = pin;
	state = 0;
	heat = 0;
	max_heat = max_heat;
}


void Overloading_output::set(bool on) {
	if (heat < max_heat && on) {
		//if cool enough switch on
		state = 1;
	    digitalWrite(pin, state);
	}
	if (!on) {
		//switch off always possible
		state = 0;
	    digitalWrite(pin, state);
	}
}


void Overloading_output::update() {
	if (state) {
		heat++;
		if (heat > max_heat) {
			//switch if off because of overheating
			heat = max_heat;
			state = 0;
		    digitalWrite(pin, state);
		}
	} else {
		heat--;
		if (heat < 0) {
			heat = 0;
		}
	}
}


bool Overloading_output::get() {
	return state;
}


Simple_input::Simple_input(int a_pin) {
	pin = a_pin;
}


bool Simple_input::get() {
	return digitalRead(pin);
}


Prelling_input::Prelling_input(int a_pin) {
	pin = a_pin;
	consecutive_ticks = 0;
}


void Prelling_input::update() {
	bool state = digitalRead(pin);
	if (state) {
		consecutive_ticks++;
		if (consecutive_ticks > 5) {
			consecutive_ticks = 5;
		}
	} else {
		consecutive_ticks--;
		if (consecutive_ticks < -5) {
			consecutive_ticks = -5;
		}
	}
}


bool Prelling_input::get() {
	return consecutive_ticks > 0;
}
