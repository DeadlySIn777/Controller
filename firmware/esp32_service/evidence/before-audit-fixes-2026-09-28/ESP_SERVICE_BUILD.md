# ESP service implementation evidence

28 September 2026. Both actual ESP32-S3 configurations compiled and linked successfully with the existing ESP-IDF 5.5.4 installation, pinned at `735507283d5b2f9fb363a1901172dbd9e847945d`, Xtensa GCC 14.2.0. No device was connected or flashed. Exact image sizes, hashes and source hashes are recorded in [ESP_SERVICE_BUILD.json](ESP_SERVICE_BUILD.json). The hashed images and build logs are retained in `firmware/esp32_service/evidence/` (with `SHA256SUMS`) because `.build/` is git-ignored; the build is not configured as reproducible (`CONFIG_APP_COMPILE_TIME_DATE=y`, `CONFIG_APP_REPRODUCIBLE_BUILD` unset), so a rebuild yields different hashes and must be compared against the retained copies, not regenerated.

| Check | Result | Limit |
|---|---|---|
| Default ESP32-S3 application | Compiled and linked; host RX disabled | No approved board pin map or physical run |
| UART-enabled compile-check variant | Compiled and linked with test-only GPIO4 | Exercises conditional compilation; GPIO4 is not assigned for the product |
| Portable C core, GCC strict warnings | Passed | Host execution, not ESP timing |
| Address and undefined-behavior sanitizers | Passed | Covers the executed cases, not every possible program behavior |
| CRC/replay/clocks/freshness/reboot/parser checks | Passed | Health observations remain advisory and unauthenticated |
| Corruption/noise input | All 40 single-byte positions rejected; 100,000 pseudo-random bytes processed with bounded buffer assertions | Not exhaustive fuzzing or an electrical UART test |
| Python frame encoder tests | 5 passed | Same wire format; opens no hardware port |

The implemented helper reports host-link freshness separately from backend progress. A fresh heartbeat cannot hide an unchanged progress counter. Independent review caught and corrected a first-sample overclaim: every new boot now needs a subsequent counter advance before progress becomes fresh. UART-buffer age and cross-boot authentication remain limitations, so observations are advisory. It exposes no motion, reset, spindle, relay or enable command. Default firmware emits read-only USB diagnostic status; wireless provisioning, PGOOD/DISARMED inputs and recovery sequencing remain unfinished.

Reproduce with [firmware instructions](../firmware/esp32_service/README.md). SDK-generated build output includes example flashing commands; none were executed. Image existence is build evidence, not authorization to flash an unknown board.
