#ifndef UART_H
#define UART_H

#include <stdint.h>

void uart_init(uint32_t baud);
void uart_write_char(char ch);
void uart_write(const char *text);
uint8_t uart_read_char(char *out);

#endif
