/*
 * gpio.c
 *
 *  Created on: 25.10.2020
 *      Author: ftobler
 */


#include "gpio.h"

uint8_t gpio_read(IoPin* pin) {
	if ((pin->port->IDR & pin->pin) != (uint32_t)GPIO_PIN_RESET) {
		return 1;
	}
	return 0;
}
void gpio_write(IoPin* pin, uint8_t on) {
	if (on) {
		pin->port->BSRR = (uint32_t)(pin->pin);
	} else {
		pin->port->BSRR = (uint32_t)(pin->pin << 16);
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

