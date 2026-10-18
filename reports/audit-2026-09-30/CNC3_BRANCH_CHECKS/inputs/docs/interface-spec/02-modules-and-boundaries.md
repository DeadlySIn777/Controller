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

| Slot | Card | 8-motor unit | 12-motor unit | Identity | Firmware |
|---|---|---|---|---|---|
| S0 | PSM: Power and service module | yes | yes | MIR-1 class 0x07 | none |
| S1 | CMC: Compute carrier card | yes | yes | CM5 OTP serial + MIR-1 class 0x06 | eMMC image |
| S2 | MC: Motion card | yes | yes | MIR-1 class 0x05; gateware build ID in CNC1 capability pages | gateware (host restore) |
| S3 | MIA: Motor interface card A (M0-M7) | yes | yes | MIR-1 class 0x03; presence and PGOOD latched by the FPGA and the PSM tamper latch | none |
| S4 | MX4: Motor expansion card (M8-M11) | no | yes | MIR-1 class 0x01 + FPGA-latched straps (must agree) | none |
| S5 | EIA: Encoder and fast-input card | yes | yes | MIR-1 class 0x04 | none |
| S6 | EX8: Encoder expansion card (ENC4-ENC11) | no | option | MIR-1 class 0x02 + class bits in its shift register | none |
| fixed once | XTB: Expansion terminal board | no | yes | none (the MX4 and EX8 identities cover the expansion) | none |
| S7 | DIC: Digital input card | yes | yes | MIR-1 class 0x11 (= IOL1 class) + class and slot in every IOL1 response | STM32G031 loader + app |
| S8, S9 | DO: Output card DOA/DOB (one part number; bank from the slot code) | yes | yes | MIR-1 class 0x21 (= IOL1 class), bank from the slot straps | STM32G031 loader + app |
| S10 | ACC: Analog, communication and process card | yes | yes | MIR-1 class 0x31 (= IOL1 class) with calibration descriptor; full calibration record in the controller's protected flash | STM32G031 loader + app |
| S11 | ESC: ESP32-S3 service card | yes | yes | eFuse MAC + MIR-1 class 0x08 | ESP-IDF, 2 OTA slots |
| XCART1 | SCART: Settings cartridge | yes | yes | cartridge serial + machine lineage | none (records) |
| S12 | XS: synchronized expansion slot (reserved) | empty | empty | MIR-1 class 0x50 | set by the future module |

"option" for EX8 on a twelve-motor unit: EX8 is fitted with MX4 when the machine needs twelve encoders (allocation sheet E of section 03) and left out for open-loop twelve-motor machines (sheet F).

| Card | Contents |
|---|---|
| PSM | entry eFuses and reverse protection for XP1 CORE (4 A class), XP2 FIELD_A and XP3 FIELD_B (section 04 section 10); physical fuses in holders on the base<br>CORE_5V 6 A and MOTION_5V >= 3 A converters, EXP_5V switch with a real power-good, AUX_5V/AUX_24V bank limiters and monitors<br>8 switched CORE_5V slot feeds (12 feed contacts) with fault flags<br>TPS386000 rail supervision, sequencing, POR and the power-cycle tamper latches for MIA, MX4, EIA and EX8<br>3 x INA238AIDGSR entry monitors, POWERFAIL_N early warning, ESP_CHIP_PU<br>cartridge slot XCART1 with guide<br>AT30TSE752A identity and temperature |
| CMC | dual 100-pin CM4/CM5-family module socket, mated at the factory (fine-pitch module connectors never handled in the field); reference module Raspberry Pi CM5102016 for costing and the first timing qualification; other modules (CM4, CB2) are qualified separately before they are offered<br>bracket: XETH1, XDSP1, XUSB1, XUSB2, XANT1; customer Wi-Fi uses the CM5's certified radio, never the ESP<br>2 x TCA9548APWR identity branches and the dedicated cartridge bus<br>host side of CNC1 SPI, MC flash-restore path, ESP UART, RS-485 UART and CAN SPI |
| MC | Efinix T20F256I4, ASE-50.000MHZ-L-C-T clock, W25Q32JVSSIQ configuration flash (Codex fpga_core candidates)<br>section 04 supervisory circuitry: WD_M and WD_O (TPS3851G18SDRBT with CL10C332JB8NNNC), both arm latches, OPI_TX latch, sticky trip flags, final TX/OUT/PROC_PERMIT gates<br>Ioff buffers on every card-bound output, including the MX4 buffer (TX_PERMIT_B, STEP/DIR/EN 8-11) whose qualified OE clears OPI_BOE; bank-A buffers have OE tied active<br>OPI_OUT latch, PERMIT_OUT_REQ gate (PERMIT_OUT open during self-tests), DIC_OK filter, 10 kOhm pull-downs on EXT_PERMIT_3V3 and PROCESS_PERMIT_EXT_3V3<br>slot status register (presence and power-good of every slot without another FPGA path)<br>configuration-flash restore path from the CMC<br>local 1.2 V/3.3 V regulation and supervisor; AT30TSE752A |
| MIA | 4 x AM26C31IPWR with 10 kOhm pull-downs on every STEP and DIR input (idle low)<br>per channel TLP3640A(TPL,E) normally open and TLP4176A(TP,F) normally closed on one LED current (section 04 section 3)<br>SN74LVC07APWR LED drivers, TPS22918DBVR LED-supply switch, OPI_A latch<br>4 x ISO1212DBQR alarm inputs<br>AT30TSE752A; local 3.3 V and supervisor |
| MX4 | MIA circuits for 4 channels on TX_PERMIT_B<br>MOD_ID0-2 straps (class 1)<br>EXP_5V supervisor driving EXP_PGOOD<br>sold with the XTB for field upgrades; factory-fitted on twelve-motor units |
| EIA | 4 x AM26LV32EIPWR: ENC0-3 A/B/Z, FREQ0-1, MPG A/B (16 channels, none spare)<br>TPS2553DBVR-1 per encoder port, MPG and FREQ supply<br>two unfiltered probe front ends with typed supplies<br>pendant/status shift register (XH2 selectors, MPG enable, XF presence, supply faults)<br>XF 1-Wire identity bridge<br>AT30TSE752A |
| EX8 | 6 x AM26LV32EIPWR (24 channels)<br>8 x TPS2553DBVR-1<br>own 24 V to 5 V converter fed from CORE_24V through the expansion power switch<br>status shift register with class bits<br>AT30TSE752A |
| XTB | 136 header positions: XM8-XM11 and XE4-XE11 (section 03)<br>passive; one har-bus 64 connector and two chassis studs to the base<br>factory-fitted on twelve-motor units; fitted once in the field together with the first MX4 or EX8, then part of the fixed wiring |
| DIC | DI0-DI23: 12 x ISO1212DBQR with group sensor-supply limiters<br>XS1 safety interface: EXT_PERMIT and PROCESS_PERMIT hard-wired to the MC (pulled down at the MC receiver; DIC presence and power-good form DIC_OK in base_ok); SAFETY_STATUS, RESET_ARM, CONTACTOR_FB, STO_FB direct to the FPGA; ARM_LAMP (FIELD_B 0.05 A); PERMIT_OUT photorelay<br>card controller STM32G031C8T6 (IOL1 port L0)<br>AT30TSE752A |
| DO | 8 outputs: 2 x TPS274C65ASRHAR (quad 72 mOhm high-side, SPI with CRC, 10-bit ADC for per-channel current, VS and FET temperature, on/off-state open-load, DO_EN)<br>card controller STM32G031K8T6 on the LOGIC side (IOL1 port L1 or L2); one ISO7762FDBQR isolator (4 forward: SCLK, SDI, CS_N, DO_EN; 2 reverse: SDO, wired-OR FLT; F variant: outputs default low when the logic side is unpowered) to the switches' SPI (device CRC on)<br>card watchdogs of section 01 section 4.7: 1.0 ms accept timer and hardware-started IWDG (<= 2 ms), both refreshed only by fully accepted frames<br>DO_EN = OUT_PERMIT_k AND OUT_EN latch Q AND CARD_EN (controller pin with pull-down); the OUT_EN latch (SN74LVC2G74DCUR half, CLR_N = qualified OUT_PERMIT_k) keeps the outputs off after any accepted permission drop until a new epoch and IO_ENABLE<br>AT30TSE752A |
| ACC | AO0 and AO1, each in its own isolated domain (DAC80501ZDQFR, OPA197IDBVR, ISO7740FDBQR, TMR 1-2412 per channel), zero clamp on OUT_PERMIT_ACC<br>AI0-AI3 in one isolated group, 0-10 V / 4-20 mA ranges, powered with the 24 V 100 mA sensor supply from a RECOM REC3.5-2424SRW/R8/A<br>PWM0-1 buffers (FPGA-generated; OE from OUT_PERMIT_ACC through the OUT_EN latch; no inverted mode)<br>PEN0-1 TLP3640A contacts, LED current gated by PROC_PERMIT through the PEN latch in hardware<br>isolated RS-485 (CMC UART) and isolated CAN transceiver; the MCP2518FDT-E/SL CAN controller (section 01 D01-6) sits on the CMC SPI<br>card controller STM32G031K8T6 (IOL1 port L3): analog acquisition, timestamps, calibration<br>AT30TSE752A |
| ESC | ESP32-S3-WROOM-1U-N8, U.FL to the XANT2 unique-coupling bulkhead<br>XUSB_SVC USB-C service port<br>wired UART to the CMC; ESP_CHIP_PU owned by the PSM supervisor<br>observes RAILS_OK and MOTION_DISARMED only; no motion or permission authority<br>AT30TSE752A |
| SCART | protected configuration memory with two committed generations (Codex BOM item with the interface limits of codex_bom_items_with_limits: >= 2 x the committed-record capacity of MODULAR_REPAIR_AND_MEMORY.md, >= 10^5 write cycles, >= 20 years retention, hardware write-protect pin, I2C at 400 kHz)<br>Infineon FM24V02A-G history-ring F-RAM (section 04 section 12.2), separate from the write-protected configuration memory<br>hardware WP default-protected; write window only on CART_WP_EN<br>keyed housing |

