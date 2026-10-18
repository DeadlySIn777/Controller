#include <inttypes.h>
#include <stdio.h>
#include "sdkconfig.h"
#include "esp_err.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "service_health.h"

/* Diagnostic status is sampled and printed once per SERVICE_STATUS_PERIOD_MS
 * from a loop that polls UART input every SERVICE_POLL_MS. Deadlines are the
 * named SH_LINK_TIMEOUT_MS / SH_PROGRESS_TIMEOUT_MS in service_health.h. */
#define SERVICE_STATUS_PERIOD_MS 1000u
#define SERVICE_POLL_MS 10u

void app_main(void) {
    sh_state health;
    sh_init(&health);
#if CONFIG_CNC_SERVICE_HOST_RX_GPIO >= 0
#if CONFIG_CNC_SERVICE_HOST_RX_GPIO == 19 || CONFIG_CNC_SERVICE_HOST_RX_GPIO == 20 || (CONFIG_CNC_SERVICE_HOST_RX_GPIO >= 22 && CONFIG_CNC_SERVICE_HOST_RX_GPIO <= 32)
/* GPIO19/20 carry the USB Serial/JTAG console, GPIO22-25 do not exist on the
 * ESP32-S3 and GPIO26-32 are the module SPI flash bus. uart_set_pin() would
 * either reject the pin at boot (ESP_ERROR_CHECK -> abort -> reboot loop) or
 * silently steal the console/flash pin, so refuse the value at compile time. */
#error "CONFIG_CNC_SERVICE_HOST_RX_GPIO must not be 19, 20 or 22-32 on ESP32-S3"
#endif
    /* No TX, reset, enable, step, spindle or relay output is configured. */
    const uart_config_t config = {
        .baud_rate = 115200, .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE, .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE, .source_clk = UART_SCLK_DEFAULT
    };
    ESP_ERROR_CHECK(uart_param_config(UART_NUM_1, &config));
    ESP_ERROR_CHECK(uart_set_pin(UART_NUM_1, UART_PIN_NO_CHANGE,
        CONFIG_CNC_SERVICE_HOST_RX_GPIO, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
    ESP_ERROR_CHECK(uart_driver_install(UART_NUM_1, 512, 0, 0, NULL, 0));
#endif
    uint64_t last_print = 0;
    for (;;) {
        const uint64_t now = (uint64_t)(esp_timer_get_time() / 1000);
#if CONFIG_CNC_SERVICE_HOST_RX_GPIO >= 0
        uint8_t bytes[128];
        const int n = uart_read_bytes(UART_NUM_1, bytes, sizeof(bytes), 0);
        for (int i = 0; i < n; ++i) sh_feed(&health, bytes[i], now);
#endif
        if (now - last_print >= SERVICE_STATUS_PERIOD_MS) {
            last_print = now;
            const sh_snapshot s = sh_observe(&health, now, SH_LINK_TIMEOUT_MS,
                SH_PROGRESS_TIMEOUT_MS);
            printf("{\"service_version\":1,\"uptime_ms\":%" PRIu64
                ",\"host_seen\":%s,\"link_fresh\":%s,\"backend_progress_fresh\":%s,"
                "\"motion_authority\":false,\"host_flags_are_advisory\":true}\n",
                now, s.host_seen ? "true" : "false", s.link_fresh ? "true" : "false",
                s.backend_progress_fresh ? "true" : "false");
        }
        vTaskDelay(pdMS_TO_TICKS(SERVICE_POLL_MS));
    }
}
