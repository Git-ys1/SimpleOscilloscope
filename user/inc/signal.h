#ifndef SIGNAL_H
#define SIGNAL_H

#include <stdint.h>

typedef enum {
    SIGNAL_WAVE_SINE = 0,
    SIGNAL_WAVE_SQUARE,
    SIGNAL_WAVE_TRIANGLE,
    SIGNAL_WAVE_SAW
} signal_wave_t;

typedef struct {
    uint32_t sequence;
    uint32_t time_ms;
    uint16_t value_mv;
    signal_wave_t wave;
    uint16_t frequency_hz;
    uint16_t amplitude_mv;
    uint16_t offset_mv;
    uint16_t sample_rate_hz;
} signal_sample_t;

void signal_init(void);
signal_sample_t signal_next_sample(uint32_t time_ms);

void signal_set_wave(signal_wave_t wave);
uint8_t signal_set_wave_name(const char *name);
void signal_set_frequency(uint16_t hz);
void signal_set_amplitude(uint16_t mv);
void signal_set_offset(uint16_t mv);
void signal_set_sample_rate(uint16_t hz);

signal_wave_t signal_get_wave(void);
const char *signal_wave_name(signal_wave_t wave);
uint16_t signal_get_frequency(void);
uint16_t signal_get_amplitude(void);
uint16_t signal_get_offset(void);
uint16_t signal_get_sample_rate(void);

#endif