## 4. The fixed wiring base

- **Passive.** Copper, 315 standard field-terminal positions of section 03, the three entry fuse holders, shield bonding (SB1 rail, XPE1), card guides and the slot connectors. No semiconductor, no firmware, no memory: the machine's lineage lives in the cartridge, not in the base.
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

| Card | Conn. | Family | Single-ended | Diff. pairs | Signal returns | Power | Other field | Presence | Identity bus | Used/total | Spare |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PSM | P1 | C096 | 30 | 0 | 12 | 34 | 6 | 2 | 2 | 86/96 | 10 |
| PSM | P2 | H15 | 0 | 0 | 0 | 14 | 0 | 0 | 0 | 14/15 | 1 |
| CMC | P1 | C096 | 30 | 0 | 20 | 8 | 0 | 2 | 28 | 88/96 | 8 |
| MC | P1+P2 | 2 x HB160 | 194 | 0 | 66 | 8 | 0 | 2 | 2 | 272/320 | 48 |
| MIA | P1 | C096 | 36 | 0 | 14 | 4 | 0 | 2 | 2 | 58/96 | 38 |
| MIA | P2 | C096 | 0 | 16 | 0 | 2 | 48 | 0 | 0 | 82/96 | 14 |
| MX4 | P1 | C096 | 23 | 0 | 9 | 4 | 0 | 2 | 2 | 40/96 | 56 |
| MX4 | P2 | C096 | 0 | 8 | 0 | 2 | 24 | 0 | 0 | 42/96 | 54 |
| EIA | P1 | C096 | 22 | 0 | 9 | 4 | 0 | 2 | 2 | 39/96 | 57 |
| EIA | P2 | C096 | 0 | 16 | 0 | 2 | 39 | 0 | 0 | 73/96 | 23 |
| EX8 | P1 | C096 | 28 | 0 | 11 | 6 | 0 | 2 | 2 | 49/96 | 47 |
| EX8 | P2 | C096 | 0 | 24 | 0 | 0 | 24 | 0 | 0 | 72/96 | 24 |
| XTB | P1 | HB160 | 0 | 32 | 0 | 4 | 48 | 0 | 0 | 116/160 | 44 |
| DIC | P1 | C096 | 17 | 0 | 7 | 2 | 0 | 2 | 2 | 30/96 | 66 |
| DIC | P2 | C096 | 0 | 0 | 0 | 4 | 47 | 0 | 0 | 51/96 | 45 |
| DOA | P1 | C032 | 10 | 0 | 5 | 2 | 0 | 2 | 2 | 21/32 | 11 |
| DOA | P2 | C032 | 0 | 0 | 0 | 5 | 12 | 0 | 0 | 17/32 | 15 |
| DOB | P1 | C032 | 10 | 0 | 5 | 2 | 0 | 2 | 2 | 21/32 | 11 |
| DOB | P2 | C032 | 0 | 0 | 0 | 5 | 12 | 0 | 0 | 17/32 | 15 |
| ACC | P1 | C096 | 23 | 0 | 9 | 6 | 0 | 2 | 2 | 42/96 | 54 |
| ACC | P2 | C096 | 0 | 6 | 0 | 0 | 22 | 0 | 0 | 34/96 | 62 |
| ESC | P1 | C032 | 7 | 0 | 4 | 2 | 0 | 2 | 2 | 17/32 | 15 |
| SCART | P1 | C032 | 1 | 0 | 0 | 4 | 0 | 2 | 2 | 9/32 | 23 |
| XS | P1 | C096 | 8 | 0 | 4 | 4 | 0 | 2 | 2 | 20/96 | 76 |

