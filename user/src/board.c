#include "board.h"
#include "osc_config.h"
#include "stm32f10x.h"

static volatile uint32_t g_ms_ticks;
static uint8_t g_led_on;

__weak void board_sample_timer_tick(void)
{
}

void SysTick_Handler(void)
{
    g_ms_ticks++;
}

void TIM2_IRQHandler(void)
{
    if ((TIM2->SR & TIM_SR_UIF) != 0U) {
        TIM2->SR = (uint16_t)~TIM_SR_UIF;
        board_sample_timer_tick();
    }
}

uint32_t board_millis(void)
{
    return g_ms_ticks;
}

static void gpio_config_pin(GPIO_TypeDef *port, uint8_t pin, uint32_t mode_cnf)
{
    volatile uint32_t *reg;
    uint32_t shift;

    if (pin < 8U) {
        reg = &port->CRL;
        shift = (uint32_t)pin * 4U;
    } else {
        reg = &port->CRH;
        shift = ((uint32_t)pin - 8U) * 4U;
    }

    *reg = (*reg & ~(0xFU << shift)) | ((mode_cnf & 0xFU) << shift);
}

static void board_gpio_init(void)
{
    RCC->APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPAEN | RCC_APB2ENR_IOPCEN;

    gpio_config_pin(GPIOA, 8U, 0x0BU);   /* PA8: TIM1_CH1 PWM output */
    gpio_config_pin(GPIOA, 9U, 0x0BU);   /* PA9: USART1 TX */
    gpio_config_pin(GPIOA, 10U, 0x04U);  /* PA10: USART1 RX floating input */
    gpio_config_pin(GPIOC, 13U, 0x02U);  /* PC13: onboard LED output */

    board_led_set(0U);
}

static void board_pwm_init(void)
{
    RCC->APB2ENR |= RCC_APB2ENR_TIM1EN;

    TIM1->PSC = (uint16_t)((SystemCoreClock / 1000000U) - 1U);
    TIM1->ARR = 999U;
    TIM1->CCR1 = 500U;
    TIM1->CCMR1 = (6U << 4) | TIM_CCMR1_OC1PE;
    TIM1->CCER = TIM_CCER_CC1E;
    TIM1->BDTR = TIM_BDTR_MOE;
    TIM1->CR1 = TIM_CR1_ARPE | TIM_CR1_CEN;
    TIM1->EGR = TIM_EGR_UG;
}

static void board_sample_timer_init(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM2EN;
    TIM2->PSC = (uint16_t)((SystemCoreClock / 1000000U) - 1U);
    TIM2->DIER = TIM_DIER_UIE;
    TIM2->CR1 = TIM_CR1_ARPE | TIM_CR1_CEN;
    NVIC_EnableIRQ(TIM2_IRQn);
    board_sample_timer_set_rate(OSC_DEFAULT_RATE_HZ);
}

void board_init(void)
{
    SystemCoreClockUpdate();
    board_gpio_init();
    board_pwm_init();
    SysTick_Config(SystemCoreClock / 1000U);
    board_sample_timer_init();
}

void board_led_set(uint8_t on)
{
    g_led_on = on ? 1U : 0U;
    if (g_led_on) {
        GPIOC->BRR = GPIO_BRR_BR13;
    } else {
        GPIOC->BSRR = GPIO_BSRR_BS13;
    }
}

void board_led_toggle(void)
{
    board_led_set((uint8_t)!g_led_on);
}

void board_pwm_set_mv(uint16_t millivolts)
{
    uint32_t duty;

    if (millivolts > OSC_MAX_MV) {
        millivolts = OSC_MAX_MV;
    }

    duty = ((uint32_t)millivolts * 1000U) / OSC_MAX_MV;
    if (duty > 999U) {
        duty = 999U;
    }

    TIM1->CCR1 = (uint16_t)duty;
}

void board_sample_timer_set_rate(uint16_t sample_rate_hz)
{
    uint32_t arr;

    if (sample_rate_hz < OSC_MIN_RATE_HZ) {
        sample_rate_hz = OSC_MIN_RATE_HZ;
    }
    if (sample_rate_hz > OSC_MAX_RATE_HZ) {
        sample_rate_hz = OSC_MAX_RATE_HZ;
    }

    arr = (1000000UL / (uint32_t)sample_rate_hz);
    if (arr == 0UL) {
        arr = 1UL;
    }
    TIM2->ARR = (uint16_t)(arr - 1UL);
    TIM2->EGR = TIM_EGR_UG;
}
