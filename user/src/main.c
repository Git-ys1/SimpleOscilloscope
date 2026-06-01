#include "board.h"
#include "osc_config.h"
#include "protocol.h"
#include "signal.h"
#include "uart.h"
#include <stdint.h>

static uint8_t time_due(uint32_t now, uint32_t deadline)
{
    return ((int32_t)(now - deadline) >= 0) ? 1U : 0U;
}

int main(void)
{
    uint32_t next_sample_ms;
    uint32_t last_led_ms;
    uint32_t now;
    signal_sample_t sample;
    uint16_t binary_values[OSC_BINARY_BLOCK_POINTS];
    uint16_t binary_count;
    uint32_t binary_sequence;
    uint32_t binary_first_ms;

    board_init();
    uart_init(OSC_UART_BAUD);
    signal_init();
    protocol_init();
    protocol_send_boot();

    now = board_millis();
    next_sample_ms = now;
    last_led_ms = now;
    binary_count = 0U;
    binary_sequence = 0U;
    binary_first_ms = now;

    while (1) {
        protocol_poll();
        now = board_millis();

        if (protocol_streaming_enabled() && time_due(now, next_sample_ms)) {
            sample = signal_next_sample(now);
            board_pwm_set_mv(sample.value_mv);
            if (protocol_binary_enabled()) {
                if (binary_count == 0U) {
                    binary_sequence = sample.sequence;
                    binary_first_ms = now;
                }
                binary_values[binary_count++] = sample.value_mv;
                if (binary_count >= OSC_BINARY_BLOCK_POINTS || time_due(now, binary_first_ms + 100U)) {
                    protocol_send_binary_block(binary_sequence, sample.sample_rate_hz, binary_values, binary_count);
                    binary_count = 0U;
                }
            } else {
                binary_count = 0U;
                protocol_send_sample(&sample);
            }
            next_sample_ms += signal_get_interval_ms();
            if (time_due(now, next_sample_ms + signal_get_interval_ms())) {
                next_sample_ms = now + signal_get_interval_ms();
            }
        }

        if (time_due(now, last_led_ms + 500U)) {
            board_led_toggle();
            last_led_ms = now;
        }
    }
}
