/*
 * uart_handler.cpp
 *
 *  Created on: May 29, 2021
 *      Author: ftobler
 */

#ifndef UART_HANDLER_H_
#define UART_HANDLER_H_

#include "stdint.h"


typedef struct {
	char id;
	int num;
	float valueX;  //x-axies
	float valueY;  //y-axies
	float valueZ;  //z-axies
	float valueE;  //e-axies
	float valueA;  //a-axies
	float valueB;  //b-axies
	float valueC;  //c-axies
	float valueF;  //feedrate
	float valueS;  //value for io
	float valueP;  //number for io
	float valueT;  //dwell time
	float valueO;  //command overlap
} Gcode_command;

void uart_init();
void uart_loop();
int uart_command_available();
Gcode_command uart_command_get();
void uart_message(const char* message);

#endif


