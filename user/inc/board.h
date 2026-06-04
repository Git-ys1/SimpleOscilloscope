#ifndef BOARD_H
#define BOARD_H

#include <stdint.h>

void board_init(void);
uint32_t board_millis(void);
void board_led_set(uint8_t on);
void board_led_toggle(void);
void board_pwm_set_mv(uint16_t millivolts);
void board_sample_timer_set_rate(uint16_t sample_rate_hz);

#endif
