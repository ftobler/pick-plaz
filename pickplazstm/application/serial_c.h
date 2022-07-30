/*
 * serial_c.h
 *
 *  Created on: Jul 30, 2022
 *      Author: ftobler
 */


#ifndef SERIAL_C_H_
#define SERIAL_C_H_


#ifdef __cplusplus
extern "C" {
#endif


/**
 * calls the interrupt function on the C++ class from a C compatible interface.
 */
void serial_isr_legacy_c();


#ifdef __cplusplus
}
#endif


#endif /* SERIAL_C_H_ */
