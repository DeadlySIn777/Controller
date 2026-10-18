Interface specification revision: IS-1

# 03 - Field terminals and machine allocations

Section 03 of interface specification IS-1, written 28 September 2026. Machine-readable companions: `spec/terminals.json` and `spec/allocations.json` (both `"spec_revision": "IS-1"`). Codex's hardware and Claude's implementation both build against this revision; a change needs a new revision identifier (IS-2), not an in-place edit.

**Status: specification only.** Nothing in this section is implemented, built, measured or ready for manufacture. No schematic, PCB, gateware or driver change is claimed. Every electrical figure is a proposed target, a datasheet value or arithmetic, labelled as such. Codex owns the schematics, power/protection, connectors, PCB and hardware BOM that realise these terminals; Claude owns the FPGA logic, CNC1 protocol/driver and configuration-service integration that consume them. Both reference IS-1.

Machine-readable sources: [`spec/terminals.json`](../../spec/terminals.json) (every field terminal with all columns) and [`spec/allocations.json`](../../spec/allocations.json) (allocation sheets with counts). The tables below are rendered from those files; if they ever disagree, the JSON wins and the disagreement is a defect.

## 1. Evidence classes used here

| Class | Meaning in this section |
|---|---|
| source_inspection | Reading repository and Codex files |
| datasheet | Manufacturer/distributor data read on 28 Sep 2026 |
| arithmetic | Derived numbers |
| proposal | Engineering choice made under the user's delegated authority, not yet built |

No ERC, DRC, SPICE, HDL simulation, synthesis or physical measurement exists for anything specified in this section. The six-joint/two-encoder terminal map (`hardware/terminal-map.csv`, 96 positions) is historical baseline evidence and is superseded here as the product target; it is not relabelled.

## 2. Decisions made in this section (delegated engineering authority)

Section 04 (safety, permission, power and fault timing) fixes the enable circuit, its parts, the motor-plug signal set, the AUX loop supplies, the permission nets and the field-entry split. This section adopts those decisions unchanged and fixes the contact numbers, connector parts, card ownership and allocations around them.

| # | Decision | Reason | Cost direction (numbers unknown unless stated) | Standard or option |
|---|---|---|---|---|
| D03-1 | One fixed wiring base (BASE) carries every standard field terminal. It is passive copper (terminals, fuse holders, chassis/shield bonding, card slots) with no semiconductors; TVS, limiters and isolators sit on the replaceable card next to its slot connector. | A failed protection part is replaced with its card, never by rewiring. The short unprotected run from terminal to card is accepted and must pass the ESD/surge tests of the qualification plan. | Base PCB + terminal set on every unit; card connectors per slot (unpriced) | Standard |
| D03-2 | Terminal family: Phoenix Contact COMBICON MC 1,5 (3.81 mm) pluggable headers with screw-flange plugs for all signal and I/O groups; MSTB 2,5 (5.08 mm) for the three 24 V entries. Item numbers verified on manufacturer/distributor listings (section 4). | Pluggable plugs let the whole base be replaced without disturbing individual wires; flange screws resist vibration. One family keeps tooling and spares simple. Contact ratings (8 A nominal, 160 V for MC 1,5) are far above every signal load; the power entries use the larger family, derated by Codex against the 10 A-class requirement of section 04. | Header + plug per connector; price not yet recorded | Standard |
| D03-3 | Motor plug = 14 positions, 13 used; IS-1 contact numbers for Codex's connector map: 1 STEP+, 2 STEP-, 3 DIR+, 4 DIR-, 5 SIG_0V, 6 SHIELD, 7 empty gap, 8 EN_NO, 9 EN_COM, 10 EN_NC, 11 AUX_5V, 12 AUX_24V, 13 AUX_RTN, 14 ALARM_IN (signal set and parts from section 04 section 3.5). | Both enable polarities with correct power-loss behaviour (TLP3640A form A + TLP4176A form B on one LED current); AUX_5V/AUX_24V from FIELD keep a DM542T V4 disabled on LOGIC power loss; LOGIC contacts 1-5 separated from floating/FIELD contacts by the shield and an empty position. Supersedes the 10-contact order of MOTION_EXPANSION section 7.2. | 14-way plug instead of 10-way; two photorelays per channel | Standard (all 12 channels) |
| D03-4 | Channels 8-11 and encoders 4-11 terminate on an expansion terminal board XTB, fitted once (factory-fitted on twelve-motor units) and then part of the fixed wiring; the MX4 and EX8 electronics cards plug in behind it. | Eight-motor units do not pay for 4 unused motor plugs and 8 encoder plugs, while a twelve-motor unit's field terminals never move when MX4 or EX8 is replaced. | XTB board + 12 headers only on expanded units | Option (twelve-motor / encoder expansion) |
| D03-5 | Encoder expansion EX8 provides ENC4-ENC11, so a twelve-motor unit has one encoder per motor (12 total) with MX4 and EX8 fitted at the same time. | Nobody chooses between twelve motors and their feedback. Matches the expanded target's 'eight additional ABZ ports; twelve total' and the encoder-expansion power reservation of section 04 section 10.1. | EX8 card (6 quad receivers, 8 supply limiters, own converter) + 24 FPGA pins | Option |
| D03-6 | Three 24 V entries with their own plugs: XP1 CORE (4 A class), XP2 FIELD_A (DO0-DO7, AUX supplies, probes), XP3 FIELD_B (DO8-DO15, DI and safety sensor supplies). Loads and limits are section 04 section 10's. | 16 x 0.5 A = 8 A cannot come through the single 6 A entry; splitting keeps every output at its full rating without raising any limit. | One more entry branch (Codex's TPS26630 topology repeated) | Standard |
| D03-7 | General DO terminals use the T1 driver selected in section 02 section 11.2: TPS274C65ASRHAR (integrated 10-bit ADC; per-channel current, VOUT and FET temperature; on/off-state open-load; short-to-supply; adjustable current limit). TPS274C65BS is excluded (its datasheet comparison table lists no ADC and no current sense). | Per-channel digital current, on/off-state open-load, short-to-supply, current limit, thermal and VS/VOUT/temperature over SPI fit the serial DO-card transport; section 02 section 11.2 holds the full comparison against TPS4H160BQPWPRQ1 plus external acquisition. | Driver price not recorded (unknown, not zero); one isolator per card instead of three | Standard |
| D03-8 | Channel names are 0-based everywhere (M0-M11, ENC0-ENC11, DI0-DI23, DO0-DO15) on silkscreen, UI, HAL and CNC1. HAL prefixes follow the existing cnc1 driver: `cnc1.N.*` per motor channel, `cnc1.encoder.N.*` per encoder. | One name per wire from terminal to software removes a common wiring error; matches the existing driver's pin names. | None | Standard |
| D03-9 | Handwheel port = XH1 (differential or single-ended A/B with a 2.5 V bias terminal, enable button) + XH2 (10 selector inputs). MPG A/B use receiver channels 15-16 of the four base quad receivers. | A dedicated port that never consumes a general DI or an encoder port. | Shift register + bias network on EIA | Standard |
| D03-10 | XF measurement-module port = FREQ0/1 differential inputs + 5 V supply + module presence + 1-Wire identity line. | The plasma divided-voltage module (and later measurement modules) is identified and presence-checked through its own plug; raw arc voltage never reaches the controller. | 1-Wire bridge on EIA | Standard |
| D03-11 | XS1 machine safety interface on the digital-input card (DIC): EXT_PERMIT and PROCESS_PERMIT hard-wired into the permission chain (section 04 section 6), chain status, deliberate reset/arm with lamp, contactor and STO feedback, and a PERMIT_OUT contact that follows TX_PERMIT. | Gives the machine safety design a monitored hand-off without making the controller a safety controller. PERMIT_OUT adds one TX_PERMIT receiver, now listed in the section 04 section 6.3 fan-out table (integration item R03-1, closed). | ISO1212 channels + one photorelay | Standard |
| D03-12 | Analog outputs AO0/AO1 each get their own isolation domain; the four AI share one isolated group with software-selected 0-10 V / 4-20 mA ranges. | Two VFDs or process devices with different commons connect without a ground loop; AI sensors usually share one supply. | Second isolated AO supply | Standard |

### 2.1 Enable and process-contact parts (from section 04, verified there)

| Function | Part | Values used here | IS-1 published rating |
|---|---|---|---|
| Normally-open enable, process contacts, PERMIT_OUT | Toshiba TLP3640A(TPL,E), 1-Form-A photorelay | 60 V, 1 A, RON <= 0.3 ohm (section 04 section 3.1, datasheet) | AC or DC 0-30 V, <= 50 mA |
| Normally-closed enable | Toshiba TLP4176A(TP,F), 1-Form-B photorelay | 60 V, 0.5 A, RON <= 2.5 ohm (section 04 section 3.1, datasheet) | AC or DC 0-30 V, <= 50 mA |

One LED current drives both switches of a channel (section 04 section 3.2). With no command, no TX_PERMIT or no LOGIC power the LEDs are dark: **EN_NO open, EN_NC closed**. States and exceptions E1-E5 are normative in section 04 sections 3.3-3.4; the configuration service shows them in the wiring guide.

**DM542T V4 reference drive, supported (wiring mode NC-5V):** XMn.1/2 -> PUL+/PUL-, XMn.3/4 -> DIR+/DIR- (drive switch S2 set to 5 V; opto drive compatibility is profile test TT-XMn-01..04), XMn.11 AUX_5V -> ENA+, ENA- -> XMn.10 EN_NC, XMn.9 EN_COM -> XMn.13 AUX_RTN, XMn.12 AUX_24V -> ALM+, ALM- -> XMn.14 ALARM_IN, `alarm_on_no_current` = 1. The drive is disabled whenever the channel is disarmed and when the controller's LOGIC power is lost with FIELD present. The profile carries section 04's timing (ENA leads DIR by >= 200 ms, 2.5 us high/low, 5 us DIR setup, <= 200 kHz).

## 3. Domains, returns and bonding

| Domain | Terminals | Reference | Crosses to LOGIC through |
|---|---|---|---|
| CORE_24V | XP1 | CORE 0 V (logic converter input side) | Converter (Codex core_converter) |
| LOGIC_TX | STEP/DIR pairs, SIG_0V, PWM | LOGIC_GND (non-isolated RS-422) | Direct; AM26C31 / buffer |
| LOGIC_ENC | Encoder, MPG and FREQ lines and their 5 V supplies | LOGIC_GND (non-isolated) | Direct; receivers |
| FIELD_A | DO0-DO7, AUX_5V/AUX_24V/AUX_RTN, ALARM_IN, probes | FIELD_A 0 V (not tied to LOGIC on the controller) | ISO1212, isolators, TPS274C65ASRHAR SPI isolation (ISO7762FDBQR) |
| FIELD_B | DO8-DO15, DI0-DI23, sensor supplies, XS1 safety interface | FIELD_B 0 V | ISO1212, isolators |
| ISO_SW | EN_NO/EN_COM/EN_NC, process contacts, PERMIT_OUT | Floating (each contact isolated) | Photorelay barrier |
| ISO_AO0, ISO_AO1, ISO_AI | Analog outputs (one domain each), analog-input group | Own isolated commons | Isolated converters/isolators on ACC |
| ISO_485, ISO_CAN | Field buses | Own isolated commons | Isolated transceivers on ACC |
| CHASSIS | SHIELD contacts, SB1 clamp rail, XPE1 | Protective earth | Never a signal return |

The motor plug carries LOGIC_TX (1-5), CHASSIS (6), an empty gap (7), ISO_SW (8-10) and FIELD_A (11-14). Creepage/clearance between SIG_0V and any floating or FIELD contact must suit 60 V working voltage (section 04 section 3.5); at 3.81 mm pitch the empty position 7 gives 7.62 mm between contacts 6 and 8 (arithmetic, pitch only; Codex checks the real PCB and plug geometry). Shield drains terminate at the controller end only (SB1 clamp rail bonded to XPE1).

## 4. Connector summary

| Connector | Location | Pos | Header / plug (Phoenix item) | Owning card | Fitted | Purpose |
|---|---|---:|---|---|---|---|
| XP1 | fixed base, power edge | 4 | MSTB 2,5/ 4-GF-5,08 (1776524) / MSTB 2,5/ 4-STF-5,08 (1778001) | PSM | standard | CORE entry |
| XP2 | fixed base, power edge | 4 | MSTB 2,5/ 4-GF-5,08 (1776524) / MSTB 2,5/ 4-STF-5,08 (1778001) | PSM | standard | FIELD_A entry |
| XP3 | fixed base, power edge | 4 | MSTB 2,5/ 4-GF-5,08 (1776524) / MSTB 2,5/ 4-STF-5,08 (1778001) | PSM | standard | FIELD_B entry |
| XPE1 | fixed base, power edge | 1 | Base PCB bonded mounting point to enclosure metal (Codex) / Ring terminal (customer) | BASE | standard | Protective earth / chassis bond and cable-shield clamp rail |
| XM0 | fixed base, motor row | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MIA | standard | Motor channel M0: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM1 | fixed base, motor row | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MIA | standard | Motor channel M1: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM2 | fixed base, motor row | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MIA | standard | Motor channel M2: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM3 | fixed base, motor row | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MIA | standard | Motor channel M3: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM4 | fixed base, motor row | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MIA | standard | Motor channel M4: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM5 | fixed base, motor row | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MIA | standard | Motor channel M5: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM6 | fixed base, motor row | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MIA | standard | Motor channel M6: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM7 | fixed base, motor row | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MIA | standard | Motor channel M7: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM8 | expansion terminal board XTB (fixed once fitted) | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MX4 | expansion (twelve-motor units; XTB factory-fitted) | Motor channel M8: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM9 | expansion terminal board XTB (fixed once fitted) | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MX4 | expansion (twelve-motor units; XTB factory-fitted) | Motor channel M9: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM10 | expansion terminal board XTB (fixed once fitted) | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MX4 | expansion (twelve-motor units; XTB factory-fitted) | Motor channel M10: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XM11 | expansion terminal board XTB (fixed once fitted) | 14 | MC 1,5/14-GF-3,81 (1827981) / MC 1,5/14-STF-3,81 (1827826) | MX4 | expansion (twelve-motor units; XTB factory-fitted) | Motor channel M11: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm |
| XE0 | fixed base, encoder row | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EIA | standard | ABZ encoder port ENC0 |
| XE1 | fixed base, encoder row | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EIA | standard | ABZ encoder port ENC1 |
| XE2 | fixed base, encoder row | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EIA | standard | ABZ encoder port ENC2 |
| XE3 | fixed base, encoder row | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EIA | standard | ABZ encoder port ENC3 |
| XE4 | expansion terminal board XTB | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EX8 | encoder expansion (EX8 fitted) | ABZ encoder port ENC4 |
| XE5 | expansion terminal board XTB | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EX8 | encoder expansion (EX8 fitted) | ABZ encoder port ENC5 |
| XE6 | expansion terminal board XTB | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EX8 | encoder expansion (EX8 fitted) | ABZ encoder port ENC6 |
| XE7 | expansion terminal board XTB | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EX8 | encoder expansion (EX8 fitted) | ABZ encoder port ENC7 |
| XE8 | expansion terminal board XTB | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EX8 | encoder expansion (EX8 fitted) | ABZ encoder port ENC8 |
| XE9 | expansion terminal board XTB | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EX8 | encoder expansion (EX8 fitted) | ABZ encoder port ENC9 |
| XE10 | expansion terminal board XTB | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EX8 | encoder expansion (EX8 fitted) | ABZ encoder port ENC10 |
| XE11 | expansion terminal board XTB | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EX8 | encoder expansion (EX8 fitted) | ABZ encoder port ENC11 |
| XH1 | fixed base, operator row | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EIA | standard | MPG/handwheel encoder and enable button |
| XH2 | fixed base, operator row | 12 | MC 1,5/12-GF-3,81 (1827965) / MC 1,5/12-STF-3,81 (1827800) | EIA | standard | Pendant selector switches (axis, multiplier, auxiliary) |
| XDI0 | fixed base, I/O row | 12 | MC 1,5/12-GF-3,81 (1827965) / MC 1,5/12-STF-3,81 (1827800) | DIC | standard | General inputs DI0-DI7 with group sensor supply |
| XDI1 | fixed base, I/O row | 12 | MC 1,5/12-GF-3,81 (1827965) / MC 1,5/12-STF-3,81 (1827800) | DIC | standard | General inputs DI8-DI15 with group sensor supply |
| XDI2 | fixed base, I/O row | 12 | MC 1,5/12-GF-3,81 (1827965) / MC 1,5/12-STF-3,81 (1827800) | DIC | standard | General inputs DI16-DI23 with group sensor supply |
| XDO0 | fixed base, I/O row | 12 | MC 1,5/12-GF-3,81 (1827965) / MC 1,5/12-STF-3,81 (1827800) | DOA | standard | General sourcing outputs DO0-DO7 |
| XDO1 | fixed base, I/O row | 12 | MC 1,5/12-GF-3,81 (1827965) / MC 1,5/12-STF-3,81 (1827800) | DOB | standard | General sourcing outputs DO8-DO15 |
| XPR | fixed base, process row | 6 | MC 1,5/ 6-GF-3,81 (1827907) / MC 1,5/ 6-STF-3,81 (1827745) | EIA | standard | Two fast probe inputs with typed sensor supplies |
| XF | fixed base, process row | 10 | MC 1,5/10-GF-3,81 (1827949) / MC 1,5/10-STF-3,81 (1827787) | EIA | standard | Two differential frequency inputs + measurement-module presence/identity (plasma divided-voltage module, THCAD-class) |
| XPW | fixed base, process row | 6 | MC 1,5/ 6-GF-3,81 (1827907) / MC 1,5/ 6-STF-3,81 (1827745) | ACC | standard | Two buffered PWM outputs |
| XPC0 | fixed base, process row | 2 | MC 1,5/ 2-GF-3,81 (1827868) / MC 1,5/ 2-STF-3,81 (1827703) | ACC | standard | Process enable 0: hardware-gated floating contact (torch start / laser enable / ohmic enable) |
| XPC1 | fixed base, process row | 2 | MC 1,5/ 2-GF-3,81 (1827868) / MC 1,5/ 2-STF-3,81 (1827703) | ACC | standard | Process enable 1: hardware-gated floating contact (torch start / laser enable / ohmic enable) |
| XAO | fixed base, analog row | 6 | MC 1,5/ 6-GF-3,81 (1827907) / MC 1,5/ 6-STF-3,81 (1827745) | ACC | standard | Two isolated 0-10 V analog outputs, independent isolation per channel |
| XAI | fixed base, analog row | 12 | MC 1,5/12-GF-3,81 (1827965) / MC 1,5/12-STF-3,81 (1827800) | ACC | standard | Four protected analog inputs with sensor supplies (one isolated AI group) |
| XB1 | fixed base, communication row | 6 | MC 1,5/ 6-GF-3,81 (1827907) / MC 1,5/ 6-STF-3,81 (1827745) | ACC | standard | Isolated RS-485 field bus |
| XB2 | fixed base, communication row | 6 | MC 1,5/ 6-GF-3,81 (1827907) / MC 1,5/ 6-STF-3,81 (1827745) | ACC | standard | Isolated CAN field bus |
| XS1 | fixed base, safety row | 12 | MC 1,5/12-GF-3,81 (1827965) / MC 1,5/12-STF-3,81 (1827800) | DIC | standard | Machine safety-chain interface: external permit, process interlock, chain status, deliberate reset/arm with lamp, contactor and STO feedback, output-permission contact |

Totals (arithmetic): 45 field connectors, 451 field terminals; 315 on a standard eight-motor unit, 136 added by XTB (XM8-XM11, XE4-XE11). Connector item numbers are proposals to Codex (connector owner): verified as orderable catalogue items, not yet footprint-approved or derated for this design. Coding profiles (so that no plug fits a wrong header of the same size) are Codex's selection; the rule is stated per connector in `terminals.json`.

Edge length (arithmetic, pitch only, no flange/gap allowance): 302 MC 1,5 positions on the base x 3.81 mm = 1151 mm; 136 positions on XTB = 518 mm; plus three MSTB 4-way entries at 5.08 mm. The base therefore needs its terminals on more than one edge or in two tiers (motor/encoder row, I/O row, process/analog/communication/safety row, power edge); the mechanical arrangement is Codex's, the row grouping above is fixed.

### 4.1 Card ownership

| Card | Contents |
|---|---|
| BASE | Fixed wiring base: passive copper, all field terminals, fuse holders, chassis/shield bonding (SB1 rail, XPE1 stud), card slots. No semiconductors, so a base replacement is rare and a card replacement never disturbs a wire. |
| XTB | Expansion terminal board: passive, fitted once (factory on twelve-motor units), carries XM8-XM11 and XE4-XE11; becomes part of the fixed wiring once fitted |
| MC | Motion card: T20F256 FPGA, 50 MHz clock, configuration flash, two TPS3851 watchdogs (WD_M, WD_O), both arm latches, OPI_TX latch and the final TX/OUT/PROC_PERMIT gates (section 04 sections 5-6), Ioff buffers on every card-bound output including the MX4 path, AT30TSE752A identity and board temperature |
| MIA | Motor interface card A: M0-M7 AM26C31 x4, 8 x (TLP3640A + TLP4176A) with SN74LVC07A drivers and the TPS22918 LED-supply switch, ISO1212 x4 for alarms, TX_PERMIT_A receiver, OPI_A latch (section 04); AUX_5V/AUX_24V arrive from the power module |
| MX4 | Motor expansion card: M8-M11 (same circuits as MIA, 4 channels, TX_PERMIT_B), identity EEPROM, EXP_5V supervisor, OPI_B latch |
| EIA | Encoder and fast-input card: ENC0-3 + FREQ0-1 + MPG A/B (4 x AM26LV32E-class), TPS2553-1 per port, probes (ISO1212, unfiltered), pendant shift register, XF identity bridge |
| EX8 | Encoder expansion card: ENC4-11 (6 x AM26LV32E-class, 8 x TPS2553-1), identity |
| DIC | Digital input card: DI0-DI23 (12 x ISO1212), group sensor-supply limiters, serial link with identity/sequence/CRC; XS1 safety interface (EXT_PERMIT and PROCESS_PERMIT hard-wired to the motion card, status/feedback inputs direct to the FPGA, arm lamp, PERMIT_OUT photorelay) |
| DOA | Output card A: DO0-DO7, 2 x TPS274C65ASRHAR behind one ISO7762FDBQR isolator, OUT_PERMIT AND CARD_EN hardware gate on DO_EN, card accept timer 1.0 ms and IWDG <= 2 ms output cutoff (section 01 section 4.7) |
| DOB | Output card B: DO8-DO15, identical part number to DOA (slot-coded identity) |
| ACC | Analog/communication/process card: AO0-1 (independently isolated), AI0-3 (isolated group), RS-485 and CAN isolated transceivers, PWM buffers, process-enable photoMOS |
| PSM | Power and service module: CORE/FIELD_A/FIELD_B entry eFuses (TPS26630), converters (incl. MOTION_5V and FIELD_5V), per-bank AUX_5V/AUX_24V limiters and monitors, 3 x INA238AIDGSR entry monitors, POR and tamper latches, cartridge slot |
| CMC | Compute carrier card: dual 100-pin CM4/CM5-family module socket, mated at the factory; reference module Raspberry Pi CM5102016 (costing and first timing qualification), other modules qualified separately; Ethernet, HDMI, USB host, antenna feed |
| ESC | ESP32-S3 service card: USB-C service port, service antenna |
| SCART | Settings cartridge |

Card names are the IS-1 names of section 02 (slot map in section 02 section 3), which adopted this list unchanged.

## 5. Terminal tables

Columns rendered here: position, net, function, domain, electrical target, FPGA/serial resource, CNC1 field, HAL pin, power-up state, fault state, test id. The UI label, protection and owning card of each terminal are in `terminals.json` (the UI label equals the silkscreen text). Update class: `servo` = carried every 1 ms exchange (T2); `telemetry` = sampled locally, timestamped, reported with age; `none` = passive.

### XP1

CORE entry. Keying: Unique coding profile per entry (Codex to select coding item) so CORE/FIELD_A/FIELD_B plugs cannot be swapped. Cable: Customer PSU cable, 1.5-2.5 mm2 class; no shield.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CORE_24V_IN | CORE +24 V input | CORE_24V | Nominal 24 V DC, 19-30 V draft entry envelope (Codex power_entry r0.2); 4 A-class entry, fuse and connector: 3.011 A input at 18 V with 12 motors + 8-port encoder expansion (including the ACC AI group), current-limit minimum >= 3.61 A (IS-1 section 04 section 10.1, arithmetic) | - | HOST.i2c.psm.entry[0].v / HOST.i2c.psm.entry[0].i | cnc1.supply.core.voltage / cnc1.supply.core.current | Entry eFuse starts after UVLO; motion stays disarmed | eFuse latched off on overload/thermal; motion inhibited if CORE; outputs of that bank off if FIELD | telemetry | TT-XP1-01 |
| 2 | CORE_0V | CORE 0 V return | CORE_24V | Return; not bonded to other domains on the controller | - | - | - | n/a | n/a | none | TT-XP1-02 |
| 3 | XP1_SHDN_A | CORE remote shutdown/clear contact, side A | CORE_24V | Dry contact, logic-level current only; close A-B to switch this entry off; opening again clears a latched eFuse fault | - | STS.safety bit 20 (entry power-good: the effect of a shutdown request; the contact state itself is not reported) | cnc1.power.core-ok | Open = entry runs | n/a (input) | servo | TT-XP1-03 |
| 4 | XP1_SHDN_B | CORE remote shutdown/clear contact, side B | CORE_24V | See position 3 | - | - | - | n/a | n/a | none | TT-XP1-04 |

### XP2

