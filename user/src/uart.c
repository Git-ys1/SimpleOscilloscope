#include "uart.h"
#include "stm32f10x.h"

#define UART_RX_BUFFER_SIZE 128U

static volatile uint8_t g_rx_buffer[UART_RX_BUFFER_SIZE];
static volatile uint16_t g_rx_head;
static volatile uint16_t g_rx_tail;

void USART1_IRQHandler(void)
{
    uint32_t sr = USART1->SR;

    if ((sr & USART_SR_RXNE) != 0U) {
        uint8_t ch = (uint8_t)(USART1->DR & 0xFFU);
        uint16_t next = (uint16_t)((g_rx_head + 1U) % UART_RX_BUFFER_SIZE);
        if (next != g_rx_tail) {
            g_rx_buffer[g_rx_head] = ch;
            g_rx_head = next;
        }
    } else if ((sr & USART_SR_ORE) != 0U) {
        (void)USART1->DR;
    }
}

void uart_init(uint32_t baud)
{
    uint32_t brr;

    g_rx_head = 0U;
    g_rx_tail = 0U;

    RCC->APB2ENR |= RCC_APB2ENR_USART1EN;
    brr = (SystemCoreClock + (baud / 2U)) / baud;
    USART1->BRR = (uint16_t)brr;
    USART1->CR1 = USART_CR1_TE | USART_CR1_RE | USART_CR1_RXNEIE | USART_CR1_UE;
    NVIC_EnableIRQ(USART1_IRQn);
}

void uart_write_char(char ch)
{
    while ((USART1->SR & USART_SR_TXE) == 0U) {
    }
    USART1->DR = (uint16_t)(uint8_t)ch;
}

void uart_write(const char *text)
{
    while (*text != '\0') {
        uart_write_char(*text++);
    }
}

uint8_t uart_read_char(char *out)
{
    if (g_rx_head == g_rx_tail) {
        return 0U;
    }

    *out = (char)g_rx_buffer[g_rx_tail];
    g_rx_tail = (uint16_t)((g_rx_tail + 1U) % UART_RX_BUFFER_SIZE);
    return 1U;
}
