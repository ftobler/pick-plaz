/*
 * Serial.c
 *
 *  Created on: Oct 17, 2020
 *      Author: Florin (Nicolas)
 */

#include "Serial.h"
#include "stm32f4xx.h"
#include "stm32f4xx_hal_def.h"
#include "gpio.h"

//public functions

static void Serial_enableTx(Serial* _this);
static void initBuf(Buffer* b);
static inline uint8_t Buffer_getByte(Buffer* b);
static inline uint32_t Buffer_getAvailable(Buffer* b);
static inline void Buffer_setByte(Buffer* b, uint8_t data);


Serial serial1;

void ISR_Serial(Serial* _this) {

    UART_HandleTypeDef *huart = _this->handler;

    uint32_t isrflags   = READ_REG(huart->Instance->SR);
    uint32_t cr1its     = READ_REG(huart->Instance->CR1);

	uint32_t errorflags = (isrflags & (uint32_t)(USART_SR_PE | USART_SR_FE | USART_SR_ORE | USART_SR_NE | USART_SR_IDLE));
	if (errorflags == 0 || 1) {
		//handle normal
		if (((isrflags & USART_SR_RXNE) != 0U) && ((cr1its & USART_CR1_RXNEIE) != 0U)) {
			uint8_t data = (uint8_t)(huart->Instance->DR & (uint8_t)0x00FF);
			Buffer_setByte(&_this->in, data);
		}
	} else {
		//handle the errors (receive error)
	}

	if (((isrflags & USART_SR_TXE) != 0U) && ((cr1its & USART_CR1_TXEIE) != 0U)) {
		//sent something
		uint8_t outAvail = Buffer_getAvailable(&_this->out);
		if (outAvail == 0) {
			  /* Disable the UART Transmit Complete Interrupt */
			  __HAL_UART_DISABLE_IT(huart, UART_IT_TXE);

			  /* Enable the UART Transmit Complete Interrupt */
			  __HAL_UART_ENABLE_IT(huart, UART_IT_TC);
		} else {
			huart->Instance->DR = Buffer_getByte(&_this->out);
		}
    }

	if (((isrflags & USART_SR_TC) != 0U) && ((cr1its & USART_CR1_TCIE) != 0U)) {
		//transmission ended

		/* Disable the UART Transmit Complete Interrupt */
		__HAL_UART_DISABLE_IT(huart, UART_IT_TC);

		_this->txnComplete = 1;

		if (_this->flow) {
			gpio_ResetPin(_this->flowPort, _this->flowPin);
		}
	}
	__HAL_UART_DISABLE_IT(huart, USART_CR1_IDLEIE);
	__HAL_UART_DISABLE_IT(huart, USART_CR1_PEIE);
}



void Serial_init(Serial* _this, UART_HandleTypeDef* handler) {
	_this->handler = handler;
	initBuf(&_this->in);
	initBuf(&_this->out);
	_this->flow = 0;

	UART_HandleTypeDef *huart = handler;

    huart->ErrorCode = HAL_UART_ERROR_NONE;
    huart->RxState = HAL_UART_STATE_BUSY_RX;

    /* Enable the UART Parity Error interrupt and Data Register Not Empty interrupt */
    SET_BIT(huart->Instance->CR1, USART_CR1_PEIE | USART_CR1_RXNEIE);
}


void Serial_initFlow(Serial* _this, GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin) {
	_this->flow = 1;
	_this->flowPort = GPIOx;
	_this->flowPin = GPIO_Pin;
}

uint16_t Serial_available(Serial* _this){
	return Buffer_getAvailable(&_this->in);
}

void Serial_flushRX(Serial* _this){
	initBuf(&_this->in);
}

void Serial_flushTX(Serial* _this){
	initBuf(&_this->out);
}

void Serial_print(Serial* _this, const char* str){
	const uint8_t* ptr = (uint8_t*)str;
	while (*ptr != '\0'){
		Buffer_setByte(&_this->out, *ptr);
		ptr++;
	}
	Serial_enableTx(_this);
}

/**
 * unguarded about overflow!
 * use Serial_available!
 */
uint8_t Serial_read(Serial* _this) {
	return Buffer_getByte(&_this->in);
}

uint16_t Serial_readBuf(Serial* _this, uint8_t* buf, uint16_t len) {
	uint16_t count = 0;
	while (Buffer_getAvailable(&_this->in) && (count < len)) {
		buf[count] = Buffer_getByte(&_this->in);
		count++;
	}
	return count;

//	uint16_t max = Buffer_getAvailable(&_this->in);
//	if (max > len) {
//		len = max;
//	}
//	for (uint16_t i = 0; i < len; i++) {
//		buf[i] = Buffer_getByte(&_this->in);
//	}
//	return len;
}


void Serial_writeBuf(Serial* _this, const uint8_t* buf, uint16_t len) {
	for (uint16_t i = 0; i < len; i++) {
		Buffer_setByte(&_this->out, buf[i]);
	}
	Serial_enableTx(_this);
}
void Serial_write(Serial* _this, const uint8_t data) {
	Buffer_setByte(&_this->out, data);
	Serial_enableTx(_this);
}


static void Serial_enableTx(Serial* _this) {
	if (_this->flow) {
		gpio_SetPin(_this->flowPort, _this->flowPin);
	}
	UART_HandleTypeDef *huart = _this->handler;
//	if (huart->gState == HAL_UART_STATE_READY) {
//		huart->ErrorCode = HAL_UART_ERROR_NONE;
//		huart->gState = HAL_UART_STATE_BUSY_TX;
//		/* Enable the UART Transmit data register empty Interrupt */
//		    __HAL_UART_ENABLE_IT(huart, UART_IT_TXE);
//	} else {
//		//huart->gState = HAL_UART_STATE_BUSY_TX;
//	}
	__HAL_UART_ENABLE_IT(huart, UART_IT_TXE);
	_this->txnComplete = 0;
}


static void initBuf(Buffer* b) {
	b->head = 0;
	b->tail = 0;
}
static inline uint8_t Buffer_getByte(Buffer* b) {
	uint32_t tail = b->tail;
	uint8_t data = b->buf[tail];
	b->tail = (tail + 1) % BUFFER_LEN;
	return data;
}
static inline uint32_t Buffer_getAvailable(Buffer* b) {
	return (b->head - b->tail) % BUFFER_LEN;
}
static inline void Buffer_setByte(Buffer* b, uint8_t data) {
	uint32_t head = b->head;
	b->buf[head] = data;
	b->head = (head + 1) % BUFFER_LEN;
}
