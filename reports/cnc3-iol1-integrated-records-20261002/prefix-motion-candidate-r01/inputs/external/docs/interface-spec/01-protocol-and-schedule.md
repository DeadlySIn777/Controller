Interface specification revision: IS-1

# 01 — CNC1 protocol, card link and per-cycle schedule

Section 01 of interface specification IS-1, written 28 September 2026. Machine-readable companion: [`spec/protocol.json`](../../spec/protocol.json) (`"spec_revision": "IS-1"`). Consistency check: `python tools/is1_protocol_check.py` (add `--hd` for the exhaustive CRC search). Codex's hardware (schematics, power/protection, connectors, PCB, hardware BOM) and Claude's implementation (gateware, CNC1 protocol and LinuxCNC driver, card firmware, configuration and diagnostics service) both build against this revision. A change to anything here needs a new revision identifier (IS-2), not an in-place edit.

**Status.** This is a specification. No RTL, driver, card firmware, schematic, layout or measurement exists for anything defined in this section, and nothing in it is ready for manufacture. The six-joint/two-encoder CNC1 endpoint, its ABI v1 ([gateware/PROTOCOL.md](../../gateware/PROTOCOL.md)) and ABI v2 ([cnc1/PROTOCOL_V2.md](../../cnc1/PROTOCOL_V2.md)), its tests and its synthesis result stay unchanged as **historical baseline evidence**; they are not eight- or twelve-channel evidence.

This section adopts, without change, the decisions of [section 03](03-terminals-and-allocations.md) (cards, terminals, logical field names, proposed HAL names) and [section 04](04-safety-power-timing.md) (timing classes, safety status fields, fault bits, watchdogs, progress pulses, output-path interruption rule, fault states, history persistence). Where section 03 proposed a HAL name or logical field and this section differs, this section governs, as section 03 states.

## 0. Evidence labels

| Label | Meaning |
|---|---|
| [DS] | Manufacturer datasheet or product page, opened and read for this section (section 11) |
| [DDR] | Datasheet desk review recorded earlier in the repository |
| [AR] | Arithmetic from stated inputs, including the scripted exhaustive CRC syndrome searches in section 3.3 and 4.5. Not a measurement |
| [SI] | Source inspection of repository files |
| [REQ] | Requirement or budget allocation set by IS-1. Not evidence that anything meets it |
| [ME] | Physical measurement. **There are none in this section.** Every [ME] item is a required future measurement |

No HDL simulation, synthesis, place-and-route, ERC, DRC or bench measurement was run for this section. The only executed checks are the arithmetic/consistency script and the CRC searches.

## 1. Decisions made in this section

Taken under the user's authority to resolve ordinary engineering decisions. Costs are not priced here (unknown, not zero); the costing section prices them with the replacement-card cost of each card.

| # | Decision | Reason (evidence) | Cost and capability | Standard / option |
|---|---|---|---|---|
| D01-1 | Two chip selects on the one host SPI bus with fixed, different frame lengths: **CS_FB 176 bytes** (feedback read, before LinuxCNC computes) and **CS_CMD 96 bytes** (command write, after). Motion, the complete machine-control I/O, feedback, latched faults and validity travel in these two transactions every cycle; there is no third "I/O page" exchange | Wire time plus guards per 1 ms cycle: 436.16 µs at 5 MHz and 349.12 µs at 6.25 MHz, against 615.84 µs for the record's 2 × 128 B plus a separate 128 B I/O exchange and 564.16 µs for two symmetric 176 B frames [AR]. The FPGA must know the response type at CS assertion (the snapshot instant), before any command byte arrives, so the type is selected by the chip select, not by an opcode | One extra FPGA input, one extra Ioff buffer channel, one host CS line; unpriced. Gains full I/O at 1 kHz inside the 700 µs target allocation at both clock rates (section 5) | Standard |
| D01-2 | Step, encoder and handwheel counts travel as the **low 24 bits** of the FPGA's 32-bit counters; the host unwraps modulo 2^24 | Saves 36 bytes (57.6 µs at 5 MHz) per cycle [AR]. The unambiguous span of ±2^23 counts is 0.84 s at the 10,000,000 transitions/s encoder goal and 42.9 s at the 195,312.5 steps/s cap, against a 5 ms FPGA watchdog and a host sample-age limit ≤ 5 ms [AR] | None | Standard |
| D01-3 | Index and probe captures are **events** in the FPGA's 256-entry hardware event ring (section 04 12.2), delivered one per cycle in CNS3 and acknowledged by the host; the per-cycle index-latched counts of ABI v1/v2 are dropped | Exact core-tick capture of up to four configured counters per probe edge; one-shot index capture matches LinuxCNC's `index-enable` protocol; saves 36 bytes per cycle [AR] | FPGA block RAM (fit unverified) | Standard |
| D01-4 | Detailed currents, temperatures, voltages and error counters are **telemetry**: sampled on the cards, mirrored in the FPGA with timestamps and ages, delivered one 22-byte mirror entry per cycle. Protection never depends on it (T2) | Keeps the per-cycle frames fixed and short; each value carries its sample age (T4) | FPGA block RAM | Standard |
| D01-5 | **IOL1**: every serial I/O card (DIC, DOA, DOB, ACC) has an **STM32G031** MCU (STM32G031C8T6 on DIC for its 24 inputs, STM32G031K8T6 on the others) as a point-to-point SPI slave; 40-byte frames with identity, epoch, sequence and **CRC-32C**; 100 µs period; validate before commit; card-local accept timer and hardware IWDG | The confirmed decision allows serial I/O only with identity, sequence/freshness and CRC validated before outputs change. Shift registers cannot check a CRC or report identity; a raw converter SPI cannot validate before commit; a CPLD/FPGA per card needs a bitstream. The MCU's CRC unit has a programmable polynomial [DS] and its independent watchdog runs from its own clock [DS] | One MCU per card plus passives, unpriced; each spare card carries it. Gains identity, freshness, CRC-validated outputs, output readback, per-output current/fault/temperature over the TPS274C65ASRHAR SPI (section 03 D03-7), card temperatures, card-local watchdogs and field firmware update without a programmer | Standard (required by the confirmed decision) |
| D01-6 | RS-485 and CAN terminate on the **compute module** (kernel RS-485 tty with MB2HAL; MCP2518FDT-E/SL CAN FD controller with the mainline `mcp251xfd` SocketCAN driver), never in the FPGA and never in the servo thread | A connector and transceiver do not implement Modbus or an accessory's CAN protocol; Linux has mature drivers; gateware stays small; bus retries cannot delay motion. MB2HAL is documented by LinuxCNC as non-real-time and as unsuitable as the only run-enable path [SI] | MCP2518FDT-E/SL [DS] and a second host SPI bus, unpriced; transceivers on ACC (section 03) | Standard |
| D01-7 | EIA and EX8 status bits (pendant selectors, MPG enable, XF presence, port supply faults) use **input-only parallel-in shift registers** with a fixed 1010 marker and double-read agreement | Matches section 03's 3-wire allocation. The registers carry no outputs, so the output-card validation rule does not apply; the marker and the agreement check detect stuck, open and shifted chains | Shift registers, unpriced | Standard |
| D01-8 | Host frames keep **CRC-16/CCITT-FALSE** | Hamming distance 4 at both frame lengths, verified by exhaustive search [AR]; the RTL already streams it; every rejection latches a fault, so undetected-error probability is not relied on for availability | None | Standard |
| D01-9 | The schedule is budgeted at **5 MHz**; 6.25 MHz is used only after the host SPI buffer path is qualified at that rate | The recorded host SPI buffer budget is ≤ 5 MHz ([part-selections](../../reports/audit-2026-09-28/part-selections.json) `host_spi_buffer`) [SI]; the 6.25 MHz ceiling is the FPGA oversampling bound, not a qualified board rate. No limit is raised to make the budget fit | None | Standard |
| D01-10 | Keep **read before compute, write after compute** (two transactions per cycle). A single write-behind transaction per cycle is recorded only as a measured fallback | Write-behind would save one transaction but delay every command by up to one period; it is adopted only if the bench (section 5.7) shows the two-transaction schedule cannot meet the 1 ms deadline | None | — |
| D01-11 | **XS reservation**: CNF3 byte 173 is `port_status_L4_XS`, CONFIGURE_IO page 0 byte 18 is `expected_port_class_L4`, telemetry source 0x04 and HAL port `l4` are reserved for a fifth IOL1 port to the synchronized-expansion slot | Section 02 reserves the XS slot, its six FPGA pins and base contacts; reserving the frame fields now means an XS module needs only a class definition, not a new frame layout | None (the byte was reserved) | Reserved; always 0 in IS-1 |
| D01-12 | **Step-rate cap stays 195,312.5 steps/s per channel** (MAX_RATE 0x01000000, timing table minimum 100 ticks = 2 µs) | It is the rate the existing RTL was simulated at [SI]; the DM542T V4 reference drive accepts at most 200 kHz [DS]; the expanded target's 2,000,000 steps/s figure is a qualification goal that would need a shorter timing minimum, a new MAX_RATE and physical AM26C31/cable qualification. A higher cap can be added later under a CAP3 feature bit without a layout change (`max_rate` is already a capability field) | None | Standard; higher cap is a later option |

## 2. What this section supersedes

In [MOTION_EXPANSION_8_TO_12.md](../MOTION_EXPANSION_8_TO_12.md) (revision 3); the rest of that record stays as design history.

| Old text | IS-1 |
|---|---|
| §5 CNC3/CNS3/CAP3 symmetric 128-byte draft, status layout, NOP + UPDATE per cycle | Sections 3 and 5 here (CS_FB 176 B + CS_CMD 96 B, full I/O in the same two transactions). ABI byte stays 0x03; the record's draft layout is never implemented |
| §5.4 no enable-polarity support | Section 04 section 3: one logical enable per channel drives an NO and an NC photorelay. CNC1 needs no polarity field; the DM542T V4 is supported |
| §5.7 link budget | Section 5 here |
| §9 HAL pin list (`cnc1.N.alarm-in`, `cnc1.enc.K.*`) | Section 7 here (`cnc1.N.alarm`, `cnc1.encoder.K.*`) |
| §14.2 serialized DI/DO through shift registers with marker bits | IOL1 (section 4) for every I/O card; markers survive only on the input-only EIA/EX8 status registers |
| §5.1 `progress_wdi` toggles once per accepted UPDATE | Section 04 5.1: one 1 µs pulse per accepted ARM or UPDATE (`progress_m`) and per accepted output-image exchange (`progress_o`) |
| ABI v1/v2 per-cycle index-latched counts | One-shot INDEX_CAPTURE events (D01-3) |

## 3. Host link: CNC1 ABI 3 (IS-1)

### 3.1 Physical rules

- One SPI bus from the compute module to the motion card, mode 0, MSB first, active-low chip selects, oversampled by the FPGA's 50 MHz core; SCLK ≤ core/8 = 6.25 MHz [SI, v1 rule]. Budget cases: 5.00 MHz (baseline) and 6.25 MHz.
- **CS_FB** frames are exactly **176 bytes** (1,408 rising SCLK edges); **CS_CMD** frames exactly **96 bytes** (768 edges). Shorter, longer, early release, or both chip selects asserted at the same time: rejected, LINK fault latched, all channels disarm, I/O disabled. The bit counter needs 11 bits.
- Snapshot at synchronized CS assertion; commit only after CS release with exact length, CRC and semantic validation (v1 rule). MISO is driven only while one chip select is asserted.
- CS guards ≥ 8 core ticks before the first rising edge and after the last falling edge, and ≥ 8 ticks high between transactions (0.48 µs per transaction) [SI, v1 rule].
- All multibyte fields are big-endian. `u24` fields are the low 24 bits of 32-bit FPGA counters.
- ABI byte = 0x03 in every frame. A v3 driver never talks to a v1/v2 endpoint and vice versa; any mismatch fails closed as `CNC1_BAD_CAPS`.

### 3.2 Per-cycle order

1. The servo thread wakes at (or after) the nominal period boundary T(k).
2. `cnc1.read`: CS_FB transaction carrying FB_READ (event acknowledgement, telemetry priority) → **CNF3** feedback snapshot. The driver validates it and publishes every input pin.
3. LinuxCNC motion, kinematics and the other HAL functions compute.
4. `cnc1.write`: CS_CMD transaction carrying UPDATE (twelve rates and the whole output image) → **CNS3**, whose snapshot was taken at the CS_CMD assertion of this cycle, before this UPDATE commits. It carries the head of the event ring, one telemetry mirror entry and the UPDATE-interval timing. The driver processes it at the end of the cycle; its facts enter the history ring with this cycle's number.

### 3.3 CRC

CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF, no reflection, no final XOR; `123456789` → 0x29B1) over every byte except the last two, stored MSB first in the last two bytes. Hamming distance [AR, exhaustive syndrome search, `tools/is1_protocol_check.py --hd`]: **4** at the 1,408-bit and 768-bit codewords (no undetected error of weight 2 or 3 exists; weight-4 undetected patterns exist). The polynomial has the factor (x + 1) and period 32,767, so HD 4 holds up to 32,751 data bits. Every CRC failure latches a fault; the protocol never retries a rejected frame.

### 3.4 Sessions, sequences and opcodes

One sequence counter is shared by both chip selects: next = last + 1, nonzero, no wrap (the driver starts a new session before exhaustion). FB_READ, READ_PAGE, MAINT and NOP carry sequence 0 and never advance it. The record's §5.3 acceptance rules for SYNC, ARM, UPDATE, DISARM, READ_CAPS and CONFIGURE carry over except where the table says otherwise.

| Code | Name | Chip select | Session / sequence | Accepted when | Effect |
|---|---|---|---|---|---|
| 0x00 | NOP | CS_CMD | session 0 or the current session; sequence 0 | always; bytes 6-7 and 16-93 zero | returns CNS3; changes nothing; never feeds a watchdog |
| 0x01 | SYNC | CS_CMD | new nonzero session != current, sequence 0 | disarmed; I/O disabled; qualification complete; no power-cycle fault; inhibit released; payload zero | new session; clears clearable faults and per-channel latches; restarts faulted IOL1 ports with new epochs; does not set pos_continuity |
| 0x02 | ARM | CS_CMD | current session, next sequence | record 5.3 rules (config_valid, mask == required_mask, installed, no asserted tripping alarm, rates zero) plus: both watchdog self-tests passed since power-up or motion-card change; every encoder in required_encoder_mask valid; motion-critical ports active; and the safety-interface preconditions of section 3.4a (accepted RESET_ARM release within reset_arm_window_ms when required, contactor de-energized, STO state as expected, reset/arm not held); otherwise refused with ARM_REFUSED | arms at zero rate; raises FPGA_MOTION_REQUEST and PERMIT_OUT_REQ; strobes OPI rearm (TX, A, B, BOE); starts 5 ms watchdog; consumes the reset/arm release; one progress_m pulse |
| 0x03 | UPDATE | CS_CMD | current session, next sequence | armed, fault-free, mask == armed mask, unmasked rates zero, \|rate\| within clamp, I/O payload valid (zero while I/O disabled) | atomically replaces 12 rates and the whole output image; restarts the 5 ms motion watchdog and, when I/O is enabled, the 5 ms I/O watchdog; one progress_m pulse; one progress_o pulse when I/O enabled |
| 0x04 | DISARM | CS_CMD | current session, next sequence | mask and rates zero; accepted with faults latched | clean commanded stop (section 04 4.2): no new STEP pulses, current pulse completes, then request drops; pos_continuity kept only if the stop was clean |
| 0x05 | READ_PAGE | CS_FB | session 0 or current, sequence 0 | motion disarmed; byte 16 = page 0-3; bytes 17-173 zero | the next completed CS_FB transaction returns the page instead of CNF3 and consumes it (v2 rule) |
| 0x06 | CONFIGURE | CS_FB | record 5.3 rule (session 0/sequence 0 before a session, else current session and next sequence) | disarmed; I/O disabled; qualification complete; payload valid | record 5.3 accept/reject semantics; rejection clears config_valid, required_mask and alarm masks |
| 0x07 | CONFIGURE_IO | CS_FB | as CONFIGURE | disarmed; I/O disabled; page 0-9 valid | page 0 or 1 replaces that page atomically and clears io_config_valid until page 0 is re-accepted with a matching io_config_hash; pages 2-9 queue a CONFIG_WRITE to the named port; any rejection clears io_config_valid |
| 0x08 | IO_CLEAR_FAULTS | CS_CMD | current session, next sequence | motion disarmed; I/O enabled; each cleared output commanded 0 in this frame's dout_image; rates and mask zero (while armed the same clear travels in UPDATE bytes 80-81) | clears the named output fault latches (FPGA and card); does not re-energize anything; one progress_o pulse |
| 0x09 | IO_WRITE | CS_CMD | current session, next sequence | motion disarmed; I/O enabled; rates and mask zero | replaces the output image; restarts the I/O watchdog; one progress_o pulse |
| 0x0A | IO_ENABLE | CS_CMD | current session, next sequence | io_config_valid; required ports active and identity-matched; no I/O fault; output self-test passed; payload zero | raises FPGA_OUTPUT_REQUEST (SET1 of WD_O, OUT arm latch); strobes OPI_REARM_O; each card re-arms its own output-enable latch only after this and a new epoch (section 4.7); IOL1 frames carry OUT_REQ while OUT_PERMIT is high; one progress_o pulse |
| 0x0B | IO_DISABLE | CS_CMD | current session, next sequence | payload zero; accepted with faults latched | zeroes the output image, drops OUT_REQ and FPGA_OUTPUT_REQUEST |
| 0x0C | MAINT | CS_FB | current session, sequence 0 | motion disarmed; I/O disabled; byte 16 = port 0-3, bytes 17-56 = one complete 40-byte IOL1 frame with control b5 set; rest zero | forwards the frame to the port; the card response returns as the next CS_FB response (page mechanism); used for card firmware update and identity reads |
| 0x0D | SELFTEST | CS_CMD | current session, next sequence | disarmed; I/O disabled; no self-test running (the two tests never overlap); byte 16 = 1 motion watchdog, 2 output watchdog; rest zero | section 04 5.4: the FPGA enters SELFTEST and raises the request with EN_N_i forced high, rates zero, PEN/PWM/AO requests zero, PERMIT_OUT_REQ low (PERMIT_OUT stays open) and OUT_REQ zero in every IOL1 frame (card enables stay low); result in safety word b21/b22 and fault bit WATCHDOG_SELFTEST_FAILED |
| 0x0E | CLEAR_CONTINUITY | CS_CMD | current session, next sequence | disarmed; channel_mask names channels whose re-reference the host has completed; rest zero | sets pos_continuity for those channels |
| 0x10 | FB_READ | CS_FB | session 0 or current session; sequence 0 | payload per fb_read_payload | returns CNF3; pops the event ring when event_ack equals the event last shown; never feeds a watchdog |

### 3.4a Per-channel enable and the safety-interface ARM preconditions (normative)