Motion-card connectors in detail (272 of 320 contacts used, 48 spare for the reserved growth listed in section 8):

| Group crossing the motion-card connectors | Conductors |
|---|---|
| STEP/DIR/EN_N M0-M7 to MIA through Ioff buffers on the MC | 24 |
| STEP/DIR/EN_N M8-M11 to MX4 through Ioff buffers on the MC (reserved) | 12 |
| ALM0-7 from MIA | 8 |
| ALM8-11 from MX4 (reserved) | 4 |
| ENC0-3 A/B/Z from EIA | 12 |
| ENC4-11 A/B/Z from EX8 (reserved) | 24 |
| FREQ0-1, MPG A/B, PRB0-1 from EIA | 6 |
| PWM0-1 and PEN0-1 commands to ACC | 4 |
| XS1 status/feedback from DIC: EXT_PERMIT, PROCESS_PERMIT, SAFETY_STATUS, RESET_ARM, CONTACTOR_FB, STO_FB | 6 |
| ARM_LAMP to DIC | 1 |
| IOL1 links L0-L3 to DIC, DOA, DOB, ACC (SCLK, CMD, RSP, CS_N each) | 16 |
| status shift registers EIA (3) and EX8 (3, reserved) | 6 |
| host SPI SCLK/MOSI/MISO/CS_FB/CS_CMD from CMC (section 01 D01-1) | 5 |
| MX4 status PRESENT_A/B, EXP_PGOOD, MOD_ID0-2 (reserved) | 6 |
| TAMPER_N from PSM | 1 |
| MIA status PRESENT_A/B, PGOOD | 3 |
| OPI_OK_A, OPI_OK_B, OPI_REARM | 3 |
| RAILS_OK from PSM | 1 |
| slot presence A/B and power-good to the MC slot status register: EIA, EX8, DIC, DOA, DOB, ACC, ESC, CMC, XS (27) and SCART presence A/B (2); the DIC lines also feed the DIC_OK filter of base_ok | 29 |
| XS link (4) + SYNC_STROBE + XS_REFCLK (reserved) | 6 |
| TX_PERMIT_A to MIA; TX_PERMIT_B (Ioff copy) to MX4 | 2 |
| OUT_PERMIT_DOA, OUT_PERMIT_DOB, OUT_PERMIT_ACC (own driver and pull-down each) | 3 |
| PROC_PERMIT to ACC | 1 |
| PERMIT_OUT drive to DIC photorelay | 1 |
| XS_PERMIT (reserved) | 1 |
| configuration-flash restore path from CMC: SCK, MOSI, MISO, CS_N, CRESET_N, CDONE, BUS_SEL | 7 |
| MOTION_DISARMED observation to ESC | 1 |
| presence A and B at opposite connector ends | 2 |
| card power-good, open drain | 1 |
| identity I2C branch SDA/SCL | 2 |
| LOGIC_GND signal returns, 1 per 3 signals | 66 |
| CORE_5V feed (0.5 A/contact design) | 4 |
| CORE_5V return | 4 |

Notes:
- MX4 and EX8 field conductors enter the base through the XTB connector (116 of 160 contacts) and are routed on the base to the P2 connectors of slots S4 and S6.
- DIC P1 uses a C096 (66 spare) so the safety nets can be separated by ground contacts; DOA/DOB P2 carries its 4 A bank feed on five contacts at 1 A design current per 2 A contact.
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

| FPGA signal group | Pins | Note |
|---|---|---|
| STEP/DIR/EN_N/ALM M0-M11 (section 03) | 48 | M8-M11: 16 reserved for MX4 |
| ENC0-11 A/B/Z (section 03) | 36 | ENC4-11: 24 reserved for EX8 |
| FREQ, MPG A/B, probes, PWM, process enables (section 03) | 10 |  |
| XS1 status/feedback + ARM_LAMP (section 03) | 7 |  |
| serial links DIC/DOA/DOB/ACC + shift registers EIA/EX8 (section 03) | 22 | EX8 register: 3 reserved |
| host SPI SCLK/MOSI/MISO/CS_FB/CS_CMD | 5 | two chip selects, section 01 |
| MX4 PRESENT_A/B, EXP_PGOOD, MOD_ID0-2 + TAMPER_N | 7 | 6 reserved |
| MIA PRESENT_A/B, PGOOD | 3 |  |
| OPI_OK_TX/A/B + OPI_REARM | 4 | OPI_OK_B reserved |
| RAILS_OK readback | 1 |  |
| XS link + SYNC_STROBE + XS_REFCLK | 6 | reserved |
| progress_m, progress_o, MOTION_REQUEST, OUTPUT_REQUEST, ENDPOINT_READY | 5 | local to MC |
| WD_M_OK, WD_O_OK, TX/OUT/PROC_PERMIT readback | 5 | local to MC |
| watchdog trip flags x2 + clear | 3 | local to MC |
| clock, local reset | 2 | local to MC |
| fault LEDs | 4 | local to MC |
| MC slot status register SSR_CLK/SSR_LOAD_N/SSR_DATA | 3 | local to MC; section 01 section 4.10 |
| OPI_OK_BOE, OPI_OK_OUT, OPI_REARM_O | 3 | local to MC; section 04 section 4.2 |
| PERMIT_OUT_REQ | 1 | local to MC; section 04 section 6.2 |
| **Total** | **175** | 56 reserved for MX4, EX8, XS |

123 field-driven pins equal section 03 section 10 (12 motors and 12 encoders fitted); the rest are support pins. Total 175 of 189 usable T20F256 pins (14 spare); at least 38 must use LVDS-as-GPIO pins, which lack pull-downs and Schmitt inputs, so they go to inputs with external pulls (encoder receivers, alarm and ISO1212 outputs) and to outputs behind the MC's Ioff buffers. 27 pins stay on the MC. Fit, bank voltages and timing are unproven until Efinity place-and-route.

### 8.2 Reserved capacity (MX4 and EX8 together, plus XS)

| Resource | Reserved | Where |
|---|---|---|
| FPGA pins | 56: MX4 23 (16 channel, 6 status, OPI_OK_B), EX8 27 (24 encoder, 3 shift register), XS 6 | Section 8.1 |
| Motion-card contacts | 58 reserved conductors inside the 272 used (MX4 24: STEP/DIR/EN 12, ALM 4, status 6, OPI_OK_B, TX_PERMIT_B; EX8 27: encoders 24, shift register 3; XS 7: link 4, sync 2, permission 1), plus 48 spare contacts | Section 6 |
| Base connector positions | Slots S4 (MX4) and S6 (EX8) with both connectors, XTB connector, XS connector | Every unit |
| Terminals | 136 positions on the XTB (section 03) | XTB |
| Power | EXP_5V 0.45 A on MOTION_5V; EX8 0.523 A at 24 V from CORE_24V; 4 A-class core entry sized for both (section 04 section 10.1) | PSM |
| Protocol fields | Section 01 frames carry 12 motor and 12 encoder field sets, the installed and encoder-expansion bits, `slot_summary` and a status byte per IOL1 port; the XS port L4 is reserved at integration (CNF3 byte 173 `port_status_L4_XS`, CONFIGURE_IO page 0 byte 18, telemetry source 0x04, HAL port `l4`; section 01 D01-11), always zero until a module class is defined | Section 01 |

