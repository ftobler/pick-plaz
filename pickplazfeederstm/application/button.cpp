/*
 * button.cpp
 *
 *  Created on: Jul 23, 2022
 *      Author: ftobler
 */

#include "button.h"


#define CNT_MAX 20
#define CNT_LONGPRESS 400


Button::Button(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin) {
	port = GPIOx;
	pin = GPIO_Pin;
	cnt = 0;
}


BUTTON_Event Button::update() {
	if (!gpio_ReadPin(port, pin)) {
		if (cnt < CNT_MAX) {
			cnt++;
		}
	} else {
		if (cnt) {
			cnt--;
		}
	}

	uint32_t pinState = cnt > (CNT_MAX / 2);
	if (pinState) {
		press++;
		if (press > CNT_LONGPRESS) {
			return BUTTON_hold;
		} else {
			return BUTTON_none;
		}
	} else {
		BUTTON_Event ev = BUTTON_none;
		if (press) {
			//button was pressed before. eval which press it was
			if (press > CNT_LONGPRESS) {
				ev = BUTTON_long;
			} else {
				ev = BUTTON_short;
			}
			press = 0;
		}
		return ev;
	}
}