FIELD_A entry. Keying: Unique coding profile per entry (Codex to select coding item) so CORE/FIELD_A/FIELD_B plugs cannot be swapped. Cable: Customer PSU cable, 1.5-2.5 mm2 class; no shield.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FIELD_A_24V_IN | FIELD_A +24 V input | FIELD_A | Nominal 24 V DC, 19-30 V draft entry envelope (Codex power_entry r0.2); DO0-DO7 + AUX_24V/AUX_5V (both banks) + FIELD_5V + probe supplies: 4.58 A continuous, entry current-limit minimum >= 5.08 A, 7.5 A fuse, 10 A-class wiring and connector (IS-1 section 04 section 10.2, arithmetic) | - | HOST.i2c.psm.entry[1].v / HOST.i2c.psm.entry[1].i | cnc1.supply.field-a.voltage / cnc1.supply.field-a.current | Entry eFuse starts after UVLO; motion stays disarmed | eFuse latched off on overload/thermal; motion inhibited if CORE; outputs of that bank off if FIELD | telemetry | TT-XP2-01 |
| 2 | FIELD_A_0V | FIELD_A 0 V return | FIELD_A | Return; not bonded to other domains on the controller | - | - | - | n/a | n/a | none | TT-XP2-02 |
| 3 | XP2_SHDN_A | FIELD_A remote shutdown/clear contact, side A | FIELD_A | Dry contact, logic-level current only; close A-B to switch this entry off; opening again clears a latched eFuse fault | - | STS.safety bit 16 (entry power-good: the effect of a shutdown request; the contact state itself is not reported) | cnc1.power.field-a-ok | Open = entry runs | n/a (input) | servo | TT-XP2-03 |
| 4 | XP2_SHDN_B | FIELD_A remote shutdown/clear contact, side B | FIELD_A | See position 3 | - | - | - | n/a | n/a | none | TT-XP2-04 |

### XP3

FIELD_B entry. Keying: Unique coding profile per entry (Codex to select coding item) so CORE/FIELD_A/FIELD_B plugs cannot be swapped. Cable: Customer PSU cable, 1.5-2.5 mm2 class; no shield.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FIELD_B_24V_IN | FIELD_B +24 V input | FIELD_B | Nominal 24 V DC, 19-30 V draft entry envelope (Codex power_entry r0.2); DO8-DO15 + DI/safety sensor supplies 0.75 A + reset/arm lamp 0.05 A: 4.82 A continuous, entry current-limit minimum >= 5.32 A, 7.5 A fuse, 10 A-class wiring and connector (IS-1 section 04 section 10.2, arithmetic) | - | HOST.i2c.psm.entry[2].v / HOST.i2c.psm.entry[2].i | cnc1.supply.field-b.voltage / cnc1.supply.field-b.current | Entry eFuse starts after UVLO; motion stays disarmed | eFuse latched off on overload/thermal; motion inhibited if CORE; outputs of that bank off if FIELD | telemetry | TT-XP3-01 |
| 2 | FIELD_B_0V | FIELD_B 0 V return | FIELD_B | Return; not bonded to other domains on the controller | - | - | - | n/a | n/a | none | TT-XP3-02 |
| 3 | XP3_SHDN_A | FIELD_B remote shutdown/clear contact, side A | FIELD_B | Dry contact, logic-level current only; close A-B to switch this entry off; opening again clears a latched eFuse fault | - | STS.safety bit 17 (entry power-good: the effect of a shutdown request; the contact state itself is not reported) | cnc1.power.field-b-ok | Open = entry runs | n/a (input) | servo | TT-XP3-03 |
| 4 | XP3_SHDN_B | FIELD_B remote shutdown/clear contact, side B | FIELD_B | See position 3 | - | - | - | n/a | n/a | none | TT-XP3-04 |

### XPE1

Protective earth / chassis bond and cable-shield clamp rail. Keying: n/a. Cable: Green/yellow PE conductor from machine PE bar.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CHASSIS_PE | Protective-earth and chassis bond; cable shields clamp to SB1 rail bonded here | CHASSIS | Bond resistance target < 0.1 ohm stud-to-enclosure (to be measured) | - | - | - | n/a | n/a | none | TT-XPE1-01 |

### XM0 (template for XM0-XM7 on the base: replace 0 by n; owner MIA)