### 8.3 Where the M8-M11 terminals stay fixed

**Adopted:** section 03 D03-4. M8-M11 and ENC4-ENC11 terminate on the XTB, a passive terminal board fitted once (factory-fitted on twelve-motor units) that then belongs to the fixed wiring; the MX4 and EX8 electronics stay replaceable behind it.

- **Cost (estimate):** XTB with its 136 headers and plugs $104-167 per expanded unit. Carrying the same headers on every base instead adds about $35-43 to every eight-motor unit; plugs would ship with the expansion either way.
- **Usability:** a twelve-motor unit arrives with the XTB fitted, so its wiring never changes. A field upgrade fits the XTB once (two studs and one guided connector, no soldering, about 2 minutes of the procedure in section 13) and then the card. Afterwards MX4 and EX8 swap like any card.
- **Alternative, not chosen:** all 136 expansion terminals on the base. It gives one wiring diagram for every unit and no XTB part, but every eight-motor customer pays for terminals most never use.

### 8.4 Power allocation per card (reservations from section 04 section 10.1)

| Consumer | Rail | Allocation (A) | Basis |
|---|---|---|---|
| CMC | CORE_5V | 3.0 | section 04: compute 3.00 |
| MC | CORE_5V | 0.45 | CORE_1V2 input 0.28 + its IO_3V3 share |
| ESC | CORE_5V | 0.6 | section 04: ESP_3V3 input |
| DIC, DOA, DOB, ACC logic (card-local 3.3 V) | CORE_5V | 0.35 | remaining IO_3V3 share + misc |
| MIA | MOTION_5V | 0.9 | TX bank A 0.80 + LEDs 0.097 |
| EIA | MOTION_5V | 1.0 | 4 encoders 0.80 + MPG 0.10 + FREQ 0.10 |
| MX4 | EXP_5V from MOTION_5V | 0.45 | section 04 |
| EX8 | CORE_24V (own converter) | 0.523 | section 04; amperes at 24 V |
| ACC isolated AO domains | CORE_24V | 0.06 | section 04 'analog'; amperes at 18 V input |
| ACC AI group (REC3.5-2424SRW/R8/A) | CORE_24V | 0.19 | section 04 ai_group; amperes at 18 V input |
| XS (reserved) | CORE_5V + CORE_24V | - | contacts reserved; allocation set when a module is defined |

## 9. Card identity (MIR-1)

Every electronic card (all cards except the XTB and the cartridge) carries a **Microchip AT30TSE752A-XM8M-T** (temperature sensor with 2 Kbit EEPROM, MSOP-8, 1.7-5.5 V, -40 to 125 C; datasheet). Address pins are grounded on every card (EEPROM 0x50, temperature 0x48); each card sits on its own branch of the CMC's two TCA9548APWR switches, so equal addresses never share a bus. The factory sets the device's Reversible Software Write Protect; setting or clearing it requires VHV on A0, which only the factory fixture applies, so field software cannot rewrite the record (datasheet section 10.5). Temperature: typical +/-0.5 C at 0-85 C, +/-1.0 C at -25-105 C (datasheet, typical only); reported with validity and age at 1 Hz.

| Offset | Bytes | Field |
|---|---|---|
| 0 | 4 | magic 'CNCM' |
| 4 | 1 | format version = 1 |
| 5 | 1 | class code |
| 6 | 2 | hardware revision (major, minor) |
| 8 | 16 | serial number, ASCII, zero padded |
| 24 | 4 | manufacture date, days since 2026-01-01 |
| 28 | 4 | variant flags |
| 32 | 32 | rated capabilities: channel count, first channel, per-channel ratings, supply allocations |
| 64 | 16 | compatibility: min/max CNC1 ABI, min driver, min gateware build, min/max card firmware (u16 each) |
| 80 | 16 | calibration descriptor: method id, range, units, SHA-256 prefix of the calibration record (ACC only; zero elsewhere) |
| 96 | 32 | SHA-256 of the factory test record |
| 128 | 64 | manufacturer signature (Ed25519) over bytes 0-127; all zero on development cards |
| 192 | 60 | reserved, 0xFF |
| 252 | 4 | CRC-32 over bytes 0-251 |

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

| Criterion | (a) TPS4H160BQPWPRQ1 + external acquisition | (b) TPS274C65ASRHAR |
|---|---|---|
| complete measurement path | CS pin per quad (K(CS) = 300) -> RC -> field-side multichannel ADC -> isolated ADC SPI -> card MCU; channel chosen by SEL1/SEL2 with DIAG_EN; in the drawn design CS reaches only a test point, so no reading reaches software | ISNS -> 10-bit ADC inside the switch -> addressable SPI with device CRC -> ISO7762FDBQR -> card MCU; per-channel current, VOUT, FET temperature and VS |
| isolation per 8-output card | 8 IN + SEL1/SEL2/DIAG_EN (shared) + ADC SPI (3) forward, ADC SDO + 2 FAULT reverse: about 14 forward and 3 reverse channels, four or more isolator packages; the drawn design has no free channel | one ISO7762FDBQR: SCLK, SDI, CS_N, DO_EN forward; SDO and wired-OR FLT reverse; outputs switched by SPI, so no per-channel IN lines cross the barrier |
| sampling time | one channel per select setting; settling after each select change (time not recorded here) plus one ADC conversion; four channels per device read in sequence | 128 us per measurement (Tconv1, datasheet); a full sequential round of 4 channels x 4 quantities is at most 2.05 ms (arithmetic, interpretation, to be measured), inside the 93.05 ms age bound |
| accuracy at the declared 0.10-0.50 A | K(CS) sense error class +/-8 % recorded at the design point (part-selections, datasheet SLVSCV8E); low-current spread not recorded; plus ADC and settling error | sense-current spread +/-4.7 % at 500 mA, +/-9.9 % at 200 mA, +/-15 % at 100 mA relative to the datasheet min-max midpoint (arithmetic), plus ADC reference 2.72-2.85 V, before per-channel factory calibration; both paths need measurement over 0.10-0.50 A, never one convenient load |
| transient withstand | 48 V transient (< 400 ms) absolute maximum, below the SMCJ30CA 48.4 V reference clamp: an open defect | VS 40 V continuous and 60 V transient (< 1 ms, ON state) absolute maximum (datasheet); the 48.4 V clamp is inside the transient rating only if the clamped surge lasts < 1 ms, and the OFF-state transient is not specified: Codex confirms clamp duration or lowers the clamp |
| fault behaviour | current limit (+/-15 % for 0.5-7 A, recorded), thermal, FAULT pin | current limit per channel, IS-1 default 0.72 A setting = 0.62-0.82 A (datasheet), inrush setting, thermal, on/off-state open-load and wire-break (on-state threshold 0.38-0.61 mA), short-to-supply, SPI CRC, SPI watchdog, DO_EN disables all outputs |
| firmware and test effort | ADC driver, select sequencing and settling, per-channel analog calibration, test of every select state and of the analog chain | register driver with CRC, ADC readout, fault registers; per-channel factory calibration at two currents |
| complete implemented cost | 2 x TPS4H160BQPWPRQ1 $2.2172 @100 recorded + field ADC + about three extra isolator packages (ISO7740FDBQR class $1.61 @100 recorded) + select and ADC passives: roughly $6-10 more per card than (b) excluding the driver price difference (estimate) | 2 x TPS274C65ASRHAR (price not recorded: unknown, not zero) + one ISO7762FDBQR (price not recorded) + sense resistors |
| replacement-card cost | every DO spare carries the ADC and extra isolators | DO spare target $99 (section 15.1); the driver price must be quoted before it is confirmed |

