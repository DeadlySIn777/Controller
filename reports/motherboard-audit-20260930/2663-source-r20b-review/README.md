# Independent physical-source and population audit — r20b

Exact adopted source: `reports/motherboard-integration-20260930/r20b-2663-electrical-corrections-staged`. This is a read-only engineering audit. The original MC and the current source/PCB are unchanged. It does not certify all manufacturer pin/land geometry, target FPGA fit, routing, thermal behavior or manufacturing readiness.

Source anchors:

- design.json SHA256 `20a9e94efcf5f7e7a18e278b4b6ca05a1f339fe6c29b4409c79d7858fd57a603`
- native XML SHA256 `1ef078a7bcdf3580173e9a545f1a327ef6e1836a25631c8b8a9bb515411cec47`
- assembly-map SHA256 `792fe307b52178b6975c7cc48133299d369b754e8922627a674d3fc79fe4ff9a`
- BOM SHA256 `c9dec2c91aa17fb8d544516430cce7ce7a4a27ed216c55ed252dbfcbd6b73c8c`

`input-hashes.json` preserves67 original immutable inputs. The independent audit rerun checks all67 before comparing source/native physical references, exact MPNs, footprint IDs and BOM membership. `semantic-input-hashes.json` preserves the additional primary datasheet/frozen-contract/RTL sources used for endpoint classification. Root adoption evidence records native ERC **0 errors,68 unsuppressed warnings,0 ignored checks**, independent source-validation pass and **50 focused root tests passed**. Those are reused exact source results; this report does not claim a new ERC/DRC/target build.

## Exclusive physical inventory

**2663 physical footprints =2627 purchased fitted components +33 bare testpads +1 bare chassis bond pad +2 DNP footprints.** Native footprint-reference sets, source models and exact BOM references agree. The2 DNP parts are R7015/R7016, the optional MPG termination resistors. The33 testpads and H19501 chassis annulus are fabricated PCB geometry, excluded from purchased components and assembly placement. Separate M4 chassis bond hardware still requires an assembly selection.

The original category predicate missed TP19001 and H19501 because it looked only for one literal testpad MPN. `audit-before-exclusion-correction.json` retains that incorrect2629/32 result as superseded evidence. The corrected predicate honors explicit purchased=false and verifies the actual testpad/mounting footprints. It agrees with the independent cost v5 **2627/33/1/2** classification; no source part was removed to change the count. A further190 legacy physical entries omit the optional `physical` key: the parent component dictionary is already exclusive physical, so filtering it through bool(component.get('physical')) would wrongly discard them.

| Source region | Physical footprints | Purchased fitted | Bare PCB geometry | DNP |
| --- | ---: | ---: | ---: | ---: |
| fpga_core | 70 | 70 | 0 | 0 |
| mc_local_power | 48 | 48 | 0 | 0 |
| mc_motor_buffers | 124 | 124 | 0 | 0 |
| mc_permission | 56 | 56 | 0 | 0 |
| motherboard_acc_control | 50 | 44 | 6 | 0 |
| motherboard_analog_input | 165 | 165 | 0 | 0 |
| motherboard_analog_output | 143 | 143 | 0 | 0 |
| motherboard_comms | 95 | 95 | 0 | 0 |
| motherboard_compute | 191 | 183 | 8 | 0 |
| motherboard_control_bridges | 6 | 6 | 0 | 0 |
| motherboard_di | 120 | 120 | 0 | 0 |
| motherboard_do | 110 | 110 | 0 | 0 |
| motherboard_esp_socket | 23 | 23 | 0 | 0 |
| motherboard_fast_inputs | 28 | 26 | 0 | 2 |
| motherboard_identity_io | 14 | 14 | 0 | 0 |
| motherboard_io3_upgrade | 2 | 2 | 0 | 0 |
| motherboard_io3_window | 1 | 1 | 0 | 0 |
| motherboard_io_control | 100 | 82 | 18 | 0 |
| motherboard_motor_power | 65 | 65 | 0 | 0 |
| motherboard_motors | 226 | 226 | 0 | 0 |
| motherboard_operator | 198 | 198 | 0 | 0 |
| motherboard_power_entry | 221 | 221 | 0 | 0 |
| motherboard_process | 68 | 68 | 0 | 0 |
| motherboard_safety_sensor | 176 | 175 | 1 | 0 |
| motherboard_status | 290 | 290 | 0 | 0 |
| motherboard_terminals | 44 | 43 | 1 | 0 |
| watchdog_conditioning | 29 | 29 | 0 | 0 |
| Total | 2663 | 2627 | 34 | 2 |

