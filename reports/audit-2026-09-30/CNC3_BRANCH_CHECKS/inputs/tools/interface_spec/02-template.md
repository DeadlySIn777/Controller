Interface specification revision: IS-1

# 02 - Modules and service boundaries

Section 02 of interface specification IS-1, written 28 September 2026. Machine-readable companion: [`spec/modules.json`](../../spec/modules.json) (`"spec_revision": "IS-1"`). Codex's hardware (schematics, power/protection, connectors, PCB, hardware BOM) and Claude's implementation (gateware, CNC1 protocol and driver, card-controller firmware, configuration and diagnostics service) both build against this revision. A change needs a new revision identifier (IS-2), not an in-place edit.

**Status: specification only.** Nothing here is implemented, drawn, laid out, built, measured or ready for manufacture. The six-joint/two-encoder endpoint, its tests and its synthesis result remain historical baseline evidence. All tables below are generated from `spec/modules.json`, which in turn takes every field-terminal count from `spec/terminals.json` (section 03); if the two ever disagree, the JSON wins and the disagreement is a defect.

This section defines the fixed wiring base and every replaceable card: what each contains, every conductor that crosses its boundary, its connector, identity, firmware, removal and replacement behaviour, what its replacement re-verifies, which faults stay on its ports, its cost and spare-price target, and the capacity reserved so that the four-motor expansion and the encoder expansion can be fitted at the same time. Card names follow section 03 section 4.1 unchanged.

## 1. Evidence classes

| Class | Meaning here |
|---|---|
| datasheet | Manufacturer datasheet or product page read for this section on 28 Sep 2026 (sources in section 18) |
| recorded price | Price ladder already recorded in `research/*.json` (qty 100 unless stated) |
| observation | Price or listing seen on a distributor page or in a search snippet on 28 Sep 2026; quantity stated; not a quote |
| arithmetic | Derived here from stated inputs |
| estimate | Engineering estimate. Not evidence; used only where no price exists, and always shown as a range |
| source inspection | Read from the repository, IS-1 sections 03/04 or Codex's files |

No ERC, DRC, SPICE, HDL simulation, synthesis, Efinity place-and-route or physical measurement exists for anything in this section.

## 2. Decisions made in this section (delegated engineering authority)

| # | Decision | Reason | Standard or option |
|---|---|---|---|
| D02-1 | Thirteen card positions plus the cartridge slot on one passive base: PSM, CMC, MC, MIA, MX4, EIA, EX8, DIC, DOA, DOB, ACC, ESC and a reserved synchronized-expansion slot XS; the settings cartridge plugs into XCART1 on the PSM bracket (section 3) | Grouped by function and failure domain, not one board per chip; the names are section 03's | Standard (MX4, EX8 and XS positions empty on an eight-motor unit) |
| D02-2 | Card format: 100 x 220 mm cards standing in guides on the base, mating along the 220 mm edge, up to two connector positions (P1 logic, P2 field), a lever and one captive retaining screw | Two 94 mm connector bodies fit one 220 mm edge; guides align the card before any contact touches | Standard |
| D02-3 | Board-to-board families: DIN 41612 type C 96 and 32 contacts for card slots, HARTING har-bus 64 (160 contacts) for the motion card (two) and the XTB, DIN 41612 H15 for PSM power (section 7) | Guided, coded, 400-500 mating cycles, 2.54 mm grid (no fine-pitch alignment by eye), exact part numbers verified | Standard |
| D02-4 | Every card makes its own 3.3 V (and 1.2 V on the MC) from a switched slot feed on the PSM; card power-good is a real supervisor output | A shorted card trips only its own feed; "module power-good" becomes a physical measurement | Standard |
| D02-5 | All card-bound FPGA outputs, including the MX4 path, pass Ioff buffers on the MC | Keeps the base passive (section 03 D03-1); a card fault cannot drive an FPGA pin. Moves the "base Ioff buffer" of section 04 section 6.3 onto the MC without changing its equation. Because that buffer's qualified OE now lives on the MC, the OE net itself clears an OPI_BOE latch on the MC and every AM26C31 STEP/DIR input on the MIA and MX4 is pulled down, so an OE pulse that the MX4 receiver rejects is still latched and cannot float a counted edge (section 04 section 4.2); bank-A buffer OEs are tied active | Standard |
| D02-6 | Watchdogs, arm latches and final permission gates on the MC; tamper latches on the PSM (confirms section 04 section 6.2) | Section 5 | Standard |
| D02-7 | DIC, DOA, DOB and ACC each carry an STM32G031 card controller on its IOL1 port (section 01 D01-5: C8T6 on DIC, K8T6 on the others); each linked slot gets 4 slot-strap contacts from base copper | Section 01 governs the link; this section adds the slot straps, the card power and the identity record | Standard |
| D02-8 | General-output driver: **TPS274C65ASRHAR** (hardware requirement for Codex) | Only complete path that brings per-output current, open-load, temperature and bank VS to software through one isolated digital link (section 11.2) | Standard |
| D02-9 | Identity: Microchip AT30TSE752A-XM8M-T (EEPROM + temperature sensor) on every electronic card with a 256-byte MIR-1 record; MX4 class straps latched by the FPGA; EX8 class bits in its shift register | One part gives identity and the "useful temperature monitoring" per card; its write protection can only be changed by a factory fixture | Standard |
| D02-10 | Expansion terminals M8-M11 and ENC4-ENC11 on the XTB (adopts section 03 D03-4) | Section 8.3 compares it with putting all 136 on the base | XTB fitted with the expansion |
| D02-11 | XS: one C096 slot connector on the base reserved for a future synchronized module (link, sync strobe, reference clock, permission, power) | "Synchronized expansion" of the expanded target without re-spinning the base; a module's own field wiring (for example a plasma divider) terminates on its bracket, never on the base | Reserved |

