/*
 * uart_handler.cpp
 *
 *  Created on: May 29, 2021
 *      Author: ftobler
 */

#ifndef UART_HANDLER_H_
#define UART_HANDLER_H_

#include "stdint.h"

void uart_init();
uint8_t* uart_get_line(uint8_t* len);
void uart_loop();

#endif


