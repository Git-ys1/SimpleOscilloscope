#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include "signal.h"

void protocol_init(void);
void protocol_poll(void);
uint8_t protocol_streaming_enabled(void);
void protocol_send_boot(void);
void protocol_send_sample(const signal_sample_t *sample);

#endif