## 3. Slot map and card contents

{{SLOT_TABLE}}

"option" for EX8 on a twelve-motor unit: EX8 is fitted with MX4 when the machine needs twelve encoders (allocation sheet E of section 03) and left out for open-loop twelve-motor machines (sheet F).

{{CONTENT_TABLE}}

## 4. The fixed wiring base

- **Passive.** Copper, {{STD_T}} standard field-terminal positions of section 03, the three entry fuse holders, shield bonding (SB1 rail, XPE1), card guides and the slot connectors. No semiconductor, no firmware, no memory: the machine's lineage lives in the cartridge, not in the base.
- **Slot connectors on the base** (every unit): 15 x C096 female, 5 x C032 female, 3 x har-bus 64 male (MC P1/P2, XTB), 1 x H15 female. The MX4, EX8 and XS positions and the XTB connector are populated on every unit so that an expansion is plugged, never soldered.
- **Replacement of the base itself** is not a 5-minute service: every field plug is unscrewed from its flange and moved plug by plug to the new base, no individual wire moves (the reason section 03 uses retained plugs). The base is the lowest-risk part because it carries no active parts.
- **Field conductors** reach each card through its P2 connector, one conductor per terminal net (counts in section 6 are computed from `terminals.json`); shield drains and spacing positions stay on the base; the per-motor AUX_5V/AUX_24V terminals are branches of four bank buses from the PSM.

## 5. Where the permission latch and the external watchdogs live

**Decision (confirms section 04 section 6.2):** WD_M, WD_O, both arm latches, the OPI_TX latch, the sticky trip flags and the final TX/OUT/PROC_PERMIT gates sit **on the motion card**; the power-cycle tamper latches sit **on the PSM**, which owns logic power-on reset.

Reasons, given that the motion card is replaceable:

1. The user's decision places the FPGA "with its clock, configuration flash and supervisory circuitry" on the replaceable motion card.
2. Every latch input (CDONE, local reset, progress pulses, requests, endpoint ready) originates on the MC. Only permission outputs and EXT_PERMIT, PROCESS_PERMIT, RAILS_OK and TAMPER_N cross a connector, so a connector fault can only **remove** permission.
3. Watchdogs and FPGA are factory-tested together and replaced together; the watchdog self-test of section 04 section 5.4 runs after every MC replacement.
4. The base stays passive, so no permission silicon can ever force a base replacement.
5. Each receiving card has its own pull-down and its own local AND with its presence and power-good; a missing or half-seated MC means no permission anywhere.

Rejected: on the base (active silicon in the one part that cannot be swapped in 5 minutes); on the PSM (the watchdogs would be two connectors away from their WDI sources and a PSM swap would re-verify the permission chain). Common-cause note: the MC's watchdogs and FPGA share the card supply; a supply collapse removes permission because every permission net is pulled down at its receiver.

## 6. Conductors crossing every boundary

