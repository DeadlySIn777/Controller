# ESP32-S3 diagnostic helper

Actual ESP-IDF application plus a portable C parser/freshness monitor. This is the first implemented helper function, not a complete wireless/recovery product. It configures no machine output, reset output, spindle output or step pin. Host UART input is disabled by default until its physical pin map is reviewed. USB Serial/JTAG emits diagnostic JSON once per second.

## Implemented behavior

The helper consumes fixed 40-byte little-endian observation frames. It rejects wrong framing/version/type/length, unknown flags, CRC corruption, duplicate/reordered sequence numbers, decreasing host time and backwards progress. The bounded parser resynchronizes after noise or partial frames. Missing heartbeats and stalled progress expire separately (see the deadlines below); replayed packets within the currently tracked boot cannot renew freshness. New host identity resets diagnostic history and requires a subsequent forward counter change before reporting progress. A CRC does not authenticate the sender, so every reported host flag is advisory.

Freshness uses local processing time. Buffered UART bytes received before a service stall can be processed later; this implementation does not prove their original age. Boot identities are not authenticated or persistently remembered, so switching identities is not a security-grade replay defense. These limitations are acceptable only for the current advisory diagnostics, not for machine permission or automatic recovery.

## Freshness deadlines and required host cadence

The application uses two named deadlines from `core/service_health.h`, both in local processing time (when the ESP parses the frame, not when a host sent it or its bytes reached the UART) and both compared strictly (`age < deadline`):

| Output | Constant | True only when |
|---|---|---|
| `link_fresh` | `SH_LINK_TIMEOUT_MS` = 1000 ms | An accepted frame (correct framing and CRC, same-boot sequence higher than the last accepted one, non-decreasing host uptime) was parsed less than 1000 ms ago |
| `backend_progress_fresh` | `SH_PROGRESS_TIMEOUT_MS` = 500 ms | `link_fresh`, and an accepted frame from the same host boot carried a forward completed-cycle counter change (1 to 2^31−1 modulo 2^32) less than 500 ms ago |

Required host behaviour that follows from the code:

- Send accepted frames with gaps well below 1000 ms. 4–10 Hz is recommended. An exact 1 Hz sender sits on the strict boundary and will read stale (flap); do not read `link_fresh=false` from such a sender as a wiring fault.
- Accepted frames that show a counter advance must be less than 500 ms apart. At 4 Hz every frame must show an advance; at 10 Hz at least every fourth frame must. A heartbeat with an unchanged counter keeps `link_fresh` but lets `backend_progress_fresh` expire.
- The first frame of a new boot identity is only a baseline and never reports progress. Replayed, duplicate or reordered sequence numbers, corrupted frames and frames with unknown flags are rejected and renew neither deadline.
- Status is sampled and printed once per `SERVICE_STATUS_PERIOD_MS` (1000 ms) from a loop that polls the UART every `SERVICE_POLL_MS` (10 ms). Each printed value is an instantaneous sample, not an edge-triggered alarm: a stale interval shorter than about 1 s can fall between two samples and never appear in the output.

These deadlines were chosen for this advisory diagnostic helper. They are not measured or approved machine limits, are not qualified on hardware (no device has been flashed), and are not the FPGA/TPS3431 motion-watchdog timing in `docs/ELECTRICAL_DESIGN.md`. `tests/test_service_health.c` asserts the exact values and the 1 Hz, 4 Hz and every-other-frame-advance cases above.

`motion_authority` is always false. No message can arm, start, resume or reset the controller. Physical PGOOD/DISARMED sensing, authenticated wireless service, provisioning and stopped recovery are still future work; no arbitrary GPIO has been assigned for them.

| Bytes | Meaning |
|---|---|
| 0–3 | ASCII `ESV1` |
| 4, 5 | Version 1, observation type 1 |
| 6–7 | Payload length 28, little-endian |
| 8–15 | Nonzero host boot identity |
| 16–19 | Strictly increasing sequence; no wrap within a boot |
| 20–23 | Completed backend-cycle counter; modulo-32 forward differences only |
| 24–31 | Host monotonic uptime in milliseconds |
| 32–35 | Bit 0 reported disarmed, bit 1 reported fault; other bits rejected |
| 36–39 | IEEE CRC-32 over bytes 0–35, little-endian |