**Selected: TPS274C65ASRHAR** (TI SLVSFZ2C, February 2024; packaging addendum lists it Active). It is the only path of the two that brings per-output current, open-load, temperature and bank-supply readings to software through one isolated digital link, with a hardware disable pin and a wider transient margin. TPS274C65ASH is not needed: its extra current-limit settings serve 2 A loads, and IS-1 outputs are 0.5 A with a 1.0 A limit maximum. **TPS274C65BS must not be used** (no ADC, no current sense). This is a hardware requirement for Codex to draw, replacing the TPS4H160BQPWPRQ1 on the output cards; its price is not recorded and stays unknown. Section 01 section 8.1 derives the sense-current spread from the datasheet table (about +/-46 % at 50 mA, about +/-10 % at 200 mA); accuracy must be verified across the declared 0.10-0.50 A load range on a built card.

## 12. Timing of module data and names

Module state that protection or the servo loop needs travels every 1 ms cycle in the section 01 frames: `slot_summary` (MIA and EIA qualified, MX4 and EX8 installed, XF present, any tamper), the MX4 expansion byte, and a status byte per IOL1 port (link state, identity matched, card power-good, card fault, outputs enabled, card watchdog tripped). Everything else is sampled locally, timestamped and reported at its own rate with its age; local protection and the hardware inhibit path never wait for it (section 04 section 2).

| Quantity | Report rate | Source |
|---|---|---|
| DO current, driver temperature and VOUT per channel (current valid only while on) | >= 11 Hz worst case (>= 22 Hz without host priority requests), <= 93.05 ms age | section 01 section 8.1 |
| bank VS from each TPS274C65 | >= 11 Hz | section 01 section 8.1 |
| card controller temperature and VDD (DIC, DOA, DOB, ACC) | >= 5 Hz | section 01 section 8.1 |
| IOL1 counters per port | >= 11 Hz through the telemetry mirror (about 22 Hz without priority requests) | section 01 section 3.12 |
| card temperature (AT30TSE752A, every card) | 1 Hz | host I2C, this section |
| entry voltage/current (INA238) | 10 Hz | host I2C (TEL.supply, section 03) |
| MIR-1 identity | power-up and on request | host I2C, never cyclic |

A displayed measurement always carries validity and age; a disconnected path or stale value is shown as "unavailable" or "stale", never as a plausible zero, and DO current exists only while the output is on. Endpoints of the 700 us target, input-data age and output-update latency are defined in section 04 section 2 and scheduled in section 01 section 5; module data use the same endpoints.

Names. Linked cards have the real-time `cnc1.io.P.*` pins of section 01 section 7.1 (P = l0-l3, s0, s1). For every slot (keys `psm, cmc, mc, mia, mx4, eia, ex8, dic, doa, dob, acc, esc, scart, xs`) the userspace configuration service, not the real-time component, publishes the identity-bus data read over I2C:

| HAL pin | Type | Note |
|---|---|---|
| cnc1.module.<slot>.present | bit | both presence contacts |
| cnc1.module.<slot>.power-good | bit | card supervisor |
| cnc1.module.<slot>.accepted | bit | MIR-1 class, revision and signature accepted |
| cnc1.module.<slot>.class | u32 | MIR-1 class code |
| cnc1.module.<slot>.temperature | float | AT30TSE752A; with .temperature-valid (bit) and .temperature-age (float s) |

The same data, with the decoded MIR-1 record, the compatibility verdict and the checks still required, are the service object `hw.modules[<slot>]`, shared by the CLI and the UI.

## 13. Removal, replacement and re-verification

Common behaviour: power-off service only (no hot plug). At power-up the card's two presence contacts, its power-good and its MIR-1 record are read; outputs stay inhibited, position and homing are never restored, and nothing moves or energises until the affected checks pass and the operator arms deliberately. A card inserted or reseated under power sets the PSM tamper latch (motion-critical cards) or shows an IOL1 epoch mismatch and latches its port fault (linked cards); either way nothing resumes by itself.

Standard card procedure (time budget, estimate; to be measured on the first prototype, commissioning and rehoming timed separately):

| Step | Time budget (s, estimate) |
|---|---|
| stop the machine; the service commits pending configuration (automatic) | 30 |
| switch off the machine main disconnect / drive power; the service screen asks for this confirmation before it shows any card-removal step (exceptions E1 and E2 of section 04) | 30 |
| switch off controller power and both field entries; wait for the PSM 'safe' LED, or a fixed 60 s when the LED stays dark or the PSM is the failed card (Codex sizes bleeders so every rail is below 5 V within 30 s [REQ]) | 60 |
| open the card-cage cover (two captive screws) | 30 |
| release the card's retaining screw and lever it out along its guides | 20 |
| slide the replacement along the same guides until the lever seats; tighten the retaining screw | 30 |
| close the cover | 30 |
| power on: disarmed boot, identification, compatibility verdict and list of required checks | 90 |
| **Total** | **320** (5.3 min) |

The first two steps come before the safe power-down, so the 5-minute card-replacement target (product direction C6) is timed from the end of step 3; the drive-power confirmation is mandatory because a disable-on-current drive with a powered ENA source is enabled while its interface card is out (section 04 exceptions E1, E2). Special cases: the cartridge is pulled from its front guide (about 2.5 minutes including power cycle); a first MX4/EX8 installation adds fitting the XTB once (about 7 minutes in total, not a repair); the base is not a 5-minute module (section 4).

