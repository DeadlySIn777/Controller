# Motor capacity: all twelve interfaces on one motherboard

**Current user decision, 30 September 2026:** fit all twelve differential STEP/DIR motor interfaces directly on the one active custom motherboard, each with its own enable and alarm. At least eight usable motors remain the minimum capacity; no custom MX4/XTB motors-9–12 card, eight-channel depopulation or paid unlock is adopted. Four standard ABZ encoders, 24 general DI/16 smart DO, the remaining process/analog/comms/protection/status functions, 20 ms independent fault-to-inhibit, integrity/freshness, safe defaults, offline settings/licence recovery and deliberate restart remain required. Optional external specialty/accessory expansion adds useful capability without supplying missing mandatory motor channels.

The physical integration contract is [MOTHERBOARD_IS2.md](MOTHERBOARD_IS2.md), with current service in [MODULAR_REPAIR_AND_MEMORY.md](MODULAR_REPAIR_AND_MEMORY.md), decisions in [ADR-024](ARCHITECTURE_DECISIONS.md#adr-024--consolidate-into-one-motherboard-with-commodity-modules) and measurable gates in [CURRENT_ACCEPTANCE_GATES.md](CURRENT_ACCEPTANCE_GATES.md). The untouched external IS-1/CNC3 source supplies reusable logical/electrical/protocol requirements, with a versioned transition required for board-region identity/calibration rather than fabricated removable-card presence.

**Evidence boundary:** MC r0.4/revision-14 is partial 327-part source/native work with twelve STEP/DIR/enable Ioff paths, not twelve complete motor interfaces or the finished motherboard. Six-joint/two-encoder RTL/LinuxCNC/synthesis evidence remains historical. Do not treat the scratch resource estimates, draft ABI, recorded price arithmetic or older card timing model below as deployed CNC3, vendor device fit, full routing or physical qualification. Complete all-channel circuits, pin/bank allocation, gates/defaults, expanded RTL/driver/runtime, power and fault tests against the current target.

Current work: preserve reusable circuits and existing copper; consolidate remaining interfaces into the same board; reconcile a versioned fitted twelve-channel capability map with CNC3 and the UI/CLI; test eight- and twelve-motor machine configurations on the fitted twelve-interface hardware while retaining all promised general I/O and simultaneous optional encoder/process expansion. Cost the complete motherboard and purchased modules separately at 1/10/100 (and production study 1,000), with unknown blocks explicit and actual service spare costs. Normal configuration masks select machine usage; they do not create a paid hardware-channel unlock.

**Additional user motion target, 1 October 2026:** qualify twelve simultaneously active STEP/DIR channels at up to 2 MHz per channel, independent per-channel STEP-high/low and DIR-setup/hold timing, polarity and maximum-rate profiles, atomic twelve-channel command updates in a deterministic 1 kHz LinuxCNC servo cycle, four ABZ encoder inputs in the base and qualified encoder expansion toward twelve that can coexist with all twelve motors. Each drive profile must clamp the commanded rate to its verified timing and electrical limits. This is a qualification target, not an implemented twelve-channel runtime, selected faster timing profile, electrical-rating increase or guarantee for every supported compute module. The one-motherboard architecture and all fitted interfaces remain unchanged.

The retained CNC3/IS-1 contract has separate 96-byte command and 176-byte feedback transactions. At the nominal 6.25 MHz host SPI ceiling, their 2,176 bits take 348.16 µs of ideal wire time; a 700 µs complete-exchange allocation leaves 351.84 µs theoretically for guards and software/transport overhead. This arithmetic does not prove loaded target latency or a 1 kHz real-time deadline. The legacy 50 MHz step generator requires `high + low + 1` ticks between STEP rises: merely raising MAX_RATE is invalid. An illustrative 12/12-tick profile gives a 25-tick period, with safe DDS increment at most `floor(2^32/25) = 171798691`; the ceiling increment can create a 24-tick interval and must be rejected. This example is analysis only. The existing historical default remains 195,312.5 pulses/s with six active channels. Qualification must cover all twelve pulse generators simultaneously, reversals, timing boundaries, atomic commit, encoder coexistence, watchdog/inhibit and actual output signal quality.

The earlier LinuxCNC 2.9.4 record reports that twelve- and sixteen-joint motion modules load and seventeen is rejected; it is a module-loading check, not a loaded machine, chosen kinematics, verified compute affinity or twelve-motor real-time proof. CPU affinity is module-specific commissioning work, not a guarantee. Exact attachment/source hashes and the unchanged historical record are archived in `reports/motherboard-docs-20261001/motion-target-2MHz-r01/receipt.json`.

## Historical eight-plus-four draft and review record

The complete earlier record follows unchanged. Its plug-in-MX4/fixed-base/removable-FPGA physical selections, card-presence/tamper topology, old implementation instructions and open-choice language are **superseded history**, not current build instructions. Retained logical/electrical/fault requirements still apply where not explicitly physically superseded. The history's statements about what was implemented or tested retain their original date and scope. The exact pre-transition bytes are archived in `reports/motherboard-architecture-transition-20260930/planning-docs-before/docs/MOTION_EXPANSION_8_TO_12.md`.

---

# Motion expansion: eight motors minimum, twelve by plug-in module

Design record, 28 September 2026. **This is a proposal. None of it is implemented. No RTL, driver, HAL, configuration-service, schematic or PCB change described here exists yet, and nothing here is ready for manufacture.** The six-joint/two-encoder CNC1 endpoint, its ABI v1/v2, its synthesis result and its tests remain historical baseline evidence. They are not eight- or twelve-channel evidence.

**Requirements reconciliation, 30 September 2026:** the record below preserves the earlier ABI v3 draft, option arithmetic and review history; its open-choice language is superseded where the user has already decided. Confirmed: eight motors standard, motors 9–12 on a plug-in module and a factory-fitted twelve-motor version; an individual enable and alarm for every motor; a fixed wiring base and replaceable FPGA motion card with clock, flash and supervisory circuitry; 24 general DI and 16 general DO; identity, sequence/freshness and CRC validation before serialized-card outputs change; and 20 ms fault-to-inhibit, without relaxing it to fit the TPS3431. US$400 is the preliminary controller-assembly reference, superseding all-inclusive price assumptions; screens and other complete kits, expansion, improvement deltas and spare cards must be separately costed. This is requirements accounting, not implementation evidence.

**Integration boundary:** a separate worktree at `C:/Users/Gluis/claude-worktrees/controller-interface-spec` contains frozen `docs/CONTROLLER_INTERFACE_SPEC.md` revision IS-1, `spec/*.json`, and CNC3 host codec/core work. That specification supersedes this earlier ABI draft as the proposed shared implementation contract; its reviewed integration into this checkout is still pending. The CNC3 host tests are separate from current CNC1 RTL/LinuxCNC evidence. This reconciliation neither edits IS-1 nor merges its work, and must not be used as a new interface revision. Resolve the detailed interface against that contract in the controlled integration step.

Revision 2, same day. An independent review of revision 1 found 5 safety/ABI defects, 9 medium and 9 minor items. All 23 are closed in this revision; section 18 lists where and how. This revision also adds the pulse-rate statement (section 12), the external-watchdog decision (section 8.1), the reconciliation with Codex's drawn transmitter and permission sheets (section 13), a mapping onto a fixed wiring base with replaceable service modules (section 14) and the first bench measurement plan (section 15). Open user decisions are regrouped by priority in section 17.

Revision 3, same day. An independent verification of revision 2 found that review items 11, 12 and 13 were only partly closed and raised eight further problems (LED-anode voltage, watchdog behaviour while disarmed and six numeric or wording errors). Section 18.1 records how each was checked and closed. Nothing new has been implemented.

Related records: [project memory](../PROJECT_MEMORY.md) (requirement, line 17), [expanded hardware target](EXPANDED_HARDWARE_TARGET.md), [CNC1 ABI v1](../gateware/PROTOCOL.md), [CNC1 ABI v2 discovery](../cnc1/PROTOCOL_V2.md), [modular repair](MODULAR_REPAIR_AND_MEMORY.md), [FPGA synthesis report](../reports/FPGA_SYNTHESIS.md), [twelve-channel transmitter study](../reports/TWELVE_CHANNEL_TRANSMITTER.md), [machine permission](../reports/MACHINE_PERMISSION.md).

## 1. Requirement and working assumptions

**User requirement (28 September 2026, later decisions incorporated):** the controller must run eight motors standard and support motors 9–12 on a plug-in module, also offered factory-fitted. Preserve full I/O, diagnostics, protection and repairability while costing the preliminary US$400 controller assembly and separately priced complete screen/other kits. The earlier Mesa-price included-screen objective remains historical context in [project memory](../PROJECT_MEMORY.md), not the current price ceiling.

| # | Working assumption | Status after review |
|---|---|---|
| A1 | A motor channel is differential STEP/DIR plus one individual drive-enable switch plus one individual drive-alarm input | Accepted. [Project memory](../PROJECT_MEMORY.md) line 17 records eight channels "with individual enable and alarm". Flag: the current RTL has one common `motion_enable` and no alarm inputs (`gateware/rtl/cnc_endpoint.v`). Both are new logic and new I/O. |
| A2 | Motor channels are not axes. A gantry uses two channels | Accepted. LinuxCNC maps them with duplicate trivkins letters (section 10). |
| A3 | Encoders stay at the four ABZ ports ENC0–ENC3 | Accepted. Each encoder costs about 77 FF (about 308 FF for four in the `c_narrow_12_4` mapping, section 6.1; netlist-name estimate) plus two status words. No pin, resource or electrical reason was found to add more. Four encoders do not give feedback for 8 or 12 motors ([target](EXPANDED_HARDWARE_TARGET.md), "Candidate scope"). |
| A4 | The base product must be as cheap as possible | Accepted. It is the main reason channels 9–12 go on a plug-in module instead of every board. |
| A5 | Channels 9–12 use the same electrical interface and connector as channels 1–8 | Added here. One plug type for all motors keeps harnesses interchangeable. |
| A6 | Power-off installation only; no hot-plug in the first release | Added here, per [modular repair §6](MODULAR_REPAIR_AND_MEMORY.md#6-supported-replacement-workflow). |

The earlier request's exact verbatim attachment was not archived in this record, but later confirmed decisions in project memory explicitly preserve individual enable and alarm on every channel. **U12 is resolved; do not ask again or remove interfaces to reduce cost.** A supported drive without a usable alarm/enable behavior needs a documented profile exception and commissioning response; a global power interlock does not count as its per-channel enable circuit.

## 2. Evidence classes used in this record

| Class | Meaning here |
|---|---|
| Source inspection | Reading repository files. No execution. |
| HDL simulation | Icarus Verilog 13 testbenches on scratch copies of the RTL. |
| Lint | Verilator 5.048 `-Wall`. |
| Technology mapping | Yosys 0.52 `synth_efinix` primitive counts. **Not** packing, place-and-route, LE occupancy, timing or a fit. |
| Formal (partial) | Yosys `sat -tempinduct` range invariants. Not full sequential equivalence. |
| Module-load test | LinuxCNC 2.9.4 `halrun` loading modules in the isolated rootfs. No task, GUI, homing or motion. |
| Datasheet / recorded price | Values from TI, Efinix and the repo's recorded DigiKey ladders. |
| Datasheet desk review | A second-source reading of a datasheet with arithmetic (the TPS3851 check in section 8.1). No board, no measurement. |
| Codex schematic evidence | KiCad ERC and netlist validators run by Codex on `hardware/tx_twelve` and `hardware/machine_permission`. Read here by source inspection of their reports; not re-run for this record. |
| Arithmetic / estimate | Derived numbers. Estimates are labelled. |

No ERC, DRC, SPICE, physical measurement, Efinity run or bitstream exists for anything this record proposes.

The probe runs were made in this session's scratch directory, `C:/Users/Gluis/AppData/Local/Temp/claude/C--Users-Gluis-OneDrive-Documents-ChatGPT-Controller/280553e2-7c85-48b3-a5fa-96a4c2e06e60/scratchpad/expansion/` (below: `SCRATCH/`), plus `/root/.cache/controller-lab-linuxcnc/rootfs/work/expansion-probe/` in the WSL rootfs. The scratch directory is temporary. It is not archived evidence. Implementation step P2 (section 16) must reproduce these numbers inside the repository before they are cited as gateware evidence.

## 3. Options considered and choice

Three probes (FPGA mapping, pins/electrical/cost, link timing and LinuxCNC limits) fed three candidate designs. All three chose the same topology: **one T20-class CNC1 endpoint with twelve STEP/DIR generators, M0–M7 built on the base, M8–M11 on a power-off plug-in module wired to the same FPGA.** They differ in cost, safety detail and protocol form.

Topologies rejected by all three, with the probe numbers behind the rejection:

- **(A) All twelve channels populated on every base board.** Rejected on two grounds only. (1) Per-unit cost: every unit, including eight-motor units, pays +$17.97 at qty 1 / +$10.07 at qty 100 of priced parts (recorded prices), plus unpriced enable switches, passives, about 62 placements and area. (2) Edge length: the twelve motor plugs need 420 mm (3.5 mm pitch) to 610 mm (5.08 mm) of edge (arithmetic). Two other figures are **not** reasons to prefer D1. A needs 138 FPGA signals, while D1 needs 145 (section 7.1). CORE_5V reaches 6.35 A in A and also in D1 with the module fitted, and the TX_5V branch in section 7.3 fixes both equally. Codex's drawn `hardware/tx_twelve` sheet is option A; section 13 reconciles it.
- **(C) A second CNC1 endpoint for channels 9–12.** It costs $42.62 of priced parts at qty 1 plus an unpriced oscillator, flash, JTAG, supervisor, permission network, link and PCB. It needs a shared clock, a snapshot/commit strobe, a wired-OR fault and supervisor progress from both endpoints. Gantry pairs cannot be split across endpoints. With a second 128-byte frame it uses 821 µs of a 1 ms cycle at 5 MHz.

### Scores (1–10, higher is better)

| Design | Cost | Feasibility | Timing & safety | Modularity & service | Simplicity | Total |
|---|---:|---:|---:|---:|---:|---:|
| **D1 cost-first, "M8+4"**: passive module, no module regulator or firmware; single 128 B frame; runtime per-channel timing CONFIGURE; FPGA-latched qualification; separate 2-pin FIELD connector | 8 | 7 | 7 | 8 | 7 | **37** |
| D2 modularity-first, "Base-8 + MX4 bay": Ioff buffer gated in hardware, module-local buck, FPGA-enforced required mask, enable readback, capability pages 0–2 | 6 | 7 | 8 | 9 | 6 | 36 |
| D3 timing-and-safety-first: same topology; 128 B read + 72 B write (two fixed lengths, header CRC); FPGA-owned installed set | 7 | 6 | 8 | 7 | 5 | 33 |

Reasons:

- **D1** leaves the least on every base: a header, a small power switch and pull-ups. Its module is passive, so there is no module firmware to service. It is the only design with runtime per-channel STEP/DIR timing. That is necessary because the reference DM542T V4 drive needs 2.5 µs high/low and 5 µs DIR setup, which the current 100-tick (2 µs) build-time defaults do not meet ([target](EXPANDED_HARDWARE_TARGET.md), "Timing goals"). This covers the drive's timing only. The drive's enable polarity is a separate problem (section 8, U11). Weaknesses: the FPGA drives the internal header directly, which leaves back-power and ESD exposure to the FPGA pins; and the endpoint does not itself stop a twelve-motor machine from arming only eight channels.
- **D2** has the strongest service story and two good safety ideas: a hardware-gated Ioff buffer between FPGA and header, and a required mask enforced in the FPGA. It costs more on every base (buffer, eFuse, 3.3 V switch, I2C switch) and on every module (buck converter). It keeps build-time timing, so the reference drive is not supported. It puts FIELD pins on the logic header, separated by depopulated positions.
- **D3** cuts link time with a shorter write (320.96 µs instead of 410.56 µs at 5 MHz). The cost is two valid frame lengths in the SPI state machine, a second CRC position and more validation cases. The saving is not needed to fit a 1 ms cycle on wire time. The design text available to this review was incomplete beyond its summary, so its hardware detail was not scored beyond what the summary states.

**Selected: D1**, with grafts from D2 and D3 (table below). D1 is chosen because:
- it gives eight-motor units the lowest recorded priced-parts cost. That holds for eight-motor units only: a twelve-motor D1 unit has the same $30.54 of priced parts at qty 100 as option A, plus the unpriced module overhead (section 7.4). The base's expansion-readiness parts are also unpriced;
- it adds no link time for channels 9–12;
- it supports the reference drive's STEP/DIR timing (not its enable polarity).

The later user decision resolves U13: use replaceable electronics behind a fixed wiring base, with the FPGA, clock, flash and supervisory circuits on the motion card. The plain D1 layout remains a historical cost/resource comparison, not an open product alternative.

| Grafted idea | From | Where it fits in D1 |
|---|---|---|
| Hardware-gated Ioff buffer between the FPGA and every base-to-module output (STEP8–11, DIR8–11, EN8–11 and TX_PERMIT_B). Its OE comes from hardware permission AND presence AND EXP_PGOOD AND no tamper, not from the FPGA | D2 | Section 7.3. It also solves D1's open question of whether FPGA pins can sink enable-LED current for bank B. |
| `required_mask` in CONFIGURE, with ARM mask == required mask enforced in the FPGA, and a mandatory CONFIGURE before any ARM | D2 | Section 5. A machine configured for twelve motors can never arm eight, including after a rejected CONFIGURE, which clears `config_valid` (section 5.3). |
| `config_hash` echo and `expected_module_class` checked by the FPGA against the latched straps | D2 | Section 5 |
| The installed set is decided only by the FPGA from hardware it reads; the host cannot write it | D3 (also D1) | Sections 5 and 8 |
| Asymmetric frame lengths as a later, measured v3.1 option, not in v3.0 | D3, D2 | Section 5.7 |
| Guided "add motors" and "reconfigure to 8" preview/diff flows; the module holds only its own identity | D2 | Section 10 |

Not grafted: D2's module-local buck (D1's base-supplied transmitter branch is cheaper; see open decision U6), D2's FIELD pins on the logic header (D1's separate J_EXPF keeps domains apart), and D2's per-channel enable readback (it costs 12 FPGA pins; open decision U5).

