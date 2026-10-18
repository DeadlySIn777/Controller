Interface specification revision: IS-1

# 04 — Safety, permission, power and fault timing

Section 04 of interface specification IS-1, written 28 September 2026 and integrated 29 September 2026 (section 6.1 sources, section 6.3 fan-out, section 8 field placement, output driver and overvoltage note aligned with sections 01-03), and repaired the same day after the independent review (OUT arm-latch clear term, OPI_OUT and OPI_BOE, card OUT_EN latches, permit-input defaults and DIC_OK, PERMIT_OUT held open in self-test, CWD leakage allowance, AUX_5V chain, numeric bounds on every fault path, safety-interface rules, AI-group and arm-lamp loads). Machine-readable companion: [`spec/safety.json`](../../spec/safety.json) (`"spec_revision": "IS-1"`). Codex's hardware (schematics, power/protection, connectors, PCB, hardware BOM) and Claude's implementation (gateware, CNC1 protocol and driver, configuration and diagnostics service) both build against this revision. A change to anything here needs a new revision identifier (IS-2), not an in-place edit.

**Status.** This is a specification. Nothing in it is implemented, simulated, synthesized, drawn, laid out, measured or ready for manufacture. The six-joint/two-encoder endpoint, its tests and its synthesis result are **historical baseline evidence** and are not eight- or twelve-channel evidence. None of this is a certified safety function. Machine E-stop, STO, brakes and stored-energy control still need their own machine-level design.

## 0. Evidence labels

Every number carries one of these labels.

| Label | Meaning |
|---|---|
| [DS] | Manufacturer datasheet or product page, opened and read for this section (links in section 15) |
| [DDR] | Datasheet desk review done earlier and recorded in the repository (TPS3851 timing, advice-verification record) |
| [AR] | Arithmetic from stated inputs. Not a measurement |
| [SI] | Source inspection of repository files |
| [REQ] | Requirement or budget allocation set by this specification. Not evidence that anything meets it |
| [RES] | Engineering reservation carried over from the electrical ledger or set here |
| [ME] | Physical measurement. **There are none in this section.** Every [ME] item below is a required future measurement |

No HDL simulation, synthesis, ERC, DRC, SPICE or bench measurement was run for this section.

## 1. What this section supersedes

The following points in [MOTION_EXPANSION_8_TO_12.md](../MOTION_EXPANSION_8_TO_12.md) (revision 3) are superseded by IS-1. The rest of that record stays as design history.

| Old text | IS-1 decision | Section here |
|---|---|---|
| §5.4 and U11: no enable-polarity support; DM542T V4 wired with ENA unconnected | Every channel has a normally-open **and** a normally-closed solid-state switch. Disable-on-current drives, including the DM542T V4, are **supported** through the normally-closed switch | 3 |
| §7.2: 10-contact motor plug | 14-position motor plug signal set (13 used) | 3.5 |
| §8 filtering: "the Ioff-buffer OE uses the unfiltered presence and EXP_PGOOD lines … a glitch there only blanks bank-B outputs for its duration and latches nothing" | Withdrawn. Every gate term is filtered **before** it reaches any output gate, and every output-gate transition while armed is captured by a hardware latch | 4 |
| §8.1 and U15: watchdog part and timing open | TPS3851G18SDRBT, timing capacitor 3.3 nF C0G (CL10C332JB8NNNC), `progress_wdi` changed to one pulse per accepted ARM or UPDATE, SET1 driven by the motion request | 5 |
| §14.3: permission-latch placement | On the replaceable motion card, beside the FPGA it supervises | 6 |
| §8: "Enable output closes only when …" (single switch) | Section 3.3 state table | 3.3 |
| Implicit "everything off" fault response for general outputs | A fault state per output function (section 9) | 9 |

Decisions U1 (plug-in MX4 module), U12 (individual enable and alarm) and U13 (FPGA on a replaceable motion card behind a fixed wiring base) were confirmed by the user on 28 September 2026 ([PROJECT_MEMORY.md](../../PROJECT_MEMORY.md)). U8 (a bay presence change stops the whole machine) is adopted here.

## 2. Timing classes: kept separate

These five quantities are different things. None may be traded against another, and none may be raised to make something fit.

| Class | Value | Kind | Enforced by |
|---|---|---|---|
| Servo period | 1.000 ms (1 kHz) | Deadline. A late cycle is an overrun, counted and reported | LinuxCNC servo thread; driver period check |
| Cycle-completion target | 700 µs of each 1 ms cycle | **Engineering-margin target, not a safety limit.** Missing it is a recorded finding, not a fault | Measurement only (section 14 here; bench method in section 01 section 5.7) |
| FPGA command watchdog | 5.000 ms [SI] (250,000 ticks at 50 MHz) | Safety-relevant timeout. No accepted ARM/UPDATE for 5 ms latches WATCHDOG and disarms | FPGA logic |
| External (clock-stall) watchdog | 9.26 / 11.04 / 13.02 ms min/nom/max [DDR][AR], including the CWD leakage allowance (9.51 / 12.67 ms from capacitor and IC tolerances alone) | Safety-relevant timeout, independent of the FPGA clock | TPS3851 on the motion card (section 5) |
| Fault-to-inhibit | ≤ 20 ms [REQ], user requirement, not relaxed | Bound from a fault instant to "electrical outputs inhibited" (section 7.1) for every path, including clock stall | Hardware permission chain |