**Per-channel enable.** Each channel has its own physical enable (section 04 section 3) and its own HAL request `cnc1.N.enable`, but arming stays all-or-nothing (the record's rule, kept because a partly armed gantry or kinematic chain is unsafe):

1. When `cnc1.enable` rises, every `cnc1.N.enable` must equal the channel's bit in the configured `required_mask`. Otherwise the driver sends no ARM, keeps everything disarmed and reports `CNC1_ENABLE_MISMATCH` naming the channels.
2. While armed, a fall of any `cnc1.N.enable` makes the driver send a clean DISARM of all channels (pulse-boundary stop, continuity kept) and report which channel requested it. A rise while armed is ignored until the next ARM.
3. A non-joint channel (an indexer such as a carousel or turret) is a LinuxCNC **extra joint** (`motmod num_extrajoints`), so its `cnc1.N.enable` comes from `joint.J.amp-enable-out` like every other channel (section 7.2).
4. No opcode changes the armed mask while armed. Independent enabling of one channel while others run is not offered in IS-1.

Acceptance test (added to the enable-polarity row of the master document): with four channels armed, drop one `cnc1.N.enable`: all channels disarm cleanly, `pos_continuity` stays set, every NO opens and every NC closes; with a required channel's request low, raise `cnc1.enable`: no ARM is sent.

**Safety-interface preconditions (XS1).** CONFIGURE_IO page 1 bytes 39–53 configure them; the FPGA enforces them without the host:

| Input | Rule | Fault or event |
|---|---|---|
| RESET_ARM (XS1.5) | A press counts when it is released after `reset_arm_press_min_ms` and before `reset_arm_press_max_ms` while EXT_PERMIT is high. The release sets `reset_arm_ready` (safety word bit 30) for `reset_arm_window_ms`; ARM consumes it. With `reset_arm_required` = 1 (default) an ARM without it is refused. A longer press is "stuck" and blocks ARM while it persists | ARM_REFUSED (bit 27); SAFETY_INTERFACE event sources 0, 1, 5 |
| CONTACTOR_FB (XS1.7) | Mode 1 (NO auxiliary) or 2 (NC mirror). Must read de-energized at ARM, energized within `contactor_close_ms` after TX_PERMIT rises, de-energized within `contactor_open_ms` after it falls | CONTACTOR_FEEDBACK (bit 25): disarm all, ARM refused until SYNC with the input agreeing |
| STO_FB (XS1.8) | Mode 1: STO active exactly while PERMIT_OUT is open; mode 2: STO active while armed is a fault. Within `sto_response_ms` | STO_FEEDBACK (bit 26): disarm all, ARM refused |
| SAFETY_STATUS (XS1.4) | Diagnostic: disagreement with EXT_PERMIT longer than `chain_mismatch_ms` | SAFETY_INTERFACE event source 2, no fault |

`reset_arm_required` = 0 is accepted only when the profile declares a machine safety relay with its own manual reset feeding EXT_PERMIT (validator rule V-EL-12, section 05); the deliberate action then lives in the safety relay, and the reason is recorded in the profile. Machine-on and ARM are one operator action: the qualified release raises `cnc1.safety.reset-arm-ready`, the generated HAL turns it into `halui.machine.on`, `motion.motion-enabled` raises `cnc1.enable`, and the driver's ARM arrives inside the window (section 7.2).

### 3.5 CS_FB command (176 bytes) and FB_READ payload

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0–3 | `magic` | ascii | exactly 'CNC3' (43 4E 43 33) |  |
| 4 | `abi` | u8 | exactly 0x03 |  |
| 5 | `opcode` | u8 | listed opcode valid on this chip select |  |
| 6–7 | `channel_mask` | u16 | bits 12-15 zero; per-opcode rule |  |
| 8–11 | `session` | u32 | per-opcode rule (section 3.4) |  |
| 12–15 | `sequence` | u32 | per-opcode rule (section 3.4) |  |
| 16–173 | `payload` | bytes | opcode-specific; FB_READ: see fb_read_payload; unused bytes zero |  |
| 174–175 | `crc16` | u16 | CRC-16/CCITT-FALSE over bytes 0-173, MSB first |  |

FB_READ payload, bytes 16–173 (offsets below are relative to byte 16):

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0 | `event_ack` | u8 | sequence number of the last event record the host has stored; 0 = none | CMD.event_ack |
| 1 | `telemetry_priority_source` | u8 | telemetry source id to deliver next; 0xFF = automatic rotation; served in at most every other mirror slot (section 3.12) | CMD.telemetry_request.source |
| 2 | `telemetry_priority_page` | u8 | page of that source; ignored when source is 0xFF | CMD.telemetry_request.page |
| 3–157 | `zero` | bytes | all zero |  |

### 3.6 CNF3 feedback response (CS_FB, 176 bytes)

Sampled at the synchronized CS_FB assertion. This is the per-cycle servo status of T2: motion feedback, all machine-control inputs, output readback, latched faults and data validity for 12 motors and 12 encoders at the same time, with every expansion field present whether or not MX4 or EX8 is fitted.

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0–3 | `magic` | ascii | 'CNF3' (43 4E 46 33) |  |
| 4 | `abi` | u8 | 0x03 |  |
| 5 | `state` | u8 | b0 motion permission effective; b1 endpoint ready; b2 qualification complete; b3 config_valid; b4 io_config_valid; b5 io_enabled; b6 first-fault snapshot frozen; b7 zero | STS.state |
| 6–7 | `armed_mask` | u16 | 0 when disarmed | STS.armed_mask |
| 8–11 | `session` | u32 | current session | STS.session |
| 12–15 | `last_sequence` | u32 | last accepted sequence | STS.last_sequence |
| 16–19 | `snapshot_ticks` | u32 | core-tick timestamp of this snapshot (CS assertion) | STS.timestamp |
| 20–23 | `fault_word` | u32 | section 3.9 | STS.fault_word |
| 24–25 | `installed_mask` | u16 | motion channels installed (record rules) | STS.installed_mask |
| 26–27 | `step_timing_latched` | u16 | sticky until SYNC | STS.step_timing_latched |
| 28–29 | `alarm_levels` | u16 | filtered alarm inputs, 1 = input current flowing | STS.alarm |
| 30–31 | `alarm_trip_latched` | u16 | sticky until SYNC | STS.alarm_latched |
| 32–33 | `enable_after_gating` | u16 | logical EN_i driven to EN_N_i (commanded, not physical readback) | STS.enable_cmd_state |
| 34–35 | `pos_continuity` | u16 | section 04 4.2; 1 = no interruption since CLEAR_CONTINUITY | STS.pos_continuity |
| 36–38 | `step_count_0` | u24 | low 24 bits of the emitted-step counter of channel M0; host unwraps modulo 2^24 | STS.motor[0].position |
| 39–41 | `step_count_1` | u24 | low 24 bits of the emitted-step counter of channel M1; host unwraps modulo 2^24 | STS.motor[1].position |
| 42–44 | `step_count_2` | u24 | low 24 bits of the emitted-step counter of channel M2; host unwraps modulo 2^24 | STS.motor[2].position |
| 45–47 | `step_count_3` | u24 | low 24 bits of the emitted-step counter of channel M3; host unwraps modulo 2^24 | STS.motor[3].position |
| 48–50 | `step_count_4` | u24 | low 24 bits of the emitted-step counter of channel M4; host unwraps modulo 2^24 | STS.motor[4].position |
| 51–53 | `step_count_5` | u24 | low 24 bits of the emitted-step counter of channel M5; host unwraps modulo 2^24 | STS.motor[5].position |
| 54–56 | `step_count_6` | u24 | low 24 bits of the emitted-step counter of channel M6; host unwraps modulo 2^24 | STS.motor[6].position |
| 57–59 | `step_count_7` | u24 | low 24 bits of the emitted-step counter of channel M7; host unwraps modulo 2^24 | STS.motor[7].position |
| 60–62 | `step_count_8` | u24 | low 24 bits of the emitted-step counter of channel M8; host unwraps modulo 2^24 | STS.motor[8].position |
| 63–65 | `step_count_9` | u24 | low 24 bits of the emitted-step counter of channel M9; host unwraps modulo 2^24 | STS.motor[9].position |
| 66–68 | `step_count_10` | u24 | low 24 bits of the emitted-step counter of channel M10; host unwraps modulo 2^24 | STS.motor[10].position |
| 69–71 | `step_count_11` | u24 | low 24 bits of the emitted-step counter of channel M11; host unwraps modulo 2^24 | STS.motor[11].position |
| 72–74 | `encoder_count_0` | u24 | low 24 bits of the x4 quadrature count of ENC0; zero and invalid when not installed | STS.enc[0].count |
| 75–77 | `encoder_count_1` | u24 | low 24 bits of the x4 quadrature count of ENC1; zero and invalid when not installed | STS.enc[1].count |
| 78–80 | `encoder_count_2` | u24 | low 24 bits of the x4 quadrature count of ENC2; zero and invalid when not installed | STS.enc[2].count |
| 81–83 | `encoder_count_3` | u24 | low 24 bits of the x4 quadrature count of ENC3; zero and invalid when not installed | STS.enc[3].count |
| 84–86 | `encoder_count_4` | u24 | low 24 bits of the x4 quadrature count of ENC4; zero and invalid when not installed | STS.enc[4].count |
| 87–89 | `encoder_count_5` | u24 | low 24 bits of the x4 quadrature count of ENC5; zero and invalid when not installed | STS.enc[5].count |
| 90–92 | `encoder_count_6` | u24 | low 24 bits of the x4 quadrature count of ENC6; zero and invalid when not installed | STS.enc[6].count |
| 93–95 | `encoder_count_7` | u24 | low 24 bits of the x4 quadrature count of ENC7; zero and invalid when not installed | STS.enc[7].count |
| 96–98 | `encoder_count_8` | u24 | low 24 bits of the x4 quadrature count of ENC8; zero and invalid when not installed | STS.enc[8].count |
| 99–101 | `encoder_count_9` | u24 | low 24 bits of the x4 quadrature count of ENC9; zero and invalid when not installed | STS.enc[9].count |
| 102–104 | `encoder_count_10` | u24 | low 24 bits of the x4 quadrature count of ENC10; zero and invalid when not installed | STS.enc[10].count |
| 105–107 | `encoder_count_11` | u24 | low 24 bits of the x4 quadrature count of ENC11; zero and invalid when not installed | STS.enc[11].count |
| 108–109 | `encoder_valid_mask` | u16 | installed, qualified and supply OK, bits 0-11 | STS.enc.valid |
| 110–111 | `encoder_illegal_mask` | u16 | illegal AB transition seen, sticky until SYNC | STS.enc.illegal |
| 112–113 | `encoder_fault_mask` | u16 | port supply fault (TPS2553-1 FAULT through the EIA/EX8 status registers); a single open or shorted encoder line is not detected in IS-1 | STS.enc.fault |
| 114–115 | `index_armed_mask` | u16 | one-shot index capture armed and not yet fired | STS.enc.index_armed |
| 116–118 | `mpg_count` | u24 | low 24 bits of the handwheel x4 count | STS.mpg.count |
| 119 | `mpg_status` | u8 | b0 MPG counter valid; b1 illegal transition seen; b2 EIA status register valid; b3 EX8 status register valid; b4-7 zero | STS.mpg.status |
| 120 | `probe_status` | u8 | b0-1 filtered level P0/P1; b2-3 raw synchronized level; b4-5 capture armed; b6-7 capture overrun (sticky until SYNC) | STS.probe.state |
| 121 | `event_status` | u8 | b0-6 min(pending events,127); b7 event ring overflow (sticky until SYNC) | STS.event_status |
| 122–124 | `freq0_count` | u24 | FREQ0 counted edges, low 24 bits | STS.freq[0].count |
| 125–128 | `freq0_last_edge_ticks` | u32 | core-tick time of the last counted FREQ0 edge | STS.freq[0].last_edge |
| 129–131 | `freq1_count` | u24 | FREQ1 counted edges, low 24 bits | STS.freq[1].count |
| 132–135 | `freq1_last_edge_ticks` | u32 | core-tick time of the last counted FREQ1 edge | STS.freq[1].last_edge |
| 136–138 | `din` | u24 | DI0-DI23 after card filter, bit i = DIi; valid only with port L0 active and din_age <= din_stale_limit_us | STS.din |
| 139 | `din_age` | u8 | age of DI data at this snapshot in 10 us units; 255 = stale or never valid; DI invalid when older than din_stale_limit_us or when port L0 has latched its fault, whichever comes first | STS.din_valid |
| 140–141 | `dout_applied` | u16 | applied output state read back from DOA/DOB (bit i = DOi) | STS.dout_readback |
| 142–143 | `dout_fault_latched` | u16 | any latched fault per output | STS.dout_fault |
| 144 | `process_pwm_state` | u8 | b0-1 PEN0/1 command after gating; b2-3 PWM0/1 enabled after gating; b4 arm lamp; b5-7 zero | STS.proc_en_state |
| 145 | `aout_state` | u8 | b0-1 AO0/1 applied equals commanded (card readback); b2-3 AO0/1 zero clamp active; b4-7 zero | STS.ao.state |
| 146–147 | `ain0` | s16 | AI0 raw code (scale from the ACC factory record) | STS.ai[0].value |
| 148–149 | `ain1` | s16 | AI1 raw code | STS.ai[1].value |
| 150–151 | `ain2` | s16 | AI2 raw code | STS.ai[2].value |
| 152–153 | `ain3` | s16 | AI3 raw code | STS.ai[3].value |
| 154 | `ain_status` | u8 | b0-3 AI0-3 valid (in range, link fresh); b4-7 AI0-3 over/under range | STS.ai.valid |
| 155 | `ain_age` | u8 | age of the AI samples at this snapshot, 10 us units; 255 = stale | STS.ai.age |
| 156 | `port_status_L0_DIC` | u8 | b0-1 link state (0 down, 1 sync, 2 active, 3 fault latched); b2 identity matched; b3 card power-good (MC slot status register, section 4.10); b4 card fault; b5 outputs enabled (card report); b6 error since last FB read; b7 card watchdog tripped | STS.port[L0_DIC] |
| 157 | `port_status_L1_DOA` | u8 | b0-1 link state (0 down, 1 sync, 2 active, 3 fault latched); b2 identity matched; b3 card power-good (MC slot status register, section 4.10); b4 card fault; b5 outputs enabled (card report); b6 error since last FB read; b7 card watchdog tripped | STS.port[L1_DOA] |
| 158 | `port_status_L2_DOB` | u8 | b0-1 link state (0 down, 1 sync, 2 active, 3 fault latched); b2 identity matched; b3 card power-good (MC slot status register, section 4.10); b4 card fault; b5 outputs enabled (card report); b6 error since last FB read; b7 card watchdog tripped | STS.port[L2_DOB] |
| 159 | `port_status_L3_ACC` | u8 | b0-1 link state (0 down, 1 sync, 2 active, 3 fault latched); b2 identity matched; b3 card power-good (MC slot status register, section 4.10); b4 card fault; b5 outputs enabled (card report); b6 error since last FB read; b7 card watchdog tripped | STS.port[L3_ACC] |
| 160 | `port_status_S0_EIA` | u8 | b0-1 link state (0 down, 1 sync, 2 active, 3 fault latched); b2 identity matched; b3 card power-good (MC slot status register, section 4.10); b4 card fault; b5 outputs enabled (card report); b6 error since last FB read; b7 card watchdog tripped | STS.port[S0_EIA] |
| 161 | `port_status_S1_EX8` | u8 | b0-1 link state (0 down, 1 sync, 2 active, 3 fault latched); b2 identity matched; b3 card power-good (MC slot status register, section 4.10); b4 card fault; b5 outputs enabled (card report); b6 error since last FB read; b7 card watchdog tripped | STS.port[S1_EX8] |
| 162 | `mx4_expansion` | u8 | b0 presence A; b1 presence B; b2 EXP_PGOOD; b3-5 MOD_ID latched; b6 class matches; b7 tamper latch | STS.expansion.mx4 |
| 163 | `slot_summary` | u8 | b0 MIA qualified; b1 MX4 installed; b2 EIA qualified; b3 EX8 installed; b4 XF module present; b5 any tamper latch; b6-7 zero | STS.slots |
| 164–167 | `safety_power_word` | u32 | section 3.10 | STS.safety |
| 168 | `config_generation` | u8 | motion CONFIGURE generation | STS.config_generation |
| 169 | `io_config_generation` | u8 | CONFIGURE_IO generation | STS.io_config_generation |
| 170–171 | `pendant_inputs` | u16 | b0-9 MPG_SEL_X,Y,Z,A,B,C,MUL_X1,X10,X100,PEND_AUX; b10 MPG_ENABLE; b11 XF present; b12 XF supply fault; b13 MPG supply fault; b14-15 probe 0/1 supply fault | STS.mpg.select |
| 172 | `ex8_expansion` | u8 | same bit layout as mx4_expansion, for EX8 | STS.expansion.ex8 |
| 173 | `port_status_L4_XS` | u8 | same bit layout as port_status_L0_DIC; always 0 in IS-1: the XS slot, its FPGA pins, base contacts and IOL1 port L4 are reserved (section 02 section 8.2) but no XS module class is defined | STS.port[L4_XS] |
| 174–175 | `crc16` | u16 | CRC-16/CCITT-FALSE over bytes 0-173 |  |

### 3.7 CS_CMD command (96 bytes)

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0–3 | `magic` | ascii | exactly 'CNC3' (43 4E 43 33) |  |
| 4 | `abi` | u8 | exactly 0x03 |  |
| 5 | `opcode` | u8 | listed opcode valid on this chip select |  |
| 6–7 | `channel_mask` | u16 | bits 12-15 zero; per-opcode rule |  |
| 8–11 | `session` | u32 | per-opcode rule (section 3.4) |  |
| 12–15 | `sequence` | u32 | per-opcode rule (section 3.4) |  |
| 16–19 | `rate_0` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[0].rate |
| 20–23 | `rate_1` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[1].rate |
| 24–27 | `rate_2` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[2].rate |
| 28–31 | `rate_3` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[3].rate |
| 32–35 | `rate_4` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[4].rate |
| 36–39 | `rate_5` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[5].rate |
| 40–43 | `rate_6` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[6].rate |
| 44–47 | `rate_7` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[7].rate |
| 48–51 | `rate_8` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[8].rate |
| 52–55 | `rate_9` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[9].rate |
| 56–59 | `rate_10` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[10].rate |
| 60–63 | `rate_11` | s32 | UPDATE: \|rate\| <= min(MAX_RATE, channel clamp); zero for unmasked channels and every other opcode | CMD.motor[11].rate |
| 64–65 | `dout_image` | u16 | UPDATE/IO_WRITE/IO_CLEAR_FAULTS: DO0-DO15 requested state; zero when I/O disabled and for other opcodes; bits outside the CONFIGURE_IO enable mask zero | CMD.dout |
| 66 | `output_requests` | u8 | b0-1 PEN0/1 request; b2-3 PWM0/1 enable; b4-5 AO0/1 enable; b6 arm lamp; b7 zero | CMD.proc_en |
| 67 | `reserved_a` | u8 | zero |  |
| 68–69 | `index_arm_mask` | u16 | level request per encoder; a 0->1 change arms a one-shot index capture; bits 12-15 zero | CMD.enc.index_enable |
| 70 | `probe_arm` | u8 | b0-1 level request, 0->1 arms a one-shot capture on P0/P1; b2-7 zero | CMD.probe.arm |
| 71 | `reserved_b` | u8 | zero |  |
| 72–73 | `pwm0_duty` | u16 | 0..65535 = 0..1 of period; <= configured max duty | CMD.pwm[0].duty |
| 74–75 | `pwm1_duty` | u16 | as pwm0 | CMD.pwm[1].duty |
| 76–77 | `aout0_code` | u16 | <= configured AO0 max code | CMD.ao[0] |
| 78–79 | `aout1_code` | u16 | <= configured AO1 max code | CMD.ao[1] |
| 80–81 | `dout_fault_clear` | u16 | UPDATE, IO_WRITE or IO_CLEAR_FAULTS: outputs whose latched fault is cleared; the same bits must be 0 in dout_image; zero for other opcodes | CMD.dout_fault_clear |
| 82–93 | `zero` | bytes | all zero |  |
| 94–95 | `crc16` | u16 | CRC-16/CCITT-FALSE over bytes 0-93 |  |

The FPGA commits the twelve rates and the whole output image atomically at CS release. With I/O disabled every output field must be zero, otherwise the frame is rejected.

### 3.8 CNS3 status response (CS_CMD, 96 bytes)

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0–3 | `magic` | ascii | 'CNS3' (43 4E 53 33) |  |
| 4 | `abi` | u8 | 0x03 |  |
| 5 | `state` | u8 | as CNF3 byte 5 | STS.state |
| 6–7 | `armed_mask` | u16 |  | STS.armed_mask |
| 8–11 | `session` | u32 |  | STS.session |
| 12–15 | `last_sequence` | u32 |  | STS.last_sequence |
| 16–19 | `snapshot_ticks` | u32 | CS assertion of this CS_CMD transaction | STS.timestamp |
| 20–23 | `fault_word` | u32 | section 3.9 | STS.fault_word |
| 24–25 | `dout_image_in_force` | u16 | DO image the FPGA is sending to DOA/DOB | STS.dout_image |
| 26–27 | `dout_applied` | u16 |  | STS.dout_readback |
| 28–29 | `dout_fault_latched` | u16 |  | STS.dout_fault |
| 30–33 | `safety_power_word` | u32 | section 3.10 | STS.safety |
| 34–35 | `pos_continuity` | u16 |  | STS.pos_continuity |
| 36 | `event_seq` | u8 | 0 = no event pending; else 1..255 wrapping, skipping 0 | EVT.seq |
| 37 | `event_type` | u8 | section 3.11 | EVT.type |
| 38 | `event_source` | u8 | probe, encoder, fault bit, port or channel number | EVT.source |
| 39 | `event_flags` | u8 | per type | EVT.flags |
| 40–43 | `event_ticks` | u32 | core-tick time of the event | EVT.timestamp |
| 44–46 | `event_value0` | u24 | per type | EVT.value[0] |
| 47–49 | `event_value1` | u24 | per type | EVT.value[1] |
| 50–52 | `event_value2` | u24 | per type | EVT.value[2] |
| 53–55 | `event_value3` | u24 | per type | EVT.value[3] |
| 56 | `telemetry_source` | u8 | 0x00-0x03 ports L0-L3; 0x04 reserved for L4 (XS); 0x10 EIA status; 0x11 EX8 status; 0x80 FPGA core; 0x81-0x86 FPGA per-port counters; 0xFF none | TEL.source |
| 57 | `telemetry_page` | u8 | page number within the source | TEL.page |
| 58 | `telemetry_counter` | u8 | increments each time this source/page is refreshed in the mirror (mod 256) | TEL.counter |
| 59 | `telemetry_validity` | u8 | b0 page valid; b1 stale (mirror copy older than its source's stale limit); b2 source port faulted; b3-7 zero | TEL.validity |
| 60–63 | `telemetry_rx_ticks` | u32 | core-tick time the FPGA accepted the page | TEL.rx_timestamp |
| 64–65 | `telemetry_card_age_us` | u16 | card-reported age of the sampled values at transmission, us; 0xFFFF unknown | TEL.card_age |
| 66–75 | `telemetry_data` | bytes | page content (section 4.9) | TEL.data |
| 76–77 | `telemetry_rotation` | u16 | mirror rotation index of this entry | TEL.rotation |
| 78–79 | `last_update_interval_us` | u16 | time between the last two accepted UPDATEs, us, saturating at 65535 | STS.timing.update_interval |
| 80–81 | `late_update_count` | u16 | UPDATE intervals > 1.5 x configured servo period since SYNC, saturating | STS.timing.late_updates |
| 82–85 | `slot_status` | u32 | MC slot status register (section 4.10), two agreeing reads: b0-2 EIA presence A, presence B, power-good; b3-5 EX8; b6-8 DIC; b9-11 DOA; b12-14 DOB; b15-17 ACC; b18-20 ESC; b21-23 CMC; b24-26 XS; b27-28 SCART presence A/B; b29 register valid (marker and agreement); b30-31 zero | STS.slot_status |
| 86–93 | `zero` | bytes | all zero |  |
| 94–95 | `crc16` | u16 | CRC-16/CCITT-FALSE over bytes 0-93 |  |

### 3.9 Fault word (CNF3 and CNS3 bytes 20–23)

Bits 0–8 keep the record's meaning; bits 9–12 are section 04's additions; bits 13–24 are new here; bits 25–27 are the safety-interface faults of section 3.4a.

| Bit | Name | Cause | Response | Cleared by |
|---|---|---|---|---|
| 0 | `LINK` | host frame rejected (any rule) | disarm all; I/O disabled | SYNC |
| 1 | `WATCHDOG` | 5 ms without accepted ARM/UPDATE while armed | disarm all | SYNC |
| 2 | `INHIBIT` | external inhibit or authorization withheld | disarm all | SYNC |
| 3 | `STEP_TIMING` | DDS overflow while pulse timer busy | disarm all | SYNC |
| 4 | `DRIVE_ALARM` | alarm on an armed channel in alarm_trip_mask | disarm all | SYNC |
| 5 | `EXPANSION_CHANGED` | MX4/EX8/MIA/EIA presence, PGOOD or tamper change after qualification | disarm all, installed 0 | power cycle |
| 6 | `EXPANSION_INVALID` | invalid module state at qualification | whole machine inhibited | power cycle |
| 7 | `CONFIG_REJECTED` | CONFIGURE rejected or ARM mask != required_mask | config_valid cleared | valid CONFIGURE then SYNC |
| 8 | `MODULE_CLASS_MISMATCH` | latched MOD_ID class != expected class | ARM refused | SYNC after correct CONFIGURE |
| 9 | `OUTPUT_PATH_INTERRUPTED` | OPI_OK_TX, OPI_OK_A, OPI_OK_B or OPI_OK_BOE low while armed (section 04 4.2) | disarm all; pos_continuity cleared in that domain | SYNC, ARM, re-reference |
| 10 | `PERMISSION_PATH_STUCK` | OPI or permit readback did not follow the request | ARM refused | SYNC after service |
| 11 | `WATCHDOG_SELFTEST_FAILED` | section 04 5.4 | ARM/IO_ENABLE refused | SYNC and passing self-test |
| 12 | `AUX_SUPPLY_FAULT` | AUX24/AUX5 monitor low while armed | disarm all | SYNC |
| 13 | `IO_LINK_FAULT` | an IOL1 port or status register latched a fault | I/O disabled; motion disarmed if the port is motion-critical | SYNC |
| 14 | `IO_WATCHDOG` | 5 ms without accepted UPDATE/IO_WRITE while I/O enabled | I/O disabled | SYNC |
| 15 | `OUTPUT_READBACK_MISMATCH` | the state a card reports in response n (applied after command n-1) differs from the image the FPGA sent in command n-1, in two consecutive responses (section 4.8) | output forced off; I/O disabled if motion-critical | IO_CLEAR_FAULTS or SYNC |
| 16 | `DO_FAULT` | a card reported an output fault latch | that output forced off | IO_CLEAR_FAULTS |
| 17 | `IO_CONFIG_REJECTED` | CONFIGURE_IO rejected or card rejected CONFIG_WRITE | io_config_valid cleared | valid CONFIGURE_IO |
| 18 | `EVENT_OVERFLOW` | event ring full when a new event arrived | none on outputs; probe/index results after the overflow unusable | SYNC |
| 19 | `ENCODER_FAULT` | illegal transition or port supply fault on an encoder in required_encoder_mask while armed; a single open or shorted line is not detected in IS-1 (section 8.1) | disarm all | SYNC |
| 20 | `POWER_FAULT` | F_PGOOD_A/B, MOTION_5V, EXP_PGOOD or CORE power-good low | disarm all; I/O disabled | SYNC after supply returns |
| 21 | `SAFETY_INPUT_OPEN` | EXT_PERMIT low while armed or I/O enabled | hardware already inhibits; FPGA disarms and disables I/O | SYNC |
| 22 | `OUTPUT_PERMIT_LOST` | OPI_OK_OUT cleared (the OUT_PERMIT final gate fell, however short) or OUT_PERMIT readback low while I/O enabled | I/O disabled; FPGA_OUTPUT_REQUEST dropped; every output card has already latched its own enable off in hardware (section 4.7) and stays off until a new epoch and IO_ENABLE | SYNC, then IO_ENABLE |
| 23 | `PROCESS_PERMIT_LOST` | PROC_PERMIT fell while a PEN was requested | PEN requests cleared | SYNC |
| 24 | `SLOT_FAULT` | presence A/B or power-good of DIC, DOA, DOB, ACC, ESC, CMC or XS fell in the MC slot status register (section 4.10; two agreeing reads) | that port faulted; motion disarmed if motion-critical | SYNC |
| 25 | `CONTACTOR_FEEDBACK` | contactor_fb (XS1.7) disagrees with the expected contactor state for longer than contactor_close_ms after TX_PERMIT rose or contactor_open_ms after it fell, or the contactor does not read de-energized at ARM (CONFIGURE_IO page 1 bytes 39-49, section 3.4a) | disarm all (PERMIT_OUT opens with TX_PERMIT); ARM refused while set | SYNC after the input agrees with the disarmed state |
| 26 | `STO_FEEDBACK` | sto_fb (XS1.8) disagrees with the expected STO state for longer than sto_response_ms: mode 1, STO active exactly while PERMIT_OUT is open; mode 2, STO active while armed (section 3.4a) | disarm all; ARM refused while set | SYNC after the input agrees with the disarmed state |
| 27 | `ARM_REFUSED` | ARM received while a safety-interface precondition was unmet: no accepted RESET_ARM release within reset_arm_window_ms (when required), reset/arm held longer than reset_arm_press_max_ms, contactor not de-energized, STO state unexpected, or EXT_PERMIT low (section 3.4a) | nothing armed; a SAFETY_INTERFACE event names the unmet precondition | SYNC |

### 3.10 Safety and power word (CNF3 164–167, CNS3 30–33)

Physical sources, fault responses and HAL names of bits 0–22 are fixed by section 04 section 8; bits 23–26 are the section 03 XS1 inputs; bit 27 is the EX8 power-good from its status register; bits 28–29 are the OPI_OUT and OPI_BOE latches (section 04 section 4.2); bit 30 is `reset_arm_ready` (section 3.4a).

| Bit | Name | Bit | Name |
|---|---|---|---|
| 0 | `tx_permit` | 1 | `out_permit` |
| 2 | `proc_permit` | 3 | `wd_m_ok` |
| 4 | `wd_o_ok` | 5 | `wd_m_tripped` |
| 6 | `wd_o_tripped` | 7 | `opi_ok_tx` |
| 8 | `opi_ok_a` | 9 | `opi_ok_b` |
| 10 | `ext_permit` | 11 | `process_permit_ext` |
| 12 | `aux24_ok_a` | 13 | `aux24_ok_b` |
| 14 | `aux5_ok_a` | 15 | `aux5_ok_b` |
| 16 | `f_pgood_a` | 17 | `f_pgood_b` |
| 18 | `motion5v_pgood` | 19 | `exp_pgood` |
| 20 | `core_pgood` | 21 | `selftest_motion_ok` |
| 22 | `selftest_output_ok` | 23 | `reset_arm` |
| 24 | `chain_status` | 25 | `contactor_fb` |
| 26 | `sto_fb` | 27 | `enc_exp_pgood` |
| 28 | `opi_ok_out` | 29 | `opi_ok_boe` |
| 30 | `reset_arm_ready` | 31 | `zero` |

### 3.11 Event ring

The FPGA hardware event ring (section 04 12.2) holds 256 records of 20 bytes with 50 MHz timestamps. CNS3 bytes 36–55 always show the oldest unacknowledged record (`event_seq` 0 = empty). The host stores it, then acknowledges it with `event_ack` in the next FB_READ; the FPGA pops the record only when `event_ack` equals the sequence it last showed, so a lost CNS3 simply shows the same record again. Delivery latency is one cycle when the ring is empty and one cycle per queued record otherwise. A full ring sets EVENT_OVERFLOW and CNF3 `event_status` b7; probe and index results after an overflow are unusable.

| Type | Name | Source | Flags | Values |
|---|---|---|---|---|
| 0x01 | PROBE_CAPTURE | probe 0/1 | b0 edge was rising; b1 overrun before this event | the four configured capture sources (u24 each) latched on the same core tick as the qualified edge |
| 0x02 | INDEX_CAPTURE | encoder 0-11 | 0 | v0 x4 count at the synchronized index rising edge (u24); v1-v3 zero |
| 0x03 | FAULT_LATCHED | lowest newly set fault bit | 0 | v0 fault_word[23:0]; v1 fault_word[31:24]<<16 \| armed_mask; v2 safety word[23:0]; v3 safety word[31:24]<<16 \| pos_continuity |
| 0x04 | PORT_FAULT | port 0-3, 0x10 EIA, 0x11 EX8 | cause 1 CRC, 2 format/length/timeout, 3 sequence/epoch, 4 identity, 5 readback, 6 card watchdog, 7 card reset | v0 consecutive failures; v1 total failures (low 24 bits) |
| 0x05 | OUTPUT_FAULT | output 0-15 | b0 overcurrent/current limit; b1 thermal; b2 open load on; b3 open load off; b4 short to VS | v0 last ISNS code of that output, 0xFFFFFF if not measured |
| 0x06 | DEADLINE | 0 | 0 | v0 UPDATE interval us; v1 configured servo period us; v2 sequence low 24 bits |
| 0x07 | WATCHDOG_TRIP | 0 WD_M, 1 WD_O | 0 | v0 core ticks since the last progress pulse (low 24 bits) |
| 0x08 | OPI | 0 TX, 1 A, 2 B, 3 BOE (bank-B Ioff-buffer OE), 4 OUT | b0 armed at the time | 0 |
| 0x09 | SLOT_CHANGE | slot id (MIR-1 class code of the slot; 0x20 = XF measurement module presence) | b0 presence A; b1 presence B; b2 PGOOD; b3 tamper | 0 |
| 0x0A | SUPPLY_CHANGE | safety-word bit number | b0 new level | 0 |
| 0x0B | SAFETY_INPUT_CHANGE | safety-word bit number | b0 new level | 0 |
| 0x0C | SAFETY_INTERFACE | 0 reset/arm release accepted; 1 reset/arm held too long (stuck); 2 chain status disagrees with EXT_PERMIT longer than chain_mismatch_ms; 3 contactor feedback mismatch; 4 STO feedback mismatch; 5 ARM refused (flags name the precondition) | source 5: b0 no reset/arm release, b1 contactor, b2 STO, b3 EXT_PERMIT low, b4 reset/arm stuck; other sources: b0 new level | v0 duration in ms (press time, mismatch time); v1-v3 zero |

### 3.12 Telemetry mirror

The FPGA keeps the latest copy of every card telemetry page, of the status registers and of its own counter pages, each with the core-tick time it was accepted and the card-reported age of the values. Each CNS3 carries one 22-byte entry (bytes 56–77) in a fixed round robin over all entries. A host priority request in FB_READ bytes 17–18 (for a value a screen is showing) may take **at most every other slot**, so it can never starve the rotation. The IS-1 default fit (DIC 3 pages, DOA 12, DOB 12, ACC 8, EIA 1, EX8 1, FPGA core 2, FPGA port counters 6) has **45 entries**, so every entry is delivered at least every 45 ms (about 22 Hz) without priority requests and at least every **90 ms** (about 11 Hz) with them [AR]. Output current, temperature and VOUT are therefore at most 90 ms delivery + 3.05 ms card sample age = **93.05 ms** old at the host [AR on REQ], inside their 100 ms stale limit. Page contents are in section 4.9.

Age of a telemetry value at display = display time − (FPGA accept time − card-reported age). The driver publishes that age with every value. **One stale rule (T4):** each source has one fixed stale limit, `stale_ms` in the telemetry map and host-source tables of section 8.1a (100 ms for output-card values, 200 ms for slow supply and temperature values, 500 ms for host-I2C entry monitors, 5 s for 1 Hz host temperatures) [REQ]; a value older than its limit is shown stale, a source without a path is unavailable, and neither is ever shown as zero. Section 03 section 6 cites this rule.

### 3.13 CONFIGURE and CONFIGURE_IO

Both are sent on CS_FB (176-byte command capacity) while disarmed with I/O disabled, and both keep the record's rule that a rejected configuration clears the corresponding `*_config_valid`, so nothing configured earlier survives a failed reconfiguration.

CONFIGURE payload (opcode 0x06), relative to byte 16:

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0 | `format` | u8 | 0x02 (IS-1); 0x01 was the record's draft and is rejected |  |
| 1 | `expected_module_class` | u8 | 0 or a class listed in CAP3 page 0 byte 56 (1 = MX4) |  |
| 2–3 | `required_mask` | u16 | nonzero; subset of installed_mask; bits 8-11 only with expected_module_class != 0 |  |
| 4–5 | `alarm_trip_mask` | u16 | subset of required_mask |  |
| 6–7 | `alarm_on_no_current` | u16 | bits 12-15 zero |  |
| 8–15 | `timing_0` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 16–23 | `timing_1` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 24–31 | `timing_2` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 32–39 | `timing_3` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 40–47 | `timing_4` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 48–55 | `timing_5` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 56–63 | `timing_6` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 64–71 | `timing_7` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 72–79 | `timing_8` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 80–87 | `timing_9` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 88–95 | `timing_10` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 96–103 | `timing_11` | 4 x u16 | STEP high, STEP low min, DIR setup, DIR hold, core ticks, each in [100, 1023] |  |
| 104–107 | `config_hash` | u32 | opaque, echoed in FLT3/IDP3 pages |  |
| 108–109 | `servo_period_us` | u16 | 250..2500; used only for late-UPDATE counting; the 5 ms watchdog is fixed |  |
| 110 | `expected_encoder_expansion_class` | u8 | 0 none, 1 EX8 |  |
| 111 | `encoder_filter_ticks` | u8 | 0..15 core ticks of AB/Z glitch filter |  |
| 112–113 | `required_encoder_mask` | u16 | encoders an armed joint depends on; bits 4-11 need EX8; ARM refused unless all valid |  |
| 114 | `mpg_config` | u8 | b0 MPG counter enabled; b1-3 MPG filter ticks/4; b4-7 zero |  |
| 115–157 | `zero` | bytes | all zero |  |

CONFIGURE_IO page 0 (opcode 0x07), relative to byte 16:

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0 | `page` | u8 | 0 |  |
| 1–4 | `expected_port_class` | 4 x u8 | class expected on L0-L3 (0 = no card expected; section 4.2) |  |
| 5 | `required_port_mask` | u8 | b0-3 L0-L3, b4 EIA status, b5 EX8 status; IO_ENABLE refused unless all active |  |
| 6 | `motion_critical_port_mask` | u8 | a fault on these ports also disarms motion (default 0x3F) |  |
| 7–8 | `dout_enable_mask` | u16 | outputs the host may command; others must stay 0 |  |
| 9 | `output_function_mask` | u8 | b0-1 PEN0/1 usable; b2-3 PWM0/1; b4-5 AO0/1; b6 arm lamp |  |
| 10–13 | `io_config_hash` | u32 | opaque, echoed |  |
| 14–15 | `din_stale_limit_us` | u16 | 250..440; default 440; DI invalid when older than this at the snapshot or when port L0 has latched its fault, whichever comes first (section 5.3) |  |
| 16–17 | `ain_stale_limit_us` | u16 | 250..440; default 440; AI invalid when older than this at the snapshot or when port L3 has latched its fault, whichever comes first (section 5.3) |  |
| 18 | `expected_port_class_L4` | u8 | 0 in IS-1 (no XS module class defined); nonzero is rejected until a revision defines a class |  |
| 19–157 | `zero` | bytes | all zero |  |

CONFIGURE_IO page 1:

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0 | `page` | u8 | 1 |  |
| 1 | `probe0_flags` | u8 | b0 active-high; b1-7 zero |  |
| 2 | `probe0_filter_ticks` | u8 | 0..255 core ticks |  |
| 3–6 | `probe0_capture_sources` | 4 x u8 | 0x00-0x0B step count Mi; 0x10-0x1B encoder ENCk; 0x20 MPG; 0xFF none |  |
| 7 | `probe1_flags` | u8 | as probe0 |  |
| 8 | `probe1_filter_ticks` | u8 |  |  |
| 9–12 | `probe1_capture_sources` | 4 x u8 |  |  |
| 13 | `freq0_flags` | u8 | b0 count falling instead of rising; b1-7 zero |  |
| 14 | `freq0_filter_ticks` | u8 | 0..15 |  |
| 15–16 | `freq0_no_signal_ms` | u16 | 1..10000; no edge for this long => NO_SIGNAL (never shown as 0 Hz) |  |
| 17 | `freq1_flags` | u8 |  |  |
| 18 | `freq1_filter_ticks` | u8 |  |  |
| 19–20 | `freq1_no_signal_ms` | u16 |  |  |
| 21–24 | `pwm0_period_ticks` | u32 | 50..50,000,000 (1 Hz..1 MHz) |  |
| 25–26 | `pwm0_max_duty` | u16 | clamp; commands above it are rejected |  |
| 27 | `pwm0_flags` | u8 | zero: IS-1 has no inverted PWM; the hardware-inhibited level (low) must be the connected device's off level (section 04 section 9) |  |
| 28–31 | `pwm1_period_ticks` | u32 |  |  |
| 32–33 | `pwm1_max_duty` | u16 |  |  |
| 34 | `pwm1_flags` | u8 | zero: IS-1 has no inverted PWM; the hardware-inhibited level (low) must be the connected device's off level (section 04 section 9) |  |
| 35–36 | `aout0_max_code` | u16 | commands above it are rejected |  |
| 37–38 | `aout1_max_code` | u16 |  |  |
| 39 | `safety_if_flags` | u8 | b0 reset_arm_required (default 1: ARM needs an accepted RESET_ARM release; 0 only when the profile declares a machine safety relay with its own manual reset feeding EXT_PERMIT, validator rule V-EL-12); b1-2 contactor_fb_mode (0 not used, 1 NO auxiliary contact closed = energized, 2 NC mirror contact closed = de-energized); b3-4 sto_fb_mode (0 not used, 1 follows PERMIT_OUT, 2 status only: STO active while armed is a fault); b5 sto_fb_active_high (1 = input current flowing means STO active); b6-7 zero |  |
| 40–41 | `reset_arm_window_ms` | u16 | 500..10000, default 5000: an accepted release enables one ARM within this time |  |
| 42–43 | `reset_arm_press_min_ms` | u16 | 20..2000, default 50: shorter presses are ignored |  |
| 44–45 | `reset_arm_press_max_ms` | u16 | 100..5000, default 5000: a longer press is 'stuck', never an arm request (SAFETY_INTERFACE event source 1) |  |
| 46–47 | `contactor_close_ms` | u16 | 10..2000: contactor must read energized within this time after TX_PERMIT rises |  |
| 48–49 | `contactor_open_ms` | u16 | 10..2000: contactor must read de-energized within this time after TX_PERMIT falls |  |
| 50–51 | `sto_response_ms` | u16 | 1..2000: STO feedback must reach its expected state within this time |  |
| 52–53 | `chain_mismatch_ms` | u16 | 10..5000: chain status disagreeing with EXT_PERMIT for longer than this is reported (diagnostic event, no fault) |  |
| 54–157 | `zero` | bytes | all zero |  |

CONFIGURE_IO pages 2–9 forward card configuration (section 4.4) to one port; the card validates it, applies it only in the SYNCED state and reports its CRC-32C, which the host compares with the stored record:

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0 | `page` | u8 | 2..9 |  |
| 1 | `port` | u8 | 0..3 |  |
| 2 | `blob_index` | u8 | 0..7 |  |
| 3–26 | `card_config` | bytes | class-specific configuration forwarded verbatim in a CONFIG_WRITE link frame (section 4.8) |  |
| 27–157 | `zero` | bytes | all zero |  |

### 3.14 Pages returned on CS_FB after READ_PAGE

Page 0 (motion capabilities; the record's §5.6 content, relocated and extended):

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0–3 | `magic` | ascii | 'CAP3' |  |
| 4 | `abi` | u8 | 3 |  |
| 5 | `page` | u8 | 0 |  |
| 6 | `step_channels` | u8 | 12 |  |
| 7 | `installed_channels` | u8 | 0, 8 or 12 |  |
| 8 | `encoders_supported` | u8 | 12 |  |
| 9 | `encoders_base` | u8 | 4 |  |
| 10 | `encoders_installed` | u8 | 4 or 12 (0 while unqualified) |  |
| 11 | `mpg_ports` | u8 | 1 |  |
| 12–15 | `feature_bitmap` | u32 | b0 STEP; b1 AB; b2 index one-shot; b3 atomic update; b4 watchdog; b5 per-channel enable; b6 per-channel alarm; b7 bank B; b8 runtime timing; b9 required-mask ARM; b10 alarm trip; b11 pos_continuity; b12 OPI; b13 watchdog self-test; b14 event ring; b15 telemetry mirror; b16 two chip selects |  |
| 16–19 | `core_hz` | u32 | 50,000,000 |  |
| 20–23 | `max_rate` | u32 | 0x01000000 |  |
| 24–31 | `reference_timing` | 4 x u16 | 100/100/100/100 |  |
| 32–33 | `timing_min` | u16 | 100 |  |
| 34–35 | `timing_max` | u16 | 1023 |  |
| 36–39 | `watchdog_ticks` | u32 | 250,000 |  |
| 40–41 | `alarm_sample_ticks` | u16 | 500 |  |
| 42 | `filter_samples` | u8 | 4 |  |
| 43 | `zero_a` | u8 | 0 |  |
| 44–45 | `fb_frame_bytes` | u16 | 176 |  |
| 46–47 | `cmd_frame_bytes` | u16 | 96 |  |
| 48 | `min_sclk_divider` | u8 | 8 |  |
| 49 | `bank_count` | u8 | 2 |  |
| 50–53 | `bank_layout` | 4 x u8 | 0,8,8,4 |  |
| 54 | `expansion_state` | u8 | record 5.6 byte 52 semantics |  |
| 55 | `mod_id_latched` | u8 | bits 2:0 |  |
| 56 | `accepted_module_class` | u8 | 1 (MX4) |  |
| 57 | `accepted_encoder_expansion_class` | u8 | 1 (EX8) |  |
| 58–59 | `zero_b` | u16 | 0 |  |
| 60–63 | `qualification_ticks` | u32 | 1,048,576 |  |
| 64–67 | `gateware_build_id` | u32 | build identifier |  |
| 68–71 | `spec_revision` | ascii | 'IS-1' |  |
| 72–73 | `event_ring_depth` | u16 | 256 |  |
| 74–75 | `telemetry_entries` | u16 | number of mirror entries |  |
| 76–77 | `progress_pulse_ticks` | u16 | 50 (1 us, section 04 5.1) |  |
| 78–79 | `zero_c` | u16 | 0 |  |
| 80–173 | `zero` | bytes | 0 |  |
| 174–175 | `crc16` | u16 | CRC over 0-173 |  |

Page 1 (I/O capabilities):

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0–3 | `magic` | ascii | 'CAP3' |  |
| 4 | `abi` | u8 | 3 |  |
| 5 | `page` | u8 | 1 |  |
| 6 | `din_count` | u8 | 24 |  |
| 7 | `dout_count` | u8 | 16 |  |
| 8 | `probe_count` | u8 | 2 |  |
| 9 | `freq_count` | u8 | 2 |  |
| 10 | `pwm_count` | u8 | 2 |  |
| 11 | `process_enable_count` | u8 | 2 |  |
| 12 | `aout_count` | u8 | 2 |  |
| 13 | `ain_count` | u8 | 4 |  |
| 14 | `link_ports` | u8 | 4 |  |
| 15 | `status_registers` | u8 | 2 |  |
| 16–19 | `io_feature_bitmap` | u32 | b0 IOL1 link; b1 output readback; b2 card telemetry; b3 port passthrough (MAINT); b4 probe capture; b5 reciprocal frequency |  |
| 20–21 | `link_period_us` | u16 | 100 |  |
| 22 | `link_sclk_divider` | u8 | 6 (8.333 MHz) |  |
| 23 | `link_frame_bytes` | u8 | 40 |  |
| 24 | `link_crc_id` | u8 | 1 = CRC-32C |  |
| 25 | `card_accept_timeout_periods` | u8 | 10 |  |
| 26 | `port_fault_threshold` | u8 | 3 |  |
| 27 | `zero_a` | u8 | 0 |  |
| 28–31 | `io_watchdog_ticks` | u32 | 250,000 |  |
| 32–35 | `pwm_min_period_ticks` | u32 | 50 |  |
| 36–39 | `accepted_port_classes` | 4 x u8 | 0x11, 0x21, 0x21, 0x31 |  |
| 40–173 | `zero` | bytes | 0 |  |
| 174–175 | `crc16` | u16 | CRC over 0-173 |  |

Page 2 (first-fault snapshot, frozen at the first latched fault until SYNC):

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0–3 | `magic` | ascii | 'FLT3' |  |
| 4 | `abi` | u8 | 3 |  |
| 5 | `page` | u8 | 2 |  |
| 6–7 | `armed_mask_at_fault` | u16 |  |  |
| 8–11 | `session` | u32 |  |  |
| 12–15 | `last_sequence` | u32 |  |  |
| 16–19 | `fault_ticks` | u32 | core-tick time of the first latched fault |  |
| 20–23 | `fault_word_at_freeze` | u32 |  |  |
| 24–27 | `first_fault_bits` | u32 | bits that set in the first faulting tick |  |
| 28–31 | `safety_power_word` | u32 |  |  |
| 32–35 | `rate_in_force_0` | s32 |  |  |
| 36–39 | `rate_in_force_1` | s32 |  |  |
| 40–43 | `rate_in_force_2` | s32 |  |  |
| 44–47 | `rate_in_force_3` | s32 |  |  |
| 48–51 | `rate_in_force_4` | s32 |  |  |
| 52–55 | `rate_in_force_5` | s32 |  |  |
| 56–59 | `rate_in_force_6` | s32 |  |  |
| 60–63 | `rate_in_force_7` | s32 |  |  |
| 64–67 | `rate_in_force_8` | s32 |  |  |
| 68–71 | `rate_in_force_9` | s32 |  |  |
| 72–75 | `rate_in_force_10` | s32 |  |  |
| 76–79 | `rate_in_force_11` | s32 |  |  |
| 80–82 | `step_count_0` | u24 |  |  |
| 83–85 | `step_count_1` | u24 |  |  |
| 86–88 | `step_count_2` | u24 |  |  |
| 89–91 | `step_count_3` | u24 |  |  |
| 92–94 | `step_count_4` | u24 |  |  |
| 95–97 | `step_count_5` | u24 |  |  |
| 98–100 | `step_count_6` | u24 |  |  |
| 101–103 | `step_count_7` | u24 |  |  |
| 104–106 | `step_count_8` | u24 |  |  |
| 107–109 | `step_count_9` | u24 |  |  |
| 110–112 | `step_count_10` | u24 |  |  |
| 113–115 | `step_count_11` | u24 |  |  |
| 116–117 | `alarm_levels` | u16 |  |  |
| 118–119 | `enable_after_gating` | u16 |  |  |
| 120–125 | `port_status` | 6 x u8 |  |  |
| 126–127 | `last_update_interval_us` | u16 |  |  |
| 128–129 | `pos_continuity` | u16 |  |  |
| 130–131 | `dout_image` | u16 |  |  |
| 132–133 | `dout_applied` | u16 |  |  |
| 134–135 | `dout_fault` | u16 |  |  |
| 136–139 | `fault_count_since_reset` | u32 |  |  |
| 140–143 | `config_hash` | u32 |  |  |
| 144–173 | `zero` | bytes | 0 |  |
| 174–175 | `crc16` | u16 |  |  |

Page 3 (card identity collected from IOL1 IDENT_READ frames):

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0–3 | `magic` | ascii | 'IDP3' |  |
| 4 | `abi` | u8 | 3 |  |
| 5 | `page` | u8 | 3 |  |
| 6–7 | `port_valid_mask` | u16 |  |  |
| 8–11 | `snapshot_ticks` | u32 |  |  |
| 12–15 | `zero_a` | bytes | 0 |  |
| 16 | `L0_class` | u8 |  |  |
| 17 | `L0_hw_revision` | u8 |  |  |
| 18–19 | `L0_fw_version` | u16 |  |  |
| 20–23 | `L0_serial` | u32 |  |  |
| 24–27 | `L0_factory_record_crc32` | u32 |  |  |
| 28–31 | `L0_applied_config_crc32` | u32 |  |  |
| 32 | `L0_reset_cause` | u8 | b0 power-on; b1 brown-out; b2 IWDG; b3 software; b4 pin |  |
| 33 | `L0_bootloader_version` | u8 |  |  |
| 34 | `L0_card_state` | u8 |  |  |
| 35 | `L0_slot_straps` | u8 |  |  |
| 36–37 | `L0_capability_bits` | u16 |  |  |
| 38–41 | `L0_zero` | bytes | 0 |  |
| 42 | `L1_class` | u8 |  |  |
| 43 | `L1_hw_revision` | u8 |  |  |
| 44–45 | `L1_fw_version` | u16 |  |  |
| 46–49 | `L1_serial` | u32 |  |  |
| 50–53 | `L1_factory_record_crc32` | u32 |  |  |
| 54–57 | `L1_applied_config_crc32` | u32 |  |  |
| 58 | `L1_reset_cause` | u8 | b0 power-on; b1 brown-out; b2 IWDG; b3 software; b4 pin |  |
| 59 | `L1_bootloader_version` | u8 |  |  |
| 60 | `L1_card_state` | u8 |  |  |
| 61 | `L1_slot_straps` | u8 |  |  |
| 62–63 | `L1_capability_bits` | u16 |  |  |
| 64–67 | `L1_zero` | bytes | 0 |  |
| 68 | `L2_class` | u8 |  |  |
| 69 | `L2_hw_revision` | u8 |  |  |
| 70–71 | `L2_fw_version` | u16 |  |  |
| 72–75 | `L2_serial` | u32 |  |  |
| 76–79 | `L2_factory_record_crc32` | u32 |  |  |
| 80–83 | `L2_applied_config_crc32` | u32 |  |  |
| 84 | `L2_reset_cause` | u8 | b0 power-on; b1 brown-out; b2 IWDG; b3 software; b4 pin |  |
| 85 | `L2_bootloader_version` | u8 |  |  |
| 86 | `L2_card_state` | u8 |  |  |
| 87 | `L2_slot_straps` | u8 |  |  |
| 88–89 | `L2_capability_bits` | u16 |  |  |
| 90–93 | `L2_zero` | bytes | 0 |  |
| 94 | `L3_class` | u8 |  |  |
| 95 | `L3_hw_revision` | u8 |  |  |
| 96–97 | `L3_fw_version` | u16 |  |  |
| 98–101 | `L3_serial` | u32 |  |  |
| 102–105 | `L3_factory_record_crc32` | u32 |  |  |
| 106–109 | `L3_applied_config_crc32` | u32 |  |  |
| 110 | `L3_reset_cause` | u8 | b0 power-on; b1 brown-out; b2 IWDG; b3 software; b4 pin |  |
| 111 | `L3_bootloader_version` | u8 |  |  |
| 112 | `L3_card_state` | u8 |  |  |
| 113 | `L3_slot_straps` | u8 |  |  |
| 114–115 | `L3_capability_bits` | u16 |  |  |
| 116–119 | `L3_zero` | bytes | 0 |  |
| 120–173 | `zero` | bytes | 0 |  |
| 174–175 | `crc16` | u16 |  |  |

Every card's AT30TSE752A MIR-1 identity record (section 02 section 9) and the XF 1-Wire identity are read by the host over the identity I2C branches, never relayed through CNC1.

### 3.15 Output-path interruption and position validity (correction 2)

The rule and its hardware are section 04 section 4. What the protocol adds:

- A commanded DISARM is a clean stop at a pulse boundary; `pos_continuity` stays set only if every masked channel finished its pulse and DIR hold.
- Every other disarm (rejected frame, watchdog, alarm, OPI, supply, safety input, encoder or I/O fault on a motion-critical port) clears `pos_continuity` for the affected channels, and CNF3/CNS3 carry the result in every cycle. The driver drives `halui.joint.J.unhome` for every joint J that contains an affected channel (joint index from the channel-to-joint map, section 7.2).
- A noise pulse rejected by a filter changes no output: every presence, power-good, tamper and alarm input passes the 30–40 µs qualification filter before the FPGA acts on it, every hardware gate uses the qualified net (section 04 4.2), and the counting inputs (encoders, probes, frequency, handwheel) have their own glitch filters and never gate an output. No protocol state exists in which outputs are blanked and then resume.
- A late UPDATE is not an interruption: the previous validated rates stay in force until the 5 ms watchdog, the interval is counted (`late_update_count`, DEADLINE event), and the watchdog expiry is a latched fault with continuity cleared.
- Card-side: an IOL1 frame that fails validation changes no output (section 4.6).

### 3.16 Versioning and reference vectors

`spec_revision` "IS-1" appears in CAP3 page 0 bytes 68–71 and in `spec/protocol.json`. The ABI byte changes only when a layout changes incompatibly; IS-2 may add fields in reserved bytes with a new CAP3 feature bit. ABI v1 and v2 builds stay buildable as historical evidence and are never negotiated with ABI 3.

Reference vectors (Python `binascii.crc_hqx` and a bitwise CRC-32C; arithmetic, not RTL output):

| Vector | Bytes | Start of frame (hex) | CRC |
|---|---|---|---|
| `fb_read_session0` | 176 | `434e43330310000000000000000000000000…` | `0x4CFC` |
| `read_page0` | 176 | `434e43330305000000000000000000000000…` | `0x1724` |
| `sync_session1` | 96 | `434e43330301000000000001000000000000…` | `0xD968` |
| `nop_cmd` | 96 | `434e43330300000000000000000000000000…` | `0x2222` |
| `update_8ch_do5` | 96 | `434e4333030300ff00000001000000030000…` | `0xA792` |
| `iol1_sync_doa` | 40 | `a70121010001000001ff0000000000000000…` | `0x8FEB9757` |

Full frames are in `spec/protocol.json` (`crc.vectors`). They are format vectors: `update_8ch_do5` also needs the matching session state and I/O enabled to be accepted.

## 4. Card link: IOL1

### 4.1 Topology and electrical requirement

Point-to-point from the motion card, one FPGA SPI master per card slot, four wires per port: SCLK, CMD (FPGA → card), RSP (card → FPGA), CS_N. 3.3 V LVCMOS with an Ioff buffer and series termination at each card connector (power-off service; no back-powering of an unpowered card). SPI mode 0, MSB first. SCLK = core/6 = **8.333 MHz** (60 ns high, 60 ns low), below the STM32G031's 32 Mbit/s SPI slave rating [DS]. The FPGA samples RSP on the rising SCLK edge; the round trip (FPGA SCLK out → buffers → card output → buffers → FPGA input) must be < 60 ns [REQ]. If timing analysis or measurement shows it is not, the gateware delays its sampling point by whole core ticks (a build option that changes no frame format); SCLK is not raised. Each port runs one transaction every **100 µs**. A card failure cannot block another card's link.

### 4.2 Ports and card classes

| Port | Card (section 03) | Class | Slot straps | MCU |
|---|---|---|---|---|
| L0 | DIC, DI0–DI23 and sensor/safety supply monitors | 0x11 | 0 | STM32G031C8T6 (LQFP48) [DS, DigiKey listing] |
| L1 | DOA, DO0–DO7, 2 × TPS274C65ASRHAR | 0x21 | 1 | STM32G031K8T6 (LQFP32) [DS] |
| L2 | DOB, DO8–DO15, identical part number to DOA | 0x21 | 2 | STM32G031K8T6 |
| L3 | ACC, AO0–1, AI0–3 and ACC monitors (RS-485/CAN transceivers are wired to the host, section 7.3) | 0x31 | 3 | STM32G031K8T6 |

DOA and DOB are one part number; the base's slot straps make them distinct, and a DO8 card answers only to the slot it reads. A card in its bootloader reports class 0x7F. The output driver is the T1 selection of section 02 section 11.2, **TPS274C65ASRHAR** (two per DO8 card, addressable SPI behind one ISO7762FDBQR isolator); the DO8 realtime and telemetry bytes below are defined for that part. A different driver would need a new class number and a new revision.

### 4.3 Frame layout (40 bytes each direction)

Command (FPGA → card):

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0 | `sof` | u8 | 0xA7 |  |
| 1 | `version` | u8 | 0x01 |  |
| 2 | `expected_class` | u8 | must equal the card's own class |  |
| 3 | `expected_slot` | u8 | b0-3 slot id; b4-7 zero; must equal the base straps read by the card |  |
| 4–5 | `epoch` | u16 | nonzero; changes on every link (re)start |  |
| 6–7 | `sequence` | u16 | 0 only in SYNC frames; otherwise last+1, wrapping 0xFFFF -> 0x0001 |  |
| 8 | `control` | u8 | b0 SYNC; b1 OUT_REQ; b2 CLEAR_FAULTS; b3 IDENT_READ; b4 CONFIG_WRITE; b5 MAINT; b6-7 zero |  |
| 9 | `telemetry_request` | u8 | page to return next; 0xFF = card rotation |  |
| 10–35 | `payload` | bytes | class-specific (section 4.4) |  |
| 36–39 | `crc32c` | u32 | CRC-32C over bytes 0-35, MSB first |  |

Response (card → FPGA), prepared by the card before the transaction starts:

| Bytes | Field | Type | Rule | Logical name |
|---|---|---|---|---|
| 0 | `sof` | u8 | 0x7A |  |
| 1 | `version` | u8 | 0x01 |  |
| 2 | `class` | u8 | card's factory class |  |
| 3 | `slot` | u8 | b0-3 slot straps read from the base; b4-7 hardware major revision |  |
| 4–5 | `epoch_echo` | u16 | epoch of the last accepted frame |  |
| 6–7 | `sequence_echo` | u16 | sequence of the last accepted frame |  |
| 8 | `card_state` | u8 | b0-2 state (0 INIT, 1 SYNCED, 2 ACTIVE, 3 FAULT_LATCHED, 4 CONFIG_INVALID, 7 BOOT); b3 OUT_PERMIT seen; b4 outputs enabled; b5 field supply OK; b6 card fault; b7 reset cause pending |  |
| 9 | `telemetry_page` | u8 | page carried in bytes 26-35 |  |
| 10–25 | `realtime` | bytes | class-specific (section 4.4) |  |
| 26–35 | `telemetry` | bytes | class-specific page (section 4.9) |  |
| 36–39 | `crc32c` | u32 | CRC-32C over bytes 0-35 |  |

### 4.4 Class payloads

| Class | Card | Port | MCU | Command payload (bytes 10–35) | Realtime payload (response bytes 10–25) | Configuration blob (24 B) |
|---|---|---|---|---|---|---|
| 0x11 | DIC | L0 | STM32G031C8T6 (LQFP48) | all zero in ACTIVE; CONFIG_WRITE: blob index + 24 B | 0-2 DI filtered (24 bits); 3-5 DI raw; 6-7 sample age us; 8 sensor-group limiter fault bits; 9 safety-supply fault bits; 10-15 zero | 0 format 1; 1-3 debounce per 8-input group, 100 us units (0-255); 4-23 zero |
| 0x21 | DO8 (DOA slot 1, DOB slot 2) | L1, L2 | STM32G031K8T6 (LQFP32) | 0 output image (8 bits); 1 fault-clear mask; 2-25 zero | 0 applied (SW_STATE readback AND driver enable); 1 fault any; 2 overcurrent/current limit; 3 thermal; 4 open load on; 5 open load off; 6 short to VS; 7 b0-1 FLT pins, b2-3 VS undervoltage dev0/1, b4-5 SPI/CRC error dev0/1, b6 OUT_PERMIT drop latched (OUT_EN latch cleared); 8-9 readback age us; 10-15 zero | 0 format 1; 1-8 ILIM_REG[3:0] code per output: default 0110 = 0.72 A setting (0.62-0.82 A [DS Table 8-4 and ICL table]); codes above 0111 (0.85 A setting, 0.72-1.00 A [DS]) are rejected so the limit never exceeds section 04's 1.0 A maximum; 9 on-state open-load enable mask; 10 off-state open-load enable mask; 11 inrush code: INRUSH_LIMIT 00 (same limit) or 10 (0.5x) only; 01 (2x) and 11 (fixed 2.2 A) are rejected; 12 latch-off (retry disable) mask; 13-23 zero |
| 0x31 | ACC | L3 | STM32G031K8T6 (LQFP32) | 0-1 AO0 code; 2-3 AO1 code; 4 b0-1 AO enable; 5-25 zero | 0-1 AO0 applied (DAC register readback); 2-3 AO1 applied; 4-5 AI0; 6-7 AI1; 8-9 AI2; 10-11 AI3; 12-13 AI sample age us; 14 AI valid/range bits; 15 AO status (b0-1 clamp, b2-3 readback ok, b4 DAC reference alarm, b5 OUT_PERMIT drop latched, b6 PROC_PERMIT drop latched) | 0 format 1; 1-4 AI range code per channel; 5 AI sample-rate code (>= 1 kHz per channel); 6 RS-485 termination; 7 CAN termination; 8-23 zero |
| 0x7F | BOOT (any card in its bootloader) | any | - | MAINT update records | bootloader status; IWDG refreshed by the SRAM erase/program routine; outputs off | - |

### 4.5 CRC-32C and its Hamming distance

CRC-32C (Castagnoli; poly 0x1EDC6F41, init 0xFFFFFFFF, reflected in and out, final XOR 0xFFFFFFFF; `123456789` → 0xE3069283) over bytes 0–35, stored MSB first in bytes 36–39. At the 320-bit codeword (288 data bits) an exhaustive syndrome search [AR] finds **no undetected error pattern of weight ≤ 5** and finds weight-6 patterns: **HD 6**. Every burst up to 32 bits is detected (degree-32 generator). At the same length CRC-32/IEEE gives HD 5 and CRC-16/CCITT HD 4 [AR]. The STM32G0 CRC unit computes it with a programmable polynomial and input/output reversal [DS, RM0444]; the FPGA streams it bitwise.

### 4.6 Validate before commit

**Card side.** A command frame changes outputs only after all of these pass, in this order: complete 40-byte frame with CS released after exactly 320 clocks and no SPI overrun; CRC-32C; SOF 0xA7 and version 0x01; `expected_class` equals the card's own class; `expected_slot` equals the slot straps the card reads from the base; `epoch` equals the current epoch (a SYNC frame: new nonzero epoch with sequence 0); `sequence` = last + 1 (0xFFFF → 0x0001); reserved bits and bytes zero; class checks (output bits only inside the configured mask, AO code ≤ configured maximum, OUT_REQ only with OUT_PERMIT seen high). Only then does the card apply the output image, reload its accept timer, refresh its IWDG and store the epoch and sequence. A frame that fails any check changes nothing and increments the matching card-side counter.

**FPGA side.** A card response is used only after its CRC, SOF, class, slot, epoch echo and sequence echo check. Three consecutive failures on a port latch the port fault (IO_LINK_FAULT, PORT_FAULT event); DI and AI keep their last valid value with a growing age and become invalid at their stale limit (never reported as low or zero).

### 4.7 Card watchdogs and hardware gates

- **Accept timer:** firmware timer reloaded only on a fully accepted frame; 1.0 ms (10 link periods, within section 04's ≥ 3 periods and ≤ 2 ms). Expiry: outputs off (DO SW_STATE = 0, AO to the zero clamp), state FAULT_LATCHED until the FPGA starts a new epoch.
- **IWDG:** the STM32G0 independent watchdog (own clock), hardware-started by option byte; in the application it is refreshed only in the accept path. Its maximum timeout must be ≤ 2 ms over the LSI tolerance [REQ]. A hung MCU therefore resets, and reset leaves CARD_EN low. In the bootloader (outputs off, CARD_EN and the OUT_EN latch low) flash erase and program run from an SRAM routine with interrupts disabled that refreshes the IWDG while it polls the flash busy flag, so a page erase longer than the IWDG timeout (the STM32G031 page-erase time is milliseconds-class; the DS12992 memory-characteristics figure is to be read into the firmware record, and the rule does not depend on it) never resets the card mid-update.
- **Hardware gates:** every output enable = qualified OUT_PERMIT_k (hardwired from the motion card, section 04) AND OUT_EN latch Q AND CARD_EN (MCU pin with a pull-down). The OUT_EN latch (one half of an SN74LVC2G74DCUR; the ACC uses the second half the same way for PROC_PERMIT) has D = 1, CLK = an MCU strobe, and asynchronous CLR_N = the qualified OUT_PERMIT_k net. Any OUT_PERMIT_k drop that passes the card's 2 µs acceptance filter, however short, clears it: the outputs go off and **stay off** (PWM low, AO clamped) when OUT_PERMIT_k returns. The MCU reads Q, reports the drop (DO8 realtime byte 7 b6, ACC byte 15 b5), writes SW_STATE = 0 and re-arms the latch only in ACTIVE after a new epoch and IO_ENABLE. The TPS274C65 restores the stored SW_STATE when DO_EN returns [DS], which is why SW_STATE is written 0 first. The motion card's OPI_OUT latch records the same drop and the FPGA latches OUTPUT_PERMIT_LOST.
- **Card-to-driver hop:** the DO8 MCU talks to its two TPS274C65ASRHAR through the digital isolator in addressable SPI mode with the device CRC enabled (CRCEN = 1) [DS], so the isolated hop is checked as well; a driver SPI or CRC error is reported in realtime byte 7 and the affected outputs are commanded off.

### 4.8 Readback, faults, restart, configuration and firmware update

- **Readback:** response *n* carries the state applied after command *n* − 1 (DO: TPS274C65 SW_STATE read back and CARD_EN; AO: DAC register read back). The FPGA compares it with the image it sent in command *n* − 1; two consecutive mismatches latch OUTPUT_READBACK_MISMATCH for that output, which is then forced off. SW_STATE readback proves the register, not the load: the physical output is covered by the driver's VOUT, current and open-load diagnostics (section 8).
- **Driver faults:** the card forwards the TPS274C65 fault latches every 100 µs; the FPGA forces the output off in its image and latches DO_FAULT and an OUTPUT_FAULT event. IO_CLEAR_FAULTS clears it only while that output is commanded off.
- **Restart:** power-up or card reset → INIT with outputs off → the FPGA sends SYNC frames with a new epoch → IDENT_READ and CONFIG_WRITE are verified against the stored configuration → SYNCED → ACTIVE only after the host's IO_ENABLE. A card that resets during operation shows an epoch mismatch and its reset cause; the port fault latches and nothing resumes automatically.
- **Firmware update:** each card carries a write-protected bootloader. The host service sends update records through MAINT (opcode 0x0C) while motion is disarmed and I/O disabled. The bootloader keeps the IWDG alive from its SRAM erase/program routine (section 4.7) and never raises CARD_EN. An interrupted update leaves the card in its bootloader (class 0x7F) with outputs off; the service restarts the update from the local package. No programmer, no internet and no manual flashing.

### 4.9 Card telemetry pages (10 bytes each)

**DIC**

- p0: 0-1 SENS_G0 mV; 2-3 SENS_G1 mV; 4-5 SENS_G2 mV; 6 limiter fault bits; 7 safety-supply fault bits; 8-9 SAFE_24V mV
- p1: 0-1 MCU temperature 0.1 C (s16); 2-3 MCU VDD mV; 4 reset cause; 5 firmware minor; 6-9 applied config CRC-32C
- p2: card-side link counters u16: 0-1 CRC, 2-3 format, 4-5 sequence/epoch, 6-7 identity, 8-9 accept-timer trips

**DO8**

- p0-p7 (output k): 0-1 ISNS code (10-bit; 0xFFFF = not measured: output off, ADC reported FF, or diagnostics disabled); 2-3 TSNS code; 4-5 VOUT code; 6-7 age of the ADC values at transmission, us; 8 b0 output on during sample, b1 ISNS saturated, b2 below qualified accuracy range (card factory record); 9 output index
- p8: 0-1 VS code device 0; 2-3 VS code device 1; 4-5 MCU temperature 0.1 C; 6-7 MCU VDD mV; 8 reset cause; 9 firmware minor
- p9: card-side link counters (as DIC p2)
- p10: 0-4 fault detail, 5 bits per output (overcurrent, thermal, open load on, open load off, short to VS), packed MSB first; 5 device 0 global flags; 6 device 1 global flags; 7 FLT pin levels; 8-9 driver SPI error count
- p11: 0-3 applied config CRC-32C; 4-7 factory record CRC-32C; 8-9 zero

**ACC**

- p0-p3 (AI k): 0-1 raw code; 2-3 sample age us; 4 range code; 5 flags (over, under, open); 6-9 zero
- p4: 0-1 AO0 readback; 2-3 AO1 readback; 4 DAC alarm flags; 5 clamp state; 6-9 zero
- p5: 0-1 AI reference mV; 2-3 AI sensor supply mV; 4 sensor supply fault; 5 PWM auxiliary fault; 6 isolated-supply power-good bits (AO0, AO1, AI, RS-485, CAN); 7 zero; 8-9 MCU temperature 0.1 C
- p6: card-side link counters
- p7: 0-3 applied config CRC-32C; 4-7 factory record CRC-32C; 8-9 firmware version

**EIA_status_register**

- p0: 0-2 raw 24-bit image; 3 marker-check failures (mod 256); 4-9 zero

**EX8_status_register**

- p0: 0-1 raw 16-bit image; 2 marker-check failures; 3-9 zero

**FPGA_core_0x80**

- p0: 0-1 max UPDATE interval since last delivery us; 2-3 late count; 4-5 min UPDATE interval us; 6-7 rejected host frames since power-up; 8-9 event ring high-water mark
- p1: 0-3 seconds since configuration; 4-7 latched-fault count since power-up; 8-9 zero

**FPGA_port_counters_0x81_0x86**

- p0: u16 counters 0-1 CRC, 2-3 format/SOF/length/timeout, 4-5 sequence/epoch, 6-7 identity, 8-9 readback mismatch

TPS274C65ASRHAR measurement facts used [DS]: 10-bit ADC; round robin of current, temperature, VOUT and VS; "ADC sample update time in each measurement" 128 µs; current is sensed only while the switch is on; the ADC reports FF otherwise; sense current at RSNS = 1 kΩ is 0.834–0.890 mA at 1 A, 0.410–0.45 mA at 500 mA, 0.151–0.184 mA at 200 mA, 0.068–0.092 mA at 100 mA and 0.02–0.054 mA at 50 mA. The typical column of that table is not legible in the extracted datasheet text, so IS-1 states the spread relative to the midpoint of the minimum and maximum: ±3.2 % at 1 A, ±4.7 % at 500 mA, ±9.9 % at 200 mA, ±15 % at 100 mA and ±46 % at 50 mA [AR on DS]. The ADC reference (2.72–2.85 V [DS]) and the sense-resistor tolerance add to this before the per-channel factory calibration stored in the card record. IS-1 therefore declares the qualified display range as 0.10–0.50 A per output; below 0.10 A the value is flagged "below qualified range", and accuracy is verified by measurement at 0.10, 0.25 and 0.50 A per channel at both ambient extremes, never at one convenient load [ME required]. The datasheet does not state the complete round-robin period for four channels; if each measurement takes 128 µs sequentially it is 16 × 128 µs = 2.048 ms [AR, interpretation, to be measured].

### 4.10 EIA, EX8 and MC slot status registers

The MC slot status register is local to the motion card: 29 presence and power-good lines arrive through the base (section 02 section 6) from every slot that has no other path to the FPGA. Its bits appear in CNS3 `slot_status` every cycle and drive `port_status` b3, SLOT_FAULT and `cnc1.module.<slot>.present/.power-good`.

| Register | Wires | Bits | Read period | Layout | Acceptance |
|---|---|---|---|---|---|
| EIA | SR_CLK, SR_LOAD_N, SR_DATA | 24 | 100 µs at core/8 = 6.25 MHz | bits 0-9 MPG_SEL_X..PEND_AUX; 10 MPG_ENABLE; 11 XF present; 12 XF supply fault; 13 MPG supply fault; 14-15 probe 0/1 supply fault; 16-19 ENC0-3 supply fault; 20-23 fixed marker 1010 (tied on the far end of the chain) | marker must read 1010 and two consecutive reads must agree before a bit changes in STS; three consecutive marker failures latch IO_LINK_FAULT on port S0 |
| EX8 | SR_CLK, SR_LOAD_N, SR_DATA | 16 | 100 µs at core/8 | bits 0-7 ENC4-11 supply fault; 8 EX8 power-good; 9-11 zero; 12-15 marker 1010 | as EIA; port S1 |
| MC_slot | SSR_CLK, SSR_LOAD_N, SSR_DATA (local to the MC) | 40 | 100 µs at core/6 = 8.33 MHz | bits 0-28 as CNS3 slot_status b0-28 (presence A, presence B, power-good of EIA, EX8, DIC, DOA, DOB, ACC, ESC, CMC, XS; SCART presence A/B); 29-35 zero; 36-39 fixed marker 1010 | marker must read 1010 and two consecutive reads must agree before a bit changes in STS; a fall of a presence or power-good bit of a fitted card latches SLOT_FAULT; three consecutive marker failures latch IO_LINK_FAULT; worst-case age at the snapshot 2 x 100 us + 5.12 us read = 205.12 us [AR] |

Input-only status registers carry no outputs, so the validate-before-commit rule for output cards does not apply; the fixed marker plus double-read agreement detects stuck, open and shifted chains. The worst-case age of a status bit at the FB snapshot is 2 x 100 us + one read (4.16 us) [AR]. The MC slot status register collects the presence contacts and power-good of every slot that has no other path to the FPGA; its inputs arrive through the base on the MC connector (section 02 section 6).

### 4.11 What never travels over IOL1

STEP/DIR, drive enables, drive alarms, encoders, the handwheel A/B, probes, frequency inputs, PWM, process enables, EXT_PERMIT, PROCESS_PERMIT, the XS1 status/feedback inputs and every permission net stay direct FPGA or hardware signals (sections 03 and 04). OUT_PERMIT never travels inside the link.

## 5. Per-cycle schedule

### 5.1 Endpoints (section 04 section 2)

- **Start:** the nominal servo period boundary T(k); scheduling latency counts.
- **Completion C(k):** CS_CMD release of the accepted UPDATE (FPGA commit). **Target C(k) ≤ 700 µs** — an engineering-margin target, not a safety limit.
- **Deadline:** the 1 ms servo period; the thread must also finish (CMD ioctl return) before T(k+1).
- **Included in C(k):** wake latency, both ioctl entries and the FB ioctl return, CS_FB and CS_CMD wire time and guards, CNF3 decode, all LinuxCNC computation of the cycle, UPDATE encode, spidev and DMA gaps. The phase list is `schedule.pre_commit_phases` in `spec/protocol.json`; `tools/interface_spec_validate.py` recomputes C(k) from it.
- **Measured separately:** input data age and output update latency (5.3), each with its own bound; the 1 ms servo deadline, the 5 ms FPGA command watchdog and the 20 ms fault-to-inhibit bound (section 04) are never folded into these numbers. Host overhead is an allocation until a target compute module is measured (section 5.7).

### 5.2 One complete cycle at 5 MHz and 6.25 MHz

Wire time and guards are arithmetic [AR]. Every host-side row is an **allocation [REQ]** until measured; there is no measurement of any host in this repository.

| Phase | 5 MHz (µs) | ends at (µs) | 6.25 MHz (µs) | ends at (µs) | Label |
|---|---|---|---|---|---|
| Scheduling delay (wake latency) | 80.00 | 80.00 | 80.00 | 80.00 | [REQ] |
| FB ioctl entry to CS_FB assert | 25.00 | 105.00 | 25.00 | 105.00 | [REQ] |
| CS_FB 176 B wire + 0.48 µs guards | 282.08 | 387.08 | 225.76 | 330.76 | [AR] |
| CS_FB release to ioctl return | 15.00 | 402.08 | 15.00 | 345.76 | [REQ] |
| CNF3 decode and pin publish | 10.00 | 412.08 | 10.00 | 355.76 | [REQ] |
| LinuxCNC motion, kinematics, HAL functions | 60.00 | 472.08 | 60.00 | 415.76 | [REQ] |
| UPDATE encode | 5.00 | 477.08 | 5.00 | 420.76 | [REQ] |
| CMD ioctl entry to CS_CMD assert | 25.00 | 502.08 | 25.00 | 445.76 | [REQ] |
| CS_CMD 96 B wire + 0.48 µs guards | 154.08 | 656.16 | 123.36 | 569.12 | [AR] |
| **Completion C(k)** (commit) |  | **656.16** |  | **569.12** | [AR on REQ] |
| Margin to the 700 µs target |  | 43.84 |  | 130.88 | [AR on REQ] |
| Margin to the 1 ms period |  | 343.84 |  | 430.88 | [AR on REQ] |
| CS_CMD release to ioctl return (thread end) | 15.00 | 671.16 | 15.00 | 584.12 | [REQ] |
| FPGA commit processing after CS release | ≤ 0.2 |  | ≤ 0.2 |  | [REQ, RTL design] |

The full-I/O card exchanges (section 5.4) run inside the FPGA in parallel with this schedule and take no host time; the host reads their latest validated results in CNF3.

Reading the table: at 5 MHz the host may spend at most **263.84 µs** in total on scheduling latency, ioctl overheads and computation for C(k) to meet 700 µs (563.84 µs for the 1 ms period); at 6.25 MHz **350.88 µs** (650.88 µs). The allocation above uses 220.00 µs. If the bench exceeds the allocation, the finding is recorded and the decision rules in 5.7 apply; no rate, timeout or limit is raised.

2 kHz is not feasible: the wire time alone is 87.2 % of a 500 µs period at 5 MHz [AR].

### 5.3 Input data age and output update latency

| Quantity | Path | 5 MHz | 6.25 MHz | Label |
|---|---|---:|---:|---|
| Counter age at use (steps, encoders, MPG, alarms, safety bits) | CNF3 snapshot → FB wire → ioctl return → decode | 307.08 µs | 250.76 µs | [AR on REQ] |
| DI age at use, no rejected frame | card sample → IOL1 (staleness at the snapshot ≤ 240.6 µs: ≤ 100 µs sample-to-frame, 40.4 µs frame and guards, 0.2 µs check, ≤ 100 µs until the next frame replaces it) → counter path; plus configured debounce and ISO1212 propagation | 547.68 µs + filter | 491.36 µs + filter | [AR on REQ] |
| DI/AI age at use, worst valid case | two rejected frames leave the data valid (240.6 + 2 × 100 = 440.6 µs); the third latches the port fault and invalidates it; `din_stale_limit_us` / `ain_stale_limit_us` are limited to 250–440 µs, so the snapshot age of valid data is ≤ the configured limit ≤ 440 µs → counter path | 747.08 µs + filter | 690.76 µs + filter | [AR on REQ] |
| Motion command latency | cnc1.write encode → CMD ioctl → CS_CMD wire → commit; new rate in force ≤ 3 core ticks later | 184.08 µs | 153.36 µs | [AR on REQ] |
| DO/AO update latency | commit → next IOL1 frame (≤ 100 µs) → 40.4 µs frame and guards → card apply (≤ 20 µs [REQ]) = ≤ 160.4 µs; plus driver switching or DAC settling | 344.48 µs + switching | 313.76 µs + switching | [AR on REQ] |
| Status-register bit (pendant, supply faults) staleness at the snapshot | change → next read (≤ 100 µs) → agreeing second read (+100 µs) → read time (3.84 µs shift + 0.32 µs load) | 204.16 µs | 204.16 µs | [AR] |

IS-1 targets [REQ]: counter age ≤ 400 µs; DI age ≤ 600 µs plus the configured debounce with no rejected frame and ≤ 750 µs plus debounce in the worst valid case; DO command-to-driver ≤ 400 µs plus switching. DI and AI are invalid at the earlier of their stale limit and the port fault, never later, so data older than the published bound is never reported as valid. `tools/interface_spec_validate.py` checks the configurable range against both bounds.

### 5.4 I/O link schedule (FPGA-internal, independent of the host)

Per port and 100 µs period: 1.0 µs guard + 38.40 µs frame + 1.0 µs guard = 40.40 µs on the wire, leaving a 59.60 µs card processing window [AR]. All four ports and both status registers run in parallel. The host exchange never waits for a card; it reads the latest validated copy.

### 5.5 Watchdog margins (kept distinct)

- FPGA command watchdog: 5 ms without an accepted ARM/UPDATE. Nominal UPDATE spacing 1 ms leaves 4 ms [AR]; the driver keeps its rule period ≤ watchdog/2.
- External watchdogs (section 04 5.1): 9.26/11.04/13.02 ms min/nom/max including the CWD leakage allowance (9.51/12.67 ms from capacitor and IC tolerances alone), with one progress pulse per accepted ARM or UPDATE (WD_M) and per accepted UPDATE or IO_WRITE while I/O is enabled (WD_O). Legal spacing is below 5 ms, so the margin to tWD(min) is > 4.2 ms [AR on DDR].
- I/O watchdog in the FPGA: 5 ms without accepted UPDATE/IO_WRITE while I/O is enabled → IO_WATCHDOG.
- Card accept timer 1.0 ms and IWDG ≤ 2 ms (section 4.7).
- Fault-to-inhibit ≤ 20 ms: section 04 5.5 and 7.2; not a function of the servo schedule.

### 5.6 Rejected alternatives

| Alternative | Wire time at 5 MHz per cycle | Why rejected |
|---|---:|---|
| Record's 2 × 128 B plus a separate 128 B I/O exchange | 615.84 µs | Leaves 84.16 µs for the whole host at 700 µs [AR] |
| Two symmetric 176 B frames on one chip select | 564.16 µs | Wastes 80 bytes each way |
| One write-behind transaction per cycle | 282.08 µs | Adds up to one period of command latency; fallback only (D01-10) |
| Raising SCLK above core/8 | — | Raises a design limit to fit a budget; not allowed |

### 5.7 Bench method: host overhead, jitter and the 700 µs distribution

Instruments: logic analyser ≥ 200 MS/s with ≥ 16 channels on SERVO_MARK (a spare host GPIO, section 9), CS_FB, CS_CMD, SCLK, MOSI, MISO, `progress_m`, `progress_o`, one IOL1 port (CS_N, SCLK), one DO output through a divider and one STEP output; a pattern generator for DI/probe/encoder stimulus.

1. The IS-1 driver drives SERVO_MARK high at servo-thread entry and toggles it immediately before and after each ioctl (memory-mapped GPIO set/clear, one store each; its own cost is measured first with back-to-back toggles). It records CLOCK_MONOTONIC at the same points into the HR1 record.
2. Nominal grid: T(k) = a + k·P with P the configured period and *a* the lower envelope of (entry(k) − k·P) over each 10 s window, so wake latency = entry(k) − T(k) ≥ 0. Cross-check P against the FPGA snapshot-tick deltas to separate host-clock and FPGA-oscillator error.
3. Per cycle derive: wake latency; FB ioctl pre (entry → CS_FB assert); FB wire (CS_FB assert → release); FB post (release → ioctl return); computation (FB return → CMD ioctl entry); CMD pre; CMD wire; **C(k)** (T(k) → CS_CMD release); thread end (CMD ioctl return). The FPGA's `last_update_interval_us`, `late_update_count` and progress-pulse spacing give the endpoint's view.
4. Conditions, each ≥ 4 hours: idle; touchscreen UI with the 3D preview animating; network throughput both directions with file transfer to storage; ESP UART at its maximum message rate with Wi-Fi/BLE active; RS-485 Modbus polling at its maximum and CAN at 50 % bus load; all of these combined with 12 channels stepping and all I/O cards switching. Run `cyclictest` separately under the same loads as a scheduler baseline (never concurrently with the servo thread).
5. Report per condition: histograms (1 µs bins) of every quantity, maximum, 99.9th, 99.999th and 99.9999th percentiles; count of C(k) > 700 µs; count of period overruns; maximum UPDATE interval and maximum progress-pulse spacing against 5 ms and 9.51 ms.
6. Input age: the pattern generator toggles DI0, a probe and an encoder; the driver pulses SERVO_MARK in the cycle that first reports the change; the analyser gives edge → report age. Output latency: the host toggles DO0 in a known cycle; the analyser gives CS_CMD release → IOL1 frame → DO0 edge.
7. Decision rules: if the measured host overhead exceeds the 5 MHz allowance, first qualify the host buffer path at 6.25 MHz (D01-9); if that is not possible or not enough, measure the write-behind fallback (D01-10); the finding is recorded, and no limit, timeout or rate is raised.

### 5.8 72-hour combined-load test and fault injection

Load, instruments and pass criteria are section 04 section 14 (≈ 259.2 million cycles). This section adds the protocol counters that must be recorded for the whole run: C(k) and wake-latency histograms; `late_update_count` and DEADLINE events; EVENT_OVERFLOW (must stay 0); every host and IOL1 error counter (every error traced to an injection); maximum telemetry age per source (≤ its stale limit); FB/CMD CRC failures seen by the host; history snapshots written and read back.

Protocol fault injection after the 72 h run, under the same load, each ≥ 10 times: bit errors on host MOSI/MISO and on each IOL1 CMD/RSP line (series interposer); a test gateware build (never shipped) that corrupts a chosen IOL1 command CRC, sequence, epoch, class or slot, where the recorded outputs must not change; card reset in operation; MCU halted through SWD (IWDG must reset it and outputs must go off within 2 ms); OUT_PERMIT removed; wrong-slot and wrong-class cards at power-up; replayed and out-of-order host frames; LinuxCNC killed; card firmware update interrupted by power removal at every stage, and a complete update run with the IWDG active (the card must come back in its bootloader with outputs off, never reset by its IWDG during a page erase, and complete the update offline); OUT_PERMIT pulses of 0.2, 0.5, 2 and 5 µs at each output card (an accepted pulse keeps that card's outputs off until IO_ENABLE); bank-B Ioff-buffer OE pulses of 0.1, 0.3, 1 and 2 µs (OPI_BOE set, STEP/DIR at their pulled idle level, no counted edge at the drive); both watchdog self-tests with a meter on PERMIT_OUT (it never closes).

## 6. Every advertised connection

Update rate, maximum data age, fault response and HAL mapping. Rates and ages are design bounds [AR on REQ allocations] unless marked.

| Connection | Dir | Transport field | Update rate | Maximum data age | Fault response | LinuxCNC HAL |
|---|---|---|---|---|---|---|
| M0-M11 STEP/DIR | out | CMD.motor[i].rate (CS_CMD UPDATE) | 1 kHz servo | command computation to FPGA commit <= 184.08 us at 5 MHz / 153.36 us at 6.25 MHz [AR on REQ allocations]; commit to new rate in effect <= 3 core ticks (60 ns) [SI design rule] | rejected frame, watchdog, alarm trip, OPI, supply or safety fault: all channels disarm; pos_continuity cleared unless a clean DISARM | cnc1.N.position-cmd (float in), cnc1.N.scale, cnc1.N.emitted-count (float out) |
| Emitted step counts | in | STS.motor[i].position (CNF3 36-71) | 1 kHz | <= 307.08 us at 5 MHz / 250.76 us at 6.25 MHz from snapshot to use [AR] | CRC/format/sequence/timestamp or implausible delta: CNC1_BAD_FRAME/CNC1_COUNT, feedback-valid false, driver fault | cnc1.N.position-fb (float out), cnc1.feedback-valid |
| Per-channel enable EN_NO/EN_NC | out | armed mask (ARM/DISARM); STS.enable_cmd_state (CNF3 32-33) | on ARM/DISARM/fault; reported 1 kHz | switching times per section 04 3.1 (TLP3640A tON <= 0.5 ms, TLP4176A <= 1 ms / 3 ms [DS via 04]) | any fault: LED string dark, NO open, NC closed (section 04 3.3). cnc1.N.enable must equal the required_mask bit when cnc1.enable rises (else the driver sends no ARM and reports CNC1_ENABLE_MISMATCH); a drop of any cnc1.N.enable while armed causes a clean DISARM of all channels (section 3.4a) | cnc1.N.enable (bit in, per-channel request), cnc1.N.enable-commanded (bit out), cnc1.enable (bit in, global) |
| ALM0-ALM11 | in | STS.alarm / STS.alarm_latched (CNF3 28-31) | sampled every 10 us in the FPGA; reported 1 kHz | filter 30-40 us; at use <= 40 us + counter age [AR] | armed channel in alarm_trip_mask: DRIVE_ALARM, disarm all within the filter time | cnc1.N.alarm, cnc1.N.alarm-latched |
| Position continuity | in | STS.pos_continuity (CNF3 34-35, CNS3 34-35) | 1 kHz | snapshot | cleared: every joint J whose channel map contains the channel is unhomed through halui.joint.J.unhome (joint index, not channel index; extra joints are unhomed with motion disabled, section 7.2) | cnc1.N.position-continuity |
| ENC0-ENC3 (EIA), ENC4-ENC11 (EX8) | in | STS.enc[k].count (CNF3 72-107), valid/illegal/fault/index-armed masks (108-115); index via INDEX_CAPTURE event | 1 kHz counts; index event delivered in the CNS3 of the same cycle when it occurs before CS_CMD assertion, otherwise the next | counts as step counts; index value exact to the core tick | illegal transition or port supply fault: encoder invalid; ENCODER_FAULT and disarm when required by an armed joint. A single open or shorted line is not detected in IS-1: it shows as following error where the loop closes on the encoder, as step/encoder disagreement in the preview, and in the commissioning count check | cnc1.encoder.K.count, .position, .velocity, .scale, .index-enable (io), .valid, .fault, .supply-fault |
| Handwheel MPG A/B and pendant inputs | in | STS.mpg.count (116-118), STS.mpg.status (119), STS.mpg.select (170-171, EIA status register) | count 1 kHz; pendant bits every 100 us register read | count as counters; pendant bits <= 204.16 us at the snapshot [AR] | invalid, or the enable button released when the profile declares one: counts discarded (never buffered) and never converted into motion | cnc1.mpg.counts, cnc1.mpg.valid, cnc1.mpg.enable, cnc1.mpg.sel-x/-y/-z/-a/-b/-c, cnc1.mpg.mul-x1/-x10/-x100, cnc1.mpg.pend-aux, cnc1.mpg.supply-fault |
| Probes P0/P1 | in | STS.probe.state (120); PROBE_CAPTURE event (CNS3 36-55) | level 1 kHz; capture per event | capture latency 2-3 core ticks + configured filter [SI design]; delivery <= 1 cycle when the ring is empty | overrun sticky; host rejects the probe result | cnc1.probe.N.in, cnc1.probe.N.captured, cnc1.probe.N.capture-seq, cnc1.probe.N.capture-time, cnc1.probe.N.capture-value.J (J = 0-3), cnc1.probe.N.overrun |
| FREQ0/FREQ1 (XF measurement port) | in | STS.freq[k].count / .last_edge (CNF3 122-135) | 1 kHz | frequency value age = snapshot - last edge; NO_SIGNAL after freqK_no_signal_ms | NO_SIGNAL: valid false, never shown as 0 Hz; XF absent or supply fault: invalid | cnc1.freq.N.frequency, cnc1.freq.N.count, cnc1.freq.N.valid, cnc1.freq.N.age, cnc1.freq.module-present, cnc1.freq.module-id-valid, cnc1.freq.supply-fault |
| PWM0/PWM1 | out | CMD.pwm[k].duty (CS_CMD 72-75), enable bits (66) | 1 kHz; new duty at the next PWM period boundary | commit + <= one PWM period | OUT_PERMIT low: buffer disabled in hardware (output pulled low, the device's required off level; no inverted mode); ACC OUT_EN latch keeps it off until re-armed; I/O fault: enable dropped | cnc1.pwm.N.value, cnc1.pwm.N.enable, cnc1.pwm.N.frequency, cnc1.pwm.aux-fault |
| Process enables PEN0/PEN1 | out | CMD.proc_en (66 b0-1); STS.proc_en_state (144) | 1 kHz | commit + photoMOS switching (ACC part, section 03/04) | PROC_PERMIT low: opened in hardware; PROCESS_PERMIT_LOST clears the request | cnc1.proc-en.N.cmd, cnc1.proc-en.N.commanded |
| AO0/AO1 (ACC) | out | CMD.ao[k] (CS_CMD 76-79) -> IOL1 L3 | 1 kHz command; 10 kHz link | commit to DAC write <= 160.4 us [AR, 20 us card allocation REQ] + DAC settling [DS not read here] | link loss >= card accept timeout 1.0 ms or OUT_PERMIT low: zero clamp | cnc1.aout.N.value, cnc1.aout.N.enable, cnc1.aout.N.readback, cnc1.aout.N.readback-valid |
| AI0-AI3 (ACC) | in | STS.ai[k] (CNF3 146-155) | card sampling >= 1 kHz per channel [REQ]; relayed every 100 us | carried in ain_age; snapshot staleness <= card sample period + min(ain_stale_limit_us, 440.6 us) [AR]; at use add the counter age of section 5.3 | older than ain_stale_limit_us, port L3 fault latched, or out of range: valid false | cnc1.ain.N.value, cnc1.ain.N.valid, cnc1.ain.N.age, cnc1.ain.ref-voltage, cnc1.ain.sensor-supply-voltage, cnc1.ain.sensor-supply-fault |
| DI0-DI23 (DIC) | in | STS.din (CNF3 136-138), din_age (139) | 10 kHz link; reported 1 kHz | snapshot staleness <= din_stale_limit_us (250-440, default 440); at use <= 747.08 us at 5 MHz / 690.76 us at 6.25 MHz in the worst valid case (two rejected frames), 547.68 / 491.36 us with no rejected frame [AR on REQ]; plus configured debounce and ISO1212 propagation | older than din_stale_limit_us or port L0 fault latched: all DI invalid (never read as low); machine-enable chain drops when DI are used for machine functions | cnc1.din.N, cnc1.din.N-not, cnc1.din-valid, cnc1.din-age |
| DO0-DO15 (DOA/DOB) | out | CMD.dout (CS_CMD 64-65); STS.dout_readback / dout_fault (CNF3 140-143) | 1 kHz command; 10 kHz link | commit to driver write <= 160.4 us [AR] + driver switching | readback mismatch or driver fault: output forced off and latched; card accept timeout 1.0 ms / IWDG <= 2 ms: outputs off; any accepted OUT_PERMIT_k drop: card OUT_EN latch off until a new epoch and IO_ENABLE (OUTPUT_PERMIT_LOST) | cnc1.dout.N (in), cnc1.dout.N-applied, cnc1.dout.N-fault, cnc1.dout.N-current, cnc1.dout.N-current-valid, cnc1.dout.N-current-age, cnc1.dout.clear-faults |
| Safety interface XS1 (EXT_PERMIT, PROCESS_PERMIT, chain status, reset/arm, contactor and STO feedback) and arm lamp | in/out | STS.safety (CNF3 164-167, CNS3 30-33); CMD arm lamp (66 b6) | direct FPGA inputs; reported 1 kHz | input filter (section 04, <= 1 ms allocation for EXT_PERMIT) + snapshot | EXT_PERMIT low: hardware inhibit, SAFETY_INPUT_OPEN; PROCESS_PERMIT low: both process contacts open in hardware, PROCESS_PERMIT_LOST; contactor mismatch: CONTACTOR_FEEDBACK; STO mismatch: STO_FEEDBACK; reset/arm: ARM precondition (ARM_REFUSED), stuck button reported; chain status: SAFETY_INTERFACE event (diagnostic) | cnc1.safety.ext-permit, .process-permit, .chain-status, .reset-arm, .contactor-fb, .sto-fb, .arm-lamp, .reset-arm-ready |
| Permission and watchdog readbacks | in | STS.safety bits 0-9, 21-22, 28-29 | 1 kHz | snapshot | section 04 section 8 | cnc1.safety.tx-permit, .out-permit, .proc-permit, .wd-motion-ok, .wd-output-ok, .wd-motion-tripped, .wd-output-tripped, .opi-ok-tx, .opi-ok-a, .opi-ok-b, .selftest-ok, .opi-ok-out, .opi-ok-boe |
| Supply monitors (AUX, field entries, MOTION_5V, EXP_5V, core, EX8) | in | STS.safety bits 12-20, 27 | 1 kHz | monitor filter + snapshot | POWER_FAULT / AUX_SUPPLY_FAULT: disarm | cnc1.safety.aux24-ok-a/-b, cnc1.safety.aux5-ok-a/-b, cnc1.power.field-a-ok, cnc1.power.field-b-ok, cnc1.power.motion5v-ok, cnc1.power.exp5v-ok, cnc1.power.core-ok |
| Entry voltage and current (PSM) | in | host I2C telemetry TEL.supply.* (not CNC1) | 10 Hz [REQ] | host timestamp carried; stale after 500 ms | diagnostic only; protection is the entry eFuses and PGOOD bits | cnc1.supply.core.voltage/.current, cnc1.supply.field-a.voltage/.current, cnc1.supply.field-b.voltage/.current (service-published, userspace) |
| Module presence and identity | in | STS.slot_status (CNS3 82-85), STS.slots, STS.expansion.mx4/ex8, STS.port[*] (1 kHz); IDP3 page and EEPROM/1-Wire identity (at qualification) | presence 1 kHz; identity at qualification and on request | MIA/MX4 lines: 30-40 us filter + snapshot; other slots: MC slot status register <= 205.12 us [AR] | change under power: EXPANSION_CHANGED / SLOT_FAULT; wrong class: refused | cnc1.installed-channels, cnc1.expansion-installed, cnc1.encoder-expansion-installed, cnc1.io.P.state, cnc1.io.P.identity-ok, cnc1.io.P.card-class |
| IOL1 ports L0-L3 and status registers S0-S1 | both | STS.port[*]; TEL 0x81-0x86 counters | 10 kHz link; counters >= 20 Hz | counter page age carried | 3 consecutive failures: port fault latched (section 4.6) | cnc1.io.P.crc-errors, .format-errors, .sequence-errors, .identity-errors, .readback-errors |
| Host SPI link (CNC1) | both | all frames; CNS3 78-81 timing | 2 transactions per 1 ms cycle | - | any rejected frame: LINK fault; host-side CRC error: CNC1_BAD_FRAME | cnc1.fault, cnc1.fault-word, cnc1.fault-code, cnc1.timing.update-interval-us, cnc1.timing.late-updates, cnc1.timing.completion-us, cnc1.timing.wake-latency-us, cnc1.timing.overruns, cnc1.timing.target-exceeded, cnc1.event.lost |
| RS-485 (ACC transceiver, host UART) | both | not CNC1; Linux tty in kernel RS-485 mode | per device profile (MB2HAL transaction rates); never in the servo thread | per transaction; mb2hal num_errors | profile-defined hold/inhibit; never the only run-enable path | mb2hal.<tx>.<n>.float/.int/.bit, mb2hal.<tx>.num_errors; service summary cnc1.bus.rs485.errors |
| CAN (ACC transceiver, host MCP2518FD) | both | not CNC1; SocketCAN (mcp251xfd driver) | per device profile; never in the servo thread | per signal, carried | profile-defined; bus-off reported | cnc1can.<signal>.value, cnc1can.<signal>.valid, cnc1can.<signal>.age-ns, cnc1can.bus-off; service summary cnc1.bus.can.errors |
| ESP service link | both | not CNC1; separate UART owned by the diagnostics service | service-defined | heartbeat age | missing heartbeat record; no motion or output effect | none in the servo thread |
| Card and compute temperatures | in | HOST.i2c.module[slot].temperature; HOST.sysfs.soc_temperature (not CNC1) | 1 Hz | carried per value; stale after 5 s | diagnostic; warning above the card's MIR-1 rated limit; never used by protection | cnc1.module.<slot>.temperature, -temperature-valid, -temperature-age (service-published) |
| XS synchronized expansion (reserved) | both | STS.port[L4_XS] (CNF3 173, always 0 in IS-1); CONFIGURE_IO page 0 byte 18 | 10 kHz link when a module class is defined | as IOL1 ports | a nonzero expected class is rejected in IS-1; the slot stays empty | cnc1.io.l4.* (reserved) |

## 7. LinuxCNC HAL mapping

### 7.1 `cnc1` component pins

All pins keep the existing `cnc1.` prefix and the existing global pins of [`hal_cnc1.c`](../../cnc1/src/hal_cnc1.c) (`cnc1.enable`, `cnc1.reset`, `cnc1.fault`, `cnc1.ready`, `cnc1.armed`, `cnc1.feedback-valid`, `cnc1.state`, `cnc1.fault-code`, the configuration pins). Channel N = 0–11, encoder K = 0–11, DI 0–23, DO 0–15, 0-based everywhere (section 03 naming rule).

| Group | Pins (direction) |
|---|---|
| Per channel | `cnc1.N.position-cmd` (in), `cnc1.N.position-fb` (out), `cnc1.N.scale`, `cnc1.N.emitted-count` (out), `cnc1.N.enable` (in, per-channel request; rules in section 3.4a), `cnc1.N.enable-commanded` (out), `cnc1.N.alarm` (out), `cnc1.N.alarm-latched` (out), `cnc1.N.timing-fault` (out), `cnc1.N.position-continuity` (out) |
| Global motion | `cnc1.installed-channels` (u32), `cnc1.expansion-installed`, `cnc1.encoder-expansion-installed`, `cnc1.config-generation`, `cnc1.fault-word` (u32) |
| Encoders | `cnc1.encoder.K.count` (s32), `.position`, `.velocity`, `.scale`, `.index-enable` (io, cleared by the driver on INDEX_CAPTURE), `.valid`, `.fault`, `.supply-fault` |
| Handwheel | `cnc1.mpg.counts` (s32), `cnc1.mpg.valid`, `cnc1.mpg.enable`, `cnc1.mpg.sel-x`, `-y`, `-z`, `-a`, `-b`, `-c`, `cnc1.mpg.mul-x1`, `-x10`, `-x100`, `cnc1.mpg.pend-aux`, `cnc1.mpg.supply-fault` |
| Probes | `cnc1.probe.N.in`, `.capture-enable` (in), `.captured` (one-cycle pulse), `.capture-seq` (u32), `.capture-time` (float s, FPGA time), `.capture-value.J` (float, J = 0–3, scaled by the source's scale), `.overrun` |
| Frequency | `cnc1.freq.N.frequency` (float Hz), `.count` (s32), `.valid`, `.age` (float s); `cnc1.freq.module-present`, `cnc1.freq.module-id-valid`, `cnc1.freq.supply-fault` |
| PWM / process | `cnc1.pwm.N.value` (float 0–1), `.enable`, `.frequency`; `cnc1.pwm.aux-fault`; `cnc1.proc-en.N.cmd` (in), `cnc1.proc-en.N.commanded` (out) |
| Analog | `cnc1.aout.N.value` (float V), `.enable`, `.readback`, `.readback-valid`; `cnc1.ain.N.value`, `.valid`, `.age`; `cnc1.ain.ref-voltage`, `cnc1.ain.sensor-supply-voltage`, `cnc1.ain.sensor-supply-fault` |
| Digital I/O | `cnc1.din.N`, `cnc1.din.N-not`, `cnc1.din-valid`, `cnc1.din-age`; `cnc1.dout.N` (in), `cnc1.dout.N-applied`, `cnc1.dout.N-fault`, `cnc1.dout.N-overcurrent`, `-thermal`, `-open-load`, `-short-to-supply`, `cnc1.dout.N-current`, `-current-valid`, `-current-age`, `cnc1.dout.N-temperature`, `cnc1.dout.N-voltage`; `cnc1.dout.clear-faults` (in, edge) |
| I/O session and ports | `cnc1.io-enable` (in), `cnc1.io-enabled`, `cnc1.io-fault`; per port P = `l0`–`l3`, `s0`, `s1` (and `l4`, reserved for an XS module): `cnc1.io.P.state`, `.identity-ok`, `.card-class`, `.power-good`, `.crc-errors`, `.format-errors`, `.sequence-errors`, `.identity-errors`, `.readback-errors`, `.temperature`, `.vdd` |
| Safety and power | section 04 section 8 names (`cnc1.safety.*`, `cnc1.power.*`) plus `cnc1.safety.chain-status`, `.reset-arm`, `.reset-arm-ready`, `.contactor-fb`, `.sto-fb`, `.opi-ok-out`, `.opi-ok-boe`, `.arm-lamp` (in) |
| Timing and events | `cnc1.timing.update-interval-us`, `.late-updates`, `.completion-us`, `.wake-latency-us`, `.overruns`, `.target-exceeded` (count of C(k) > 700 µs); `cnc1.event.lost`; `cnc1.link.crc-errors`, `cnc1.link.rejected-frames` |

Every measurement pin with a `-valid`/`.valid` companion keeps its last value when invalid, and consumers must read the validity pin; the service API returns `null` with the validity state instead of a number (T4). Supply voltages from the power module (`cnc1.supply.*`) are published by the userspace service from host I2C, not by the real-time component.

### 7.1a Pin registry

The table above is the readable summary. The normative list is `hal_pins` in `spec/protocol.json`: every pin name the `cnc1` component, the configuration service and the bus adapters publish, with type, direction, transport source and whether the real-time component or the userspace service publishes it. Placeholders expand over `hal_index` (for example `{m}` = 0–11, `{port}` = l0–l4, s0, s1). Every HAL name in `spec/terminals.json`, in the connection table (section 6, `hal_pins`) and in `spec/safety.json` must resolve to this registry; `tools/interface_spec_validate.py` checks it.

| Pin | Type | Dir | Source | Published by |
|---|---|---|---|---|
| `cnc1.{m}.position-cmd` | float | in | CMD.motor[m].rate | cnc1 (real time) |
| `cnc1.{m}.position-fb` | float | out | STS.motor[m].position | cnc1 (real time) |
| `cnc1.{m}.scale` | float | in | configuration | cnc1 (real time) |
| `cnc1.{m}.emitted-count` | s32 | out | STS.motor[m].position | cnc1 (real time) |
| `cnc1.{m}.enable` | bit | in | ARM channel_mask: must equal the required_mask bit when cnc1.enable rises; a drop while armed causes a clean DISARM of all channels (section 3.4a) | cnc1 (real time) |
| `cnc1.{m}.enable-commanded` | bit | out | STS.enable_cmd_state | cnc1 (real time) |
| `cnc1.{m}.alarm` | bit | out | STS.alarm | cnc1 (real time) |
| `cnc1.{m}.alarm-latched` | bit | out | STS.alarm_latched | cnc1 (real time) |
| `cnc1.{m}.timing-fault` | bit | out | STS.step_timing_latched | cnc1 (real time) |
| `cnc1.{m}.position-continuity` | bit | out | STS.pos_continuity | cnc1 (real time) |
| `cnc1.enable` | bit | in | global | cnc1 (real time) |
| `cnc1.reset` | bit | in | driver | cnc1 (real time) |
| `cnc1.fault` | bit | out | STS.fault_word | cnc1 (real time) |
| `cnc1.ready` | bit | out | driver | cnc1 (real time) |
| `cnc1.armed` | bit | out | STS.armed_mask | cnc1 (real time) |
| `cnc1.feedback-valid` | bit | out | driver | cnc1 (real time) |
| `cnc1.state` | s32 | out | driver | cnc1 (real time) |
| `cnc1.fault-code` | s32 | out | driver | cnc1 (real time) |
| `cnc1.installed-channels` | u32 | out | STS.installed_mask | cnc1 (real time) |
| `cnc1.expansion-installed` | bit | out | STS.slots | cnc1 (real time) |
| `cnc1.encoder-expansion-installed` | bit | out | STS.slots | cnc1 (real time) |
| `cnc1.config-generation` | u32 | out | STS.config_generation | cnc1 (real time) |
| `cnc1.fault-word` | u32 | out | STS.fault_word | cnc1 (real time) |
| `cnc1.io-enable` | bit | in | IO_ENABLE | cnc1 (real time) |
| `cnc1.io-enabled` | bit | out | STS.state | cnc1 (real time) |
| `cnc1.io-fault` | bit | out | STS.fault_word | cnc1 (real time) |
| `cnc1.encoder.{k}.count` | s32 | out | STS.enc[k].count | cnc1 (real time) |
| `cnc1.encoder.{k}.position` | float | out | STS.enc[k].count | cnc1 (real time) |
| `cnc1.encoder.{k}.velocity` | float | out | STS.enc[k].count | cnc1 (real time) |
| `cnc1.encoder.{k}.scale` | float | in | configuration | cnc1 (real time) |
| `cnc1.encoder.{k}.index-enable` | bit | io | CMD.enc.index_enable / INDEX_CAPTURE event | cnc1 (real time) |
| `cnc1.encoder.{k}.valid` | bit | out | STS.enc.valid | cnc1 (real time) |
| `cnc1.encoder.{k}.fault` | bit | out | STS.enc.fault / STS.enc.illegal | cnc1 (real time) |
| `cnc1.encoder.{k}.supply-fault` | bit | out | STS.enc.fault | cnc1 (real time) |
| `cnc1.mpg.counts` | s32 | out | STS.mpg.count | cnc1 (real time) |
| `cnc1.mpg.valid` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.enable` | bit | out | STS.mpg.select bit 10 (MPG_ENABLE); gates jog counts when the profile declares an enable button (section 7.2) | cnc1 (real time) |
| `cnc1.mpg.sel-x` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.sel-y` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.sel-z` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.sel-a` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.sel-b` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.sel-c` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.mul-x1` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.mul-x10` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.mul-x100` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.pend-aux` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.mpg.supply-fault` | bit | out | STS.mpg.select / STS.mpg.status | cnc1 (real time) |
| `cnc1.probe.{p}.in` | bit | out | STS.probe.state / PROBE_CAPTURE event / CMD.probe.arm | cnc1 (real time) |
| `cnc1.probe.{p}.capture-enable` | bit | in | STS.probe.state / PROBE_CAPTURE event / CMD.probe.arm | cnc1 (real time) |
| `cnc1.probe.{p}.captured` | bit | out | STS.probe.state / PROBE_CAPTURE event / CMD.probe.arm | cnc1 (real time) |
| `cnc1.probe.{p}.capture-seq` | u32 | out | STS.probe.state / PROBE_CAPTURE event / CMD.probe.arm | cnc1 (real time) |
| `cnc1.probe.{p}.capture-time` | float | out | STS.probe.state / PROBE_CAPTURE event / CMD.probe.arm | cnc1 (real time) |
| `cnc1.probe.{p}.overrun` | bit | out | STS.probe.state / PROBE_CAPTURE event / CMD.probe.arm | cnc1 (real time) |
| `cnc1.probe.{p}.capture-value.{j}` | float | out | PROBE_CAPTURE event | cnc1 (real time) |
| `cnc1.supply.probe-{p}.fault` | bit | out | STS.mpg.select bits 14-15 | cnc1 (real time) |
| `cnc1.freq.{f}.frequency` | float | out | STS.freq[f].count / STS.freq[f].last_edge | cnc1 (real time) |
| `cnc1.freq.{f}.count` | s32 | out | STS.freq[f].count / STS.freq[f].last_edge | cnc1 (real time) |
| `cnc1.freq.{f}.valid` | bit | out | STS.freq[f].count / STS.freq[f].last_edge | cnc1 (real time) |
| `cnc1.freq.{f}.age` | float | out | STS.freq[f].count / STS.freq[f].last_edge | cnc1 (real time) |
| `cnc1.freq.module-present` | bit | out | STS.mpg.select / HOST.onewire.xf.identity | cnc1 (real time) |
| `cnc1.freq.module-id-valid` | bit | out | STS.mpg.select / HOST.onewire.xf.identity | cnc1 (real time) |
| `cnc1.freq.supply-fault` | bit | out | STS.mpg.select / HOST.onewire.xf.identity | cnc1 (real time) |
| `cnc1.pwm.{w}.value` | float | in | CMD.pwm[w].duty / CMD.proc_en | cnc1 (real time) |
| `cnc1.pwm.{w}.enable` | bit | in | CMD.pwm[w].duty / CMD.proc_en | cnc1 (real time) |
| `cnc1.pwm.{w}.frequency` | float | in | CMD.pwm[w].duty / CMD.proc_en | cnc1 (real time) |
| `cnc1.pwm.aux-fault` | bit | out | TEL.acc.pwm_aux_fault | cnc1 (real time) |
| `cnc1.proc-en.{e}.cmd` | bit | in | CMD.proc_en | cnc1 (real time) |
| `cnc1.proc-en.{e}.commanded` | bit | out | STS.proc_en_state | cnc1 (real time) |
| `cnc1.aout.{a}.value` | float | in | CMD.ao[a] / STS.ao.state / TEL.ao[a].readback | cnc1 (real time) |
| `cnc1.aout.{a}.enable` | bit | in | CMD.ao[a] / STS.ao.state / TEL.ao[a].readback | cnc1 (real time) |
| `cnc1.aout.{a}.readback` | float | out | CMD.ao[a] / STS.ao.state / TEL.ao[a].readback | cnc1 (real time) |
| `cnc1.aout.{a}.readback-valid` | bit | out | CMD.ao[a] / STS.ao.state / TEL.ao[a].readback | cnc1 (real time) |
| `cnc1.ain.{i}.value` | float | out | STS.ai[i].value / STS.ai.valid / STS.ai.age | cnc1 (real time) |
| `cnc1.ain.{i}.valid` | bit | out | STS.ai[i].value / STS.ai.valid / STS.ai.age | cnc1 (real time) |
| `cnc1.ain.{i}.age` | float | out | STS.ai[i].value / STS.ai.valid / STS.ai.age | cnc1 (real time) |
| `cnc1.ain.ref-voltage` | float | out | TEL.acc.* | cnc1 (real time) |
| `cnc1.ain.sensor-supply-voltage` | float | out | TEL.acc.* | cnc1 (real time) |
| `cnc1.ain.sensor-supply-fault` | bit | out | TEL.acc.* | cnc1 (real time) |
| `cnc1.din.{d}` | bit | out | STS.din | cnc1 (real time) |
| `cnc1.din.{d}-not` | bit | out | STS.din | cnc1 (real time) |
| `cnc1.din-valid` | bit | out | STS.din_valid | cnc1 (real time) |
| `cnc1.din-age` | float | out | STS.din_valid | cnc1 (real time) |
| `cnc1.dout.{o}` | bit | in | CMD.dout | cnc1 (real time) |
| `cnc1.dout.{o}-applied` | bit | out | STS.dout_readback | cnc1 (real time) |
| `cnc1.dout.{o}-fault` | bit | out | STS.dout_fault | cnc1 (real time) |
| `cnc1.dout.{o}-overcurrent` | bit | out | OUTPUT_FAULT event / TEL.dout[o].fault_detail | cnc1 (real time) |
| `cnc1.dout.{o}-thermal` | bit | out | OUTPUT_FAULT event | cnc1 (real time) |
| `cnc1.dout.{o}-open-load` | bit | out | OUTPUT_FAULT event | cnc1 (real time) |
| `cnc1.dout.{o}-short-to-supply` | bit | out | OUTPUT_FAULT event | cnc1 (real time) |
| `cnc1.dout.{o}-current` | float | out | TEL.dout[o].current | cnc1 (real time) |
| `cnc1.dout.{o}-current-valid` | bit | out | TEL.dout[o].current | cnc1 (real time) |
| `cnc1.dout.{o}-current-age` | float | out | TEL.dout[o].current | cnc1 (real time) |
| `cnc1.dout.{o}-temperature` | float | out | TEL.dout[o].temperature | cnc1 (real time) |
| `cnc1.dout.{o}-temperature-valid` | bit | out | TEL.dout[o].temperature | cnc1 (real time) |
| `cnc1.dout.{o}-temperature-age` | float | out | TEL.dout[o].temperature | cnc1 (real time) |
| `cnc1.dout.{o}-voltage` | float | out | TEL.dout[o].vout | cnc1 (real time) |
| `cnc1.dout.{o}-voltage-valid` | bit | out | TEL.dout[o].vout | cnc1 (real time) |
| `cnc1.dout.{o}-voltage-age` | float | out | TEL.dout[o].vout | cnc1 (real time) |
| `cnc1.dout.clear-faults` | bit | in | CMD.dout_fault_clear | cnc1 (real time) |
| `cnc1.io.{port}.state` | u32 | out | STS.port[*] / TEL.fpga.port_counters / TEL.card | cnc1 (real time) |
| `cnc1.io.{port}.identity-ok` | bit | out | STS.port[*] / TEL.fpga.port_counters / TEL.card | cnc1 (real time) |
| `cnc1.io.{port}.card-class` | u32 | out | STS.port[*] / TEL.fpga.port_counters / TEL.card | cnc1 (real time) |
| `cnc1.io.{port}.power-good` | bit | out | STS.port[*] b3 from the MC slot status register (STS.slot_status) | cnc1 (real time) |
| `cnc1.io.{port}.crc-errors` | u32 | out | STS.port[*] / TEL.fpga.port_counters / TEL.card | cnc1 (real time) |
| `cnc1.io.{port}.format-errors` | u32 | out | STS.port[*] / TEL.fpga.port_counters / TEL.card | cnc1 (real time) |
| `cnc1.io.{port}.sequence-errors` | u32 | out | STS.port[*] / TEL.fpga.port_counters / TEL.card | cnc1 (real time) |
| `cnc1.io.{port}.identity-errors` | u32 | out | STS.port[*] / TEL.fpga.port_counters / TEL.card | cnc1 (real time) |
| `cnc1.io.{port}.readback-errors` | u32 | out | STS.port[*] / TEL.fpga.port_counters / TEL.card | cnc1 (real time) |
| `cnc1.io.{port}.temperature` | float | out | TEL.card[i].mcu_temperature on l0-l3; always 'unavailable' on s0, s1 and l4 (no MCU; T4) | cnc1 (real time) |
| `cnc1.io.{port}.vdd` | float | out | TEL.card[i].vdd on l0-l2; always 'unavailable' on l3, s0, s1 and l4 (no source; T4) | cnc1 (real time) |
| `cnc1.safety.tx-permit` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.out-permit` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.proc-permit` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.wd-motion-ok` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.wd-output-ok` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.wd-motion-tripped` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.wd-output-tripped` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.opi-ok-tx` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.opi-ok-a` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.opi-ok-b` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.opi-ok-boe` | bit | out | STS.safety bit 29 | cnc1 (real time) |
| `cnc1.safety.opi-ok-out` | bit | out | STS.safety bit 28 | cnc1 (real time) |
| `cnc1.safety.ext-permit` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.process-permit` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.selftest-ok` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.chain-status` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.reset-arm` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.reset-arm-ready` | bit | out | STS.safety bit 30 | cnc1 (real time) |
| `cnc1.safety.contactor-fb` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.sto-fb` | bit | out | STS.safety | cnc1 (real time) |
| `cnc1.safety.aux24-ok-{bank}` | bit | out | STS.safety bits 12-13 | cnc1 (real time) |
| `cnc1.safety.aux5-ok-{bank}` | bit | out | STS.safety bits 14-15 | cnc1 (real time) |
| `cnc1.safety.arm-lamp` | bit | in | CMD.proc_en bit 6 | cnc1 (real time) |
| `cnc1.power.field-a-ok` | bit | out | STS.safety bits 16-20, 27 | cnc1 (real time) |
| `cnc1.power.field-b-ok` | bit | out | STS.safety bits 16-20, 27 | cnc1 (real time) |
| `cnc1.power.motion5v-ok` | bit | out | STS.safety bits 16-20, 27 | cnc1 (real time) |
| `cnc1.power.exp5v-ok` | bit | out | STS.safety bits 16-20, 27 | cnc1 (real time) |
| `cnc1.power.core-ok` | bit | out | STS.safety bits 16-20, 27 | cnc1 (real time) |
| `cnc1.power.enc-exp-ok` | bit | out | STS.safety bits 16-20, 27 | cnc1 (real time) |
| `cnc1.timing.update-interval-us` | u32 | out | CNS3 78-81 / driver CLOCK_MONOTONIC | cnc1 (real time) |
| `cnc1.timing.late-updates` | u32 | out | CNS3 78-81 / driver CLOCK_MONOTONIC | cnc1 (real time) |
| `cnc1.timing.completion-us` | u32 | out | CNS3 78-81 / driver CLOCK_MONOTONIC | cnc1 (real time) |
| `cnc1.timing.wake-latency-us` | u32 | out | CNS3 78-81 / driver CLOCK_MONOTONIC | cnc1 (real time) |
| `cnc1.timing.overruns` | u32 | out | CNS3 78-81 / driver CLOCK_MONOTONIC | cnc1 (real time) |
| `cnc1.timing.target-exceeded` | u32 | out | CNS3 78-81 / driver CLOCK_MONOTONIC | cnc1 (real time) |
| `cnc1.event.lost` | u32 | out | STS.event_status | cnc1 (real time) |
| `cnc1.link.crc-errors` | u32 | out | driver | cnc1 (real time) |
| `cnc1.link.rejected-frames` | u32 | out | TEL.fpga.core | cnc1 (real time) |
| `cnc1.supply.{entry}.voltage` | float | out | HOST.i2c.psm.entry[i].v | service / other component |
| `cnc1.supply.{entry}.current` | float | out | HOST.i2c.psm.entry[i].i | service / other component |
| `cnc1.supply.dout-{bank}.voltage` | float | out | TEL.dout_bank[i].vs | service / other component |
| `cnc1.supply.sensor-{g}.voltage` | float | out | TEL.dic.sensor_group[i].mv | service / other component |
| `cnc1.supply.sensor-{g}.fault` | bit | out | TEL.dic.limiter_fault | service / other component |
| `cnc1.supply.safety-24v.voltage` | float | out | TEL.dic.safe24_mv | service / other component |
| `cnc1.supply.safety-24v.fault` | bit | out | TEL.dic.safety_supply_fault | service / other component |
| `cnc1.bus.rs485.errors` | u32 | out | HOST.tty.rs485.errors | service / other component |
| `cnc1.bus.can.errors` | u32 | out | HOST.socketcan.errors | service / other component |
| `cnc1.module.{slot}.present` | bit | out | STS.slot_status (EIA, EX8, DIC, DOA, DOB, ACC, ESC, CMC, XS, SCART presence), STS.expansion.mx4/ex8 and STS.slots (MIA, MX4), STS.safety core_pgood/motion5v_pgood (PSM), CDONE and the CNC1 link (MC) | service / other component |
| `cnc1.module.{slot}.power-good` | bit | out | STS.slot_status (EIA, EX8, DIC, DOA, DOB, ACC, ESC, CMC, XS, SCART presence), STS.expansion.mx4/ex8 and STS.slots (MIA, MX4), STS.safety core_pgood/motion5v_pgood (PSM), CDONE and the CNC1 link (MC) | service / other component |
| `cnc1.module.{slot}.accepted` | bit | out | STS.slots / HOST.i2c.module[i].mir1 / HOST.i2c.module[i].temperature | service / other component |
| `cnc1.module.{slot}.class` | u32 | out | STS.slots / HOST.i2c.module[i].mir1 / HOST.i2c.module[i].temperature | service / other component |
| `cnc1.module.{slot}.temperature` | float | out | STS.slots / HOST.i2c.module[i].mir1 / HOST.i2c.module[i].temperature | service / other component |
| `cnc1.module.{slot}.temperature-valid` | bit | out | STS.slots / HOST.i2c.module[i].mir1 / HOST.i2c.module[i].temperature | service / other component |
| `cnc1.module.{slot}.temperature-age` | float | out | STS.slots / HOST.i2c.module[i].mir1 / HOST.i2c.module[i].temperature | service / other component |
| `cnc1can.<signal>.value` | float | out | HOST.socketcan | service / other component |
| `cnc1can.<signal>.valid` | bit | out | HOST.socketcan | service / other component |
| `cnc1can.<signal>.age-ns` | u32 | out | HOST.socketcan | service / other component |
| `cnc1can.bus-off` | bit | out | HOST.socketcan | service / other component |
| `mb2hal.<tx>.<n>.float` | float | io | MB2HAL (LinuxCNC) | service / other component |
| `mb2hal.<tx>.<n>.int` | s32 | io | MB2HAL (LinuxCNC) | service / other component |
| `mb2hal.<tx>.<n>.bit` | bit | io | MB2HAL (LinuxCNC) | service / other component |
| `mb2hal.<tx>.num_errors` | u32 | out | MB2HAL (LinuxCNC) | service / other component |
| `halui.joint.{jt}.unhome` | bit | in | LinuxCNC halui; driven per joint J when any channel mapped to J loses continuity (joint index from the profile's channel-to-joint map, section 7.2) | service / other component |

Index placeholders: `{m}` = 0–11; `{k}` = 0–11; `{d}` = 0–23; `{o}` = 0–15; `{p}` = 0–1; `{f}` = 0–1; `{w}` = 0–1; `{e}` = 0–1; `{a}` = 0–1; `{i}` = 0–3; `{j}` = 0–3; `{g}` = 0–2; `{port}` = l0, l1, l2, l3, l4, s0, s1; `{slot}` = psm, cmc, mc, mia, mx4, eia, ex8, dic, doa, dob, acc, esc, scart, xs; `{entry}` = core, field-a, field-b; `{bank}` = a, b; `{jt}` = 0–15.

### 7.2 LinuxCNC nets generated by the configuration service

Every net has exactly one writer. The allocation sheets (`spec/allocations.json`, a `hal` block on every assignment and a `hal_map` per sheet) are the machine-readable form; `tools/interface_spec_validate.py` builds the net list from them and refuses two writers on one pin.

- **Joints.** The profile's channel-to-joint map gives each channel C its joint J (joint and channel numbers differ in general). `joint.J.motor-pos-cmd` → `cnc1.C.position-cmd`. Exactly one `motor-pos-fb` source per joint: `cnc1.C.position-fb` (step count) **or** `cnc1.encoder.K.position` (scaled) when the joint closes on an encoder, never both. Gantries use duplicate trivkins letters (LinuxCNC 2.9.4 allows 16 joints and 9 axis letters [SI]); every joint of a gantry group gets the same negative `HOME_SEQUENCE` and identical search and latch settings, and duplicate letters always move together.
- **Indexers.** A stepper that is not a coordinated joint (tool carousel, turret) is a LinuxCNC **extra joint**: `[KINS]JOINTS` counts it, `[EMCMOT]EMCMOT = motmod num_extrajoints=n`, extra joints take the last joint numbers, and after homing the carousel/turret component drives `joint.J.posthome-cmd` [SI, motion(9) man page]. Enable, amp-fault, homing and unhome then follow the joint rules below.
- **Enable.** `joint.J.amp-enable-out` → `cnc1.C.enable` (one writer each; section 3.4a); the single global `cnc1.enable` from `motion.motion-enabled`.
- **Faults and position validity.** `cnc1.C.alarm-latched OR cnc1.fault` → `joint.J.amp-fault-in` (one `or2` per joint). `halui.joint.J.unhome` is driven for every joint J that contains a channel whose `pos_continuity` fell (joint index from the map, never the channel number; an extra joint can only be unhomed with motion disabled, which the fault disarm already does). `VOLATILE_HOME = 1` (section 04 4.2).
- **Machine enable.** `iocontrol.0.emc-enable-in` = `cnc1.safety.ext-permit` AND NOT `cnc1.fault` AND `cnc1.din-valid` (the last term whenever any DI is mapped to a machine function: homes, limits, interlocks). Machine-on comes from the UI or from the qualified reset/arm release (`cnc1.safety.reset-arm-ready` rising → `halui.machine.on`); `motion.motion-enabled` then raises `cnc1.enable` and the ARM of section 3.4a follows.
- **Home and limit switches on DI.** `cnc1.din.K` → `joint.J.home-sw-in` / `neg-lim-sw-in` / `pos-lim-sw-in`; one DI may feed several joint pins (a shared limit chain), but no joint pin has two writers.
- **Probe.** LinuxCNC has one `motion.probe-input`. One probe: `cnc1.probe.P.in` → `motion.probe-input` directly. Two probes: both are normalised to "triggered = 1" by their CONFIGURE_IO polarity and combined by one generated `or2`, whose output is the only writer of `motion.probe-input`; a tripped tool setter therefore blocks part probing with LinuxCNC's own "probe already tripped" error instead of being ignored. A profile may instead declare a `mux2` selected by a `motion.digital-out` M-code. The setup service records which probe is fitted and active. Stock G38 records positions at servo-cycle resolution; the core-tick captures on `cnc1.probe.N.capture-value.J` are available to remaps and the setup service. Plasma sheets use `plasmac.float-switch` and `plasmac.ohmic-probe` instead.
- **Spindle.** With a spindle encoder K: `cnc1.encoder.K.position` → `spindle.0.revs`; `cnc1.encoder.K.velocity` scaled to rev/s → `spindle.0.speed-in` (feed per revolution, CSS, at-speed); `spindle.0.index-enable` ⇄ `cnc1.encoder.K.index-enable`. `spindle.0.speed-out-abs` → scale → `cnc1.aout.0.value`. `spindle.0.forward` / `spindle.0.reverse` (or `spindle.0.on` plus a direction DO) → the run and direction DOs, one writer each. `spindle.0.at-speed` ← the VFD "ready/at speed" DI, or a `near` comparator of `speed-in` against the command when there is no such DI. A spindle driven over Modbus always keeps a hardware run-enable DO (or XPC0 contact); the validator refuses a bus-only run path (V-EL-08).
- **Handwheel.** `cnc1.mpg.counts` → `axis.L.jog-counts`, gated by the selector pins, `cnc1.mpg.valid` and, when the profile declares an enable/deadman button, `cnc1.mpg.enable` (generated `mux`/`and2` logic). Counts arriving while the gate is closed are discarded, never buffered, so releasing the enable mid-jog stops the jog and pressing it again never replays old counts.
- **Analog and digital.** `motion.analog-in-NN` ← `cnc1.ain.N.value`; each `cnc1.dout.N` has exactly one writer: `motion.digital-out-NN`, `iocontrol.0.coolant-flood/-mist`, a spindle pin, or `joint.J.amp-enable-out` for a brake release.

### 7.3 RS-485 and CAN

| Bus | Termination | Driver | HAL mapping | Timing and faults |
|---|---|---|---|---|
| RS-485 (isolated transceiver on ACC) | Compute UART; kernel RS-485 mode (TIOCSRS485) drives the transceiver direction from RTS | Linux serial driver; LinuxCNC MB2HAL (non-real-time userspace) generated from the device profile | `mb2hal.<tx>.<n>.float/.int/.bit`, `mb2hal.<tx>.num_errors` [SI, LinuxCNC MB2HAL doc]; service summary `cnc1.bus.rs485.errors` | Transaction rates from the device profile; never in the servo thread; `num_errors` feeds the profile's hold/inhibit; Modbus is never the only run-enable path (LinuxCNC doc warning) |
| CAN (isolated transceiver on ACC) | MCP2518FDT-E/SL on a compute SPI bus separate from the motion SPI [DS] | Mainline `mcp251xfd` SocketCAN driver [DS]; new userspace HAL component `cnc1can` (Claude, not implemented) mapping profile signals | `cnc1can.<signal>.value`, `.valid`, `.age-ns`, `cnc1can.bus-off`; service summary `cnc1.bus.can.errors` | Per device profile; bus-off and stale signals reported with age; never in the servo thread |

Why not in the FPGA: no Modbus or CAN protocol stack belongs in gateware, the LE budget is already the fit risk (record §6.3), Linux already has maintained drivers, and a bus retry storm then cannot delay a motion frame.

## 8. Diagnostics transport (direction A), fault history and the display rule

### 8.1 Every diagnostic signal

| Signal | Physical source | Transport field | Update rate | Age bound | Validity | HAL / service | Fault response |
|---|---|---|---|---|---|---|---|
| Output current, per DO | TPS274C65ASRHAR ISNS -> 10-bit ADC -> DOA/DOB MCU over isolated SPI | TEL L1/L2 p0-p7 bytes 0-1 (+ age 6-7) | >= 11 Hz delivery worst case (>= 22 Hz without host priority requests); card polls each output's ADC result at least every 1 ms [REQ] | <= 90 ms delivery + <= 3.05 ms card sample age (1 ms poll + 2.048 ms ADC round robin) = <= 93.05 ms [AR on REQ], inside the 100 ms stale limit; carried per value | 0xFFFF not measured (output off or ADC FF); below-accuracy flag; stale when older than 100 ms | cnc1.dout.N-current, -current-valid, -current-age | diagnostic; sustained excess against the declared load is a bank fault (section 04 10.2); protection is the driver's own current limit |
| Overcurrent/current-limit, thermal, open load (on/off), short to VS, per DO | TPS274C65ASRHAR fault registers and FLT | IOL1 realtime (every 100 us) -> STS.dout_fault per cycle; detail TEL p10; OUTPUT_FAULT event | 10 kHz link, 1 kHz host | <= 240.6 us to snapshot [AR] | port active | cnc1.dout.N-fault, cnc1.dout.N-overcurrent, -thermal, -open-load, -short-to-supply | output forced off and latched; IO_CLEAR_FAULTS with the output commanded off |
| Driver temperature and output voltage per DO | TPS274C65ASRHAR TSNS/VOUT ADC | TEL L1/L2 p0-p7 bytes 2-5 | >= 11 Hz | <= 93.05 ms | as current | cnc1.dout.N-temperature, cnc1.dout.N-voltage (+ -valid, -age) | diagnostic |
| Field supply at each output card (VS) | TPS274C65ASRHAR VSNS | TEL L1/L2 p8 | >= 11 Hz | <= 93.05 ms | stale 100 ms | cnc1.supply.dout-a.voltage, cnc1.supply.dout-b.voltage | diagnostic; undervoltage flag also in realtime byte 7 |
| Entry voltages and currents | PSM monitors (Codex part) | host I2C | 10 Hz | carried; stale 500 ms | I2C read OK | cnc1.supply.core/field-a/field-b.voltage/.current | diagnostic |
| Power-good: AUX24/AUX5 per bank, field entries, MOTION_5V, EXP_5V, core, EX8 | supervisors/monitors (section 04) | STS.safety | 1 kHz | snapshot | direct | cnc1.safety.aux*, cnc1.power.* | fault and disarm (section 04) |
| Card power-good and presence | presence contacts at both connector ends and the card power-good of every slot: MIA and MX4 direct to the MC (30-40 us filter); EIA, EX8, DIC, DOA, DOB, ACC, ESC, CMC, XS and SCART presence through the MC slot status register | STS.slot_status (CNS3 82-85); STS.port[*] b3 for L0-L3 and S0-S1; STS.expansion.mx4/ex8; STS.slots | 1 kHz | MIA/MX4 30-40 us filter + snapshot; slot status register <= 205.12 us [AR] | slot status register marker 1010 and two agreeing reads (b29) | cnc1.io.P.power-good, cnc1.module.<slot>.present, cnc1.module.<slot>.power-good | SLOT_FAULT |
| Card MCU temperature and VDD | STM32G031 internal sensor and VREFINT | TEL DIC p1, DO8 p8, ACC p5 | >= 5 Hz | <= 200 ms | card calibration values present | cnc1.io.P.temperature (l0-l3), cnc1.io.P.vdd (l0-l2); always 'unavailable' on s0, s1 and l4 and for l3 vdd (no source; T4) | diagnostic |
| Sensor-group and safety-supply voltages and limiter faults (DIC) | DIC monitors (section 03) | DIC realtime bytes 8-9 (faults, every 100 us) and TEL p0 (voltages) | faults 1 kHz host; voltages >= 5 Hz | faults <= 240.6 us; voltages <= 200 ms | port active | cnc1.supply.sensor-N.voltage/.fault, cnc1.supply.safety-24v.voltage/.fault | DI of that group invalid |
| Encoder port supply faults (single-line open/short not detected in IS-1) | EIA/EX8 status registers (TPS2553-1 FAULT per port). The AM26LV32E has no fault output; its fail-safe holds the output high, so one open or shorted line with the other line toggling gives a legal back-and-forth count, not an illegal transition | STS.enc.fault | 100 us read, 1 kHz host | <= 204.16 us | marker check | cnc1.encoder.K.fault, cnc1.encoder.K.supply-fault | supply fault: encoder invalid, ENCODER_FAULT if required. Line faults are found only indirectly: following error where the loop closes on the encoder, step/encoder disagreement in the preview (service contract section 05), and the commissioning count check |
| AI reference, AI sensor supply, PWM auxiliary fault, isolated-supply power-good (ACC) | ACC monitors | TEL L3 p5 | >= 5 Hz | <= 200 ms | port active | cnc1.ain.ref-voltage, cnc1.ain.sensor-supply-voltage/-fault, cnc1.pwm.aux-fault | AI invalid when the reference is out of range |
| AO readback | DAC register readback (ACC) | STS.ao.state per cycle; TEL L3 p4 codes | 1 kHz flag, >= 5 Hz codes | flag <= 240.6 us | port active | cnc1.aout.N.readback, -valid | mismatch: OUTPUT_READBACK_MISMATCH, clamp |
| Communication error counters | FPGA per-port and host-SPI counters; card-side counters | TEL 0x81-0x86 and card p2/p9/p6; CNS3 78-81; driver | >= 11 Hz | <= 90 ms | counters monotonic until power cycle | cnc1.io.P.*-errors, cnc1.link.crc-errors, cnc1.link.rejected-frames | diagnostic; the fault itself is latched by the port rules |
| Servo timing (UPDATE interval, late count, host completion, wake latency) | FPGA timer; driver CLOCK_MONOTONIC | CNS3 78-81; FPGA core TEL p0; HR1 record | 1 kHz | 1 cycle | - | cnc1.timing.* | recorded; overrun of the 1 ms period counted |
| Watchdog trips, OPI, self-test results | section 04 latches | STS.safety; WATCHDOG_TRIP/OPI events | 1 kHz | snapshot | direct | section 04 section 8 | section 04 |
| Motion-card, every card's and compute temperature | AT30TSE752A-XM8M-T on the MC and on every electronic card (section 02 section 9), read by the host over the CMC identity I2C branch; compute SoC thermal zone via Linux sysfs | HOST.i2c.module[slot].temperature; HOST.sysfs.soc_temperature (not CNC1) | 1 Hz | carried per value; stale after 5 s | I2C read OK and MIR-1 accepted; else unavailable | cnc1.module.<slot>.temperature, cnc1.module.<slot>.temperature-valid, cnc1.module.<slot>.temperature-age (service-published) | diagnostic; the service warns above the card's rated limit from its MIR-1 record |
| Module presence, power-good and identity per slot | presence contacts at both connector ends, card supervisor power-good, AT30TSE752A MIR-1 record | STS.slot_status, STS.slots, STS.expansion.mx4/ex8, STS.port[*] (1 kHz); STS.safety core_pgood and motion5v_pgood for the PSM; HOST.i2c.module[slot].mir1 (at power-up and on request) | presence/power-good 1 kHz; identity at qualification | MIA/MX4 30-40 us filter + snapshot; other slots <= 205.12 us (slot status register); identity carries its read time | CRC-32 of the MIR-1 record; class/slot agreement | cnc1.module.<slot>.present, cnc1.module.<slot>.power-good, cnc1.module.<slot>.accepted, cnc1.module.<slot>.class | change under power: EXPANSION_CHANGED or SLOT_FAULT; incompatible or unidentified card: refused and inhibited |
| Port 5 V / 24 V limiter voltages (encoder, MPG, XF, probe supplies) | TPS2553-1 and probe/XF limiter fault outputs only; no per-port voltage ADC in IS-1 | fault flags in STS.enc.fault and STS.mpg.select bits 12-15 | fault flags 1 kHz | <= 204.16 us | marker check of the status register | cnc1.encoder.K.supply-fault, cnc1.mpg.supply-fault, cnc1.freq.supply-fault, cnc1.supply.probe-N.fault | port fault; the voltage itself is shown as 'not measured' (T4), never as a number |
| Safety-interface feedback: reset/arm, contactor, STO, safety-chain status | XS1.4, XS1.5, XS1.7, XS1.8 through ISO1212 channels on the DIC, direct FPGA pins | STS.safety bits 23-26 and 30; SAFETY_INTERFACE event | 1 kHz | input filter + snapshot | EXT_PERMIT path powered (DIC present) | cnc1.safety.reset-arm, cnc1.safety.reset-arm-ready, cnc1.safety.contactor-fb, cnc1.safety.sto-fb, cnc1.safety.chain-status | CONTACTOR_FEEDBACK / STO_FEEDBACK latch and disarm; ARM_REFUSED; chain-status disagreement reported (section 3.4a) |

### 8.1a Telemetry map and host-side sources

Every `TEL.*` name used in `spec/terminals.json` resolves to a mirror page below, and every `HOST.*` name to a host-side source that never passes through CNC1 or the servo thread.

| Logical name | Mirror source | Page | Bytes | Age from | Rate | Stale after (ms) |
|---|---|---|---|---|---|---|
| `TEL.dout[i].current` | L1 (DO0-7) / L2 (DO8-15) | i mod 8 | 0-1 | bytes 6-7 + FPGA rx time | >= 20 Hz | 100 |
| `TEL.dout[i].temperature` | L1/L2 | i mod 8 | 2-3 | bytes 6-7 | >= 20 Hz | 100 |
| `TEL.dout[i].vout` | L1/L2 | i mod 8 | 4-5 | bytes 6-7 | >= 20 Hz | 100 |
| `TEL.dout[i].flags` | L1/L2 | i mod 8 | 8 | bytes 6-7 | >= 20 Hz | 100 |
| `TEL.dout_bank[i].vs` | L1 (bank a) / L2 (bank b) | 8 | 0-3 | FPGA rx time | >= 20 Hz | 100 |
| `TEL.dout[i].fault_detail` | L1/L2 | 10 | 0-4 | FPGA rx time | >= 20 Hz | 100 |
| `TEL.dic.sensor_group[i].mv` | L0 | 0 | 0-5 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.dic.limiter_fault` | L0 | 0 | 6 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.dic.safety_supply_fault` | L0 | 0 | 7 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.dic.safe24_mv` | L0 | 0 | 8-9 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.card[i].mcu_temperature` | L0 p1 / L1,L2 p8 / L3 p5 | see source | DIC 0-1, DO 4-5, ACC 8-9 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.card[i].vdd` | L0 p1 / L1,L2 p8 | see source | DIC 2-3, DO 6-7 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.card[i].link_counters` | L0 p2 / L1,L2 p9 / L3 p6 | see source | 0-9 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.ai[i].raw` | L3 | i (0-3) | 0-5 | bytes 2-3 | >= 20 Hz | 100 |
| `TEL.ao[i].readback` | L3 | 4 | 0-3 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.acc.ai_ref_mv` | L3 | 5 | 0-1 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.acc.ai_sensor_supply_mv` | L3 | 5 | 2-3 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.acc.ai_sensor_supply_fault` | L3 | 5 | 4 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.acc.pwm_aux_fault` | L3 | 5 | 5 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.acc.iso_supply_pgood` | L3 | 5 | 6 | FPGA rx time | >= 5 Hz | 200 |
| `TEL.eia.status_raw` | 0x10 | 0 | 0-3 | FPGA rx time | >= 20 Hz | 100 |
| `TEL.ex8.status_raw` | 0x11 | 0 | 0-2 | FPGA rx time | >= 20 Hz | 100 |
| `TEL.fpga.core` | 0x80 | 0-1 | 0-9 | FPGA rx time | >= 20 Hz | 100 |
| `TEL.fpga.port_counters[i]` | 0x81-0x86 | 0 | 0-9 | FPGA rx time | >= 20 Hz | 100 |

| Host-side name | Source | Rate | Stale after (ms) |
|---|---|---|---|
| `HOST.i2c.psm.entry[i].v` | INA238AIDGSR bus voltage per entry (core, field-a, field-b) on the PSM | 10 Hz | 500 |
| `HOST.i2c.psm.entry[i].i` | INA238AIDGSR shunt current per entry | 10 Hz | 500 |
| `HOST.i2c.module[i].temperature` | AT30TSE752A-XM8M-T per card | 1 Hz | 5000 |
| `HOST.i2c.module[i].mir1` | AT30TSE752A EEPROM MIR-1 record | power-up and on request | - |
| `HOST.onewire.xf.identity` | XF module 1-Wire EEPROM through the EIA bridge | qualification and after replacement | - |
| `HOST.tty.rs485.errors` | kernel RS-485 tty and MB2HAL num_errors | 1 Hz summary | 5000 |
| `HOST.socketcan.errors` | mcp251xfd SocketCAN error counters and bus-off | 1 Hz summary | 5000 |
| `HOST.sysfs.soc_temperature` | compute module SoC thermal zone | 1 Hz | 5000 |

### 8.2 Fault history ring

- **FPGA layer:** the 256-record event ring (3.11) and the FLT3 first-fault page (3.14). Both survive a host crash while the FPGA keeps power; both are lost at FPGA reset.
- **Host layer:** the driver writes two 64-byte records per cycle into a preallocated 4,096-cycle RAM ring from the servo thread (single producer, lock-free): HR1 (status facts) and HR2 (commands as sent). A non-real-time historian reads it. On every section 04 trigger it freezes 2 s before and 2 s after, writes the window to host storage (write temporary file, fsync, rename) and writes summaries to the cartridge FM24V02A-G ring (section 04 12.2). Records carry only values from named transport fields with their timestamps and validity. Diagnoses are a separate record type that cites record IDs (section 04 12.1); the AI may write diagnoses and next tests, never facts.

HR1 (status, per cycle):

| Bytes | Field | Content |
|---|---|---|
| 0–1 | `magic` | 'H1' |
| 2 | `version` | 1 |
| 3 | `flags` | b0 trigger cycle; b1 post-trigger; b2 FB CRC error this cycle; b3 CMD CRC error |
| 4–7 | `cycle` | u32 servo cycle counter |
| 8–11 | `host_us` | CLOCK_MONOTONIC us, low 32 bits |
| 12–13 | `wake_latency_us` | u16 |
| 14–15 | `completion_us` | u16, C_n |
| 16–19 | `snapshot_ticks` | CNF3 16-19 |
| 20–23 | `fault_word` |  |
| 24–27 | `safety_word` |  |
| 28–29 | `armed_mask` |  |
| 30–31 | `pos_continuity` |  |
| 32–33 | `alarm_levels` |  |
| 34–35 | `enable_after_gating` |  |
| 36–38 | `din` |  |
| 39 | `din_age` |  |
| 40–41 | `dout_image` |  |
| 42–43 | `dout_applied` |  |
| 44–45 | `dout_fault` |  |
| 46–51 | `port_status` |  |
| 52–53 | `update_interval_us` |  |
| 54–55 | `late_updates` |  |
| 56–57 | `rate_nonzero_mask` |  |
| 58 | `event_seq` |  |
| 59 | `telemetry_source` |  |
| 60–61 | `host_spi_errors` | low 16 bits |
| 62–63 | `crc16` | CRC-16/CCITT-FALSE over 0-61 |

HR2 (commands, per cycle):

| Bytes | Field | Content |
|---|---|---|
| 0 | `magic` | 'C' |
| 1 | `version` | 1 |
| 2–3 | `cycle_low` | matches HR1 cycle low 16 bits |
| 4–51 | `rates` | 12 x s32 as sent |
| 52–53 | `pwm0_duty` |  |
| 54–55 | `pwm1_duty` |  |
| 56–57 | `aout0_code` |  |
| 58–59 | `aout1_code` |  |
| 60 | `output_requests` | CS_CMD byte 66 |
| 61 | `arm_summary` | b0-1 probe arm; b2 any index arm |
| 62–63 | `crc16` | over 0-61 |

### 8.3 Display rule (T4) as carried by the protocol

- Every per-cycle input has a validity source: port state and `din_age`/`ain_age` for card data, `encoder_valid_mask`, `mpg_status`, `freq` NO_SIGNAL, the safety word.
- Every telemetry value carries its FPGA accept time and card-reported age; the driver publishes `-valid` and `-age`; one stale rule: the fixed per-source limit of section 3.12 and 8.1a.
- Pins without a source are published as unavailable, never as a number: `cnc1.io.P.temperature` on s0, s1 and l4, `cnc1.io.P.vdd` on l3, s0, s1 and l4, and every per-port 5 V/24 V limiter voltage (fault flag only).
- An output's current is **not measured** while the output is off (ISNS 0xFFFF), is flagged when below the card's qualified accuracy range, and is shown as unavailable or stale, never as 0 A.
- Accuracy is verified across the declared load range on built cards (section 03 lists 0.10–0.50 A for the DO test) [ME]; the card factory record stores its calibration and the lower accuracy limit it was verified to.

## 9. Hand-offs

**Hardware requirements for Codex (IS-1):**

- CS_CMD: a second host chip select to the FPGA; the host SPI path then needs five buffered channels (SCLK, MOSI, CS_FB, CS_CMD towards the FPGA, MISO back), so the single SN74AVC4T774PWR (four bits) needs a second buffer device or a wider part; one FPGA input; the host IRQ line of the earlier draft is dropped (the protocol is polled)
- SERVO_MARK: one spare compute GPIO routed to a test point on the compute carrier for the timing bench
- Host SPI path qualification at 6.25 MHz (the recorded host_spi_buffer budget is 5 MHz); until then IS-1 budgets at 5 MHz
- IOL1 x4 (DIC, DOA, DOB, ACC): SCLK, CMD, RSP, CS_N point-to-point with Ioff buffers and series termination at each card; 4 slot-strap bits per slot on the base
- Card MCU: STM32G031C8T6 on DIC, STM32G031K8T6 on DOA, DOB and ACC; SPI1 slave with DMA; IWDG hardware option; CARD_EN pin with pull-down ANDed with OUT_PERMIT_k into every output enable; SWD factory pads only
- EIA (24-bit) and EX8 (16-bit) parallel-in status shift registers with a fixed 1010 marker at the far end
- CAN: MCP2518FDT-E/SL on a compute SPI bus separate from the motion SPI; RS-485: compute UART with RTS for kernel RS-485 direction control; both transceivers isolated on ACC (section 03)
- PSM entry voltage/current monitors readable on a host I2C branch
- Motion-card temperature: the AT30TSE752A-XM8M-T fitted to every electronic card (section 02 section 9) is the MC board sensor; place it near the FPGA and the watchdog/permission logic
- DOA/DOB: 2 x TPS274C65ASRHAR in addressable SPI mode behind one ISO7762FDBQR (4 forward: SCLK, SDI, CS_N, DO_EN; 2 reverse: SDO and the wired-OR FLT of both devices); the F variant's default-low outputs leave DO_EN low when the logic side is unpowered
- MC slot status register (input-only, 40 bits, marker 1010 at the far end, 74HC165-class) reading presence A/B and power-good of EIA, EX8, DIC, DOA, DOB, ACC, ESC, CMC and XS and SCART presence A/B; those 29 lines cross the base to the MC connector; SSR_CLK/SSR_LOAD_N/SSR_DATA are local FPGA pins
- OPI_OK_OUT and OPI_OK_BOE latches (SN74LVC2G74DCUR) on the MC and the OPI_REARM_O strobe; PERMIT_OUT drive = TX_PERMIT AND PERMIT_OUT_REQ (FPGA pin, 10 kOhm pull-down) on the MC (section 04 6.2)
- 10 kOhm pull-downs on EXT_PERMIT_3V3 and PROCESS_PERMIT_EXT_3V3 at the MC receiver, so an absent, unseated or unpowered DIC reads 'not permitted'; qualified DIC_OK (DIC presence A and B and DIC power-good) in base_ok and out_base_ok (section 04 6.2)
- on every DO and ACC card an OUT_EN latch (one half of SN74LVC2G74DCUR; ACC: second half for PROC_PERMIT) with CLR_N = the qualified OUT_PERMIT_k net, in series with CARD_EN in every output enable, Q read by the card MCU
- 10 kOhm pull-downs on the STEP and DIR inputs of every AM26C31 on the MIA and the MX4 (idle low, matching the FPGA's STEP-low idle state)

**Implementation owned by Claude (IS-1):** ABI 3 encoder/decoder and vectors in `gateware/tools/protocol.py`; two-chip-select SPI endpoint with 176/96-byte frames, the event ring and the telemetry mirror; four IOL1 masters with CRC-32C and the port rules of 4.6; the EIA/EX8 status-register readers; the section 04 safety logic this protocol reports; the `cnc1` driver and HAL pins of section 7 with the HR1/HR2 ring; STM32G031 card firmware (IOL1 endpoint, accept timer, IWDG, readback, telemetry, bootloader); the `cnc1can` component; configuration-service support for CONFIGURE_IO, card identity and the display rule; the timing instrumentation of 5.7.

## 10. Blockers (exact dependencies)

| Item | Blocked by |
|---|---|
| Measured host overhead, jitter and the 700 us distribution | CM5102016 purchase (reference compute module), motion-card prototype, logic analyser >= 200 MS/s |
| 72-hour combined-load test | all prototype cards, drives, quadrature/pattern generators and independent pulse counters (section 04 section 14) |
| FPGA fit of 2 frame channels, 4 IOL1 masters with CRC-32C, 2 status registers, 256-entry event ring and telemetry mirror | Efinix Efinity place-and-route (not installed) |
| Card processing inside the 59.6 us window and the <= 20 us apply allocation | an STM32G031 development board (purchase) or the built cards; firmware can be written and host-tested meanwhile |
| TPS274C65ASRHAR complete ADC round-robin period | the datasheet gives 128 us per measurement only; measure on a built DO card |

Everything else in this section (RTL, simulation of the endpoint and the IOL1 link, the driver against Verilated RTL, card firmware compiled and unit-tested on the host, the service) can proceed without hardware.

## 11. Sources opened for this section

- TI TPS274C65 product page and datasheet SLVSFZ2C (Feb 2024): https://www.ti.com/product/TPS274C65 , https://www.ti.com/lit/ds/symlink/tps274c65.pdf (variant table: AS and ASH have the ADC and current sense, BS has neither; 10-bit ADC; 128 µs measurement update; SPI ≤ 10 MHz with optional CRC; DO_EN behaviour; SPI watchdog 400 µs–1.2 s; current-sense table)
- ST STM32G031K8 product page and DS12992: https://www.st.com/en/microcontrollers-microprocessors/stm32g031k8.html (two SPIs up to 32 Mbit/s master and slave; independent and window watchdogs); STM32G0 reference manual RM0444 CRC unit (programmable polynomial and size); DigiKey listings for STM32G031K8T6 and STM32G031C8T6
- Microchip MCP2518FD: https://www.microchip.com/en-us/product/mcp2518fd ; orderable MCP2518FDT-E/SL (SOIC-14); Linux `drivers/net/can/spi/mcp251xfd`
- LinuxCNC MB2HAL documentation, local copy `research/vendor-src/linuxcnc/docs/src/drivers/mb2hal.adoc` (pin names, `num_errors`, run-enable warning) [SI]
- Repository: `gateware/PROTOCOL.md`, `cnc1/PROTOCOL_V2.md`, `cnc1/src/cnc1.h`, `cnc1/src/hal_cnc1.c`, `docs/MOTION_EXPANSION_8_TO_12.md`, `docs/EXPANDED_HARDWARE_TARGET.md`, `reports/audit-2026-09-28/ELECTRICAL_HANDOFF.md` and `part-selections.json`, sections 03 and 04 of IS-1 [SI]

---

Interface specification revision IS-1. Nothing in this section is implemented, measured or ready for manufacture.
