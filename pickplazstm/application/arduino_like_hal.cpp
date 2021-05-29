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

int32_t micros() {
	return htim2.Instance->CNT;
}

void delayMicroseconds(int delay) {
	int32_t time = micros();
	int32_t end = time + delay; // could overflow
	if (time - end > delay) {
		//overflowed
		while (micros() > time) {
			//wait for micros to also overflow
		}
		while (micros() < end) {
			//wait normal
		}
	} else {
		//normal
		while (micros() < end) {

		}
	}
}

GPIO_TypeDef* ports[] = {GPIOA, GPIOB, GPIOC, GPIOD, GPIOE, 0, 0, GPIOH};

void digitalWrite(int pin, int value) {
	GPIO_TypeDef* GPIOx = ports[pin / 16];
	uint16_t GPIO_Pin = 1 << (pin & 0x0F);
	if (value) {
		GPIOx->BSRR = (uint32_t)GPIO_Pin;
	} else {
		GPIOx->BSRR = (uint32_t)(GPIO_Pin << 16);
	}
}

uint8_t digitalRead(int pin, int value) {
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