Regions are schematic/functional regions on **one custom active PCB**, not separate cards. R/C references total1969 and explicit TVS-kind components65. Those do not establish that isolation/diagnostic circuits are expendable.

## Rack, module and duplication findings

No actual DIN41612, har-bus, H15 power connector, card cage or card-guide component was found in the physical inventory. The historical rack topology has not survived as a fitted connector family.

Actual compute bay sockets are J15001/J15002, Amphenol10164227-1001A1RLF. Actual replaceable ESP board sockets are J16001/J16002, Würth61302211821. Actual SD socket is J15003, Molex503398-1892. Purchased CM/ESP boards are separate from the custom PCB BOM. There is **no fitted BCM/H616/RK Linux SoC, soldered ESP processor, M.2 socket or expandable RAM slot** in this motherboard inventory. Same-form-factor BTT compute interchangeability is not electrically qualified by these sockets.

One T20 FPGA and four STM32 MCUs are fitted: U13001 DI acquisition/control, U13004 DOA, U13008 DOB and U14501 ACC analog/process. These MCUs own actual local IOL1 acquisition/reset/output/default behavior; they are not four duplicate Linux computers. CORE5/MOTION5/FPGA1.2 supplies and five independent analog-island converters have different voltage, return-domain and headroom functions. No isolation supplies were removed to reduce a count.

U5004 is a concrete future consolidation candidate: one used SN74LVC244A channel, pin2 TX_PERMIT→pin18 TX_PERMIT_A_BUFFER_OUT; VCC IO3, GND LOGIC, both OE LOW and the other seven inputs grounded. It is a functional Ioff permission buffer. Substituting an exact single-channel part needs an off-state/load/default/land review. **No component is presently proven safe for deletion without a circuit review.**

## Exact named single-pad obligations

`single-pad-semantic-classification.json` independently counts physical pads in native XML rather than accepting nonphysical schematic connectors as receivers. It classifies all **69 named nets with one actual physical pad**:

- Seven obsolete dedicated FPGA machine-status inputs. Frozen modules.json explicitly moves machine status and homes onto DI24/IOL1. Their exact U1001 balls H13/G14/H14/H15/H16/J15/K14 can be reconciled to native NC while preserving all24 DI and real machine functions. The saved working-r14 board proves all seven have **zero tracks/vias/zones**. No change is made by this report.
- Four live FPGA diagnostic fault outputs A3/C6/A4/E5. The bring-up RTL actually produces these signals; propose four real labelled bare testpads and test-only use. Do not NC them as rack remnants.
- Eight exact optional PCIe contacts on J15002. Optional NVMe is unimplemented; propose explicit contact NC and removal of its unused page ports while keeping actual SD/eMMC. A raw pin label is not an M.2 implementation.
- Two unused builtin TPS62901/02 PG pins. Real core/IO permission uses independent U2004/U2005 LTC2962 voltage windows and U2006.4 FPGA_CRESET_N. The builtin pins are unpulled/unobserved and can be explicitly documented NC; do not promise their telemetry.
- Three unused TPS26630 FLT outputs. TI permits these outputs floating if unused. Protection still operates, but a readable FLT flag requires an actual pullup and receiver in its own ground domain. Propose documented NC only without crediting absent flag telemetry.
- One unobserved U11006.16 FIELD_B entry PGOOD. Frozen PSM groups require F_PGOOD_A/B. Actual AUX24_B/AUX5_B motor-bank health is A-derived, not independent B-entry health: U11016.1 uses FIELD_A_24V_PROTECTED and U11014.1 uses FIELD_5V. It is not a substitute. A bounded real separate-return receiver is required.
- **44 ISO1212 substrate islands** (DI24, motor alarms12, probes2, safety6). TI pins12/13 connect internal die substrates and recommend an individual floating2×2mm plane. These are **not field returns**. Never join them to GND, FGND, each other or another signal. Preserve/document the individual island geometry; exact44 corrects the earlier42-count assumption.