The payload length denotes bytes 8–35, including flags. The complete wire frame is always 40 bytes. A future incompatible change must change the version. The first counter sample in any boot is only a baseline; a later forward change supplies progress evidence. UI status polls are not servo-cycle progress. `controller_lab.service_health.encode_health` produces the same framing without opening any port.

## Reproduce

The existing local SDK is ESP-IDF 5.5.4, commit `735507283d5b2f9fb363a1901172dbd9e847945d`, with Xtensa GCC 14.2.0. From PowerShell run `./firmware/esp32_service/build-local.ps1`. It defaults to the Windows Espressif installer layout under `C:\Espressif`; on another workstation set `IDF_PATH`, `IDF_TOOLS_PATH` and, if needed, `IDF_PYTHON_ENV_PATH` first. The script refuses any ESP-IDF version other than 5.5.4 because the recorded evidence was compiled with it. This compiles only; it never invokes flash or monitor. The compiled application is under `.build/esp32s3/`.

`.build/` and `*.log` are git-ignored, so the images and logs cited by `reports/ESP_SERVICE_BUILD.md` are retained in `evidence/` together with `evidence/manifest.json` and `evidence/SHA256SUMS`. From PowerShell (not Git Bash, whose MSYS environment ESP-IDF's export script rejects; the recorder strips it), `python firmware/esp32_service/record_evidence.py --build --clean --host-tests` deletes the two variant build directories (build output only), runs both `build-local.ps1` variants and the host core tests below in the `GarciaMechBuilder` WSL distribution (`--wsl-distro` to change), copies the images and logs, writes the manifest and checksums, and refreshes the build and source hashes in `reports/ESP_SERVICE_BUILD.json`. `--clean` also deletes the generated `.build/uart-sdkconfig` so the UART variant's configuration is regenerated from `sdkconfig.defaults` and `sdkconfig.uart-build-check.defaults`; a copy is retained as `evidence/uart-compile-check.sdkconfig` and hashed, and the tracked `sdkconfig` (the default variant's configuration) is in `source_sha256`. Without `--build` it re-records what is already in `.build/` only if every image is newer than all firmware sources, CMake/Kconfig files, defaults files and its effective `sdkconfig`, and otherwise refuses. Without `--host-tests` it removes any earlier `evidence/host-core-test.log` instead of carrying it forward, and the report's `host_core_validation.result` says the tests were not rerun. `evidence_record` in `reports/ESP_SERVICE_BUILD.json` and the manifest record which steps ran. `python -m pytest -q firmware/esp32_service/tests/test_record_evidence.py` tests these guards without building. The build is not reproducible: `CONFIG_APP_COMPILE_TIME_DATE=y` and `CONFIG_BOOTLOADER_COMPILE_TIME_DATE=y` embed the build time and `CONFIG_APP_REPRODUCIBLE_BUILD` is unset, so a rebuild of identical source produces different image hashes. The recorded hashes identify the retained copies; they are not something a rebuild is expected to reproduce. The retained images are build evidence only, not release or flash images.

`build-local.ps1 -UartCompileCheck` uses a separate configuration/output folder to compile the UART code path with a test-only GPIO value. That value is not an approved hardware pin map or a firmware release to flash. Both configurations must compile before recording complete build evidence.

Host core tests on the existing WSL Alpine GCC:

```sh
mkdir -p firmware/esp32_service/.build
gcc -std=c11 -O1 -g -Wall -Wextra -Werror -pedantic \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Ifirmware/esp32_service/core \
  firmware/esp32_service/core/service_health.c \
  firmware/esp32_service/tests/test_service_health.c \
  -o firmware/esp32_service/.build/test_service_health_sanitized
firmware/esp32_service/.build/test_service_health_sanitized
```

The tests cover standard CRC vectors, expiry boundaries, the documented 1000/500 ms deadlines and host cadence, replay, counter wrap, reboot, stale progress despite fresh heartbeats, each single-byte corruption position (with every accepted-health field compared before and after), truncation, parser resynchronization, and 100,000 pseudo-random input bytes. They do not measure physical UART behavior, power, radio interference or GPIO timing.

Espressif references: [standard I/O and USB console](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/esp32s3/api-guides/stdio.html), [UART API](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/esp32s3/api-reference/peripherals/uart.html). No device was connected or flashed.
