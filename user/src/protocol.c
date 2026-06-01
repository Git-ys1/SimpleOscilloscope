#include "protocol.h"
#include "osc_config.h"
#include "uart.h"
#include <stdlib.h>
#include <string.h>

#define RX_LINE_MAX 96U

static char g_rx_line[RX_LINE_MAX];
static uint8_t g_rx_len;
static uint8_t g_streaming;

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
        send_ok("RATE");
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
        uart_write(",USART1_PA9_PA10,PA8_PWM\r\n");
    } else if (strcmp(line, "HELP") == 0) {
        uart_write("HELP,PING|ID?|STATUS|START|STOP|SET WAVE SINE|SQUARE|TRI|SAW|SET FREQ n|SET AMP n|SET OFFSET n|SET RATE n\r\n");
    } else if (strcmp(line, "STATUS") == 0) {
        send_status();
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

void protocol_send_boot(void)
{
    uart_write("BOOT,");
    uart_write(OSC_FW_NAME);
    uart_write(",");
    uart_write(OSC_FW_VERSION);
    uart_write(",STM32F103C8T6,115200\r\n");
    send_status();
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