Additional driver omission found while classifying entry PGOOD: both DOA_FIELD_POWER_GOOD and DOB_FIELD_POWER_GOOD currently consist of MCU PB1/pin16, existing10k LOW bias and a nonphysical boundary; they have **no actual physical driver**. Existing DOB local voltage window drives the independent safety-domain health, not these MCU inputs. New minimal integrated source22 should add two real isolated entry-PG receivers with their distinct field returns and preserve all existing voltage-window/safety wiring. They are read-only observations, not constants or motion permission grants. FA_PGOOD also serves an analog converter-EN divider (~1.6–2.7V): direct connection to a3.3V ISO CMOS input would fail the HIGH threshold, so its receiver needs a real level qualification that does not alter that divider.

The exact proposals and open hardware connections are engineering-source obligations. They are not deferred physical-prototype-only issues and are not suppressed by this audit.

## Source versus actual routed PCB

Published CAD23 SHA256 `54c0889735c59f3d516319e50912a1db7b034781b32b1b70984885c2741efba5` contains **1780 footprints,5928 track/via items,5 zones and6 copper layers**. Its independently recomputed own1780-source connectivity records **514 complete of1160 multiple-pad nets,646 incomplete nets,2893 uncapped missing joins,0 orphan copper**. Its complete_source_population_pass applies to that older1780 source subset only. Against r20b2663, **883 physical source footprints are missing**.

CAD23 has five source-footprint substitutions still absent: L11001 larger XAL1010, AO converters U14601/U14619 new wide-input SIP8, and U14026/U14027 corrected MAX17612 package. Saved working-r14 contains1780 footprints/5890 tracks-vias/5 zones and applies those five exact corrections; all common footprint IDs now agree with r20b. Its38-item copper removal is bounded correction evidence, not a claim that all old copper remained unchanged. It still lacks883 source parts. Root owns subsequent full population and routing.

The provisional outline centerline is460×340mm; the native bounding box460.15×340.15 includes its0.15mm stroke. This is not a final enclosure, mounting or manufacturing outline. None of these partial boards is a release for PCBWay.

## Cost and evidence limits

This report's inherited980-price coverage is deliberately historical:58 exact current purchased MPNs have some old USD catalogue evidence, with231 current purchased MPNs absent from that older basket. All full current1/10/100 totals remain null here. Use the separately frozen current `reports/motherboard-cost-20260930/source-r20b-2663-complete-cost-v5/` for current exact-MPN observations/MOQ cash/partial subtotals; never substitute an old part's price for a new converter/coil/shunt. It still reports unknown full manufactured/controller kit totals. Package-name whitelist misses are not proof of wrong manufacturer geometry.

This audit checks actual source/native/BOM/ref identities and exact limited endpoint semantics. It does not independently reverify every manufacturer's die function or land dimension. Those remain tied to child source reviews plus final native geometry/electrical checks. Target compilation, production twelve-channel HDL/FPGA vendor fit, loaded real-time timing, physical rail/inrush/thermal behavior, complete routing/return/clearance and a full procurement/manufacturing package remain separate evidence gates.
