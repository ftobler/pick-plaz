/*
 * uart_handler.cpp
 *
 *  Created on: May 29, 2021
 *      Author: ftobler
 */


#include "uart_handler.h"
#include "main.h"
#include "stm32f4xx_hal.h"
#include "Serial.h"

extern UART_HandleTypeDef huart1;
extern Serial serial1;


#define UART_BUF_SIZE 128
uint8_t buf[2][UART_BUF_SIZE];
uint8_t isr_rec_byte[5];
uint8_t isr_trans_byte[5];



void uart_init() {
	//HAL_UART_Receive_IT(&huart1, isr_rec_byte, 5);
	Serial_init(&serial1, &huart1);
}


/*void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    for (int i = 0; i < 5; i++) {
    	isr_trans_byte[i] = isr_rec_byte[i];
    }
	HAL_UART_Receive_IT(&huart1, isr_rec_byte, 5);
	HAL_UART_Transmit_IT(&huart1, isr_trans_byte, 5);
}*/


uint8_t* uart_get_line(uint8_t* len) {
	return 0;
}


void uart_loop() {
	//static char* str = "STM32 sagt hallo\n";

	//HAL_UART_Transmit_IT(&huart1, (uint8_t*)str, 17);
	while (Serial_available(&serial1)) {
		uint8_t buf = Serial_read(&serial1);
		Serial_write(&serial1, buf);
	}


	//Serial_write(&serial1, 'a');
}



