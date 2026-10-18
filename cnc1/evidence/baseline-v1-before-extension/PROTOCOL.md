# CNC1 reference FPGA ABI, version 1

This repository now includes a custom RTL reference endpoint for six STEP/DIR generators and two ABZ counters. **It is not Mesa HostMot2, is not supported by `hm2_spix` unchanged, and has no completed LinuxCNC realtime driver.** The implementation is a bounded functional reference for the proposed LinuxCNC + FPGA controller. No T20 project, bitstream, pin assignment, resource fit, timing closure, physical SPI test, or machine test is claimed.

The embedded ROCK 3C is the current engineering host baseline. A future custom LinuxCNC realtime HAL component must own this SPI device exclusively. Python, the browser, Wi-Fi, and ESP service firmware must not write cyclic motion commands. The browser connects to the local LinuxCNC service; it is not in this servo link.

## Electrical and timing contract

| Item | Reference contract |
|---|---|
| Core clock | 50 MHz; 20 ns tick; board oscillator/constraints still required |
| SPI | Dedicated short internal bus; mode 0; MSB first; active-low CS; no bus sharing assumed |
| SCLK | At most core/8 = 6.25 MHz; each high and low phase at least four core ticks |
| CS guards | At least eight core ticks from CS assertion to first SCLK rise, and from last SCLK fall to CS release; at least eight ticks high between transfers |
| Frame | Exactly 512 rising edges per CS assertion: 64 bytes full duplex |
| Snapshot | FPGA captures all response fields when synchronized CS assertion is detected; this is one coherent core-clock sample |
| Commit | Command acts only after synchronized CS release, exact length, CRC, and semantic validation |
| Reset | Active-low `reset_n`; asynchronous assertion, internal two-clock synchronous release; boot is disarmed and authorization is withheld |
| External inhibit | Active-low `inhibit_n`; asynchronously gates motion permission and clears authorization; reassertion requires a new SYNC and ARM |
| MISO | `spi_miso` is data, `spi_miso_oe` is a board-wrapper tri-state enable; no pad primitive is included |

At 5 MHz the wire time is 102.4 microseconds per frame, plus guards, kernel/driver overhead, and scheduling. At 6.25 MHz it is 81.92 microseconds. These are arithmetic wire times, not measured Linux servo deadlines. The simulation exercises 5 and 6.25 MHz. Real input delays, synchronizer placement, routing, CS timing, and ROCK 3C SPI behavior require target constraints and oscilloscope/logic-analyzer validation. SPI data and clock are oversampled; no recovered-clock domain is used.

If CS stays asserted with an incomplete frame, the prior valid command remains in force until the watchdog expires. On early CS release, the frame is rejected and link fault latches. Overlength is detected on the first extra clock; outputs are disabled on the ensuing core-clock processing. Fault detection has synchronization/logic latency. This is not a zero-latency physical safety function.

## Common encoding

All multibyte fields are big endian. Signed quantities use 32-bit two's complement. CRC is **CRC-16/CCITT-FALSE**, polynomial `0x1021`, initial value `0xFFFF`, no reflection, no final XOR, over bytes 0–61. Bytes 62–63 contain the CRC, most significant byte first. The `123456789` known-answer CRC is `0x29B1`.

The implementation streams receive and transmit CRC calculations one bit at a time. CRC detects transport corruption probabilistically; it is not authentication or a certified safety protocol. Session/sequence checks reduce accidental stale-command acceptance; they do not resist a malicious host. There is no persistent boot nonce. After full FPGA reset, a replay of an entire valid recorded handshake is not cryptographically excluded. The realtime driver must deliberately create a fresh nonzero session and require a new operator enable after reconnect/reset/fault.

### Command, 64 bytes

| Byte offsets | Field | Validation |
|---|---|---|
| 0–3 | Magic `CNC1` / `43 4e 43 31` | Exact match |
| 4 | ABI version | `01` |
| 5 | Opcode | Defined below |
| 6 | Axis mask | Bits 0–5 correspond to generators 0–5; bits 6–7 zero |
| 7 | Reserved | Zero |
| 8–11 | Session | 32-bit identifier |
| 12–15 | Sequence | 32-bit sequence |
| 16–39 | Six signed rates | Axis order 0–5; phase increment per core tick |
| 40–61 | Reserved | All zero |
| 62–63 | CRC | Common encoding above |