## 4. Selected architecture

```text
 host (LinuxCNC + cnc1 v3 driver) --- one SPI CS, <= 6.25 MHz, 128 B full duplex ---+
                                                                                    |
 T20F256 endpoint: 12 STEP/DIR generators, 12 EN, 12 ALM, 4 ABZ, 1 session,          |
                   1 watchdog, 1 progress_wdi, one atomic commit, one snapshot  <----+
     |                                    |
     | M0-M7 (direct FPGA pins)           | M8-M11 + TX_PERMIT_B (FPGA/permission -> Ioff buffer -> J_EXP)
     v                                    v
 BASE: 4 AM26C31, 8 enable switches,   MX4 MODULE (passive, no firmware):
       4 ISO1212 (alarms), 8 plugs,        2 AM26C31, 4 enable switches, 2 ISO1212,
       tamper latch, EXP_5V switch         4 plugs, ID straps, WP identity EEPROM,
                                           EXP_5V supervisor (drives EXP_PGOOD)
 machine_permission (external watchdog + edge-armed latch; part open, section 8.1)
   -> TX_PERMIT: 4 base AM26C31 G inputs, the bank-A enable-LED supply switch and the
      Ioff buffer (OE gate and the TX_PERMIT_B channel); TX_PERMIT_B then gates the
      2 module AM26C31 and the bank-B enable-LED supply switch. All of it is
      independent of the FPGA clock.
```

- **One bitstream on every unit** with NUM_STEP=12 and NUM_ENC=4. Installing the module changes no bitstream, ABI, link time or driver build. Only the installed mask and identity change.
- **Bank A (M0–M7) on every base.** Bank B (M8–M11) is the MX4 module, fitted with the power off.
- **The FPGA owns the installed set.** It latches presence, power-good, the tamper state and the class straps once, after a 20.97 ms qualification window. Any later change latches EXPANSION_CHANGED. Recovery needs a **power cycle**, and a hardware tamper latch on the base enforces that: an FPGA reset alone requalifies to "inhibited", not to "installed" (sections 7.3 and 8).
- **All or nothing.** ARM must equal the configured required mask. Any fault on any channel disarms all twelve.

## 5. CNC1 ABI v3 draft (byte-exact)

Status: **draft specification only.** No encoder, decoder, RTL or test exists. v1 ([PROTOCOL.md](../gateware/PROTOCOL.md)) and v2 ([PROTOCOL_V2.md](../cnc1/PROTOCOL_V2.md)) stay as they are and remain historical six-channel builds.

### 5.1 Rules carried over from v1/v2

Except where stated, these carry over: SPI mode 0, MSB first, active-low CS, SCLK at most core/8 = 6.25 MHz, CS guards of at least 8 core ticks, snapshot at synchronized CS assertion, commit only after CS release with exact length, CRC and semantic validation, big-endian fields, signed 32-bit DDS rates, session/sequence rules (next = last + 1, nonzero, no wrap), reject-means-link-fault-and-disarm, the 5 ms FPGA watchdog restarted by an accepted ARM or UPDATE (v1: "since the last accepted ARM/UPDATE", [PROTOCOL.md](../gateware/PROTOCOL.md) line 99), `progress_wdi` toggling only on an accepted UPDATE (so the external watchdog sees a falling edge only every second UPDATE; section 8.1), the external inhibit behaviour, and the v2 rule that a pending capability page is served and consumed by the next completed transaction.

Changes:

- **Frame:** exactly 128 bytes in both directions, i.e. 1,024 rising SCLK edges per CS assertion. 1,023 or 1,025 edges are rejected; overlength is detected at edge 1,025. `cnc_spi_frame.v` must widen `bit_count` from `[9:0]` to `[10:0]`. With the unchanged 10-bit counter every 1,024-bit frame is rejected (fails closed) and overlength detection is lost to wraparound. HDL simulation of a scratch copy shows a correct 1,024-bit frame accepted and 1,023/1,025 rejected with the 11-bit counter (`SCRATCH/link-timing/length-probe.log`).
- **CRC:** CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF, no reflection, no final XOR) over bytes 0–125, stored MSB first in bytes 126–127. Known answer `123456789` → 0x29B1. Detection strength over 1,008 data bits relies on published Hamming-distance tables (HD 4 up to 32,751 bits); this has not been re-derived here.
- **No fallback.** ABI byte = 0x03 in every frame. A v3 driver never talks to a v1/v2 endpoint and vice versa; any mismatch fails closed as `CNC1_BAD_CAPS`.

### 5.2 Command frame, 128 bytes

| Bytes | Field | Validation |
|---|---|---|
| 0–3 | Magic `CNC3` = `43 4E 43 33` | Exact |
| 4 | ABI = `03` | Exact |
| 5 | Opcode | 00–06 only |
| 6–7 | Channel mask, u16. Bit *i* = channel M*i*, i = 0..11 | Bits 12–15 zero |
| 8–11 | Session, u32 | Per opcode |
| 12–15 | Sequence, u32 | Per opcode |
| 16–63 | Twelve s32 rates; channel *i* at 16 + 4*i* (opcodes 00–04) | Nonzero only in UPDATE and only for masked channels; \|rate\| ≤ MAX_RATE |
| 16–125 | Opcode payload for 05 and 06 (replaces the rate area) | Defined below |
| 64–125 | Zero for opcodes 00–04 | All zero |
| 126–127 | CRC over 0–125 | Exact |

### 5.3 Opcodes

| Code | Name | Accepted when | Effect |
|---|---|---|---|
| 00 | NOP | Always. Bytes 6–125 zero | Reads status. Never feeds the watchdog or changes state. |
| 01 | SYNC | Disarmed; bank-B qualification complete; no power-cycle fault (fault bits 5–6); inhibit released and synchronized; nonzero session different from current; sequence 0; mask and rates zero | New session. Clears fault bits 0–4, 7 and 8 and the per-channel latches at bytes 24–25 and 28–29. Does not clear `config_valid`. |
| 02 | ARM | Same session, next sequence; disarmed; fault-free; `config_valid` = 1; **mask == required_mask**; required_mask ⊆ installed_mask; if mask & 0x0F00 ≠ 0, bank B healthy now and class matched; no asserted alarm on a channel in `alarm_trip_mask`; all rates zero | Arms the masked channels at zero speed, closes their enables, starts the watchdog. |
| 03 | UPDATE | Same session, next sequence; armed; fault-free; mask == armed mask; unmasked rates zero; \|rate\| ≤ MAX_RATE | Atomically replaces all twelve rates, feeds the watchdog, toggles `progress_wdi`. |
| 04 | DISARM | Same session, next sequence; mask and rates zero. Accepted with faults latched | Removes motion permission, zeros rates, opens all enables. Keeps fault latches. |
| 05 | READ_CAPS | Disarmed; bytes 6–15 zero; byte 16 = page (0 in v3.0); bytes 17–125 zero | The next completed transaction returns the page and consumes it (v2 rule). |
| 06 | CONFIGURE | Disarmed; qualification complete; no power-cycle fault; mask zero; if a session exists, same session and next sequence, otherwise session 0 and sequence 0 | Accepted: replaces the whole configuration atomically (section 5.4), sets `config_valid`, increments `config_generation`, stores this frame's CRC, and clears the session so SYNC then ARM are needed. **Rejected: clears `config_valid`, `required_mask`, `alarm_trip_mask` and `alarm_on_no_current`; keeps `config_generation`, the stored CRC and `config_hash` of the last accepted frame for diagnosis.** Never feeds the watchdog. |

Any other opcode, and any violated rule, is rejected: the link fault (bit 0) latches and all channels disarm. A rejected CONFIGURE or an ARM whose mask differs from the required mask also sets bit 7. Because a rejected CONFIGURE clears `config_valid`, no earlier configuration survives it: a machine configured for twelve motors cannot fall back to arming eight after a failed reconfiguration (for example with the module absent). The endpoint does not derive per-channel rate caps. The driver must send \|rate\| ≤ min(MAX_RATE, floor(2³²/(high + low)), drive and machine limit). The period term assumes the v3 stepgen adopts the guarded load-minus-one low counter (section 12). If P3 does not adopt it, the term stays floor(2³²/(high + low + 1)). A DDS overflow while the pulse timer is busy still latches STEP_TIMING and disarms (existing fail-safe). Example (arithmetic): DM542T-class timing of 125/125 ticks allows floor(2³²/250) = 17,179,869, i.e. 199,999.998 steps/s (17,111,423 = 199,203 steps/s without the fix). MAX_RATE 0x01000000 (195,312.5 steps/s) still governs.

### 5.4 CONFIGURE payload (opcode 06, bytes 16–125)

| Bytes | Field | Validation |
|---|---|---|
| 16 | Format = `01` (channel configuration) | Exact |
| 17 | `expected_module_class`: 0 = no module required; otherwise the required class | Accepted only if 0 or a class this gateware accepts (CAP3 byte 54; in v3.0 only class 1, MX4). Every other value, including classes 2–6 that a future gateware might accept, is rejected. Nonzero requires bank B installed and latched MOD_ID == this value |
| 18–19 | `required_mask` u16 | Nonzero; bits 12–15 zero; ⊆ installed_mask; bits 8–11 only if `expected_module_class` ≠ 0 |
| 20–21 | `alarm_trip_mask` u16. Set bit: an asserted alarm on that armed channel latches DRIVE_ALARM and disarms all | ⊆ required_mask |
| 22–23 | `alarm_on_no_current` u16. Set bit: the alarm is asserted when **no** input current flows (the fail-closed choice for drives whose healthy output conducts); clear: asserted when current flows | Bits 12–15 zero |
| 24–119 | Timing table. Channel *i* at 24 + 8*i*: u16 STEP high, u16 STEP low minimum, u16 DIR setup, u16 DIR hold, in core ticks | Every value in [TIMING_MIN = 100, TIMING_MAX = 1023], for all twelve channels |
| 120–123 | `config_hash` u32, opaque; echoed in status | Any |
| 124–125 | Zero | Zero |

After reset `config_valid` = 0, so ARM is impossible until a valid CONFIGURE. TIMING_MIN stays at the existing 100-tick default. Lowering it toward the 2 MHz goal is a separate, evidence-gated change (section 16).

**No enable-polarity field.** The review proposed an `enable_sense` field at bytes 124–125 for drives that are *disabled* by applied enable voltage (DM542T V4, [target](EXPANDED_HARDWARE_TARGET.md) line 54). This revision does not add it. An inverted enable would need the switch closed while disarmed, but the enable-LED supply is gated by TX_PERMIT, which is low whenever the machine is disarmed or faulted. The inverted drive would therefore still be enabled while disarmed, after a fault and at controller power loss. The only way to make inversion work would be an enable-LED supply that permission does not gate, and that would weaken the permission rule for every channel. Instead, a drive that is disabled by applied voltage must be wired with ENA unconnected (always enabled while powered), and its profile must declare an independent drive-power or STO interlock as its stop path (U11). The configuration service refuses such a profile without that declaration. A normally-closed (form-B) enable switch fitted per channel would give fail-safe disabling for these drives. It is a possible later hardware variant, unpriced and not designed (U11).

### 5.5 Status response, 128 bytes

| Bytes | Field |
|---|---|
| 0–3 | Magic `CNS3` = `43 4E 53 33` |
| 4 | ABI `03` |
| 5 | b0 effective motion permission; b1 endpoint ready; b2 bank-B qualification complete; b3 bank B installed; b4 `config_valid`; b5–7 zero |
| 6–7 | Armed mask u16 (0 when disarmed) |
| 8–11 | Session |
| 12–15 | Last accepted sequence |
| 16–19 | Snapshot timestamp, u32 core ticks |
| 20–23 | Fault word u32: b0 LINK; b1 WATCHDOG; b2 INHIBIT/authorization withheld; b3 STEP_TIMING; b4 DRIVE_ALARM; b5 EXPANSION_CHANGED (power-cycle fault); b6 EXPANSION_INVALID (power-cycle fault); b7 CONFIG_REJECTED; b8 MODULE_CLASS_MISMATCH; b9–31 zero. SYNC cannot clear b5–b6. An FPGA reset clears the registers, but requalification sets them again while the base tamper latch is set, and only removing logic power clears that latch (section 7.3) |
| 24–25 | Per-channel STEP_TIMING mask, sticky until SYNC |
| 26–27 | Filtered alarm input levels, 1 = input current flowing (raw wiring view; zero for uninstalled channels) |
| 28–29 | Per-channel alarm-trip latched mask, sticky until SYNC |
| 30–31 | Installed mask: 0x0000 before qualification and whenever EXPANSION_INVALID or EXPANSION_CHANGED is latched; otherwise 0x00FF bank A only, 0x0FFF with bank B |
| 32–79 | Twelve s32 emitted-step counts, channel *i* at 32 + 4*i* |
| 80–95 | Four s32 encoder counts |
| 96–111 | Four s32 index-latched counts |
| 112 | Encoder flags: b0–3 index seen, b4–7 illegal transition seen (sticky until reset, as v1) |
| 113 | Expansion live state (after the input filter, section 8): b0 presence A seated; b1 presence B seated; b2 EXP_PGOOD; b3–5 MOD_ID latched at qualification; b6 class matches `expected_module_class`; b7 base tamper latch set |
| 114–115 | Drive-enable command mask after gating (logical FPGA output, **not** a physical switch readback) |
| 116 | `config_generation` u8 (0 = never configured; wraps 255 → 1) |
| 117 | Zero |
| 118–119 | CRC field of the last accepted CONFIGURE frame, 0 if none |
| 120–123 | `config_hash` echo |
| 124–125 | Reserved zero |
| 126–127 | CRC over 0–125 |

The status describes the state sampled at CS assertion, before that transaction's command commits (v1 rule). The expanded DI/DO, probe, frequency, PWM and analog data **do not fit** in the three remaining reserved bytes (117, 124 and 125). They need a separately versioned I/O page or transaction, not ad hoc use of reserved bytes ([PROTOCOL.md](../gateware/PROTOCOL.md), "Board and driver integration").

### 5.6 Capability page 0 (response after READ_CAPS page 0)

| Bytes | Field |
|---|---|
| 0–3 | `CAP3` = `43 41 50 33` |
| 4 / 5 | ABI `03` / page `00` |
| 6 | Gateware STEP channels = 12 |
| 7 | Installed channels: 0 while qualification is pending and whenever EXPANSION_INVALID or EXPANSION_CHANGED is latched, else 8 or 12 |
| 8 / 9 | ABZ encoders = 4 / frequency channels = 0 |
| 10–11 | Installed mask |
| 12–15 | Feature bitmap: b0 STEP; b1 AB quadrature; b2 index; b3 atomic update; b4 watchdog; b5 per-channel enable; b6 per-channel alarm; b7 expansion bank B; b8 runtime timing CONFIGURE; b9 required-mask ARM rule; b10 alarm hardware trip |
| 16–19 | Core Hz = 50,000,000 |
| 20–23 | MAX_RATE = 0x01000000 |
| 24–31 | Reference timing high/low/setup/hold = 100/100/100/100 (u16 each) |
| 32–33 / 34–35 | TIMING_MIN = 100 / TIMING_MAX = 1023 |
| 36–39 | Watchdog ticks = 250,000 |
| 40–41 / 42 / 43 | Alarm sample period 500 ticks (10 µs) / filter samples 4 / zero |
| 44–45 / 46 / 47 | Frame bytes = 128 / minimum SCLK divider = 8 / bank count = 2 |
| 48–51 | Bank A first/width = 0/8; bank B first/width = 8/4 |
| 52 | Expansion state: b0 presence A now; b1 presence B now; b2 PGOOD now; b3 qualification complete; b4 bank B installed; b5 CHANGED latched; b6 INVALID latched; b7 tamper latch set now |
| 53 | MOD_ID latched, bits 2:0 |
| 54 | Module class accepted by this gateware = 1 (MX4). The only class that can qualify bank B and the only nonzero `expected_module_class` CONFIGURE accepts |
| 55 | Zero |
| 56–59 | Qualification window = 1,048,576 ticks (20.97 ms) |
| 60–63 | Gateware build ID u32 |
| 64–125 | Zero |
| 126–127 | CRC |

