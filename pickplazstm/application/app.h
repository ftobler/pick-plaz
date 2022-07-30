/*
 * app.cpp
 *
 *  Created on: May 29, 2021
 *      Author: ftobler
 */


#ifndef APP_H_
#define APP_H_

#ifdef __cplusplus
extern "C" {
#endif

void setup();

void timer_isr();

void systick_isr();

void loop();


#ifdef __cplusplus
}
#endif


#endif