There are no independently writable live registers. This fixed register image is validated and committed atomically, preventing a half-written set of axis rates from becoming active.

| Opcode | Name | Rules and effect |
|---|---|---|
| `00` | NOP/read status | All bytes 6–61 zero; never feeds the watchdog or changes motion state |
| `01` | SYNC/recover | Disarmed only; nonzero session different from current session; sequence 0; mask/rates zero; inhibit must be released and synchronized; clears latched faults and establishes a new session |
| `02` | ARM | Same session, next sequence; disarmed and fault-free; mask nonzero; all rates zero; enables the selected axes at zero velocity and starts watchdog |
| `03` | UPDATE | Same session, next sequence; already armed and fault-free; mask exactly equals armed mask; bounded rates, unused axes zero; atomically replaces rates and feeds watchdog |
| `04` | DISARM | Same session, next sequence; mask/rates zero; immediately removes motion permission and zeros rates; preserves fault latches |

Sequence must equal the last accepted sequence plus one, must be nonzero, and may not wrap. The driver must DISARM and SYNC a new session before exhaustion. ARM cannot be used to change an already armed mask. Repeated SYNC with the current session is rejected. Recovery is deliberate: stop the host command stream, reconcile machine state, SYNC a new session, acknowledge its status, then ARM zero-speed and acknowledge before sending nonzero UPDATE.

Any bad CRC, wrong length, invalid magic/version/reserved bits/opcode, bad session/sequence, invalid state transition, mask mismatch, nonzero ARM rate, or excessive rate latches a link fault and disarms all axes. A valid DISARM is accepted even if faults are latched, but cannot clear them. A valid SYNC sent while armed is a protocol error and disarms; it does not recover within that same frame. NOP can read fault status.

### Response, 64 bytes

| Byte offsets | Field |
|---|---|
| 0–3 | Magic `CNS1` / `43 4e 53 31` |
| 4 | ABI version `01` |
| 5 | Bit 0 effective motion permission; bit 1 endpoint ready; bits 2–7 zero |
| 6 | Current armed axis mask; zero when disarmed |
| 7 | Fault bits: 0 link, 1 watchdog, 2 inhibit/boot authorization withheld, 3 step timing; remaining bits zero |
| 8–11 | Current session, zero before SYNC |
| 12–15 | Last accepted motion-control sequence; zero after SYNC |
| 16–19 | Snapshot core timestamp, unsigned 32-bit ticks |
| 20–43 | Six signed emitted-pulse counters, axis order 0–5 |
| 44–51 | Two signed quadrature counts, encoder order 0–1 |
| 52–59 | Two signed index-latched quadrature counts, encoder order 0–1 |
| 60 | Bits 0–1 index seen; bits 4–5 illegal quadrature transition seen; other bits zero |
| 61 | Reserved zero |
| 62–63 | CRC of snapshot payload |

**Response describes state sampled at the beginning of the transaction, before that transaction's command is committed.** The host must check acknowledgment in a subsequent response; sending an ARM frame does not make that same frame's response report armed. It must treat corrupted/missing responses, unexpected session/sequence, counter discontinuity, and stale timestamps as link failure. A NOP transaction can retrieve an acknowledgment but does not extend the watchdog deadline.

`endpoint_ready` means synchronized inhibit release, established session, and no latched fault. It is not proof that a LinuxCNC driver is loaded, machine limits are satisfied, drive ready is true, or physical safety contacts are closed. Timestamp wraps every 85.89934592 seconds at 50 MHz. Timestamp and all counters reset with the FPGA, so the driver needs its own host sample time, connection epoch, and modulo-wrap handling. Do not interpret a changed sequence by itself as a fresh physical feedback sample.

## Motion and encoder behavior

Rates are DDS phase increments. Nominal pulse frequency is `abs(rate) * core_hz / 2^32`, with negative rate driving DIR high and decrementing the generated-pulse count. Production default `MAX_RATE = 0x01000000` gives a maximum **195,312.5 pulses/second per channel at 50 MHz**. This is a chosen reference limit, not a silicon maximum or a Mesa specification. LinuxCNC must enforce machine acceleration/velocity limits and compute the signed increments in its servo thread. This endpoint does not plan trajectories, interpolate positions, buffer jobs, close position loops, or decelerate after communication loss.