Counting rules (arithmetic): a differential pair counts as one pair and two conductors; signal returns are one LOGIC_GND contact per three single-ended signals (ground-adjacent for permission nets on the MC, section 04 section 10.4); power contacts are sized at the design current per contact of section 7; presence uses one contact at each end of the connector; the identity bus is the card's own I2C branch. Field-side counts come from `terminals.json`.

{{BOUNDARY_TABLE}}

Motion-card connectors in detail ({{MC_USED}} of 320 contacts used, {{MC_SPARE}} spare for the reserved growth listed in section 8):

{{MC_TABLE}}

Notes:
- MX4 and EX8 field conductors enter the base through the XTB connector ({{XTB_USED}} of 160 contacts) and are routed on the base to the P2 connectors of slots S4 and S6.
- DIC P1 uses a C096 ({{DIC_SPARE_NOTE}} spare) so the safety nets can be separated by ground contacts; DOA/DOB P2 carries its 4 A bank feed on five contacts at 1 A design current per 2 A contact.
- The PSM P1 carries 8 switched CORE_5V slot feeds on 12 feed contacts plus 12 returns (contacts: CMC 4, MC 2, ESC 1, DIC 1, DOA 1, DOB 1, ACC 1, XS 1); MIA, EIA and MX4 are fed from MOTION_5V/EXP_5V, EX8 from CORE_24V through its own converter (section 04 section 10.1).

## 7. Connector requirements and selected families

