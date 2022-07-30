/*
 * serial_c.c
 *
 *  Created on: Jul 30, 2022
 *      Author: ftobler
 */

#include "serial_c.h"
#include "Serial.h"



extern Serial serial1;


void serial_isr_legacy_c() {
	serial1.ISR();
}
