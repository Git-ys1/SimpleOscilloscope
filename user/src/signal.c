#include "signal.h"
#include "osc_config.h"
#include <string.h>

typedef struct {
    signal_wave_t wave;
    uint16_t frequency_hz;
    uint16_t amplitude_mv;
    uint16_t offset_mv;
    uint16_t sample_rate_hz;
    uint32_t phase;
    uint32_t sequence;
} signal_state_t;

static signal_state_t g_signal;

static const int16_t k_sine_table[64] = {
      0,   98,  195,  290,  383,  471,  556,  634,
    707,  773,  831,  882,  924,  957,  981,  995,
   1000,  995,  981,  957,  924,  882,  831,  773,
    707,  634,  556,  471,  383,  290,  195,   98,
      0,  -98, -195, -290, -383, -471, -556, -634,
   -707, -773, -831, -882, -924, -957, -981, -995,
  -1000, -995, -981, -957, -924, -882, -831, -773,
   -707, -634, -556, -471, -383, -290, -195,  -98
};

static uint16_t clamp_u16(uint16_t value, uint16_t min_value, uint16_t max_value)
{
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}

static uint16_t clamp_mv(int32_t value)
{
    if (value < 0) {
        return 0U;
    }
    if (value > (int32_t)OSC_MAX_MV) {
        return OSC_MAX_MV;
    }
    return (uint16_t)value;
}

static int16_t waveform_value(signal_wave_t wave, uint16_t phase)
{
    int32_t value;

    switch (wave) {
    case SIGNAL_WAVE_SQUARE:
        return (phase < 32768U) ? 1000 : -1000;
    case SIGNAL_WAVE_TRIANGLE:
        if (phase < 16384U) {
            value = ((int32_t)phase * 1000L) / 16384L;
        } else if (phase < 49152U) {
            value = 1000L - (((int32_t)phase - 16384L) * 2000L) / 32768L;
        } else {
            value = -1000L + (((int32_t)phase - 49152L) * 1000L) / 16384L;
        }
        return (int16_t)value;
    case SIGNAL_WAVE_SAW:
        value = -1000L + ((int32_t)phase * 2000L) / 65535L;
        return (int16_t)value;
    case SIGNAL_WAVE_SINE:
    default:
    {
        uint16_t index = (uint16_t)((phase >> 10) & 0x3FU);
        uint16_t next_index = (uint16_t)((index + 1U) & 0x3FU);
        int32_t current = k_sine_table[index];
        int32_t next = k_sine_table[next_index];
        int32_t fraction = (int32_t)(phase & 0x03FFU);
        return (int16_t)(current + (((next - current) * fraction) / 1024L));
    }
    }
}

void signal_init(void)
{
    g_signal.wave = SIGNAL_WAVE_SINE;
    g_signal.frequency_hz = OSC_DEFAULT_FREQ_HZ;
    g_signal.amplitude_mv = OSC_DEFAULT_AMP_MV;
    g_signal.offset_mv = OSC_DEFAULT_OFFSET_MV;
    g_signal.sample_rate_hz = OSC_DEFAULT_RATE_HZ;
    g_signal.phase = 0U;
    g_signal.sequence = 0U;
}

signal_sample_t signal_next_sample(uint32_t time_ms)
{
    signal_sample_t sample;
    uint32_t step;
    int16_t normalized;
    int32_t millivolts;

    step = ((uint32_t)g_signal.frequency_hz * 65536U) / g_signal.sample_rate_hz;
    g_signal.phase = (g_signal.phase + step) & 0xFFFFU;

    normalized = waveform_value(g_signal.wave, (uint16_t)g_signal.phase);
    millivolts = (int32_t)g_signal.offset_mv +
                 (((int32_t)g_signal.amplitude_mv * (int32_t)normalized) / 1000L);

    g_signal.sequence++;

    sample.sequence = g_signal.sequence;
    sample.time_ms = time_ms;
    sample.value_mv = clamp_mv(millivolts);
    sample.wave = g_signal.wave;
    sample.frequency_hz = g_signal.frequency_hz;
    sample.amplitude_mv = g_signal.amplitude_mv;
    sample.offset_mv = g_signal.offset_mv;
    sample.sample_rate_hz = g_signal.sample_rate_hz;
    return sample;
}

void signal_set_wave(signal_wave_t wave)
{
    if (wave <= SIGNAL_WAVE_SAW) {
        g_signal.wave = wave;
    }
}

uint8_t signal_set_wave_name(const char *name)
{
    if (strcmp(name, "SINE") == 0) {
        signal_set_wave(SIGNAL_WAVE_SINE);
    } else if (strcmp(name, "SQUARE") == 0) {
        signal_set_wave(SIGNAL_WAVE_SQUARE);
    } else if (strcmp(name, "TRI") == 0 || strcmp(name, "TRIANGLE") == 0) {
        signal_set_wave(SIGNAL_WAVE_TRIANGLE);
    } else if (strcmp(name, "SAW") == 0) {
        signal_set_wave(SIGNAL_WAVE_SAW);
    } else {
        return 0U;
    }
    return 1U;
}

void signal_set_frequency(uint16_t hz)
{
    g_signal.frequency_hz = clamp_u16(hz, OSC_MIN_FREQ_HZ, OSC_MAX_FREQ_HZ);
}

void signal_set_amplitude(uint16_t mv)
{
    g_signal.amplitude_mv = clamp_u16(mv, 0U, OSC_MAX_MV);
}

void signal_set_offset(uint16_t mv)
{
    g_signal.offset_mv = clamp_u16(mv, 0U, OSC_MAX_MV);
}

void signal_set_sample_rate(uint16_t hz)
{
    g_signal.sample_rate_hz = clamp_u16(hz, OSC_MIN_RATE_HZ, OSC_MAX_RATE_HZ);
}

signal_wave_t signal_get_wave(void)
{
    return g_signal.wave;
}

const char *signal_wave_name(signal_wave_t wave)
{
    switch (wave) {
    case SIGNAL_WAVE_SQUARE:
        return "SQUARE";
    case SIGNAL_WAVE_TRIANGLE:
        return "TRI";
    case SIGNAL_WAVE_SAW:
        return "SAW";
    case SIGNAL_WAVE_SINE:
    default:
        return "SINE";
    }
}

uint16_t signal_get_frequency(void)
{
    return g_signal.frequency_hz;
}

uint16_t signal_get_amplitude(void)
{
    return g_signal.amplitude_mv;
}

uint16_t signal_get_offset(void)
{
    return g_signal.offset_mv;
}

uint16_t signal_get_sample_rate(void)
{
    return g_signal.sample_rate_hz;
}