**700 µs endpoints** (the protocol section owns the full per-cycle schedule; this is the safety section's definition so that all sections measure the same thing):

- **Start:** the *nominal* period boundary T(k) of the servo thread, i.e. the instant the thread should have started. Scheduling latency therefore counts against the 700 µs.
- **End:** the FPGA-side commit of the cycle's last host-to-FPGA exchange (chip-select release of the UPDATE/I/O frame that the FPGA accepts), observed on a logic analyser.
- **Included:** thread wake-up latency, all LinuxCNC computation for the cycle, driver encode/decode, spidev/ioctl overhead, wire time of every exchange, CS guards, inter-byte and DMA gaps.
- **Measured separately, not folded into the 700 µs:** (a) **input data age** = time from the FPGA snapshot instant (CS assertion of the status read) to the moment the servo thread uses that data; (b) **output update latency** = time from the thread's computation of a command to the FPGA commit, and from the commit to the first physical output change (for STEP, the first edge at the new rate).

The 700 µs target, the 1 ms deadline, the 5 ms watchdog and the 20 ms fault-to-inhibit bound are reported in separate columns in every test record.

**Protection never depends on telemetry (T2).** Every item in sections 4–7 acts in hardware or in the FPGA without any host transfer. Telemetry (currents, temperatures, history) reports what protection already did.

## 3. Per-channel drive enable, both polarities, and the drive alarm

### 3.1 Selected parts

| Function | Part (orderable) | Key ratings | Evidence |
|---|---|---|---|
| Normally-open switch, "form A", one per channel | Toshiba **TLP3640A(TPL,E)** (SO4, 1-Form-A photorelay) | VOFF 60 V; ION 1 A; RON ≤ 0.3 Ω at 1 A, IF 5 mA; IFT ≤ 3 mA; IOFF ≤ 1 µA at 60 V; VF 1.50/1.65/1.80 V at 10 mA; tON ≤ 0.5 ms, tOFF ≤ 0.2 ms (RL 200 Ω, VDD 20 V, IF 5 mA, 25 °C); isolation 3,750 Vrms; Topr −40 to 110 °C; output dV/dt ≤ 0.1 kV/µs with LED off | [DS] Toshiba product page and datasheet Rev.1.0.A |
| Normally-closed switch, "form B", one per channel | Toshiba **TLP4176A(TP,F)** (2.54SOP4, 1-Form-B photorelay) | VOFF 60 V; ION 0.5 A; RON ≤ 2.5 Ω at 0.5 A; IFC ≤ 3 mA to open, IFT ≥ 0.1 mA return (stays closed below 0.1 mA); IOFF ≤ 1 µA; VF 1.0/1.15/1.3 V at 10 mA; recommended VDD ≤ 48 V, IF 5–25 mA; tON ≤ 1 ms, tOFF ≤ 3 ms (IF 5 mA, 25 °C); isolation 1,500 Vrms; Topr −40 to 105 °C | [DS] Toshiba product page and datasheet Rev.3.0.A |
| LED cathode driver (open drain, 5.5 V tolerant, Ioff) | TI **SN74LVC07APWR** (hex, TSSOP-14), 2 per 8 channels on bank A, 1 on MX4 | VCC 1.65–5.5 V; outputs tolerate 5.5 V; IOL 24 mA; Ioff partial-power-down | [DS] TI product page |
| Per-bank LED supply switch | TI **TPS22918DBVR** (SOT-23-6 load switch with configurable quick output discharge) | 1–5.5 V, 2 A, 52 mΩ typ | [DS] TI product page |

Why these: both photorelays are MOSFET-output, two-terminal, AC/DC-capable switches from one manufacturer with the same trigger-current class (≤ 3 mA), so one LED string drives both. The form-B part is the only verified 60 V-class normally-closed photorelay in a four-pin SMD package found for this revision (the 350 V TLP4176G has RON ≤ 25 Ω; the 60 V TLP4590A is a larger DIP6). The form-A part is chosen over Panasonic AQY212GS because its turn-on time is 0.5 ms max against 5.0 ms max [DS], which shortens the enable path in the fault budget.

### 3.2 Circuit per channel (requirement on Codex's motor-interface card and MX4 module)

```text
 MOTION_5V (bank A) / EXP_5V (bank B)
      |
 TPS22918 (EN = TX_PERMIT_x after the card's filtered receiver, section 4.2)
      |  LED_SUPPLY_x, quick output discharge fitted
      +--> LED of TLP3640A --> LED of TLP4176A --> 220 ohm 1 % --> SN74LVC07A output
                                                                   (input = EN_N_i, active low, from the FPGA,
                                                                    bank B via the Ioff buffer; 10 kohm pull-up
                                                                    to IO_3V3 on the card)
 Floating outputs:  EN_COM ---[TLP3640A]--- EN_NO      (open when LED dark)
                    EN_COM ---[TLP4176A]--- EN_NC      (closed when LED dark)
```

- The two LEDs are in **series**. One current drives both; an open LED, an open resistor or a dead driver leaves both LEDs dark, which is the disabling state for both wiring modes.
- LED current [AR] from a 4.85–5.15 V supply [REQ], VF from [DS] at 10 mA and VOL(LVC07A) ≤ 0.55 V [DS table, confirm at schematic]: minimum (4.85 − 1.80 − 1.30 − 0.55)/(220 × 1.01) = **5.40 mA**; maximum (5.15 − 1.50 − 1.00)/(220 × 0.99) = **12.17 mA**. Minimum is 1.8× the 3 mA worst-case trigger current at 25 °C; maximum is inside TLP4176A's recommended 5–25 mA and below TLP3640A's 30 mA absolute rating. Cold-temperature margin (VF rises) is an [ME] item; the product's rated internal ambient in this revision is 0–55 °C [REQ].
- Off-state: the SN74LVC07A's output leakage must stay below the TLP4176A's 0.1 mA minimum return current so a "dark" LED is guaranteed dark [REQ; confirm IOZ at schematic].
- The SN74LVC07A is non-inverting with an open-drain output: a low input sinks LED current, a high or undriven input (pulled up) leaves the LED dark. An unconfigured FPGA, an unpowered IO_3V3 (Ioff: output high impedance) or a missing Ioff-buffer drive therefore all leave both switches in their disabling state.
- Two independent cuts per channel: the FPGA's EN_N_i (per channel) and TX_PERMIT through TPS22918 (per bank, hardware, no FPGA clock). Bank A's TPS22918 is on the bank-A motor-interface card; bank B's is on the MX4 module, fed from EXP_5V and enabled by TX_PERMIT_B.
- The logical enable EN_i (driven out as EN_N_i = NOT EN_i) is `armed AND mask[i] AND installed[i] AND (bank B healthy if i ≥ 8) AND no fault AND not self-test` (unchanged from the record, §8), with hardware TX_PERMIT on top.
- **AUX_5V chain for the NC-5V (DM542T V4) wiring [REQ, AR].** AUX_5V setpoint 5.00 V ±1.5 % → ≥ 4.925 V; bank limiter drop ≤ 0.05 V → ≥ 4.875 V at the monitor node; AUX5_OK falling trip ≥ 4.80 V; base and connector distribution drop ≤ 0.05 V at full bank load → **XMn.11 ≥ 4.75 V whenever AUX5_OK is high**. Worst-case ENA voltage while disarmed = 4.75 − 2.5 Ω × 16 mA (TLP4176A RON [DS] × DM542T maximum logic current [DS]) − 1.25 Ω × 16 mA (declared maximum cable loop resistance, about 8 m of 0.25 mm² pair, entered in the drive profile) = **4.69 V ≥ 4.5 V**, 0.19 V margin [AR]. At the moment AUX5_OK trips the terminal is still ≥ 4.70 V, so the drive leaves the disabled band only after ARM has already been refused and a fault latched (exception E1). Commissioning measures ENA+ to ENA− on every NC-5V channel while disarmed: pass ≥ 4.60 V [ME].
- Per-channel protection: a bidirectional TVS across EN_COM–EN_NO and EN_COM–EN_NC with stand-off ≥ 30 V and clamping below 60 V at its rated pulse [REQ; part to be selected and verified by Codex]. Published enable-loop rating: **DC or AC, 0–30 V, ≤ 50 mA continuous per switch** [REQ], below both parts' 60 V/0.5 A ratings and the TLP4176A's 48 V recommended VDD.

### 3.3 States (normative)

"Energized" means LED current flows. EN_NO/EN_NC are the terminal states.

| Condition | LED | EN_NO (form A) | EN_NC (form B) | Enable-on-current drive (wired to NO) | Disable-on-current drive, e.g. DM542T V4 (wired to NC) |
|---|---|---|---|---|---|
| Armed, channel in the armed mask, TX_PERMIT high | on | closed | open | enabled | enabled (no ENA current) |
| Disarmed, or channel not in mask | off | open | closed | disabled | disabled (ENA current flows) |
| Any latched fault, watchdog trip, inhibit | off | open | closed | disabled | disabled |
| FPGA unconfigured, in reset or clock stalled | off (TX_PERMIT low, TPS22918 off) | open | closed | disabled | disabled |
| Controller LOGIC power lost (MOTION_5V/IO_3V3 gone), FIELD power present | off | open | closed | disabled | **disabled**, because the ENA loop is fed from the FIELD-domain AUX_5V (3.4, 10.3) |
| Motion card removed (power-off service, or pulled under power) | off (TX_PERMIT pull-downs) | open | closed | disabled | disabled |
| Motor-interface card (or MX4) removed | switches absent | open | **open** | disabled | **enabled if the drive and its ENA loop source are powered** (exception E2) |
| Self-test (section 5.4) | off (every EN_N_i forced high) | open | closed | disabled | disabled |

### 3.4 Wiring modes (generated by the configuration service from the drive profile)

| Mode | Wiring | Loop source | Use |
|---|---|---|---|
| NO-sourced | AUX_24V → drive EN+; drive EN− → EN_NO; EN_COM → AUX_RTN | Controller AUX_24V (FIELD, current-limited per bank) | 24 V-class enable-on-current inputs |
| NO-drive | Drive's own enable supply through EN_NO/EN_COM (floating contact) | Drive | Servo "SON"-type inputs referenced to the drive's COM |
| NC-5V (**DM542T V4 reference**) | DM542T S2 set to 5 V (needed anyway for the 5 V differential STEP/DIR, [DS] manual); AUX_5V → ENA+; ENA− → EN_NC; EN_COM → AUX_RTN | Controller AUX_5V (FIELD domain, section 10.3) | Drives disabled by 4.5–24 V at ENA and enabled at 0–0.5 V [DS] |
| NC-drive | Drive's own disable loop through EN_NC/EN_COM | Drive or user supply that is powered whenever the drive is | Other disable-on-current drives |

DM542T V4 facts used [DS, OMC DM542T V4.0 manual]: ENA "default no connection" = enabled; disable by 4.5–24 V, enable by 0–0.5 V; logic signal current 7/10/16 mA min/typ/max; ENA must lead DIR by at least 200 ms; STEP high and low ≥ 2.5 µs; DIR setup ≥ 5 µs; pulse input ≤ 200 kHz; supply 18–50 V. The generated profile therefore sets `enable_settle_ms` ≥ 200 before any nonzero rate, the per-channel timing table to ≥ 125/125/250 ticks, and the rate cap to ≤ 200 kHz.

**Explicit exceptions (not hidden, shown by the configuration service and in the wiring guide):**

| # | Exception | Consequence | Required mitigation |
|---|---|---|---|
| E1 | Disable-on-current drive whose ENA loop source is lost while the drive stays powered (AUX_5V fault, whole-controller power loss including FIELD, user supply off) | Drive becomes enabled. STEP/DIR are high-impedance (TX_PERMIT low), so no pulses, but the motor is energized | AUX_5V_x power-good is monitored (section 8); ARM refused and a fault latched while it is low. The profile must declare an independent stop path (E-stop removes drive power or STO). The service refuses the profile without it and the commissioning checklist confirms it; the service cannot verify it electrically |
| E2 | Motor-interface card or MX4 removed while the drive and its ENA loop source are powered | Same as E1 for disable-on-current drives | Service procedure removes drive power first (section 11 of this spec, power-off service). Not a supported operating state |
| E3 | Open ENA conductor on a disable-on-current drive | Drive enabled whenever powered; not electrically detectable in IS-1 | Commissioning check "disarmed ⇒ drive disabled" on every channel, repeated after any harness or card change |
| E4 | Welded (failed-short) photorelay | Form A short: drive enabled while disarmed (no pulses). Form B short: drive cannot be enabled (detected at first jog) | Commissioning check E3 detects A-short; no per-channel physical readback in IS-1 (U5 remains deferred; cost of 12 readback inputs recorded as an open costing item) |
| E5 | Drive that needs an enable voltage above 30 V or a current above 50 mA, or an enable input that is not isolated and not compatible with a floating contact | Not supported by the built-in switches | Use an external relay module driven from EN_NO; listed as an unsupported profile until qualified |

No other enable behaviour is excluded. A global power interlock is never counted as a per-channel enable.

### 3.5 Motor plug signal set (supersedes the 10-contact plug)

Fourteen positions, thirteen used. Codex's connector map owns the family, contact numbers and keying; this section fixes the signal set and domain grouping.

| Group | Signals | Domain |
|---|---|---|
| Motion | STEP+, STEP−, DIR+, DIR−, SIG_0V | LOGIC (AM26C31, referenced, not isolated) |
| Separation | SHIELD (chassis), one unpopulated position | chassis / clearance |
| Enable | EN_NO, EN_COM, EN_NC | floating (photorelay outputs) |
| Aux supply | AUX_5V, AUX_24V, AUX_RTN | FIELD, current-limited per bank |
| Alarm | ALARM_IN | FIELD (ISO1212 sinking input) |

Requirement on the connector map: LOGIC contacts and floating/FIELD contacts are separated by SHIELD and the unpopulated position; creepage and clearance between SIG_0V and any FIELD or floating contact must suit 60 V working voltage [REQ]; a short between any two adjacent contacts must not damage anything outside the motor-interface card (containment matrix, section 13).

### 3.6 Drive alarm input

- Front end: one ISO1212 channel per motor (sinking, current-limited; 2.47 mA maximum per input with the recorded 562 Ω RSENSE [DS, recorded in the record §7.3]).
- Wiring: AUX_24V → drive ALM+; drive ALM− → ALARM_IN. For a drive with a sourcing alarm output referenced to its own 0 V, that 0 V connects to AUX_RTN.
- Polarity is per channel in CONFIGURE (`alarm_on_no_current`). **DM542T V4: `alarm_on_no_current` = 1**, because its ALM+/ALM− is "low impedance as default" and goes high impedance in a protection fault (30 V/100 mA rating) [DS]. An open alarm wire then reads as an alarm (fail-closed).
- AUX_24V is monitored per bank (AUX24_OK_A/B, section 8). A shorted AUX_24V on one plug pulls the whole bank's feed into current limit; the monitor faults that bank and disarms. Without the monitor, drives with `alarm_on_no_current` = 0 would read "healthy" with a dead feed.
- Filter: 10 µs sampler, four equal samples, accepted in 30–40 µs [AR, record §8], then trip → disarm all.

## 4. Motion-output interruption rule (correction 2)

### 4.1 Rule (normative)

1. **Any event that interrupts an active motion-output path latches a fault and invalidates the position state of every channel on that path.** "Active" means the FPGA holds that path armed. "Interrupts" means any transition of a physical gate that can stop or change a STEP, DIR or enable output: TX_PERMIT, TX_PERMIT_B, the bank-B Ioff-buffer OE, the AM26C31 G inputs, the TPS22918 enables, a card presence, power-good or tamper term, or the FPGA's own output gating on a fault. The same rule applies to the output domain: any accepted OUT_PERMIT transition latches OUTPUT_PERMIT_LOST and leaves the affected outputs off until a new deliberate IO_ENABLE.
2. **A pulse that the qualification filter rejects never reaches a physical output gate.** Filtering sits in front of the gate, never behind it. There is no path by which outputs are "briefly blanked and then carry on".
3. Recovery needs a new SYNC and ARM **and** a re-established position (homing, or an encoder-verified re-reference defined by the profile). Nothing is restored automatically.

### 4.2 Design

```text
 raw gate term (presence, PGOOD, tamper, TX_PERMIT arriving at a card)
      |
  RC + Schmitt qualification filter   <-- rejects every pulse < t_rej, accepts every pulse >= t_acc
      |
  QUALIFIED GATE NET  (the only version used anywhere downstream)
      |------------------> output gate (AM26C31 G, Ioff OE, TPS22918 EN)
      |------------------> OPI latch CLR_N (SN74LVC2G74DCUR, asynchronous)
      |------------------> FPGA status input (synchronized, 4-sample filter for status only)
      '------------------> tamper latch (where the term is a presence/PGOOD term)
```

- **Output-path-interruption (OPI) latch.** One D flip-flop per gate domain: TX (motion card: TX_PERMIT final gate), A (bank-A card: qualified TX_PERMIT_A), B (MX4: qualified TX_PERMIT_B), **BOE** (motion card: the qualified bank-B Ioff-buffer OE net itself) and **OUT** (motion card: OUT_PERMIT final gate). D = 1; CLK = FPGA strobe `OPI_REARM_x`, issued only during ARM (TX, A, B, BOE) or IO_ENABLE (OUT, strobe `OPI_REARM_O`) while the gate net is high; asynchronous CLR_N = the gate net. Q (OPI_OK_x) goes to the FPGA. Q = 1 means "no gate transition since the last ARM (or IO_ENABLE)".
- **Why a separate BOE latch.** The bank-B Ioff buffer and its OE are on the motion card (section 02 D02-5). An OE low pulse between 0.1 and 2 µs can float STEP8–11, DIR8–11 and EN_N8–11 at the MX4 while its TX_PERMIT_B receiver rejects the pulse and OPI_B stays set. OPI_BOE is cleared by the OE net itself, so every OE transition that can change an output latches OUTPUT_PATH_INTERRUPTED. Every AM26C31 STEP and DIR input on the MIA and the MX4 has a 10 kΩ pull-down, matching the FPGA's STEP-low idle state, so a floated input rests at the idle level and cannot create a counted edge; EN_N inputs keep their pull-ups (LED dark). Bank-A buffers have their OE tied active (power-off isolation comes from Ioff and the receiver pulls), so they have no OE transition to latch.
- **Output cards.** Each DO and ACC card has an OUT_EN latch (SN74LVC2G74DCUR half, CLR_N = qualified OUT_PERMIT_k) in series with CARD_EN in every output enable; an accepted OUT_PERMIT_k drop turns the card's outputs off and keeps them off (PWM low, AO clamped, SW_STATE written 0) until a new epoch and IO_ENABLE re-arm it (section 01 section 4.7). The ACC's second half does the same for PROC_PERMIT (PEN latch).
- **Why nothing can slip through.** The qualified net's shortest possible pulse is set by the filter (≥ t_rej by construction, and the RC slew across the Schmitt hysteresis gives the output a minimum pulse width that Codex computes). IS-1 requires that minimum to be ≥ 100 ns [REQ], against a 3.5 ns minimum clear pulse for the SN74LVC2G74 at 3.3 V ±0.3 V, 125 °C [SI, Codex's machine-permission report, from the TI table]. The same net drives the gate and the latch, so an interruption that can change an output always sets the latch.
- **Filter values [REQ].** Presence, PGOOD and tamper terms: reject every pulse < 5 µs, accept every pulse ≥ 30 µs over tolerance (this also satisfies the record's tamper-filter rule, §7.3.1, and is consistent with the FPGA's 30–40 µs status filter). TX_PERMIT and OUT_PERMIT at each receiving card: reject < 0.5 µs, accept ≥ 2 µs. All to be shown by glitch injection (section 14).
- **FPGA reaction.** While the FPGA holds a domain armed, OPI_OK_TX/A/B/BOE low latches `OUTPUT_PATH_INTERRUPTED` (new fault bit), disarms all channels (all-or-nothing rule unchanged) and clears `pos_continuity` for every channel in that domain (TX domain: all channels; BOE and B: channels 8–11). OPI_OK_OUT low while I/O is enabled latches `OUTPUT_PERMIT_LOST` and disables I/O. No filter is applied to OPI_OK: it only changes on a real gate transition.
- **Proof test on every disarm.** A commanded DISARM must make OPI_OK_x fall within 10 µs [REQ] of the FPGA dropping its request. If it does not, the FPGA latches `PERMISSION_PATH_STUCK` and refuses the next ARM. This checks the hardware gate path on every arm/disarm cycle, not only at commissioning.
- **Clean commanded stop.** On a commanded DISARM the FPGA stops issuing new STEP pulses, lets the current pulse finish its configured high and low times and DIR hold, then drops the request. `pos_continuity` stays set. On any fault the gate drops at once and continuity is cleared. This replaces the historical combinational `step_out & motion_enable` gating [SI, `gateware/rtl/cnc_endpoint.v` lines 104–108], which can truncate a pulse without recording it.
- **`pos_continuity` (per channel, sticky).** Set by the host's CLEAR_CONTINUITY request, accepted only while disarmed and only after the host reports a completed re-reference for that channel. Cleared by: OPI on the channel's domain while armed; any fault disarm while the channel is armed; STEP_TIMING on the channel; FPGA reset or reconfiguration (resets to 0); installed-mask change. It is carried in every status frame.
- **Position validity is higher level.** The host's position-valid state for a joint = homed AND `pos_continuity` of every channel of the joint AND (no enable drop since homing OR the profile declares and commissioning verified that the axis holds position unpowered). The driver drives `halui.joint.J.unhome` [SI, LinuxCNC 2.9 halui man page] for every joint J that contains the channel (joint index from the profile's channel-to-joint map, never the channel number) when it becomes false, and the generated INI sets `VOLATILE_HOME = 1` on every joint (unhomed on machine OFF [SI, ini-homing doc]).