Motor channel M0: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm. Keying: All motor plugs share one coding pattern (harnesses interchangeable between channels, by design); no other connector on the product has 14 positions. Cable: Shielded twisted-pair drive-signal cable; drain to position 6 and/or SB1 clamp; motor power wiring never enters the controller.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | M0_STEP_P | STEP+ differential | LOGIC_TX | RS-422 differential, 5 V-supplied AM26C31; differential output magnitude >= 2 V into 100 ohm (AM26C31 datasheet class; loaded value to be measured); rate <= min(board, gateware cap 195,312.5 steps/s at 50 MHz, configured timing, drive limit); 2 MHz/channel is an unqualified goal. Opto-input drives (e.g. DM542T V4 PUL/DIR, S2 set to 5 V) need the profile's compatibility test | FPGA STEP0_FPGA ball P2 | CMD.motor[0].rate / STS.motor[0].position / STS.pos_continuity bit 0 | cnc1.0.position-cmd / cnc1.0.position-fb / cnc1.0.position-continuity | High-impedance (AM26C31 G held low by TX_PERMIT_A pull-downs); FPGA holds STEP low | High-impedance through the hardware permission path. Per IS-1 section 04 section 4: any interruption of an active path latches OUTPUT_PATH_INTERRUPTED and clears pos_continuity (joint unhomed); a rejected noise pulse never changes these pins | servo | TT-XM0-01 |
| 2 | M0_STEP_N | STEP- differential | LOGIC_TX | RS-422 differential, 5 V-supplied AM26C31; differential output magnitude >= 2 V into 100 ohm (AM26C31 datasheet class; loaded value to be measured); rate <= min(board, gateware cap 195,312.5 steps/s at 50 MHz, configured timing, drive limit); 2 MHz/channel is an unqualified goal. Opto-input drives (e.g. DM542T V4 PUL/DIR, S2 set to 5 V) need the profile's compatibility test | FPGA STEP0_FPGA ball P2 | CMD.motor[0].rate / STS.motor[0].position / STS.pos_continuity bit 0 | cnc1.0.position-cmd / cnc1.0.position-fb / cnc1.0.position-continuity | High-impedance (AM26C31 G held low by TX_PERMIT_A pull-downs); FPGA holds STEP low | High-impedance through the hardware permission path. Per IS-1 section 04 section 4: any interruption of an active path latches OUTPUT_PATH_INTERRUPTED and clears pos_continuity (joint unhomed); a rejected noise pulse never changes these pins | servo | TT-XM0-02 |
| 3 | M0_DIR_P | DIR+ differential | LOGIC_TX | RS-422 differential, 5 V-supplied AM26C31; differential output magnitude >= 2 V into 100 ohm (AM26C31 datasheet class; loaded value to be measured); rate <= min(board, gateware cap 195,312.5 steps/s at 50 MHz, configured timing, drive limit); 2 MHz/channel is an unqualified goal. Opto-input drives (e.g. DM542T V4 PUL/DIR, S2 set to 5 V) need the profile's compatibility test | FPGA DIR0_FPGA ball J5 | CMD.motor[0].rate / STS.motor[0].position / STS.pos_continuity bit 0 | cnc1.0.position-cmd / cnc1.0.position-fb / cnc1.0.position-continuity | High-impedance (AM26C31 G held low by TX_PERMIT_A pull-downs); FPGA holds STEP low | High-impedance through the hardware permission path. Per IS-1 section 04 section 4: any interruption of an active path latches OUTPUT_PATH_INTERRUPTED and clears pos_continuity (joint unhomed); a rejected noise pulse never changes these pins | servo | TT-XM0-03 |
| 4 | M0_DIR_N | DIR- differential | LOGIC_TX | RS-422 differential, 5 V-supplied AM26C31; differential output magnitude >= 2 V into 100 ohm (AM26C31 datasheet class; loaded value to be measured); rate <= min(board, gateware cap 195,312.5 steps/s at 50 MHz, configured timing, drive limit); 2 MHz/channel is an unqualified goal. Opto-input drives (e.g. DM542T V4 PUL/DIR, S2 set to 5 V) need the profile's compatibility test | FPGA DIR0_FPGA ball J5 | CMD.motor[0].rate / STS.motor[0].position / STS.pos_continuity bit 0 | cnc1.0.position-cmd / cnc1.0.position-fb / cnc1.0.position-continuity | High-impedance (AM26C31 G held low by TX_PERMIT_A pull-downs); FPGA holds STEP low | High-impedance through the hardware permission path. Per IS-1 section 04 section 4: any interruption of an active path latches OUTPUT_PATH_INTERRUPTED and clears pos_continuity (joint unhomed); a rejected noise pulse never changes these pins | servo | TT-XM0-04 |
| 5 | M0_SIG0V | Signal reference (LOGIC_GND) for STEP/DIR | LOGIC_TX | LOGIC_GND return for the RS-422 pairs; connect to the drive's signal common only if its input requires a reference | - | - | - | n/a | n/a | none | TT-XM0-05 |
| 6 | M0_SHIELD | Cable shield drain (chassis via SB1 rail) | CHASSIS | Chassis via base copper to SB1/XPE1; never a signal return | - | - | - | n/a | n/a | none | TT-XM0-06 |
| 7 | M0_NC_GAP | Not connected: creepage/clearance gap between LOGIC and floating/FIELD groups (plug position left empty) | NONE | No connection on the base; plug position left empty | - | - | - | n/a | n/a | none | TT-XM0-07 |
| 8 | M0_EN_NO | Enable switch, normally open (form A, TLP3640A). Wiring modes NO-sourced (AUX_24V -> drive EN+, drive EN- -> EN_NO, EN_COM -> AUX_RTN) or NO-drive (drive's own loop). Use for drives enabled by energising their input (servo SON). | ISO_SW | Floating photorelay contact, AC or DC, 0-30 V, <= 50 mA continuous per switch (IS-1 published rating, section 04 section 3.2); TLP3640A(TPL,E) form A: 60 V, 1 A, RON <= 0.3 ohm; TLP4176A(TP,F) form B: 60 V, 0.5 A, RON <= 2.5 ohm (datasheets via section 04) | FPGA EN0_N_FPGA ball H12 | STS.armed_mask bit 0 (per-channel enable follows the ARM channel_mask) / STS.enable_cmd_state bit 0 | cnc1.0.enable / cnc1.0.enable-commanded | OPEN (LED dark) | OPEN on command loss, TX_PERMIT loss, fault, self-test or LOGIC power loss | servo | TT-XM0-08 |
| 9 | M0_EN_COM | Enable switch common (shared by the NO and NC switch) | ISO_SW | Floating photorelay contact, AC or DC, 0-30 V, <= 50 mA continuous per switch (IS-1 published rating, section 04 section 3.2); TLP3640A(TPL,E) form A: 60 V, 1 A, RON <= 0.3 ohm; TLP4176A(TP,F) form B: 60 V, 0.5 A, RON <= 2.5 ohm (datasheets via section 04) | FPGA EN0_N_FPGA ball H12 | - | - | n/a (common) | n/a (common) | servo | TT-XM0-09 |
| 10 | M0_EN_NC | Enable switch, normally closed (form B, TLP4176A). Wiring mode NC-5V for the DM542T V4 reference drive: AUX_5V -> ENA+, ENA- -> EN_NC, EN_COM -> AUX_RTN; the drive is disabled while disarmed and on controller LOGIC power loss because AUX_5V comes from FIELD. Exceptions E1-E5 (section 04 section 3.4) are shown by the service. | ISO_SW | Floating photorelay contact, AC or DC, 0-30 V, <= 50 mA continuous per switch (IS-1 published rating, section 04 section 3.2); TLP3640A(TPL,E) form A: 60 V, 1 A, RON <= 0.3 ohm; TLP4176A(TP,F) form B: 60 V, 0.5 A, RON <= 2.5 ohm (datasheets via section 04) | FPGA EN0_N_FPGA ball H12 | STS.armed_mask bit 0 (per-channel enable follows the ARM channel_mask) / STS.enable_cmd_state bit 0 | cnc1.0.enable / cnc1.0.enable-commanded | CLOSED (LED dark) | CLOSED on command loss, TX_PERMIT loss, fault, self-test or LOGIC power loss | servo | TT-XM0-10 |
| 11 | M0_AUX_5V | AUX_5V: FIELD-derived 5 V loop supply for 5 V enable inputs (e.g. DM542T V4 ENA), current-limited per bank | FIELD_A | 5 V from FIELD_A, per-bank limit; load A 8 x 16 mA = 128 mA, B 64 mA (section 04 section 10.3) | - | STS.safety bit 14 | cnc1.safety.aux5-ok-a | On with FIELD_A (independent of LOGIC rails) | Limiter active: AUX5_OK_A low -> ARM refused / fault latched if armed; alarms of the bank read asserted (fail-closed) | servo | TT-XM0-11 |
| 12 | M0_AUX_24V | AUX_24V: FIELD 24 V loop supply for alarm outputs and 24 V enable loops, current-limited per bank | FIELD_A | 24 V from FIELD_A, limit min >= 1.1 x load, max <= 0.30 A (bank A) / 0.20 A (bank B); load A 0.148 A, B 0.074 A (section 04 section 10.3) | - | STS.safety bit 12 | cnc1.safety.aux24-ok-a | On with FIELD_A (independent of LOGIC rails) | Limiter active: AUX24_OK_A low -> ARM refused / fault latched if armed; alarms of the bank read asserted (fail-closed) | servo | TT-XM0-12 |
| 13 | M0_AUX_RTN | AUX return (FIELD_A 0 V) | FIELD_A | FIELD_A return for AUX loops and the alarm input | - | - | - | n/a | n/a | none | TT-XM0-13 |
| 14 | M0_ALM_IN | Drive alarm input (ISO1212 sinking, 24 V) | FIELD_A | Sinking 24 V input: AUX_24V -> drive ALM+, drive ALM- -> ALM_IN (or a sourcing alarm output with its 0 V on AUX_RTN); 0-30 V, low 0-5 V, high 15-30 V; 2.47 mA max (ISO1212, 562 ohm RSENSE); polarity per channel (alarm_on_no_current = 1 for DM542T V4) | FPGA ALM0_FPGA ball B12 | STS.alarm bit 0 / STS.alarm_latched bit 0 | cnc1.0.alarm / cnc1.0.alarm-latched | Ignored until endpoint qualification; ARM refused while asserted | Alarm on an armed channel in the trip mask disarms all channels (latched); open wire reads 'alarm' when alarm_on_no_current = 1 (fail-closed) | servo | TT-XM0-14 |

### XM8 (template for XM8-XM11 on XTB: replace 8 by n; owner MX4; permission TX_PERMIT_B)

Motor channel M8: differential STEP/DIR, individual NO/COM/NC enable switch pair, per-bank AUX loop supplies, individual alarm. Keying: All motor plugs share one coding pattern (harnesses interchangeable between channels, by design); no other connector on the product has 14 positions. Cable: Shielded twisted-pair drive-signal cable; drain to position 6 and/or SB1 clamp; motor power wiring never enters the controller.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | M8_STEP_P | STEP+ differential | LOGIC_TX | RS-422 differential, 5 V-supplied AM26C31; differential output magnitude >= 2 V into 100 ohm (AM26C31 datasheet class; loaded value to be measured); rate <= min(board, gateware cap 195,312.5 steps/s at 50 MHz, configured timing, drive limit); 2 MHz/channel is an unqualified goal. Opto-input drives (e.g. DM542T V4 PUL/DIR, S2 set to 5 V) need the profile's compatibility test | FPGA STEP8_FPGA ball E2 | CMD.motor[8].rate / STS.motor[8].position / STS.pos_continuity bit 8 | cnc1.8.position-cmd / cnc1.8.position-fb / cnc1.8.position-continuity | High-impedance (AM26C31 G held low by TX_PERMIT_B pull-downs); FPGA holds STEP low | High-impedance through the hardware permission path. Per IS-1 section 04 section 4: any interruption of an active path latches OUTPUT_PATH_INTERRUPTED and clears pos_continuity (joint unhomed); a rejected noise pulse never changes these pins | servo | TT-XM8-01 |
| 2 | M8_STEP_N | STEP- differential | LOGIC_TX | RS-422 differential, 5 V-supplied AM26C31; differential output magnitude >= 2 V into 100 ohm (AM26C31 datasheet class; loaded value to be measured); rate <= min(board, gateware cap 195,312.5 steps/s at 50 MHz, configured timing, drive limit); 2 MHz/channel is an unqualified goal. Opto-input drives (e.g. DM542T V4 PUL/DIR, S2 set to 5 V) need the profile's compatibility test | FPGA STEP8_FPGA ball E2 | CMD.motor[8].rate / STS.motor[8].position / STS.pos_continuity bit 8 | cnc1.8.position-cmd / cnc1.8.position-fb / cnc1.8.position-continuity | High-impedance (AM26C31 G held low by TX_PERMIT_B pull-downs); FPGA holds STEP low | High-impedance through the hardware permission path. Per IS-1 section 04 section 4: any interruption of an active path latches OUTPUT_PATH_INTERRUPTED and clears pos_continuity (joint unhomed); a rejected noise pulse never changes these pins | servo | TT-XM8-02 |
| 3 | M8_DIR_P | DIR+ differential | LOGIC_TX | RS-422 differential, 5 V-supplied AM26C31; differential output magnitude >= 2 V into 100 ohm (AM26C31 datasheet class; loaded value to be measured); rate <= min(board, gateware cap 195,312.5 steps/s at 50 MHz, configured timing, drive limit); 2 MHz/channel is an unqualified goal. Opto-input drives (e.g. DM542T V4 PUL/DIR, S2 set to 5 V) need the profile's compatibility test | FPGA DIR8_FPGA ball F3 | CMD.motor[8].rate / STS.motor[8].position / STS.pos_continuity bit 8 | cnc1.8.position-cmd / cnc1.8.position-fb / cnc1.8.position-continuity | High-impedance (AM26C31 G held low by TX_PERMIT_B pull-downs); FPGA holds STEP low | High-impedance through the hardware permission path. Per IS-1 section 04 section 4: any interruption of an active path latches OUTPUT_PATH_INTERRUPTED and clears pos_continuity (joint unhomed); a rejected noise pulse never changes these pins | servo | TT-XM8-03 |
| 4 | M8_DIR_N | DIR- differential | LOGIC_TX | RS-422 differential, 5 V-supplied AM26C31; differential output magnitude >= 2 V into 100 ohm (AM26C31 datasheet class; loaded value to be measured); rate <= min(board, gateware cap 195,312.5 steps/s at 50 MHz, configured timing, drive limit); 2 MHz/channel is an unqualified goal. Opto-input drives (e.g. DM542T V4 PUL/DIR, S2 set to 5 V) need the profile's compatibility test | FPGA DIR8_FPGA ball F3 | CMD.motor[8].rate / STS.motor[8].position / STS.pos_continuity bit 8 | cnc1.8.position-cmd / cnc1.8.position-fb / cnc1.8.position-continuity | High-impedance (AM26C31 G held low by TX_PERMIT_B pull-downs); FPGA holds STEP low | High-impedance through the hardware permission path. Per IS-1 section 04 section 4: any interruption of an active path latches OUTPUT_PATH_INTERRUPTED and clears pos_continuity (joint unhomed); a rejected noise pulse never changes these pins | servo | TT-XM8-04 |
| 5 | M8_SIG0V | Signal reference (LOGIC_GND) for STEP/DIR | LOGIC_TX | LOGIC_GND return for the RS-422 pairs; connect to the drive's signal common only if its input requires a reference | - | - | - | n/a | n/a | none | TT-XM8-05 |
| 6 | M8_SHIELD | Cable shield drain (chassis via SB1 rail) | CHASSIS | Chassis via base copper to SB1/XPE1; never a signal return | - | - | - | n/a | n/a | none | TT-XM8-06 |
| 7 | M8_NC_GAP | Not connected: creepage/clearance gap between LOGIC and floating/FIELD groups (plug position left empty) | NONE | No connection on the base; plug position left empty | - | - | - | n/a | n/a | none | TT-XM8-07 |
| 8 | M8_EN_NO | Enable switch, normally open (form A, TLP3640A). Wiring modes NO-sourced (AUX_24V -> drive EN+, drive EN- -> EN_NO, EN_COM -> AUX_RTN) or NO-drive (drive's own loop). Use for drives enabled by energising their input (servo SON). | ISO_SW | Floating photorelay contact, AC or DC, 0-30 V, <= 50 mA continuous per switch (IS-1 published rating, section 04 section 3.2); TLP3640A(TPL,E) form A: 60 V, 1 A, RON <= 0.3 ohm; TLP4176A(TP,F) form B: 60 V, 0.5 A, RON <= 2.5 ohm (datasheets via section 04) | FPGA EN8_N_FPGA ball N14 | STS.armed_mask bit 8 (per-channel enable follows the ARM channel_mask) / STS.enable_cmd_state bit 8 | cnc1.8.enable / cnc1.8.enable-commanded | OPEN (LED dark) | OPEN on command loss, TX_PERMIT loss, fault, self-test or LOGIC power loss | servo | TT-XM8-08 |
| 9 | M8_EN_COM | Enable switch common (shared by the NO and NC switch) | ISO_SW | Floating photorelay contact, AC or DC, 0-30 V, <= 50 mA continuous per switch (IS-1 published rating, section 04 section 3.2); TLP3640A(TPL,E) form A: 60 V, 1 A, RON <= 0.3 ohm; TLP4176A(TP,F) form B: 60 V, 0.5 A, RON <= 2.5 ohm (datasheets via section 04) | FPGA EN8_N_FPGA ball N14 | - | - | n/a (common) | n/a (common) | servo | TT-XM8-09 |
| 10 | M8_EN_NC | Enable switch, normally closed (form B, TLP4176A). Wiring mode NC-5V for the DM542T V4 reference drive: AUX_5V -> ENA+, ENA- -> EN_NC, EN_COM -> AUX_RTN; the drive is disabled while disarmed and on controller LOGIC power loss because AUX_5V comes from FIELD. Exceptions E1-E5 (section 04 section 3.4) are shown by the service. | ISO_SW | Floating photorelay contact, AC or DC, 0-30 V, <= 50 mA continuous per switch (IS-1 published rating, section 04 section 3.2); TLP3640A(TPL,E) form A: 60 V, 1 A, RON <= 0.3 ohm; TLP4176A(TP,F) form B: 60 V, 0.5 A, RON <= 2.5 ohm (datasheets via section 04) | FPGA EN8_N_FPGA ball N14 | STS.armed_mask bit 8 (per-channel enable follows the ARM channel_mask) / STS.enable_cmd_state bit 8 | cnc1.8.enable / cnc1.8.enable-commanded | CLOSED (LED dark) | CLOSED on command loss, TX_PERMIT loss, fault, self-test or LOGIC power loss | servo | TT-XM8-10 |
| 11 | M8_AUX_5V | AUX_5V: FIELD-derived 5 V loop supply for 5 V enable inputs (e.g. DM542T V4 ENA), current-limited per bank | FIELD_A | 5 V from FIELD_A, per-bank limit; load A 8 x 16 mA = 128 mA, B 64 mA (section 04 section 10.3) | - | STS.safety bit 15 | cnc1.safety.aux5-ok-b | On with FIELD_A (independent of LOGIC rails) | Limiter active: AUX5_OK_B low -> ARM refused / fault latched if armed; alarms of the bank read asserted (fail-closed) | servo | TT-XM8-11 |
| 12 | M8_AUX_24V | AUX_24V: FIELD 24 V loop supply for alarm outputs and 24 V enable loops, current-limited per bank | FIELD_A | 24 V from FIELD_A, limit min >= 1.1 x load, max <= 0.30 A (bank A) / 0.20 A (bank B); load A 0.148 A, B 0.074 A (section 04 section 10.3) | - | STS.safety bit 13 | cnc1.safety.aux24-ok-b | On with FIELD_A (independent of LOGIC rails) | Limiter active: AUX24_OK_B low -> ARM refused / fault latched if armed; alarms of the bank read asserted (fail-closed) | servo | TT-XM8-12 |
| 13 | M8_AUX_RTN | AUX return (FIELD_A 0 V) | FIELD_A | FIELD_A return for AUX loops and the alarm input | - | - | - | n/a | n/a | none | TT-XM8-13 |
| 14 | M8_ALM_IN | Drive alarm input (ISO1212 sinking, 24 V) | FIELD_A | Sinking 24 V input: AUX_24V -> drive ALM+, drive ALM- -> ALM_IN (or a sourcing alarm output with its 0 V on AUX_RTN); 0-30 V, low 0-5 V, high 15-30 V; 2.47 mA max (ISO1212, 562 ohm RSENSE); polarity per channel (alarm_on_no_current = 1 for DM542T V4) | FPGA ALM8_FPGA ball G13 | STS.alarm bit 8 / STS.alarm_latched bit 8 | cnc1.8.alarm / cnc1.8.alarm-latched | Ignored until endpoint qualification; ARM refused while asserted | Alarm on an armed channel in the trip mask disarms all channels (latched); open wire reads 'alarm' when alarm_on_no_current = 1 (fail-closed) | servo | TT-XM8-14 |

### XE0 (template for XE0-XE3 on the base; owner EIA)

ABZ encoder port ENC0. Keying: Encoder coding pattern distinct from motor and 24 V plugs (Codex coding profile). Cable: Shielded twisted pairs; shield drain to position 10 and SB1 clamp at the controller end.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ENC0_5V | Encoder +5 V supply (per-port limited) | LOGIC_ENC | 5 V +/-5 %, 200 mA normal load per port; TPS2553-1 threshold 207-284 mA (Codex encoder_power arithmetic) | - | STS.enc.fault bit 0 / TEL.eia.status_raw bit 16 | cnc1.encoder.0.supply-fault | Enabled after logic power-good; disabled while the card is unqualified | Latched off on overcurrent/thermal; channel reports 'encoder supply fault'; feedback marked invalid | telemetry | TT-XE0-01 |
| 2 | ENC0_0V | Encoder 0 V (LOGIC_GND) | LOGIC_ENC | LOGIC_GND return | - | - | - | n/a | n/a | none | TT-XE0-02 |
| 3 | ENC0_A_P | Encoder A+ | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC0_A_FPGA ball B5 | STS.enc[0].count / STS.enc.valid bit 0 / STS.enc.illegal bit 0 / STS.enc.fault bit 0 / STS.enc.index_armed bit 0 / CMD.enc.index_enable bit 0 / EVT.type INDEX_CAPTURE | cnc1.encoder.0.count / cnc1.encoder.0.position / cnc1.encoder.0.velocity / cnc1.encoder.0.index-enable / cnc1.encoder.0.valid / cnc1.encoder.0.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE0-03 |
| 4 | ENC0_A_N | Encoder A- | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC0_A_FPGA ball B5 | STS.enc[0].count / STS.enc.valid bit 0 / STS.enc.illegal bit 0 / STS.enc.fault bit 0 / STS.enc.index_armed bit 0 / CMD.enc.index_enable bit 0 / EVT.type INDEX_CAPTURE | cnc1.encoder.0.count / cnc1.encoder.0.position / cnc1.encoder.0.velocity / cnc1.encoder.0.index-enable / cnc1.encoder.0.valid / cnc1.encoder.0.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE0-04 |
| 5 | ENC0_B_P | Encoder B+ | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC0_B_FPGA ball A7 | STS.enc[0].count / STS.enc.valid bit 0 / STS.enc.illegal bit 0 / STS.enc.fault bit 0 / STS.enc.index_armed bit 0 / CMD.enc.index_enable bit 0 / EVT.type INDEX_CAPTURE | cnc1.encoder.0.count / cnc1.encoder.0.position / cnc1.encoder.0.velocity / cnc1.encoder.0.index-enable / cnc1.encoder.0.valid / cnc1.encoder.0.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE0-05 |
| 6 | ENC0_B_N | Encoder B- | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC0_B_FPGA ball A7 | STS.enc[0].count / STS.enc.valid bit 0 / STS.enc.illegal bit 0 / STS.enc.fault bit 0 / STS.enc.index_armed bit 0 / CMD.enc.index_enable bit 0 / EVT.type INDEX_CAPTURE | cnc1.encoder.0.count / cnc1.encoder.0.position / cnc1.encoder.0.velocity / cnc1.encoder.0.index-enable / cnc1.encoder.0.valid / cnc1.encoder.0.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE0-06 |
| 7 | ENC0_Z_P | Encoder Index+ | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC0_Z_FPGA ball B7 | STS.enc[0].count / STS.enc.valid bit 0 / STS.enc.illegal bit 0 / STS.enc.fault bit 0 / STS.enc.index_armed bit 0 / CMD.enc.index_enable bit 0 / EVT.type INDEX_CAPTURE | cnc1.encoder.0.count / cnc1.encoder.0.position / cnc1.encoder.0.velocity / cnc1.encoder.0.index-enable / cnc1.encoder.0.valid / cnc1.encoder.0.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE0-07 |
| 8 | ENC0_Z_N | Encoder Index- | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC0_Z_FPGA ball B7 | STS.enc[0].count / STS.enc.valid bit 0 / STS.enc.illegal bit 0 / STS.enc.fault bit 0 / STS.enc.index_armed bit 0 / CMD.enc.index_enable bit 0 / EVT.type INDEX_CAPTURE | cnc1.encoder.0.count / cnc1.encoder.0.position / cnc1.encoder.0.velocity / cnc1.encoder.0.index-enable / cnc1.encoder.0.valid / cnc1.encoder.0.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE0-08 |
| 9 | ENC0_0V2 | Encoder 0 V, second contact (sense/second cable) | LOGIC_ENC | LOGIC_GND return | - | - | - | n/a | n/a | none | TT-XE0-09 |
| 10 | ENC0_SHIELD | Shield drain | CHASSIS | Chassis via SB1 | - | - | - | n/a | n/a | none | TT-XE0-10 |

### XE4 (template for XE4-XE11 on XTB; owner EX8)

ABZ encoder port ENC4. Keying: Encoder coding pattern distinct from motor and 24 V plugs (Codex coding profile). Cable: Shielded twisted pairs; shield drain to position 10 and SB1 clamp at the controller end.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ENC4_5V | Encoder +5 V supply (per-port limited) | LOGIC_ENC | 5 V +/-5 %, 200 mA normal load per port; TPS2553-1 threshold 207-284 mA (Codex encoder_power arithmetic) | - | STS.enc.fault bit 4 / TEL.ex8.status_raw bit 0 | cnc1.encoder.4.supply-fault | Enabled after logic power-good; disabled while the card is unqualified | Latched off on overcurrent/thermal; channel reports 'encoder supply fault'; feedback marked invalid | telemetry | TT-XE4-01 |
| 2 | ENC4_0V | Encoder 0 V (LOGIC_GND) | LOGIC_ENC | LOGIC_GND return | - | - | - | n/a | n/a | none | TT-XE4-02 |
| 3 | ENC4_A_P | Encoder A+ | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC4_A_FPGA (ball unassigned) | STS.enc[4].count / STS.enc.valid bit 4 / STS.enc.illegal bit 4 / STS.enc.fault bit 4 / STS.enc.index_armed bit 4 / CMD.enc.index_enable bit 4 / EVT.type INDEX_CAPTURE | cnc1.encoder.4.count / cnc1.encoder.4.position / cnc1.encoder.4.velocity / cnc1.encoder.4.index-enable / cnc1.encoder.4.valid / cnc1.encoder.4.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE4-03 |
| 4 | ENC4_A_N | Encoder A- | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC4_A_FPGA (ball unassigned) | STS.enc[4].count / STS.enc.valid bit 4 / STS.enc.illegal bit 4 / STS.enc.fault bit 4 / STS.enc.index_armed bit 4 / CMD.enc.index_enable bit 4 / EVT.type INDEX_CAPTURE | cnc1.encoder.4.count / cnc1.encoder.4.position / cnc1.encoder.4.velocity / cnc1.encoder.4.index-enable / cnc1.encoder.4.valid / cnc1.encoder.4.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE4-04 |
| 5 | ENC4_B_P | Encoder B+ | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC4_B_FPGA (ball unassigned) | STS.enc[4].count / STS.enc.valid bit 4 / STS.enc.illegal bit 4 / STS.enc.fault bit 4 / STS.enc.index_armed bit 4 / CMD.enc.index_enable bit 4 / EVT.type INDEX_CAPTURE | cnc1.encoder.4.count / cnc1.encoder.4.position / cnc1.encoder.4.velocity / cnc1.encoder.4.index-enable / cnc1.encoder.4.valid / cnc1.encoder.4.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE4-05 |
| 6 | ENC4_B_N | Encoder B- | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC4_B_FPGA (ball unassigned) | STS.enc[4].count / STS.enc.valid bit 4 / STS.enc.illegal bit 4 / STS.enc.fault bit 4 / STS.enc.index_armed bit 4 / CMD.enc.index_enable bit 4 / EVT.type INDEX_CAPTURE | cnc1.encoder.4.count / cnc1.encoder.4.position / cnc1.encoder.4.velocity / cnc1.encoder.4.index-enable / cnc1.encoder.4.valid / cnc1.encoder.4.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE4-06 |
| 7 | ENC4_Z_P | Encoder Index+ | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC4_Z_FPGA (ball unassigned) | STS.enc[4].count / STS.enc.valid bit 4 / STS.enc.illegal bit 4 / STS.enc.fault bit 4 / STS.enc.index_armed bit 4 / CMD.enc.index_enable bit 4 / EVT.type INDEX_CAPTURE | cnc1.encoder.4.count / cnc1.encoder.4.position / cnc1.encoder.4.velocity / cnc1.encoder.4.index-enable / cnc1.encoder.4.valid / cnc1.encoder.4.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE4-07 |
| 8 | ENC4_Z_N | Encoder Index- | LOGIC_ENC | RS-422 differential, 120 ohm termination; goal 10,000,000 count transitions/s per port (unqualified); single-ended encoders need the listed adapter profile | FPGA ENC4_Z_FPGA (ball unassigned) | STS.enc[4].count / STS.enc.valid bit 4 / STS.enc.illegal bit 4 / STS.enc.fault bit 4 / STS.enc.index_armed bit 4 / CMD.enc.index_enable bit 4 / EVT.type INDEX_CAPTURE | cnc1.encoder.4.count / cnc1.encoder.4.position / cnc1.encoder.4.velocity / cnc1.encoder.4.index-enable / cnc1.encoder.4.valid / cnc1.encoder.4.fault | Counter held at 0 and marked invalid until qualification/SYNC | Illegal quadrature transition or receiver fail-safe state latches ENC fault; feedback marked invalid (commanded-vs-measured overlay shows 'stale/invalid') | servo | TT-XE4-08 |
| 9 | ENC4_0V2 | Encoder 0 V, second contact (sense/second cable) | LOGIC_ENC | LOGIC_GND return | - | - | - | n/a | n/a | none | TT-XE4-09 |
| 10 | ENC4_SHIELD | Shield drain | CHASSIS | Chassis via SB1 | - | - | - | n/a | n/a | none | TT-XE4-10 |

### XH1

MPG/handwheel encoder and enable button. Keying: Distinct coding from XE* encoder plugs (Codex). Cable: Pendant cable, shield to position 10.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MPG_5V | Handwheel +5 V supply | LOGIC_ENC | 5 V, 100 mA limit target (limiter with fault flag; Codex to select) | - | STS.mpg.select bit 13 | cnc1.mpg.supply-fault | On after logic power-good | Limited; handwheel counts marked invalid | telemetry | TT-XH1-01 |
| 2 | MPG_0V | Handwheel 0 V | LOGIC_ENC | LOGIC_GND return | - | - | - | n/a | n/a | none | TT-XH1-02 |
| 3 | MPG_A_P | Handwheel A+ | LOGIC_ENC | RS-422 differential or single-ended 5 V TTL with A-/B- linked to MPG_VREF; <= 100 kHz edge rate target | FPGA MPG_A_FPGA (ball unassigned) | STS.mpg.count / STS.mpg.status | cnc1.mpg.counts / cnc1.mpg.valid | Counts ignored until MPG_ENABLE and a selected axis | Counts frozen and marked invalid; never converted into motion when invalid | servo | TT-XH1-03 |
| 4 | MPG_A_N | Handwheel A- | LOGIC_ENC | RS-422 differential or single-ended 5 V TTL with A-/B- linked to MPG_VREF; <= 100 kHz edge rate target | FPGA MPG_A_FPGA (ball unassigned) | STS.mpg.count / STS.mpg.status | cnc1.mpg.counts / cnc1.mpg.valid | Counts ignored until MPG_ENABLE and a selected axis | Counts frozen and marked invalid; never converted into motion when invalid | servo | TT-XH1-04 |
| 5 | MPG_B_P | Handwheel B+ | LOGIC_ENC | RS-422 differential or single-ended 5 V TTL with A-/B- linked to MPG_VREF; <= 100 kHz edge rate target | FPGA MPG_B_FPGA (ball unassigned) | STS.mpg.count / STS.mpg.status | cnc1.mpg.counts / cnc1.mpg.valid | Counts ignored until MPG_ENABLE and a selected axis | Counts frozen and marked invalid; never converted into motion when invalid | servo | TT-XH1-05 |
| 6 | MPG_B_N | Handwheel B- | LOGIC_ENC | RS-422 differential or single-ended 5 V TTL with A-/B- linked to MPG_VREF; <= 100 kHz edge rate target | FPGA MPG_B_FPGA (ball unassigned) | STS.mpg.count / STS.mpg.status | cnc1.mpg.counts / cnc1.mpg.valid | Counts ignored until MPG_ENABLE and a selected axis | Counts frozen and marked invalid; never converted into motion when invalid | servo | TT-XH1-06 |
| 7 | MPG_VREF | 2.5 V bias for single-ended handwheels (link A- and B- here) | LOGIC_ENC | 2.5 V reference, 1 mA max, resistor-fed | - | - | - | Present with logic power | n/a | none | TT-XH1-07 |
| 8 | MPG_ENABLE | Pendant enable/deadman button input (to MPG_0V = active) | LOGIC_ENC | Contact to MPG_0V, internal pull-up to 5 V | serial EIA.status bit 10 | STS.mpg.select bit 10 | cnc1.mpg.enable | Reads released | Reads released (fail-safe: no jog) | servo | TT-XH1-08 |
| 9 | MPG_0V2 | Handwheel 0 V, second contact | LOGIC_ENC | LOGIC_GND return | - | - | - | n/a | n/a | none | TT-XH1-09 |
| 10 | MPG_SHIELD | Shield drain | CHASSIS | Chassis via SB1 | - | - | - | n/a | n/a | none | TT-XH1-10 |

### XH2

Pendant selector switches (axis, multiplier, auxiliary). Keying: Distinct coding from motor XM* plugs (same position count, different coding). Cable: Pendant cable.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MPG_SEL_X | Pendant selector input SEL_X (contact to SW_COM = active) | LOGIC_ENC | 5 V logic contact input, pull-up to 5 V, switch to SW_COM (0 V); not a 24 V input | serial EIA.status bit 0 | STS.mpg.select bit 0 | cnc1.mpg.sel-x | Reads inactive | Reads inactive (no axis selected: handwheel ignored) | servo | TT-XH2-01 |
| 2 | MPG_SEL_Y | Pendant selector input SEL_Y (contact to SW_COM = active) | LOGIC_ENC | 5 V logic contact input, pull-up to 5 V, switch to SW_COM (0 V); not a 24 V input | serial EIA.status bit 1 | STS.mpg.select bit 1 | cnc1.mpg.sel-y | Reads inactive | Reads inactive (no axis selected: handwheel ignored) | servo | TT-XH2-02 |
| 3 | MPG_SEL_Z | Pendant selector input SEL_Z (contact to SW_COM = active) | LOGIC_ENC | 5 V logic contact input, pull-up to 5 V, switch to SW_COM (0 V); not a 24 V input | serial EIA.status bit 2 | STS.mpg.select bit 2 | cnc1.mpg.sel-z | Reads inactive | Reads inactive (no axis selected: handwheel ignored) | servo | TT-XH2-03 |
| 4 | MPG_SEL_A | Pendant selector input SEL_A (contact to SW_COM = active) | LOGIC_ENC | 5 V logic contact input, pull-up to 5 V, switch to SW_COM (0 V); not a 24 V input | serial EIA.status bit 3 | STS.mpg.select bit 3 | cnc1.mpg.sel-a | Reads inactive | Reads inactive (no axis selected: handwheel ignored) | servo | TT-XH2-04 |
| 5 | MPG_SEL_B | Pendant selector input SEL_B (contact to SW_COM = active) | LOGIC_ENC | 5 V logic contact input, pull-up to 5 V, switch to SW_COM (0 V); not a 24 V input | serial EIA.status bit 4 | STS.mpg.select bit 4 | cnc1.mpg.sel-b | Reads inactive | Reads inactive (no axis selected: handwheel ignored) | servo | TT-XH2-05 |
| 6 | MPG_SEL_C | Pendant selector input SEL_C (contact to SW_COM = active) | LOGIC_ENC | 5 V logic contact input, pull-up to 5 V, switch to SW_COM (0 V); not a 24 V input | serial EIA.status bit 5 | STS.mpg.select bit 5 | cnc1.mpg.sel-c | Reads inactive | Reads inactive (no axis selected: handwheel ignored) | servo | TT-XH2-06 |
| 7 | MPG_MUL_X1 | Pendant selector input MUL_X1 (contact to SW_COM = active) | LOGIC_ENC | 5 V logic contact input, pull-up to 5 V, switch to SW_COM (0 V); not a 24 V input | serial EIA.status bit 6 | STS.mpg.select bit 6 | cnc1.mpg.mul-x1 | Reads inactive | Reads inactive (no axis selected: handwheel ignored) | servo | TT-XH2-07 |
| 8 | MPG_MUL_X10 | Pendant selector input MUL_X10 (contact to SW_COM = active) | LOGIC_ENC | 5 V logic contact input, pull-up to 5 V, switch to SW_COM (0 V); not a 24 V input | serial EIA.status bit 7 | STS.mpg.select bit 7 | cnc1.mpg.mul-x10 | Reads inactive | Reads inactive (no axis selected: handwheel ignored) | servo | TT-XH2-08 |
| 9 | MPG_MUL_X100 | Pendant selector input MUL_X100 (contact to SW_COM = active) | LOGIC_ENC | 5 V logic contact input, pull-up to 5 V, switch to SW_COM (0 V); not a 24 V input | serial EIA.status bit 8 | STS.mpg.select bit 8 | cnc1.mpg.mul-x100 | Reads inactive | Reads inactive (no axis selected: handwheel ignored) | servo | TT-XH2-09 |
| 10 | MPG_PEND_AUX | Pendant selector input PEND_AUX (contact to SW_COM = active) | LOGIC_ENC | 5 V logic contact input, pull-up to 5 V, switch to SW_COM (0 V); not a 24 V input | serial EIA.status bit 9 | STS.mpg.select bit 9 | cnc1.mpg.pend-aux | Reads inactive | Reads inactive (no axis selected: handwheel ignored) | servo | TT-XH2-10 |
| 11 | MPG_SW_COM | Selector switch common (0 V) | LOGIC_ENC | LOGIC_GND | - | - | - | n/a | n/a | none | TT-XH2-11 |
| 12 | MPG_SEL_SHIELD | Shield drain | CHASSIS | Chassis via SB1 | - | - | - | n/a | n/a | none | TT-XH2-12 |

### XDI0

General inputs DI0-DI7 with group sensor supply. Keying: Coding distinct from XDO* and XM* (Codex). Cable: Unshielded field wiring acceptable; 3-wire PNP sensors take +24 V and 0 V from this plug.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | DI00 | General input DI0 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 0 | STS.din bit 0 / STS.din_valid | cnc1.din.0 / cnc1.din.0-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI0-01 |
| 2 | DI01 | General input DI1 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 1 | STS.din bit 1 / STS.din_valid | cnc1.din.1 / cnc1.din.1-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI0-02 |
| 3 | DI02 | General input DI2 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 2 | STS.din bit 2 / STS.din_valid | cnc1.din.2 / cnc1.din.2-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI0-03 |
| 4 | DI03 | General input DI3 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 3 | STS.din bit 3 / STS.din_valid | cnc1.din.3 / cnc1.din.3-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI0-04 |
| 5 | DI04 | General input DI4 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 4 | STS.din bit 4 / STS.din_valid | cnc1.din.4 / cnc1.din.4-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI0-05 |
| 6 | DI05 | General input DI5 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 5 | STS.din bit 5 / STS.din_valid | cnc1.din.5 / cnc1.din.5-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI0-06 |
| 7 | DI06 | General input DI6 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 6 | STS.din bit 6 / STS.din_valid | cnc1.din.6 / cnc1.din.6-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI0-07 |
| 8 | DI07 | General input DI7 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 7 | STS.din bit 7 / STS.din_valid | cnc1.din.7 / cnc1.din.7-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI0-08 |
| 9 | SENS24_G0 | Sensor supply +24 V group 0 | FIELD_B | +24 V from FIELD_B through a group current limiter, 0.20 A per group (3 groups 0.60 A + safety branch 0.15 A = the 0.75 A sensor allowance of section 04 section 10.2) | - | TEL.dic.sensor_group[0].mv / TEL.dic.limiter_fault bit 0 / STS.port[L0_DIC] | cnc1.supply.sensor-0.voltage / cnc1.supply.sensor-0.fault | On with FIELD_A | Limited; group inputs flagged 'sensor supply fault' | telemetry | TT-XDI0-09 |
| 10 | SENS24_G0b | Sensor supply +24 V group 0, second contact | FIELD_B | +24 V from FIELD_B through a group current limiter, 0.20 A per group (3 groups 0.60 A + safety branch 0.15 A = the 0.75 A sensor allowance of section 04 section 10.2) | - | TEL.dic.sensor_group[0].mv / TEL.dic.limiter_fault bit 0 / STS.port[L0_DIC] | cnc1.supply.sensor-0.voltage / cnc1.supply.sensor-0.fault | On with FIELD_A | Limited; group inputs flagged 'sensor supply fault' | telemetry | TT-XDI0-10 |
| 11 | FIELD_B_0V_DI0_11 | Field 0 V for sensors | FIELD_B | FIELD_B return | - | - | - | n/a | n/a | none | TT-XDI0-11 |
| 12 | FIELD_B_0V_DI0_12 | Field 0 V for sensors | FIELD_B | FIELD_B return | - | - | - | n/a | n/a | none | TT-XDI0-12 |

### XDI1

General inputs DI8-DI15 with group sensor supply. Keying: Coding distinct from XDO* and XM* (Codex). Cable: Unshielded field wiring acceptable; 3-wire PNP sensors take +24 V and 0 V from this plug.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | DI08 | General input DI8 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 8 | STS.din bit 8 / STS.din_valid | cnc1.din.8 / cnc1.din.8-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI1-01 |
| 2 | DI09 | General input DI9 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 9 | STS.din bit 9 / STS.din_valid | cnc1.din.9 / cnc1.din.9-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI1-02 |
| 3 | DI10 | General input DI10 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 10 | STS.din bit 10 / STS.din_valid | cnc1.din.10 / cnc1.din.10-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI1-03 |
| 4 | DI11 | General input DI11 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 11 | STS.din bit 11 / STS.din_valid | cnc1.din.11 / cnc1.din.11-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI1-04 |
| 5 | DI12 | General input DI12 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 12 | STS.din bit 12 / STS.din_valid | cnc1.din.12 / cnc1.din.12-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI1-05 |
| 6 | DI13 | General input DI13 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 13 | STS.din bit 13 / STS.din_valid | cnc1.din.13 / cnc1.din.13-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI1-06 |
| 7 | DI14 | General input DI14 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 14 | STS.din bit 14 / STS.din_valid | cnc1.din.14 / cnc1.din.14-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI1-07 |
| 8 | DI15 | General input DI15 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 15 | STS.din bit 15 / STS.din_valid | cnc1.din.15 / cnc1.din.15-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI1-08 |
| 9 | SENS24_G1 | Sensor supply +24 V group 1 | FIELD_B | +24 V from FIELD_B through a group current limiter, 0.20 A per group (3 groups 0.60 A + safety branch 0.15 A = the 0.75 A sensor allowance of section 04 section 10.2) | - | TEL.dic.sensor_group[1].mv / TEL.dic.limiter_fault bit 1 / STS.port[L0_DIC] | cnc1.supply.sensor-1.voltage / cnc1.supply.sensor-1.fault | On with FIELD_A | Limited; group inputs flagged 'sensor supply fault' | telemetry | TT-XDI1-09 |
| 10 | SENS24_G1b | Sensor supply +24 V group 1, second contact | FIELD_B | +24 V from FIELD_B through a group current limiter, 0.20 A per group (3 groups 0.60 A + safety branch 0.15 A = the 0.75 A sensor allowance of section 04 section 10.2) | - | TEL.dic.sensor_group[1].mv / TEL.dic.limiter_fault bit 1 / STS.port[L0_DIC] | cnc1.supply.sensor-1.voltage / cnc1.supply.sensor-1.fault | On with FIELD_A | Limited; group inputs flagged 'sensor supply fault' | telemetry | TT-XDI1-10 |
| 11 | FIELD_B_0V_DI1_11 | Field 0 V for sensors | FIELD_B | FIELD_B return | - | - | - | n/a | n/a | none | TT-XDI1-11 |
| 12 | FIELD_B_0V_DI1_12 | Field 0 V for sensors | FIELD_B | FIELD_B return | - | - | - | n/a | n/a | none | TT-XDI1-12 |

### XDI2

General inputs DI16-DI23 with group sensor supply. Keying: Coding distinct from XDO* and XM* (Codex). Cable: Unshielded field wiring acceptable; 3-wire PNP sensors take +24 V and 0 V from this plug.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | DI16 | General input DI16 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 16 | STS.din bit 16 / STS.din_valid | cnc1.din.16 / cnc1.din.16-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI2-01 |
| 2 | DI17 | General input DI17 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 17 | STS.din bit 17 / STS.din_valid | cnc1.din.17 / cnc1.din.17-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI2-02 |
| 3 | DI18 | General input DI18 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 18 | STS.din bit 18 / STS.din_valid | cnc1.din.18 / cnc1.din.18-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI2-03 |
| 4 | DI19 | General input DI19 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 19 | STS.din bit 19 / STS.din_valid | cnc1.din.19 / cnc1.din.19-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI2-04 |
| 5 | DI20 | General input DI20 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 20 | STS.din bit 20 / STS.din_valid | cnc1.din.20 / cnc1.din.20-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI2-05 |
| 6 | DI21 | General input DI21 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 21 | STS.din bit 21 / STS.din_valid | cnc1.din.21 / cnc1.din.21-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI2-06 |
| 7 | DI22 | General input DI22 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 22 | STS.din bit 22 / STS.din_valid | cnc1.din.22 / cnc1.din.22-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI2-07 |
| 8 | DI23 | General input DI23 | FIELD_B | Sinking 24 V input (PNP sensor or contact to SENS_24V), 0-30 V, low 0-5 V, high 15-30 V; ~2.25 mA typ; NPN/AC need adapters | serial DIC bit 23 | STS.din bit 23 / STS.din_valid | cnc1.din.23 / cnc1.din.23-not / cnc1.din-valid | Reported invalid until the DI link has delivered a fully validated frame | Link stale or CRC/sequence error: all DI marked invalid; profile hold/inhibit policy applies (never read as 'low') | servo | TT-XDI2-08 |
| 9 | SENS24_G2 | Sensor supply +24 V group 2 | FIELD_B | +24 V from FIELD_B through a group current limiter, 0.20 A per group (3 groups 0.60 A + safety branch 0.15 A = the 0.75 A sensor allowance of section 04 section 10.2) | - | TEL.dic.sensor_group[2].mv / TEL.dic.limiter_fault bit 2 / STS.port[L0_DIC] | cnc1.supply.sensor-2.voltage / cnc1.supply.sensor-2.fault | On with FIELD_A | Limited; group inputs flagged 'sensor supply fault' | telemetry | TT-XDI2-09 |
| 10 | SENS24_G2b | Sensor supply +24 V group 2, second contact | FIELD_B | +24 V from FIELD_B through a group current limiter, 0.20 A per group (3 groups 0.60 A + safety branch 0.15 A = the 0.75 A sensor allowance of section 04 section 10.2) | - | TEL.dic.sensor_group[2].mv / TEL.dic.limiter_fault bit 2 / STS.port[L0_DIC] | cnc1.supply.sensor-2.voltage / cnc1.supply.sensor-2.fault | On with FIELD_A | Limited; group inputs flagged 'sensor supply fault' | telemetry | TT-XDI2-10 |
| 11 | FIELD_B_0V_DI2_11 | Field 0 V for sensors | FIELD_B | FIELD_B return | - | - | - | n/a | n/a | none | TT-XDI2-11 |
| 12 | FIELD_B_0V_DI2_12 | Field 0 V for sensors | FIELD_B | FIELD_B return | - | - | - | n/a | n/a | none | TT-XDI2-12 |

### XDO0

General sourcing outputs DO0-DO7. Keying: Coding distinct from XDI* (Codex). Cable: Load wiring; inductive loads need no external diode (integrated clamp) but must stay within clamp energy.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | DO00 | General sourcing output DO0 | FIELD_A | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOA bit 0 | CMD.dout bit 0 / STS.dout_readback bit 0 / STS.dout_fault bit 0 / EVT.type OUTPUT_FAULT / TEL.dout[0].current / TEL.dout[0].temperature / TEL.dout[0].vout | cnc1.dout.0 / cnc1.dout.0-applied / cnc1.dout.0-fault / cnc1.dout.0-current / cnc1.dout.0-current-valid / cnc1.dout.0-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO0-01 |
| 2 | DO01 | General sourcing output DO1 | FIELD_A | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOA bit 1 | CMD.dout bit 1 / STS.dout_readback bit 1 / STS.dout_fault bit 1 / EVT.type OUTPUT_FAULT / TEL.dout[1].current / TEL.dout[1].temperature / TEL.dout[1].vout | cnc1.dout.1 / cnc1.dout.1-applied / cnc1.dout.1-fault / cnc1.dout.1-current / cnc1.dout.1-current-valid / cnc1.dout.1-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO0-02 |
| 3 | DO02 | General sourcing output DO2 | FIELD_A | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOA bit 2 | CMD.dout bit 2 / STS.dout_readback bit 2 / STS.dout_fault bit 2 / EVT.type OUTPUT_FAULT / TEL.dout[2].current / TEL.dout[2].temperature / TEL.dout[2].vout | cnc1.dout.2 / cnc1.dout.2-applied / cnc1.dout.2-fault / cnc1.dout.2-current / cnc1.dout.2-current-valid / cnc1.dout.2-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO0-03 |
| 4 | DO03 | General sourcing output DO3 | FIELD_A | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOA bit 3 | CMD.dout bit 3 / STS.dout_readback bit 3 / STS.dout_fault bit 3 / EVT.type OUTPUT_FAULT / TEL.dout[3].current / TEL.dout[3].temperature / TEL.dout[3].vout | cnc1.dout.3 / cnc1.dout.3-applied / cnc1.dout.3-fault / cnc1.dout.3-current / cnc1.dout.3-current-valid / cnc1.dout.3-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO0-04 |
| 5 | DO04 | General sourcing output DO4 | FIELD_A | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOA bit 4 | CMD.dout bit 4 / STS.dout_readback bit 4 / STS.dout_fault bit 4 / EVT.type OUTPUT_FAULT / TEL.dout[4].current / TEL.dout[4].temperature / TEL.dout[4].vout | cnc1.dout.4 / cnc1.dout.4-applied / cnc1.dout.4-fault / cnc1.dout.4-current / cnc1.dout.4-current-valid / cnc1.dout.4-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO0-05 |
| 6 | DO05 | General sourcing output DO5 | FIELD_A | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOA bit 5 | CMD.dout bit 5 / STS.dout_readback bit 5 / STS.dout_fault bit 5 / EVT.type OUTPUT_FAULT / TEL.dout[5].current / TEL.dout[5].temperature / TEL.dout[5].vout | cnc1.dout.5 / cnc1.dout.5-applied / cnc1.dout.5-fault / cnc1.dout.5-current / cnc1.dout.5-current-valid / cnc1.dout.5-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO0-06 |
| 7 | DO06 | General sourcing output DO6 | FIELD_A | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOA bit 6 | CMD.dout bit 6 / STS.dout_readback bit 6 / STS.dout_fault bit 6 / EVT.type OUTPUT_FAULT / TEL.dout[6].current / TEL.dout[6].temperature / TEL.dout[6].vout | cnc1.dout.6 / cnc1.dout.6-applied / cnc1.dout.6-fault / cnc1.dout.6-current / cnc1.dout.6-current-valid / cnc1.dout.6-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO0-07 |
| 8 | DO07 | General sourcing output DO7 | FIELD_A | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOA bit 7 | CMD.dout bit 7 / STS.dout_readback bit 7 / STS.dout_fault bit 7 / EVT.type OUTPUT_FAULT / TEL.dout[7].current / TEL.dout[7].temperature / TEL.dout[7].vout | cnc1.dout.7 / cnc1.dout.7-applied / cnc1.dout.7-fault / cnc1.dout.7-current / cnc1.dout.7-current-valid / cnc1.dout.7-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO0-08 |
| 9 | FIELD_A_0V_DO0_9 | Load return (field 0 V) | FIELD_A | FIELD_A return; 2 outputs per return contact (1.0 A max per contact, arithmetic) | - | - | - | n/a | n/a | none | TT-XDO0-09 |
| 10 | FIELD_A_0V_DO0_10 | Load return (field 0 V) | FIELD_A | FIELD_A return; 2 outputs per return contact (1.0 A max per contact, arithmetic) | - | - | - | n/a | n/a | none | TT-XDO0-10 |
| 11 | FIELD_A_0V_DO0_11 | Load return (field 0 V) | FIELD_A | FIELD_A return; 2 outputs per return contact (1.0 A max per contact, arithmetic) | - | - | - | n/a | n/a | none | TT-XDO0-11 |
| 12 | FIELD_A_0V_DO0_12 | Load return (field 0 V) | FIELD_A | FIELD_A return; 2 outputs per return contact (1.0 A max per contact, arithmetic) | - | - | - | n/a | n/a | none | TT-XDO0-12 |

### XDO1

General sourcing outputs DO8-DO15. Keying: Coding distinct from XDI* (Codex). Cable: Load wiring; inductive loads need no external diode (integrated clamp) but must stay within clamp energy.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | DO08 | General sourcing output DO8 | FIELD_B | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOB bit 8 | CMD.dout bit 8 / STS.dout_readback bit 8 / STS.dout_fault bit 8 / EVT.type OUTPUT_FAULT / TEL.dout[8].current / TEL.dout[8].temperature / TEL.dout[8].vout | cnc1.dout.8 / cnc1.dout.8-applied / cnc1.dout.8-fault / cnc1.dout.8-current / cnc1.dout.8-current-valid / cnc1.dout.8-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO1-01 |
| 2 | DO09 | General sourcing output DO9 | FIELD_B | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOB bit 9 | CMD.dout bit 9 / STS.dout_readback bit 9 / STS.dout_fault bit 9 / EVT.type OUTPUT_FAULT / TEL.dout[9].current / TEL.dout[9].temperature / TEL.dout[9].vout | cnc1.dout.9 / cnc1.dout.9-applied / cnc1.dout.9-fault / cnc1.dout.9-current / cnc1.dout.9-current-valid / cnc1.dout.9-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO1-02 |
| 3 | DO10 | General sourcing output DO10 | FIELD_B | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOB bit 10 | CMD.dout bit 10 / STS.dout_readback bit 10 / STS.dout_fault bit 10 / EVT.type OUTPUT_FAULT / TEL.dout[10].current / TEL.dout[10].temperature / TEL.dout[10].vout | cnc1.dout.10 / cnc1.dout.10-applied / cnc1.dout.10-fault / cnc1.dout.10-current / cnc1.dout.10-current-valid / cnc1.dout.10-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO1-03 |
| 4 | DO11 | General sourcing output DO11 | FIELD_B | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOB bit 11 | CMD.dout bit 11 / STS.dout_readback bit 11 / STS.dout_fault bit 11 / EVT.type OUTPUT_FAULT / TEL.dout[11].current / TEL.dout[11].temperature / TEL.dout[11].vout | cnc1.dout.11 / cnc1.dout.11-applied / cnc1.dout.11-fault / cnc1.dout.11-current / cnc1.dout.11-current-valid / cnc1.dout.11-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO1-04 |
| 5 | DO12 | General sourcing output DO12 | FIELD_B | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOB bit 12 | CMD.dout bit 12 / STS.dout_readback bit 12 / STS.dout_fault bit 12 / EVT.type OUTPUT_FAULT / TEL.dout[12].current / TEL.dout[12].temperature / TEL.dout[12].vout | cnc1.dout.12 / cnc1.dout.12-applied / cnc1.dout.12-fault / cnc1.dout.12-current / cnc1.dout.12-current-valid / cnc1.dout.12-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO1-05 |
| 6 | DO13 | General sourcing output DO13 | FIELD_B | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOB bit 13 | CMD.dout bit 13 / STS.dout_readback bit 13 / STS.dout_fault bit 13 / EVT.type OUTPUT_FAULT / TEL.dout[13].current / TEL.dout[13].temperature / TEL.dout[13].vout | cnc1.dout.13 / cnc1.dout.13-applied / cnc1.dout.13-fault / cnc1.dout.13-current / cnc1.dout.13-current-valid / cnc1.dout.13-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO1-06 |
| 7 | DO14 | General sourcing output DO14 | FIELD_B | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOB bit 14 | CMD.dout bit 14 / STS.dout_readback bit 14 / STS.dout_fault bit 14 / EVT.type OUTPUT_FAULT / TEL.dout[14].current / TEL.dout[14].temperature / TEL.dout[14].vout | cnc1.dout.14 / cnc1.dout.14-applied / cnc1.dout.14-fault / cnc1.dout.14-current / cnc1.dout.14-current-valid / cnc1.dout.14-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO1-07 |
| 8 | DO15 | General sourcing output DO15 | FIELD_B | High-side switched +24 V (18-30 V), 0.5 A continuous per channel, 2.0 A continuous per 4-output group, driver current-limit maximum <= 1.0 A (section 04 section 10.2); TPS274C65ASRHAR (72 mohm, SPI; the T1 selection of section 02 section 11.2), default current-limit setting 0.72 A (0.62-0.82 A, datasheet) | serial DOB bit 15 | CMD.dout bit 15 / STS.dout_readback bit 15 / STS.dout_fault bit 15 / EVT.type OUTPUT_FAULT / TEL.dout[15].current / TEL.dout[15].temperature / TEL.dout[15].vout | cnc1.dout.15 / cnc1.dout.15-applied / cnc1.dout.15-fault / cnc1.dout.15-current / cnc1.dout.15-current-valid / cnc1.dout.15-current-age | OFF (device default off; card watchdog holds off until the first validated frame) | OFF (de-energised) on channel fault (latched until cleared by service action), on card-watchdog expiry (<= 2 ms, advances only on fully accepted transactions) or on OUT_PERMIT loss (hardwired, never inside the serial link); no hold-last-value state; clearing never re-energises without a new command | servo | TT-XDO1-08 |
| 9 | FIELD_B_0V_DO1_9 | Load return (field 0 V) | FIELD_B | FIELD_B return; 2 outputs per return contact (1.0 A max per contact, arithmetic) | - | - | - | n/a | n/a | none | TT-XDO1-09 |
| 10 | FIELD_B_0V_DO1_10 | Load return (field 0 V) | FIELD_B | FIELD_B return; 2 outputs per return contact (1.0 A max per contact, arithmetic) | - | - | - | n/a | n/a | none | TT-XDO1-10 |
| 11 | FIELD_B_0V_DO1_11 | Load return (field 0 V) | FIELD_B | FIELD_B return; 2 outputs per return contact (1.0 A max per contact, arithmetic) | - | - | - | n/a | n/a | none | TT-XDO1-11 |
| 12 | FIELD_B_0V_DO1_12 | Load return (field 0 V) | FIELD_B | FIELD_B return; 2 outputs per return contact (1.0 A max per contact, arithmetic) | - | - | - | n/a | n/a | none | TT-XDO1-12 |

### XPR

Two fast probe inputs with typed sensor supplies. Keying: Coding distinct from XF (Codex). Cable: Shielded cable, shield to SB1 clamp.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PRB0_IN | Fast probe input PRB0 | FIELD_A | 24 V PNP or dry contact to PRB0_24V; ISO1212 propagation 140 ns max L->H (datasheet via Codex digital_inputs design.json); capture latency/jitter to be measured | FPGA PRB0_FPGA ball G12 | STS.probe.state / CMD.probe.arm / EVT.type PROBE_CAPTURE | cnc1.probe.0.in / cnc1.probe.0.captured / cnc1.probe.0.capture-seq / cnc1.probe.0.capture-value.0 | Capture disarmed; state reported invalid until qualified | Capture overrun or stale capture latched and reported; LinuxCNC probe input forced to the configured fail state (probe tripped) | servo | TT-XPR-01 |
| 2 | PRB0_24V | Probe 0 sensor supply +24 V | FIELD_A | +24 V, 100 mA limit target | - | STS.mpg.select bit 14 | cnc1.supply.probe-0.fault | On with FIELD_A | Limited; probe input flagged invalid | telemetry | TT-XPR-02 |
| 3 | PRB0_0V | Probe 0 0 V | FIELD_A | FIELD_A return | - | - | - | n/a | n/a | none | TT-XPR-03 |
| 4 | PRB1_IN | Fast probe input PRB1 | FIELD_A | 24 V PNP or dry contact to PRB1_24V; ISO1212 propagation 140 ns max L->H (datasheet via Codex digital_inputs design.json); capture latency/jitter to be measured | FPGA PRB1_FPGA ball G15 | STS.probe.state / CMD.probe.arm / EVT.type PROBE_CAPTURE | cnc1.probe.1.in / cnc1.probe.1.captured / cnc1.probe.1.capture-seq / cnc1.probe.1.capture-value.0 | Capture disarmed; state reported invalid until qualified | Capture overrun or stale capture latched and reported; LinuxCNC probe input forced to the configured fail state (probe tripped) | servo | TT-XPR-04 |
| 5 | PRB1_24V | Probe 1 sensor supply +24 V | FIELD_A | +24 V, 100 mA limit target | - | STS.mpg.select bit 15 | cnc1.supply.probe-1.fault | On with FIELD_A | Limited; probe input flagged invalid | telemetry | TT-XPR-05 |
| 6 | PRB1_0V | Probe 1 0 V | FIELD_A | FIELD_A return | - | - | - | n/a | n/a | none | TT-XPR-06 |

### XF

Two differential frequency inputs + measurement-module presence/identity (plasma divided-voltage module, THCAD-class). Keying: Unique coding: measurement-module plug only. Cable: Shielded twisted pairs.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FREQ_5V | Measurement-module +5 V supply | LOGIC_ENC | 5 V, 150 mA limit target (THCAD-class modules are 5 V powered) | - | STS.mpg.select bit 12 | cnc1.freq.supply-fault | Off until a module is present and configured | Off; frequency readings invalid | telemetry | TT-XF-01 |
| 2 | FREQ_0V | Measurement-module 0 V | LOGIC_ENC | LOGIC_GND return | - | - | - | n/a | n/a | none | TT-XF-02 |
| 3 | FREQ0_P | Frequency input FREQ0+ | LOGIC_ENC | >= 1 MHz input goal with margin (unqualified); gate/period modes set in configuration | FPGA FREQ0_FPGA (ball unassigned) | STS.freq[0].count / STS.freq[0].last_edge | cnc1.freq.0.frequency / cnc1.freq.0.valid / cnc1.freq.0.age | Reported invalid until the first complete gate | Edge timeout or overflow: reading invalid (never zero); plasma THC hold per profile | servo | TT-XF-03 |
| 4 | FREQ0_N | Frequency input FREQ0- | LOGIC_ENC | >= 1 MHz input goal with margin (unqualified); gate/period modes set in configuration | FPGA FREQ0_FPGA (ball unassigned) | STS.freq[0].count / STS.freq[0].last_edge | cnc1.freq.0.frequency / cnc1.freq.0.valid / cnc1.freq.0.age | Reported invalid until the first complete gate | Edge timeout or overflow: reading invalid (never zero); plasma THC hold per profile | servo | TT-XF-04 |
| 5 | FREQ1_P | Frequency input FREQ1+ | LOGIC_ENC | >= 1 MHz input goal with margin (unqualified); gate/period modes set in configuration | FPGA FREQ1_FPGA (ball unassigned) | STS.freq[1].count / STS.freq[1].last_edge | cnc1.freq.1.frequency / cnc1.freq.1.valid / cnc1.freq.1.age | Reported invalid until the first complete gate | Edge timeout or overflow: reading invalid (never zero); plasma THC hold per profile | servo | TT-XF-05 |
| 6 | FREQ1_N | Frequency input FREQ1- | LOGIC_ENC | >= 1 MHz input goal with margin (unqualified); gate/period modes set in configuration | FPGA FREQ1_FPGA (ball unassigned) | STS.freq[1].count / STS.freq[1].last_edge | cnc1.freq.1.frequency / cnc1.freq.1.valid / cnc1.freq.1.age | Reported invalid until the first complete gate | Edge timeout or overflow: reading invalid (never zero); plasma THC hold per profile | servo | TT-XF-06 |
| 7 | MOD_ID | Module identity line (1-Wire EEPROM in a passive module) | LOGIC_ENC | 1-Wire open-drain, 5 V tolerant | host: EIA identity bus (I2C-to-1-Wire bridge on EIA; read by host at qualification) | HOST.onewire.xf.identity | cnc1.freq.module-id-valid | Read once at qualification | Unknown/unreadable identity: plasma profile unavailable, torch permission withheld | event | TT-XF-07 |
| 8 | MOD_PRESENT | Module presence (looped to FREQ_0V in the module plug) | LOGIC_ENC | Pull-up; module loops to 0 V | serial EIA.status bit 11 | STS.mpg.select bit 11 / STS.slots bit 4 | cnc1.freq.module-present | Read at qualification | A presence change while powered raises a SLOT_CHANGE event (source 0x20, XF module) and makes cnc1.freq.* invalid; the plasma profile holds the torch-start request at zero until a power cycle and re-verification of the module identity | servo | TT-XF-08 |
| 9 | FREQ_0V2 | Module 0 V, second contact | LOGIC_ENC | LOGIC_GND return | - | - | - | n/a | n/a | none | TT-XF-09 |
| 10 | FREQ_SHIELD | Shield drain | CHASSIS | Chassis via SB1 | - | - | - | n/a | n/a | none | TT-XF-10 |

### XPW

Two buffered PWM outputs. Keying: Coding distinct from XPR/XA* (Codex). Cable: Shielded cable to the receiving device.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM0 | PWM output 0 | LOGIC_TX | 5 V push-pull logic, +/-20 mA target, non-isolated (LOGIC_GND); frequency/resolution pairs published by gateware; isolated or 24 V PWM needs an adapter | FPGA PWM0_FPGA (ball unassigned) | CMD.pwm[0].duty / CMD.proc_en bit 2 / STS.proc_en_state bit 2 | cnc1.pwm.0.value / cnc1.pwm.0.enable / cnc1.pwm.0.frequency | Low (buffer disabled, pull-down) | Low when OUT_PERMIT falls (hardware) | servo | TT-XPW-01 |
| 2 | PWM0_0V | PWM 0 reference | LOGIC_TX | LOGIC_GND | - | - | - | n/a | n/a | none | TT-XPW-02 |
| 3 | PWM1 | PWM output 1 | LOGIC_TX | 5 V push-pull logic, +/-20 mA target, non-isolated (LOGIC_GND); frequency/resolution pairs published by gateware; isolated or 24 V PWM needs an adapter | FPGA PWM1_FPGA (ball unassigned) | CMD.pwm[1].duty / CMD.proc_en bit 3 / STS.proc_en_state bit 3 | cnc1.pwm.1.value / cnc1.pwm.1.enable / cnc1.pwm.1.frequency | Low (buffer disabled, pull-down) | Low when OUT_PERMIT falls (hardware) | servo | TT-XPW-03 |
| 4 | PWM1_0V | PWM 1 reference | LOGIC_TX | LOGIC_GND | - | - | - | n/a | n/a | none | TT-XPW-04 |
| 5 | PWM_5V_AUX | 5 V auxiliary for a PWM receiver's logic (50 mA limit) | LOGIC_TX | 5 V, 50 mA limit target | - | TEL.acc.pwm_aux_fault | cnc1.pwm.aux-fault | On with logic power | Limited, fault reported | telemetry | TT-XPW-05 |
| 6 | PWM_SHIELD | Shield drain | CHASSIS | Chassis via SB1 | - | - | - | n/a | n/a | none | TT-XPW-06 |

### XPC0

Process enable 0: hardware-gated floating contact (torch start / laser enable / ohmic enable). Keying: Unique coding per process contact (XPC0 vs XPC1). Cable: Per process profile.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PEN0_1 | Process enable 0 contact side 1 | ISO_SW | Floating form-A photorelay contact, AC or DC 0-30 V, <= 50 mA (TLP3640A(TPL,E), the same part as the motor-enable NO switch); sources needing a higher-rated contact use a profile-listed interposing relay | FPGA PEN0_CMD (ball unassigned) | CMD.proc_en bit 0 / STS.proc_en_state bit 0 | cnc1.proc-en.0.cmd / cnc1.proc-en.0.commanded | OPEN | OPEN on command loss, PROC_PERMIT loss (includes PROCESS_PERMIT_EXT at XS1.3), link loss or controller power loss | servo | TT-XPC0-01 |
| 2 | PEN0_2 | Process enable 0 contact side 2 | ISO_SW | Floating form-A photorelay contact, AC or DC 0-30 V, <= 50 mA (TLP3640A(TPL,E), the same part as the motor-enable NO switch); sources needing a higher-rated contact use a profile-listed interposing relay | - | - | - | OPEN | OPEN on command loss, PROC_PERMIT loss (includes PROCESS_PERMIT_EXT at XS1.3), link loss or controller power loss | servo | TT-XPC0-02 |

### XPC1

Process enable 1: hardware-gated floating contact (torch start / laser enable / ohmic enable). Keying: Unique coding per process contact (XPC0 vs XPC1). Cable: Per process profile.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PEN1_1 | Process enable 1 contact side 1 | ISO_SW | Floating form-A photorelay contact, AC or DC 0-30 V, <= 50 mA (TLP3640A(TPL,E), the same part as the motor-enable NO switch); sources needing a higher-rated contact use a profile-listed interposing relay | FPGA PEN1_CMD (ball unassigned) | CMD.proc_en bit 1 / STS.proc_en_state bit 1 | cnc1.proc-en.1.cmd / cnc1.proc-en.1.commanded | OPEN | OPEN on command loss, PROC_PERMIT loss (includes PROCESS_PERMIT_EXT at XS1.3), link loss or controller power loss | servo | TT-XPC1-01 |
| 2 | PEN1_2 | Process enable 1 contact side 2 | ISO_SW | Floating form-A photorelay contact, AC or DC 0-30 V, <= 50 mA (TLP3640A(TPL,E), the same part as the motor-enable NO switch); sources needing a higher-rated contact use a profile-listed interposing relay | - | - | - | OPEN | OPEN on command loss, PROC_PERMIT loss (includes PROCESS_PERMIT_EXT at XS1.3), link loss or controller power loss | servo | TT-XPC1-02 |

### XAO

Two isolated 0-10 V analog outputs, independent isolation per channel. Keying: Coding distinct from XAI (Codex). Cable: Shielded twisted pair per channel; shield at controller end only.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | AO0 | Analog output 0 (0-10 V) | ISO_AO0 | 0-10 V, >= 2 kohm receiver load, >= 12-bit effective resolution target; isolated per channel (separate isolation domain for AO0 and AO1, decided so two VFDs with different commons can connect) | serial ACC bit 0 | CMD.ao[0] / CMD.proc_en bit 4 / STS.ao.state / TEL.ao[0].readback | cnc1.aout.0.value / cnc1.aout.0.enable / cnc1.aout.0.readback / cnc1.aout.0.readback-valid | 0 V (zero clamp until first valid command and hardware permission) | Clamped to 0 V on OUT_PERMIT loss (hardware zero clamp), link loss or configuration change | servo | TT-XAO-01 |
| 2 | AO0_COM | Analog output 0 common (isolated) | ISO_AO0 | Isolated return of AO0; connect to the receiver's analog common | - | - | - | n/a | n/a | none | TT-XAO-02 |
| 3 | AO0_SHIELD | Shield drain | CHASSIS | Chassis via SB1 | - | - | - | n/a | n/a | none | TT-XAO-03 |
| 4 | AO1 | Analog output 1 (0-10 V) | ISO_AO1 | 0-10 V, >= 2 kohm receiver load, >= 12-bit effective resolution target; isolated per channel (separate isolation domain for AO0 and AO1, decided so two VFDs with different commons can connect) | serial ACC bit 1 | CMD.ao[1] / CMD.proc_en bit 5 / STS.ao.state / TEL.ao[1].readback | cnc1.aout.1.value / cnc1.aout.1.enable / cnc1.aout.1.readback / cnc1.aout.1.readback-valid | 0 V (zero clamp until first valid command and hardware permission) | Clamped to 0 V on OUT_PERMIT loss (hardware zero clamp), link loss or configuration change | servo | TT-XAO-04 |
| 5 | AO1_COM | Analog output 1 common (isolated) | ISO_AO1 | Isolated return of AO1; connect to the receiver's analog common | - | - | - | n/a | n/a | none | TT-XAO-05 |
| 6 | AO1_SHIELD | Shield drain | CHASSIS | Chassis via SB1 | - | - | - | n/a | n/a | none | TT-XAO-06 |

### XAI

Four protected analog inputs with sensor supplies (one isolated AI group). Keying: Coding distinct from XDI/XDO/XH2 (Codex). Cable: Shielded; shield to position 12.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | AI0_P | Analog input 0 + | ISO_AI | Software-selected range per channel: 0-10 V (>= 100 kohm) or 4-20 mA (switched 250 ohm burden); +/-30 V protected; 12-bit target; raw plasma voltage never enters | serial ACC bit 0 | STS.ai[0].value / STS.ai.valid bit 0 / STS.ai.age | cnc1.ain.0.value / cnc1.ain.0.valid / cnc1.ain.0.age | Invalid until first conversion | Over-range, under-range (< 3.6 mA in 4-20 mA mode = wire break) or ADC loss: reading invalid, never zero | servo | TT-XAI-01 |
| 2 | AI0_N | Analog input 0 - (group common) | ISO_AI | AI group common (isolated); differential input with common-mode +/-10 V target | - | - | - | n/a | n/a | none | TT-XAI-02 |
| 3 | AI1_P | Analog input 1 + | ISO_AI | Software-selected range per channel: 0-10 V (>= 100 kohm) or 4-20 mA (switched 250 ohm burden); +/-30 V protected; 12-bit target; raw plasma voltage never enters | serial ACC bit 1 | STS.ai[1].value / STS.ai.valid bit 1 / STS.ai.age | cnc1.ain.1.value / cnc1.ain.1.valid / cnc1.ain.1.age | Invalid until first conversion | Over-range, under-range (< 3.6 mA in 4-20 mA mode = wire break) or ADC loss: reading invalid, never zero | servo | TT-XAI-03 |
| 4 | AI1_N | Analog input 1 - (group common) | ISO_AI | AI group common (isolated); differential input with common-mode +/-10 V target | - | - | - | n/a | n/a | none | TT-XAI-04 |
| 5 | AI2_P | Analog input 2 + | ISO_AI | Software-selected range per channel: 0-10 V (>= 100 kohm) or 4-20 mA (switched 250 ohm burden); +/-30 V protected; 12-bit target; raw plasma voltage never enters | serial ACC bit 2 | STS.ai[2].value / STS.ai.valid bit 2 / STS.ai.age | cnc1.ain.2.value / cnc1.ain.2.valid / cnc1.ain.2.age | Invalid until first conversion | Over-range, under-range (< 3.6 mA in 4-20 mA mode = wire break) or ADC loss: reading invalid, never zero | servo | TT-XAI-05 |
| 6 | AI2_N | Analog input 2 - (group common) | ISO_AI | AI group common (isolated); differential input with common-mode +/-10 V target | - | - | - | n/a | n/a | none | TT-XAI-06 |
| 7 | AI3_P | Analog input 3 + | ISO_AI | Software-selected range per channel: 0-10 V (>= 100 kohm) or 4-20 mA (switched 250 ohm burden); +/-30 V protected; 12-bit target; raw plasma voltage never enters | serial ACC bit 3 | STS.ai[3].value / STS.ai.valid bit 3 / STS.ai.age | cnc1.ain.3.value / cnc1.ain.3.valid / cnc1.ain.3.age | Invalid until first conversion | Over-range, under-range (< 3.6 mA in 4-20 mA mode = wire break) or ADC loss: reading invalid, never zero | servo | TT-XAI-07 |
| 8 | AI3_N | Analog input 3 - (group common) | ISO_AI | AI group common (isolated); differential input with common-mode +/-10 V target | - | - | - | n/a | n/a | none | TT-XAI-08 |
| 9 | AI_REF_10V | 10.00 V reference for potentiometers (10 mA limit) | ISO_AI | 10 V, 10 mA limit | - | TEL.acc.ai_ref_mv | cnc1.ain.ref-voltage | On with logic power | Limited; readings using it flagged | telemetry | TT-XAI-09 |
| 10 | AI_SENS_24V | Isolated +24 V for 2-wire/3-wire transmitters (100 mA limit) | ISO_AI | +24 V isolated, 100 mA limit target, from the ACC AI-group converter RECOM REC3.5-2424SRW/R8/A (CORE_24V budget item ai_group) | - | TEL.acc.ai_sensor_supply_mv / TEL.acc.ai_sensor_supply_fault | cnc1.ain.sensor-supply-voltage / cnc1.ain.sensor-supply-fault | On with logic power | Limited; AI flagged | telemetry | TT-XAI-10 |
| 11 | AI_AGND | AI group common | ISO_AI | Isolated AI common | - | - | - | n/a | n/a | none | TT-XAI-11 |
| 12 | AI_SHIELD | Shield drain | CHASSIS | Chassis via SB1 | - | - | - | n/a | n/a | none | TT-XAI-12 |

### XB1

Isolated RS-485 field bus. Keying: Unique coding XB1 vs XB2 so RS-485 and CAN plugs cannot swap. Cable: Shielded twisted pair, 120 ohm; daisy-chain two cables per contact with ferrules.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | RS485_B | RS-485 D+ (B) | ISO_485 | Isolated RS-485 transceiver; common-mode and rates per transceiver selection (Codex); protocol/profile per THIRD_PARTY_MODBUS / device profile | host: compute UART via isolated transceiver on ACC (Modbus RTU host-side; outside servo timing) | HOST.tty.rs485.errors | cnc1.bus.rs485.errors | Transceiver in receive/recessive | Bus-off/timeout reported; profile-defined hold/inhibit for devices whose data is required | telemetry | TT-XB1-01 |
| 2 | RS485_A | RS-485 D- (A) | ISO_485 | Isolated RS-485 transceiver; common-mode and rates per transceiver selection (Codex); protocol/profile per THIRD_PARTY_MODBUS / device profile | host: compute UART via isolated transceiver on ACC (Modbus RTU host-side; outside servo timing) | HOST.tty.rs485.errors | cnc1.bus.rs485.errors | Transceiver in receive/recessive | Bus-off/timeout reported; profile-defined hold/inhibit for devices whose data is required | telemetry | TT-XB1-02 |
| 3 | RS485_COM | Isolated common | ISO_485 | Isolated bus common | - | - | - | n/a | n/a | none | TT-XB1-03 |
| 4 | RS485_TERM | Termination: link to D+ (pos 1) to fit 120 ohm across A-B | ISO_485 | 120 ohm on the card; fitted by a wire link in the plug | - | - | - | Not fitted unless linked | n/a | none | TT-XB1-04 |
| 5 | RS485_SHIELD | Shield drain | CHASSIS | Chassis via SB1 (or via RC per installation) | - | - | - | n/a | n/a | none | TT-XB1-05 |
| 6 | RS485_COM2 | Isolated common, second contact | ISO_485 | Isolated bus common | - | - | - | n/a | n/a | none | TT-XB1-06 |

### XB2

Isolated CAN field bus. Keying: Unique coding XB1 vs XB2 so RS-485 and CAN plugs cannot swap. Cable: Shielded twisted pair, 120 ohm; daisy-chain two cables per contact with ferrules.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CAN_H | CAN CAN_H | ISO_CAN | Isolated CAN transceiver; common-mode and rates per transceiver selection (Codex); protocol/profile per THIRD_PARTY_MODBUS / device profile | host: compute SPI CAN controller + isolated transceiver on ACC (host-side; outside servo timing) | HOST.socketcan.errors | cnc1.bus.can.errors | Transceiver in receive/recessive | Bus-off/timeout reported; profile-defined hold/inhibit for devices whose data is required | telemetry | TT-XB2-01 |
| 2 | CAN_L | CAN CAN_L | ISO_CAN | Isolated CAN transceiver; common-mode and rates per transceiver selection (Codex); protocol/profile per THIRD_PARTY_MODBUS / device profile | host: compute SPI CAN controller + isolated transceiver on ACC (host-side; outside servo timing) | HOST.socketcan.errors | cnc1.bus.can.errors | Transceiver in receive/recessive | Bus-off/timeout reported; profile-defined hold/inhibit for devices whose data is required | telemetry | TT-XB2-02 |
| 3 | CAN_GND | Isolated CAN ground | ISO_CAN | Isolated bus common | - | - | - | n/a | n/a | none | TT-XB2-03 |
| 4 | CAN_TERM | Termination: link to CAN_H (pos 1) to fit 120 ohm | ISO_CAN | 120 ohm on the card; fitted by a wire link in the plug | - | - | - | Not fitted unless linked | n/a | none | TT-XB2-04 |
| 5 | CAN_SHIELD | Shield drain | CHASSIS | Chassis via SB1 (or via RC per installation) | - | - | - | n/a | n/a | none | TT-XB2-05 |
| 6 | CAN_GND2 | Isolated CAN ground, second contact | ISO_CAN | Isolated bus common | - | - | - | n/a | n/a | none | TT-XB2-06 |

### XS1

Machine safety-chain interface: external permit, process interlock, chain status, deliberate reset/arm with lamp, contactor and STO feedback, output-permission contact. Keying: Unique coding (red plug body recommended) - not interchangeable with any I/O plug. Cable: Per machine safety design; the controller is NOT a safety controller.

| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | SAFE_24V | Wetting supply +24 V for safety-interface contacts (safety branch of the FIELD_B sensor supply, 0.15 A limit) | FIELD_B | +24 V from FIELD_B, 0.15 A limit | - | TEL.dic.safe24_mv / TEL.dic.safety_supply_fault | cnc1.supply.safety-24v.voltage / cnc1.supply.safety-24v.fault | On with FIELD_B | Limited; EXT_PERMIT fed from it reads low -> permission withdrawn (fail-safe) | telemetry | TT-XS1-01 |
| 2 | EXT_PERMIT_IN | External permit: 24 V from the machine safety relay's output contact; fixed assignment, hard-wired to EXT_PERMIT_3V3 in the permission chain (section 04 section 6) | FIELD_B | Sinking 24 V input, same envelope as DI (0-30 V, low 0-5 V, high 15-30 V) | FPGA EXT_PERMIT_FPGA ball G16 | STS.safety bit 10 | cnc1.safety.ext-permit | Reads 'not permitted' until qualified; 10 kohm pull-down at the MC receiver, so an absent, unseated or unpowered DIC reads 'not permitted' | Low removes hardware permission (TX_PERMIT, OUT_PERMIT, PROC_PERMIT) independent of FPGA and link: STEP/DIR high-impedance, enables withdrawn, outputs de-energised; OUTPUT_PATH_INTERRUPTED if motion was active | servo | TT-XS1-02 |
| 3 | PROCESS_PERMIT_IN | Process-enable interlock: gates only the two process-enable contacts XPC0/XPC1 (torch, laser, or a spindle run/STO input deliberately wired through XPC0/XPC1); fixed assignment, hard-wired to PROCESS_PERMIT_EXT_3V3 -> PROC_PERMIT (section 04 section 6) | FIELD_B | Sinking 24 V input, same envelope as DI (0-30 V, low 0-5 V, high 15-30 V) | FPGA PROCESS_PERMIT_FPGA (ball unassigned) | STS.safety bit 11 | cnc1.safety.process-permit | Reads 'not permitted' until qualified; 10 kohm pull-down at the MC receiver (absent or unpowered DIC reads 'not permitted') | Low removes PROC_PERMIT in hardware: both process contacts XPC0/XPC1 open, PROCESS_PERMIT_LOST; it does not stop a spindle or any DO/AO/PWM output; motion unaffected | servo | TT-XS1-03 |
| 4 | SAFETY_STATUS_IN | Safety-chain status (e.g. safety relay diagnostic output); monitoring only | FIELD_B | Sinking 24 V input, same envelope as DI (0-30 V, low 0-5 V, high 15-30 V) | FPGA SAFETY_STATUS_FPGA (ball unassigned) | STS.safety bit 24 | cnc1.safety.chain-status | Reads 'not permitted' / 'not confirmed' until qualified | Status only; disagreement with EXT_PERMIT for longer than chain_mismatch_ms raises a SAFETY_INTERFACE event (no fault) | servo | TT-XS1-04 |
| 5 | RESET_ARM_IN | Deliberate reset/arm pushbutton (momentary NO from SAFE_24V); edge plus release | FIELD_B | Sinking 24 V input, same envelope as DI (0-30 V, low 0-5 V, high 15-30 V) | FPGA RESET_ARM_FPGA (ball unassigned) | STS.safety bit 23 / STS.safety bit 30 | cnc1.safety.reset-arm / cnc1.safety.reset-arm-ready | Reads 'not permitted' / 'not confirmed' until qualified | A press counts when released after reset_arm_press_min_ms and before reset_arm_press_max_ms while EXT_PERMIT is high; the release enables one ARM within reset_arm_window_ms (reset_arm_ready, safety word bit 30); a longer press is 'stuck' (SAFETY_INTERFACE event) and ARM is refused (ARM_REFUSED, fault bit 27) while it persists | servo | TT-XS1-05 |
| 6 | ARM_LAMP | Reset/arm lamp output (24 V, 50 mA) | FIELD_B | 24 V, 50 mA sourcing (indicator only); FIELD_B budget item arm_lamp 0.05 A (section 04 section 10.2) | FPGA ARM_LAMP_FPGA (ball unassigned) | CMD.proc_en bit 6 / STS.proc_en_state bit 4 | cnc1.safety.arm-lamp | OFF | OFF | servo | TT-XS1-06 |
| 7 | CONTACTOR_FB_IN | Drive-power contactor feedback (mirror contact) | FIELD_B | Sinking 24 V input, same envelope as DI (0-30 V, low 0-5 V, high 15-30 V) | FPGA CONTACTOR_FB_FPGA (ball unassigned) | STS.safety bit 25 | cnc1.safety.contactor-fb | Reads 'not permitted' / 'not confirmed' until qualified | Per contactor_fb_mode: must read de-energized at ARM, energized within contactor_close_ms after TX_PERMIT rises and de-energized within contactor_open_ms after it falls; a mismatch latches CONTACTOR_FEEDBACK (fault bit 25), disarms all and refuses ARM until SYNC | servo | TT-XS1-07 |
| 8 | STO_FB_IN | STO / safe-torque-off status feedback from drives | FIELD_B | Sinking 24 V input, same envelope as DI (0-30 V, low 0-5 V, high 15-30 V) | FPGA STO_FB_FPGA (ball unassigned) | STS.safety bit 26 | cnc1.safety.sto-fb | Reads 'not permitted' / 'not confirmed' until qualified | Per sto_fb_mode: a mismatch with the expected STO state for longer than sto_response_ms latches STO_FEEDBACK (fault bit 26), disarms all and refuses ARM until SYNC | servo | TT-XS1-08 |
| 9 | SAFE_0V | Safety interface 0 V | FIELD_B | FIELD_B return | - | - | - | n/a | n/a | none | TT-XS1-09 |
| 10 | PERMIT_OUT_1 | Output-permission contact side 1 (closed only while TX_PERMIT and PERMIT_OUT_REQ are high; open during both watchdog self-tests) | ISO_SW | Floating form-A photorelay contact (TLP3640A class), AC or DC 0-30 V, <= 50 mA; LED supplied only while TX_PERMIT AND PERMIT_OUT_REQ are high (section 04 section 6.2); wire in series with the machine's contactor/STO request chain | - | STS.safety bit 0 (tx_permit readback; PERMIT_OUT follows TX_PERMIT in hardware) | cnc1.safety.tx-permit | OPEN | OPEN whenever TX_PERMIT or PERMIT_OUT_REQ is low (watchdog, EXT_PERMIT low, rail fault, tamper, unconfigured FPGA, disarmed, watchdog self-test) | servo | TT-XS1-10 |
| 11 | PERMIT_OUT_2 | Output-permission contact side 2 | ISO_SW | Floating form-A photorelay contact (TLP3640A class), AC or DC 0-30 V, <= 50 mA; LED supplied only while TX_PERMIT AND PERMIT_OUT_REQ are high (section 04 section 6.2); wire in series with the machine's contactor/STO request chain | - | - | - | OPEN | OPEN whenever TX_PERMIT or PERMIT_OUT_REQ is low (watchdog, EXT_PERMIT low, rail fault, tamper, unconfigured FPGA, disarmed, watchdog self-test) | servo | TT-XS1-11 |
| 12 | SAFE_SHIELD | Shield drain | CHASSIS | Chassis via SB1 | - | - | - | n/a | n/a | none | TT-XS1-12 |

Every motor connector XM0-XM11 and encoder connector XE0-XE11 has its own complete rows in `terminals.json` (nets, FPGA signal names and Codex candidate balls differ per channel). FPGA balls quoted are Codex's candidate allocation (`hardware/fpga_core/pin-allocation.json`, candidate `minimum8_expand12_t20f256`, status candidate_not_vendor_fitted; source inspection). Signals without a ball (EN via `DRIVE_ENABLE#_FPGA_RESERVED` excepted) are new IS-1 requirements on Codex's pin plan.

### 5.1 Test ids

Test id `TT-<connector>-<position>` applies the procedure of the terminal's function class. These are commissioning/qualification procedures to be run on built hardware; none has been run.

| Function class | Procedure and pass condition |
|---|---|
| power | Plug removed: PSU open-circuit voltage 19-30 V at the plug; controller side no short (> 1 kohm) between + and 0 V; powered: reported voltage within 2 % of a reference meter; shutdown contact switches the entry off and clearing never arms motion |
| spacing | No copper connection on the base or card at this position (> 10 Mohm to every neighbour); plug cavity left empty |
| return | Continuity (< 1 ohm) to the domain's reference; isolation (> 10 Mohm at 50 V) to every other domain and to CHASSIS |
| bond | Bond resistance to XPE1 < 0.1 ohm (low-ohm meter); isolation from every signal return |
| service_input | Close/open the contact; the reported state follows within one telemetry period |
| motion_output | Differential waveform at the terminal into the drive (or 100 ohm) with a scope at a low commanded rate: correct pair, polarity, pulse count equal to the commanded count; high-Z when permission is withdrawn; any interruption during motion produces a latched fault and invalid position state |
| enable_switch | Power off: EN_NO-EN_COM open (> 1 Mohm), EN_NC-EN_COM closed (< 5 ohm). Armed: NO closed, NC open. Withdraw permission / remove LOGIC power with FIELD present: return to the power-off state; 'disarmed => drive disabled' confirmed on the real drive (E3) |
| motion_input | Drive the alarm input via ALM_COM (and via the actual drive alarm contact): state and latched alarm reported, armed channel disarms all; open wire behaves per profile |
| supply | Voltage at the terminal within the target; short to its return trips the limiter, fault flag reported with timestamp, other groups unaffected (fault containment), recovery only by the documented action |
| feedback_input | Rotate the encoder by a known amount: count and direction correct; index latched; unplug/open one line: fault or invalid reported, never a silent zero |
| operator_input | Actuate each selector/handwheel/enable: reported state and counts correct; unplugged pendant reads inactive/released |
| reference | Voltage 2.5 V +/- 5 % unloaded |
| general_input | Apply 24 V and 0 V/open: state follows; kill the DI link: all DI reported invalid (not low) within the link timeout |
| general_output | Command on/off into a declared load: state, readback and current (valid, with age) reported; short and open load produce the documented fault; link loss turns outputs off via the card watchdog; accuracy test TT-DO-ACC |
| fast_input | Edge from a signal generator while an axis moves: captured counts coherent, capture latency and jitter measured; overrun reported |
| frequency_input | Signal generator at 1 kHz, 100 kHz and 1 MHz: reported frequency within gate resolution; remove signal: invalid (not zero) after timeout |
| identity | Fit a module: presence and identity read at qualification; unplug under power: MODULE_CHANGED latched, torch permission withheld |
| process_output | Power off: contact open / PWM low. Commanded with permission: closes / duty correct. Withdraw permission: opens / low within the hardware path |
| analog_output | Command 0, 5 and 10 V into 2 kohm: reference meter agrees within the accuracy target; readback valid with age; permission loss clamps to 0 V |
| analog_input | Apply 0, 5, 10 V (and 4, 12, 20 mA): reported values within target; open 4-20 mA loop flagged wire break |
| fieldbus | Loopback to a reference adapter at the profile rate: frames exchanged; error counters increase on induced errors; termination link measured 120 ohm |
| termination | With link fitted, 120 ohm +/- 5 % between the pair (bus unpowered) |
| safety_input | Operate the machine safety device: state reported; EXT_PERMIT or PROCESS_PERMIT low withdraws the corresponding hardware permission with the FPGA held in reset (independence check) |
| status_output | Lamp on/off follows command; short trips the limiter |
| permission_output | Disarmed: open; armed: closed; watchdog fault injection (stop progress pulses): opens and stays open until a deliberate re-arm |

### 5.2 Correction (2) as it applies at the terminal

STEP/DIR outputs have two legal states under fault: driven by the stepgen, or high-impedance through hardware permission. The normative rule and its circuit (output-path-interruption latches, filtered module terms, pos_continuity, unhoming) are section 04 section 4; at the terminal it means any interruption of an active pulse train is a latched fault with the affected joints unhomed, and a noise pulse rejected by an input filter never changes any output pin. The bank-B Ioff-buffer OE therefore follows the filtered module terms (section 04 section 6.2), superseding the unfiltered OE of MOTION_EXPANSION section 7.3.1, and its qualified OE net also clears the OPI_BOE latch; every AM26C31 STEP/DIR input on the MIA and MX4 has a 10 kohm pull-down, so a floating input rests at the idle level. XS1.3 gates only the process-enable contacts XPC0/XPC1.

## 6. Diagnostics at output and supply terminals (T4 display rule)

Rule applied to every row: a displayed measurement carries validity and age; a missing sense path shows **unavailable**, a reading older than its source's fixed stale limit (`stale_ms` in the telemetry map and host-source tables of section 01 section 8.1a; for example 100 ms for output current, 5 s for 1 Hz card temperatures) shows **stale**, and neither is ever shown as 0. This is the single stale rule of section 01 section 3.12. Measured facts (for example 'DO7 overcurrent, 1.9 A, 12:03:04') are stored and shown separately from any diagnosis text; guidance text below is a suggested next test, not a fact.

| Terminal type | Current | Open load | Short / overcurrent | Thermal | Supply voltage | Shown to the user as | Terminal-level guidance |
|---|---|---|---|---|---|---|---|
| Power entry: XP1.1 (CORE_24V_IN; family CORE_nV_IN) | INA238AIDGSR shunt monitor on the PSM, host I2C at 10 Hz (section 02); the TPS26630 IMON/FLT remain the protection path | n/a | TPS26630 current limit / FLT (overload/thermal latch) | TPS26630 thermal shutdown via FLT | INA238AIDGSR bus-voltage channel after the eFuse (host I2C, 10 Hz) | 'CORE: 24.1 V, 2.3 A (measured, age 80 ms)'; a missing sense path shows 'unavailable', never 0 V | If FLT latched: remove XP1 plug, measure PSU open-circuit voltage at the plug (expect 19-30 V), then check for a short between XP1.1 and XP1.2 on the controller side with the PSU disconnected; re-apply power (clearing never re-arms motion). |
| Power entry: XP2.1 (FIELD_A_24V_IN; family FIELD_A_nV_IN) | INA238AIDGSR shunt monitor on the PSM, host I2C at 10 Hz (section 02); the TPS26630 IMON/FLT remain the protection path | n/a | TPS26630 current limit / FLT (overload/thermal latch) | TPS26630 thermal shutdown via FLT | INA238AIDGSR bus-voltage channel after the eFuse (host I2C, 10 Hz) | 'FIELD_A: 24.1 V, 2.3 A (measured, age 80 ms)'; a missing sense path shows 'unavailable', never 0 V | If FLT latched: remove XP2 plug, measure PSU open-circuit voltage at the plug (expect 19-30 V), then check for a short between XP2.1 and XP2.2 on the controller side with the PSU disconnected; re-apply power (clearing never re-arms motion). |
| Power entry: XP3.1 (FIELD_B_24V_IN; family FIELD_B_nV_IN) | INA238AIDGSR shunt monitor on the PSM, host I2C at 10 Hz (section 02); the TPS26630 IMON/FLT remain the protection path | n/a | TPS26630 current limit / FLT (overload/thermal latch) | TPS26630 thermal shutdown via FLT | INA238AIDGSR bus-voltage channel after the eFuse (host I2C, 10 Hz) | 'FIELD_B: 24.1 V, 2.3 A (measured, age 80 ms)'; a missing sense path shows 'unavailable', never 0 V | If FLT latched: remove XP3 plug, measure PSU open-circuit voltage at the plug (expect 19-30 V), then check for a short between XP3.1 and XP3.2 on the controller side with the PSU disconnected; re-apply power (clearing never re-arms motion). |
| PE bond: XPE1.1 (CHASSIS_PE; family CHASSIS_PE) | none | none | none | none | none | Commissioning check result only (measured bond resistance, operator-recorded) | Measure PE stud to enclosure and to PSU PE with a low-ohm meter before first power-up. |
| STEP/DIR: XM0.1 (M0_STEP_P; family Mn_STEP_P) | none (AM26C31 has no current sense) | none per line | AM26C31 output short-circuit limiting (datasheet); not reported per line | card temperature sensor (requirement) | MOTION_5V / EXP_5V power-good (section 04 section 8) for bank A | Commanded steps and commanded position, labelled 'commanded'; measured position only where an encoder is mapped | Wrong direction: swap DIR+/DIR- at XM0.3/XM0.4 or invert in configuration (preview/diff). No motion: check the drive power LED, then measure XM0.1-XM0.2 while jogging slowly (differential voltage should alternate sign). |
| STEP/DIR: XM0.2 (M0_STEP_N; family Mn_STEP_N) | none (AM26C31 has no current sense) | none per line | AM26C31 output short-circuit limiting (datasheet); not reported per line | card temperature sensor (requirement) | MOTION_5V / EXP_5V power-good (section 04 section 8) for bank A | Commanded steps and commanded position, labelled 'commanded'; measured position only where an encoder is mapped | Wrong direction: swap DIR+/DIR- at XM0.3/XM0.4 or invert in configuration (preview/diff). No motion: check the drive power LED, then measure XM0.1-XM0.2 while jogging slowly (differential voltage should alternate sign). |
| STEP/DIR: XM0.3 (M0_DIR_P; family Mn_DIR_P) | none (AM26C31 has no current sense) | none per line | AM26C31 output short-circuit limiting (datasheet); not reported per line | card temperature sensor (requirement) | MOTION_5V / EXP_5V power-good (section 04 section 8) for bank A | Commanded steps and commanded position, labelled 'commanded'; measured position only where an encoder is mapped | Wrong direction: swap DIR+/DIR- at XM0.3/XM0.4 or invert in configuration (preview/diff). No motion: check the drive power LED, then measure XM0.1-XM0.2 while jogging slowly (differential voltage should alternate sign). |
| STEP/DIR: XM0.4 (M0_DIR_N; family Mn_DIR_N) | none (AM26C31 has no current sense) | none per line | AM26C31 output short-circuit limiting (datasheet); not reported per line | card temperature sensor (requirement) | MOTION_5V / EXP_5V power-good (section 04 section 8) for bank A | Commanded steps and commanded position, labelled 'commanded'; measured position only where an encoder is mapped | Wrong direction: swap DIR+/DIR- at XM0.3/XM0.4 or invert in configuration (preview/diff). No motion: check the drive power LED, then measure XM0.1-XM0.2 while jogging slowly (differential voltage should alternate sign). |
| Enable NO/NC: XM0.8 (M0_EN_NO; family Mn_EN_NO) | none | none | none (loop current limited by the AUX limiter or the drive's own loop) | none | AUX_5V/AUX_24V bank monitors when the loop is sourced from the controller | 'M0 enable: commanded ON, TX_PERMIT high (contact state not measured)' | Power off: XM0.8-XM0.9 open, XM0.9-XM0.10 closed (< 5 ohm). Commissioning check E3 'disarmed => drive disabled' on every channel after any harness or card change (operator-confirmed). |
| Enable NO/NC: XM0.10 (M0_EN_NC; family Mn_EN_NC) | none | none | none (loop current limited by the AUX limiter or the drive's own loop) | none | AUX_5V/AUX_24V bank monitors when the loop is sourced from the controller | 'M0 enable: commanded ON, TX_PERMIT high (contact state not measured)' | Power off: XM0.8-XM0.9 open, XM0.9-XM0.10 closed (< 5 ohm). Commissioning check E3 'disarmed => drive disabled' on every channel after any harness or card change (operator-confirmed). |
| Supply: XM0.11 (M0_AUX_5V; family Mn_AUX_nV) | none | none | per-bank limiter; AUX5_OK_A monitor | limiter thermal behaviour | AUX5_OK_A power-good carried every servo cycle (section 04 section 8) | 'AUX 5 V bank A: fault (measured flag, age 1 ms)' | Unplug the motor plugs of bank A one at a time; the plug whose removal clears the fault has the short (check XM0.11 wiring to the drive). |
| Supply: XE0.1 (ENC0_5V; family ENCn_nV) | none | none | TPS2553-1 FAULT_N (overcurrent/thermal), per port | TPS2553-1 thermal shutdown via FAULT_N | not measured in IS-1 (limiter fault flag only; the UI shows 'not measured', never a number) | 'ENC0 supply: current limit tripped at 12:03:04 (measured flag)'; voltage shown only with a sense channel, else 'not measured' | Unplug XE0; if the fault clears after re-enable the short is in the encoder cable/encoder; measure XE0.1-XE0.2 on the cable side (expect encoder load, not < 10 ohm). |
| Encoder line: XE0.3 (ENC0_A_P; family ENCn_A_P) | none | AM26LV32E fail-safe gives a steady level only; no line-fault flag in this receiver class | none per line | none | see ENC supply | Measured position with validity and age; illegal-transition counter | Counts in the wrong direction: swap A+/A- (XE0.3/XE0.4) or invert in configuration. Illegal-transition count rising: check shield at XE0.10 and SB1 and cable routing near motor power. |
| Encoder line: XE0.4 (ENC0_A_N; family ENCn_A_N) | none | AM26LV32E fail-safe gives a steady level only; no line-fault flag in this receiver class | none per line | none | see ENC supply | Measured position with validity and age; illegal-transition counter | Counts in the wrong direction: swap A+/A- (XE0.3/XE0.4) or invert in configuration. Illegal-transition count rising: check shield at XE0.10 and SB1 and cable routing near motor power. |
| Supply: XH1.1 (MPG_5V; family MPG_nV) | none | none | limiter fault flag | limiter flag | not measured in IS-1 (limiter fault flag only) | 'Handwheel supply fault' | Unplug XH1; if cleared, check pendant cable between XH1.1 and XH1.2. |
| Supply: XDI0.9 (SENS24_G0; family SENSn_Gn) | none (limit flag only) | none | limiter fault flag | limiter thermal flag | DIC ADC voltage sense per group (requirement) | 'Sensor supply G0: 23.9 V (measured, age 100 ms)' or 'current limit active' | Disconnect sensors on XDI0 one by one; a sensor whose removal clears the limit is shorted. Measure XDI0.9 to XDI0.11 with the plug removed. |
| General DO: XDO0.1 (DO00; family DOn) | TPS274C65ASRHAR integrated 10-bit ADC, IC U1 CH1; sense-current spread relative to the datasheet min-max midpoint: +/-4.7 % at 500 mA, +/-9.9 % at 200 mA, +/-15 % at 100 mA, +/-46 % at 50 mA, before per-channel factory calibration (datasheet arithmetic, unmeasured); displayed as a number only from 0.10 to 0.50 A (declared range), below 0.10 A shown as '< 0.10 A' | TPS274C65ASRHAR on-state and off-state open-load (wire-break) detection, per channel | Adjustable current limit (set per load profile, 250 mA-2.2 A range; never above the 0.5 A channel rating plus declared inrush) and short-to-supply detection; fault latched on the card | Per-channel thermal shutdown + FET temperature sense (TSNS) | TPS274C65ASRHAR VS sense of FIELD_A and VOUT sense per channel | 'DO0 ON 0.21 A +/-0.02 A (measured 12:03:04.120, age 40 ms)'; older than its 100 ms stale limit (protocol telemetry_map) shows 'stale'; link or ADC unavailable shows 'unavailable', never 0 A | Short/overcurrent on DO0: remove XDO0 plug, measure XDO0.1 to XDO0.9 on the load side (a 24 V 0.25 A coil is about 96 ohm; < 10 ohm indicates a short); open load: check continuity XDO0.1 to the load and the load return to XDO0.9-12. |
| Supply: XPR.2 (PRB0_24V; family PRBn_nV) | none | none | limiter fault flag | limiter flag | not measured in IS-1 (limiter fault flag only) | 'Probe 0 supply: current limit active' | Unplug the probe; measure XPR.2 to XPR.3 on the probe cable. |
| Supply: XF.1 (FREQ_5V; family FREQ_nV) | none | none | limiter fault flag | limiter flag | not measured in IS-1 (limiter fault flag only) | 'Measurement module supply fault' | Unplug the module; measure XF.1 to XF.2 on the module side. |
| PWM output: XPW.1 (PWM0; family PWMn) | none | none | none (buffer limited) | none | 5 V rail power-good on ACC | 'PWM0 commanded 40 % at 5 kHz (commanded, not measured)' | Measure XPW.1 to XPW.2 with a meter in DC mode: expect about duty x 5 V. |
| Supply: XPW.5 (PWM_5V_AUX; family PWM_nV_AUX) | none | none | limiter fault flag | limiter flag | not measured in IS-1 (fault flag only) | 'PWM aux supply fault' | Unplug XPW; measure XPW.5 to XPW.2. |
| Process contact: XPC0.1 (PEN0_1; family PENn_n) | none | none | none | none | none | 'Process enable 0 (e.g. torch start): commanded ON, hardware permission OK (contact state not measured)'; the process's own confirmation (e.g. Arc OK on a DI) is the measured fact | With power off measure XPC0.1-XPC0.2 open; during a dry-run test with the source in test mode confirm the source sees the start request. |
| Analog output: XAO.1 (AO0; family AOn) | none | readback shows open-circuit voltage; load presence not detected | output stage current limit (not reported unless readback deviates) | none | isolated AO supply power-good (requirement) | 'AO0 commanded 6.00 V, measured 5.98 V (age 20 ms)' - readback channel is a requirement on the ACC card; without it, 'measured: unavailable' | Commanded and measured differ by > 0.1 V: disconnect XAO.1; if readback recovers, the receiver input or wiring is overloading the output. |
| Analog input: XAI.1 (AI0_P; family AIn_P) | 4-20 mA mode: the measurement itself | 4-20 mA mode: < 3.6 mA flagged wire break | over-range flag | none | AI sensor supplies (positions 9-10) sensed | 'AI1 12.4 mA (valid, age 5 ms)'; 'AI1 wire break (measured 0.1 mA < 3.6 mA)' | Wire break: measure loop current in series at XAI.1; check sensor supply XAI.10. |
| Supply: XAI.9 (AI_REF_10V; family AI_REF_nV) | none | none | limit flag | none | ACC ADC sense | 'AI reference 10.00 V (measured)' | If low: unplug potentiometers one at a time. |
| Supply: XAI.10 (AI_SENS_24V; family AI_SENS_nV) | none | none | limiter fault flag | limiter flag | ACC ADC sense | 'AI sensor supply 23.8 V (measured)' | Unplug transmitters one at a time. |
| Field bus: XB1.1 (RS485_B; family RSn_B) | none | none | transceiver thermal/bus-fault (if reported by the chosen part) | transceiver thermal | isolated bus supply power-good (requirement) | 'RS-485: 3 CRC errors, 1 timeout in the last 10 min (counters, measured)' | Many errors: check termination link XB1.4-XB1.1 at exactly the two bus ends, shield at XB1.5, and swapped A/B. |
| Field bus: XB2.1 (CAN_H; family CAN_H) | none | none | transceiver thermal/bus-fault (if reported by the chosen part) | transceiver thermal | isolated bus supply power-good (requirement) | 'CAN: 3 CRC errors, 1 timeout in the last 10 min (counters, measured)' | Many errors: check termination link XB2.4-XB2.1 at exactly the two bus ends, shield at XB2.5, and swapped A/B. |
| Supply: XS1.1 (SAFE_24V; family SAFE_nV) | none | none | limiter fault flag | limiter flag | DIC ADC sense | 'Safety interface supply: 24.0 V (measured, age 100 ms)' | Unplug XS1; if the limit clears, check the wiring from XS1.1 to buttons and contacts. |
| PERMIT_OUT: XS1.10 (PERMIT_OUT_1; family PERMIT_OUT_n) | none | none | none | none | none | 'Output permission: CLOSED (from TX_PERMIT readback; contact state not measured)' | Commissioning: disarmed, XS1.10-XS1.11 open; armed, closed; stop the watchdog input (fault injection): opens and stays open until a deliberate re-arm. |

Output-current accuracy is stated only across the declared range (0.10-0.50 A per DO channel) from the TPS274C65 ISNS table (datasheet arithmetic); it must be verified by measurement at 0.10, 0.25 and 0.50 A per channel and at the bank's temperature extremes, not at one convenient load (test TT-DO-ACC: per channel, resistive loads drawing 0.10, 0.25 and 0.50 A, reference ammeter in series, at minimum and maximum rated ambient; pass = reading inside the stated datasheet band and flagged valid). Enable contacts, process contacts and PERMIT_OUT have no contact-state measurement in the standard product; the UI therefore labels them 'commanded (not measured)'. A per-channel enable readback would cost 12 FPGA pins plus 12 sense circuits and is recorded as an optional improvement, not fitted.

## 7. Field power arithmetic (proposal, not a rating)

- **FIELD_A:** DO0-7 4.0 A; AUX_24V A 0.148 A, B 0.074 A; FIELD_5V input 0.096 A; probe supplies 0.20 A; control 0.06 A; **4.578 A** continuous; entry current-limit minimum 5.08 A.
- **FIELD_B:** DO8-15 4.0 A; DI sensor groups 0.60 A; safety-interface branch 0.15 A; reset/arm lamp 0.05 A; control 0.02 A; **4.82 A** continuous; entry current-limit minimum 5.32 A.
- **CORE:** 3.011 A at 18 V with twelve motors and the encoder expansion; entry current-limit minimum 3.61 A (4 A class).
- Source and basis: IS-1 section 04 section 10.2 (authoritative); repeated here so each terminal can be traced to its entry. Arithmetic reservations from section 04; not ratings, not measurements. Per-output 0.5 A, 2.0 A per 4-output group, driver current-limit maximum <= 1.0 A are enforced in hardware and by the configuration validator (section 04 section 10.2); the allocation sheets below check the 2.0 A group limit against declared loads.

## 8. Non-field and service connectors

| Id | Type | Owner | Function | Domain | Diagnostics | Fault behaviour |
|---|---|---|---|---|---|---|
| XETH1 | RJ45 8P8C shielded, 10/100/1000BASE-T with magnetics | CMC | Customer LAN: UI remote access, Modbus TCP devices, optional AI companion, offline export; never in the servo path | compute Ethernet (magnetics-isolated), shield to chassis | Link state/speed, error counters (host) | Loss has no motion effect; remote sessions lose authority |
| XDSP1 | HDMI Type A (display video) - touch returns over XUSB1/XUSB2 | CMC | Display package connection (7-21 inch classes; display power comes from the display package's own supply, costed separately) | LOGIC | EDID/hot-plug detect (host) | Display loss: machine keeps running under its own rules; UI-originated commands cease |
| XUSB1 | USB-A host (USB 2.0), current-limited 500 mA | CMC | Touch controller, keyboard, third-party USB/RS-485 adapters, export media | LOGIC | Port over-current flag (host) | Port disabled on over-current |
| XUSB2 | USB-A host (USB 2.0), current-limited 500 mA | CMC | As XUSB1 | LOGIC | Port over-current flag (host) | Port disabled on over-current |
| XUSB_SVC | USB-C device port (USB 2.0) | ESC | ESP32-S3 service console: offline diagnostics, fault-history export, recovery guidance; no motion authority | LOGIC (service) | ESP service heartbeat | No effect on motion |
| XANT1 | Antenna bulkhead of the compute module's certified antenna kit (Raspberry Pi Antenna Kit for CM4/CM5, 2 dBi, per advice verification) | CMC | Customer Wi-Fi/Bluetooth on the compute module's certified radio (customer Wi-Fi is NOT routed through the service ESP) | RF | Link state (host) | No effect on motion; offline operation complete |
| XANT2 | Unique-coupling antenna bulkhead (e.g. RP-SMA) fed from ESP32-S3-WROOM-1U U.FL; antenna type/gain must match the FCC filing (47 CFR 15.203/15.204) | ESC | Service ESP BLE/Wi-Fi for local service access only | RF | ESP radio status | No effect on motion |
| XCART1 | Keyed settings-cartridge slot with write-protect | SCART (cartridge) / PSM (slot) | Removable machine-memory cartridge (versioned configuration, two committed records) | LOGIC | Presence, identity, record CRC, write-protect state | Missing/invalid cartridge: configuration from mirror only after explicit recovery transaction; no motion resume |
| XJTAG_MC | Internal: FPGA JTAG header on the motion card (factory/service fixture only) | MC | Factory programming/boundary scan; customers never flash manually (configuration flash restored by host from a verified local package) | LOGIC | n/a | n/a |
| XDBG_CMC | Internal: compute debug UART header | CMC | Factory/service console | LOGIC | n/a | n/a |
| XDBG_ESC | Internal: ESP UART/boot header | ESC | Factory programming of the service ESP | LOGIC | n/a | n/a |
| SLOT_MX | Internal: base slot S4 for MX4, two DIN 41612 C096 connectors (P1 logic, P2 field; section 02 section 7); field conductors arrive from the XTB har-bus 64 connector over base copper | BASE/XTB | Motor expansion M8-M11 | LOGIC + FIELD on separate connectors | Presence A/B, MOD_ID, EXP_PGOOD, tamper | Change under power: tamper latch, whole machine inhibited until power cycle |
| SLOT_EX | Internal: base slot S6 for EX8, two DIN 41612 C096 connectors (P1 logic with 24 encoder lines, status register, presence and power-good; P2 field from the XTB) | BASE/XTB | Encoder expansion ENC4-ENC11 (fitted simultaneously with MX4 when required) | LOGIC | Presence A/B, ID, power-good | Change under power: EXPANSION_CHANGED, inhibited until power cycle |

## 9. Allocation sheets

Each sheet assigns every function of an advertised machine to a physical terminal and carries a machine-readable HAL mapping (joint and axis per motor, the single motor-pos-fb source per joint, the pins every input writes, the single writer of every output, homing groups, probe net and spindle run paths); the validator builds the net list from it and rejects double use, capacity overflow and any pin with two writers. Counts are arithmetic from the sheet. Every sheet also uses the XS1 safety interface (external permit, process permit, chain status, reset/arm, contactor and STO feedback, PERMIT_OUT). Output fault states follow section 04 section 9 (de-energised on permission loss; workholding must be spring-applied or bistable; drawbar energise-to-release). DO group currents use stated example loads (valve 0.25 A, 24 V LED lamp 0.1 A, relay coil 0.05 A, brake 0.5 A max; pumps through an interposing relay) and must be replaced by the selected device profiles. Every DO also carries a declared start (peak) current: a load whose peak exceeds the 0.62 A minimum current-limit setting needs an interposing relay, because the card rejects the inrush modes and a current-limit event latches the output off.

| Sheet | Hardware | Fits | Motors used/spare | Encoders | DI | DO | Probes | FREQ | PWM | Proc. enables | AO | AI | DO groups 0-3/4-7/8-11/12-15 assumed all-on A (limit 2.0 each) | Not-fitting variants |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_router_3axis_gantry | Standard 8-motor controller (no expansion) | yes | 5/3 | 0/4 | 22/2 | 15/1 | 2/0 | 0/2 | 0/2 | 0/2 | 1/1 | 0/4 | 0.6 / 0.6 / 0.9 / 0.3 | - |
| B_mill_5axis_trunnion | Standard 8-motor controller | yes | 6/2 | 3/1 | 23/1 | 14/2 | 2/0 | 0/2 | 0/2 | 0/2 | 1/1 | 0/4 | 0.6 / 1.0 / 0.2 / 0.6 | B2_separate_limits |
| C_lathe | Standard 8-motor controller | yes | 3/5 | 1/3 | 20/4 | 12/4 | 1/1 | 0/2 | 0/2 | 0/2 | 1/1 | 0/4 | 0.6 / 0.8 / 0.25 / 0 | - |
| D_plasma | Standard 8-motor controller + plasma.divided_voltage.v1 module (separately rated, own identity) on XF | yes | 4/4 | 0/4 | 15/9 | 7/9 | 2/0 | 1/1 | 0/2 | 2/0 | 0/2 | 0/4 | 0.45 / 0.7 / 0 / 0 | - |
| E_twelve_motor_with_encoder_expansion | Twelve-motor controller: MX4 motor expansion + EX8 encoder expansion + XTB terminal board, all factory-fitted | yes | 12/0 | 12/0 | 22/2 | 15/1 | 2/0 | 0/2 | 0/2 | 0/2 | 0/2 | 0/4 | 1.0 / 0.6 / 1.6 / 0.15 | E2_plus_spindle_encoder |
| F_twelve_motor_open_loop | MX4 + XTB, no EX8 | yes | 12/0 | 4/0 | 15/9 | 3/13 | 0/2 | 0/2 | 0/2 | 0/2 | 1/1 | 0/4 | 0.6 / 0 / 0 / 0 | - |

### A_router_3axis_gantry: 3-axis mill/router, dual-motor Y gantry with independent homing, 5 motors, ATC, drawbar, tool sensor, coolant, lube, spindle run/dir/ready/fault, Z brake, pendant

Hardware: Standard 8-motor controller (no expansion). Interpretation: Five motors = X, Y1, Y2 (gantry pair, squared by independent home switches and a negative HOME_SEQUENCE), Z, and an ATC carousel stepper driven from HAL as an indexer. If the machine instead has dual X and dual Y (X1,X2,Y1,Y2,Z) it also fits (5 of 8 motors). LinuxCNC mapping: trivkins coordinates=XYYZ kinstype=BOTH; [KINS]JOINTS=5 with motmod num_extrajoints=1; joints 0-3 -> M0-M3; M4 carousel = extra joint 4 driven through joint.4.posthome-cmd by the carousel component after homing.

| Function | Class | Channel | Terminal | Assumed load / peak | LinuxCNC mapping |
|---|---|---:|---|---|---|
| X joint | motor | 0 | XM0.1-14 | - | joint 0 (X); motor-pos-fb cnc1.0.position-fb |
| Y1 joint (gantry left) | motor | 1 | XM1.1-14 | - | joint 1 (Y); motor-pos-fb cnc1.1.position-fb |
| Y2 joint (gantry right) | motor | 2 | XM2.1-14 | - | joint 2 (Y); motor-pos-fb cnc1.2.position-fb |
| Z joint | motor | 3 | XM3.1-14 | - | joint 3 (Z); motor-pos-fb cnc1.3.position-fb |
| ATC carousel stepper (HAL indexer) | motor | 4 | XM4.1-14 | - | joint 4 (-, extra joint); motor-pos-fb cnc1.4.position-fb |
| Home X | di | 0 | XDI0.1 | - | joint.0.home-sw-in |
| Home Y1 | di | 1 | XDI0.2 | - | joint.1.home-sw-in |
| Home Y2 | di | 2 | XDI0.3 | - | joint.2.home-sw-in |
| Home Z | di | 3 | XDI0.4 | - | joint.3.home-sw-in |
| Limit X (both ends, NC series) | di | 4 | XDI0.5 | - | joint.0.neg-lim-sw-in; joint.0.pos-lim-sw-in |
| Limit Y1 | di | 5 | XDI0.6 | - | joint.1.neg-lim-sw-in; joint.1.pos-lim-sw-in |
| Limit Y2 | di | 6 | XDI0.7 | - | joint.2.neg-lim-sw-in; joint.2.pos-lim-sw-in |
| Limit Z | di | 7 | XDI0.8 | - | joint.3.neg-lim-sw-in; joint.3.pos-lim-sw-in |
| ATC carousel home | di | 8 | XDI1.1 | - | joint.4.home-sw-in |
| ATC cover open confirm | di | 9 | XDI1.2 | - | motion.digital-in-00 |
| ATC cover closed confirm | di | 10 | XDI1.3 | - | motion.digital-in-01 |
| Drawbar clamped | di | 11 | XDI1.4 | - | motion.digital-in-02 |
| Drawbar released | di | 12 | XDI1.5 | - | motion.digital-in-03 |
| Air pressure OK | di | 13 | XDI1.6 | - | motion.digital-in-04 |
| Lube level/pressure OK | di | 14 | XDI1.7 | - | motion.digital-in-05 |
| Spindle ready / at speed (VFD relay) | di | 15 | XDI1.8 | - | spindle.0.at-speed |
| Spindle fault (VFD relay) | di | 16 | XDI2.1 | - | motion.digital-in-06 |
| Enclosure door closed (status, not safety) | di | 17 | XDI2.2 | - | motion.digital-in-07 |
| Cycle start | di | 18 | XDI2.3 | - | halui.program.run |
| Feed hold | di | 19 | XDI2.4 | - | halui.program.pause |
| Coolant level OK | di | 20 | XDI2.5 | - | motion.digital-in-08 |
| Dust collector running | di | 21 | XDI2.6 | - | motion.digital-in-09 |
| Touch probe | probe | 0 | XPR.1 | - | or2.probe.in0 <- cnc1.probe.0.in |
| Tool length sensor | probe | 1 | XPR.4 | - | or2.probe.in1 <- cnc1.probe.1.in |
| Spindle forward/run (VFD input via interposing relay or VFD 24 V input) | do | 0 | XDO0.1 | 0.05 A / 0.05 A (relay) | written by spindle.0.forward |
| Spindle reverse/dir | do | 1 | XDO0.2 | 0.05 A / 0.05 A | written by spindle.0.reverse |
| Drawbar release valve (interlocked: spindle stopped) | do | 2 | XDO0.3 | 0.25 A / 0.25 A | written by motion.digital-out-00 |
| Spindle cone air blast | do | 3 | XDO0.4 | 0.25 A / 0.25 A | written by motion.digital-out-01 |
| ATC cover valve | do | 4 | XDO0.5 | 0.25 A / 0.25 A | written by motion.digital-out-02 |
| Coolant flood (pump contactor coil relay) | do | 5 | XDO0.6 | 0.05 A / 0.05 A (relay) | written by iocontrol.0.coolant-flood |
| Coolant mist valve | do | 6 | XDO0.7 | 0.25 A / 0.25 A | written by iocontrol.0.coolant-mist |
| Lube pump (through an interposing relay; the pump start current is on the relay contact) | do | 7 | XDO0.8 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-03 |
| Z brake release (coil must be <= 0.5 A continuous, else interposing relay) | do | 8 | XDO1.1 | 0.5 A / 0.5 A (relay) | written by joint.3.amp-enable-out |
| Dust collector (contactor relay) | do | 9 | XDO1.2 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-04 |
| Dust boot lift valve | do | 10 | XDO1.3 | 0.25 A / 0.25 A | written by motion.digital-out-05 |
| Work light | do | 11 | XDO1.4 | 0.1 A / 0.3 A | written by motion.digital-out-06 |
| Stack light green | do | 12 | XDO1.5 | 0.1 A / 0.2 A | written by motion.digital-out-07 |
| Stack light amber | do | 13 | XDO1.6 | 0.1 A / 0.2 A | written by motion.digital-out-08 |
| Stack light red | do | 14 | XDO1.7 | 0.1 A / 0.2 A | written by motion.digital-out-09 |
| Spindle speed 0-10 V to VFD | ao | 0 | XAO.1-2 | - | written by spindle.0.speed-out-abs (scaled to volts) |
| Drive STO feedback | sto_fb | 0 | XS1.8 | - | - |
| Machine E-stop/safety relay output -> external permit | safety_ext_permit | 0 | XS1.2 | - | - |
| Process-enable interlock (gates XPC0/XPC1 only; not a spindle stop) | process_permit | 0 | XS1.3 | - | - |
| Safety relay diagnostic status | safety_status | 0 | XS1.4 | - | - |
| Reset/arm pushbutton with lamp | reset_arm | 0 | XS1.5 (+XS1.6 lamp) | - | - |
| Drive-power contactor mirror contact | contactor_fb | 0 | XS1.7 | - | - |
| Output permission contact in series with contactor request | permit_out | 0 | XS1.10-11 | - | - |
| Handwheel (MPG) with enable button | mpg | 0 | XH1.1-10 | - | - |
| Pendant axis select X | pendant_sel | 0 | XH2.1 | - | axis X |
| Pendant axis select Y | pendant_sel | 1 | XH2.2 | - | axis Y |
| Pendant axis select Z | pendant_sel | 2 | XH2.3 | - | axis Z |
| Pendant x1 | pendant_sel | 6 | XH2.7 | - | - |
| Pendant x10 | pendant_sel | 7 | XH2.8 | - | - |
| Pendant x100 | pendant_sel | 8 | XH2.9 | - | - |

- Joints: 4 kinematic + 1 extra = 5. Homing groups: Y joints [1, 2] HOME_SEQUENCE -1; X joints [0] HOME_SEQUENCE 1; Z joints [3] HOME_SEQUENCE 0; - joints [4] HOME_SEQUENCE 2.
- Probe net: or2 - both probes normalised to 'triggered = 1' by their CONFIGURE_IO polarity, combined by one generated or2 whose output is the only writer of motion.probe-input; the setup service records which probe is fitted and active.
- Spindles: spindle.0 run do:0, do:1, speed ao:0, at-speed din:15, feedback none.
- Process interlock (XS1.3): XS1.3 open opens XPC0 and XPC1 only. No output of this sheet is on XPC0/XPC1, so XS1.3 removes nothing here; a spindle stop belongs in the EXT_PERMIT safety chain or needs the spindle run/STO input wired through XPC0.
- Note: M4 (ATC carousel) is LinuxCNC extra joint 4 (motmod num_extrajoints=1, [KINS]JOINTS=5): it homes with the joints, then the carousel component drives joint.4.posthome-cmd; enable, amp-fault and unhome follow the joint rules.

Spare after allocation: motor 3, encoder 4, di 2, do 1, freq 2, pwm 2, proc_en 2, ao 1, ai 4, rs485 1, can 1. Pendant selector inputs used: 6 of 10.

Optional additions checked against spare capacity: ENC0 spindle encoder for rigid tapping (fits: 4 encoders free); RS-485 Modbus VFD speed/direction plus DO0 as the hardware run-enable (fits; Modbus is never the only run path).

### B_mill_5axis_trunnion: 5-axis mill (A/C trunnion) with spindle encoder, rotary scales, umbrella ATC on a stepper, rotary clamps, through-spindle coolant

Hardware: Standard 8-motor controller. Interpretation: Separate X/Y/Z limit inputs would need 25 DI; this sheet uses one combined X/Y/Z overtravel chain (standard LinuxCNC practice, loses which-axis identification) to fit 23 DI. Variant B2 (separate limits) is recorded as NOT FITTING. LinuxCNC mapping: xyzac-trt-kins (TCP); [KINS]JOINTS=6 with num_extrajoints=1; joints 0-4 -> M0-M4; M5 carousel = extra joint 5; spindle.0 from ENC0 (revs, speed-in, index-enable).

| Function | Class | Channel | Terminal | Assumed load / peak | LinuxCNC mapping |
|---|---|---:|---|---|---|
| X joint | motor | 0 | XM0.1-14 | - | joint 0 (X); motor-pos-fb cnc1.0.position-fb |
| Y joint | motor | 1 | XM1.1-14 | - | joint 1 (Y); motor-pos-fb cnc1.1.position-fb |
| Z joint | motor | 2 | XM2.1-14 | - | joint 2 (Z); motor-pos-fb cnc1.2.position-fb |
| A (trunnion tilt) joint | motor | 3 | XM3.1-14 | - | joint 3 (A); motor-pos-fb cnc1.3.position-fb |
| C (rotary table) joint | motor | 4 | XM4.1-14 | - | joint 4 (C); motor-pos-fb cnc1.4.position-fb |
| Umbrella carousel stepper | motor | 5 | XM5.1-14 | - | joint 5 (-, extra joint); motor-pos-fb cnc1.5.position-fb |
| Spindle encoder (ABZ, index) | encoder | 0 | XE0.1-10 | - | spindle.0.revs <- cnc1.encoder.0.position; spindle.0.speed-in <- cnc1.encoder.0.velocity (scaled to rev/s); spindle.0.index-enable <-> cnc1.encoder.0.index-enable |
| A-axis rotary scale | encoder | 1 | XE1.1-10 | - | measured position of joint 3 for the preview overlay and the service disagreement check (no motor-pos-fb) |
| C-axis rotary scale | encoder | 2 | XE2.1-10 | - | measured position of joint 4 for the preview overlay and the service disagreement check (no motor-pos-fb) |
| Home X | di | 0 | XDI0.1 | - | joint.0.home-sw-in |
| Home Y | di | 1 | XDI0.2 | - | joint.1.home-sw-in |
| Home Z | di | 2 | XDI0.3 | - | joint.2.home-sw-in |
| Home A | di | 3 | XDI0.4 | - | joint.3.home-sw-in |
| Home C | di | 4 | XDI0.5 | - | joint.4.home-sw-in |
| Combined X/Y/Z overtravel chain (NC series) | di | 5 | XDI0.6 | - | joint.0.neg-lim-sw-in; joint.0.pos-lim-sw-in; joint.1.neg-lim-sw-in; joint.1.pos-lim-sw-in; joint.2.neg-lim-sw-in; joint.2.pos-lim-sw-in |
| A overtravel | di | 6 | XDI0.7 | - | joint.3.neg-lim-sw-in; joint.3.pos-lim-sw-in |
| Carousel home | di | 7 | XDI0.8 | - | joint.5.home-sw-in |
| Carousel arm in | di | 8 | XDI1.1 | - | motion.digital-in-00 |
| Carousel arm out | di | 9 | XDI1.2 | - | motion.digital-in-01 |
| Drawbar clamped | di | 10 | XDI1.3 | - | motion.digital-in-02 |
| Drawbar released | di | 11 | XDI1.4 | - | motion.digital-in-03 |
| A clamped | di | 12 | XDI1.5 | - | motion.digital-in-04 |
| C clamped | di | 13 | XDI1.6 | - | motion.digital-in-05 |
| Air OK | di | 14 | XDI1.7 | - | motion.digital-in-06 |
| Lube OK | di | 15 | XDI1.8 | - | motion.digital-in-07 |
| Coolant level OK | di | 16 | XDI2.1 | - | motion.digital-in-08 |
| Through-spindle coolant pressure OK | di | 17 | XDI2.2 | - | motion.digital-in-09 |
| Spindle ready | di | 18 | XDI2.3 | - | spindle.0.at-speed |
| Spindle fault | di | 19 | XDI2.4 | - | motion.digital-in-10 |
| Door closed (status) | di | 20 | XDI2.5 | - | motion.digital-in-11 |
| Cycle start | di | 21 | XDI2.6 | - | halui.program.run |
| Feed hold | di | 22 | XDI2.7 | - | halui.program.pause |
| 3D touch probe | probe | 0 | XPR.1 | - | or2.probe.in0 <- cnc1.probe.0.in |
| Tool setter | probe | 1 | XPR.4 | - | or2.probe.in1 <- cnc1.probe.1.in |
| Spindle run | do | 0 | XDO0.1 | 0.05 A / 0.05 A | written by spindle.0.forward |
| Spindle reverse | do | 1 | XDO0.2 | 0.05 A / 0.05 A | written by spindle.0.reverse |
| Drawbar release valve | do | 2 | XDO0.3 | 0.25 A / 0.25 A | written by motion.digital-out-00 |
| Cone air blast | do | 3 | XDO0.4 | 0.25 A / 0.25 A | written by motion.digital-out-01 |
| Carousel arm in valve | do | 4 | XDO0.5 | 0.25 A / 0.25 A | written by motion.digital-out-02 |
| Carousel arm out valve | do | 5 | XDO0.6 | 0.25 A / 0.25 A | written by motion.digital-out-03 |
| A clamp release valve (spring-applied clamp; energise to release, section 04 section 9) | do | 6 | XDO0.7 | 0.25 A / 0.2 A | written by motion.digital-out-04 |
| C clamp release valve (spring-applied clamp) | do | 7 | XDO0.8 | 0.25 A / 0.2 A | written by motion.digital-out-05 |
| Coolant flood (relay) | do | 8 | XDO1.1 | 0.05 A / 0.05 A (relay) | written by iocontrol.0.coolant-flood |
| Through-spindle coolant (relay) | do | 9 | XDO1.2 | 0.05 A / 0.05 A (relay) | written by iocontrol.0.coolant-mist |
| Lube pump (through an interposing relay; the pump start current is on the relay contact) | do | 10 | XDO1.3 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-06 |
| Chip conveyor (relay) | do | 11 | XDO1.4 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-07 |
| Z brake release (<= 0.5 A) | do | 12 | XDO1.5 | 0.5 A / 0.5 A | written by joint.2.amp-enable-out |
| Work light | do | 13 | XDO1.6 | 0.1 A / 0.3 A | written by motion.digital-out-08 |
| Spindle speed 0-10 V | ao | 0 | XAO.1-2 | - | written by spindle.0.speed-out-abs (scaled to volts) |
| Drive STO feedback | sto_fb | 0 | XS1.8 | - | - |
| Machine E-stop/safety relay output -> external permit | safety_ext_permit | 0 | XS1.2 | - | - |
| Process-enable interlock (gates XPC0/XPC1 only; not a spindle stop) | process_permit | 0 | XS1.3 | - | - |
| Safety relay diagnostic status | safety_status | 0 | XS1.4 | - | - |
| Reset/arm pushbutton with lamp | reset_arm | 0 | XS1.5 (+XS1.6 lamp) | - | - |
| Drive-power contactor mirror contact | contactor_fb | 0 | XS1.7 | - | - |
| Output permission contact in series with contactor request | permit_out | 0 | XS1.10-11 | - | - |
| Handwheel (MPG) with enable button | mpg | 0 | XH1.1-10 | - | - |
| Pendant axis select X | pendant_sel | 0 | XH2.1 | - | axis X |
| Pendant axis select Y | pendant_sel | 1 | XH2.2 | - | axis Y |
| Pendant axis select Z | pendant_sel | 2 | XH2.3 | - | axis Z |
| Pendant axis select A | pendant_sel | 3 | XH2.4 | - | axis A |
| Pendant axis select C | pendant_sel | 5 | XH2.6 | - | axis C |
| Pendant x1 | pendant_sel | 6 | XH2.7 | - | - |
| Pendant x10 | pendant_sel | 7 | XH2.8 | - | - |
| Pendant x100 | pendant_sel | 8 | XH2.9 | - | - |

- Joints: 5 kinematic + 1 extra = 6. Homing groups: Z joints [2] HOME_SEQUENCE 0; X joints [0] HOME_SEQUENCE 1; Y joints [1] HOME_SEQUENCE 1; A joints [3] HOME_SEQUENCE 2; C joints [4] HOME_SEQUENCE 2; - joints [5] HOME_SEQUENCE 3.
- Probe net: or2 - both probes normalised to 'triggered = 1' by their CONFIGURE_IO polarity, combined by one generated or2 whose output is the only writer of motion.probe-input; the setup service records which probe is fitted and active.
- Spindles: spindle.0 run do:0, do:1, speed ao:0, at-speed din:18, feedback encoder:0.
- Process interlock (XS1.3): XS1.3 open opens XPC0 and XPC1 only. No output of this sheet is on XPC0/XPC1, so XS1.3 removes nothing here; a spindle stop belongs in the EXT_PERMIT safety chain or needs the spindle run/STO input wired through XPC0.
- Note: M5 (umbrella carousel) is extra joint 5 (num_extrajoints=1, [KINS]JOINTS=6).
- Note: the A/C rotary scales are measured-only in this sheet; a closed-loop variant with pid is a profile option.

Spare after allocation: motor 2, encoder 1, di 1, do 2, freq 2, pwm 2, proc_en 2, ao 1, ai 4, rs485 1, can 1. Pendant selector inputs used: 8 of 10.

**Does not fit - B2_separate_limits:** Separate X, Y and Z overtravel inputs need 25 general DI; 24 exist. Short by 1 DI. Resolution: Use B (combined chain), or move cycle start/feed hold onto the pendant (only if those buttons are physically on the pendant), or add the optional industrial-I/O module (proposal, not in the standard product). Never drop a limit silently.

Optional additions checked against spare capacity: Spindle speed/direction via Modbus RS-485 plus DO0 as the hardware run-enable (fits; Modbus is never the only run path); ENC3 linear scale (fits: 1 encoder free).

### C_lathe: Lathe with spindle encoder (threading/CSS), stepper-indexed turret, hydraulic chuck and tailstock

Hardware: Standard 8-motor controller. Interpretation: Turret indexed by a stepper on M2 (HAL indexer + lock valve); chuck and tailstock by valves with position confirmation; spindle encoder with index for G33/G76 and CSS. LinuxCNC mapping: trivkins coordinates=XZ; [KINS]JOINTS=3 with num_extrajoints=1; joints 0-1 -> M0-M1; M2 turret = extra joint 2; spindle.0.revs/speed-in/index-enable from ENC0; lathe mode in the INI.

| Function | Class | Channel | Terminal | Assumed load / peak | LinuxCNC mapping |
|---|---|---:|---|---|---|
| X joint | motor | 0 | XM0.1-14 | - | joint 0 (X); motor-pos-fb cnc1.0.position-fb |
| Z joint | motor | 1 | XM1.1-14 | - | joint 1 (Z); motor-pos-fb cnc1.1.position-fb |
| Turret indexer stepper | motor | 2 | XM2.1-14 | - | joint 2 (-, extra joint); motor-pos-fb cnc1.2.position-fb |
| Spindle encoder A/B/index (threading) | encoder | 0 | XE0.1-10 | - | spindle.0.revs <- cnc1.encoder.0.position; spindle.0.speed-in <- cnc1.encoder.0.velocity (scaled to rev/s); spindle.0.index-enable <-> cnc1.encoder.0.index-enable |
| Home X | di | 0 | XDI0.1 | - | joint.0.home-sw-in |
| Home Z | di | 1 | XDI0.2 | - | joint.1.home-sw-in |
| Limit X | di | 2 | XDI0.3 | - | joint.0.neg-lim-sw-in; joint.0.pos-lim-sw-in |
| Limit Z | di | 3 | XDI0.4 | - | joint.1.neg-lim-sw-in; joint.1.pos-lim-sw-in |
| Turret home | di | 4 | XDI0.5 | - | joint.2.home-sw-in |
| Turret locked | di | 5 | XDI0.6 | - | motion.digital-in-00 |
| Chuck clamped | di | 6 | XDI0.7 | - | motion.digital-in-01 |
| Chuck open | di | 7 | XDI0.8 | - | motion.digital-in-02 |
| Tailstock advanced | di | 8 | XDI1.1 | - | motion.digital-in-03 |
| Tailstock retracted | di | 9 | XDI1.2 | - | motion.digital-in-04 |
| Hydraulic pressure OK | di | 10 | XDI1.3 | - | motion.digital-in-05 |
| Lube OK | di | 11 | XDI1.4 | - | motion.digital-in-06 |
| Coolant level OK | di | 12 | XDI1.5 | - | motion.digital-in-07 |
| Spindle ready | di | 13 | XDI1.6 | - | spindle.0.at-speed |
| Spindle fault | di | 14 | XDI1.7 | - | motion.digital-in-08 |
| Door closed (status) | di | 15 | XDI1.8 | - | motion.digital-in-09 |
| Chuck foot pedal | di | 16 | XDI2.1 | - | motion.digital-in-10 |
| Tailstock foot pedal | di | 17 | XDI2.2 | - | motion.digital-in-11 |
| Cycle start | di | 18 | XDI2.3 | - | halui.program.run |
| Feed hold | di | 19 | XDI2.4 | - | halui.program.pause |
| Tool setter arm contact | probe | 1 | XPR.4 | - | motion.probe-input <- cnc1.probe.1.in |
| Spindle run | do | 0 | XDO0.1 | 0.05 A / 0.05 A | written by spindle.0.forward |
| Spindle reverse | do | 1 | XDO0.2 | 0.05 A / 0.05 A | written by spindle.0.reverse |
| Chuck clamp coil of a bistable (detented) valve - holds position on de-energise (section 04 section 9) | do | 2 | XDO0.3 | 0.25 A / 0.2 A | written by motion.digital-out-00 |
| Chuck unclamp coil of the bistable valve (interlocked: spindle stopped) | do | 3 | XDO0.4 | 0.25 A / 0.2 A | written by motion.digital-out-01 |
| Tailstock advance coil (bistable valve) | do | 4 | XDO0.5 | 0.25 A / 0.25 A | written by motion.digital-out-02 |
| Tailstock retract coil (bistable valve) | do | 5 | XDO0.6 | 0.25 A / 0.25 A | written by motion.digital-out-03 |
| Turret lock valve | do | 6 | XDO0.7 | 0.25 A / 0.25 A | written by motion.digital-out-04 |
| Coolant (relay) | do | 7 | XDO0.8 | 0.05 A / 0.05 A (relay) | written by iocontrol.0.coolant-flood |
| Lube pump (through an interposing relay; the pump start current is on the relay contact) | do | 8 | XDO1.1 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-05 |
| Chip conveyor (relay) | do | 9 | XDO1.2 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-06 |
| Work light | do | 10 | XDO1.3 | 0.1 A / 0.3 A | written by motion.digital-out-07 |
| Hydraulic pump (relay) | do | 11 | XDO1.4 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-08 |
| Spindle speed 0-10 V | ao | 0 | XAO.1-2 | - | written by spindle.0.speed-out-abs (scaled to volts) |
| Drive STO feedback | sto_fb | 0 | XS1.8 | - | - |
| Machine E-stop/safety relay output -> external permit | safety_ext_permit | 0 | XS1.2 | - | - |
| Process-enable interlock (gates XPC0/XPC1 only; not a spindle stop) | process_permit | 0 | XS1.3 | - | - |
| Safety relay diagnostic status | safety_status | 0 | XS1.4 | - | - |
| Reset/arm pushbutton with lamp | reset_arm | 0 | XS1.5 (+XS1.6 lamp) | - | - |
| Drive-power contactor mirror contact | contactor_fb | 0 | XS1.7 | - | - |
| Output permission contact in series with contactor request | permit_out | 0 | XS1.10-11 | - | - |
| Handwheel (MPG) with enable button | mpg | 0 | XH1.1-10 | - | - |
| Pendant axis select X | pendant_sel | 0 | XH2.1 | - | axis X |
| Pendant axis select Z | pendant_sel | 2 | XH2.3 | - | axis Z |
| Pendant x1 | pendant_sel | 6 | XH2.7 | - | - |
| Pendant x10 | pendant_sel | 7 | XH2.8 | - | - |
| Pendant x100 | pendant_sel | 8 | XH2.9 | - | - |

- Joints: 2 kinematic + 1 extra = 3. Homing groups: X joints [0] HOME_SEQUENCE 0; Z joints [1] HOME_SEQUENCE 1; - joints [2] HOME_SEQUENCE 2.
- Probe net: direct - single probe wired directly: cnc1.probe.1.in is the only writer of motion.probe-input.
- Spindles: spindle.0 run do:0, do:1, speed ao:0, at-speed din:13, feedback encoder:0.
- Process interlock (XS1.3): XS1.3 open opens XPC0 and XPC1 only. No output of this sheet is on XPC0/XPC1, so XS1.3 removes nothing here; a spindle stop belongs in the EXT_PERMIT safety chain or needs the spindle run/STO input wired through XPC0.
- Note: M2 (turret) is extra joint 2 (num_extrajoints=1, [KINS]JOINTS=3).
- Note: optional C axis on M3 would be kinematic joint 2 and the turret would become extra joint 3: joint and channel numbers differ, so unhome and enable follow the channel-to-joint map, never the channel number.

Spare after allocation: motor 5, encoder 3, di 4, do 4, probe 1, freq 2, pwm 2, proc_en 2, ao 1, ai 4, rs485 1, can 1. Pendant selector inputs used: 5 of 10.

Optional additions checked against spare capacity: C-axis/live tooling motor on M3 with its encoder on ENC1 (fits).

Safety note: Chuck-open-while-spinning protection must be part of the machine safety design (a pressure switch in the EXT_PERMIT safety chain, XS1.2), not only the DO3 software interlock. XS1.3 gates only the process-enable contacts XPC0/XPC1 and does not stop the spindle in this sheet.

### D_plasma: Plasma table: dual-Y gantry, torch height Z, divided-voltage THC module on FREQ0, torch start, Arc OK, float switch, breakaway; ohmic sensing only with a qualified external ohmic module (not specified in IS-1)

Hardware: Standard 8-motor controller + plasma.divided_voltage.v1 module (separately rated, own identity) on XF. Interpretation: Arc voltage enters only through the isolated plasma.divided_voltage.v1 module into FREQ0; raw arc voltage never reaches any controller terminal. Arc OK and torch start are wired direct (DI7, XPC0) only when the source's CNC port provides a dry Arc OK contact and a torch-start input within the XPC contact rating (0-30 V, <= 50 mA); otherwise both pass through the module. This supersedes PLASMA_MODULE_SYSTEM section 2's 'module provides Arc OK and torch start' for sources that meet those conditions; the module still carries the divided voltage. Float switch uses PRB0 (hardware capture during probe-down); PRB1 takes the contact output of an external ohmic module, which is not specified in IS-1; ohmic enable uses process enable 1. HF-start sources with ohmic sensing are rejected by profile. LinuxCNC mapping: trivkins coordinates=XYYZ; [KINS]JOINTS=4; plasmac component: arc-voltage-in from cnc1.freq.0 via the module calibration chain; arc-ok-in from DI7; float-switch from PRB0, ohmic-probe from PRB1; torch-on -> cnc1.proc-en.0.

| Function | Class | Channel | Terminal | Assumed load / peak | LinuxCNC mapping |
|---|---|---:|---|---|---|
| X joint | motor | 0 | XM0.1-14 | - | joint 0 (X); motor-pos-fb cnc1.0.position-fb |
| Y1 joint | motor | 1 | XM1.1-14 | - | joint 1 (Y); motor-pos-fb cnc1.1.position-fb |
| Y2 joint | motor | 2 | XM2.1-14 | - | joint 2 (Y); motor-pos-fb cnc1.2.position-fb |
| Z (torch height) joint | motor | 3 | XM3.1-14 | - | joint 3 (Z); motor-pos-fb cnc1.3.position-fb |
| Arc voltage (divided-voltage module, frequency; module presence XF.8 and 1-Wire identity XF.7 bind the module record) (FREQ1 declared 'absent' in the module record) | freq | 0 | XF.3-4 | - | plasmac.arc-voltage-in <- cnc1.freq.0.frequency through the module calibration |
| Torch start (isolated contact to source CNC port) | proc_en | 0 | XPC0.1-2 | - | written by plasmac.torch-on |
| Ohmic sensing enable (external ohmic module, not specified in IS-1) | proc_en | 1 | XPC1.1-2 | - | written by plasmac.ohmic-enable |
| Float switch (captured) | probe | 0 | XPR.1 | - | plasmac.float-switch <- cnc1.probe.0.in |
| Ohmic contact sense (requires a qualified external ohmic module, not specified in IS-1) | probe | 1 | XPR.4 | - | plasmac.ohmic-probe <- cnc1.probe.1.in |
| Home X | di | 0 | XDI0.1 | - | joint.0.home-sw-in |
| Home Y1 | di | 1 | XDI0.2 | - | joint.1.home-sw-in |
| Home Y2 | di | 2 | XDI0.3 | - | joint.2.home-sw-in |
| Home Z (top) | di | 3 | XDI0.4 | - | joint.3.home-sw-in |
| Limit X | di | 4 | XDI0.5 | - | joint.0.neg-lim-sw-in; joint.0.pos-lim-sw-in |
| Limit Y1 | di | 5 | XDI0.6 | - | joint.1.neg-lim-sw-in; joint.1.pos-lim-sw-in |
| Limit Y2 | di | 6 | XDI0.7 | - | joint.2.neg-lim-sw-in; joint.2.pos-lim-sw-in |
| Arc OK (source contact, wetted from sensor supply) | di | 7 | XDI0.8 | - | plasmac.arc-ok-in |
| Torch breakaway | di | 8 | XDI1.1 | - | plasmac.breakaway |
| Plasma source ready/fault status | di | 9 | XDI1.2 | - | motion.digital-in-00 |
| Air pressure OK | di | 10 | XDI1.3 | - | motion.digital-in-01 |
| Water table level | di | 11 | XDI1.4 | - | motion.digital-in-02 |
| Fume extraction running | di | 12 | XDI1.5 | - | motion.digital-in-03 |
| Cycle start | di | 13 | XDI1.6 | - | halui.program.run |
| Feed hold | di | 14 | XDI1.7 | - | halui.program.pause |
| Fume extraction fan (relay) | do | 0 | XDO0.1 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-00 |
| Water table pump (relay) | do | 1 | XDO0.2 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-01 |
| Scribe/marker valve | do | 2 | XDO0.3 | 0.25 A / 0.25 A | written by motion.digital-out-02 |
| Laser crosshair pointer | do | 3 | XDO0.4 | 0.1 A / 0.2 A | written by motion.digital-out-03 |
| Z brake release (<= 0.5 A) | do | 4 | XDO0.5 | 0.5 A / 0.5 A | written by joint.3.amp-enable-out |
| Stack light green | do | 5 | XDO0.6 | 0.1 A / 0.2 A | written by motion.digital-out-04 |
| Stack light red | do | 6 | XDO0.7 | 0.1 A / 0.2 A | written by motion.digital-out-05 |
| Drive STO feedback | sto_fb | 0 | XS1.8 | - | - |
| Machine E-stop/safety relay output -> external permit | safety_ext_permit | 0 | XS1.2 | - | - |
| Process-enable interlock (gates XPC0/XPC1 only; not a spindle stop) | process_permit | 0 | XS1.3 | - | - |
| Safety relay diagnostic status | safety_status | 0 | XS1.4 | - | - |
| Reset/arm pushbutton with lamp | reset_arm | 0 | XS1.5 (+XS1.6 lamp) | - | - |
| Drive-power contactor mirror contact | contactor_fb | 0 | XS1.7 | - | - |
| Output permission contact in series with contactor request | permit_out | 0 | XS1.10-11 | - | - |
| Handwheel (MPG) with enable button | mpg | 0 | XH1.1-10 | - | - |
| Pendant axis select X | pendant_sel | 0 | XH2.1 | - | axis X |
| Pendant axis select Y | pendant_sel | 1 | XH2.2 | - | axis Y |
| Pendant axis select Z | pendant_sel | 2 | XH2.3 | - | axis Z |
| Pendant x1 | pendant_sel | 6 | XH2.7 | - | - |
| Pendant x10 | pendant_sel | 7 | XH2.8 | - | - |
| Pendant x100 | pendant_sel | 8 | XH2.9 | - | - |

- Joints: 4 kinematic + 0 extra = 4. Homing groups: Y joints [1, 2] HOME_SEQUENCE -1; Z joints [3] HOME_SEQUENCE 0; X joints [0] HOME_SEQUENCE 1.
- Probe net: plasmac - PRB0 -> plasmac.float-switch and PRB1 -> plasmac.ohmic-probe, one writer each; motion.probe-input is not used.
- Process interlock (XS1.3): XS1.3 open opens XPC0 and XPC1 only. It gates the torch start and the ohmic enable in this sheet.
- Note: Ohmic sensing needs a separately qualified external ohmic module; it is not specified in IS-1 (PRB1 accepts its isolated contact output).

Spare after allocation: motor 4, encoder 4, di 9, do 9, freq 1, pwm 2, ao 2, ai 4, rs485 1, can 1. Pendant selector inputs used: 6 of 10.

Optional additions checked against spare capacity: Powermax RS-485 remote settings via XB1 on a supported source option (profile-specific).

Safety note: Torch start closes only with PROC_PERMIT (OUT_PERMIT AND TX_PERMIT AND the XS1.3 process interlock). HF-start sources combined with ohmic sensing are rejected by the profile (QtPlasmaC caution, PLASMA_MODULE_SYSTEM section 6). Raw arc voltage never enters any controller terminal.

### E_twelve_motor_with_encoder_expansion: Twelve-motor multi-head gantry machine, every motor with encoder feedback (MX4 + EX8 fitted together)

Hardware: Twelve-motor controller: MX4 motor expansion + EX8 encoder expansion + XTB terminal board, all factory-fitted. Interpretation: Joint map follows the sim-12motor profile (XYYZABCUVWZZ): gantry Y1/Y2, three ganged plunging heads (Z, Z2, Z3 share the Z coordinate and move together), A/C head, B rotary table, U/V/W offset slides. All twelve drives return ABZ to ENC0-ENC11. The three spindles take speed and direction over Modbus RS-485 and each has a hardware run-enable on DO12-DO14, so a bus failure, host crash or permission loss stops them. LinuxCNC mapping: trivkins coordinates=XYYZABCUVWZZ kinstype=BOTH; motmod num_joints=12 (module-load tested only, MOTION_EXPANSION section 10), num_spindles=3; each joint's motor-pos-fb from its own encoder only.

| Function | Class | Channel | Terminal | Assumed load / peak | LinuxCNC mapping |
|---|---|---:|---|---|---|
| Joint 0 (X) | motor | 0 | XM0.1-14 | - | joint 0 (X); motor-pos-fb cnc1.encoder.0.position |
| Joint 1 (Y1) | motor | 1 | XM1.1-14 | - | joint 1 (Y); motor-pos-fb cnc1.encoder.1.position |
| Joint 2 (Y2) | motor | 2 | XM2.1-14 | - | joint 2 (Y); motor-pos-fb cnc1.encoder.2.position |
| Joint 3 (Z) | motor | 3 | XM3.1-14 | - | joint 3 (Z); motor-pos-fb cnc1.encoder.3.position |
| Joint 4 (A) | motor | 4 | XM4.1-14 | - | joint 4 (A); motor-pos-fb cnc1.encoder.4.position |
| Joint 5 (B) | motor | 5 | XM5.1-14 | - | joint 5 (B); motor-pos-fb cnc1.encoder.5.position |
| Joint 6 (C) | motor | 6 | XM6.1-14 | - | joint 6 (C); motor-pos-fb cnc1.encoder.6.position |
| Joint 7 (U) | motor | 7 | XM7.1-14 | - | joint 7 (U); motor-pos-fb cnc1.encoder.7.position |
| Joint 8 (V) | motor | 8 | XM8.1-14 | - | joint 8 (V); motor-pos-fb cnc1.encoder.8.position |
| Joint 9 (W) | motor | 9 | XM9.1-14 | - | joint 9 (W); motor-pos-fb cnc1.encoder.9.position |
| Joint 10 (Z2) | motor | 10 | XM10.1-14 | - | joint 10 (Z); motor-pos-fb cnc1.encoder.10.position |
| Joint 11 (Z3) | motor | 11 | XM11.1-14 | - | joint 11 (Z); motor-pos-fb cnc1.encoder.11.position |
| Motor M0 encoder feedback | encoder | 0 | XE0.1-10 | - | joint.0.motor-pos-fb <- cnc1.encoder.0.position (the only pos_fb source of joint 0) |
| Motor M1 encoder feedback | encoder | 1 | XE1.1-10 | - | joint.1.motor-pos-fb <- cnc1.encoder.1.position (the only pos_fb source of joint 1) |
| Motor M2 encoder feedback | encoder | 2 | XE2.1-10 | - | joint.2.motor-pos-fb <- cnc1.encoder.2.position (the only pos_fb source of joint 2) |
| Motor M3 encoder feedback | encoder | 3 | XE3.1-10 | - | joint.3.motor-pos-fb <- cnc1.encoder.3.position (the only pos_fb source of joint 3) |
| Motor M4 encoder feedback | encoder | 4 | XE4.1-10 | - | joint.4.motor-pos-fb <- cnc1.encoder.4.position (the only pos_fb source of joint 4) |
| Motor M5 encoder feedback | encoder | 5 | XE5.1-10 | - | joint.5.motor-pos-fb <- cnc1.encoder.5.position (the only pos_fb source of joint 5) |
| Motor M6 encoder feedback | encoder | 6 | XE6.1-10 | - | joint.6.motor-pos-fb <- cnc1.encoder.6.position (the only pos_fb source of joint 6) |
| Motor M7 encoder feedback | encoder | 7 | XE7.1-10 | - | joint.7.motor-pos-fb <- cnc1.encoder.7.position (the only pos_fb source of joint 7) |
| Motor M8 encoder feedback | encoder | 8 | XE8.1-10 | - | joint.8.motor-pos-fb <- cnc1.encoder.8.position (the only pos_fb source of joint 8) |
| Motor M9 encoder feedback | encoder | 9 | XE9.1-10 | - | joint.9.motor-pos-fb <- cnc1.encoder.9.position (the only pos_fb source of joint 9) |
| Motor M10 encoder feedback | encoder | 10 | XE10.1-10 | - | joint.10.motor-pos-fb <- cnc1.encoder.10.position (the only pos_fb source of joint 10) |
| Motor M11 encoder feedback | encoder | 11 | XE11.1-10 | - | joint.11.motor-pos-fb <- cnc1.encoder.11.position (the only pos_fb source of joint 11) |
| Home joint 0 | di | 0 | XDI0.1 | - | joint.0.home-sw-in |
| Home joint 1 | di | 1 | XDI0.2 | - | joint.1.home-sw-in |
| Home joint 2 | di | 2 | XDI0.3 | - | joint.2.home-sw-in |
| Home joint 3 | di | 3 | XDI0.4 | - | joint.3.home-sw-in |
| Home joint 4 | di | 4 | XDI0.5 | - | joint.4.home-sw-in |
| Home joint 5 | di | 5 | XDI0.6 | - | joint.5.home-sw-in |
| Home joint 6 | di | 6 | XDI0.7 | - | joint.6.home-sw-in |
| Home joint 7 | di | 7 | XDI0.8 | - | joint.7.home-sw-in |
| Home joint 8 | di | 8 | XDI1.1 | - | joint.8.home-sw-in |
| Home joint 9 | di | 9 | XDI1.2 | - | joint.9.home-sw-in |
| Home joint 10 | di | 10 | XDI1.3 | - | joint.10.home-sw-in |
| Home joint 11 | di | 11 | XDI1.4 | - | joint.11.home-sw-in |
| Limit X | di | 12 | XDI1.5 | - | joint.0.neg-lim-sw-in; joint.0.pos-lim-sw-in |
| Limit Y1 | di | 13 | XDI1.6 | - | joint.1.neg-lim-sw-in; joint.1.pos-lim-sw-in |
| Limit Y2 | di | 14 | XDI1.7 | - | joint.2.neg-lim-sw-in; joint.2.pos-lim-sw-in |
| Head Z/Z2/Z3 top overtravel chain | di | 15 | XDI1.8 | - | joint.3.pos-lim-sw-in; joint.10.pos-lim-sw-in; joint.11.pos-lim-sw-in |
| Air OK | di | 16 | XDI2.1 | - | motion.digital-in-00 |
| Lube OK | di | 17 | XDI2.2 | - | motion.digital-in-01 |
| Cycle start | di | 18 | XDI2.3 | - | halui.program.run |
| Feed hold | di | 19 | XDI2.4 | - | halui.program.pause |
| Door closed (status) | di | 20 | XDI2.5 | - | motion.digital-in-02 |
| Dust collector running | di | 21 | XDI2.6 | - | motion.digital-in-03 |
| Spindle VFDs x3 (Modbus RTU) | rs485 | 0 | XB1.1-6 | - | - |
| Tool setter | probe | 1 | XPR.4 | - | or2.probe.in1 <- cnc1.probe.1.in |
| Touch probe | probe | 0 | XPR.1 | - | or2.probe.in0 <- cnc1.probe.0.in |
| Head 1 dust hood valve | do | 0 | XDO0.1 | 0.25 A / 0.25 A | written by motion.digital-out-00 |
| Head 2 dust hood valve | do | 1 | XDO0.2 | 0.25 A / 0.25 A | written by motion.digital-out-01 |
| Head 3 dust hood valve | do | 2 | XDO0.3 | 0.25 A / 0.25 A | written by motion.digital-out-02 |
| Head 1 mist | do | 3 | XDO0.4 | 0.25 A / 0.25 A | written by motion.digital-out-03 |
| Head 2 mist | do | 4 | XDO0.5 | 0.25 A / 0.25 A | written by motion.digital-out-04 |
| Head 3 mist | do | 5 | XDO0.6 | 0.25 A / 0.25 A | written by motion.digital-out-05 |
| Lube pump (through an interposing relay; the pump start current is on the relay contact) | do | 6 | XDO0.7 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-06 |
| Dust collector (relay) | do | 7 | XDO0.8 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-07 |
| Z brake (<= 0.5 A) | do | 8 | XDO1.1 | 0.5 A / 0.5 A | written by joint.3.amp-enable-out |
| Z2 brake (<= 0.5 A) | do | 9 | XDO1.2 | 0.5 A / 0.5 A | written by joint.10.amp-enable-out |
| Z3 brake (<= 0.5 A) | do | 10 | XDO1.3 | 0.5 A / 0.5 A | written by joint.11.amp-enable-out |
| Work light | do | 11 | XDO1.4 | 0.1 A / 0.3 A | written by motion.digital-out-08 |
| Drive STO feedback | sto_fb | 0 | XS1.8 | - | - |
| Machine E-stop/safety relay output -> external permit | safety_ext_permit | 0 | XS1.2 | - | - |
| Process-enable interlock (gates XPC0/XPC1 only; not a spindle stop) | process_permit | 0 | XS1.3 | - | - |
| Safety relay diagnostic status | safety_status | 0 | XS1.4 | - | - |
| Reset/arm pushbutton with lamp | reset_arm | 0 | XS1.5 (+XS1.6 lamp) | - | - |
| Drive-power contactor mirror contact | contactor_fb | 0 | XS1.7 | - | - |
| Output permission contact in series with contactor request | permit_out | 0 | XS1.10-11 | - | - |
| Handwheel (MPG) with enable button | mpg | 0 | XH1.1-10 | - | - |
| Pendant axis select X | pendant_sel | 0 | XH2.1 | - | axis X |
| Pendant axis select Y | pendant_sel | 1 | XH2.2 | - | axis Y |
| Pendant axis select Z | pendant_sel | 2 | XH2.3 | - | axis Z |
| Pendant axis select A | pendant_sel | 3 | XH2.4 | - | axis A |
| Pendant axis select B | pendant_sel | 4 | XH2.5 | - | axis B |
| Pendant axis select C | pendant_sel | 5 | XH2.6 | - | axis C |
| Pendant x1 | pendant_sel | 6 | XH2.7 | - | - |
| Pendant x10 | pendant_sel | 7 | XH2.8 | - | - |
| Pendant x100 | pendant_sel | 8 | XH2.9 | - | - |
| Spindle 1 VFD run-enable (hardware; Modbus carries speed and direction) | do | 12 | XDO1.5 | 0.05 A / 0.05 A | written by spindle.0.on |
| Spindle 2 VFD run-enable (hardware) | do | 13 | XDO1.6 | 0.05 A / 0.05 A | written by spindle.1.on |
| Spindle 3 VFD run-enable (hardware) | do | 14 | XDO1.7 | 0.05 A / 0.05 A | written by spindle.2.on |

- Joints: 12 kinematic + 0 extra = 12. Homing groups: Y joints [1, 2] HOME_SEQUENCE -1; Z joints [3, 10, 11] HOME_SEQUENCE -2; X joints [0] HOME_SEQUENCE 3; A joints [4] HOME_SEQUENCE 4; B joints [5] HOME_SEQUENCE 4; C joints [6] HOME_SEQUENCE 4; U joints [7] HOME_SEQUENCE 5; V joints [8] HOME_SEQUENCE 5; W joints [9] HOME_SEQUENCE 5.
- Probe net: or2 - both probes normalised to 'triggered = 1' by their CONFIGURE_IO polarity, combined by one generated or2 whose output is the only writer of motion.probe-input; the setup service records which probe is fitted and active.
- Spindles: spindle.0 run do:12, speed rs485:modbus, at-speed modbus status, feedback none; spindle.1 run do:13, speed rs485:modbus, at-speed modbus status, feedback none; spindle.2 run do:14, speed rs485:modbus, at-speed modbus status, feedback none.
- Process interlock (XS1.3): XS1.3 open opens XPC0 and XPC1 only. No output of this sheet is on XPC0/XPC1, so XS1.3 removes nothing here; a spindle stop belongs in the EXT_PERMIT safety chain or needs the spindle run/STO input wired through XPC0.
- Note: Z, Z2 and Z3 are duplicate trivkins Z letters, so they move together as one ganged axis; independent plunging heads are not possible with the nine letters XYZABCUVW already in use.
- Note: each joint's motor-pos-fb comes from its encoder only; the step count cnc1.C.position-fb is not connected to motor-pos-fb in this sheet.

Spare after allocation: di 2, do 1, freq 2, pwm 2, proc_en 2, ao 2, ai 4, can 1. Pendant selector inputs used: 9 of 10.

**Does not fit - E2_plus_spindle_encoder:** A spindle encoder would be a 13th ABZ encoder; 12 exist with EX8 fitted. Short by 1 encoder. Resolution: Run one non-critical motor (e.g. an offset slide) without external feedback, or use a Modbus spindle speed/position report for non-synchronized work. The MPG has its own receiver and is unaffected.

### F_twelve_motor_open_loop: Twelve-motor configuration without encoder expansion (MX4 only)

Hardware: MX4 + XTB, no EX8. Interpretation: Same joint map as E with open-loop drives; 4 base encoders used for spindle + 3 scales. Shows the motor expansion does not require the encoder expansion. LinuxCNC mapping: trivkins coordinates=XYYZABCUVWZZ kinstype=BOTH.

| Function | Class | Channel | Terminal | Assumed load / peak | LinuxCNC mapping |
|---|---|---:|---|---|---|
| Joint 0 | motor | 0 | XM0.1-14 | - | joint 0 (X); motor-pos-fb cnc1.0.position-fb |
| Joint 1 | motor | 1 | XM1.1-14 | - | joint 1 (Y); motor-pos-fb cnc1.1.position-fb |
| Joint 2 | motor | 2 | XM2.1-14 | - | joint 2 (Y); motor-pos-fb cnc1.2.position-fb |
| Joint 3 | motor | 3 | XM3.1-14 | - | joint 3 (Z); motor-pos-fb cnc1.3.position-fb |
| Joint 4 | motor | 4 | XM4.1-14 | - | joint 4 (A); motor-pos-fb cnc1.4.position-fb |
| Joint 5 | motor | 5 | XM5.1-14 | - | joint 5 (B); motor-pos-fb cnc1.5.position-fb |
| Joint 6 | motor | 6 | XM6.1-14 | - | joint 6 (C); motor-pos-fb cnc1.6.position-fb |
| Joint 7 | motor | 7 | XM7.1-14 | - | joint 7 (U); motor-pos-fb cnc1.7.position-fb |
| Joint 8 | motor | 8 | XM8.1-14 | - | joint 8 (V); motor-pos-fb cnc1.8.position-fb |
| Joint 9 | motor | 9 | XM9.1-14 | - | joint 9 (W); motor-pos-fb cnc1.9.position-fb |
| Joint 10 | motor | 10 | XM10.1-14 | - | joint 10 (Z); motor-pos-fb cnc1.10.position-fb |
| Joint 11 | motor | 11 | XM11.1-14 | - | joint 11 (Z); motor-pos-fb cnc1.11.position-fb |
| Spindle encoder | encoder | 0 | XE0.1-10 | - | spindle.0.revs <- cnc1.encoder.0.position; spindle.0.speed-in <- cnc1.encoder.0.velocity (scaled to rev/s); spindle.0.index-enable <-> cnc1.encoder.0.index-enable |
| X scale | encoder | 1 | XE1.1-10 | - | measured position of joint 0 (preview overlay and disagreement check) |
| Y1 scale | encoder | 2 | XE2.1-10 | - | measured position of joint 1 (preview overlay and disagreement check) |
| Y2 scale | encoder | 3 | XE3.1-10 | - | measured position of joint 2 (preview overlay and disagreement check) |
| Home joint 0 | di | 0 | XDI0.1 | - | joint.0.home-sw-in |
| Home joint 1 | di | 1 | XDI0.2 | - | joint.1.home-sw-in |
| Home joint 2 | di | 2 | XDI0.3 | - | joint.2.home-sw-in |
| Home joint 3 | di | 3 | XDI0.4 | - | joint.3.home-sw-in |
| Home joint 4 | di | 4 | XDI0.5 | - | joint.4.home-sw-in |
| Home joint 5 | di | 5 | XDI0.6 | - | joint.5.home-sw-in |
| Home joint 6 | di | 6 | XDI0.7 | - | joint.6.home-sw-in |
| Home joint 7 | di | 7 | XDI0.8 | - | joint.7.home-sw-in |
| Home joint 8 | di | 8 | XDI1.1 | - | joint.8.home-sw-in |
| Home joint 9 | di | 9 | XDI1.2 | - | joint.9.home-sw-in |
| Home joint 10 | di | 10 | XDI1.3 | - | joint.10.home-sw-in |
| Home joint 11 | di | 11 | XDI1.4 | - | joint.11.home-sw-in |
| Limit chain | di | 12 | XDI1.5 | - | joint.0.neg-lim-sw-in; joint.0.pos-lim-sw-in; joint.1.neg-lim-sw-in; joint.1.pos-lim-sw-in; joint.2.neg-lim-sw-in; joint.2.pos-lim-sw-in; joint.3.neg-lim-sw-in; joint.3.pos-lim-sw-in; joint.4.neg-lim-sw-in; joint.4.pos-lim-sw-in; joint.5.neg-lim-sw-in; joint.5.pos-lim-sw-in; joint.6.neg-lim-sw-in; joint.6.pos-lim-sw-in; joint.7.neg-lim-sw-in; joint.7.pos-lim-sw-in; joint.8.neg-lim-sw-in; joint.8.pos-lim-sw-in; joint.9.neg-lim-sw-in; joint.9.pos-lim-sw-in; joint.10.neg-lim-sw-in; joint.10.pos-lim-sw-in; joint.11.neg-lim-sw-in; joint.11.pos-lim-sw-in |
| Cycle start | di | 13 | XDI1.6 | - | halui.program.run |
| Feed hold | di | 14 | XDI1.7 | - | halui.program.pause |
| Lube pump (through an interposing relay; the pump start current is on the relay contact) | do | 0 | XDO0.1 | 0.05 A / 0.05 A (relay) | written by motion.digital-out-00 |
| Z brake (<= 0.5 A) | do | 1 | XDO0.2 | 0.5 A / 0.5 A | written by joint.3.amp-enable-out |
| Spindle run | do | 2 | XDO0.3 | 0.05 A / 0.05 A | written by spindle.0.forward |
| Spindle speed | ao | 0 | XAO.1-2 | - | written by spindle.0.speed-out-abs (scaled to volts) |
| Machine E-stop/safety relay output -> external permit | safety_ext_permit | 0 | XS1.2 | - | - |
| Process-enable interlock (gates XPC0/XPC1 only; not a spindle stop) | process_permit | 0 | XS1.3 | - | - |
| Safety relay diagnostic status | safety_status | 0 | XS1.4 | - | - |
| Reset/arm pushbutton with lamp | reset_arm | 0 | XS1.5 (+XS1.6 lamp) | - | - |
| Drive-power contactor mirror contact | contactor_fb | 0 | XS1.7 | - | - |
| Output permission contact in series with contactor request | permit_out | 0 | XS1.10-11 | - | - |
| Handwheel (MPG) with enable button | mpg | 0 | XH1.1-10 | - | - |
| Pendant axis select X | pendant_sel | 0 | XH2.1 | - | axis X |
| Pendant axis select Y | pendant_sel | 1 | XH2.2 | - | axis Y |
| Pendant axis select Z | pendant_sel | 2 | XH2.3 | - | axis Z |
| Pendant x1 | pendant_sel | 6 | XH2.7 | - | - |
| Pendant x10 | pendant_sel | 7 | XH2.8 | - | - |
| Pendant x100 | pendant_sel | 8 | XH2.9 | - | - |

- Joints: 12 kinematic + 0 extra = 12. Homing groups: Y joints [1, 2] HOME_SEQUENCE -1; Z joints [3, 10, 11] HOME_SEQUENCE -2; X joints [0] HOME_SEQUENCE 3; A joints [4] HOME_SEQUENCE 4; B joints [5] HOME_SEQUENCE 4; C joints [6] HOME_SEQUENCE 4; U joints [7] HOME_SEQUENCE 5; V joints [8] HOME_SEQUENCE 5; W joints [9] HOME_SEQUENCE 5.
- Probe net: none - no probe fitted; motion.probe-input unconnected.
- Spindles: spindle.0 run do:2, speed ao:0, at-speed near comparator on spindle.0.speed-in (encoder 0), feedback encoder:0.
- Process interlock (XS1.3): XS1.3 open opens XPC0 and XPC1 only. No output of this sheet is on XPC0/XPC1, so XS1.3 removes nothing here; a spindle stop belongs in the EXT_PERMIT safety chain or needs the spindle run/STO input wired through XPC0.
- Note: Z, Z2 and Z3 move together (duplicate Z letters).

Spare after allocation: di 9, do 13, probe 2, freq 2, pwm 2, proc_en 2, ao 1, ai 4, rs485 1, can 1, sto_fb 1. Pendant selector inputs used: 6 of 10.

## 10. Resource demand created by these terminals

- Direct FPGA signals from field terminals (12 motors, 12 encoders fitted): **101** (STEP 12, DIR 12, EN_N 12, ALM 12, encoder A/B/Z 36, FREQ 2, MPG A/B 2, probes 2, PWM 2, process enables 2, XS1 status/feedback 6, arm lamp 1).
- Serial-link pins: DIC 4, DOA 4, DOB 4, EIA status shift register (pendant, MPG enable, XF presence, supply faults) 3, EX8 status shift register (8 encoder-supply faults, presence) 3, ACC IOL1 port L3 (AO, AI, ACC monitors) 4 = **22**. Total field-driven FPGA pins **123** (arithmetic).
- Arithmetic from this terminal list (12 motors, 12 encoders fitted). Excludes host SPI, clock, reset, configuration, watchdog/permission, expansion presence/ID/tamper and status pins, which the FPGA-resource section of IS-1 adds. T20F256: 195 advertised GPIO, 189 after 6 dual-purpose configuration pins, 137 full-feature (Efinix DS v6.0 via MOTION_EXPANSION section 7.1). Fit unproven until Efinity place-and-route (tool unavailable here).
- Differential receiver channels: 16 on the base (ENC0-3 ABZ 12 + FREQ 2 + MPG 2 = four quad receivers, no spare channel) and 24 on EX8 (six quad receivers).
- Protocol fields: every servo-class terminal above needs its CNC1 field in every servo exchange (T2); telemetry-class rows need a telemetry-page field with timestamp/age. Section 01 carries all of them for 12 motors and 12 encoders simultaneously (CNF3/CNS3 field sets, telemetry map), and `tools/interface_spec_validate.py` checks that every CNC1 and HAL name in `terminals.json` resolves to section 01.

## 11. Blockers and dependencies (exact)

| Item | Blocked by | What continues meanwhile |
|---|---|---|
| FPGA pin fit of the 123 field-driven pins plus support pins on T20F256 | Efinix Efinity place-and-route (tool not installed here) | Yosys technology mapping and the pin plan by bank/voltage |
| Connector footprints, coding-profile items, creepage between motor-plug domains | Codex schematic/PCB work (owner) | Terminal/net list frozen here as IS-1 |
| Enable LED driver, TVS values, limiter parts for sensor/probe/alarm supplies | Codex part selection and ERC | Functional behaviour and ratings fixed here |
| DM542T V4 opto-input compatibility with AM26C31 drive, enable/alarm polarity | Physical drive + bench measurement (purchase) | Profile text and tests TT-XMn-* |
| DO current accuracy across 0.10-0.50 A, open-load thresholds, photorelay timing | Built DO/MIA cards + measurement | Datasheet arithmetic in section 6 |
| Encoder 10 M transitions/s, FREQ 1 MHz, probe capture latency | Built EIA card + signal generator measurement | HDL simulation of the decoders (gateware work) |
| Field entry fuse, cable and PSU ratings (E-34) | Codex power_entry selection + measurement | Split-entry arithmetic in section 7 |

Reproduce: this file is rendered from `spec/terminals.json` and `spec/allocations.json` by `python tools/interface_spec/render_03.py`; the JSON files are the frozen IS-1 source (the author-time generator that first produced them is superseded by the integrated JSON and is not archived). `python tools/interface_spec_validate.py` checks that this rendering is current and runs the structural checks: unique terminal ids, every connector position 1..n populated exactly once, every allocation terminal present, no terminal or resource channel used twice in a sheet, no channel above capacity, every CNC1 and HAL name resolvable. These are specification checks, not hardware tests.
