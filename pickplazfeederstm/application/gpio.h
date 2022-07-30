/*
 * gpio.h
 *
 *  Created on: 25.10.2020
 *      Author: ftobler
 */

#ifndef APP_GPIO_H_
#define APP_GPIO_H_


#ifdef __cplusplus
extern "C" {
#endif


#include "stm32f0xx_hal.h"
#include "stdint.h"


typedef struct {
	uint16_t pin;
	GPIO_TypeDef* port;
} IoPin;


void gpio_write(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin, uint8_t on);
uint8_t gpio_ReadPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin);
void gpio_SetPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin);
void gpio_ResetPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin);


#ifdef __cplusplus
}
#endif


#endif