The module's EEPROM identity (serial, revision, factory test record) is read by the host, never relayed through the FPGA.

Arithmetic reference vectors (Python `binascii.crc_hqx`, not RTL output): an all-zero-payload NOP (`CNC3`, 03, 00, rest zero) has CRC 0xE064; SYNC with session 1, sequence 0 has CRC 0x7AD5; READ_CAPS page 0 has CRC 0xC23E.

### 5.7 Link budget (arithmetic only)

The current driver makes two transactions per servo cycle: a NOP read (`cnc1.c:141-143`) and an UPDATE write (`cnc1.c:213-215`). Wire time plus minimum CS guards (0.48 µs per transaction), excluding spidev/ioctl overhead, controller setup, LinuxCNC compute and jitter:

| Scenario | 5 MHz | 6.25 MHz |
|---|---:|---:|
| v1/v2 historical, 2 × 64 B | 205.76 µs | 164.80 µs |
| **v3.0, 2 × 128 B (8 or 12 channels)** | **410.56 µs (41.1 % of 1 ms)** | **328.64 µs (32.9 %)** |
| v3.1 option: 128 B read + 72 B write (D3) | 320.96 µs | 256.96 µs |
| Rejected: second endpoint, 128 B each | 821.12 µs | — |

The response is 204.8 µs old at the end of a 128 B read at 5 MHz (163.84 µs at 6.25 MHz). A 2 kHz servo (500 µs period) is **not feasible at 5 MHz**: wire time alone is 82 % of the period (410.56/500). At 6.25 MHz it is 66 % (328.64/500) before any spidev, controller, LinuxCNC or jitter overhead, and it is unproven until the bench measurement in section 15 exists. 24-bit rates were rejected because at the current LSB they cap the rate at 97,656 steps/s, below today's 195,312.5. The v3.1 asymmetric option and a one-transaction-per-cycle option (164.32 µs at 6.25 MHz, one extra period of latency) are adopted only after a measured target-host servo cycle.

## 6. FPGA resources and fit risk

Device: Efinix T20F256 as the reference (19,728 LEs; each logic cell is a 4-input LUT or adder plus a register, [FPGA_SYNTHESIS.md](../reports/FPGA_SYNTHESIS.md) line 22). It is still not a fixed selection.

### 6.1 Measured technology mapping (Yosys 0.52 `synth_efinix`)

All runs: exit 0, four check passes per `synthesis.log`, each reporting "Found and reported 0 problems" (28 of 28 across the seven runs; the line numbers differ per run, for example lines 601, 867, 2629 and 2633 of `c_narrow_12_4` and 487, 753, 2235 and 2239 of `a_orig_6_2`), no latches, fully mapped, `CDC_STRUCTURAL_CHECK_PASSED`, Verilator `-Wall` clean (default and 1364-2005 modes). Scratch RTL is a parameterized copy of `gateware/rtl/*.v` with NUM_STEP, NUM_ENC and FRAME_BITS. Its frame layout is a measurement vehicle, not the v3 layout above.

| Run (`SCRATCH/probe-fpga/results/<run>/results/mapped-stat.json`) | Config | LUT4 | ADD | FF | GBUFCE | Total | LE bracket* |
|---|---|---:|---:|---:|---:|---:|---:|
| `a_orig_6_2` (unmodified RTL; equals `gateware/synthesis/manifest.json`) — **historical six-joint** | 6/2, 512 bit | 4,072 | 2,132 | 3,221 | 1 | 9,426 | 31–48 % |
| `a_param_6_2` | 6/2, 512 bit | 4,069 | 2,132 | 3,221 | 1 | 9,423 | — |
| `b_param_8_4` | 8/4, 704 bit, 32-bit guard counters | 5,512 | 2,886 | 4,409 | 1 | 12,808 | 43–65 % |
| `c_param_12_4` | 12/4, 832 bit, 32-bit guard counters | 7,487 | 4,118 | 5,705 | 1 | 17,311 | 59–88 % |
| `n_narrow_6_2` | 6/2, guard counters narrowed to 7 bit | 3,270 | 1,532 | 2,621 | 1 | 7,424 | — |
| `b_narrow_8_4` | 8/4, narrowed | 4,429 | 2,086 | 3,609 | 1 | 10,125 | 33–51 % |
| `c_narrow_12_4` | 12/4, narrowed | 5,859 | 2,918 | 4,505 | 1 | 13,283 | 44–67 % |

\*Arithmetic bracket = (LUT4 + ADD) … (LUT4 + ADD + FF) over 19,728. It is an estimate, not occupancy. Route-throughs and control-set rules can move it either way.

Supporting evidence for the counter narrowing (32 → clog2(P+1) bits, about −21 to −23 % of primitives):

- HDL simulation: the unchanged `tb_cnc_endpoint` (252 checks, pulse-timing monitors on six channels, MISO minimum 83 ns setup / 63 ns hold) and `tb_cnc_endpoint_v2` (27 checks) pass on the parameterized and narrowed 6/2 builds (`SCRATCH/probe-fpga/build/tests-{orig,param,narrow}.log`).
- Formal (partial): `sat -tempinduct` proves `high_left ≤ PULSE`, `low_left ≤ SPACE`, `setup_left ≤ DIR_SETUP`, `hold_left ≤ DIR_HOLD` on the original stepgen at 100-tick parameters (`SCRATCH/probe-fpga/equiv/inv.log`). A bounded 60-step miter was stopped after more than 10 minutes and is inconclusive, not evidence.
- The proof covers build-time widths only. The v3 runtime timing table uses 10-bit counters and needs its own proof.

Flip-flop attribution in `c_narrow_12_4` (netlist name matching, approximate): `rx_shift` 832 + `tx_shift` 808 + endpoint `frame` 736 = 2,376 of 4,505 FF (53 %); stepgen 1,525; encoders about 308. The encoder figure is 180 under encoder net names plus the 128 `enc_counts` FF that sit under endpoint net names, about 77 per encoder. The frame buffers are the largest lever.

### 6.2 Estimated v3 motion core (not synthesized)

Estimate from D1, re-derived against `c_narrow_12_4` (5,859 LUT4 / 2,918 ADD / 4,505 FF):

| Change | LUT4 | ADD | FF |
|---|---:|---:|---:|
| Frame 832 → 1,024 bits: +192 each in `rx_shift`, `tx_shift` and the endpoint frame register (736 → ~928) | — | — | +576 |
| Remove the endpoint frame register; decode from `rx_shift` after CS release | — | — | −928 |
| 10-bit runtime timing counters | — | +150 | +144 |
| Timing registers 12 × 4 × 10 bits, range checks | +290 | — | +480 |
| Alarm synchronizers, 10 µs sampler, 4-sample filters (alarms, presence, PGOOD, tamper) | — | — | +100 |
| Enable gating, installed/required masks, qualification | +100 | — | +60 |
| **Estimate** | **~6,250** | **~3,070** | **~4,940** |

**About 14.3k primitives, bracket ~47–72 % of 19,728. If the frame register is kept, FF rise by ~928 to ~5,870: about 15.2k primitives, bracket ~47–77 %.** Keeping the register adds flip-flops only, so the lower end of the bracket does not move. All rows are estimates, not synthesis.

### 6.3 Fit risk (judgement)

- The motion core alone is plausible on a T20. The rest of the expanded candidate (24 DI, 16 DO, 2 probe, 2 frequency, 2 PWM, process enables, analog and bus logic) is **unmeasured** and is the real fit risk.
- Twelve channels **without** the counter narrowing are high risk once that I/O logic is added. The narrowing and frame-register removal are treated as mandatory.
- 50 MHz timing closure and routing are unknown for every configuration. The likely critical paths are the ~1,000-bit `tx_shift` parallel load and the frame decode.
- Only Efinity place-and-route and timing on the complete design may produce a fit or utilization statement.
- Fallback, if the complete design does not fit: first a larger pin-compatible Efinix device (not verified to exist in F256); second, separate 8- and 12-channel bitstreams with the same v3 ABI (installing the module then needs a verified gateware update).

## 7. Pins, connectors, electrical, power and cost budgets

Sources: pins-electrical-cost probe (paper budget from `hardware/electrical-design.json` at sha256 prefix `f5abb8b171ee4c8e`, `research/motion-io-cost-sources.json`, TI SLLS103P, TI SLLSEY7G, Efinix T20 DS v6.0). No ERC, DRC or measurement.

### 7.1 FPGA GPIO (arithmetic, not a fit)

| Item | Count |
|---|---:|
| T20F256 advertised GPIO / LVDS-as-GPIO / full-feature | 195 / 52 / 143 (DS v6.0 Table 2 note 3, Table 13) |
| Minus 6 dual-purpose configuration pins | 189 usable / 137 full-feature |
| Base: 92 direct signals + 30 baseline support | 122 floor (~122–135 with estimated expanded support) |
| Bank B: STEP8–11, DIR8–11, EN8–11, ALM8–11 | +16 |
| Expansion status: MOD_PRESENT_A_N, MOD_PRESENT_B_N, EXP_PGOOD, MOD_ID0–2 | +6 |
| Tamper latch status EXP_TAMPER_N (new in revision 2, section 7.3) | +1 |
| **Total** | **145 floor, ~145–158 estimated, of 189** |

The 92 direct signals are 16 STEP/DIR, 8 EN, 8 ALM, 12 encoder, 24 general DI, 16 general DO, 2 probe, 2 frequency, 2 PWM and 2 process enables ([target](EXPANDED_HARDWARE_TARGET.md), resource table). The 30 support pins are the baseline `pin_reservations` (`electrical-design.json` line 1935): host SPI 4, analog SPI 4, output faults 4, motion permission 1, external inhibit 1, watchdog progress 1, motion disarmed 1, fault status 4, endpoint ready 1, reference clock 1, logic reset 1, power status 1, future expansion 6. Revision 1 quoted a 144 floor; the tamper-status pin that closes review item 11 makes it 145. Option A needs 138.

That exceeds the 137 full-feature pins, so at least 8 signals must use LVDS-as-GPIO pins. Those have no pull-down or Schmitt trigger, and Efinix recommends at most 16 outputs per bank. Suitable users: alarm/receiver inputs with external pulls, and bank-B outputs, which sit behind the Ioff buffer with module-side pull defaults. A package CSV and bank audit are required. The optional per-channel enable readback (U5) would add 4–12 inputs.

Concurrent work, source inspection only: Codex's `hardware/fpga_core/pin-allocation.json` (candidate `minimum8_expand12_t20f256`, modified 28 Sep 21:48) assigns STEP0–11, DIR0–11, ALM0–11 and `DRIVE_ENABLE#_FPGA_RESERVED` 0–11 to balls, plus twelve `HOME#_FPGA` inputs that are not in the 92-signal count; 96 user allocations, 87 balls unconnected, status `candidate_not_vendor_fitted`. This record reuses that ball plan for STEP/DIR/ALM/EN and does not overwrite it. The HOME inputs and the new expansion-status pins must be reconciled with it (U10).

### 7.2 Connectors

**Motor plug, all twelve channels, 10 contacts.** Revision 1 kept the [target](EXPANDED_HARDWARE_TARGET.md) "Connector proposal" order, which puts ALARM_COM (FIELD +24 V) at contact 8 next to SIGNAL_0V (LOGIC) at contact 9. Revision 2 reorders the contacts so the LOGIC group and the FIELD group are separated by the shield contact and the floating enable-switch pair:

| Contact | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Signal | STEP+ | STEP− | DIR+ | DIR− | SIGNAL_0V | SHIELD/CHASSIS | EN_SW1 | EN_SW2 | ALARM_IN | ALARM_COM |
| Domain | LOGIC | LOGIC | LOGIC | LOGIC | LOGIC | chassis | isolated switch | isolated switch | FIELD | FIELD |

ALARM_COM is a per-bank, current-limited FIELD +24 V feed for the drive's floating alarm opto (ALARM_COM → drive ALM+, drive ALM− → ALARM_IN, ISO1212 sinking input). This resolves the probe's flag (a), but it puts FIELD power on every motor plug (U3). The enable-switch contacts may carry the drive's own enable supply, often FIELD-level, so they sit on the FIELD side of the shield. The motor plug necessarily carries both domains. "LOGIC and FIELD never share a header" applies only to J_EXP and J_EXPF, not to the motor plug. Creepage and clearance between contacts 5–6–7 and a short from ALARM_COM to any contact still need review before U3 is accepted. The alternative in U3 is a separate two-contact alarm plug per motor (more parts, unpriced). The new order departs from the target document's proposal. That document is not edited here; the change is recorded under U3. One plug per motor, so each motor unplugs as a unit. Proposed pitch 3.5 mm: 280 mm for the base's eight plugs plus 112 mm for the four encoder plugs, 140 mm on the module bracket. At 5.08 mm the base needs 406 + 163 mm (U4). The 10-way plug is unpriced; the recorded 8-way TBP01 is only a cost proxy.

**J_EXP, base-to-module logic header:** 2 × 20, 2.54 mm, shrouded and keyed; the module carries the mating socket on four standoffs. All logic signals are 3.3 V referenced to LOGIC_GND.

| Pins | Signal | Pins | Signal |
|---|---|---|---|
| 1–2 | EXP_5V (base switched transmitter branch) | 22 | TX_PERMIT_B: TX_PERMIT through a spare Ioff-buffer channel with the bank-B OE, pulled down on the module. Never the raw permission net, never the FPGA |
| 3 | MOD_PRESENT_A_N | 23–26 | ALM8–ALM11 (module → base, ISO1212 outputs) |
| 4, 6, 9, 12, 15, 21, 27, 32, 36–39 | LOGIC_GND (12 total) | 28 | EXP_PGOOD (open drain; module supervisor wired-AND the base switch fault flag; pull-up on the module, weak pull-down on the base) |
| 5, 7 / 8, 10 | STEP8, DIR8 / STEP9, DIR9 | 29–31 | MOD_ID0–2 |
| 11, 13 / 14, 16 | STEP10, DIR10 / STEP11, DIR11 | 33–34 | I2C_SDA, I2C_SCL (host-owned, isolatable branch) |
| 17–20 | EN8_N–EN11_N (active low, LED cathode sink) | 35 | IO_3V3 (ISO1212 VCC1, EEPROM, gate logic) |
| | | 40 | MOD_PRESENT_B_N |

Presence pins sit at opposite ends to detect a skewed or half-seated module. STEP/DIR/EN and TX_PERMIT_B reach J_EXP only through the base Ioff buffer (graft from D2). A 74LVC16244-class buffer has 16 channels; bank B uses 13 (4 STEP, 4 DIR, 4 EN, TX_PERMIT_B).

**J_EXPF, field connector:** separate 2-position keyed plug. Pin 1 FIELD_ALM_24V (bank-B current-limited alarm supply), pin 2 FIELD_GND. J_EXP and J_EXPF never mix LOGIC and FIELD. Chassis/shield bonds through the mounting hardware.

### 7.3 Electrical and power

| Quantity | 8 motors (base) | +4 (MX4) | Basis |
|---|---:|---:|---|
| AM26C31 ICs | 4 | 2 | 4 drivers each |
| TX 5 V current, datasheet-typical | 0.56 A | 0.28 A | 31 mA/channel into 100 Ω (VOD 3.1 V typ), ICC 3 mA max per input, 1.7 mA at 2 MHz (SLLS103P §5.5, §5.7) |
| TX 5 V current, ledger convention | 0.80 A | 0.40 A | 50 mA per differential signal (`electrical-design.json` `tx_cables`, line 145) |
| Per-IC dissipation | ~0.31 W, ~34 °C rise | same | Estimate, θJA 107.5 °C/W |
| ISO1212 devices (alarms, pooled with DI) | 4 | 2 | 16 → 18 devices total |
| FIELD alarm current | 19.8 mA | 9.9 mA | 2.47 mA max per input, RSENSE 562 Ω (SLLSEY7G §5.9) |
| Enable switches | 8 | 4 | Floating; LED 3–10 mA each, estimated; MPN unselected |
| SMF36A-class TVS | 8 | 4 | Provision |

Rails. No capacity is raised:

