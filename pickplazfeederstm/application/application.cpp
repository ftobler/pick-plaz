/*
 * application.cpp
 *
 *  Created on: Jul 23, 2022
 *      Author: ftobler
 */


#include "application.h"
#include "stm32f0xx_hal.h"
#include "main.h"
#include "gpio.h"
#include "button.h"



typedef enum {
	MOTOR_init,
	MOTOR_idle,
	Motor_running_forward,
	Motor_running_backward,
	Motor_break,
} MOTOR_en;

typedef enum {
	APP_init,
	APP_idle,
	APP_increment_forward1,
	APP_increment_backward1,
	APP_increment_forward2,
	APP_increment_backward2,
	APP_free_forward,
	APP_free_backward,
} APP_en;

enum {
	MOTOR_FORWARD_NORMAL = 2048,
	MOTOR_BACKWARD_NORMAL = -2048,
	MOTOR_FORWARD_FAST = 2048,
	MOTOR_BACKWARD_FAST = -2048,
	MOTOR_STOP = 0
};

extern ADC_HandleTypeDef hadc;
extern TIM_HandleTypeDef htim1; //led
extern TIM_HandleTypeDef htim3; //motor


static volatile uint32_t adc_opto_value = 0;
static Button btnForward(SW_FORWARD_GPIO_Port, SW_FORWARD_Pin);
static Button btnBackward(SW_BACKWARD_GPIO_Port, SW_BACKWARD_Pin);

static uint32_t opto_is_indexed = 0;
static uint32_t last_feed_signal_state = 0;

static uint32_t app_forward_request = 0;
static uint32_t app_backward_request = 0;
static uint32_t app_forward_continious_rq = 0;
static uint32_t app_backward_continious_rq = 0;
static APP_en app_state = APP_init;
static uint32_t app_timer = 0;
static void run_app_fsm();

static int32_t motor_target = 0;   // -2047..+2047. 0 = not running
static MOTOR_en motor_state = MOTOR_init;
static uint32_t motor_timer = 0;
static void run_motor_fsm();
static void set_motor(uint32_t pwm, uint32_t direction);

static void eval_led();


void app_init() {
	HAL_ADCEx_Calibration_Start(&hadc);
	HAL_TIM_Base_Start(&htim1);
	HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
	HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_2);
	HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_3);
	HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_4);
	HAL_TIM_Base_Start(&htim3);
	HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
	HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_2);
	gpio_SetPin(OPTO_LED_GPIO_Port, OPTO_LED_Pin);
}

void app_systick() {

	//if feed signal is present, request a forward request once.
	uint32_t feed_signal_state = !gpio_ReadPin(FEED_GPIO_Port, FEED_Pin);
	if (last_feed_signal_state != feed_signal_state && feed_signal_state) {
		app_forward_request = 1;
	}
	last_feed_signal_state = feed_signal_state;

	//handle button action
	switch (btnForward.update()) {
	case BUTTON_short:
		app_forward_request = 1;
		break;
	case BUTTON_long:
		break;
	case BUTTON_hold:
		app_forward_continious_rq = 1;
		break;
	case BUTTON_none:
	default:
		app_forward_continious_rq = 0;
	}


	//handle button action
	switch (btnBackward.update()) {
	case BUTTON_short:
		app_backward_request = 1;
		break;
	case BUTTON_long:
		break;
	case BUTTON_hold:
		app_backward_continious_rq = 1;
		break;
	case BUTTON_none:
	default:
		app_backward_continious_rq = 0;
	}

	//get the opto interruptor state
	HAL_ADC_Start(&hadc);
	HAL_ADC_PollForConversion(&hadc, 1);
	adc_opto_value = HAL_ADC_GetValue(&hadc); //
	HAL_ADC_Stop(&hadc);
	if (opto_is_indexed) {
		opto_is_indexed = adc_opto_value > 2800;
	} else {
		opto_is_indexed = adc_opto_value > 3200;
	}

	//set the leds
//	htim1.Instance->CCR1 = opto_is_indexed ? 2047 : 0;
//	htim1.Instance->CCR4 = gpio_ReadPin(FEED_GPIO_Port, FEED_Pin) ? 2047 : 0;

	run_app_fsm();
	run_motor_fsm();
	eval_led();
}


extern uint8_t sintab[256];
uint32_t sine_speed = 55;

