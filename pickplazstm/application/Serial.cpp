/*
 * Serial.c
 *
 *  Created on: Oct 17, 2020
 *      Author: Florin
 */

#include "Serial.h"
#include "stm32f4xx.h"
#include "stm32f4xx_hal_def.h"
#include "gpio.h"


Serial serial1;


Buffer::Buffer() {
	init();
}

void Buffer::init() {
	head = 0;
	tail = 0;
}

inline uint8_t Buffer::getByte() {
	uint32_t _tail = tail;
	uint8_t data = buf[_tail];
	tail = (_tail + 1) % BUFFER_LEN;
	return data;
}


inline uint32_t Buffer::getAvailable() {
	return (head - tail) % BUFFER_LEN;
}


inline void Buffer::setByte(uint8_t data) {
	uint32_t _head = head;
	buf[_head] = data;
	head = (_head + 1) % BUFFER_LEN;
}


void Serial::ISR() {

    //UART_HandleTypeDef *huart = _this->handler;

    uint32_t isrflags   = READ_REG(huart->Instance->SR);
    uint32_t cr1its     = READ_REG(huart->Instance->CR1);

	uint32_t errorflags = (isrflags & (uint32_t)(USART_SR_PE | USART_SR_FE | USART_SR_ORE | USART_SR_NE | USART_SR_IDLE));
	if (errorflags == 0 || 1) {
		//handle normal
		if (((isrflags & USART_SR_RXNE) != 0U) && ((cr1its & USART_CR1_RXNEIE) != 0U)) {
			uint8_t data = (uint8_t)(huart->Instance->DR & (uint8_t)0x00FF);
			in.setByte(data);
		}
	} else {
		//handle the errors (receive error)
	}

	if (((isrflags & USART_SR_TXE) != 0U) && ((cr1its & USART_CR1_TXEIE) != 0U)) {
		//sent something
		uint8_t outAvail = out.getAvailable();
		if (outAvail == 0) {
			  /* Disable the UART Transmit Complete Interrupt */
			  __HAL_UART_DISABLE_IT(huart, UART_IT_TXE);

			  /* Enable the UART Transmit Complete Interrupt */
			  __HAL_UART_ENABLE_IT(huart, UART_IT_TC);
		} else {
			huart->Instance->DR = out.getByte();
		}
    }

	if (((isrflags & USART_SR_TC) != 0U) && ((cr1its & USART_CR1_TCIE) != 0U)) {
		//transmission ended

		/* Disable the UART Transmit Complete Interrupt */
		__HAL_UART_DISABLE_IT(huart, UART_IT_TC);

		txnComplete = 1;

		if (flow) {
			gpio_ResetPin(flowPort, flowPin);
		}
	}
	__HAL_UART_DISABLE_IT(huart, USART_CR1_IDLEIE);
	__HAL_UART_DISABLE_IT(huart, USART_CR1_PEIE);
}


void Serial::init(UART_HandleTypeDef* handler) {
	huart = handler;
	flow = 0;

	UART_HandleTypeDef *huart = handler;

    huart->ErrorCode = HAL_UART_ERROR_NONE;
    huart->RxState = HAL_UART_STATE_BUSY_RX;

    /* Enable the UART Parity Error interrupt and Data Register Not Empty interrupt */
    SET_BIT(huart->Instance->CR1, USART_CR1_PEIE | USART_CR1_RXNEIE);
}


void Serial::initFlow(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin) {
	flow = 1;
	flowPort = GPIOx;
	flowPin = GPIO_Pin;
}


uint16_t Serial::available(){
	return in.getAvailable();
}


void Serial::flushRX(){
	in.init();
}


void Serial::flushTX(){
	out.init();
}


void Serial::print(const char* str){
	const uint8_t* ptr = (uint8_t*)str;
	while (*ptr != '\0'){
		out.setByte(*ptr);
		ptr++;
	}
	enableTx();
}


/**
 * unguarded about overflow!
 * use Serial_available!
 */
uint8_t Serial::read() {
	return in.getByte();
}


uint16_t Serial::readBuf(uint8_t* buf, uint16_t len) {
	uint16_t count = 0;
	while (in.getAvailable() && (count < len)) {
		buf[count] = in.getByte();
		count++;
	}
	return count;
}


void Serial::writeBuf(const uint8_t* buf, uint16_t len) {
	for (uint16_t i = 0; i < len; i++) {
		out.setByte(buf[i]);
	}
	enableTx();
}


void Serial::write(const uint8_t data) {
	out.setByte(data);
	enableTx();
}


void Serial::enableTx() {
	if (flow) {
		gpio_SetPin(flowPort, flowPin);
	}
	__HAL_UART_ENABLE_IT(huart, UART_IT_TXE);
	txnComplete = 0;
}



