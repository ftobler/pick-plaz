/*
 * uart_handler.cpp
 *
 *  Created on: May 29, 2021
 *      Author: ftobler
 */


#include "uart_handler.h"
#include "main.h"
#include "stm32f4xx_hal.h"
#include "Serial.h"
#include "math.h"
#include "queue.h"

extern UART_HandleTypeDef huart1;
extern Serial serial1;



#define UART_BUF_SIZE 128
uint8_t buf[UART_BUF_SIZE];
int buf_index = 0;

#define QUEUE_LEN 15
Queue<Gcode_command> queue;
Gcode_command queue_data[QUEUE_LEN];


static void process_parse_command();
static void seek_space(int* index);
static float read_num(int* index);
static char to_upper(char c);



void uart_init() {
	//HAL_UART_Receive_IT(&huart1, isr_rec_byte, 5);
	queue.init(queue_data, QUEUE_LEN);
	serial1.init(&huart1);
}


void uart_loop() {
	while (serial1.available()) {
		uint8_t tmp = serial1.read();
		buf[buf_index++] = tmp;
		if (tmp == '\r' || tmp == '\n') {
			//line is finished
			process_parse_command();
			buf_index = 0;
		}
	}
}

int uart_command_available() {
	return queue.getUsedSpace();
}

Gcode_command uart_command_get() {
	return queue.pop();
}



static void process_parse_command() {
	//a command example is: "G1 X40.6 Y30.00\n"
	//two commands can be sent on one line, acting as one: "G1 X40.6 Y30.00;G1 X20.6 Y50.00\n"
	bool do_loop;
	int index = 0;
	do {
		do_loop = false;
		bool end_reached = false;
		Gcode_command cmd;
		cmd.num = -1;
		cmd.valueX = NAN;
		cmd.valueY = NAN;
		cmd.valueZ = NAN;
		cmd.valueE = NAN;
		cmd.valueA = NAN;
		cmd.valueB = NAN;
		cmd.valueC = NAN;
		cmd.valueF = NAN;
		cmd.valueS = NAN;
		cmd.valueT = NAN;
		seek_space(&index);
		cmd.id = to_upper(buf[index++]);
		cmd.num = (int)read_num(&index);
		do {
			seek_space(&index);
			char id = to_upper(buf[index++]);
			switch (id) {
			case ';':
				do_loop = true;
				end_reached = true;
				break;
			case '\r':
			case '\n':
				end_reached = true;
				break;
			case 'X':
				cmd.valueX = read_num(&index);
				break;
			case 'Y':
				cmd.valueY = read_num(&index);
				break;
			case 'Z':
				cmd.valueZ = read_num(&index);
				break;
			case 'E':
				cmd.valueE = read_num(&index);
				break;
			case 'A':
				cmd.valueA = read_num(&index);
				break;
			case 'B':
				cmd.valueB = read_num(&index);
				break;
			case 'C':
				cmd.valueC = read_num(&index);
				break;
			case 'F':
				cmd.valueF = read_num(&index);
				break;
			case 'S':
				cmd.valueS = read_num(&index);
				break;
			case 'T':
				cmd.valueT = read_num(&index);
				break;
			default:
				end_reached = true;
			}
		} while (!end_reached);
		seek_space(&index);
		queue.push(cmd);
	} while(do_loop);
	serial1.writeBuf((uint8_t*)"ok\n", 3);
}


static void seek_space(int* index) {
	int i = *index;
	while (buf[i] == ' ') {
		i++;
	}
	*index = i;
}

static float read_num(int* index) {
	float number = 0;
	float adder_negative = 0.1;
	float factor = 1.0;
	int i = *index;
	bool isPositive = true;
	bool finished = false;
	do {
		char c = buf[i];
		if (c == '.') {
			i++;
			isPositive = false;
		} else if (c >= '0' && c <= '9') {
			int digit = c - '0';
			if (isPositive) {
				number = number * 10 + digit;
			} else {
				number = number + digit * adder_negative;
				adder_negative = adder_negative / 10;
			}
			i++;
		} else if (c == '-') {
			factor = -1.0;
		} else {
			finished = true;
		}
	} while (!finished);
	*index = i;
	return number * factor;
}


static char to_upper(char c) {
	if (c >= 'a' && c <= 'z') {
		c = c - 0x20;
	}
	return c;
}



