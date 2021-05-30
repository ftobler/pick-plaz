/*
 * arduino_like_timer.cpp
 *
 *  Created on: May 29, 2021
 *      Author: ftobler
 */

#include "arduino_like_hal.h"
#include "main.h"
#include "stm32f4xx_hal.h"


extern TIM_HandleTypeDef htim2;  //counts in 1us interval. until it overflows at 2^32


GPIO_TypeDef* ports[] = {GPIOA, GPIOB, GPIOC, GPIOD, GPIOE, 0, 0, GPIOH};



int32_t micros() {
	return htim2.Instance->CNT;
}


void delay(int delay) {
	uint32_t startTime = uwTick;
	uint32_t endTime = startTime + delay;
	if (startTime > endTime) {
		//overflow occured. wait for uwTick to really overflow
		while (uwTick < UINT32_MAX)
		//now wait for time to be reached
		while (uwTick < endTime) {
			//busy wait
		}
	} else {
		while (uwTick < endTime) {
			//busy wait
		}
	}
}

void delayMicroseconds(int delay) {
    //not very accurate but seems to work well enough for the purpose
	delay = (delay-1) * 10;
	while (delay) {
		delay--;
	}
}


void digitalWrite(int pin, int value) {
	GPIO_TypeDef* GPIOx = ports[pin / 16];
	uint16_t GPIO_Pin = 1 << (pin & 0x0F);
	if (value) {
		GPIOx->BSRR = (uint32_t)GPIO_Pin;
	} else {
		GPIOx->BSRR = (uint32_t)(GPIO_Pin << 16);
	}
}

uint8_t digitalRead(int pin) {
	GPIO_TypeDef* GPIOx = ports[pin / 16];
	uint16_t GPIO_Pin = 1 << (pin & 0x0F);
	if ((GPIOx->IDR & GPIO_Pin) != (uint32_t)GPIO_PIN_RESET)
		return 1;
	else
		return 0;
}

void pinMode(int pin, int mode) {
	//pin mode is configured through cubeMX
}



