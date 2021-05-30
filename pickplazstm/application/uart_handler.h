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
	float valueX;
	float valueY;
	float valueZ;
	float valueE;
	float valueA;
	float valueB;
	float valueC;
	float valueF;
	float valueS;
	float valueP;
	float valueT;
} Gcode_command;

void uart_init();
void uart_loop();
int uart_command_available();
Gcode_command uart_command_get();
void uart_message(const char* message);

#endif


