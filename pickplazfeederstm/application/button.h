/*
 * button.h
 *
 *  Created on: Jul 23, 2022
 *      Author: ftobler
 */

#ifndef BUTTON_H_
#define BUTTON_H_


#include "stdint.h"
#include "gpio.h"


typedef enum {
	BUTTON_none,
	BUTTON_short,  //generated on release
	BUTTON_long,   //generated on release
	BUTTON_hold,   //while holding the button and count as longpress
} BUTTON_Event;

class Button {
private:
	GPIO_TypeDef* port;
	uint16_t pin;
	uint32_t cnt;  //for debounce
	uint32_t press;  //for long press
public:
	Button(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin);
	BUTTON_Event update();
};



#endif /* BUTTON_H_ */