| Card | What its replacement re-verifies before normal operation |
|---|---|
| PSM | entry voltages and currents against the INA238 readings; every slot feed and power-good; tamper latch set/clear by power cycle; AUX_5V/AUX_24V per bank; POWERFAIL_N warning time against the history-ring flush time |
| CMC | image and package manifest; cartridge read and mirror reconciliation; CNC1 link, ABI and capability pages; display and touch; rehoming |
| MC | watchdog self-tests (section 04 section 5.4) and OPI proof tests; every installed channel: step/dir timing, enables NO/NC, alarms; every encoder, probe and frequency input in use; gateware build and ABI; rehoming |
| MIA | per channel M0-M7: 'disarmed => drive disabled' (E3), enable NO/NC, alarm polarity; direction check: a channel outside any gantry group jogs alone at low rate; the channels of a gantry group (from the sheet's homing groups) are homed with their shared negative HOME_SEQUENCE and jogged together as one axis, never one joint alone; scales and geometry preserved |
| MX4 | M8-M11 only: E3, enables, alarms, direction check with the MIA gantry rule |
| EIA | encoder direction, count and index per port in use; MPG counts and pendant selectors; probe polarity and capture; frequency reading against a reference; XF module identity |
| EX8 | ENC4-ENC11 in use |
| XTB | continuity of XM8-XM11 and XE4-XE11 during MX4/EX8 commissioning |
| DIC | DI0-DI23 polarity and assignments; XS1: external permit removes permission; XS1.3 open opens XPC0/XPC1 (and stops a spindle only where its run or STO input is wired through XPC0); reset/arm window, contactor and STO feedback mismatch faults; PERMIT_OUT follows TX_PERMIT and stays open during both watchdog self-tests |
| DO | each assigned output energised once in a scoped commissioning action with current, open-load and fault readback; bank VS reading against the PSM monitor |
| ACC | AO zero and full scale against a meter; AI chain end to end; PROC_PERMIT removal opens PEN0/PEN1; RS-485/CAN device discovery |
| ESC | service heartbeat; accessory sequences that depend on it |
| SCART | lineage, both committed records, history ring, mirror reconciliation |

## 14. Fault containment per card

Required behaviour; every row needs a fault-injection measurement (section 04 section 13 and 14).

| Card | Stays on the port | Stays on the card | Machine-level (by design) |
|---|---|---|---|
| PSM | short at one AUX terminal: that bank's AUX limiter | short on a card's logic supply: only that slot feed trips; FIELD_A overload: FIELD_A eFuse; FIELD_B and logic unaffected | CORE entry or converter failure stops all logic; permission falls through RAILS_OK |
| CMC | USB or Ethernet port fault: that port only | CMC crash: the FPGA 5 ms command watchdog disarms | motion stops with the host |
| MC | a shorted card-bound line: its Ioff buffer channel, never the FPGA pin | FPGA clock stall: WD_M/WD_O remove permission (section 04 section 5.5) | MC failure stops motion and permission-gated outputs |
| MIA | STEP/DIR pair short: that AM26C31 output's short-circuit limit; enable contact overstress: that photorelay pair; alarm input surge: its TVS/ISO1212 channel | card power loss or removal: tamper latch, whole machine inhibited until a power cycle | any MIA fault disarms all motion (all-or-nothing arming) |
| MX4 | as MIA | as MIA | all-or-nothing arming |
| EIA | encoder 5 V short: that port's TPS2553; that encoder's data invalid at once | card power loss: tamper latch, machine inhibited until a power cycle | loss of feedback used by a loop stops motion |
| EX8 | as EIA | as EIA | as EIA |
| DIC | input surge: its TVS/RTHR/ISO1212 channel; sensor supply short: that group's limiter | controller hang: 3 failed IOL1 frames latch the port fault; DI keep their last value with growing age, then become invalid; safety terms stay in hardware | EXT_PERMIT open removes permission |
| DO | DO short: TPS274C65 current limit/thermal on that channel; the entry never trips | controller hang: accept timer (1.0 ms) or IWDG (<= 2 ms) drops CARD_EN and so DO_EN; bank load above 2.0 A: measured against declared loads, bank fault | an output feeding an essential service follows the machine's hold/inhibit policy |
| ACC | AO short: that output stage; bus wiring fault: that isolated transceiver | AI isolated supply failure: AI0-3 unavailable; AO domains unaffected | loss of a spindle speed command follows the process fault policy |
| ESC | USB service port fault: that port | ESP failure: service and accessory functions stop | only declared essential-service dependencies |
| SCART | - | stuck bus: dedicated cartridge bus with host timeouts | edits blocked until resolved; motion unaffected |

## 15. Cost structure and selling prices

### 15.1 Per card and for the controller on its own

All figures USD at quantity 100. "Recorded-price lines" sums only parts with a recorded ladder; everything else in the estimate column is an engineering estimate (section 1). PCB fabrication and assembly appear as estimate lines per card; PCBWay quotes, yield and rework, freight, warranty and certification are **not** included and remain unknown, not zero.

| Item | Recorded-price lines (USD) | Estimate (USD, qty 100) | Spare price target | Standard / expansion |
|---|---|---|---|---|
| Fixed wiring base with card cage | 0.00 | 243-384 | - | fixed |
| Field plugs, 315 standard positions | 0.00 | 110-189 | - | fixed |
| PSM | 0.00 | 64-119 | $199 | standard |
| CMC (CM5 + carrier) | 97.50 | 136-167 | $279 | standard |
| MC | 0.00 | 64-115 | $219 | standard |
| MIA | 6.77 | 46-77 | $149 | standard |
| EIA | 5.59 | 38-60 | $129 | standard |
| DIC | 15.23 | 46-68 | $119 | standard |
| DOA or DOB (each; two fitted) | 0.00 | 27-48 | $99 | standard |
| ACC | 34.49 | 121-159 | $249 | standard |
| ESC | 0.00 | 22-39 | $79 | standard |
| SCART | 0.00 | 11-27 | $39 | standard |
| MX4 | 3.38 | 34-56 | $159 | expansion |
| XTB, 136 headers and plugs | 0.00 | 104-167 | $199 | expansion |
| EX8 | 8.38 | 43-67 | $139 | expansion |

| Build | Estimate (USD, qty 100) | Against the US$400 reference | Recommended price at 45 % margin (USD) |
|---|---|---|---|
| 8 motors, 4 encoders | 955-1500 | 2.4-3.8 x | 1739-2729 |
| 12 motors (MX4 + XTB) | 1093-1723 | 2.7-4.3 x | 1989-3139 |
| 12 motors + 12 encoders (MX4 + XTB + EX8) | 1136-1790 | 2.8-4.5 x | 2069-3259 |

**Against the US$400 controller-only reference:** the complete implemented controller is estimated at $955-1500, about 2.4-3.8 times the reference, before PCBWay quotes. The largest items are the field terminal set (base headers plus plugs, $110-189 for plugs alone), the base with its slot connectors ($243-384) and the compute module ($97.50 recorded). No required function is removed to close the gap; the choices below are what the user can change.

### 15.2 Cost-driving choices

| Engineering choice | Cost difference per controller (USD, estimate) | Capability gained | Replacement-card effect | Standard or optional |
|---|---|---|---|---|
| Retained screw-flange field plugs (section 03) instead of Same Sky TBP01 5.08 mm non-locking plugs | +144 to +248 | plugs cannot vibrate loose; 3.81 mm pitch keeps the terminal rows about 25 % shorter | none | standard (adopted) |
| Fixed wiring base with separate cards instead of one board with keyed pluggable terminal groups | +176 to +292 (board-to-board connector halves on both sides, $146-222 from the cost lines, plus per-card PCB, regulation and identity overhead, estimate $30-70) | card replacement in under 5 minutes without moving a plug; faults contained per card | spare is one card, not the whole board | standard (user decision) |
| DIN 41612 / har-bus slot connectors instead of card-edge fingers | +60 to +110 (card-edge candidate not verified) | guided, coded, >= 400 mating cycles, no hard-gold fingers on every card | none | standard (adopted) |
| Expansion readiness on every unit (MX4, EX8, XS slots and the XTB connector) | +27 to +41 | MX4, EX8 and a future synchronized module install without soldering or a new base | none | standard (required) |
| Expansion terminals on the XTB (section 03) instead of all 136 on the base | -35 to -43 on 8-motor units | 8-motor units do not carry unused terminals | XTB is one more expansion part | XTB (adopted) |
| TPS274C65ASRHAR instead of TPS4H160BQPWPRQ1 with external acquisition | unknown (TPS274C65 price not recorded) | per-output current, open-load, temperature and bank-supply readings reach software | the DO spare carries the same difference | standard |
| Separate isolation for AO0 and AO1 (section 03 D03-12) instead of one shared domain | +11 to +13 (second TMR 1-2412 and ISO7740, recorded prices) | two devices with different commons without a ground loop | ACC spare | standard |
| Isolated 24 V AI sensor supply on the ACC (RECOM REC3.5-2424SRW/R8/A) | +42 to +47 (observation CAD 61.39 @100; USD is an estimate) | loop-powered 2- and 4-wire transmitters on AI0-AI3 without an external supply; the CORE_24V budget includes it (0.19 A) | ACC spare target $249 instead of $199 | standard (XAI.10 belongs to the full I/O) |
| Repair-round safety parts: OPI_BOE/OPI_OUT, OUT_EN and PEN latches, slot status register, STEP/DIR pull-downs | +3 to +6 across MC, DOA, DOB, ACC (estimate) | no output returns after a permission glitch; interrupted bank-B paths always latched; module power-good visible for every slot | DO spare +$0.3-0.6; MC +$2-4 | standard (required) |
| CM5 instead of CM4 on the CMC | +10 (qty 1 recorded retail: $97.50 against $87.50) | CPU headroom (not measured) | CMC spare | standard; CM4 qualified later |

### 15.3 Packages built around the controller

Controller estimate plus the recorded display, the MEAN WELL GST90A24-P1M control supply ($27.20 recorded; its sizing is not re-derived for this design), an HDMI cable ($3.96 recorded) and the $15 AI setup allowance (a ceiling, not an expected spend). Enclosure or pendant housing, machine-side field supplies, harnesses, packaging and setup assistance are unknown and excluded, never zero.

| Screen | Display (recorded) | Display USD | Package cost estimate (USD) | Recommended package price (USD) |
|---|---|---|---|---|
| 7 in | Waveshare 7inch HDMI LCD (B), SKU 10829 | 44.29 (qty 100) | 1045-1591 | 1873-2863 |
| 10 in | Waveshare 10.1DP-CAPLCD, SKU 23739 | 76.27 (qty 100) | 1077-1623 | 1923-2913 |
| 12 in | Waveshare 12.3inch 1920x720, SKU 28481 | 106.59 (qty 100) | 1107-1653 | 1973-2963 |
| 14 in | Waveshare 14inch 2160x1440 (US), SKU 28504 | 179.99 (qty 1 only) | 1181-1726 | 2083-3073 |
| 18 in | Luckfox 18.5-Touch-Monitor (US), SKU 32186 | 129.99 (qty 1 only) | 1131-1676 | 2003-2993 |
| 21 in | Luckfox 21.5-Touch-Monitor (US), SKU 34985 | 159.99 (qty 1 only) | 1161-1706 | 2053-3043 |

### 15.4 Recommended selling prices

Rule (recommendation, a commercial assumption rather than evidence), exactly as `gen_02.py` computes it and the validator re-checks it: price = complete implemented cost / (1 - gross margin), rounded up to the next multiple of US$10, less US$1; 45 % on the controller, 35 % on package additions and 50 % on spares and expansions. A package price is the separately rounded controller price plus the separately rounded add-on price plus the $15 AI allowance.

- Controller, eight motors: **US$1739-2729** on today's estimate. Publish nothing until PCBWay quotes replace the estimate lines.
- MX4 with XTB (field upgrade to twelve motors): US$279-449. EX8 on its own: US$89-139.
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

| Drawn file / block | Drawn value | IS-1 value | Reason |
|---|---|---|---|
| hardware/fpga_core/pin-allocation.json (sha256 24d4f7a4...) | 22 dedicated FPGA machine inputs: HOME0-11_FPGA, PROBE_FPGA (G12), TOOLSETTER_FPGA (G15), DOOR_STATUS_FPGA, PROTECTIVE_STATUS_FPGA (G16), SPINDLE_FAULT_FPGA, SPINDLE_READY_FPGA, FEED_HOLD_FPGA, CYCLE_START_FPGA, LUBE_STATUS_FPGA, SPARE_FPGA | homes and machine status move to the 24 general DI on the DIC (IOL1 L0, identity/sequence/CRC checked); balls reused: G16 -> EXT_PERMIT status copy, G15 -> PRB1, G12 -> PRB0 (terminals.json codex_net/ball fields); the other balls return to the IS-1 ball plan | all 24 DI kept with validated serial transport; FPGA pins go to 12 motors, 12 encoders and the safety logic |
| hardware/fpga_core/pin-allocation.json | DRIVE_ENABLE0-11_FPGA_RESERVED | EN0-11_N_FPGA per-channel enable (active low) to the SN74LVC07A LED drivers of the NO/NC photorelay pair | individual enable on every channel (decision 3) |
| hardware/fpga_core/design.json motor_capacity | individual_enable_circuits_present 0; alarm_circuits_present 6 | 12 per-channel NO + NC enable circuits; 12 alarm inputs (ISO1212) | eight motors standard with twelve on MX4, individual enable and alarm on every channel |
| hardware/power_entry (requirements.json) | two protected entries: CORE_24V_PROTECTED and FIELD_24V_PROTECTED | three entries: CORE (4 A class, current-limit minimum >= 3.61 A), FIELD_A (>= 5.08 A), FIELD_B (>= 5.32 A) | 16 x 0.5 A outputs plus AUX loads exceed one 6 A field entry; single-short containment (section 04 section 10.2) |
| hardware/encoder_power | ENC0_5V_LIMITED and ENC1_5V_LIMITED only | ENC0-3 on the EIA and ENC4-11 on the EX8, one TPS2553DBVR-1 per port | 4 ABZ encoders standard plus the 8-port expansion fitted together with MX4 |
| hardware/machine_permission | TPS3431 watchdog (about 57.7-71.9 ms), one arm latch | 2 x TPS3851G18SDRBT with CL10C332JB8NNNC (WD_M, WD_O), wired-AND WDO/RESET, arm_latch_M cleared by latch_clear_n and arm_latch_O cleared by latch_clear_O_n, CWD guard ring | 20 ms fault-to-inhibit with the normally-closed enable switch (section 04 section 5) |
| hardware/machine_permission and controller_assembly/assembly-map.json | six-G-input permission fan-out | IS-1 fan-out of section 04 section 6.3: PERMIT_OUT gated by PERMIT_OUT_REQ, OPI_TX/A/B/BOE/OUT, DIC_OK in base_ok, pull-downs on EXT_PERMIT_3V3 and PROCESS_PERMIT_EXT_3V3, OUT_EN latch on each output card; Codex re-runs the permission validator | corrections (2) and the repair-round safety findings |
| controller_assembly/assembly-map.json host SPI | one chip select through SN74AVC4T774PWR (4 bits) | CS_FB and CS_CMD: five buffered channels (second buffer or wider part), SERVO_MARK test point | two fixed-length transactions per cycle (section 01 D01-1) |
| output driver block (assembly map) | TPS4H160BQPWPRQ1 with CS only to a test point | 2 x TPS274C65ASRHAR per 8 outputs behind one ISO7762FDBQR, OUT_EN latch, STM32G031K8T6 on IOL1 | T1: per-output current, open-load and temperature must reach software |
| tx_twelve / tx_bank | 10-contact motor plug; STEP/DIR receiver-input idle pulls not stated | 14-position motor plug (13 used, section 03 D03-3); 10 kOhm pull-downs on every AM26C31 STEP/DIR input on MIA and MX4 | enable NO/NC and AUX supplies per plug; a floating input must rest at the idle level (section 04 section 4.2) |
| base and motion-card connectors (not drawn) | presence/power-good of DIC, DOA, DOB, ACC, ESC, CMC, XS, SCART not routed to the FPGA | 29 lines to the MC slot status register (section 6 MC groups; section 01 section 4.10) | module power-good diagnostics (A2) need a physical path |

### 16.2 Parts recorded as Codex BOM items with the interface limits they must meet

| Item | Owner | Interface limits it must meet |
|---|---|---|
| cartridge configuration memory (SCART) | Codex | capacity >= 2 x the committed-record size of MODULAR_REPAIR_AND_MEMORY.md (two generations); >= 10^5 write cycles; >= 20 years retention; hardware WP pin driven by CART_WP_EN; I2C 400 kHz on the dedicated cartridge bus; 2.7-3.6 V |
| ACC AI ADC | Codex | >= 4 channels; >= 1 kHz per channel [REQ]; >= 16-bit; <= +/-0.1 % of full scale after the card's factory calibration over 0-55 C on the 0-10 V and 4-20 mA ranges; SPI to the STM32G031K8T6 across the AI-group isolator |
| ACC AI-group isolated supply | Codex | selected: RECOM REC3.5-2424SRW/R8/A (18-36 V in, 24 V 145 mA, 84 %, DigiKey listing); a cheaper isolated converter meeting 24 V >= 120 mA, >= 80 % efficiency and >= 1.5 kV isolation may replace it after costing |
| isolated RS-485 transceiver (ACC) | Codex | half-duplex, >= 1 Mbit/s, fail-safe receiver, driver enable from RTS, >= 2.5 kVrms isolation, bus-pin ESD >= 8 kV contact, <= 1/4 unit load |
| isolated CAN FD transceiver (ACC) | Codex | >= 2 Mbit/s data phase (MCP2518FDT-E/SL controller), >= 2.5 kVrms isolation, bus-fault protection covering a 24 V short, dominant time-out |
| ARM_LAMP driver (DIC) | Codex | 24 V high-side, 50 mA continuous, current limit <= 0.1 A, survives a sustained short, fault flag readable by the DIC controller |
| MPG, XF and probe supply limiters (EIA) | Codex | MPG 5 V 100 mA, XF 5 V 150 mA, probes 24 V 100 mA each; limit <= 1.5 x load; fault flag into the EIA status register |
| enable-loop and PERMIT_OUT TVS (MIA, MX4, DIC) | Codex | bidirectional, stand-off >= 30 V, clamp < 60 V at its rated pulse (section 04 section 3.2) |

### 16.3 External modules named by the allocation sheets

| Module | Interface | Provides | Status and cost |
|---|---|---|---|
| plasma.divided_voltage.v1 | XF: FREQ0 differential frequency output on XF.3-4 (FREQ1 on the second pair), FREQ_5V supply 150 mA limit (XF.1), 1-Wire identity on XF.7 and presence on XF.8, both bound to the module record | isolated measurement of the source's documented divided arc voltage, delivered as a frequency on FREQ0; conditioned Arc OK and a source-compatible torch-start interface for sources whose CNC port does not offer a dry Arc OK contact and a torch-start input within the XPC0 rating (0-30 V, <= 50 mA) | proposal (docs/PLASMA_MODULE_SYSTEM.md); not designed, rated or qualified; cost unknown, not zero; priced with the plasma package, not the controller |
| external ohmic-sensing module | isolated contact output into PRB1 (XPR.4) and enable from process-enable 1 (XPC1) | ohmic torch-to-plate contact detection | requires a separately qualified module; no interface record beyond the terminals above; cost unknown, not zero |

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
| FPGA pin fit of 175 signals | Efinix Efinity place-and-route (not installed) | Arithmetic budget, section 8.1 |
| Connector footprints, card guides, cage mechanics | Codex PCB and enclosure work (owner) | Families and part numbers fixed here |
| Contact-rating and creepage checks of mixed rows | Codex layout | Row rules of section 7 |

Sources opened for this section: TI TPS274C65 product page and datasheet SLVSFZ2C; HARTING product pages 09031966921, 09032966421, 09031326921, 02011601101, 02071601101, 09061152911, and catalogue listings for 09032326824, 09062152821, 09036966921; Rapid Electronics pages for HARTING 09 03 296 6825 and Phoenix 1843321; Microchip AT30TSE752A/754A/758A datasheet (Atmel-8854G); TI INA238 and TCA9548A product pages; distributor search results for STM32G031C8T6, ESP32-S3-WROOM-1U-N8 and HARTING 09031966921. Recorded prices come from `research/hardware-cost-model.json` and `research/compute-display-matrix.json`.

## 19. Not claimed

No card, base, connector footprint, firmware, gateware or driver described here exists. No cost is a quotation. No replacement time, current accuracy, temperature accuracy or containment behaviour has been measured. Nothing here is a certified safety function or ready for manufacture.

---

Interface specification revision IS-1. Nothing in this section is implemented, measured or ready for manufacture.
