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
| D01-1 | Two chip selects on the one host SPI bus with fixed, different frame lengths: **CS_FB 176 bytes** (feedback read, before LinuxCNC computes) and **CS_CMD 96 bytes** (command write, after). Motion, the complete machine-control I/O, feedback, latched faults and validity travel in these two transactions every cycle; there is no third "I/O page" exchange | Wire time plus guards per 1 ms cycle: {{WIRE5}} µs at 5 MHz and {{WIRE625}} µs at 6.25 MHz, against {{REJ3X128}} µs for the record's 2 × 128 B plus a separate 128 B I/O exchange and {{REJSYM}} µs for two symmetric 176 B frames [AR]. The FPGA must know the response type at CS assertion (the snapshot instant), before any command byte arrives, so the type is selected by the chip select, not by an opcode | One extra FPGA input, one extra Ioff buffer channel, one host CS line; unpriced. Gains full I/O at 1 kHz inside the 700 µs target allocation at both clock rates (section 5) | Standard |
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

{{OPCODES}}

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

{{TABLE:fb_command}}

FB_READ payload, bytes 16–173 (offsets below are relative to byte 16):

{{TABLE:fb_read_payload_at_16}}

### 3.6 CNF3 feedback response (CS_FB, 176 bytes)

Sampled at the synchronized CS_FB assertion. This is the per-cycle servo status of T2: motion feedback, all machine-control inputs, output readback, latched faults and data validity for 12 motors and 12 encoders at the same time, with every expansion field present whether or not MX4 or EX8 is fitted.

{{TABLE:fb_response_CNF3}}

### 3.7 CS_CMD command (96 bytes)

{{TABLE:cmd_command}}

The FPGA commits the twelve rates and the whole output image atomically at CS release. With I/O disabled every output field must be zero, otherwise the frame is rejected.

### 3.8 CNS3 status response (CS_CMD, 96 bytes)

{{TABLE:cmd_response_CNS3}}

### 3.9 Fault word (CNF3 and CNS3 bytes 20–23)

Bits 0–8 keep the record's meaning; bits 9–12 are section 04's additions; bits 13–24 are new here; bits 25–27 are the safety-interface faults of section 3.4a.

{{FAULTS}}

### 3.10 Safety and power word (CNF3 164–167, CNS3 30–33)

Physical sources, fault responses and HAL names of bits 0–22 are fixed by section 04 section 8; bits 23–26 are the section 03 XS1 inputs; bit 27 is the EX8 power-good from its status register; bits 28–29 are the OPI_OUT and OPI_BOE latches (section 04 section 4.2); bit 30 is `reset_arm_ready` (section 3.4a).

{{SAFETY}}

### 3.11 Event ring

The FPGA hardware event ring (section 04 12.2) holds 256 records of 20 bytes with 50 MHz timestamps. CNS3 bytes 36–55 always show the oldest unacknowledged record (`event_seq` 0 = empty). The host stores it, then acknowledges it with `event_ack` in the next FB_READ; the FPGA pops the record only when `event_ack` equals the sequence it last showed, so a lost CNS3 simply shows the same record again. Delivery latency is one cycle when the ring is empty and one cycle per queued record otherwise. A full ring sets EVENT_OVERFLOW and CNF3 `event_status` b7; probe and index results after an overflow are unusable.

{{EVENTS}}

### 3.12 Telemetry mirror

The FPGA keeps the latest copy of every card telemetry page, of the status registers and of its own counter pages, each with the core-tick time it was accepted and the card-reported age of the values. Each CNS3 carries one 22-byte entry (bytes 56–77) in a fixed round robin over all entries. A host priority request in FB_READ bytes 17–18 (for a value a screen is showing) may take **at most every other slot**, so it can never starve the rotation. The IS-1 default fit (DIC 3 pages, DOA 12, DOB 12, ACC 8, EIA 1, EX8 1, FPGA core 2, FPGA port counters 6) has **{{MIRROR}} entries**, so every entry is delivered at least every {{MIRROR}} ms (about 22 Hz) without priority requests and at least every **{{MIRRORMAX}} ms** (about 11 Hz) with them [AR]. Output current, temperature and VOUT are therefore at most 90 ms delivery + 3.05 ms card sample age = **93.05 ms** old at the host [AR on REQ], inside their 100 ms stale limit. Page contents are in section 4.9.

Age of a telemetry value at display = display time − (FPGA accept time − card-reported age). The driver publishes that age with every value. **One stale rule (T4):** each source has one fixed stale limit, `stale_ms` in the telemetry map and host-source tables of section 8.1a (100 ms for output-card values, 200 ms for slow supply and temperature values, 500 ms for host-I2C entry monitors, 5 s for 1 Hz host temperatures) [REQ]; a value older than its limit is shown stale, a source without a path is unavailable, and neither is ever shown as zero. Section 03 section 6 cites this rule.

