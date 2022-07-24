/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2022 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f0xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define FEED_Pin GPIO_PIN_3
#define FEED_GPIO_Port GPIOA
#define OPTO_INTERRUPT_Pin GPIO_PIN_4
#define OPTO_INTERRUPT_GPIO_Port GPIOA
#define OPTO_LED_Pin GPIO_PIN_5
#define OPTO_LED_GPIO_Port GPIOA
#define MOT_NEG_Pin GPIO_PIN_6
#define MOT_NEG_GPIO_Port GPIOA
#define MOT_POS_Pin GPIO_PIN_7
#define MOT_POS_GPIO_Port GPIOA
#define SW_FORWARD_Pin GPIO_PIN_2
#define SW_FORWARD_GPIO_Port GPIOB
#define SW_BACKWARD_Pin GPIO_PIN_10
#define SW_BACKWARD_GPIO_Port GPIOB
#define LED3_Pin GPIO_PIN_8
#define LED3_GPIO_Port GPIOA
#define LED2_Pin GPIO_PIN_9
#define LED2_GPIO_Port GPIOA
#define LED1_Pin GPIO_PIN_10
#define LED1_GPIO_Port GPIOA
#define LED0_Pin GPIO_PIN_11
#define LED0_GPIO_Port GPIOA
#define TP1_Pin GPIO_PIN_3
#define TP1_GPIO_Port GPIOB
#define TP2_Pin GPIO_PIN_4
#define TP2_GPIO_Port GPIOB
#define TP3_Pin GPIO_PIN_5
#define TP3_GPIO_Port GPIOB
#define TP4_Pin GPIO_PIN_6
#define TP4_GPIO_Port GPIOB
#define TP5_Pin GPIO_PIN_7
#define TP5_GPIO_Port GPIOB
/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