Defaults are 100 core ticks each for STEP high, minimum STEP low, DIR setup, and DIR hold from the last STEP rising edge: 2 microseconds at 50 MHz. DDS overflow intervals at the allowed maximum leave margin for these pulse constraints. A reversal completes an in-progress pulse and holds/settles DIR before further pulses; zero rate completes an in-progress pulse and clears phase. The six generators are independent and update rates from the same accepted frame. If a DDS overflow arrives while pulse timing is busy, the channel latches a timing fault and the endpoint disarms rather than silently claiming a delivered pulse. A change to the rate limit or timing parameters requires new timing analysis and tests.

DISARM, reset, inhibit, and faults remove permission immediately within their described latency and **can truncate an in-progress STEP pulse**. They are not controlled feed holds. Generated-pulse counters are diagnostic counts of internal rising edges; they are not motor/axis feedback, and cannot prove that a drive accepted a truncated pulse or that the mechanism reached position. After an abrupt fault, physical position must be reconciled under the machine's recovery procedure.

Each encoder uses synchronized ABZ inputs and x4 Gray-code decoding. Positive order is `00 -> 01 -> 11 -> 10 -> 00`. A two-bit AB change does not increment the count and sets a sticky diagnostic. On synchronized Z rising edge, the current updated count is latched without zeroing it. Counts continue while disarmed or faulted; index-seen/invalid-transition flags clear only on reset. Startup AB levels and input filtering need machine-specific handling; this reference has no debounce/noise filter beyond synchronization and no proven maximum encoder edge rate.

The default watchdog is 250,000 core ticks = 5 ms at 50 MHz, measured while armed since the last accepted ARM/UPDATE. Expiry wins over a frame arriving on the deadline. NOP, malformed transactions, Linux/browser liveness, and ESP activity cannot feed it. Tests shorten this to 20,000 ticks to exercise expiry. **An FPGA clock halt cannot be detected by this clocked watchdog; the board's independent external watchdog and default-disabled drive gate are still mandatory.** Inhibit pulse capture is modeled asynchronously but the minimum physical pulse width remains a target-device/board requirement.

## Board and driver integration still required

The endpoint has 31 logical pad signals if all four faults and endpoint-ready are exported: clock/reset/inhibit (3), SPI (4), STEP/DIR (12), ABZ (6), global motion enable (1), endpoint ready (1), faults (4). MISO OE is a wrapper control, not an additional connector signal. Some diagnostics may stay internal after board review. There is no Efinix pad primitive, PLL, package/bank assignment, voltage standard, boot flash, or reset/pull-down circuit in this directory.

This subset does not implement the board's 6 per-drive enables, 6 alarms, 16 field inputs, 8 general outputs, spindle command/0–10 V, probe latch, external watchdog progress output, or tool changer behavior. Those need explicit new RTL/protocol allocation and tests. Do not assign spare reserved ABI bytes to actuators ad hoc.

The future HAL driver must use preallocated buffers and deterministic SPI access on the selected ROCK 3C Linux RT build; measure complete servo-cycle latency under display/render/storage/network load; own the device exclusively; convert velocity/rate units safely; validate every response; maintain host timestamp/epoch and session; expose commanded motion separately from emitted counts and actual encoder feedback; implement zero-speed handshake; and latch communication faults into LinuxCNC's machine state. The existing Python LinuxCNC command/stat/error adapter is an operator frontend, not this driver. `hm2_spix` on an unmodified host does not implement CNC1.

The control system must route E-stop, drive gate, rail/reset qualification, and external watchdog through independently reviewed hardware. ESP observes diagnostics over its separate service link and has no arm/STEP/DIR path. No change here authorizes physical machine operation.

## Reproduce the software evidence

From the project root on Windows:

```powershell
python gateware/tools/protocol.py --write-vectors
wsl -d GarciaMechBuilder -- sh -lc 'cd /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/gateware && sh tools/run_tests.sh'
```

On another Linux installation with Icarus Verilog, run `python3 gateware/tools/protocol.py --write-vectors` from the project root and `sh gateware/tools/run_tests.sh`. Verilator provides a second lint check when installed. Neither script opens a hardware device. Build outputs stay under `gateware/build/`, which is ignored. Checked-in `tests/vectors.hex` and `tests/vectors.json` contain independent Python `binascii.crc_hqx` vectors.

See `../reports/GATEWARE_VALIDATION.md` for the actual tools, results, and unresolved acceptance gates.