Requirements for every board-to-board boundary:
- **Guided:** card guides align the card before any contact touches; no fine-pitch alignment by eye (2.54 mm grid everywhere; the compute module's fine-pitch connectors are mated at the factory and never handled in the field).
- **Retained:** card lever plus one captive retaining screw per card; field plugs retained by their screw flanges (section 03).
- **Keyed:** HARTING coded versions or coding keys per card class so a card cannot enter a wrong slot; DOA and DOB share one part number and one coding, and learn their bank from a slot code on the base.
- **Mating cycles:** at least 400 (DIN 41612 performance level 2) or 500 (har-bus 64, H15), against a service life of a few swaps plus factory test.
- **Current:** every power contact rated at least twice its continuous current (section 04 section 10.4). Design currents: 1.0 A per 2 A DIN contact, 0.5 A per 1 A har-bus contact, 7.5 A per 15 A H15 contact.
- **Domains:** LOGIC and FIELD conductors in separate rows with an unused row or a separate connector between them; presence contacts at both ends of each connector.

| Id | Family | Card part (male/female as noted) | Base part | Contacts | Rating | Mating cycles | Verified | Price status |
|---|---|---|---|---:|---|---:|---|---|
| C096 | DIN 41612 type C, 3 rows | HARTING 09 03 196 6921 (C096MS-3,0C1-2, male, angled); coded 09 03 696 6921 | HARTING 09 03 296 6825 (female, straight, 4.5 mm solder) | 96 | 2 A, performance level 2 | >= 400 | datasheet/product pages | female GBP 2.54 @100 (observation); male $4.67-5.23 qty 1 (search snippet) |
| C032 | DIN 41612 type C, 32 | HARTING 09 03 132 6921 (C032MS-3,0C1-2, male, angled) | HARTING 09 03 232 6824 (C032FS-2,9C1-2, female, straight) | 32 | 2 A, level 2 | >= 400 | product page / catalogue | not recorded |
| HB160 | har-bus 64, 5 rows | HARTING 02 04 160 1101 (female, right angle) | HARTING 02 01 160 1101 (male) | 160 | 1 A, level 1 (IEC 61076-4-113) | >= 500 | product pages; card-side gender from an RS listing | not recorded |
| H15 | DIN 41612 H15 (DIN-Power) | HARTING 09 06 115 2911 (H015MS-3,2C1-1, male, angled) | HARTING 09 06 215 2821 (H015FS4,0C1-1, female, straight) | 15 | 15 A, level 1 | >= 500 | product page / catalogue | not recorded |

Rejected for card slots: card-edge fingers (cheaper, but hard-gold plating on every card, typically fewer mating cycles and no candidate verified here) and fine-pitch mezzanine connectors (alignment by eye, low cycle counts). The field terminals themselves are section 03's Phoenix COMBICON MC 1,5 and MSTB 2,5 parts.

## 8. FPGA pins and capacity reserved for both expansions at once

### 8.1 FPGA pin budget (arithmetic, not a fit)

{{FPGA_TABLE}}

{{FPGA_FIELD}} field-driven pins equal section 03 section 10 (12 motors and 12 encoders fitted); the rest are support pins. Total {{FPGA_TOTAL}} of 189 usable T20F256 pins ({{FPGA_SPARE}} spare); at least {{FPGA_LVDS}} must use LVDS-as-GPIO pins, which lack pull-downs and Schmitt inputs, so they go to inputs with external pulls (encoder receivers, alarm and ISO1212 outputs) and to outputs behind the MC's Ioff buffers. {{FPGA_LOCAL}} pins stay on the MC. Fit, bank voltages and timing are unproven until Efinity place-and-route.

### 8.2 Reserved capacity (MX4 and EX8 together, plus XS)

| Resource | Reserved | Where |
|---|---|---|
| FPGA pins | {{FPGA_RES}}: MX4 23 (16 channel, 6 status, OPI_OK_B), EX8 27 (24 encoder, 3 shift register), XS 6 | Section 8.1 |
| Motion-card contacts | 58 reserved conductors inside the {{MC_USED}} used (MX4 24: STEP/DIR/EN 12, ALM 4, status 6, OPI_OK_B, TX_PERMIT_B; EX8 27: encoders 24, shift register 3; XS 7: link 4, sync 2, permission 1), plus {{MC_SPARE}} spare contacts | Section 6 |
| Base connector positions | Slots S4 (MX4) and S6 (EX8) with both connectors, XTB connector, XS connector | Every unit |
| Terminals | {{XTB_T}} positions on the XTB (section 03) | XTB |
| Power | EXP_5V 0.45 A on MOTION_5V; EX8 0.523 A at 24 V from CORE_24V; 4 A-class core entry sized for both (section 04 section 10.1) | PSM |
| Protocol fields | Section 01 frames carry 12 motor and 12 encoder field sets, the installed and encoder-expansion bits, `slot_summary` and a status byte per IOL1 port; the XS port L4 is reserved at integration (CNF3 byte 173 `port_status_L4_XS`, CONFIGURE_IO page 0 byte 18, telemetry source 0x04, HAL port `l4`; section 01 D01-11), always zero until a module class is defined | Section 01 |

### 8.3 Where the M8-M11 terminals stay fixed

**Adopted:** section 03 D03-4. M8-M11 and ENC4-ENC11 terminate on the XTB, a passive terminal board fitted once (factory-fitted on twelve-motor units) that then belongs to the fixed wiring; the MX4 and EX8 electronics stay replaceable behind it.

- **Cost (estimate):** XTB with its {{XTB_T}} headers and plugs ${{XTB_LO}}-{{XTB_HI}} per expanded unit. Carrying the same headers on every base instead adds about ${{OPTA_LO}}-{{OPTA_HI}} to every eight-motor unit; plugs would ship with the expansion either way.
- **Usability:** a twelve-motor unit arrives with the XTB fitted, so its wiring never changes. A field upgrade fits the XTB once (two studs and one guided connector, no soldering, about 2 minutes of the procedure in section 13) and then the card. Afterwards MX4 and EX8 swap like any card.
- **Alternative, not chosen:** all 136 expansion terminals on the base. It gives one wiring diagram for every unit and no XTB part, but every eight-motor customer pays for terminals most never use.

### 8.4 Power allocation per card (reservations from section 04 section 10.1)

{{POWER_TABLE}}

## 9. Card identity (MIR-1)

Every electronic card (all cards except the XTB and the cartridge) carries a **Microchip AT30TSE752A-XM8M-T** (temperature sensor with 2 Kbit EEPROM, MSOP-8, 1.7-5.5 V, -40 to 125 C; datasheet). Address pins are grounded on every card (EEPROM 0x50, temperature 0x48); each card sits on its own branch of the CMC's two TCA9548APWR switches, so equal addresses never share a bus. The factory sets the device's Reversible Software Write Protect; setting or clearing it requires VHV on A0, which only the factory fixture applies, so field software cannot rewrite the record (datasheet section 10.5). Temperature: typical +/-0.5 C at 0-85 C, +/-1.0 C at -25-105 C (datasheet, typical only); reported with validity and age at 1 Hz.

{{IDENT_TABLE}}

Class codes: 0x01 MX4, 0x02 EX8, 0x03 MIA, 0x04 EIA, 0x05 MC, 0x06 CMC, 0x07 PSM, 0x08 ESC, 0x11 DIC, 0x21 DO (DOA/DOB), 0x31 ACC, 0x50 XS module; 0x7F reserved (IOL1 bootloader state); 0x00 and 0xFF invalid. The three linked-card codes equal their IOL1 class (section 01 section 4.2), so the class read over I2C and the class echoed on the link must agree.

Compatibility rules, checked by the configuration service before anything is restored:
1. The class code equals the slot's class; for MX4 the FPGA-latched straps and for EX8 the class bits in its shift register must equal the EEPROM class.
2. The hardware revision is listed in the installed software package's compatibility table.
3. The rated capabilities cover every channel the active configuration uses; a weaker card stays in a diagnostic state.
4. CNC1 ABI, gateware build and card firmware are inside the driver's supported ranges; otherwise a local update is offered or the card is refused.
5. On production units the signature verifies against the manufacturer key; development cards show "unqualified" and cannot arm. (Key provisioning is a pre-production item.)
6. A CRC-32 failure or unreadable record makes the card unidentified and inhibited.

CRC detects corruption only; it does not prove accuracy, supplier or wiring (MODULAR_REPAIR_AND_MEMORY.md section 2).

## 10. Firmware, offline restore and version checks

| Card | Programmed content | Offline restore (approved local image, no account, no internet) | Version check |
|---|---|---|---|
| CMC | eMMC image: Linux, LinuxCNC, CNC1 driver, configuration service, local image store for all programmable cards | Replacement CMC ships imaged; recovery route for a corrupt image is a USB recovery medium (route to qualify) | Package manifest against the cartridge's dependency manifest |
| MC | Gateware in W25Q32JVSSIQ | Host holds CRESET_N low (CDONE low keeps every permission off), writes the flash through the bus switch, verifies by readback, releases, then reads the build ID from the capability page | Build ID and ABI against the driver |
| DIC, DOA, DOB, ACC | STM32G031 (C8T6 on DIC, K8T6 on the others): write-protected bootloader + application | Host service sends update records through IOL1 MAINT (section 01 section 4.8) while motion is disarmed and I/O disabled; image SHA-256 and signature checked before and after writing; an interrupted update leaves the card in its bootloader (IOL1 class 0x7F) with outputs off and the service restarts it. A card whose bootloader itself fails is replaced, not reflashed | Loader and application versions against the MIR-1 range |
| ESC | ESP-IDF 5.5.4 application, two OTA slots with rollback | Host over the UART in ROM download mode (ESP_BOOT plus a supervised reset through ESP_CHIP_PU) | Application version and rollback state |
| PSM, MIA, MX4, EIA, EX8, XTB | None | Nothing to restore | MIR-1 only |
| SCART | Records, not firmware | Restore from mirror or export is an explicit recovery transaction | Lineage and schema |

Every card ships programmed and tested; the customer never uses a programmer, IDE or firmware search. Updates happen stopped and disarmed with permissions withheld, and keep the previous supported image until the new combination passes its checks.

## 11. Linked input/output cards

### 11.1 What section 01 governs and what this section adds

The link to DIC, DOA, DOB and ACC is **IOL1** (section 01 section 4): one point-to-point SPI port per card (L0-L3), 40-byte frames every 100 us, CRC-32C, and the order of checks that must all pass before a card changes an output (frame length, CRC, SOF/version, class, slot straps, epoch, sequence, reserved bits, class limits). Card watchdogs are section 01 section 4.7's: a 1.0 ms accept timer and a hardware-started IWDG (<= 2 ms) running from the controller's own clock, both refreshed only in the accept path; every output enable is `OUT_PERMIT_k AND CARD_EN`, with CARD_EN pulled down. Hardware permission never travels inside the link.

This section adds, at the module boundary:
- **Slot straps:** 4 contacts per linked slot tied to LOGIC_GND or left open on the base copper, read by the card controller and compared with `expected_slot`; DOA and DOB are one part number and learn their bank only from these straps.
- **Card power and identity:** each linked card is fed by its own switched CORE_5V slot feed on the PSM, makes its own 3.3 V, and carries the AT30TSE752A with a MIR-1 record whose class equals the IOL1 class.
- **DO_EN caution (datasheet):** the TPS274C65 restores the stored SW_STATE when DO_EN returns high, so the controller writes SW_STATE = 0 before it raises CARD_EN (section 01 section 4.7), and a replacement card powers up with CARD_EN low.

### 11.2 Output-driver selection (correction T1): TPS274C65ASRHAR

{{T1_TABLE}}

**Selected: TPS274C65ASRHAR** (TI SLVSFZ2C, February 2024; packaging addendum lists it Active). It is the only path of the two that brings per-output current, open-load, temperature and bank-supply readings to software through one isolated digital link, with a hardware disable pin and a wider transient margin. TPS274C65ASH is not needed: its extra current-limit settings serve 2 A loads, and IS-1 outputs are 0.5 A with a 1.0 A limit maximum. **TPS274C65BS must not be used** (no ADC, no current sense). This is a hardware requirement for Codex to draw, replacing the TPS4H160BQPWPRQ1 on the output cards; its price is not recorded and stays unknown. Section 01 section 8.1 derives the sense-current spread from the datasheet table (about +/-46 % at 50 mA, about +/-10 % at 200 mA); accuracy must be verified across the declared 0.10-0.50 A load range on a built card.

## 12. Timing of module data and names

Module state that protection or the servo loop needs travels every 1 ms cycle in the section 01 frames: `slot_summary` (MIA and EIA qualified, MX4 and EX8 installed, XF present, any tamper), the MX4 expansion byte, and a status byte per IOL1 port (link state, identity matched, card power-good, card fault, outputs enabled, card watchdog tripped). Everything else is sampled locally, timestamped and reported at its own rate with its age; local protection and the hardware inhibit path never wait for it (section 04 section 2).

{{TEL_TABLE}}

A displayed measurement always carries validity and age; a disconnected path or stale value is shown as "unavailable" or "stale", never as a plausible zero, and DO current exists only while the output is on. Endpoints of the 700 us target, input-data age and output-update latency are defined in section 04 section 2 and scheduled in section 01 section 5; module data use the same endpoints.

Names. Linked cards have the real-time `cnc1.io.P.*` pins of section 01 section 7.1 (P = l0-l3, s0, s1). For every slot (keys `psm, cmc, mc, mia, mx4, eia, ex8, dic, doa, dob, acc, esc, scart, xs`) the userspace configuration service, not the real-time component, publishes the identity-bus data read over I2C:

{{HAL_TABLE}}

The same data, with the decoded MIR-1 record, the compatibility verdict and the checks still required, are the service object `hw.modules[<slot>]`, shared by the CLI and the UI.

## 13. Removal, replacement and re-verification

Common behaviour: power-off service only (no hot plug). At power-up the card's two presence contacts, its power-good and its MIR-1 record are read; outputs stay inhibited, position and homing are never restored, and nothing moves or energises until the affected checks pass and the operator arms deliberately. A card inserted or reseated under power sets the PSM tamper latch (motion-critical cards) or shows an IOL1 epoch mismatch and latches its port fault (linked cards); either way nothing resumes by itself.

Standard card procedure (time budget, estimate; to be measured on the first prototype, commissioning and rehoming timed separately):

{{PROC_TABLE}}

The first two steps come before the safe power-down, so the 5-minute card-replacement target (product direction C6) is timed from the end of step 3; the drive-power confirmation is mandatory because a disable-on-current drive with a powered ENA source is enabled while its interface card is out (section 04 exceptions E1, E2). Special cases: the cartridge is pulled from its front guide (about 2.5 minutes including power cycle); a first MX4/EX8 installation adds fitting the XTB once (about 7 minutes in total, not a repair); the base is not a 5-minute module (section 4).

{{REVERIFY_TABLE}}

## 14. Fault containment per card

Required behaviour; every row needs a fault-injection measurement (section 04 section 13 and 14).

{{CONTAIN_TABLE}}

## 15. Cost structure and selling prices

### 15.1 Per card and for the controller on its own

All figures USD at quantity 100. "Recorded-price lines" sums only parts with a recorded ladder; everything else in the estimate column is an engineering estimate (section 1). PCB fabrication and assembly appear as estimate lines per card; PCBWay quotes, yield and rework, freight, warranty and certification are **not** included and remain unknown, not zero.

{{COST_TABLE}}

{{TOTALS_TABLE}}

**Against the US$400 controller-only reference:** the complete implemented controller is estimated at ${{LO8}}-{{HI8}}, about {{R_LO}}-{{R_HI}} times the reference, before PCBWay quotes. The largest items are the field terminal set (base headers plus plugs, ${{PLUG_LO}}-{{PLUG_HI}} for plugs alone), the base with its slot connectors (${{BASE_LO}}-{{BASE_HI}}) and the compute module ($97.50 recorded). No required function is removed to close the gap; the choices below are what the user can change.

### 15.2 Cost-driving choices

{{CHOICE_TABLE}}

### 15.3 Packages built around the controller

Controller estimate plus the recorded display, the MEAN WELL GST90A24-P1M control supply ($27.20 recorded; its sizing is not re-derived for this design), an HDMI cable ($3.96 recorded) and the $15 AI setup allowance (a ceiling, not an expected spend). Enclosure or pendant housing, machine-side field supplies, harnesses, packaging and setup assistance are unknown and excluded, never zero.

{{PACKAGE_TABLE}}

### 15.4 Recommended selling prices

Rule (recommendation, a commercial assumption rather than evidence), exactly as `gen_02.py` computes it and the validator re-checks it: price = complete implemented cost / (1 - gross margin), rounded up to the next multiple of US$10, less US$1; 45 % on the controller, 35 % on package additions and 50 % on spares and expansions. A package price is the separately rounded controller price plus the separately rounded add-on price plus the $15 AI allowance.

- Controller, eight motors: **US${{P_LO}}-{{P_HI}}** on today's estimate. Publish nothing until PCBWay quotes replace the estimate lines.
- MX4 with XTB (field upgrade to twelve motors): US${{MX4P_LO}}-{{MX4P_HI}}. EX8 on its own: US${{EX8P_LO}}-{{EX8P_HI}}.
- Spare-price targets are in the table of 15.1. Rule: no field-facing card spare above 10 % of the controller price; the MC, PSM and ACC may exceed it only with a written reason (recorded in `modules.json` `spare_target_reasons`: the ACC now carries the isolated AI group); an expansion card's spare target never exceeds its expansion selling price (the EX8 spare is the same card, so its target equals the EX8 price); the CMC is dominated by the compute module and could also be offered as a carrier for a customer-supplied qualified CM5.

## 16. Reconciliation with sections 03 and 04

| Item | Section 03/04 text | IS-1 resolution (this section governs card boundaries) |
|---|---|---|
| MX4 Ioff buffer | 04 section 6.3: "through the base Ioff buffer" | On the MC (D02-5); equation and filters unchanged; base stays passive as 03 D03-1 requires |
| SLOT_MX / SLOT_EX | 03 section 8: J_EXP 2x20 + J_EXPF from MOTION_EXPANSION section 7.2 | Superseded: C096 P1/P2 slots for MX4 and EX8, field conductors via the XTB har-bus connector |
| IO_3V3 | 04 section 10.1: one central rail | Same total reservation, but each card derives its 3.3 V locally from its slot feed (D02-4) |
| Card-local output watchdog | 03 section 4.1: "<= 2 ms" | Section 01 section 4.7 adopted (1.0 ms accept timer + IWDG <= 2 ms); no separate watchdog IC on the card |
| Card controllers and class codes | 01 D01-5 and section 4.2 | Adopted; MIR-1 class of each linked card equals its IOL1 class |
| Slot straps | 01 section 9: 4 slot-strap bits per slot on the base | 4 contacts on each linked slot's P1, tied on base copper |
| CAN controller | 01 D01-6: MCP2518FDT-E/SL on a second host SPI bus | On the CMC side of the SPI; the isolated transceiver sits on the ACC |
| T1 driver | 03 D03-7 defers to the I/O section | TPS274C65ASRHAR selected here (section 11.2) |
| Card names | 03 section 4.1 | Adopted unchanged |
| Host SPI conductors | 02 draft: SCLK/MOSI/MISO/CS_N + host IRQ | Integration: CS_FB and CS_CMD (section 01 D01-1); the protocol is polled, so the IRQ line is dropped; the conductor count stays 5 |
| Compute module | 03 section 4.1: CM4/CM5/CB2 family; 02 draft: CM5102016 | Integration: dual 100-pin CM4/CM5-family socket; CM5102016 is the reference module for costing and the first timing qualification; others are qualified separately |
| Motion-card temperature | 01 draft: no MC sensor allocated | Integration: the AT30TSE752A on every card (section 9) is the MC board sensor |
| EXTERNAL_PERMIT source | 04 section 6.1: 'I/O card' | Integration: the DIC (XS1), hard-wired to the MC; section 04 updated |
| PERMIT_OUT receiver | 03 R03-1 | Integration: added to the TX_PERMIT fan-out in section 04 section 6.3 |
| DO isolator | 02 draft: one isolator, 4 forward + 1 reverse | Integration: ISO7762FDBQR, 4 forward + 2 reverse (FLT readable without SPI), default-low outputs |
| Slot presence and power-good | STD group on every card, routed nowhere for DIC, DOA, DOB, ACC, ESC, CMC, XS, SCART | Repair round: 29 lines to the MC slot status register (section 6 MC groups; section 01 section 4.10); DIC lines also form DIC_OK in base_ok |
| Output-card enables | OUT_PERMIT AND CARD_EN | Repair round: OUT_PERMIT_k AND OUT_EN latch AND CARD_EN; the latch holds outputs off after any accepted permission drop |
| Bank-B Ioff OE | OE filtered, OPI only on the MX4 | Repair round: the qualified OE net also clears OPI_BOE on the MC; STEP/DIR inputs pulled down at every AM26C31 |

### 16.1 Changes required to Codex's drawn hardware

{{HWCHANGE_TABLE}}

### 16.2 Parts recorded as Codex BOM items with the interface limits they must meet

{{BOMLIM_TABLE}}

### 16.3 External modules named by the allocation sheets

{{EXTMOD_TABLE}}

## 17. Hand-offs

**To Codex (hardware, IS-1 requirements):** the card format and connectors of sections 2 and 7 (exact HARTING parts, coding per class); the boundary counts of section 6 as the connector pin budgets; switched CORE_5V slot feeds and card-local regulation with real power-good (D02-4); Ioff buffers on the MC (D02-5); AT30TSE752A-XM8M-T on every electronic card with grounded address pins and factory RSWP (section 9); TPS274C65ASRHAR, isolator and the OUT_PERMIT AND OUT_EN latch AND CARD_EN gate on DOA/DOB and the ACC (section 11); the MC slot status register and its 29 base lines; the changes of section 16.1 and the BOM limits of section 16.2; 4 slot-strap contacts per linked slot tied on the base; 2 x TCA9548APWR on the CMC; 3 x INA238AIDGSR entry monitors on the PSM; the XTB with one har-bus connector and two chassis studs; the reserved XS connector.

**To Claude (implementation):** the IOL1 work listed in section 01 section 9; MIR-1 parser and compatibility rules in the configuration service; `hw.modules` service object and the HAL pins of section 12; MC flash-restore and card-firmware restore tools working from the local image store; replacement workflow of section 13 on top of the existing `python -m controller_config recovery` commands.

## 18. Blockers (exact dependencies) and sources

| Item | Blocked by | Continues meanwhile |
|---|---|---|
| USD quotes for every "estimate" line, and the selling prices derived from them | PCBWay turnkey quotation on complete design files (not yet drawn) and distributor quotes | Estimate ranges and recorded prices above |
| TPS274C65ASRHAR, AT30TSE752A, TLP3640A/TLP4176A, HARTING prices | Distributor price pages refused automated access (DigiKey 403) or show no price (TI) | Unknown, not zero |
| Replacement times under 5 minutes | Built cards, base and card cage | Time budget of section 13 |
| USD price of the REC3.5-2424SRW/R8/A AI-group converter | Distributor quote in USD (only a CAD listing was read) | Estimate range $42-47 |
| Current accuracy of TPS274C65ASRHAR at 0.10-0.50 A | Built DO card and measurement | Datasheet comparison |
| FPGA pin fit of {{FPGA_TOTAL}} signals | Efinix Efinity place-and-route (not installed) | Arithmetic budget, section 8.1 |
| Connector footprints, card guides, cage mechanics | Codex PCB and enclosure work (owner) | Families and part numbers fixed here |
| Contact-rating and creepage checks of mixed rows | Codex layout | Row rules of section 7 |

Sources opened for this section: TI TPS274C65 product page and datasheet SLVSFZ2C; HARTING product pages 09031966921, 09032966421, 09031326921, 02011601101, 02071601101, 09061152911, and catalogue listings for 09032326824, 09062152821, 09036966921; Rapid Electronics pages for HARTING 09 03 296 6825 and Phoenix 1843321; Microchip AT30TSE752A/754A/758A datasheet (Atmel-8854G); TI INA238 and TCA9548A product pages; distributor search results for STM32G031C8T6, ESP32-S3-WROOM-1U-N8 and HARTING 09031966921. Recorded prices come from `research/hardware-cost-model.json` and `research/compute-display-matrix.json`.

## 19. Not claimed

No card, base, connector footprint, firmware, gateware or driver described here exists. No cost is a quotation. No replacement time, current accuracy, temperature accuracy or containment behaviour has been measured. Nothing here is a certified safety function or ready for manufacture.

---

Interface specification revision IS-1. Nothing in this section is implemented, measured or ready for manufacture.
