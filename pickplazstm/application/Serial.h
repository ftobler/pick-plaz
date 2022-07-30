/*
 * Serialh
 *
 *  Created on: 17.10.2020
 *      Author: Florin
 */


#ifndef SERIAL_H_
#define SERIAL_H_


#include "main.h"
#include "stm32f4xx.h"


#define BUFFER_LEN 256


class Buffer {
private:
	uint32_t head;
	uint32_t tail;
	uint8_t buf[BUFFER_LEN];
public:
	Buffer();
	inline uint8_t getByte();
	void init();
	inline uint32_t getAvailable();
	inline void setByte(uint8_t data);
};


class Serial {
private:
	UART_HandleTypeDef* huart;
	Buffer out;
	Buffer in;
	uint8_t txnComplete;
	uint8_t flow;
	GPIO_TypeDef* flowPort;
	uint16_t flowPin;
	void enableTx();
public:
	void ISR();
	void init(UART_HandleTypeDef* handler);
	void initFlow(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin);
	uint16_t available();
	void flushRX();
	void flushTX();
	void print(const char* str);
	uint8_t read();
	uint16_t readBuf(uint8_t* buf, uint16_t len);
	void writeBuf(const uint8_t* buf, uint16_t len);
	void write(const uint8_t data);
};


#endif /* SERIAL_H_ */