## 5. External watchdogs

### 5.1 Parts and timing

Two identical, independent watchdogs on the motion card:

| | Motion watchdog (WD_M) | Output watchdog (WD_O) |
|---|---|---|
| Part | TI **TPS3851G18SDRBT** [DDR: active, standard timing, G18 threshold used only as a supply-present check on IO_3V3] | same |
| Timing capacitor | **3.3 nF C0G ±5 %, Samsung CL10C332JB8NNNC** (0603, 50 V, mass production) [DS, Samsung product page] | same |
| Timeout min/nom/max | **9.26 / 11.04 / 13.02 ms** [DDR, AR: tWD = 3.23 × C[nF] + 0.381 ms, TI factors 0.905×/1.095×, capacitor ±5 % gives 9.51 / 12.67 ms; the CWD leakage allowance of ±10 nA against the 375 nA charge current [DDR] multiplies by 375/385 and 375/365] | same |
| CWD node requirement | Guard ring around the CWD node to the device ground reference, no-clean flux residue removed, no conformal coating bridging the node; Codex states the leakage budget at 55 °C and 85 % RH [REQ] | same |
| WDI source | `progress_m`: one pulse per accepted ARM or UPDATE | `progress_o`: one pulse per accepted full-I/O exchange (armed or not) |
| SET1 | FPGA_MOTION_REQUEST, 100 kΩ pull-down | FPGA_OUTPUT_REQUEST, 100 kΩ pull-down |
| Gates | TX_PERMIT (motion, PWM/process via PROC_PERMIT) | OUT_PERMIT (general DO, PWM, AO, process) |

**Relation to the user's recorded candidate.** PROJECT_MEMORY and the task brief record TPS3851G18SDRBT with a 4.7 nF C0G capacitor (CL10C472JB8NNNC, 13.40/15.56/17.87 ms) as the verified candidate for the retained 20 ms requirement. IS-1 keeps that part and the 20 ms requirement and changes only the capacitor: with the normally-closed enable switch required by correction (4) the 4.7 nF design gives 17.87 + 4.31 = 22.18 ms, which fails 20 ms (more with leakage); 3.3 nF gives 12.67 + 4.31 = 16.98 ms from capacitor and IC tolerances and **17.33 ms** with the leakage allowance [AR]. The 20 ms limit is the requirement; the capacitor is the engineering choice that meets it.

