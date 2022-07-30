/*
 * serial_c.c
 *
 *  Created on: Jul 30, 2022
 *      Author: ftobler
 */


#include "serial_c.h"
#include "Serial.h"


extern Serial serial1;


/**
 * calls the interrupt function on the C++ class from a C compatible interface.
 */
void serial_isr_legacy_c() {
	serial1.ISR();
}