- CORE_5V (6 A, `electrical-design.json` line 65, 5.35 A of loads today) would reach 5.95 A with eight motors and four encoder ports on the reservation convention, and 6.35 A with twelve. **The eight-motor base already has no margin.**
- **CORE_24V is over capacity with eight motors.** Capacity is 2 A at 18 V minimum input (`electrical-design.json` line 61). The probe's output for eight motors and four encoder ports is 2.004 A on the reservation convention. That becomes 2.01 A once the logic-converter input is rounded up to 10 mA as the ledger does (lines 229–232). Twelve motors give 2.135 A, or 2.14 A with the same round-up (`budget.py`: 6.35 A × 5 V / 0.85 / 18 V = 2.075 A, rounded up to 2.08 A, plus 0.06 A). Datasheet-typical transmitter loads give 1.925 A and 2.016 A (arithmetic, `budget.py`). Moving the transmitters to TX_5V does **not** reduce the load on the 24 V entry, because TX_5V is still fed from it.
- Decision: move all transmitters to a dedicated **TX_5V branch sized for both banks (1.2 A reservation)**. The base supplies bank B through EXP_5V, a current-limited load switch (section 7.3.1). The 24 V logic-entry converter and its input budget must then be re-derived and resized with TX_5V as a named branch. No capacity is raised on paper. This is mandatory ledger work. The converter is unselected and unpriced, and resizing it costs money on every unit, including eight-motor units.
- The AM26C31's 31 mA typical load into 100 Ω exceeds its ±20 mA recommended IOH/IOL row, while VOD is specified into 100 Ω. Review against the termination choice.
- Partial power: bank-B outputs and TX_PERMIT_B pass only through the Ioff buffer, whose OE is `TX_PERMIT AND PRESENT_A AND PRESENT_B AND EXP_PGOOD AND NOT TAMPER` in hardware. The FPGA never drives a header pin directly or back-powers an unpowered module. The module has pull-downs on STEP8–11, DIR8–11 and TX_PERMIT_B only. **EN8_N–EN11_N are active low** (bank-B LED cathodes sink through the buffer), so the module has **pull-ups** on them to its switched LED-anode supply. An undriven enable then leaves its LED dark and its switch open. A pull-down would have closed the switch.
- Enables: each bank has an LED-anode supply switch. Bank A's switch is on the base, gated by TX_PERMIT. Bank B's switch is on the module, gated by TX_PERMIT_B with its own module-side pull-down. TX_PERMIT_B leaves the buffer only when OE is true, so it already equals TX_PERMIT AND both presence pins AND EXP_PGOOD AND not tamper; the bank-B supply therefore needs all of these. Bank-A cathodes sink into FPGA pins (drive strength to be checked against T20 settings; add a buffer if insufficient). Bank-B cathodes sink through the Ioff buffer. Switch requirements before selection: ≥ 40 V, ≥ 50 mA, low off-state leakage, polarity, isolation group, turn-on/off time. The T20's unconfigured I/O state must be checked to confirm the enables stay open during configuration. **Each LED-anode supply is a switched copy of IO_3V3, the same rail as the Ioff buffer VCC and the FPGA bank VCCIO (3.3 V, to be confirmed in the bank audit), so a logic-high cathode fully turns the LED off; the module's bank-B supply is switched from J_EXP pin 35 by the TX_PERMIT_B-gated switch. An anode rail above VCCIO requires open-drain cathode drivers and is not allowed with push-pull FPGA or 74LVC outputs.** Reason (arithmetic): with a 5 V anode, a high cathode at about 3.3 V leaves about 1.7 V across the LED and its resistor, above the 1.1–1.4 V forward voltage of typical photo-MOS and opto LEDs, so an unarmed channel could close its enable while TX_PERMIT is high; bank A would also back-drive the FPGA pins above VCCIO. The added IO_3V3 load (up to 12 LEDs at 3–10 mA, estimate, plus the switch drops) goes into the P9 ledger.
- The general-output bank (16 × 0.5 A = 8 A against the 6 A field entry) is the FIELD overload problem, independent of the motor count.

#### 7.3.1 EXP_5V, power-good and the power-cycle tamper latch

