/*
 * io.h
 *
 *  Created on: May 30, 2021
 *      Author: ftobler
 */

#ifndef IO_H_
#define IO_H_


#include "stdint.h"

class Simple_output {
private:
	int pin;
	bool state;
public:
	Simple_output(int a_pin);
	void set(bool on);
	bool get();
};

class Overloading_output {
private:
	int pin;
	bool state;
	int heat;
	int max_heat;
public:
	Overloading_output(int a_pin, int max_heat);
	void set(bool on);
	void update();
	bool get();
};

class Simple_input {
private:
	int pin;
public:
	Simple_input(int a_pin);
	bool get();
};

class Prelling_input {
private:
	int pin;
	int consecutive_ticks;
public:
	Prelling_input(int a_pin);
	void update();
	bool get();
};

#endif /* IO_H_ */
