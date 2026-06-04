#include "protocol.h"
#include "board.h"
#include "osc_config.h"
#include "uart.h"
#include <stdlib.h>
#include <string.h>

#define RX_LINE_MAX 96U
#define BINARY_SYNC0 0xA5U
#define BINARY_SYNC1 0x5AU
#define BINARY_VERSION 1U
#define BINARY_TYPE_DATA 1U
#define BINARY_HEADER_LEN 15U
#define BINARY_CRC_LEN 2U

static char g_rx_line[RX_LINE_MAX];
static uint8_t g_rx_len;
static volatile uint8_t g_streaming;
static volatile uint8_t g_binary_enabled;

static uint8_t starts_with(const char *text, const char *prefix)
{
    return strncmp(text, prefix, strlen(prefix)) == 0 ? 1U : 0U;
}

static void write_u32(uint32_t value)
{
    char buf[11];
    uint8_t i = 0U;

    if (value == 0U) {
        uart_write_char('0');
        return;
    }

    while (value > 0U && i < sizeof(buf)) {
        buf[i++] = (char)('0' + (value % 10U));
        value /= 10U;
    }

    while (i > 0U) {
        uart_write_char(buf[--i]);
    }
}

static void send_ok(const char *key)
{
    uart_write("OK,");
    uart_write(key);
    uart_write("\r\n");
}

static void send_err(const char *reason)
{
    uart_write("ERR,");
    uart_write(reason);
    uart_write("\r\n");
}

static void send_status(void)
{
    uart_write("STATUS,");
    uart_write(signal_wave_name(signal_get_wave()));
    uart_write(",");
    write_u32(signal_get_frequency());
    uart_write(",");
    write_u32(signal_get_amplitude());
    uart_write(",");
    write_u32(signal_get_offset());
    uart_write(",");
    write_u32(signal_get_sample_rate());
    uart_write(",");
    uart_write(g_streaming ? "RUN" : "STOP");
    uart_write("\r\n");
}

static void send_format(void)
{
    uart_write("FORMAT,");
    uart_write(g_binary_enabled ? "BINARY" : "ASCII");
    uart_write("\r\n");
}

static void send_capabilities(void)
{
    uart_write("CAP,RATE_MIN=");
    write_u32(OSC_MIN_RATE_HZ);
    uart_write(",RATE_MAX=");
    write_u32(OSC_MAX_RATE_HZ);
    uart_write(",FREQ_MIN=");
    write_u32(OSC_MIN_FREQ_HZ);
    uart_write(",FREQ_MAX=");
    write_u32(OSC_MAX_FREQ_HZ);
    uart_write(",BAUD=");
    write_u32(OSC_UART_BAUD);
    uart_write(",BLOCK=");
    write_u32(OSC_BINARY_BLOCK_POINTS);
    uart_write("\r\n");
}

static uint16_t crc16_ccitt(const uint8_t *data, uint16_t len)
{
    uint16_t crc = 0xFFFFU;
    uint16_t i;
    uint8_t bit;

    for (i = 0U; i < len; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (bit = 0U; bit < 8U; bit++) {
            if ((crc & 0x8000U) != 0U) {
                crc = (uint16_t)((crc << 1) ^ 0x1021U);
            } else {
                crc = (uint16_t)(crc << 1);
            }
        }
    }
    return crc;
}

static void put_u16_le(uint8_t *frame, uint16_t *index, uint16_t value)
{
    frame[(*index)++] = (uint8_t)(value & 0xFFU);
    frame[(*index)++] = (uint8_t)((value >> 8) & 0xFFU);
}

static void put_u32_le(uint8_t *frame, uint16_t *index, uint32_t value)
{
    frame[(*index)++] = (uint8_t)(value & 0xFFU);
    frame[(*index)++] = (uint8_t)((value >> 8) & 0xFFU);
    frame[(*index)++] = (uint8_t)((value >> 16) & 0xFFU);
    frame[(*index)++] = (uint8_t)((value >> 24) & 0xFFU);
}

static uint16_t mv_to_adc(uint16_t value_mv)
{
    uint32_t adc = ((uint32_t)value_mv * 4095U) / OSC_MAX_MV;
    return (uint16_t)adc;
}

static void handle_set(const char *line)
{
    uint16_t value;
    const char *arg;

    if (starts_with(line, "SET WAVE ")) {
        arg = line + 9;
        if (signal_set_wave_name(arg)) {
            send_ok("WAVE");
        } else {
            send_err("bad_wave");
        }
    } else if (starts_with(line, "SET FREQ ")) {
        value = (uint16_t)atoi(line + 9);
        signal_set_frequency(value);
        send_ok("FREQ");
    } else if (starts_with(line, "SET AMP ")) {
        value = (uint16_t)atoi(line + 8);
        signal_set_amplitude(value);
        send_ok("AMP");
    } else if (starts_with(line, "SET OFFSET ")) {
        value = (uint16_t)atoi(line + 11);
        signal_set_offset(value);
        send_ok("OFFSET");
    } else if (starts_with(line, "SET RATE ")) {
        value = (uint16_t)atoi(line + 9);
        signal_set_sample_rate(value);
        board_sample_timer_set_rate(signal_get_sample_rate());
        send_ok("RATE");
    } else if (strcmp(line, "SET FORMAT ASCII") == 0) {
        g_binary_enabled = 0U;
        send_ok("FORMAT");
        send_format();
    } else if (strcmp(line, "SET FORMAT BINARY") == 0) {
        g_binary_enabled = 1U;
        send_ok("FORMAT");
        send_format();
    } else {
        send_err("bad_set");
    }
}