- **EXP_PGOOD is a real power-good.** A load switch's open-drain fault flag only reports overcurrent or thermal faults; it does not prove the rail is up. EXP_PGOOD is therefore the wired-AND (open drain) of a voltage supervisor on EXP_5V and the base switch's fault flag. The EXP_5V switch and its fault flag are on the base. **The supervisor is on the module** (revision 3), sensing EXP_5V after J_EXP pins 1–2, so a bad 5 V contact is caught as well as a sagging rail. Its threshold must sit at or above the AM26C31's 4.5 V minimum supply. It must be a type with a separate SENSE input, powered from IO_3V3 (J_EXP pin 35), so that its open-drain output is defined while EXP_5V is absent. The EXP_PGOOD pull-up is on the module (to IO_3V3) and the base has a weak pull-down, so an open contact on pin 28 or pin 35 reads "not good". On an eight-motor base without a module EXP_PGOOD therefore reads low, which changes nothing: qualification installs bank A only when both presence pins read absent. Part and resistor values unselected.
- **Qualification timing.** The qualification sample at the end of the 20.97 ms window (1,048,576 ticks) must fall after the selected switch's maximum turn-on time plus the supervisor's maximum power-good delay, counted from EXP_5V enable. Because EXP_5V is enabled at logic power-on, before the window starts, a part whose sum is at most 20.97 ms always satisfies this. A slower part makes a fitted module qualify as INVALID (fail-safe), and P3 then lengthens the window. The window is a qualification delay, not a safety limit, so lengthening it relaxes nothing.
- **Tamper latch (closes review item 11).** Revision 1 said both "only a reset clears" and "needs a power cycle". This revision requires a power cycle and enforces it in hardware:
  - At logic power-on reset (the rail supervisor's reset, **not** the FPGA reset), a flip-flop captures the two presence inputs. EXP_5V is enabled only if both read seated at that moment.
  - After that, any difference between the captured and the present presence state sets an asynchronous TAMPER latch. So does EXP_PGOOD (the module supervisor wired-AND the base switch's fault flag) being low at any time once EXP_5V has been enabled and a blanking time of at least the switch's maximum turn-on time plus the supervisor's maximum power-good delay has elapsed. On a base where EXP_5V was not enabled at power-on, the EXP_PGOOD term is not armed. The term is level-sensitive, not edge-triggered, so a rail that never came up also sets TAMPER when the blanking ends. The blanking also masks the fault flag that many current-limited switches assert while limiting inrush. The blanking must end, over tolerance, no later than one qualification window (20.97 ms, or the longer window if P3 lengthens it) after EXP_5V enable, which is no later than the earliest possible FPGA qualification sample. Otherwise a PGOOD dip that the FPGA latches as EXPANSION_CHANGED could recover inside the blanking time without setting TAMPER. The latch, flip-flop and blanking timer run from IO_3V3 and are cleared only by that power-on reset.
  - Because TAMPER can only be cleared by a power cycle, it must not trip on noise. On an eight-motor base the presence pins are an open header. The latch therefore sees the presence and fault lines through an RC low-pass and a Schmitt input, sized so that, over component tolerance, every pulse the FPGA filter can accept (30 µs or longer) sets it, while pulses shorter than a lower bound (to be chosen, for example 5–10 µs) cannot; a TAMPER set by a shorter pulse is still seen by the FPGA through EXP_TAMPER_N and latched as EXPANSION_CHANGED. Stiff pull-ups sit on the open header. Values are unselected, and both properties must be shown by glitch injection (bench plan B4). The spread between the two bounds has to absorb the Schmitt threshold spread and the RC tolerance; that ratio is part of the part selection. Revision 2 specified the filter the wrong way round (reject everything under 30 µs); a real filter built that way would trip somewhere above 30 µs, so a 30–45 µs glitch could latch EXPANSION_CHANGED in the FPGA without setting TAMPER, and an FPGA reset would then requalify the module. The Ioff-buffer OE uses the unfiltered presence and EXP_PGOOD lines, because a glitch there only blanks bank-B outputs for its duration and latches nothing.
  - TAMPER turns EXP_5V off and forces the Ioff-buffer OE low. It drives EXP_TAMPER_N to the FPGA (the +1 pin in section 7.1), and it enters the machine-permission block as an extra term of `base_ok`. TX_PERMIT for bank A therefore also falls in hardware, independent of the FPGA clock (whole-machine stop, U8).
  - After an FPGA reset, qualification reads EXP_TAMPER_N and latches EXPANSION_CHANGED again. A module inserted or reseated under power can therefore never be requalified without removing logic power. The same applies to a module removed under power and to an EXP_5V trip or sag after the blanking time: bank A alone stays inhibited until the power cycle.
  - Cost: two to four logic gates and a flip-flop, the RC/Schmitt filters, a blanking timer (RC or counter), pull resistors and one FPGA pin. Unpriced. The permission-block change is a requirement on Codex's `hardware/machine_permission` sheet, which this record does not edit (section 13).

#### 7.3.2 Permission fanout, re-derived

Codex's permission block ([MACHINE_PERMISSION.md](../reports/MACHINE_PERMISSION.md), lines 3 and 93) is sized for its final LVC1G11 gate driving six AM26C31 G inputs, six 10 kΩ pull-downs and the block's own 10 kΩ default: below 2.44 mA at 3.4 V (Codex schematic evidence). Revision 1 said this block "is already sized" for D1. That was not checked, because D1 changes the load. Arithmetic re-derivation for D1 (estimate; the validator has not been re-run):

| Load on TX_PERMIT in D1 | Count | Worst-case current at 3.4 V |
|---|---:|---:|
| Base AM26C31 G inputs (bank A) with their 10 kΩ ±2 % pull-downs | 4 | 4 × 0.347 mA + 4 × 1 µA |
| Block's own 10 kΩ default | 1 | 0.347 mA |
| Bank-A LED-supply switch enable, assumed with a 10 kΩ pull-down | 1 | 0.347 mA + input leakage (part unselected) |
| Ioff-buffer OE gate input and the TX_PERMIT_B buffer-channel input (LVC, ±5 µA max each) | 2 | 10 µA |
| **Total** | | **about 2.1 mA plus the LED-switch input leakage** |

The module's two G inputs, their pull-downs, the module LED-supply switch and the J_EXP cable capacitance are driven by the buffer channel, not by the permission gate. The static load therefore falls from Codex's six-bank case (six 10 kΩ + 1). But three new kinds of load appear: the OE gate, the buffer channel and an LED-supply switch. Their input types, leakage and the gate's edge behaviour need Codex's validator re-run on the chosen parts before this is accepted. If D1 is rejected in favour of full population (U1), Codex's six-bank sizing applies directly, and only the LED-supply switches are new.

### 7.4 Cost (recorded DigiKey ladders; largest qualifying break; identical MPNs pooled, `research/hardware-cost-model.json` line 1031)

| Block | Qty 1 | Qty 100 | Unpriced (unknown, not zero) |
|---|---:|---:|---|
| Base motor block, M0–M7 (4 AM26C31, 4 ISO1212, 8 SMF36A, terminal proxy) | $35.92 | $20.47 | 8 enable switches and LED gates, passives, 10-way plugs, PCB area, assembly |
| Base motor block when a module is built in the same run (AM26C31 reaches a lower break) | $35.92 | $20.36 | As above |
| Base expansion readiness | — | — | J_EXP, J_EXPF, EXP_5V switch, Ioff buffer, tamper latch with its filters and blanking timer, pull-ups, EXP_PGOOD pull-down, series resistors, knockout plate, 0.4 A share of TX_5V, share of the resized 24 V logic-entry converter |
| MX4 module, pooled with a base run | $17.96 | $10.18 | Module PCB, J_EXP socket, J_EXPF plug, 24C02-class EEPROM, EXP_5V supervisor (open-drain EXP_PGOOD, threshold ≥ 4.5 V) and its pull-up, 4 enable switches, LED-supply switch, pull-ups/pull-downs, 4 plugs, bracket, assembly/programming/test |
| MX4 module, built alone | $24.27 | $11.15 | As above |
| System delta of adding MX4 (module + the base's pooled saving) | +$17.96 | +$10.07 | As above |
| **D1 twelve-motor unit, priced parts (base + pooled module)** | **$53.88** | **$30.54** | All of the above |
| Option A twelve-motor block, priced parts | $53.89 | $30.54 | Plus 4 switches, ~62 placements, 40 contacts |
| Rejected (A): extra paid by every unit for 12 on base | +$17.97 | +$10.07 | As the line above |
| Rejected (C): second endpoint priced parts | $42.62 | FPGA unknown; rest $14.48 | Clock, flash, JTAG, supervisor, permission, link, PCB |

At qty 100 the pooled module's own priced parts are $10.18. The $10.07 figure is the system delta: building a module in the same run also drops the base block from $20.47 to $20.36, because the AM26C31 then reaches a lower price break. A twelve-motor D1 unit therefore has the same $30.54 of priced parts at qty 100 as option A ($53.88 against $53.89 at qty 1, a rounding difference). On top of that D1 adds the module PCB, J_EXP, J_EXPF, EEPROM, EXP_5V supervisor, buffer, tamper latch and module assembly, all unpriced. D1's cost advantage is real only for eight-motor units, and even there the readiness parts are unpriced (recorded prices; `budget.py` output re-run for this revision). No base or module total is claimed. Price context only: Mesa 7I96S $149 / $108 (qty 100) and 7I76EU $219 / $158, board only, no host or display (`research/MESA_PRICE_SNAPSHOT.json`). No complete Mesa-priced package has been demonstrated ([compute/display matrix](../research/COMPUTE_DISPLAY_MATRIX.md), line 58).

## 8. Fault, inhibit and permission behaviour

Principle: the endpoint arms exactly the configured required set or nothing, and nothing that touches bank B can leave bank A running alone.

The hardware permission expression stays `RAILS_OK AND CONFIG_VALID AND EXTERNAL_PERMIT AND HW_WATCHDOG_OK AND FPGA_ARM_LATCH` ([ELECTRICAL_DESIGN.md](ELECTRICAL_DESIGN.md), line 100). D1 adds one term: NOT TAMPER (section 7.3.1). An external watchdog watches the single `progress_wdi`; which part and timing is an open decision (section 8.1). The permission fanout for D1 is re-derived in section 7.3.2; Codex's validator has not been re-run for it.

**Input filtering.** The presence, EXP_PGOOD and EXP_TAMPER_N inputs pass a two-flop synchronizer and then the same 10 µs sampler and 4-sample filter as the alarm inputs. A level is accepted only after four equal consecutive samples, which takes 30–40 µs plus two core clocks. A glitch shorter than 30 µs is always rejected; one longer than 40 µs is always accepted (arithmetic). Without this, a single-clock glitch on the open presence header of an eight-motor base would latch a power-cycle fault. The hardware paths do not wait for the FPGA or its clock. The Ioff-buffer OE acts on the unfiltered presence lines at once. The tamper latch, and through it EXP_5V switch-off and the permission term, acts after its RC/Schmitt filter delay (section 7.3.1).

| Situation | Without MX4 (installed 0x00FF) | With MX4 (installed 0x0FFF) |
|---|---|---|
| Boot | After 20.97 ms: both presence pins high, tamper clear → bank A only. SYNC and CONFIGURE rejected until then. | Both presence low, EXP_PGOOD high, tamper clear and latched MOD_ID an accepted class (1) → 0x0FFF. Presence A ≠ B; present without PGOOD; present with MOD_ID 0b111, 0b000 or any class the gateware does not accept; or tamper set → EXPANSION_INVALID (power-cycle fault): installed mask 0x0000, CAP3 byte 7 = 0, `endpoint_ready` low, whole machine inhibited. |
| Profile needs 12, module absent or wrong class | CONFIGURE with bits 8–11 or a nonzero class is rejected (b0 + b7/b8), and the rejection clears `config_valid`, `required_mask` and the alarm masks. No channel can arm. The driver refuses before SYNC (`CNC1_BAD_CAPS`). | A module of an unaccepted class never qualifies (INVALID above). b8 remains for a future gateware that accepts more than one class. The host also checks the EEPROM class, revision and CRC against the straps. |
| Profile needs 8, module fitted | — | Normal. M8–M11 idle, STEP/DIR pads held low, enables held open by their pull-ups. |
| Module removed, inserted, half-unseated, EXP_5V trips or EXP_PGOOD falls while powered | Insertion under power: the tamper latch sets (after its RC filter), EXP_5V stays off and TX_PERMIT falls for bank A. The FPGA latches EXPANSION_CHANGED after its filter and disarms; installed mask 0x0000. The EXP_PGOOD term is not armed on this base, because EXP_5V was not enabled at power-on. | The hardware acts independently of the FPGA clock: the Ioff OE drops at once; after the RC filter the tamper latch sets (for EXP_PGOOD, the blanking time has always elapsed by the time qualification completes), EXP_5V goes off and TX_PERMIT falls for both banks. The FPGA latches EXPANSION_CHANGED 30–40 µs after the change and disarms all 12 channels, **even for an 8-motor profile** (U8). Installed mask becomes 0x0000. |
| Recovery from any expansion fault | Remove logic power, then requalify, CONFIGURE, SYNC and ARM. An FPGA or host reset alone requalifies as INVALID/CHANGED because the tamper latch is still set. | Same. |
| Drive alarm on an armed channel in the trip mask | DRIVE_ALARM + per-channel bit; all disarm; LinuxCNC sees `amp-fault-in`. SYNC clears the latch; ARM is refused while the alarm is still asserted. | Same. |
| Alarm on an unarmed or untripped channel | Reported in bytes 26–27, not latched. | Same. |
| Alarm wiring absent with `alarm_on_no_current` set | Alarm reads asserted → ARM refused (fail-closed). Disabling the trip for a drive without an alarm output is an explicit, displayed profile choice. | Same. |
| Link fault, FPGA watchdog (5 ms, 250,000 ticks, restarted by accepted ARM or UPDATE), step timing | Unchanged from v1: latch, disarm all. | Same. |
| External inhibit / E-stop input | Unchanged: combinational gating of STEP, DIR and enables; SYNC and ARM needed afterwards. | Same, also gating the bank-B buffer. |
| FPGA unconfigured or clock stalled | Unconfigured: CDONE low and default-open permission. Clock stalled: only the external watchdog detects it, after its timeout (the open decision in section 8.1). Then permission falls, enables open and the AM26C31 outputs go high impedance. | Same; Ioff buffer OE low. |

An enable output EN*i* closes only when: armed, mask bit *i*, installed bit *i*, bank B healthy (for *i* ≥ 8), no fault, synchronized inhibit released, and in hardware TX_PERMIT (TX_PERMIT_B for bank B).

Caveats:
- DISARM and faults can truncate a STEP pulse; position must be reconciled or rehomed.
- An enable switch that opens on power loss does **not** disable drives that are enabled when their input is open. The DM542T V4 is such a drive: applied enable voltage *disables* it ([target](EXPANDED_HARDWARE_TARGET.md) line 54), so closing the switch on ARM would disable it while armed. v3 has no enable-polarity field (section 5.4). Such drives are wired with ENA unconnected, and their profile must declare an independent drive-power or STO interlock; the configuration service refuses the profile without that declaration and requires it to be confirmed during commissioning (H4), but cannot verify it electrically (U11).
- None of this is a certified safety function.

### 8.1 External watchdog: historical comparison; 20 ms retained

The FPGA's own 5 ms watchdog handles communication loss while the FPGA clock runs. Only the external watchdog on `progress_wdi` catches a stalled FPGA clock. Two parts are on record, with different timeouts:

| | TPS3851G18SDRBT candidate ([audit E-30](../reports/audit-2026-09-28/ELECTRICAL_HANDOFF.md), corrected) | TPS3431SDRBR as drawn by Codex (`hardware/machine_permission`) |
|---|---|---|
| Timing capacitor | 4.7 nF C0G ±5 % (Samsung CL10C472JB8NNNC, 0603, 50 V; product page checked) | 120 pF C0G ±5 % (GRM1885C1H121JA01D) |
| Timeout min / nominal / max | **13.40 / 15.56 / 17.87 ms** (datasheet desk review: tWD = 3.23 × C[nF] + 0.381 ms, TI factors 0.905×/1.095×, ±5 % capacitor) | **about 57.7–71.0 ms fresh; about 71.9 ms maximum with 10 pF parasitic allowance** (Codex schematic evidence, `validation.json`; tWD = 77.4 × C[nF] + 55 ms) |
| Against the 20 ms study limit (`external_watchdog_study_ms`) | Meets it, leaving **2.13 ms** (20 − 17.87) for everything after WDO: pull-up RC, latch, gates, isolator, output stage and the drive's enable response. That downstream latency is unmeasured | Does not meet it; about 3.6× the limit at the maximum. Codex treats it as clock-stall backup only and replaced the 20 ms study value without a recorded user decision |
| Margin over legal WDI spacing | 13.40 ms minimum against falling edges up to about 10 ms apart: 34 % | Large |
| Other differences | Supervisor plus watchdog, different pinout and footprint. WDO is a 170–230 ms pulse, not a latch. WDO is high-impedance (reads OK) during the 170–230 ms power-up reset, so HW_WATCHDOG_OK must be qualified by the part's RESET. G18 threshold supplied from IO_3V3, used only as a supply-present check (G33/G50 thresholds overlap their rail minima). SET1 high to enable | Drawn, ERC-clean and validated by Codex (27 unit tests); EN/SET1 tied high; WDO wired-AND with ENOUT |
| Behaviour while disarmed | With SET1 tied high it cycles (WDO low 170–230 ms, then high 13.40–17.87 ms), holding inhibit through `watchdog_good` → `raw_inhibit_n` for most of the time (datasheet desk review: WDI is ignored while WDO is low). SYNC, ARM and the first falling WDI edge must complete within 13.40 ms of WDO release; because `progress_wdi` is 0 after reset and keeps its level across DISARM, the first falling edge can need two UPDATEs after ARM. Arithmetic: release detection plus SYNC, ARM and two UPDATEs is about 4–5 ms at a 1 kHz servo, but about 10–12.5 ms at the driver's 2.5 ms servo bound, leaving about 0.9–3.4 ms. A miss drops WDO again, inhibits and disarms (fail-safe), and the host retries after the next release. Alternatively drive SET1 from the arm request with a pull-down (watchdog off while disarmed; 150 µs SET1 setup, during which WDI is ignored, added to the arm timeline). That is a change to Codex's permission sheet, and a stuck-low SET1 then also disables the watchdog, which is tolerable only because the same request gates TX_PERMIT | Same structure, with a 57.7 ms minimum window ([MACHINE_PERMISSION.md](../reports/MACHINE_PERMISSION.md) line 70: WDO asserts for 170–230 ms while disarmed, then opens another interval), so arming has far more room |

**Why the minimum must exceed about 10 ms.** Both parts restart only on a *falling* WDI edge. `progress_wdi` inverts once per accepted UPDATE, so a falling edge arrives only every second UPDATE. The FPGA accepts ARM/UPDATE gaps up to just under 5 ms, so legal traffic can space falling edges almost 10 ms apart (2 × 5 ms). For this reason the earlier E-30 candidate of **3.3 nF (9.51 / 11.04 / 12.67 ms) is withdrawn**: its 9.51 ms minimum could trip on traffic the FPGA accepts.

**If the downstream latency measures above about 2 ms** (bench plan, section 15): use 3.9 nF C0G ±5 % instead (11.18 / 12.98 / 14.90 ms, 5.10 ms budget; the MPN is not verified). Alternatively, the v3 RTL could make `progress_wdi` a short pulse on each accepted UPDATE (one falling edge per UPDATE, pulse at least 50 ns). That lowers the required minimum to about 5 ms and makes a shorter timeout possible. The v3 endpoint is new RTL, so this costs little there, but it changes the progress contract Codex's block was validated against and needs new tests. It is part of U15.

The later user decision retains **20 ms fault-to-inhibit** and rejects relaxing it to about 72 ms. U15 is therefore resolved as a requirement; exact circuit/progress implementation and tolerance/downstream timing closure remain engineering work against the shared interface contract. The drawn TPS3431 does not meet this requirement. The historical TPS3851 arithmetic above is a candidate study, not proof that a replacement circuit or the complete permission path has met the bound.

## 9. Changes to `cnc1` core, transport and HAL (planned, not implemented)

Hard-coded six-channel, two-encoder, 64-byte or 8-bit-mask values, by source inspection (files dated 28 Sep 16:24 and 15:56; recheck before P6):

| File | Lines |
|---|---|
| `cnc1/src/cnc1.c` | 21–25, 31–34, 44–50 (codec: 64-byte frames, 8-bit mask, 6 rates, 2 encoders); 72, 74, 83–84, 87, 105, 107 (scales and validation); 158–189 (count checks and feedback); 257–258 (UPDATE rates); 166 (`elapsed>500000`, a 10 ms stale limit expressed in 50 MHz ticks, to be derived from the discovered core Hz) |
| `cnc1/src/cnc1.h` | 9–10 (`CNC1_AXES`/`CNC1_ENCODERS`, unused today); 22, 24, 41–42, 45–46, 59–61, 64–67, 95, 114 |
| `cnc1/src/hal_cnc1.c` | 23–27, 57–58, 70, 81, 96, 134, 142 |
| `cnc1/src/sim_transport.cpp` | 13–14, 53–81 |

- `cnc1/src/cnc1.h`: add `CNC1_MAX_CHANNELS 12`, `CNC1_MAX_ENCODERS 4`, `CNC1_V3_FRAME 128`. Masks become `uint16_t`. Arrays are sized by the maxima; the live count comes from capability page 0. Every line in the table must change.
- New codec `cnc1v3.c` for CNC3/CNS3/CAP3 and CONFIGURE, validating reserved fields, bits 12–15, the installed mask, the power-cycle expansion bits, the tamper bit and the CONFIGURE echo (generation, CRC, hash).
- Transport boundary becomes `exchange(ctx, tx, rx, len)` with len 128 for ABI 3 (`cnc1.h:32`; `spidev_transport.c:123-149`).
- Discovery: READ_CAPS page 0 → CONFIGURE (required mask, trip mask, polarity, timing table, hash, expected class) → SYNC → ARM → a profile `enable_settle_ms` of zero-rate UPDATEs before any nonzero rate.
- Per-channel rate clamp: min(MAX_RATE, floor(2³²/(high + low)), profile/drive limit), or floor(2³²/(high + low + 1)) if the v3 stepgen keeps the extra low tick (section 12).
- `hal_cnc1.c`: parameters `expected_channels=8|12` and `expected_expansion_class=0|1`; a mismatch with the capability page raises `CNC1_BAD_CAPS` and SYNC is never sent. Line 55 (`/50000000`) is the simulation-seconds conversion for the `sim-seconds` pin, not a driver rate constant. It may use the discovered core Hz, but it has no effect on hardware timing.
- HAL pins per channel N = 0..11: `cnc1.N.position-cmd`, `.position-fb`, `.scale`, `.alarm-in`, `.alarm-latched`, `.enable-cmd`, `.timing-fault`; per encoder `cnc1.enc.K.*`; global `cnc1.enable` (in, the existing single arm request), `cnc1.fault` (out, the existing aggregate fault), `cnc1.installed-channels`, `cnc1.expansion-installed`, `cnc1.expansion-fault`, `cnc1.config-generation`.
- `sim_transport.cpp`: 128-byte arrays, `bit < 1024`, CRC at 126–127, fault-injection offsets moved to v3 fields; the Verilated top exposes simulation-only `mod_present_n[1:0]`, `exp_pgood`, `exp_tamper_n`, `mod_id[2:0]`, `alarm_in[11:0]` and `en_n[11:0]`. One simulated exchange = 8 + 1024 × 8 + 18 ticks.
- Python: `runtime.py` (310, 341, 421), `persistent_runtime.py` (281, 283), `model.py` (120), `integration.py` (27, 45, 120), `persistent_integration.py` (71) take counts from capabilities instead of 6/3.

## 10. LinuxCNC, configuration service and guided wiring

**LinuxCNC 2.9.4 limits** (installed header in the isolated rootfs, `linuxcnc-uspace 1:2.9.4-2+deb13u1`): `EMCMOT_MAX_JOINTS` 16, `EMCMOT_MAX_AXIS` 9 (`emcmotcfg.h:25,31`). Module-load test (`SCRATCH/link-timing/halrun-probe.log`): `trivkins coordinates=XYYZABCUVWZZ kinstype=BOTH` with `motmod num_joints=12` loads, 16 joints load, 17 are rejected ("num_joints is 17, must be between 1 and 16", `motion.c` line 326). This is a module-load test only. Twelve motors with nine axis letters need duplicate letters (gantry, multi-Z). Duplicate letters do not *need* `kinstype=BOTH`. The review reports that `trivkins.c` line 103 sets `allow_duplicates = 1` regardless of kinstype. That source file is not in the local `research/vendor-src` tree, so this revision has not re-checked it. The local kins(9) man page (`research/vendor-src/linuxcnc/docs/src/man/man9/kins.9.adoc`, lines 115–128) describes BOTH as the choice that allows unambiguous jogging of each individual joint in joint mode. It recommends BOTH, and cautions that moving one joint of a duplicated set can rack a gantry. The module-load test above used BOTH; the default kinstype with duplicates has not been load-tested here. Gantry homing uses a negative `HOME_SEQUENCE`.

New explicit simulation profiles (disconnected interface, Verilated RTL): `sim-8motor` (XYYZABCU, Y gantry) and `sim-12motor` (XYYZABCUVWZZ). Both use `kinstype=BOTH` as the man page recommends, and the guided setup shows the racking caution for joint-mode jogging of gantry pairs. The existing 3-joint XYZ profile stays as v1/v2 evidence. Nets:
- `joint.J.motor-pos-cmd` → `cnc1.C.position-cmd` per the profile's channel map, and `cnc1.C.position-fb` → `joint.J.motor-pos-fb`.
- **Enable:** a HAL signal may have only one writer, so the joints' `amp-enable-out` pins cannot all be netted to `cnc1.enable`. Follow `cnc1/profiles/sim/simulation.hal` line 16 (`net drive-enable joint.0.amp-enable-out => cnc1.enable`), or drive `cnc1.enable` from `motion.motion-enabled`, or from an AND of all `joint.J.amp-enable-out` through a `logic`/`and2` component.
- **Faults:** one `or2` per joint (`loadrt or2 count=12` for the twelve-joint profile) computes `cnc1.C.alarm-latched OR cnc1.fault` → `joint.J.amp-fault-in`.

Any two channels can form a gantry pair, including one base and one module channel, because all twelve share one commit and one snapshot.

**Configuration service, CLI and UI** (one service contract; structured output, validation, preview/diff, reversible apply):

- Schema: `motion.channels[0..11]` = {bank, joint mapping, drive profile, scale, timing ticks, alarm trip and polarity, enable wiring, `enable_settle_ms`, commissioned}; `hardware.expansion` = {expected: none | MX4 class 1, detected straps, EEPROM serial/revision/test hash, state}.
- Validation: a joint on M8–M11 needs bank B expected, detected, identity-matched and commissioned; timing and rate are the minimum of board, gateware, drive and machine limits and are never raised; `required_mask` is derived from the joint map.
- Status text examples: "Motion: 8 of 12 channels installed. Bank B: not installed [How to add 4 motors]"; "Expansion changed while powered — switch the controller off and on again"; "Module half-seated (presence mismatch)"; "M9 drive alarm"; "M3 alarm wiring not detected (fail-closed)"; "M2 drive profile disables on applied enable voltage — wire ENA open and confirm the drive-power interlock".
- Guided "add motors 9–12": preview (installed 8 → 12, no assignment changed) → save and power off → fit module and J_EXPF → power up disarmed → detected identity and verdict → assign joints with preview/diff → generated per-plug wiring guide (drive model, STEP/DIR differential or opto warning, enable contact and the open-input-enables warning, ALARM_COM wiring and polarity) → continuity/voltage checks → scoped per-channel checks for M8–M11 only (alarm, enable, low-rate direction jog) → arm.
- Removal: profiles using M8–M11 become "unavailable — inhibited"; the user refits the module or applies a previewed, reversible remap to eight motors. Nothing is deleted. A same-class replacement keeps assignments and re-verifies only M8–M11. The module holds only its identity and factory record ([modular repair §2](MODULAR_REPAIR_AND_MEMORY.md#2-separate-settings-calibration-and-executable-software)).
- Illustrative CLI verbs (not implemented): `controller hw expansion status --json`, `controller config motion channel set 9 --drive dm542t-v4 --preview`, `controller commission channel 9`.

## 11. Module (MX4) contents and identity

Two AM26C31 (series/default network as the `tx_twelve` banks 5–6), G inputs from TX_PERMIT_B with module-side pull-downs; pull-downs on STEP8–11 and DIR8–11; **pull-ups on EN8_N–EN11_N to the switched LED-anode supply**; 4 enable switches plus one TX_PERMIT_B-gated LED-supply switch whose enable also has a pull-down; that switch takes its input from IO_3V3 on J_EXP pin 35, so the bank-B LED-anode supply is a switched copy of IO_3V3, the same rail as the base Ioff buffer VCC and the FPGA bank VCCIO, and a logic-high cathode fully turns the LED off (an anode rail above VCCIO would need open-drain cathode drivers and is not allowed with the push-pull 74LVC outputs); an EXP_5V supervisor (open-drain EXP_PGOOD, threshold ≥ 4.5 V, separate SENSE input on EXP_5V after pins 1–2, powered from IO_3V3) with the EXP_PGOOD pull-up; 2 ISO1212 with 4 SMF36A; 4 ten-way motor plugs (revision 2 contact order) on a rear bracket; a 24C02-class identity EEPROM with WP held protected on the module and written only through a factory fixture pad; MOD_ID straps (class 1 = 0b001; 0b111 reads as absent and 0b000 is reserved, and both, like any class the gateware does not accept, make a seated module INVALID); both presence pins tied to LOGIC_GND. No MCU, firmware or regulator. EEPROM record: magic, format version, class (must equal straps), hardware revision, serial, channel count 4, first channel 8, electrical ratings, factory test hash, CRC32. The host reads it through a bounded-timeout, isolatable I2C branch.

## 12. Pulse-rate statement

Mechanism, by source inspection of `gateware/rtl/cnc_stepgen.v`:
- Each channel's 32-bit DDS accumulator adds its rate every 20 ns core tick, and each overflow requests one STEP.
- A STEP may start only when the high and low counters have both expired. An overflow that arrives while they are busy latches STEP_TIMING and disarms.
- A channel's limit is therefore the lower of the MAX_RATE cap and the rate implied by the minimum STEP period.

The generators are independent copies that update from one accepted frame. Independent generators do not mean independent link bandwidth: all rates travel in one frame, and all counts return in one status.

| Build | Statement | Evidence class |
|---|---|---|
| Historical 6/2, as built | **The limit is 195,312.5 pulses/second per channel, with 6 channels operating simultaneously, and it comes from the default MAX_RATE increment 0x01000000, which lets each 32-bit DDS overflow at most once every 256 ticks of the 50 MHz core (50,000,000 / 256).** | Source inspection and arithmetic, plus HDL simulation: a scratch run of `cnc_stepgen` at this rate gave a 256-tick period (100 high, 156 low) and no fault. [PROTOCOL.md](../gateware/PROTOCOL.md) line 91 states the same figure. Not measured on hardware |
| Historical 6/2, timing ceiling (reachable only if MAX_RATE were raised, which is not planned) | **The limit is 248,756 pulses/second per channel, with 6 channels operating simultaneously, and it comes from the 201-tick minimum STEP period of the unmodified `cnc_stepgen.v` at 100/100 ticks.** STEP is high for 100 ticks and low for 101. The extra low tick exists because the next rise tests the registered `low_left == 0`, which becomes true one tick after the counter reaches zero. Largest fault-free increment 0x01460CBC = 21,367,996 (248,756.21 steps/s); 0x0147AE14 latches STEP_TIMING | **HDL simulation only**: a scratch iverilog 13.0 run over 999 pulses (min = max = 201 ticks) and the project testbench bound. PROTOCOL.md line 93 documents the period as PULSE + SPACE + 1. The extra tick is conservative (low ≥ 100), not a safety defect |
| Historical 6/2 with the guarded fix (scratch copy only, not in the tree) | **The limit is 250,000 pulses/second per channel, with 6 channels operating simultaneously, and it comes from an exact 200-tick minimum STEP period (100 high + 100 low) once `cnc_stepgen.v` loads `low_left <= (SPACE_CYCLES > 1) ? SPACE_CYCLES - 1 : 0;`.** Largest fault-free increment 0x0147AE14 = floor(2³²/200) = 21,474,836 (249,999.994 steps/s); 0x0147B000 faults | **HDL simulation only**, on scratch copies: 999 pulses at 200 ticks with no fault; DIR setup ≥ 301 and hold ≥ 200 ticks on reversal; the project suites pass 252/252 and 27/27 once the testbench bound is changed to PULSE + SPACE. The guard is required, because a bare `SPACE_CYCLES - 1` wraps to 0xFFFFFFFF (about 86 s of dead time) when SPACE_CYCLES = 0 |
| Planned v3, 8 or 12 channels (not implemented) | **The limit is 195,312.5 pulses/second per channel, with 8 channels (base only) or 12 channels (MX4 fitted) operating simultaneously, and it comes from the unchanged MAX_RATE 0x01000000 (at most one DDS overflow per 256 ticks).** A channel's CONFIGURE timing can only lower it, to 50 MHz / (high + low) with the fix adopted: 250,000 at 100/100 and 200,000 at DM542T-class 125/125 (both above the cap, so MAX_RATE governs), or 125,000 at 200/200, where timing governs | Design arithmetic only. No v3 RTL, simulation or measurement exists |

Consequences recorded here:
- **The v3 draft adopts the guarded load-minus-one form** in its new runtime-timing stepgen (P3), so the host clamp is floor(2³²/(high + low)). CONFIGURE's TIMING_MIN of 100 ticks keeps the zero guard inactive, but the guard stays in the RTL.
- P3 also adds an elaboration or configuration check that STEP high is at least 1 tick. With PULSE_CYCLES = 0 the historical RTL sticks STEP high (scratch simulation: one rising edge while the count reached 62 in 1,000 ticks).
- Applying the fix to the historical 6/2 RTL is a separate choice. It changes the RTL hash and invalidates the current gateware, Verilator and LinuxCNC evidence manifests until they are re-run. It also changes PROTOCOL.md line 93 and its copy in `hardware/machine_permission/input-PROTOCOL.md`, the validation manifest, audit ledger entry R1-003, AUDIT_REPORT, ELECTRICAL_HANDOFF and PROJECT_BRIEFING. This record edits none of them.
- None of the four statements is an electrical, cable or drive limit. Pulse fidelity through the AM26C31 and the cable, and the drive's own input limit, are unmeasured. "Simultaneously" rests on the design and on the 6/2 testbench's timing monitors on all six channels in simulation. Simultaneous operation of 8 or 12 physical outputs has never been measured (section 15).

## 13. Reconciliation with the drawn hardware

What Codex has drawn (Codex schematic evidence, read by source inspection on 28 September; not re-run here; no Codex file is edited by this record):

- **`hardware/tx_twelve`** ([report](../reports/TWELVE_CHANNEL_TRANSMITTER.md)): six AM26C31IPWR (U1–U6) driving 24 differential signals, STEP0–11 and DIR0–11, fully populated. Each channel has a 33 Ω series resistor and a 10 kΩ input pull-down. Each bank has a 10 kΩ permission pull-down on G, 100 nF and 1 µF, with /G held inactive at CORE_5V. The sheet is supplied from CORE_5V. Outputs go to JTX0–JTX5, eight positions each (two channels' STEP/DIR pairs per connector, 48 positions in all), with the RS-422 reference return on a separate six-position JREF1 (LOGIC_GND), not on the JTX connectors; the FPGA-side STEP/DIR inputs, CORE_5V, LOGIC_GND and TX_PERMIT enter on JLOGIC1 (netlist inspection). Audit E-16 records the corresponding JPOWER split for the older six-channel sheet. KiCad ERC shows 0 violations (4 ignored checks), with a 1.2 A reservation. It has no enables and no alarms, and `manufacturing_ready` is false.
- **`hardware/machine_permission`** ([report](../reports/MACHINE_PERMISSION.md)): a TPS3431 watchdog (about 57.7–71.9 ms) and an edge-armed latch, with `TX_PERMIT = arm_latch.Q AND FPGA_MOTION_REQUEST AND raw_inhibit_n`. The final LVC1G11 is sized for six G inputs. Codex reports 27 tests passing and ERC 0/0.
- **`hardware/fpga_core/pin-allocation.json`**: STEP, DIR, ALM and DRIVE_ENABLE_RESERVED 0–11 plus HOME 0–11 assigned to balls. Status: candidate, not vendor-fitted.

`tx_twelve` is D1's rejected **option A**. What changes with the user's choice U1:

| Item | U1 = full population (option A, as drawn) | U1 = MX4 plug-in module (D1) |
|---|---|---|
| Transmitter sheet | Used as drawn: U1–U6 on the base | Split: U1–U4 (STEP0–7, DIR0–7) stay on the base; U5–U6 (STEP8–11, DIR8–11) move to the module. A new pair of sheets is derived in P9, coordinated with Codex. `tx_twelve`'s "missing expansion banks" validator check needs a split variant |
| Transmitter supply | CORE_5V → TX_5V branch (mandatory: 6.35 A on CORE_5V otherwise) | Base U1–U4 on TX_5V; module U5–U6 on EXP_5V (the TX_5V branch through the switched, supervised feed) |
| Transmitter enable (G) | TX_PERMIT to all six, as drawn | U1–U4 on TX_PERMIT; U5–U6 on TX_PERMIT_B (buffered), with their 10 kΩ permission pull-downs moved to the module |
| STEP/DIR inputs 8–11 | Direct from the FPGA, 33 Ω + 10 kΩ as drawn | From the Ioff buffer through J_EXP. The 10 kΩ pull-downs sit on the module; the 33 Ω series resistors sit at the buffer outputs (decided in P9) |
| Output connectors | JTX4–JTX5 on the base edge | Channels 8–11 on the module bracket |
| Connector scheme (independent of U1) | Codex: an 8-position JTX per two channels, STEP/DIR only, with enables and alarms elsewhere. This record: one 10-contact plug per motor (section 7.2). Still open (U3, U4) | Same |
| Enables and alarms | Not on either Codex sheet. 12 switches, 6 ISO1212 for alarms and two bank LED-supply switches on the base | 8 + 4 switches; ISO1212 split base/module; LED-supply switches per bank |
| Permission block | Codex's six-G sizing applies directly; the LED-supply switches are new loads | Re-derived fanout (section 7.3.2), a NOT TAMPER term and the TX_PERMIT_B buffer channel |
| External watchdog | Independent of U1 (U15, section 8.1) | Same |
| FPGA pins | 138 floor (1 on LVDS-as-GPIO) with the build-parameter variant below; the tied-input variant needs 144 (7 on LVDS-as-GPIO) | 145 floor (8 on LVDS-as-GPIO); 7 expansion-status pins to add to Codex's ball plan (P9) |
| Gateware and ABI | Same v3 frame and driver. The installed mask is fixed at 0x0FFF, either by tying the bank-B status inputs on the base to a fixed "bank B on board" code (which CAP3 byte 54 must then accept; the six status inputs stay FPGA pins, so this variant needs 144 pins) or by a build parameter (keeps 138). Decided in P3 | As specified in section 5 |
| Rails (reservation convention; CORE_24V as probe output, ledger 10 mA round-up in brackets) | CORE_5V 6.35 A and CORE_24V 2.135 A (2.14 A) on every unit | 5.95 A / 2.004 A (2.01 A) on eight-motor units; 6.35 A / 2.135 A (2.14 A) with the module. Both need TX_5V and a resized 24 V entry |
| Priced parts, qty 100 | $30.54 on every unit | $20.47 for eight-motor units; $30.54 with the module, plus unpriced module overhead |
| Motor-plug edge at 3.5 mm | 420 mm on the base | 280 mm base + 140 mm module bracket |

Historical unselected option: if full population were used, D1's architecture would reduce to the same endpoint with bank B permanently fitted. J_EXP, J_EXPF, the Ioff buffer, EXP_5V, the tamper latch, the MX4 module and its EEPROM would disappear. The later confirmed U1 choice is the plug-in module; retain this alternative for cost context rather than asking to choose it again.

## 14. Mapping onto a fixed wiring base with replaceable service modules

**U13 is resolved by the later confirmed user decision: fixed wiring base with replaceable service modules and FPGA motion card.** The following plain D1 comparison is retained as historical arithmetic: one base board carrying the FPGA, M0–M7 electronics and I/O with keyed pluggable terminal groups. The current architecture is specified in [modular repair §1](MODULAR_REPAIR_AND_MEMORY.md#1-wiring-remains-with-the-machine); exact connectors, circuits, fit, power and complete costs remain unfinished.

The concept under consideration: a fixed wiring base whose field terminals never move, carrying replaceable modules. The modules are compute; a motion card with FPGA, clock and configuration flash; motor/encoder interface cards; digital I/O banks; an analog/communication card; a power module; an ESP card with a detachable antenna; and a settings cartridge. Replacement is power-off only, with keyed and latched connectors, automatic identification, local firmware restore and no automatic motion resume.

### 14.1 Which side of the connector the FPGA sits on

In the user's concept the FPGA is on the motion card, so every FPGA signal that reaches field electronics crosses the motion-card connector. Counts start from D1's 145-signal budget (the revision-1 144 plus the tamper-status pin); all are arithmetic estimates:

| Layout | FPGA signals | Signals crossing the motion-card connector | Estimated connector positions (with returns and power) |
|---|---:|---:|---:|
| Plain D1 base board (FPGA on the base) | 145 | none (no motion card) | only J_EXP, 40 |
| F1: FPGA on the motion card, all I/O parallel | 145 | ~152 | ~195–210 |
| F2: F1 with the 24 general DI and 16 general DO serialized | ~109 (two I/O-card links) to ~113 (three) | ~116–120 | ~150–170 |

How F1 is counted:
- Signals that stay on the motion card if the permission block lives there (section 14.3): the 50 MHz reference clock, the arm request, `progress_wdi`, endpoint ready, and the inhibit input fed from the local raw interlock. That is 5, leaving 140 FPGA signals that cross.
- Added crossing signals: TX_PERMIT out and EXT_PERMIT_3V3 in (2); a host path to reprogram the configuration flash for local restore (about 6: SPI plus reset and status); the card's own presence and identity (about 4). About 12 in all.
- Positions assume one return per 3–4 signals for 3.3 V edges with a 6.25 MHz SPI, plus 4–8 power contacts. The connector family, ground ratio and signal integrity have not been analysed.

The fixed base also moves **every field conductor** through board-to-board connectors: for a bank-A motor/encoder card, 8 × 10 = 80 motor contacts (section 7.2) plus 4 × 8 encoder contacts, about 112; about 104 (8 × 9 = 72 plus 32) only if each motor plug's shield contact bonds to chassis on the base instead of crossing to the card. Those connectors need FIELD-voltage rating, creepage and clearance, and LOGIC and FIELD kept on separate connectors. TVS placement becomes a choice between the base, protecting at entry but making the base a failure point, and the card, which is replaceable but leaves a short unprotected run.

### 14.2 Serializing the general DI and DO (U14)

The 24 general DI, the 16 general DO and the 4 output-fault lines could reach their I/O cards over one isolated serial link per card instead of 44 parallel FPGA pins. Four lines per card (SCLK, data out, data in, latch) give a net saving of about 36 FPGA pins with two I/O cards (145 − 44 + 8 = 109). That fits inside the 137 full-feature pins with no LVDS-as-GPIO use (arithmetic).

- **Isolation placement.** The serializer can sit on the LOGIC side of the existing ISO1212 and DO-driver isolation; the link is then fault-contained (Ioff buffers, series resistors) but not galvanically isolated. Or it can sit on the FIELD side behind one 4-channel digital isolator per card, which needs a field-side logic supply but replaces per-output DO isolator channels. Both are unpriced.
- **Rate.** At least once per servo period; preferably the FPGA runs each link continuously, for example every 100 µs, and snapshots the result into the host's I/O page each servo cycle. DI age is then at most one link period plus the input filter, and a DO changes within one link period of its commit. 64 bits at 1 MHz is 64 µs (estimate). The host-to-FPGA I/O transport is itself still unspecified: it needs a separately versioned I/O page (section 5.5).
- **Integrity — superseded proposal.** The earlier shift-register-only idea used fixed markers, latched-output readback and a local watchdog. **That is insufficient for the adopted requirement.** A serialized-card implementation must validate card identity, expected sequence/freshness and CRC before outputs change, report input validity/age and apply the defined stale/fault response. The card therefore needs logic or firmware capable of that contract; shift registers alone do not supply it. This record's 64-bit rate example and cost/pin estimates must be recomputed for the complete validated exchange. No finished card implementation or physical timing is claimed.
- **What must stay direct**, and why:
  - **Drive enables and their gating.** The hardware TX_PERMIT gate must act without the FPGA clock and without any link. A serial link would add at least one link period of latency, plus a failure mode in which the last latched state persists.
  - **Drive alarms.** They feed the disarm-all trip within the 10 µs sampler and filter.
  - **Probes.** Capture must latch the step and encoder counts at the edge. A sampled link adds up to one link period of uncertainty, for example 100 µs, which is 1.67 µm at 1 m/min and 16.7 µm at 10 m/min (arithmetic). Card-side timestamps would need synchronized time.
  - **Frequency inputs.** They count individual edges, and a link sampled every 100 µs cannot see edges above 5 kHz.
  - **PWM.** It needs a directly generated waveform, unless the card gains its own PWM logic.
  - **The two process enables.** They are independently inhibited in hardware.
  - **The protective EXT_PERMIT input.** Codex's block requires it as a fixed, hard-wired assignment.
  - **STEP/DIR and encoders.**

### 14.3 Where the permission latch lives

Adopted placement under resolved U13: **on the motion card, beside the FPGA it supervises.** Its inputs (CDONE, local reset, `progress_wdi`, arm request, endpoint ready) are all motion-card signals. A motion-card swap replaces and requalifies the watchdog together with the FPGA. The earlier crossing-count study below remains provisional against IS-1; it is not a completed connector allocation. Consequences:
- TX_PERMIT has a pull-down on the base and at every receiving card, so a missing or unseated motion card means no permission.
- Every interface card gates its own transmitters and LED-supply switch with TX_PERMIT AND its own presence, power-good and tamper state. This is D1's bank-B logic applied to every card, bank A included.
- The power-cycle tamper latches must be cleared only by logic power-on reset, so they belong on the power module, which owns that reset, or on the base. Putting them on the base makes the base active rather than passive.

Historical alternatives, superseded by the adopted motion-card placement: on the power module (it survives a motion-card swap, but about 5 more signals cross and the watchdog is separated from its FPGA), or on the base (the base becomes an active board that can fail).

### 14.4 Identity and firmware per module

| Module | Automatic identification | Programmed content | Local restore | Note |
|---|---|---|---|---|
| Compute | Compute module's own serial/OTP; carrier presence | Boot image on its storage | Supplied recovery image from a local package; never from a cloud account | A blank image has no configuration authority ([modular repair §4](MODULAR_REPAIR_AND_MEMORY.md#4-two-committed-generations-and-one-authority)) |
| Motion card (FPGA, clock, flash) | Two presence pins, WP identity EEPROM (class, revision, serial, factory test) on an isolatable I2C branch; CAP3 gateware build ID | Gateware in the configuration flash, factory-programmed | Host rewrites the flash from a verified local package over the dedicated programming path, disarmed and with permission withheld (CDONE low removes permission in Codex's block). A fallback-image scheme is not verified for the T20 | Replacing it re-verifies all motion channels (timing, enables, alarms, encoders) |
| Motor/encoder interface card (bank A card; MX4 bank B) | Presence pins and MOD_ID straps latched by the FPGA; WP EEPROM read by the host | None (passive) | Nothing to restore | Re-verifies only its own channels |
| Digital I/O bank | Card identity plus validated sequence/freshness and CRC for serialized data, per the later requirement | Exact implementation pending shared contract; old shift-register-only assumption superseded | If it requires firmware, supply a programmed spare and compatible offline recovery | Re-verifies assignments, polarity, integrity/freshness and dependent functions |
| Analog/communication card | EEPROM with identity and **its own** factory calibration (never copied from the failed card) | None if the bus controllers live on the host or FPGA; firmware if it gains an MCU | Only if it has firmware: local package plus version negotiation | Whole measurement chain re-verified |
| Power module | Straps plus EEPROM | None in the first design | Nothing to restore | Owns logic POR and the tamper latches (section 14.3) |
| ESP card | eFuse MAC plus card EEPROM | ESP32-S3 application; ESP-IDF 5.5.4 OTA with two slots and rollback | Host reflashes over the wired UART in ROM download mode. That needs BOOT/EN control, but EN is supervisor-owned (audit E-38), so the download path is a design item | Detachable antenna: WROOM-1U U.FL to a panel bulkhead. FCC 47 CFR 15.203 requires a unique coupling (for example RP-SMA), and 15.204(c)(4) requires the same antenna type at no more than the authorized gain. The authorized gain is not yet read from the filing. Test in the real enclosure |
| Settings cartridge | Cartridge serial plus machine lineage | Configuration records, not firmware | Restore from mirror or export is an explicit recovery transaction | Two committed records ([modular repair §4](MODULAR_REPAIR_AND_MEMORY.md#4-two-committed-generations-and-one-authority)) |

**No automatic motion resume**, whatever module changed:
- The unit powers up disarmed, with `config_valid` = 0 in the FPGA until a CONFIGURE.
- A fresh SYNC and ARM are needed, and the affected checks are invalidated.
- No armed or homed state is stored, and stale commands cannot restart motion.
- The tamper latches make a card seated under power unusable until a power cycle.

### 14.5 Extra cost items each boundary adds (all unpriced; none is in the recorded price files)

| Boundary | Added items |
|---|---|
| Fixed base itself | Backplane/terminal PCB, all field terminal blocks moved onto it, chassis bonding, mechanical carrier and card guides, enclosure changes |
| Every card slot | LOGIC board-to-board connector pair, separate FIELD connector pair where field conductors cross, keying and latches, two presence contacts, identity EEPROM or straps, card PCB, assembly and test per card, spare stock |
| Motion card | ~195–210-position connector (F1) or ~150–170 (F2), flash-programming path from the host, the permission block moved onto it, factory programming fixture |
| Interface cards | Per-card permission gating, a power switch with a real power-good, pull defaults, Ioff buffering at the connector |
| Serialized DI/DO (U14) | Original unpriced marker/shift-register study: isolator or fault-containment buffers, shift registers, field-side regulator and local DO watchdog. Add the required identity/sequence/freshness/CRC validation hardware/firmware and recompute all quoted pin/timing/cost savings; the old ~36-pin saving is provisional |
| Power module | Owns POR and tamper latches; connector and power contacts sized for the full load |
| ESP card | U.FL-to-bulkhead cable, antenna, regulatory compliance per antenna |
| Cartridge | Memory, PCB, keyed housing, WP circuitry (already listed in modular repair §8) |

| | Plain D1 base board | Fixed wiring base with service modules |
|---|---|---|
| Field wiring on repair | Wires stay in keyed plugs; the plugs are moved to the replacement board | Terminals never move |
| Replacement unit | Whole base: FPGA, all motor/I/O electronics and compute carrier | Only the failed card |
| FPGA pins | Direct; 145 | Same, plus ~12 connector-support signals; ~109 with U14 |
| Connectors added | J_EXP and J_EXPF only | Every slot, a ~195–210-position motion-card connector, and FIELD conductors through board-to-board connectors |
| Recorded cost | D1 priced parts as in section 7.4 | Unknown; every added item is unpriced |
| New failure modes | Few | Connector wear, half-seated cards (presence and tamper handle them), more identity to manage |

## 15. Bench measurement plan: first physical eight-motor test

Scope: the first physical test of an eight-motor v3 build. It uses a bench controller, eight drives and eight unloaded motors, with no machine attached, and an independent E-stop that removes drive power. It is planned, not done.

Prerequisites: P1–P7 complete, the H1 link prototype built, and v3 gateware configured for 8 installed channels. The probe test also needs the separately versioned I/O page (not in v3.0).

Instruments: a logic analyser at ≥ 200 MS/s on CS, SCLK, MOSI, MISO, `progress_wdi`, TX_PERMIT, WDO, CDONE, a host GPIO toggled at servo-thread start, and the STEP/DIR inputs; a scope with differential probes at the drive end of the cable; a current probe on TX_5V and the 24 V entry; thermocouples on the AM26C31s; and a programmable supply able to generate dips.

Every figure below is recorded with its instrument, sample rate, run length and conditions, and the raw captures are kept with their hashes. The evidence class is physical measurement. If a result breaches an existing limit (servo period, 5 ms FPGA watchdog, 20 ms external-watchdog study limit, rate or current limits), the finding is recorded and the design changes. The limit does not.

**B1. SPI exchange time per servo cycle** (both the read and the UPDATE exchange). Measure:
- servo-thread start to first CS assert;
- per exchange, CS assert to deassert: actual SCLK (spidev cannot report it), inter-byte and DMA gaps, CS guards;
- CS deassert to ioctl return;
- thread start to the end of the UPDATE exchange, compared with SERVO_PERIOD and with the 410.56 µs (5 MHz) or 328.64 µs (6.25 MHz) wire-plus-guard arithmetic;
- the accepted-UPDATE interval at the FPGA (`progress_wdi` toggles or status-timestamp deltas): distribution, jitter and maximum;
- LinuxCNC servo-thread tmax and the latency histogram;
- margins: 5 ms minus the maximum accepted ARM/UPDATE interval (FPGA watchdog), the driver's servo period ≤ 2.5 ms rule, and the chosen external watchdog's tWD(min) minus the maximum falling-edge interval (twice the maximum UPDATE interval).

Run for at least four hours per load condition.

**B2. Simultaneous eight-channel step generation and encoder counting.**
- All eight channels at once, at a low rate, at the drive profile's maximum and at the 195,312.5 steps/s cap. The cap is tested into passive receivers only, if it exceeds the drive's rated input.
- At the drive end, measure STEP high and low widths against the configured ticks, DIR setup and hold on reversals, VOD and edge rates.
- Count ≥ 10⁶ pulses per channel on the analyser against the status counts.
- Measure edge skew between the two channels of a gantry pair.
- Record TX_5V current and AM26C31 temperature at the cap. No STEP_TIMING fault is expected.
- At the same time, drive all four ABZ ports from a quadrature generator at stepped edge rates. Compare counts, index-latched counts and illegal-transition flags with the generator, with the STEP channels idle and running.

**B3. Probe capture.**
- Trigger each probe input from a pulse generator at a known STEP count, which the analyser records.
- Measure capture latency (edge to latched count) and its jitter over ≥ 1,000 captures at three speeds, and the minimum detected pulse width, with all eight motors stepping.

**B4. Fault drills.** For every row, record three things separately and never merge them:
- (a) **fault-detected time**: t0 to the first recorded detection (FPGA fault bit or its status timestamp, WDO fall, supervisor RESET, host log);
- (b) **electrical-outputs-inhibited time**: t0 to TX_PERMIT low, to the AM26C31 outputs going high-impedance at the terminal, to every enable switch open (measured across its contacts with a test load), and to the last STEP edge;
- (c) **machine-stopped behaviour**: time to the last motor step, whether each drive disables (by its enable wiring), holding or free-wheel, position loss against the encoders, and confirmation that nothing restarts by itself.

| Scenario | Injection | t0 |
|---|---|---|
| Startup | Cold power-on with fast and slow 24 V ramps, host idle and host auto-starting LinuxCNC. Outputs must stay inhibited from t0 until a deliberate ARM. Record any glitch on STEP/DIR/EN/TX_PERMIT during FPGA configuration and during the external watchdog's power-up interval (170–230 ms reset for the TPS3851, during which WDO reads OK). Measure the arming window while disarmed: WDO release to SYNC, ARM and the first falling `progress_wdi` edge, at 1 kHz and at a 2.5 ms servo period, against the chosen watchdog's tWD(min) (13.40 ms for the TPS3851 with 4.7 nF and SET1 tied high; section 8.1) | 24 V applied |
| Host failure | With all eight channels moving: kill LinuxCNC, trigger a kernel panic, remove compute-module power | Last accepted UPDATE (`progress_wdi` edge) |
| Broken or stale communication | Open SCLK, MOSI, MISO and CS in turn; CS held low; injected CRC errors; replayed sequence; ioctl stalled past 5 ms | Injection instant |
| FPGA reset | FPGA_LOCAL_RESET_N; reconfiguration; **50 MHz oscillator stopped** (clock stall: only the external watchdog sees it; expected 13.40–17.87 ms for the TPS3851 with 4.7 nF, or about 57.7–71.9 ms for the TPS3431). Measure WDO-to-inhibit latency against the 2.13 ms budget (decides 4.7 nF against 3.9 nF, U15) | Injection instant |
| Power disturbance | 24 V dips and interruptions of set depth and duration, a slow brownout through the 18 V minimum, IO_3V3 and CORE_5V droop, and presence-pin glitches on the open J_EXP header. Glitch injection on the presence and EXP_PGOOD lines must show both tamper-filter properties over the fitted parts: every pulse of 30 µs or longer sets TAMPER, and pulses below the chosen lower bound do not. With MX4 fitted, also an EXP_5V sag below the supervisor threshold without a switch fault flag (TAMPER must set and bank A must stay inhibited after an FPGA reset), and the switch's inrush fault flag at power-on (must not set TAMPER inside the blanking time). Afterwards confirm that no automatic re-arm happens and that SYNC + ARM are required | Disturbance start |

**B5. Repeat under load.** Repeat B1, the B2 simultaneous run, B3 and every B4 drill, again recording (a), (b) and (c) separately, under each of:
- the touchscreen UI with the 3D preview animating;
- sustained network throughput with file transfer to storage;
- ESP UART traffic at its maximum message rate, with Wi-Fi/BLE active and an ESP reboot during motion;
- all of these combined.

## 16. Ordered implementation plan

**Desk-verifiable now** (source, host tests, HDL simulation, lint, technology mapping, LinuxCNC simulation; no hardware):

1. **P1 Specification and reference model.** Freeze this v3 draft as the target; extend `gateware/tools/protocol.py` with CNC3/CNS3/CAP3/CONFIGURE encode/decode and independent `binascii.crc_hqx` vectors for 8- and 12-installed cases. *Evidence: host tests.*
2. **P2 Parameterize the RTL** (NUM_STEP, NUM_ENC, FRAME_BITS; 11-bit `bit_count`; narrowed counters). Reproduce the probe mapping numbers inside the repository. First freeze the unmodified historical RTL as a separate evidence copy and confirm it still reproduces the 9,426-primitive manifest and the 252 + 27 checks, labelled historical. Record the parameterized 6/2 build's 9,423 primitives (`a_param_6_2`) as a new, separately labelled number; it does not replace 9,426. *Evidence: HDL simulation, lint, technology mapping.*
3. **P3 Implement the v3 endpoint**: frame; opcodes; 16-bit masks; installed/required masks; qualification with the accepted-class rule and the tamper input; power-cycle fault latches; the rejected-CONFIGURE clearing rule; per-channel EN gating; 4-sample filters on alarms, presence, PGOOD and tamper; alarm polarity and trip; the runtime timing table with the guarded load-minus-one low counter and a STEP-high ≥ 1 check (section 12); CONFIGURE echo; frame-register removal; and the `progress_wdi` form chosen under U15. New `tb_cnc_endpoint_v3` cases:
   - 8- and 12-installed ARM; ARM ≠ required mask; uninstalled channel in CONFIGURE;
   - a rejected CONFIGURE followed by SYNC + ARM of the old mask (must fail);
   - `expected_module_class` 2–7, 8 and 0xFF (byte 17 is a full u8); a seated module with MOD_ID 0b111, 0b000 or class 2 (INVALID, installed 0x0000, CAP3 byte 7 = 0);
   - removal and PGOOD loss mid-UPDATE: all 12 disarm 30–40 µs after the change; the modelled hardware OE drops at once and TX_PERMIT after the modelled tamper-filter delay;
   - presence glitches of 1 clock, 29 µs and 41 µs (reject, reject, accept);
   - presence glitch the FPGA accepts ⇒ modelled TAMPER set ⇒ still inhibited after FPGA reset;
   - EXP_PGOOD low with no switch fault flag, after the modelled blanking time ⇒ modelled TAMPER set ⇒ still inhibited after FPGA reset; the modelled fault flag asserted only inside the blanking time ⇒ no TAMPER;
   - tamper set across an FPGA reset (requalifies as a fault);
   - half-seated at boot; alarms on armed and unarmed channels; timing range limits; 1,023/1,025-bit frames;
   - pulse-timing monitors on all 12 channels at several timing tables, including an exact 200-tick period at 100/100 and a fault at floor(2³²/200) + 1 = 0x0147AE15 with the phase accumulator preloaded near overflow, or after at least 2.1 × 10⁵ pulses, plus 0x0147B000 as in the scratch run. Arithmetic: at 0x0147AE15 each 200-tick period leaves only 200 × 21,474,837 − 2³² = 104 of excess phase, so the first 199-tick interval (and the STEP_TIMING fault) appears only after about 21,474,733 / 104 ≈ 206,000 pulses (about 41 M core ticks, 0.83 s simulated); a 999-pulse run like the scratch check would see no fault;
   - atomic 12-rate update.

   *Evidence: HDL simulation, lint.*
4. **P4 Formal checks**: runtime 10-bit counter range invariants; `installed[i]=0 ⇒ STEP/EN idle`; `EXPANSION_* latched ⇒ armed = 0 until reset`; `tamper ⇒ installed = 0 after qualification`. *Evidence: partial formal.*
5. **P5 Synthesize** v3 12/4 with `synth_efinix` and the CDC check in the isolated rootfs; record counts against section 6 in a new manifest. *Evidence: technology mapping only.*
6. **P6 Driver and transports**: section 9 changes, synthetic CAP3 pages (8, 12, wrong class, frame bytes ≠ 128), fault injection at v3 offsets. *Evidence: host tests, target-less compile.*
7. **P7 LinuxCNC 2.9.4 simulation** through Verilated v3 RTL with `sim-8motor` and `sim-12motor`: machine on, gantry homing, MDI on every joint, commanded vs emitted counts; drills for alarm on M11, module removal and PGOOD loss (power cycle required; FPGA reset alone stays inhibited), a 12-joint profile against an 8-installed endpoint (refused before SYNC), an 8-joint profile with bank B fitted, the single-writer enable net and the 12 `or2` fault nets of section 10. *Evidence: HDL + host simulation.*
8. **P8 Configuration service, CLI, UI**: schema, simulated identity, add/remove flows, wiring guides, the refusal of a drive profile that is disabled by applied enable voltage without a declared drive-power interlock (U11), disconnected-interface tests. *Evidence: host tests.*
9. **P9 Electrical ledger and schematics**, coordinated with Codex's `hardware/` work and pending IS-1 integration; U1/U13 and the U15 limit are already confirmed:
   - a new candidate ledger for eight motors plus the 1.2 A TX_5V branch, with the 24 V logic entry re-derived and resized (it is over capacity at 8 motors, section 7.3);
   - the `tx_twelve` split per section 13 into the required eight-standard/four-plug-in architecture;
   - J_EXP, J_EXPF, the EXP_5V switch, the Ioff buffer including the TX_PERMIT_B channel, and the tamper latch with its filters, EXP_PGOOD blanking timer and permission term;
   - the MX4 schematic, with EN pull-ups to the switched IO_3V3 LED-anode supply, STEP/DIR pull-downs and the EXP_5V supervisor;
   - Codex's permission validator re-run on the D1 fanout (section 7.3.2);
   - selecting and pricing the enable switches, buffer, supervisor, EEPROM, ALARM_COM limiter and connectors.

   *Evidence: KiCad ERC plus independent netlist validators — schematic level only.*
10. **P10 Complete-design pin/bank plan and Efinity place-and-route/timing** on the full expanded design, for the layout chosen under U13/U14. *First permitted fit/utilization statement.* (Needs the user-installed vendor tool.)
11. **P11 Costing**: separate fitted fixed-base/card eight-motor and MX4 BOMs at 1/10/100/1,000 with unknowns explicit; cost factory-fitted twelve-motor, spare cards and complete packages separately. Retain option A/plain D1 comparisons as historical alternatives, not open user decisions. Show improvement cost deltas and compare assembly economics with the preliminary US$400 reference.

**Hardware steps later** (after P1–P11 and the BUILD_PLAN stage-5 bounded link prototype):

12. **H1** Physical LinuxCNC-to-FPGA link prototype measuring the 128 B servo cycle on the target host (bench plan B1; decides v3.1 asymmetric frames and U9).
13. **H2** Layout with DRC; bay SI/ESD review.
14. **H3** First eight-motor bench test per section 15 (B1–B4) with MX4 absent; later repeated with MX4 present, removed and inserted while powered (tamper latch). No machine attached.
15. **H4** Enable and alarm electrical tests against DM542T-class drives, including the ENA-unconnected wiring and its drive-power interlock; STEP/DIR at configured timing.
16. **H5** Loaded repetition (bench plan B5); gate E7 qualification. Machine operation remains unauthorized until these pass.

## 17. Decision status after requirements reconciliation

Numbers U1–U15 are retained for traceability. U1, U2, U12 and U13 are confirmed choices; U15 retains the 20 ms bound. U14 is a permitted implementation route with mandatory identity, sequence/freshness and CRC, not permission to reduce 24 general DI/16 general DO. Remaining part, connector and detailed protocol choices are engineering work; pending IS-1 integration must be reconciled before treating this older draft as an implementation instruction.

**Tier 1: blocks implementation.** Decide before P1/P3 (ABI and RTL) or P9 (schematic partition).

| # | Decision | Blocks | Recommendation in this record |
|---|---|---|---|
| U12 — resolved | Individual enable and alarm on every channel, confirmed in project memory; global interlock is not individual enable | P1, P3 engineering implementation remains | Preserve all interfaces; explicit supported-drive exceptions only |
| U11 | Drives disabled by applied enable voltage (DM542T V4): ENA unconnected plus a mandatory, declared independent drive-power or STO interlock; no enable-polarity field. A form-B enable-switch variant is a possible later option | P1 (CONFIGURE layout), P8 | ENA unconnected + interlock |
| U15 — requirement resolved | 20 ms fault-to-inhibit retained; about 72 ms is rejected. Exact part, progress form, startup and full tolerance/downstream timing must meet the shared interface contract | P3 progress implementation and P9 circuit closure remain | Drawn TPS3431 is noncompliant; historical candidates are not an approved replacement circuit |
| U1 — resolved | MX4 plug-in module for motors 9–12; eight motors standard | P9, P11 split implementation and full costing remain | Preserve historical full-population arithmetic for comparison only |
| U13 — resolved | Fixed wiring base with replaceable service modules; FPGA, clock, flash and supervisory circuits on the motion card | P9, P10 complete connector, power, fit and cost work remain | Field terminals stay in place during approved card replacement |

**Tier 2: needed before schematics and costing** (P9, P11).

| # | Decision | Recommendation |
|---|---|---|
| U14 — conditional permission confirmed | Serial transport may serve the full 24 general DI and 16 general DO only with identity, sequence/freshness and CRC validated before outputs change; marker-only proposal superseded | Recompute exact transport/pin/power/cost/timing against IS-1; independent permission path remains direct |
| U3 | ALARM_COM on every motor plug as a current-limited FIELD +24 V feed, with the revision-2 contact order (LOGIC 1–5, shield 6, enable switch 7–8, FIELD 9–10), or a separate two-contact alarm plug per motor | Accept the reordered plug, subject to creepage and short review |
| U8 | A bay presence change stops the whole machine, even an eight-motor profile. Now enforced in hardware by the tamper latch; recovery needs a power cycle. If no, the tamper term is left out of the permission block and only bank B is inhibited | Confirm yes |
| U4 | Motor plug pitch: 3.5 mm, 5.08 mm, or stacked two-row | 3.5 mm |
| U6 | Bank-B 5 V: base TX_5V branch (1.2 A) or a module-local buck (D2) | Base branch |
| U10 | Per-channel HOME inputs (present in Codex's pin allocation) as motor-channel pins or general DI | General DI unless the user wants per-motor home plugs |
| U5 | Per-channel physical enable readback (4–12 extra FPGA inputs) | Defer; logical echo only in v3.0 |
| U2 — resolved | Twelve-motor SKU ships with the plug-in module factory-fitted | Include assembly, programming/identity, complete test and expansion cost |

**Tier 3: after measurement, or cosmetic.**

| # | Decision | Recommendation |
|---|---|---|
| U9 — target recorded | Reliable 1 kHz full exchange, 700 µs completion under defined worst-case load, 72-hour combined-load and fault-injection qualification; any faster mode is a later separately qualified option | Preserve targets from project memory; detailed frames follow pending IS-1 integration and measured H1/B1 evidence |
| U7 | Terminal labels: M0–M11 (0-based, matches ABI) or Motor 1–12 (1-based, D2) | User's choice; the UI can show both |

Engineering items that are not user decisions but cost money on every unit: the resized 24 V logic-entry converter (CORE_24V over capacity at eight motors) and the TX_5V branch.

## 18. Review closure log (revision 2)

| # | Review item | Closed by | Where |
|---|---|---|---|
| 1 | Bank-B enables defaulted closed by pull-downs | Pull-ups to the module's switched LED-anode supply on EN8_N–EN11_N; pull-downs on STEP/DIR only; the module LED-supply switch is gated by TX_PERMIT_B, which carries TX_PERMIT AND both presence pins AND EXP_PGOOD AND not tamper | 7.3, 11 |
| 2 | TX_PERMIT_B was the raw permission net | Routed through a spare Ioff-buffer channel with the bank-B OE, module pull-down; permission fanout re-derived; "already sized" removed | 7.2, 7.3.2, 8 |
| 3 | Rejected CONFIGURE left `config_valid` | A rejected CONFIGURE clears `config_valid`, `required_mask` and both alarm masks; `config_generation` kept | 5.3, 8 |
| 4 | Reference drive's enable polarity unsupported | Better correction than the proposed field, with justification: no `enable_sense`, because a permission-gated LED supply cannot hold an inverted drive disabled; ENA unconnected plus a mandatory drive-power interlock; §3 claim limited to timing | 3, 5.4, 8, U11 |
| 5 | Module class and INVALID handling | CONFIGURE accepts only 0 or classes in CAP3 byte 54; bank B qualifies only with an accepted MOD_ID; 0b111, 0b000 or unsupported → INVALID; INVALID/CHANGED give installed 0x0000 and CAP3 byte 7 = 0 | 5.4–5.6, 8 |
| 6 | CORE_24V over capacity, not "at 2.00 A" | 2.004 A (2.01 A with the ledger round-up) against 2 A at eight motors, 2.135 A at twelve; TX_5V does not relieve it; 24 V entry must be resized | 7.3 |
| 7 | Option A rejected on non-discriminating grounds | Rejected on per-unit cost and edge length only; 145 vs 138 pins and the shared 6.35 A stated | 3 |
| 8 | Qty-100 cost table | Pooled module $10.18; $10.07 as system delta; D1 twelve-motor $30.54 = option A; cost advantage limited to eight-motor units | 3, 7.4 |
| 9 | P2 "9,426 unchanged" | Freeze the historical RTL copy for 9,426; record 9,423 for the parameterized build | 16 (P2) |
| 10 | Invalid HAL enable wiring | Single writer per `simulation.hal` line 16, or `motion.motion-enabled`, or an AND component; `cnc1.enable`/`cnc1.fault` added to the pin list; 12 `or2` instances | 9, 10 |
| 11 | Reset-only versus power cycle | Power cycle required and enforced by a base tamper latch cleared only by logic POR; +1 FPGA pin (145) | 4, 5.5, 7.1, 7.3.1, 8 |
| 12 | EXP_PGOOD from a fault flag | Supervisor on EXP_5V wired-AND with the fault flag (or a switch with a real power-good); qualification window vs max turn-on plus power-good delay | 7.3.1 |
| 13 | No input filter on presence/PGOOD | 4-sample filter at 10 µs, 30–40 µs latency; Ioff OE unfiltered; the power-cycle tamper latch RC/Schmitt-filtered so noise on the open header cannot trip it | 7.3.1, 8 |
| 14 | FIELD and LOGIC adjacent on the motor plug | Contacts reordered with shield and the isolated enable pair between the domains; claim narrowed to J_EXP/J_EXPF; noted under U3 | 7.2, U3 |
| 15 | "Four remaining reserved bytes" | Three (117, 124, 125) | 5.5 |
| 16 | "~15.2k (52–77 %)" | Re-derived: ~15.2k, 47–77 % (lower bound unchanged by extra FF) | 6.2 |
| 17 | FF attribution | Frame register 736; 2,376 (53 %); encoders ~308 (~77 each); A3 updated | 1, 6.1, 6.2 |
| 18 | Incomplete hard-coded list; hal_cnc1.c:55 | Full line table; line 55 identified as simulation-seconds conversion; line 166 added | 9 |
| 19 | Duplicate letters do not need BOTH | Corrected; BOTH recorded as the man page's recommended choice with its racking caution; the trivkins.c line cited from the review, not re-checked locally | 10 |
| 20 | Watchdog fed only by UPDATE | Restarted by accepted ARM or UPDATE; only `progress_wdi` is UPDATE-only | 5.1, 8 |
| 21 | A1 "not a recorded user statement" | Project memory line 17 records it; the user's request itself does not specify it; U12 kept | 1 |
| 22 | 2 kHz "marginal" | Not feasible at 5 MHz (82 %); 66 % at 6.25 MHz before overhead | 5.7 |
| 23 | "0 problems twice"; enable-supply wording | Four check passes with line numbers; per-bank LED-supply switches in section 4 | 4, 6.1 |

### 18.1 Verification closure (revision 3)

An independent verifier checked revision 2 and reported ten remaining problems. Each was re-checked before editing; none was rejected. Rows marked "partly" state what this revision added beyond the verifier's proposed text.

| Problem | Check made | Closed by | Where |
|---|---|---|---|
| EXP_PGOOD loss did not set TAMPER (items 11/12) | Source inspection of revision 2: TAMPER was set only by a presence change or the switch fault flag, so a sag below the supervisor threshold latched EXPANSION_CHANGED in the FPGA but left TAMPER clear; an FPGA reset would requalify 0x0FFF. Confirmed | EXP_PGOOD low after a blanking time (at least maximum turn-on plus maximum power-good delay) sets TAMPER; the term is armed only if EXP_5V was enabled at power-on. Added beyond the proposal: the term is level-sensitive (a rail that never rises also trips), and the blanking must end no later than one qualification window after EXP_5V enable, otherwise a dip the FPGA latches could recover inside the blanking time without setting TAMPER. Section 8 row renamed; P3 cases and B4 injections added | 7.3.1, 8, 15 (B4), 16 (P3) |
| Tamper filter specified the wrong way round (items 13/11) | Arithmetic: the FPGA filter rejects pulses under 30 µs and may accept 30–40 µs; a filter that rejects everything under 30 µs over tolerance trips somewhere above 30 µs, leaving a gap where the FPGA latches and TAMPER does not. Confirmed | Every pulse of 30 µs or longer must set TAMPER over tolerance; pulses below a lower bound (for example 5–10 µs) must not; shorter-pulse trips are still latched by the FPGA via EXP_TAMPER_N. Both properties by glitch injection. P3 case added | 7.3.1, 15 (B4), 16 (P3) |
| LED-anode supply voltage unspecified | Arithmetic: a 5 V anode against a 3.3 V push-pull high cathode leaves about 1.7 V, above typical 1.1–1.4 V opto LED forward voltages. Confirmed | Each LED-anode supply is a switched copy of IO_3V3 (bank B from J_EXP pin 35); a higher anode rail needs open-drain drivers and is not allowed. The added IO_3V3 load goes to the P9 ledger | 7.3, 11, 16 (P9) |
| Where EXP_PGOOD is generated; qualification-window wording (item 12) | Source inspection: section 4 and 7.4 placed the supervisor on the base while J_EXP pin 28 carried an open-drain EXP_PGOOD with no module driver. Confirmed. The window sentence constrained the start and then concluded on the end. Confirmed | Option (a): supervisor moved to the module, sensing EXP_5V after pins 1–2. Added beyond the proposal: a separate-SENSE supervisor powered from IO_3V3 so its output is defined with EXP_5V absent, and the pull-up on the module with a weak base pull-down so an open pin-28 or pin-35 contact reads "not good". Window sentence replaced as proposed | 4, 7.2, 7.3.1, 7.4, 11, 16 (P9) |
| TPS3851 behaviour while disarmed (U15) | Advice verification (datasheet desk review): WDO pulses low for 170–230 ms and WDI is ignored while WDO is low; SET1 low disables; SET1 low-to-high has a 150 µs setup. Source inspection: `progress_wdi` resets to 0 and toggles only on accepted UPDATE (`cnc_endpoint.v` lines 178 and 212); [MACHINE_PERMISSION.md](../reports/MACHINE_PERMISSION.md) line 70 describes the same cycling for the TPS3431. Confirmed | New 8.1 row "Behaviour while disarmed" with the 13.40 ms arming window and the SET1-from-arm-request alternative; B4 Startup row measures the arming window; U15 row updated | 8.1, 15 (B4), 17 |
| synthesis.log line numbers run-specific (item 23) | `grep` of all seven logs: the lines differ per run (for example 487/753/2235/2239 in `a_orig_6_2`; 601/867/2625/2629 in `c_param_12_4`); 28 of 28 report 0 problems. Confirmed | Wording now per run with examples | 6.1 |
| tx_twelve reference return | Netlist inspection of `hardware/tx_twelve/netlist.xml`: JREF1 pins 1–6 are LOGIC_GND; there is no JPOWER; E-16 concerns the six-channel sheet. Confirmed | Corrected | 13 |
| Numeric consistency (13/14) | Arithmetic with `budget.py`'s formula: 12 motors give 2.135 A, 2.14 A with the ledger round-up; the tied-input variant keeps six status inputs (138 + 6 = 144); the motor plug has 10 contacts (80 + 32 = 112). Confirmed | Rails row uses probe values with round-up in brackets, and 7.3 gives the twelve-motor round-up; option A pin note; 14.1 recounted, with the 104 case stated | 7.3, 13, 14.1 |
| "which the service enforces" | Source inspection of 5.4: the service can refuse a profile without the declaration but cannot verify the interlock. Confirmed | Replaced with the refusal, commissioning confirmation (H4) and the electrical-verification caveat | 8 |
| P3 test plan | Arithmetic: at 0x0147AE15 the excess is 104 per 200-tick period, so the first 199-tick interval needs about 206,000 pulses (0.83 s simulated); byte 17 is a full u8. Confirmed | Preloaded phase or at least 2.1 × 10⁵ pulses, plus 0x0147B000; class cases 2–7, 8 and 0xFF | 16 (P3) |

---

Nothing in this record is implemented or ready for manufacture. The numbers in sections 6, 7, 8.1, 12 and 14 are technology-mapping, HDL-simulation, datasheet, datasheet-desk-review, recorded-price or arithmetic results from the scratch probes and checks named above, or Codex's schematic evidence read by inspection. None is a fit, a measured timing, an ERC/DRC result of this design or a physical measurement. Section 15 is a plan for the first physical measurements.
