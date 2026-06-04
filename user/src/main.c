#include "board.h"
#include "osc_config.h"
#include "protocol.h"
#include "signal.h"
#include "uart.h"
#include <stdint.h>

#define SAMPLE_QUEUE_CAPACITY (OSC_BINARY_BLOCK_POINTS * 4U)

static volatile uint16_t g_sample_head;
static volatile uint16_t g_sample_tail;
static volatile uint16_t g_sample_count;
static signal_sample_t g_sample_queue[SAMPLE_QUEUE_CAPACITY];

static uint8_t time_due(uint32_t now, uint32_t deadline)
{
    return ((int32_t)(now - deadline) >= 0) ? 1U : 0U;
}

static void sample_queue_clear(void)
{
    __disable_irq();
    g_sample_head = 0U;
    g_sample_tail = 0U;
    g_sample_count = 0U;
    __enable_irq();
}

static uint8_t sample_queue_pop(signal_sample_t *sample)
{
    uint8_t ok = 0U;

    __disable_irq();
    if (g_sample_count > 0U) {
        *sample = g_sample_queue[g_sample_tail];
        g_sample_tail = (uint16_t)((g_sample_tail + 1U) % SAMPLE_QUEUE_CAPACITY);
        g_sample_count--;
        ok = 1U;
    }
    __enable_irq();
    return ok;
}

void board_sample_timer_tick(void)
{
    signal_sample_t sample;

    if (!protocol_streaming_enabled()) {
        return;
    }

    sample = signal_next_sample(board_millis());
    board_pwm_set_mv(sample.value_mv);
    if (g_sample_count >= SAMPLE_QUEUE_CAPACITY) {
        return;
    }

    g_sample_queue[g_sample_head] = sample;
    g_sample_head = (uint16_t)((g_sample_head + 1U) % SAMPLE_QUEUE_CAPACITY);
    g_sample_count++;
}

int main(void)
{
    uint32_t last_led_ms;
    uint32_t now;
    signal_sample_t sample;
    uint16_t binary_values[OSC_BINARY_BLOCK_POINTS];
    uint16_t binary_count;
    uint16_t drained;
    uint32_t binary_sequence;
    uint32_t binary_first_ms;

    board_init();
    uart_init(OSC_UART_BAUD);
    signal_init();
    protocol_init();
    protocol_send_boot();
    sample_queue_clear();

    now = board_millis();
    last_led_ms = now;
    binary_count = 0U;
    binary_sequence = 0U;
    binary_first_ms = now;

    while (1) {
        protocol_poll();
        now = board_millis();

        if (!protocol_streaming_enabled()) {
            sample_queue_clear();
            binary_count = 0U;
        }

        drained = 0U;
        while (drained < SAMPLE_QUEUE_CAPACITY && sample_queue_pop(&sample)) {
            drained++;
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
        }

        if (time_due(now, last_led_ms + 500U)) {
            board_led_toggle();
            last_led_ms = now;
        }
    }
}
