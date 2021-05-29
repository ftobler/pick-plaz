/*
 * gpio.h
 *
 *  Created on: 25.10.2020
 *      Author: ftobler
 */

#ifndef APP_GPIO_H_
#define APP_GPIO_H_

#include "stm32f4xx_hal.h"
#include <stdint.h>

typedef struct {
	uint16_t pin;
	GPIO_TypeDef* port;
} IoPin;


uint8_t gpio_read(IoPin* pin);
void gpio_write(IoPin* pin, uint8_t on);

uint8_t gpio_ReadPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin);
void gpio_SetPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin);
void gpio_ResetPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin);


#endif
