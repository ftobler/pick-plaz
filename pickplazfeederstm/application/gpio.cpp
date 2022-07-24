/*
 * gpio.c
 *
 *  Created on: 25.10.2020
 *      Author: ftobler
 */


#include "gpio.h"


void gpio_write(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin, uint8_t on) {
	if (on) {
		GPIOx->BSRR = (uint32_t)(GPIO_Pin);
	} else {
		GPIOx->BSRR = (uint32_t)(GPIO_Pin << 16);
	}
}


uint8_t gpio_ReadPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin) {
  if ((GPIOx->IDR & GPIO_Pin) != (uint32_t)GPIO_PIN_RESET) {
	  return 1;
  }
  return 0;
}


void gpio_SetPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin) {
  GPIOx->BSRR = (uint32_t)GPIO_Pin;
}


void gpio_ResetPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin) {
  GPIOx->BSRR = (uint32_t)(GPIO_Pin << 16);
}

