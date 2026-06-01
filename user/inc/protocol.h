#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include "signal.h"

void protocol_init(void);
void protocol_poll(void);
uint8_t protocol_streaming_enabled(void);
uint8_t protocol_binary_enabled(void);
void protocol_send_boot(void);
void protocol_send_sample(const signal_sample_t *sample);
void protocol_send_binary_block(uint32_t sequence, uint16_t sample_rate_hz, const uint16_t *values_mv, uint16_t point_count);

#endif
