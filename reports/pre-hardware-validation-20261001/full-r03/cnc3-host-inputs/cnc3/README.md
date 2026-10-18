# cnc3 — IS-1 host driver

The host side of interface specification IS-1: CNC3 frames on two chip selects (CS_FB 176 bytes,
CS_CMD 96 bytes, ABI 3). The historical six-joint `cnc1` driver and its evidence are unchanged.

| Path | Contents | Status |
|---|---|---|
| `src/cnc3_proto.[ch]` | C codec: CRC-16/CCITT-FALSE and CRC-32C, command builders, receiver validation (same rules, order and result codes as `gateware/v3/tools/protocol_v3.py`), CNF3/CNS3/CAP3 encode and decode, 24-bit counter unwrap | implemented, host-tested |
| `src/cnc3_layout.h`, `src/cnc3_rules.h`, `tests/cnc3_vectors.h` | generated from `spec/protocol.json` by `gateware/v3/tools/gen_c_layout.py`; do not edit | generated, freshness tested |
| `src/cnc3.[ch]` | driver core: discovery (READ_PAGE 0 then CAP3), CONFIGURE for 8 or 12 joints, SYNC/ARM/UPDATE/DISARM/NOP, acknowledgement checks, first-fault latching, no automatic re-arm, sample-age bound from the discovered watchdog, servo-period bound, 24-bit count unwrap with plausibility limits, position-continuity mask, event-ring storage and acknowledgement, telemetry mirror storage | implemented, host-tested against the model |
| `model/cnc3_model.[ch]` | behavioural reference model of the endpoint's host-link semantics (its header lists exactly what is and is not modelled) | test double, not the FPGA |
| `tests/test_proto.c`, `tests/test_driver.c` | codec against all golden vectors and every single-bit flip; driver against the model: bring-up for 8, 12 and 12-fitted/8-used, motion on all configured channels, 24-bit wrap over 100 s, corrupted response, corrupted command, watchdog, stale sample, period bound, twelve joints without MX4, expansion removal, continuity | host tests |
| `tools/host_tests.sh`, `tools/host_tests_rootfs.sh` | build with `-Wall -Wextra -Werror -pedantic -Wconversion -Wshadow` and ASan/LSan/UBSan; the rootfs script runs in the Debian rootfs with its own /proc | |

Evidence class: **host tests only**. No RTL, LinuxCNC, SPI device or hardware is involved yet.

Not yet implemented here: the LinuxCNC HAL component and IS-1 pin registry, the I/O exchange
(CONFIGURE_IO, IO_ENABLE/IO_WRITE, output image in UPDATE, DI/AI validity and age publication),
the spidev transport, the Verilated RTL transport and LinuxCNC profiles.
