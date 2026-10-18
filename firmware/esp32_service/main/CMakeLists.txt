idf_component_register(SRCS "service_main.c" "../core/service_health.c"
    INCLUDE_DIRS "../core" REQUIRES esp_timer esp_driver_uart)