**Gateware change adopted (recommendation made and taken under the user's authority):** `progress_wdi` changes from "toggle on each accepted UPDATE" to **one 1 µs high pulse (50 core ticks) per accepted ARM or UPDATE**, idle low. The TPS3851 restarts on a falling edge only [DDR], so the old toggle produced a falling edge every second UPDATE and legal traffic could space edges almost 10 ms apart, which forced tWD(min) > 10 ms and the 4.7 nF capacitor. With one falling edge per accepted command, the largest legal spacing is below the FPGA's own 5 ms command watchdog, so tWD(min) > 5 ms suffices. 3.3 nF gives 9.26 ms minimum with leakage (85 % margin over 5 ms) and **20 − 13.02 = 6.98 ms** for everything downstream of WDO, against 2.13 ms (before leakage) with 4.7 nF [AR]. This matters because the normally-closed enable switch alone may need up to 3 ms to close [DS]; 4.7 nF could not meet 20 ms with it. The 1 µs pulse is 20× the TPS3851's 50 ns minimum WDI pulse [DDR]. Codex's drawn TPS3431 (≈57.7–71.9 ms) is superseded for this function; the 20 ms requirement is not relaxed.

### 5.2 Wiring (requirement on Codex's machine-permission sheet)

- WDO and RESET of each TPS3851 are both open-drain and are **wired-AND onto one node** with one 10 kΩ pull-up to IO_3V3, then a Schmitt buffer: `WD_x_OK = WDO AND RESET`. During the 170–230 ms power-up reset WDO is high-impedance and would read "OK" [DDR]; the wired-AND makes the node read "not OK" then. This is the "RESET qualifies permission" rule.
- WDO is a 170–230 ms pulse, not a latch [DDR]. **Latching is done by the arm latches**: WD_M_OK is a term of `latch_clear_n` (arm_latch_M) and WD_O_OK of `latch_clear_O_n` (arm_latch_O, section 6.2), so any WDO or RESET low clears the arm latch asynchronously and permission stays off until a new, deliberate rising request (after SYNC and ARM, or IO_ENABLE). When the WDO pulse ends nothing comes back by itself: with the FPGA clock stalled the request stays high but no new rising edge ever clocks the latch, so OUT_PERMIT, the PWM buffers and the AO clamp stay inhibited.
- WDI is driven through the existing buffered-WDI arrangement (Codex: SN74LVC1G34 with 100 kΩ pull-down) so the 0.8 × VDD input threshold is met [SI].
- MR is left open (internal pull-up) or taken to a factory test pad; never to a customer terminal.
- **Watchdog trip record:** a sticky flip-flop per watchdog (SN74LVC2G74DCUR, second half of an OPI package where layout allows) set asynchronously when WD_x_OK falls while SET1 is high, read by the FPGA, cleared by the FPGA after the host has stored the event. Because SET1 is low while disarmed, the watchdog does not cycle while idle, so every recorded trip is a real one.

### 5.3 Arming sequence with SET1 on the request

SYNC → ARM accepted → FPGA raises FPGA_MOTION_REQUEST (arm latch set, SET1 high) → 150 µs SET1 set-up, WDI ignored [DDR] → timer running → first UPDATE 1 ms later (≤ 2.5 ms at the driver's slowest allowed period) delivers the first falling edge, well inside 9.26 ms [AR].

Hazard of the SET1 choice: a SET1 pin stuck low would disable the watchdog while the request is high. It is covered by the self-test in 5.4, run at every power-up and after any motion-card replacement.

### 5.4 Watchdog self-test (hardware-backed, before every first ARM)

The FPGA enters its SELFTEST state (opcode SELFTEST, section 01; the two tests run one after the other, never together). **WD_M test:** every EN_N_i forced high (LEDs dark), all rates zero, STEP/DIR idle, PEN/PWM/AO requests zero and **PERMIT_OUT_REQ low**; the FPGA raises FPGA_MOTION_REQUEST with progress pulses suppressed and timestamps the fall of WD_M_OK. **WD_O test:** PWM pins driven low, AO commanded zero, OUT_REQ zero in every IOL1 frame (so every card keeps CARD_EN and its OUT_EN latch low) and PERMIT_OUT_REQ low; the FPGA raises FPGA_OUTPUT_REQUEST and times the fall of WD_O_OK. Pass window: **9.06–13.37 ms** after the request edge [AR: tWD(min) − 0.2 ms, tWD(max) + 0.15 ms set-up + 0.2 ms, with the leakage allowance]. Outside the window, or no fall at all, latches WATCHDOG_SELFTEST_FAILED and ARM is refused. After each test WDO completes its 170–230 ms pulse; ARM waits for WD_x_OK to recover. During the WD_M test TX_PERMIT is high for about 10 ms, but nothing reaches the field: no enable (EN_N_i high, LED strings dark, NO open, NC closed), no STEP edge, no process contact (PROC_PERMIT stays low because OUT_PERMIT is low and PEN requests are zero), and **PERMIT_OUT stays open** because its LED drive is TX_PERMIT AND PERMIT_OUT_REQ (section 6.2), so the machine's contactor or STO request chain is never pulsed. The containment rows of section 13 and the glitch tests of section 14 check this at every power-up.

### 5.5 Fault-to-inhibit budget, clock-stall path (the tightest path)

| Stage | Allocation [REQ] | Basis | Status |
|---|---:|---|---|
| Last WDI falling edge to WDO low | 13.02 ms | tWD(max) with the CWD leakage allowance [DDR][AR] | datasheet-derived |
| WDO/RESET node fall to Schmitt output | 0.001 ms | open-drain sink, 10 kΩ pull-up | [ME] |
| Arm-latch clear and final AND to TX_PERMIT low | 0.001 ms | LVC logic | [ME] |
| TX_PERMIT across the motion-card connector, card RC filter and Schmitt | 0.005 ms | ≥ 2 µs acceptance filter | [ME] |
| AM26C31 outputs to high impedance | 0.001 ms | ns-class disable time [DS order of magnitude; exact figure at schematic] | [ME] |
| TPS22918 off and LED current below 0.1 mA | 0.30 ms | quick output discharge sizing (Codex) | [ME] |
| Form A opens | 0.20 ms | tOFF max, 25 °C [DS] | [ME over temperature] |
| Form B closes | 4.00 ms | max(tON, tOFF) = 3 ms at 25 °C [DS] + 1 ms temperature/ageing allowance (curves are not guaranteed) | [ME over temperature] |
| **Total, motion outputs** | **≤ 17.33 ms** | 13.02 + 4.31 [AR]; the two switches act in parallel, so only the slower (form B, 4.00 ms) is added to the 0.308 ms common path | against 20 ms: 2.67 ms unallocated margin |
| Output path: WD_O to OUT_PERMIT low, then driver disable | 13.02 + 1.00 ms | TPS274C65ASRHAR DO_EN (T1 selection, section 02 section 11.2); DO_EN-to-output-off time inside the 1.00 ms allocation is [ME] | **≤ 14.02 ms** |

Other paths are faster (section 7.2). If a measurement exceeds an allocation, the design changes; no allocation or limit is raised.

## 6. Permission chain

### 6.1 Terms and their physical sources

| Term | Physical source | Where |
|---|---|---|
| RAILS_OK | TPS386000 rail supervisor reset outputs (IO_3V3, CORE_1V2, CORE_5V/MOTION_5V) combined into FPGA_LOCAL_RESET_N and the power-sequence reset | power module → motion card |
| CONFIG_VALID | FPGA CDONE (bitstream loaded) in hardware; `config_valid` (accepted CONFIGURE) inside the FPGA, which gates FPGA_MOTION_REQUEST | motion card |
| EXTERNAL_PERMIT | Safety-chain status input XS1.2 through its ISO1212 channel → EXT_PERMIT_3V3, fixed assignment, never reconfigurable by CLI/profile; 10 kΩ pull-down at the motion-card receiver | DIC (XS1 safety interface) → motion card, hard-wired |
| DIC_OK | Qualified DIC presence A AND presence B AND DIC power-good (5 µs / 30 µs filter), so an absent, unseated or unpowered DIC removes permission even if the permit line floats | DIC → base → motion card |
| HW_WATCHDOG_OK | WD_M_OK (motion) and WD_O_OK (outputs), section 5 | motion card |
| FPGA_ARM_LATCH | Arm latch (SN74LVC2G74) clocked by the rising request, cleared by `latch_clear_n` | motion card |
| MODULE_OK | For each card: qualified presence (both pins), identity class latched by the FPGA, card power-good, NOT tamper | each card; tamper latches on the power module |
| PROCESS_PERMIT_EXT | Dedicated process-enable interlock input XS1.3, fixed assignment; it gates only the two process-enable contacts XPC0/XPC1 (torch, laser, or a spindle run/STO input deliberately wired through XPC0), never the DO/AO/PWM outputs; 10 kΩ pull-down at the motion-card receiver | DIC (XS1 safety interface) → motion card, hard-wired |

### 6.2 Equations (normative logic; gate choice is Codex's)

```text
DIC_OK          = filtered(DIC_PRESENT_A AND DIC_PRESENT_B AND DIC_PGOOD)
base_ok         = RAILS_OK AND CDONE AND DIC_OK AND EXT_PERMIT_3V3 AND NOT TAMPER_ANY
raw_inhibit_n   = base_ok AND WD_M_OK                      (to FPGA inhibit_n, never from TX_PERMIT)
latch_clear_n   = raw_inhibit_n AND FPGA_ENDPOINT_READY    (asynchronous clear of arm_latch_M)
TX_PERMIT       = arm_latch_M.Q AND FPGA_MOTION_REQUEST AND raw_inhibit_n

out_base_ok     = RAILS_OK AND CDONE AND DIC_OK AND EXT_PERMIT_3V3 AND NOT TAMPER_ANY
latch_clear_O_n = out_base_ok AND WD_O_OK AND FPGA_ENDPOINT_READY   (asynchronous clear of arm_latch_O)
OUT_PERMIT      = arm_latch_O.Q AND FPGA_OUTPUT_REQUEST AND out_base_ok AND WD_O_OK
PROC_PERMIT     = OUT_PERMIT AND TX_PERMIT AND PROCESS_PERMIT_EXT_3V3
PERMIT_OUT_DRIVE = TX_PERMIT AND PERMIT_OUT_REQ              (LED of the XS1.10-11 photorelay)

OPI_OK_TX  cleared by TX_PERMIT;  OPI_OK_OUT cleared by OUT_PERMIT;  OPI_OK_BOE cleared by the qualified
bank-B OE net (all on the motion card); OPI_OK_A / OPI_OK_B cleared by the qualified card nets

per card:  TX_PERMIT_A = filtered(TX_PERMIT) AND PRESENT_A_OK AND PGOOD_A      (bank-A card)
           TX_PERMIT_B = Ioff-buffer copy of TX_PERMIT, OE = filtered(PRESENT_A_B AND PRESENT_B_B
                         AND EXP_PGOOD AND NOT TAMPER)                           (MX4)
           OUT_PERMIT_k = filtered(OUT_PERMIT) AND card k presence/PGOOD         (each DO/PWM/AO card)
           output enable = OUT_PERMIT_k AND OUT_EN_latch.Q AND CARD_EN          (OUT_EN CLR_N = OUT_PERMIT_k)
```

- Each arm latch has an asynchronous clear containing its own watchdog and base terms (`latch_clear_n` ⊇ {base_ok, WD_M_OK}; `latch_clear_O_n` ⊇ {out_base_ok, WD_O_OK}); `tools/interface_spec_validate.py` checks this. A WDO pulse therefore clears its latch, and permission returns only on a new deliberate request edge.
- `FPGA_MOTION_REQUEST` is high only when armed with a valid CONFIGURE, the required mask equal to the armed mask, and no fault, **or** in the SELFTEST state of the WD_M test, with EN_N_i forced high, rates zero, process requests zero and PERMIT_OUT_REQ low (section 5.4).
- `FPGA_OUTPUT_REQUEST` is high when the host has an I/O session (independent of motion arming), config valid and no output-domain fault, **or** in the SELFTEST state of the WD_O test, with PWM pins low, AO commanded zero and OUT_REQ zero so every card enable stays low. General outputs are therefore usable while motion is disarmed (commissioning output tests, lights, air) and are still covered by an independent watchdog.
- `PERMIT_OUT_REQ` (FPGA pin, 10 kΩ pull-down) is high only while armed and never in SELFTEST.
- TX_PERMIT must never feed the endpoint inhibit input (arm/progress loop) [SI, Codex report]. Unchanged.
- Placement: WD_M, WD_O, both arm latches, the OPI_TX, OPI_BOE and OPI_OUT latches, the PERMIT_OUT_REQ gate, the DIC_OK filter and the final gates are **on the motion card**, beside the FPGA they supervise, so a motion-card swap replaces and re-tests them together (5.4). The tamper latches are on the **power module**, which owns logic power-on reset, so only a power cycle clears them.

### 6.3 Fan-out and defaults (requirement)

| Net | Receivers | Default with driver absent |
|---|---|---|
| TX_PERMIT | Bank-A card receiver (→ 4 AM26C31 G, TPS22918 EN, OPI_A), MX4 path through the Ioff buffer on the motion card (→ TX_PERMIT_B → 2 AM26C31 G, TPS22918 EN, OPI_B; the qualified OE also clears OPI_BOE; section 02 D02-5), PROC_PERMIT gate, PERMIT_OUT photorelay driver gated by PERMIT_OUT_REQ on the motion card (→ DIC, XS1.10–11; section 03 D03-11) | 10 kΩ pull-down at the motion-card output, on the base, and at every receiver |
| OUT_PERMIT | Each DO card through its OUT_EN latch, PWM buffer OE and analog-output zero clamp through the ACC OUT_EN latch, PROC_PERMIT gate, OPI_OUT | same; each card's OUT_EN latch is cleared while its OUT_PERMIT_k is low |
| PROC_PERMIT | Two process-enable switches through the ACC PEN latch | same |
| EXT_PERMIT_3V3 (from DIC XS1.2) | base_ok, out_base_ok, FPGA status | **10 kΩ pull-down at the motion-card receiver**: an absent, unseated or unpowered DIC reads "not permitted"; DIC_OK removes permission as well |
| PROCESS_PERMIT_EXT_3V3 (from DIC XS1.3) | PROC_PERMIT gate, FPGA status | **10 kΩ pull-down at the motion-card receiver** |
| DIC_OK | base_ok, out_base_ok | presence lines pulled to "absent" and PGOOD pulled low on the motion card |
| PERMIT_OUT_REQ, FPGA_MOTION_REQUEST, FPGA_OUTPUT_REQUEST | PERMIT_OUT gate; SET1 and arm latches | 10 kΩ / 100 kΩ pull-downs: an unconfigured FPGA requests nothing |

**Self-test containment [REQ].** No TX_PERMIT or OUT_PERMIT receiver can close a field contact or energize an output during SELFTEST: enable photorelays stay dark (EN_N_i high), PERMIT_OUT stays open (PERMIT_OUT_REQ low), process contacts stay open (PROC_PERMIT low and PEN requests zero; the two tests never overlap), DO cards keep CARD_EN and OUT_EN low, PWM pins are low and AO is commanded zero. `safety.json` lists each receiver with the term that holds it off (`permission.selftest_containment`), and the validator refuses a field-contact receiver without one.

The motion card drives only Schmitt receiver inputs on each card. Codex re-runs the permission validator for the IS-1 fanout (the six-G-input sizing no longer applies) [REQ].

Serial I/O cards: OUT_PERMIT is a **hardwired** line to every output card and gates the output drivers directly. It never travels inside the serial link. The card's own watchdog (advancing only on fully accepted transactions: identity, sequence/freshness and CRC validated before any output changes) de-energizes that card's outputs on expiry; its timeout is ≥ 3 link periods and ≤ 2 ms [REQ]. The link is IOL1 (section 01 section 4): a 1.0 ms accept timer and a hardware-started IWDG ≤ 2 ms, both refreshed only by fully accepted frames, and every output enable = OUT_PERMIT_k AND CARD_EN.

## 7. Fault detected, outputs inhibited, machine stopped

### 7.1 Definitions (three separate measurements, never merged)

| Quantity | Starts | Ends |
|---|---|---|
| t_detect | Injection instant t0 | First recorded detection: FPGA fault bit timestamp, WDO fall, supervisor reset, card watchdog expiry, host log entry |
| **t_inhibit** (the 20 ms quantity) | t0 | The **last** of: TX_PERMIT low at every card gate net; every STEP/DIR pair high-impedance at the terminal (|VOD| < 0.2 V into the drive's input); every EN_NO open (≤ 1 µA at 24 V test load) and every EN_NC closed (loop current flowing through a 1 kΩ test load); every general output off (load current < 1 mA into its declared test load); PWM low; process switches open; analog outputs ≤ 0.1 V; the last STEP edge |
| t_stop | t0 | Machine behaviour: last motor step, drive-disabled indication, holding or free-wheel, brake engagement, position loss against encoders, and confirmation that nothing restarts by itself. Machine-specific; not bounded by the controller |

### 7.2 Response per scenario (allocations [REQ]; every entry needs [ME])

| Scenario | Detection | Inhibit path | t_inhibit bound (allocation) |
|---|---|---|---|
| Startup | — | Outputs held inhibited from power-on (CDONE low, RESET low, SET1 low, pull-downs) until a deliberate ARM after self-test | No output activity at any time before ARM |
| Host failure (LinuxCNC killed, kernel panic, compute power lost) | FPGA 5 ms command watchdog | FPGA disarm → request low → TX_PERMIT low | ≤ 5.00 + 4.31 = 9.31 ms from the last accepted UPDATE |
| Broken or stale communication (CRC, length, replay, sequence) | At the rejected frame | Immediate disarm | ≤ 0.28 (longest frame, CS_FB at 5 MHz) + 4.31 = 4.59 ms |
| Link wires open or CS stuck | No accepted frames | FPGA 5 ms watchdog | ≤ 9.31 ms |
| FPGA reset or reconfiguration | FPGA_LOCAL_RESET_N / CDONE low | base_ok false in hardware | ≤ 4.31 ms from reset assertion |
| FPGA clock stall | WD_M (and WD_O) | Section 5.5 | ≤ 17.33 ms (motion), ≤ 14.02 ms (outputs) |
| Logic power disturbance | TPS386000 reset | RAILS_OK false | ≤ 0.05 + 4.31 = 4.36 ms; the TPS386000 datasheet (SBVS105F, table 6.6) gives a 4 µs minimum detectable SENSE pulse and no maximum assertion delay, so 0.05 ms is an allocation to be measured [DS][REQ] |
| Field power loss | F_PGOOD, AUX24_OK, AUX5_OK low; outputs lose supply | FPGA fault; outputs de-energize physically | ≤ 0.04 + 4.31 ms after the monitor threshold |
| Module presence/PGOOD change under power (unsupported) | Qualified term → OE drop, tamper | Hardware, then FPGA OPI and EXPANSION_CHANGED | ≤ 0.03 + 4.31 ms; recovery needs a power cycle |
| Drive alarm on an armed channel | 30–40 µs filter | FPGA disarm | ≤ 0.04 + 4.31 ms |
| External permit (safety chain) opened | ISO1212 + input filter | Hardware base_ok | ≤ 1.00 (input filter allocation) + 4.31 ms |
| DIC removed, unseated or unpowered | EXT_PERMIT_3V3 pull-down, DIC_OK | Hardware base_ok | ≤ 0.03 + 4.31 = 4.34 ms |
| Output short or overload | Output driver protection (autonomous) | Driver current limit acts at once; the card forces the output off after ≤ 0.40 ms (fault poll 100 µs + response 140.4 µs + command 140.4 µs + apply 20 µs [AR on REQ]); bank and entry limits in section 10 | ≤ 1.00 ms allocation [REQ]; the driver's own current-limit response is measured on the built card [ME] |
| OUT_PERMIT glitch accepted by an output card | Card OUT_EN latch, OPI_OUT | Outputs off and held off until IO_ENABLE | ≤ 0.002 + 1.00 ms (DO_EN allocation) |

## 8. Safety status carried every servo cycle (T2)

This section fixes their meaning; section 01 places them: the safety and power word is CNF3 bytes 164–167 and CNS3 bytes 30–33 (bits 0–27, section 01 section 3.10), the added fault bits are fault-word bits 9–12 (bits 13–24 are section 01's), and `pos_continuity` is CNF3/CNS3 bytes 34–35. Each is sampled at the FPGA snapshot and is valid for that snapshot only.

| Field | Physical source | Fault response | HAL pin | Service name |
|---|---|---|---|---|
| `tx_permit`, `out_permit`, `proc_permit` | Readback of the final gate nets | Mismatch with FPGA request ⇒ PERMISSION_PATH_STUCK | `cnc1.safety.tx-permit`, `.out-permit`, `.proc-permit` | `safety.permit.{tx,out,proc}` |
| `wd_m_ok`, `wd_o_ok`, `wd_m_tripped`, `wd_o_tripped` | Section 5.2 nodes and sticky flops | Trip ⇒ fault already latched in hardware; record | `cnc1.safety.wd-motion-ok`, `.wd-output-ok`, `.wd-motion-tripped`, `.wd-output-tripped` | `safety.watchdog.{motion,output}` |
| `opi_ok[TX,A,B,BOE,OUT]` | OPI latches | TX/A/B/BOE low while armed ⇒ OUTPUT_PATH_INTERRUPTED; OUT low while I/O enabled ⇒ OUTPUT_PERMIT_LOST | `cnc1.safety.opi-ok-tx`, `-a`, `-b`, `-boe`, `-out` | `safety.opi.{tx,a,b,boe,out}` |
| `reset_arm`, `reset_arm_ready`, `contactor_fb`, `sto_fb`, `chain_status` | XS1.4–XS1.8 ISO1212 inputs; FPGA reset/arm qualifier | CONTACTOR_FEEDBACK, STO_FEEDBACK, ARM_REFUSED, SAFETY_INTERFACE events (section 8.1) | `cnc1.safety.reset-arm`, `-ready`, `.contactor-fb`, `.sto-fb`, `.chain-status` | `safety.interface.*` |
| `pos_continuity[0..11]` | FPGA per-channel sticky | Clear ⇒ position invalid; `halui.joint.J.unhome` for every joint J containing the channel | `cnc1.N.position-continuity` | `motion.channel[N].continuity` |
| `ext_permit`, `process_permit_ext` | ISO1212 outputs | Low ⇒ inhibit (hardware) | `cnc1.safety.ext-permit`, `.process-permit` | `safety.input.{ext,process}` |
| `aux24_ok[A,B]`, `aux5_ok[A,B]` | Per-bank supply monitors | Low ⇒ ARM refused, fault if armed | `cnc1.safety.aux24-ok-a` … | `power.aux.{24,5}.{a,b}` |
| `f_pgood[A,B]`, `motion5v_pgood`, `exp_pgood` | Entry and rail power-good | Low ⇒ fault, disarm | `cnc1.power.field-a-ok` … | `power.rail.*` |
| `selftest_state` | FPGA | Fail ⇒ ARM refused | `cnc1.safety.selftest-ok` | `safety.selftest` |
| Fault word (existing bits plus OUTPUT_PATH_INTERRUPTED, PERMISSION_PATH_STUCK, WATCHDOG_SELFTEST_FAILED, AUX_SUPPLY_FAULT, CONTACTOR_FEEDBACK, STO_FEEDBACK, ARM_REFUSED) | FPGA | Latched; SYNC clears only the clearable bits | `cnc1.fault`, `cnc1.fault-word` | `safety.fault` |

### 8.1 Safety-interface behaviour (normative; section 01 section 3.4a has the fields)

| Input | Expected state and timing | Mismatch |
|---|---|---|
| CONTACTOR_FB (XS1.7), mode 1 NO auxiliary or 2 NC mirror | De-energized at ARM; energized within `contactor_close_ms` after TX_PERMIT (and so PERMIT_OUT) closes; de-energized within `contactor_open_ms` after it opens | CONTACTOR_FEEDBACK: disarm all, ARM refused until SYNC with the input agreeing |
| STO_FB (XS1.8), mode 1 follows PERMIT_OUT, mode 2 status only | Mode 1: STO active exactly while PERMIT_OUT is open, within `sto_response_ms`; mode 2: STO active while armed is a fault | STO_FEEDBACK: disarm all, ARM refused |
| RESET_ARM (XS1.5) | ARM accepted only within `reset_arm_window_ms` after a qualified release while EXT_PERMIT is high (default required; a software-only ARM is allowed only when the machine's own safety relay has a manual reset feeding EXT_PERMIT, recorded in the profile) | ARM_REFUSED; a press longer than `reset_arm_press_max_ms` is reported as stuck |
| SAFETY_STATUS (XS1.4) | Diagnostic; agrees with EXT_PERMIT | Event after `chain_mismatch_ms`, no fault |

Generated machine-enable chain: `iocontrol.0.emc-enable-in` = ext-permit AND NOT `cnc1.fault` AND `cnc1.din-valid` (when any DI serves a machine function); the reset/arm release drives `halui.machine.on`, and the ARM that follows must arrive inside the window (section 01 section 7.2).

## 9. Fault state per output function (not "everything off")

Hardware can only guarantee **de-energized** when permission falls. The configuration validator therefore checks every function against this table and refuses a mapping that relies on an output staying energized through a controller fault.

| Function | Output state on OUT_PERMIT/PROC_PERMIT loss | Requirement on the machine and profile |
|---|---|---|
| Motor brake release (gravity axis) | De-energized: brake engages | Spring-applied brake only. On hardware inhibit the drive enable and brake release drop together, so the axis can move by the brake's engagement time. Commissioning measures the drop on inhibit and the profile records it; a drive with its own brake sequencing, or a counterbalance, is recommended for gravity axes |
| Workholding clamp, vise, vacuum | De-energized | Validator refuses an "energize-to-clamp" device on a controller output. Required: spring clamp (energize to release), bistable valve, or vacuum with a check valve/reservoir sized by the machine builder |
| Spindle run / direction | De-energized | Spindle decelerates by its own VFD behaviour (t_stop, machine-specific). Analog speed command clamped to 0 V. A spindle controlled over Modbus keeps a hardware run-enable DO (or an XPC0 contact) so this row holds; the validator refuses a bus-only run path. XS1.3 does not stop a spindle on DO/AO outputs |
| Process enable (torch, laser) | Open (PROC_PERMIT) | Process interlock chain required; never on a general output |
| PWM (laser power, fan speed, a spindle PWM input) | Low (buffer disabled, pull-down); held low by the ACC OUT_EN latch | The device must be off at a low input. IS-1 has no inverted PWM (CONFIGURE_IO page 1 flags are zero), so the validator refuses a device whose off state needs a high level or a running duty cycle |
| Coolant, air blast, mist | De-energized | None |
| Lubrication | De-energized | Pump may not run after-run; accessory after-run belongs to the ESP accessory owner with its own qualified hardware path |
| Dust extraction, cabinet fans, cooling | De-energized if on a controller output | After-run cooling that must continue through a controller fault is not placed on a gated output (ESP accessory contract or hardware thermostat) |
| Lights, indicators | De-energized | Machine lighting is recommended outside controller outputs |
| Toolchanger, drawbar | De-energized | Drawbar must be "energize to release"; the validator refuses the opposite |

Host-loss response (FPGA running, host gone) is the same as permission loss for every general output. There is no "hold last value" state in IS-1.

## 10. Power requirements for Codex

All figures are reservations [RES] or arithmetic [AR]; none is a measurement. Nothing here raises a component rating. The ledger's 18 V minimum input and 85 % converter efficiency are kept; Codex's r0.2 19 V study remains Codex's open item.

### 10.1 Logic rails

| Rail | Loads (normal reservation) | 8 motors | 12 motors + MX4 | Requirement |
|---|---|---:|---:|---|
| CORE_5V (compute and logic) | Compute 3.00; IO_3V3 input 0.52 (0.6 A at 3.3 V, raised from 0.4 for 36 ISO1212 channels, isolators, FRAM, EEPROMs, buffers, 2 × TPS3851); ESP_3V3 input 0.60; CORE_1V2 input 0.28; misc 0.10 | 4.50 A | 4.50 A | Keep the 6 A converter; transmitters and encoders move off this rail |
| MOTION_5V (new branch) | TX bank A 0.80; enable LEDs 0.0122 A per channel; 4 encoder ports 0.80 (0.20 each); MPG 0.10; frequency-input sensor 0.10; + TX bank B 0.40 via EXP_5V | 1.90 A | 2.35 A | Converter ≥ 3.0 A continuous; sum of branch current-limit maxima 2.78 A (encoders 0.284 A max each from Codex's encoder-power model, MPG and frequency limits ≤ 0.15 A max) must fit without tripping the converter |
| EXP_5V (MX4, from MOTION_5V) | TX bank B 0.40; bank-B LEDs 0.049 | — | 0.45 A | Switch limit minimum ≥ 0.60 A; real power-good (record §7.3.1) |
| Encoder expansion (reserved, 8 more ABZ ports) | 8 × 0.20 A at 5 V from the module's own converter | — | 1.60 A (fault max 2.27 A) | Fed from CORE_24V through an expansion power switch; fitted **at the same time as** MX4 |

CORE_24V input at 18 V and 85 % [AR]: CORE_5V 1.471 A; MOTION_5V 0.620 A (8 motors) or 0.767 A (12); analog (AO domains) 0.06 A; **ACC AI group 0.190 A** (RECOM REC3.5-2424SRW/R8/A, 18–36 V in, 24 V 145 mA, 84 % [DS: DigiKey listing]; 100 mA sensor supply at XAI.10 + 20 mA AI-side electronics: 0.12 A × 24 V / 0.84 / 18 V); encoder expansion 0.523 A.

| Configuration | CORE_24V input | Against today's ledger (2 A) and Codex r0.2 (3 A) |
|---|---:|---|
| 8 motors, 4 encoders | 2.34 A | Over the 2 A ledger capacity (as the record found); inside 3 A |
| 12 motors (MX4) | 2.49 A | Inside 3 A |
| 12 motors + 8-port encoder expansion | **3.01 A** | Above the 3 A r0.2 study: a 4 A-class entry is required |

**Requirement:** core entry current-limit minimum ≥ 1.2 × 3.01 = **3.61 A** at 18 V input, i.e. a 4 A-class core entry, fuse and connector, so that nobody has to choose between twelve motors and encoder feedback. The display is powered by its package, not by this entry.

### 10.2 Field entries and the 16 × 0.5 A outputs

Sixteen outputs at 0.5 A are 8.0 A (192 W at 24 V) against the 6 A single field entry [AR]. IS-1 does not reduce the outputs. It **splits the field supply into two entries**, each with its own physical fuse, reverse protection and eFuse, and publishes and enforces bank limits.

| Entry | Loads | Continuous | Single-fault containment requirement |
|---|---|---:|---|
| FIELD_A | DO0–DO7 (8 × 0.5 A); AUX_24V bank A 0.148 A and bank B 0.074 A (alarm 2.47 mA + 16 mA enable loop per channel); FIELD_5V input 0.096 A (0.242 A at 5 V: 0.05 isolation + 0.192 AUX_5V, 70 % assumed); 2 probe supplies 0.20 A; control 0.06 A | 4.58 A | Current-limit minimum ≥ 4.58 − 0.5 + 1.0 = 5.08 A |
| FIELD_B | DO8–DO15 (8 × 0.5 A); DI sensor groups 3 × 0.20 A; safety-interface branch 0.15 A (XS1.1); reset/arm lamp 0.05 A (XS1.6); control 0.02 A | 4.82 A | ≥ 4.82 − 0.5 + 1.0 = 5.32 A |

Every sourcing terminal limit is listed against its entry budget in `safety.json` (`power_requirements.terminal_supply_loads`: XS1.6 arm lamp, XS1.1 safety branch, XDI sensor groups, XPR probe supplies on FIELD_A, XAI.10 AI sensor supply on CORE_24V), and the validator checks that each one is inside its entry's load list and that the load lists sum to the stated totals.

- Published limits enforced in hardware: **0.5 A continuous per output**, output-driver current-limit maximum ≤ 1.0 A per channel [REQ to the output-driver selection]; **2.0 A continuous per 4-output bank**; entry limits above. One shorted output must never trip its entry.
- Enforced in software as well: the configuration validator refuses assignments whose declared load currents exceed a bank's 2.0 A or an entry's published total; the measured output currents (section 01 section 8.1) are compared against the declared loads, and a sustained excess is a fault on that bank.
- Each entry: fuse rating from the E-34 method (load/0.75, next rating: 7.5 A), 10 A-class wiring, entry connector and mating plug [REQ]; TVS clamping coordinated with the selected output driver. The TPS274C65ASRHAR is rated VS 40 V continuous and 60 V transient (< 1 ms, ON state) [DS]; the SMCJ30CA 48.4 V clamp [SI, POWER_ENTRY.md] is inside that transient rating only if the clamped surge lasts < 1 ms, and the OFF-state transient is not specified, so Codex confirms the clamp duration or lowers the clamp. (The earlier 48 V TPS4H160 defect no longer applies to the selected driver.)
- Clearing any field trip never restarts outputs; OUT_PERMIT needs a new deliberate output request.
- Coupling stated plainly: a FIELD_A trip removes AUX_24V/AUX_5V, so motion disarms fail-closed (alarms read asserted, AUX monitors fault). A FIELD_B trip affects outputs 8–15 and sensor supply only.

### 10.3 Enable, alarm and auxiliary supplies

| Supply | Per bank | Limit | Monitor |
|---|---|---|---|
| Enable LED supply (TPS22918 from MOTION_5V / EXP_5V) | A 8 × 12.2 = 97 mA; B 49 mA | Upstream branch | Implicit via OPI and self-test |
| AUX_24V (FIELD, alarm and 24 V enable loops) | A 0.148 A; B 0.074 A | Current limit min ≥ 1.1 × load, max ≤ 0.30 A (A) / 0.20 A (B); survives a sustained short | AUX24_OK_x to the FPGA |
| AUX_5V (FIELD domain, 5 V enable loops, DM542T) | A 8 × 16 mA = 128 mA; B 64 mA | Current limit per bank; independent of LOGIC rails; FIELD_5V resized to ≥ 0.30 A or a separate converter; setpoint 5.00 V ±1.5 %, limiter drop ≤ 0.05 V, distribution drop ≤ 0.05 V (section 3.2) | AUX5_OK_x to the FPGA, falling trip ≥ 4.80 V, so XMn.11 ≥ 4.75 V while OK |

AUX_5V must stay up when LOGIC power is lost (it is derived from FIELD_24V); that is what keeps disable-on-current drives disabled on controller logic power loss (3.3).

### 10.4 Thermal and connectors

- Rated internal ambient for the controller electronics in IS-1: 0–55 °C [REQ]. Every semiconductor keeps its junction at least 15 °C below its datasheet maximum with all 16 outputs at 0.5 A, all 12 motor channels at the 195,312.5 steps/s cap and all encoder ports at their reserved current [REQ; Codex calculates, measurement [ME] confirms].
- Every power contact on a board-to-board or field connector is rated ≥ 2× its continuous current at the rated ambient [REQ].
- The motion-card connector carries TX_PERMIT, OUT_PERMIT, PROC_PERMIT, EXT_PERMIT_3V3, PROCESS_PERMIT_EXT_3V3 and the qualified module terms with a ground next to each [REQ].

## 11. Service and recovery behaviour relevant to safety

- Power-off replacement only. The unit powers up disarmed with `config_valid` = 0, `pos_continuity` = 0 on every channel, both self-tests pending.
- The service procedure starts by switching off the machine main disconnect / drive power, and the service screen asks for that confirmation before it shows any card-removal step (exceptions E1 and E2); then controller power and both field entries go off and the operator waits for the PSM 'safe' LED, or a fixed 60 s when the LED stays dark or the PSM is the failed card (section 02 section 13).
- After any replacement: self-tests (5.4), identity check, compatible configuration restore through the configuration service, then the affected checks: for a motor-interface card or MX4, per channel "disarmed ⇒ drive disabled" (E3), ENA voltage ≥ 4.60 V on NC-5V channels, alarm polarity, enable, and a direction check — a channel outside any gantry group jogs alone at low rate, while the channels of a gantry group are homed with their shared negative HOME_SEQUENCE and jogged together as one axis, never one joint alone; for the motion card, all channels plus both watchdog self-tests (PERMIT_OUT stays open) and OPI proof tests; rehoming is always required and timed separately from commissioning.
- Nothing resumes automatically. Stale commands are rejected by session and sequence rules; no armed or homed state is stored.

## 12. Diagnostic evidence chain

### 12.1 Measured facts and diagnoses are different record types

| | Fact | Diagnosis |
|---|---|---|
| Content | One measured value or state from a named physical source | A hypothesis explaining facts, and a suggested next test |
| Required fields | `fact_id`, physical source, transport field, sample timestamp (FPGA ticks + boot ID, wall clock if set), value, unit, validity (`valid`, `stale`, `unavailable`, `out_of_range`), data age at display, measurement range, accuracy class and the load range over which it was verified | `diagnosis_id`, text, `supporting_fact_ids` (≥ 1), `contradicting_fact_ids`, author (`rule:<id>` or `ai:<model/version>`), `next_test` |
| Rendering | Value with unit, age and validity; unavailable or stale is shown as such, **never as zero** | Visually distinct ("possible cause"), linked to its facts |
| Validation | Produced only by drivers and the diagnostics service | Rejected if it cites a fact ID that does not exist, or contains a number that is not in a cited fact |

Example: fact "output 7 overcurrent, 1.9 A, 12:03:04.118, valid, age 2 ms"; diagnosis "probably a damaged valve cable (supports: fact 812, 813); next test: disconnect the valve and energize output 7 from the service screen". The AI may produce diagnoses and next tests; it never produces facts.

### 12.2 Timestamped fault history ring

- **Trigger:** any latched fault, watchdog trip, OPI event, supply fault, card watchdog expiry or module change.
- **Contents per snapshot:** 2 s before and 2 s after the trigger: commanded rates and emitted counts per channel, enable and alarm states, permission nets, supply monitors, per-output state and current with validity, module presence/identity/PGOOD, communication error counters (CRC, length, sequence, timeout, serial-card rejects), temperatures, and the fault word.
- **Two layers:** (1) FPGA hardware event ring in block RAM, last 256 events with 50 MHz timestamps, readable after a host crash if the FPGA kept power; (2) persistent ring on a dedicated **Infineon FM24V02A-G** (256 Kbit I2C F-RAM, SOIC-8, 10¹⁴ write endurance, writes at bus speed, 2.0–3.6 V, −40 to 85 °C [DS]) in the machine cartridge, separate from the write-protected configuration memory, so the history stays with the machine through any module swap. Mirrored to host storage.
- **Power-loss tolerance:** the host writes 64-byte CRC-protected records continuously (20 Hz rolling summaries plus every event), so no final flush is needed; a torn last record is detected by its CRC and discarded. Capacity [AR]: 32,768 B / 64 B = 512 records; one 4 s snapshot ≈ 90 records ≈ 5.8 KB, so the F-RAM keeps the rolling ring plus the last 4 snapshots; the host mirror keeps at least 1,000 snapshots.
- **Offline:** recording, viewing and export need no internet or AI credit.

### 12.3 Hardware-backed diagnostics owned by this section

Watchdog self-tests, OPI proof test on every disarm, permission-net readback, AUX and entry monitors, watchdog trip flags, per-channel continuity. Every one has a physical source, a transport field and a response in section 8.

## 13. Protection and containment test matrix

"Expected containment" is a requirement [REQ]; each row becomes a pass/fail test on the first prototype [ME].

| Fault injected | Expected containment | Expected detection and record | Must not happen |
|---|---|---|---|
| One DO output shorted to 0 V | That output | Driver fault flag and current reading; output fault | Entry trip; other outputs in the bank dropping |
| One DO output shorted to +24 V (back-feed) | That output | Readback mismatch | Damage outside the output card |
| Bank load above 2.0 A (several outputs) | That bank | Measured current vs declared load; bank fault | Other entry affected |
| FIELD_A overload beyond the entry limit | FIELD_A | F_PGOOD_A; motion disarms fail-closed | FIELD_B, logic rails affected |
| AUX_24V shorted at one motor plug | That bank's alarm/enable supply | AUX24_OK_x; disarm | Other bank; FIELD entry trip |
| AUX_5V shorted at one motor plug | That bank's AUX_5V | AUX5_OK_x; ARM refused (exception E1 applies) | Other bank |
| 24 V applied to STEP+/DIR+ of one plug (miswire) | Motor-interface card | Channel fault on test | Damage to the motion card or FPGA |
| 60 V transient on EN_COM–EN_NC | Motor-interface card (TVS, photorelay) | Commissioning check fails for that channel | Damage to logic side (isolation) |
| Encoder supply short on one port | That port (limiter) | Port power-good; fault if the encoder belongs to an armed joint | Other encoder ports; MOTION_5V collapse |
| Encoder line open or shorted | That port | **Not detected electrically in IS-1**: the AM26LV32E fail-safe holds the output high, so the other line toggling gives a legal back-and-forth count. Found as following error where the loop closes on the encoder, as step/encoder disagreement in the preview (section 05), and by the commissioning count check | Other ports |
| Watchdog self-tests (WD_M, then WD_O) | No field effect | Self-test result bits | PERMIT_OUT closing (meter on XS1.10–11), any enable, STEP edge, process contact, DO, PWM or AO change |
| OUT_PERMIT pulse accepted by one output card | That card's outputs off until IO_ENABLE | OPI_OUT, OUTPUT_PERMIT_LOST, card OUT_EN flag | Outputs turning back on by themselves |
| DIC removed, unseated or unpowered | Whole machine inhibited | DIC_OK, slot status register, SLOT_FAULT | Any permission while EXT_PERMIT has no driver |
| EXP_5V short on MX4 | MX4 | EXP_PGOOD, tamper; whole machine inhibited (U8) | Base damage |
| Motion card removed under power (unsupported) | Whole machine inhibited | Tamper; power cycle required | Any output activity |
| Motion-card clock stopped | Whole machine inhibited | WD_M and WD_O trip, sticky flags | t_inhibit > 20 ms |
| Serial I/O card link corrupted | That card's outputs off | Card rejects; FPGA error counters | Output change on a frame that failed validation |
| Serial I/O card logic clock stopped | That card | FPGA readback timeout → output request dropped | Other cards |
| Cartridge I2C bus shorted | Configuration writes blocked | Bus timeout record | Motion or I/O effect |
| ESP crash or power loss | Diagnostics service | Missing heartbeat record | Any output or motion effect |
| Compute module power loss | Host | FPGA watchdog | t_inhibit > 9.31 ms |

## 14. 72-hour combined-load test and fault-injection acceptance

**Prerequisites.** Built motion card, bank-A card, MX4, encoder expansion, DO/DI/analog cards and fixed base of one revision; target compute module; IS-1 gateware, driver and service. None exists today (section 16).

**Load (all at once, for 72 h):**
- 12 motor channels stepping continuously on a profile mix (constant rate at the cap into passive receivers, drive-rated rates into 8 DM542T V4 drives with unloaded motors, and reversals), gantry pairs across bank A/bank B.
- 4 base + 8 expansion encoder ports from quadrature generators at stepped rates up to the port target; index pulses.
- All 24 DI toggled by a pattern generator at their maximum rate with minimum-width pulses; 2 probes triggered at known count positions; 2 frequency inputs at their qualification frequency.
- All 16 DO switching resistive and inductive test loads at declared currents up to the 2.0 A bank limit; 2 PWM at published frequency/resolution pairs; 2 AO looped back to 2 AI; process switches cycled into test loads.
- RS-485 and CAN at maximum traffic; ESP UART at its maximum message rate with Wi-Fi/BLE active.
- Touchscreen UI with the 3D preview animating; sustained network throughput with file transfer to storage; configuration export/import cycles.

**Instruments.** Independent pulse counters on all 12 STEP outputs at the drive end; logic analyser (≥ 200 MS/s) on CS, SCLK, MOSI, MISO, a thread-start GPIO, progress pulses, TX_PERMIT, OUT_PERMIT, WDO, CDONE; current probes on the core and both field entries; thermocouples on the output drivers, AM26C31s, photorelays and FPGA; supply-dip generator.

**Pass criteria for the 72 h run** (≈ 259.2 million servo cycles [AR]):
- zero unexplained resets, faults or disarms;
- zero servo deadline overruns (1 ms);
- zero pulse-count discrepancies between each independent counter and the FPGA emitted count;
- zero encoder count discrepancies against the generators;
- zero unexplained communication errors (every counted error traced to an injection);
- no temperature above the section 10.4 limits;
- 700 µs cycle completion reported as a distribution (maximum, 99.9999th percentile); exceeding it is a recorded engineering finding, not a pass/fail safety criterion.

**Fault injection (after the 72 h run, under the same load).** Every scenario of sections 7.2 and 13, at least 10 times each and at least 100 times each for the watchdog, OPI and tamper paths, with t_detect, t_inhibit and t_stop recorded separately. Each injection must show: the expected containment, the expected fact records in the history ring (and none invented), no automatic restart, and a successful recovery through SYNC, ARM and re-reference. Updates are also interrupted by power removal at every stage, and connectivity is removed, to show offline recovery.

**Glitch tests (section 4.2).** Pulses of 1 ns, 1 µs, 4 µs, 5 µs, 29 µs, 31 µs and 45 µs on every presence, PGOOD and tamper line; 0.2/0.5/2/5 µs pulses on TX_PERMIT and on OUT_PERMIT at each card; **0.1/0.3/1/2 µs pulses on the qualified bank-B Ioff-buffer OE**: rejected pulses leave every physical output untouched (analyser shows no gate transition), accepted pulses always set the OPI latch and fault, an OE pulse too short to reach TX_PERMIT_B still sets OPI_BOE and leaves STEP/DIR at their pulled idle level with no edge counted by an independent counter at the drive, and an accepted OUT_PERMIT_k pulse keeps that card's outputs off until IO_ENABLE. Both watchdog self-tests at 100 power-ups with a meter on PERMIT_OUT: it never closes.

## 15. Sources opened for this section

- Toshiba TLP3640A product page and datasheet Rev.1.0.A: https://toshiba.semicon-storage.com/eu/semiconductor/product/isolators-solid-state-relays/photorelay-mosfet-output/detail.TLP3640A.html
- Toshiba TLP4176A product page and datasheet Rev.3.0.A: https://toshiba.semicon-storage.com/eu/semiconductor/product/isolators-solid-state-relays/photorelay-mosfet-output/detail.TLP4176A.html
- Toshiba TLP4176G and TLP4590A product pages (rejected alternatives)
- Panasonic AQY212GS product page (rejected alternative): https://industry.panasonic.com/global/en/products/control/relay/photomos/number/aqy212gs
- OMC StepperOnline DM542T V4.0 user manual: https://omc-stepperonline.com/download/DM542T_V4.0.pdf
- TI SN74LVC07A: https://www.ti.com/product/SN74LVC07A ; TI TPS22918: https://www.ti.com/product/TPS22918
- Samsung CL10C332JB8NNN: https://product.samsungsem.com/mlcc/CL10C332JB8NNN.do
- Infineon FM24V02A-G: https://www.infineon.com/part/FM24V02A-G
- TPS3851 timing and behaviour: repository advice-verification record (TI SBVS300B), Codex's [MACHINE_PERMISSION.md](../../reports/MACHINE_PERMISSION.md) for the LVC gate figures
- LinuxCNC 2.9 halui and homing documentation in `research/vendor-src/linuxcnc/docs`

## 16. Blockers and hand-offs

**Genuinely blocked (exact dependency):**

| Item | Blocked by |
|---|---|
| Every [ME] figure: photorelay timing over temperature, WDO-to-inhibit, OPI capture, glitch tests, t_detect/t_inhibit/t_stop, thermal | Fabricated and assembled prototype boards (PCBWay order not placed; schematics and layout not complete) and bench instruments |
| 700 µs cycle distribution, input data age, output update latency, 72 h test | CM5102016 purchase (reference compute module), prototype boards, DM542T V4 drives and motors |
| FPGA fit of the added safety logic (OPI inputs, self-test timers, second progress output) | Efinix Efinity place-and-route (user-installed vendor tool) |

**Hand-off to Codex (hardware, IS-1 requirements):** sections 3.2 (including the AUX_5V chain), 3.5, 4.2 (filters, OPI latches including OPI_BOE and OPI_OUT, STEP/DIR idle pull-downs, card OUT_EN latches), 5.2 (TPS3851 × 2 with CL10C332JB8NNNC, CWD guard ring, wired-AND WDO/RESET, SET1 on the request, sticky trip flags), 6.2 (DIC_OK, permit pull-downs, PERMIT_OUT_REQ gate, latch_clear_O_n), 10 (AI-group converter REC3.5-2424SRW/R8/A, arm lamp on FIELD_B), 6.2–6.3 (gates and fanout on the motion card, pull-downs everywhere, validator re-run), 10 (MOTION_5V, EXP_5V, 4 A-class core entry, two field entries, AUX_24V/AUX_5V, bank limits, thermal and connector ratings), 12.2 (FM24V02A-G on the cartridge).

**Hand-off to Claude (implementation, IS-1 requirements):** progress pulse per accepted ARM/UPDATE and per accepted I/O exchange; SELFTEST state with PERMIT_OUT_REQ low and OUT_REQ zero; safety-interface qualifier (section 8.1); card firmware OUT_EN latch handling and the bootloader IWDG rule; clean commanded stop at pulse boundaries; OPI inputs, rearm strobes and proof test; `pos_continuity`; self-test sequencer; new fault bits; status fields of section 8; driver mapping to `halui.joint.J.unhome` through the channel-to-joint map and `VOLATILE_HOME = 1`; configuration-validator rules of sections 3.4 and 9; fact/diagnosis record types and the history ring.

**Unpriced cost items this section adds** (no recorded prices; unknown, not zero): per channel one TLP4176A(TP,F) and one TLP3640A(TPL,E), two TVS and one 220 Ω resistor; per bank one TPS22918DBVR; SN74LVC07APWR (2 on bank A, 1 on MX4); a second TPS3851G18SDRBT with CL10C332JB8NNNC; SN74LVC2G74DCUR for OPI_TX/OPI_BOE/OPI_OUT, trip flags and the OUT_EN/PEN latches on the output cards; the MC slot status register; the AI-group converter REC3.5-2424SRW/R8/A (observation CAD 61.39 at qty 100); qualification filters; AUX_24V/AUX_5V limiters and monitors; the second field entry (fuse, holder, eFuse, FETs, TVS, connector); the 4 A-class core entry change; MOTION_5V converter; FM24V02A-G. Location: motor-interface card and MX4 (enable parts), motion card (watchdogs, latches), power module (entries, MOTION_5V, AUX), cartridge (F-RAM). The costing section prices them, with the replacement-card cost of each card, before any selling price is recommended.

---

Interface specification revision IS-1. Nothing in this section is implemented, measured or ready for manufacture.