### 3.13 CONFIGURE and CONFIGURE_IO

Both are sent on CS_FB (176-byte command capacity) while disarmed with I/O disabled, and both keep the record's rule that a rejected configuration clears the corresponding `*_config_valid`, so nothing configured earlier survives a failed reconfiguration.

CONFIGURE payload (opcode 0x06), relative to byte 16:

{{TABLE:configure_payload_at_16}}

CONFIGURE_IO page 0 (opcode 0x07), relative to byte 16:

{{TABLE:configure_io_page0_at_16}}

CONFIGURE_IO page 1:

{{TABLE:configure_io_page1_at_16}}

CONFIGURE_IO pages 2–9 forward card configuration (section 4.4) to one port; the card validates it, applies it only in the SYNCED state and reports its CRC-32C, which the host compares with the stored record:

{{TABLE:configure_io_card_pages_at_16}}

### 3.14 Pages returned on CS_FB after READ_PAGE

Page 0 (motion capabilities; the record's §5.6 content, relocated and extended):

{{TABLE:cap3_page0}}

Page 1 (I/O capabilities):

{{TABLE:cap3_page1}}

Page 2 (first-fault snapshot, frozen at the first latched fault until SYNC):

{{TABLE:flt3_page2}}

Page 3 (card identity collected from IOL1 IDENT_READ frames):

{{TABLE:idp3_page3}}

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

{{VECTORS}}

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

{{TABLE:iol1_command}}

Response (card → FPGA), prepared by the card before the transaction starts:

{{TABLE:iol1_response}}

### 4.4 Class payloads

{{CLASSES}}

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

{{TELEMETRY}}

TPS274C65ASRHAR measurement facts used [DS]: 10-bit ADC; round robin of current, temperature, VOUT and VS; "ADC sample update time in each measurement" 128 µs; current is sensed only while the switch is on; the ADC reports FF otherwise; sense current at RSNS = 1 kΩ is 0.834–0.890 mA at 1 A, 0.410–0.45 mA at 500 mA, 0.151–0.184 mA at 200 mA, 0.068–0.092 mA at 100 mA and 0.02–0.054 mA at 50 mA. The typical column of that table is not legible in the extracted datasheet text, so IS-1 states the spread relative to the midpoint of the minimum and maximum: ±3.2 % at 1 A, ±4.7 % at 500 mA, ±9.9 % at 200 mA, ±15 % at 100 mA and ±46 % at 50 mA [AR on DS]. The ADC reference (2.72–2.85 V [DS]) and the sense-resistor tolerance add to this before the per-channel factory calibration stored in the card record. IS-1 therefore declares the qualified display range as 0.10–0.50 A per output; below 0.10 A the value is flagged "below qualified range", and accuracy is verified by measurement at 0.10, 0.25 and 0.50 A per channel at both ambient extremes, never at one convenient load [ME required]. The datasheet does not state the complete round-robin period for four channels; if each measurement takes 128 µs sequentially it is 16 × 128 µs = 2.048 ms [AR, interpretation, to be measured].

### 4.10 EIA, EX8 and MC slot status registers

The MC slot status register is local to the motion card: 29 presence and power-good lines arrive through the base (section 02 section 6) from every slot that has no other path to the FPGA. Its bits appear in CNS3 `slot_status` every cycle and drive `port_status` b3, SLOT_FAULT and `cnc1.module.<slot>.present/.power-good`.

{{STATUSREG}}

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

{{SCHEDULE}}

Reading the table: at 5 MHz the host may spend at most **{{OV5}} µs** in total on scheduling latency, ioctl overheads and computation for C(k) to meet 700 µs ({{OV5K}} µs for the 1 ms period); at 6.25 MHz **{{OV625}} µs** ({{OV625K}} µs). The allocation above uses {{ALLOC}} µs. If the bench exceeds the allocation, the finding is recorded and the decision rules in 5.7 apply; no rate, timeout or limit is raised.

2 kHz is not feasible: the wire time alone is {{TWOK}} of a 500 µs period at 5 MHz [AR].

### 5.3 Input data age and output update latency

| Quantity | Path | 5 MHz | 6.25 MHz | Label |
|---|---|---:|---:|---|
| Counter age at use (steps, encoders, MPG, alarms, safety bits) | CNF3 snapshot → FB wire → ioctl return → decode | {{AGE5}} µs | {{AGE625}} µs | [AR on REQ] |
| DI age at use, no rejected frame | card sample → IOL1 (staleness at the snapshot ≤ 240.6 µs: ≤ 100 µs sample-to-frame, 40.4 µs frame and guards, 0.2 µs check, ≤ 100 µs until the next frame replaces it) → counter path; plus configured debounce and ISO1212 propagation | {{DIAGE5}} µs + filter | {{DIAGE625}} µs + filter | [AR on REQ] |
| DI/AI age at use, worst valid case | two rejected frames leave the data valid (240.6 + 2 × 100 = 440.6 µs); the third latches the port fault and invalidates it; `din_stale_limit_us` / `ain_stale_limit_us` are limited to 250–440 µs, so the snapshot age of valid data is ≤ the configured limit ≤ 440 µs → counter path | {{DIWORST5}} µs + filter | {{DIWORST625}} µs + filter | [AR on REQ] |
| Motion command latency | cnc1.write encode → CMD ioctl → CS_CMD wire → commit; new rate in force ≤ 3 core ticks later | {{CMD5}} µs | {{CMD625}} µs | [AR on REQ] |
| DO/AO update latency | commit → next IOL1 frame (≤ 100 µs) → 40.4 µs frame and guards → card apply (≤ 20 µs [REQ]) = ≤ 160.4 µs; plus driver switching or DAC settling | {{DO5}} µs + switching | {{DO625}} µs + switching | [AR on REQ] |
| Status-register bit (pendant, supply faults) staleness at the snapshot | change → next read (≤ 100 µs) → agreeing second read (+100 µs) → read time (3.84 µs shift + 0.32 µs load) | 204.16 µs | 204.16 µs | [AR] |

IS-1 targets [REQ]: counter age ≤ 400 µs; DI age ≤ 600 µs plus the configured debounce with no rejected frame and ≤ 750 µs plus debounce in the worst valid case; DO command-to-driver ≤ 400 µs plus switching. DI and AI are invalid at the earlier of their stale limit and the port fault, never later, so data older than the published bound is never reported as valid. `tools/interface_spec_validate.py` checks the configurable range against both bounds.

### 5.4 I/O link schedule (FPGA-internal, independent of the host)

Per port and 100 µs period: 1.0 µs guard + {{LINKFRAME}} µs frame + 1.0 µs guard = {{LINKSLOT}} µs on the wire, leaving a {{LINKWIN}} µs card processing window [AR]. All four ports and both status registers run in parallel. The host exchange never waits for a card; it reads the latest validated copy.

### 5.5 Watchdog margins (kept distinct)

- FPGA command watchdog: 5 ms without an accepted ARM/UPDATE. Nominal UPDATE spacing 1 ms leaves 4 ms [AR]; the driver keeps its rule period ≤ watchdog/2.
- External watchdogs (section 04 5.1): 9.26/11.04/13.02 ms min/nom/max including the CWD leakage allowance (9.51/12.67 ms from capacitor and IC tolerances alone), with one progress pulse per accepted ARM or UPDATE (WD_M) and per accepted UPDATE or IO_WRITE while I/O is enabled (WD_O). Legal spacing is below 5 ms, so the margin to tWD(min) is > 4.2 ms [AR on DDR].
- I/O watchdog in the FPGA: 5 ms without accepted UPDATE/IO_WRITE while I/O is enabled → IO_WATCHDOG.
- Card accept timer 1.0 ms and IWDG ≤ 2 ms (section 4.7).
- Fault-to-inhibit ≤ 20 ms: section 04 5.5 and 7.2; not a function of the servo schedule.

### 5.6 Rejected alternatives

| Alternative | Wire time at 5 MHz per cycle | Why rejected |
|---|---:|---|
| Record's 2 × 128 B plus a separate 128 B I/O exchange | {{REJ3X128}} µs | Leaves {{REJ3X128LEFT}} µs for the whole host at 700 µs [AR] |
| Two symmetric 176 B frames on one chip select | {{REJSYM}} µs | Wastes 80 bytes each way |
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

{{CONNECTIONS}}

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

{{HALREG}}

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

{{DIAG}}

### 8.1a Telemetry map and host-side sources

Every `TEL.*` name used in `spec/terminals.json` resolves to a mirror page below, and every `HOST.*` name to a host-side source that never passes through CNC1 or the servo thread.

{{TELMAP}}

### 8.2 Fault history ring

- **FPGA layer:** the 256-record event ring (3.11) and the FLT3 first-fault page (3.14). Both survive a host crash while the FPGA keeps power; both are lost at FPGA reset.
- **Host layer:** the driver writes two 64-byte records per cycle into a preallocated 4,096-cycle RAM ring from the servo thread (single producer, lock-free): HR1 (status facts) and HR2 (commands as sent). A non-real-time historian reads it. On every section 04 trigger it freezes 2 s before and 2 s after, writes the window to host storage (write temporary file, fsync, rename) and writes summaries to the cartridge FM24V02A-G ring (section 04 12.2). Records carry only values from named transport fields with their timestamps and validity. Diagnoses are a separate record type that cites record IDs (section 04 12.1); the AI may write diagnoses and next tests, never facts.

HR1 (status, per cycle):

{{HR1}}

HR2 (commands, per cycle):

{{HR2}}

### 8.3 Display rule (T4) as carried by the protocol

- Every per-cycle input has a validity source: port state and `din_age`/`ain_age` for card data, `encoder_valid_mask`, `mpg_status`, `freq` NO_SIGNAL, the safety word.
- Every telemetry value carries its FPGA accept time and card-reported age; the driver publishes `-valid` and `-age`; one stale rule: the fixed per-source limit of section 3.12 and 8.1a.
- Pins without a source are published as unavailable, never as a number: `cnc1.io.P.temperature` on s0, s1 and l4, `cnc1.io.P.vdd` on l3, s0, s1 and l4, and every per-port 5 V/24 V limiter voltage (fault flag only).
- An output's current is **not measured** while the output is off (ISNS 0xFFFF), is flagged when below the card's qualified accuracy range, and is shown as unavailable or stale, never as 0 A.
- Accuracy is verified across the declared load range on built cards (section 03 lists 0.10–0.50 A for the DO test) [ME]; the card factory record stores its calibration and the lower accuracy limit it was verified to.

## 9. Hand-offs

**Hardware requirements for Codex (IS-1):**

{{HWREQ}}

**Implementation owned by Claude (IS-1):** ABI 3 encoder/decoder and vectors in `gateware/tools/protocol.py`; two-chip-select SPI endpoint with 176/96-byte frames, the event ring and the telemetry mirror; four IOL1 masters with CRC-32C and the port rules of 4.6; the EIA/EX8 status-register readers; the section 04 safety logic this protocol reports; the `cnc1` driver and HAL pins of section 7 with the HR1/HR2 ring; STM32G031 card firmware (IOL1 endpoint, accept timer, IWDG, readback, telemetry, bootloader); the `cnc1can` component; configuration-service support for CONFIGURE_IO, card identity and the display rule; the timing instrumentation of 5.7.

## 10. Blockers (exact dependencies)

{{BLOCKERS}}

Everything else in this section (RTL, simulation of the endpoint and the IOL1 link, the driver against Verilated RTL, card firmware compiled and unit-tested on the host, the service) can proceed without hardware.

## 11. Sources opened for this section

- TI TPS274C65 product page and datasheet SLVSFZ2C (Feb 2024): https://www.ti.com/product/TPS274C65 , https://www.ti.com/lit/ds/symlink/tps274c65.pdf (variant table: AS and ASH have the ADC and current sense, BS has neither; 10-bit ADC; 128 µs measurement update; SPI ≤ 10 MHz with optional CRC; DO_EN behaviour; SPI watchdog 400 µs–1.2 s; current-sense table)
- ST STM32G031K8 product page and DS12992: https://www.st.com/en/microcontrollers-microprocessors/stm32g031k8.html (two SPIs up to 32 Mbit/s master and slave; independent and window watchdogs); STM32G0 reference manual RM0444 CRC unit (programmable polynomial and size); DigiKey listings for STM32G031K8T6 and STM32G031C8T6
- Microchip MCP2518FD: https://www.microchip.com/en-us/product/mcp2518fd ; orderable MCP2518FDT-E/SL (SOIC-14); Linux `drivers/net/can/spi/mcp251xfd`
- LinuxCNC MB2HAL documentation, local copy `research/vendor-src/linuxcnc/docs/src/drivers/mb2hal.adoc` (pin names, `num_errors`, run-enable warning) [SI]
- Repository: `gateware/PROTOCOL.md`, `cnc1/PROTOCOL_V2.md`, `cnc1/src/cnc1.h`, `cnc1/src/hal_cnc1.c`, `docs/MOTION_EXPANSION_8_TO_12.md`, `docs/EXPANDED_HARDWARE_TARGET.md`, `reports/audit-2026-09-28/ELECTRICAL_HANDOFF.md` and `part-selections.json`, sections 03 and 04 of IS-1 [SI]

---

Interface specification revision IS-1. Nothing in this section is implemented, measured or ready for manufacture.