static void eval_led() {
	if (app_state == APP_idle) {
		if (opto_is_indexed) {
			htim1.Instance->CCR4 = 2048;
			htim1.Instance->CCR3 = 0;
			htim1.Instance->CCR2 = 0;
			htim1.Instance->CCR1 = 0;
		} else {
			uint32_t t1 = uwTick;
			uint32_t t2 = t1 + 128;
			htim1.Instance->CCR4 = 0;
			htim1.Instance->CCR3 = sintab[t1 % 256] * 8;
			htim1.Instance->CCR2 = sintab[t2 % 256] * 8;
			htim1.Instance->CCR1 = 0;
		}
	} else if (app_state == APP_increment_forward1 || app_state == APP_increment_forward2 || app_state == APP_free_forward) {
		uint32_t t1 = uwTick;
		uint32_t t2 = t1 + sine_speed;
		uint32_t t3 = t2 + sine_speed;
		uint32_t t4 = t3 + sine_speed;
		htim1.Instance->CCR1 = sintab[t1 % 256] * 8;
		htim1.Instance->CCR2 = sintab[t2 % 256] * 8;
		htim1.Instance->CCR3 = sintab[t3 % 256] * 8;
		htim1.Instance->CCR4 = sintab[t4 % 256] * 8;
	} else if (app_state == APP_increment_backward1 || app_state == APP_increment_backward2 || app_state == APP_free_backward) {
		uint32_t t4 = uwTick;
		uint32_t t3 = t4 + sine_speed;
		uint32_t t2 = t3 + sine_speed;
		uint32_t t1 = t2 + sine_speed;
		htim1.Instance->CCR1 = sintab[t1 % 256] * 8;
		htim1.Instance->CCR2 = sintab[t2 % 256] * 8;
		htim1.Instance->CCR3 = sintab[t3 % 256] * 8;
		htim1.Instance->CCR4 = sintab[t4 % 256] * 8;
	} else {
		uint32_t t1 = uwTick;
		uint32_t t2 = t1 + 128;
		uint32_t t3 = t2 + 128;
		uint32_t t4 = t3 + 128;
		htim1.Instance->CCR1 = sintab[t1 % 256] * 8;
		htim1.Instance->CCR2 = sintab[t2 % 256] * 8;
		htim1.Instance->CCR3 = sintab[t3 % 256] * 8;
		htim1.Instance->CCR4 = sintab[t4 % 256] * 8;
	}
}




static void run_app_fsm() {
	switch (app_state) {
	case APP_init:
		app_state = APP_idle;
		app_timer = 200;
		break;
	case APP_idle:
		motor_target = MOTOR_STOP;
		if (app_forward_request) {
			app_state = APP_increment_forward1;
			app_forward_request = 0;
			app_timer = 500;
		}
		if (app_backward_request) {
			app_state = APP_increment_backward1;
			app_backward_request = 0;
			app_timer = 500;
		}
		if (app_forward_continious_rq) {
			app_state = APP_free_forward;
		}
		if (app_backward_continious_rq) {
			app_state = APP_free_backward;
		}
		break;
	case APP_increment_forward1:
		motor_target = MOTOR_FORWARD_NORMAL;
		if (!opto_is_indexed) {
			app_state = APP_increment_forward2;
			app_timer = 1500;
		}
		if (app_timer) {
			app_timer--;
		} else {
			app_state = APP_idle; //abord
		}
		break;
	case APP_increment_forward2:
		motor_target = MOTOR_FORWARD_NORMAL;
		if (opto_is_indexed) {
			app_state = APP_idle; //regular success
		}
		if (app_timer) {
			app_timer--;
		} else {
			app_state = APP_idle; //abord
		}
		break;
	case APP_increment_backward1:
		motor_target = MOTOR_BACKWARD_NORMAL;
		if (!opto_is_indexed) {
			app_state = APP_increment_backward2;
			app_timer = 1500;
		}
		if (app_timer) {
			app_timer--;
		} else {
			app_state = APP_idle; //abord
		}
		break;
	case APP_increment_backward2:
		motor_target = MOTOR_BACKWARD_NORMAL;
		if (opto_is_indexed) {
			app_state = APP_idle; //regular success
		}
		if (app_timer) {
			app_timer--;
		} else {
			app_state = APP_idle; //abord
		}
		break;
	case APP_free_forward:
		motor_target = MOTOR_FORWARD_FAST;
		if (!app_forward_continious_rq) {
			app_state = APP_increment_forward2;
			app_timer = 1500;
		}
		break;
	case APP_free_backward:
		motor_target = MOTOR_BACKWARD_FAST;
		if (!app_backward_continious_rq) {
			app_state = APP_increment_backward2;
			app_timer = 1500;
		}
		break;
	default:
		app_state = APP_init;
	}
}


static void run_motor_fsm() {
	//motor state machine
	//applies breaking by turning the other direction
	switch (motor_state) {
	case MOTOR_init:
		set_motor(0, 0);
		motor_state = MOTOR_idle;
		break;
	case MOTOR_idle:
		set_motor(0, 0);
		if (motor_target > 0) {
			motor_state = Motor_running_forward;
		}
		if (motor_target < 0) {
			motor_state = Motor_running_backward;
		}
		break;
	case Motor_running_forward:
		if (motor_target == 0) {
			motor_state = Motor_break;
			motor_timer = 8;
			uint32_t tmp = htim3.Instance->CCR1;
			htim3.Instance->CCR1 = htim3.Instance->CCR2;
			htim3.Instance->CCR2 = tmp;
		} else {
			set_motor(motor_target, 1);
		}
		break;
	case Motor_running_backward:
		if (motor_target == 0) {
			motor_state = Motor_break;
			motor_timer = 8;
			uint32_t tmp = htim3.Instance->CCR1;
			htim3.Instance->CCR1 = htim3.Instance->CCR2;
			htim3.Instance->CCR2 = tmp;
		} else {
			set_motor(-motor_target, 0);
		}
		break;
	case Motor_break:
		if (motor_timer) {
			motor_timer--;
		} else {
			motor_state = MOTOR_idle;
		}
		if (motor_target != 0) {
			motor_state = MOTOR_idle;
		}
		break;
	default:
		motor_state = MOTOR_init;
	}
}


/**
 * pwm is from 0 to 2048
 */
static void set_motor(uint32_t pwm, uint32_t direction) {
	//timer 3
	//ch1 is positive pole
	//ch2 is negative pole
	if (direction) {
		htim3.Instance->CCR1 = 0;
		htim3.Instance->CCR2 = pwm;
	} else {
		htim3.Instance->CCR1 = pwm;
		htim3.Instance->CCR2 = 0;
	}
}