static void handle_line(char *line)
{
    if (strcmp(line, "PING") == 0) {
        uart_write("PONG,");
        uart_write(OSC_FW_NAME);
        uart_write(",");
        uart_write(OSC_FW_VERSION);
        uart_write("\r\n");
    } else if (strcmp(line, "ID?") == 0) {
        uart_write("ID,");
        uart_write(OSC_FW_NAME);
        uart_write(",STM32F103C8T6,");
        uart_write(OSC_FW_VERSION);
        uart_write(",USART1_PA9_PA10,PA8_PWM+BINARY_DATA\r\n");
    } else if (strcmp(line, "CAP?") == 0) {
        send_capabilities();
    } else if (strcmp(line, "HELP") == 0) {
        uart_write("HELP,PING|ID?|CAP?|STATUS|START|STOP|SET WAVE SINE|SQUARE|TRI|SAW|SET FREQ n|SET AMP n|SET OFFSET n|SET RATE n|SET FORMAT ASCII|BINARY\r\n");
    } else if (strcmp(line, "STATUS") == 0) {
        send_status();
        send_format();
    } else if (strcmp(line, "START") == 0) {
        g_streaming = 1U;
        send_ok("START");
    } else if (strcmp(line, "STOP") == 0) {
        g_streaming = 0U;
        send_ok("STOP");
    } else if (starts_with(line, "SET ")) {
        handle_set(line);
    } else {
        send_err("unknown_cmd");
    }
}

void protocol_init(void)
{
    g_rx_len = 0U;
    g_streaming = 1U;
    g_binary_enabled = 1U;
}

void protocol_poll(void)
{
    char ch;

    while (uart_read_char(&ch)) {
        if (ch == '\r' || ch == '\n') {
            if (g_rx_len > 0U) {
                g_rx_line[g_rx_len] = '\0';
                handle_line(g_rx_line);
                g_rx_len = 0U;
            }
        } else if (g_rx_len < (RX_LINE_MAX - 1U)) {
            g_rx_line[g_rx_len++] = ch;
        } else {
            g_rx_len = 0U;
            send_err("line_too_long");
        }
    }
}

uint8_t protocol_streaming_enabled(void)
{
    return g_streaming;
}

uint8_t protocol_binary_enabled(void)
{
    return g_binary_enabled;
}

void protocol_send_boot(void)
{
    uart_write("BOOT,");
    uart_write(OSC_FW_NAME);
    uart_write(",");
    uart_write(OSC_FW_VERSION);
    uart_write(",STM32F103C8T6,");
    write_u32(OSC_UART_BAUD);
    uart_write("\r\n");
    send_status();
    send_format();
    send_capabilities();
}

void protocol_send_sample(const signal_sample_t *sample)
{
    uart_write("OSC,");
    write_u32(sample->sequence);
    uart_write(",");
    write_u32(sample->time_ms);
    uart_write(",");
    write_u32(sample->value_mv);
    uart_write(",");
    uart_write(signal_wave_name(sample->wave));
    uart_write(",");
    write_u32(sample->frequency_hz);
    uart_write(",");
    write_u32(sample->amplitude_mv);
    uart_write(",");
    write_u32(sample->offset_mv);
    uart_write("\r\n");
}

void protocol_send_binary_block(uint32_t sequence, uint16_t sample_rate_hz, const uint16_t *values_mv, uint16_t point_count)
{
    uint8_t frame[BINARY_HEADER_LEN + (OSC_BINARY_BLOCK_POINTS * 2U) + BINARY_CRC_LEN];
    uint16_t index = 0U;
    uint16_t i;
    uint16_t adc;
    uint16_t crc;

    if (point_count == 0U) {
        return;
    }
    if (point_count > OSC_BINARY_BLOCK_POINTS) {
        point_count = OSC_BINARY_BLOCK_POINTS;
    }

    frame[index++] = BINARY_SYNC0;
    frame[index++] = BINARY_SYNC1;
    frame[index++] = BINARY_VERSION;
    frame[index++] = BINARY_TYPE_DATA;
    put_u32_le(frame, &index, sequence);
    put_u32_le(frame, &index, sample_rate_hz);
    frame[index++] = 1U;
    put_u16_le(frame, &index, point_count);

    for (i = 0U; i < point_count; i++) {
        adc = mv_to_adc(values_mv[i]);
        put_u16_le(frame, &index, adc);
    }

    crc = crc16_ccitt(frame, index);
    put_u16_le(frame, &index, crc);
    uart_write_bytes(frame, index);
}
