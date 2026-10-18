# CNC1 Linux SPI transport implementation

28 September 2026. A **laboratory Linux spidev backend is implemented and compiled** against the existing `cnc1_transport` callback interface. Tests use injected syscall responses; no SPI device was opened. The default LinuxCNC profile continues to use actual RTL simulation. This backend is not a qualified real-time motion transport.

## Implemented behavior

- Explicit initialized context, literal `/dev/spidevB.C` path and positive clock request capped at the study's 6.25 MHz laboratory ceiling. The ceiling is a software bound, not a measured board capability.
- `O_CLOEXEC` and `O_NOFOLLOW`, character-device check, nonblocking advisory `flock`, then mode-0, eight-bit, MSB-first configuration with readback. A lower positive configured maximum is accepted; incompatible mode, width, order or speed is refused.
- One `SPI_IOC_MESSAGE(1)` containing one 64-byte full-duplex transfer, with no mid-frame chip-select change. Zero-initialized transfer metadata and copied TX data support identical and partially overlapping caller buffers.
- Only a complete 64-byte result exposes RX to the common protocol driver. Short, excessive or negative returns clear RX and latch transport failure. EINTR is never blindly retried because the command may already have been transmitted. Later exchanges refuse until explicit close/reopen; opening the backend itself does not reset a CNC1 session or authorize motion.
- Setup failure releases its descriptor once and preserves the original error. Close invalidates the stored descriptor before the syscall and never retries a potentially reused descriptor. No heap allocation, logging or automatic device enumeration occurs in the exchange function.

The common CNC1 code still owns frame CRC, capability, session, sequence, freshness and motion policy. Kernel transfer success does not prove a responding CNC endpoint. The Linux API supports composite full-duplex transfers, but is synchronous, cannot report the actual on-wire bit rate, and generally cannot detect an absent SPI device through transport errors alone. [Linux SPI userspace API](https://docs.kernel.org/spi/spidev.html)

## Files and executed checks

| File | Purpose |
|---|---|
| [spidev_transport.h](../cnc1/src/spidev_transport.h) | C/C++ public lifecycle, configuration, injectable operations and common transport adapter |
| [spidev_transport.c](../cnc1/src/spidev_transport.c) | Actual Linux open/fstat/flock/ioctl/close wrappers and transport implementation |
| [test_spidev.c](../cnc1/tests/test_spidev.c) | Mocked Linux-operation checks, including every setup-stage failure and transfer error behavior |
| [test_spidev_cpp.cpp](../cnc1/tests/test_spidev_cpp.cpp) | Public C++ header links to the actual C object without opening a device |
| [test_spidev.sh](../cnc1/tools/test_spidev.sh) | Strict compilation, normal test, ASan/UBSan test and C++ linkage in the existing isolated Debian rootfs |

Both normal and ASan/UBSan runs pass **892 assertions each**, including repeated setup assertions. C++ linkage also passes. Coverage includes malformed and unterminated paths, clock bounds, character/lock failures, all eight setup ioctl failures, mismatched readback, descriptor cleanup, re-open, aliased/overlapping buffers, short/long transfers, EINTR and sticky failure. All device operations in the successful-path tests are mocks, with no physical device access.

Compiler/header packages: GCC/G++ 14.2, libc development package `2.41-12+deb13u4`, Linux userspace headers `6.12.107-1`. The [raw test output](../cnc1/evidence/spidev/tests.log), [package identities](../cnc1/evidence/spidev/build-packages.tsv) and [source/build manifest](../cnc1/evidence/spidev/manifest.json) preserve the result. An initial sanitizer launch failed because the isolated rootfs lacked a mounted `/proc`; the launcher now mounts it inside a private process/mount namespace. The original failed log is retained separately, not represented as a passing run.

Reproduce from the project directory:

```powershell
wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/test_spidev.sh
```

## Boundary before machine use

The synchronous ioctl has **no enforced completion deadline** here. A timeout errno from a driver is handled if returned; the mock timeout test does not prove bounded waiting. Thread cancellation, signals or `O_NONBLOCK` would not turn this into a measured real-time implementation. Advisory flock cannot exclude programs/kernel users that ignore it or prove exclusive ownership of a physical bus.

Still needed: exact compute/kernel/pinmux/voltage/CS configuration, exclusive physical ownership, measured transfer and total-cycle latency under graphics/storage/network load, signal integrity and CS/frame gaps, endpoint/watchdog behavior on stalled syscalls, target scheduling and independent machine inhibit. No default motion component, firmware, device-tree setting or physical board has been activated by this work.
