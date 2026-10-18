# Electrical and hardware handoff from the 2026-09-28 audit

Status: **handoff only.** Nothing in this file changes the hardware design, and nothing here is ready for manufacture. Evidence class is source inspection and datasheet desk work unless an entry says otherwise. No ERC, DRC, simulation of circuits, Efinity run or physical measurement was done for this handoff.

Scope: the six-joint/two-encoder baseline ledger (`hardware/electrical-design.json`, revision electrical-r0.1). None of this applies to the eight-motor/four-encoder candidate, which needs its own ledger.

## How this was checked

Every item was re-read against the live tree at 2026-09-28T21:25Z, because Codex was designing hardware blocks at the same time.

- `hardware/electrical-design.json` (sha256 `f5abb8b1...`), `tools/hardware_build_design.py` (`be0a93df...`) and `tools/hardware_validate.py` (`01f5b9b7...`) have not changed since 08:48Z. `hardware/validation-report.json` still describes that ledger (`design_sha256` matches).
- Since then Codex has added ten partially connected blocks: `hardware/power_entry`, `core_converter`, `logic_power`, `field_power`, `encoder_power`, `sbc_power`, `power_sequence`, `digital_inputs`, `rx_abz` and `tx_six`, joined in `hardware/controller_assembly`. Their current review record is `reports/connected-hardware-20260928/review.json` (208 scoped tests, `manufacturing_ready: false`). Those blocks settle some audit items at block level, but none of their part choices have been written back into the ledger.
- Status values used below:
  - **open**: the defect or gap is still in the live files.
  - **resolved-by-Codex**: a current Codex file removes the problem. The file is named.
  - **partly resolved-by-Codex**: a Codex block addresses it, but the ledger or another file still carries the old state.

Verified candidate MPNs from the audit's desk research are in [`part-selections.json`](part-selections.json). None of them has been integrated. The authoritative place to adopt them is the generator `tools/hardware_build_design.py`, followed by the regeneration sequence below. Do not hand-edit generated JSON or CSV files.

Regeneration sequence after any generator change:

1. `python tools/hardware_build_design.py`
2. `python tools/hardware_validate.py`
3. Rerun the block flows whose `validation.json` pins the ledger hash. These are `tx_six`, `rx_abz`, `encoder_power`, and every block with an `input-electrical-design.json` copy: `digital_inputs`, `field_power`, `logic_power`, `power_sequence`.
4. `python tools/hardware_record_review.py`, or retire `hardware/review-manifest.json` in favour of the connected-hardware review (see E-08).
5. `python -m unittest discover -s tests -p "test_hardware*.py"`, then the full suite.

Ledger IDs in brackets refer to [`findings-ledger.json`](findings-ledger.json).

---

## A. Ledger validator and review recorder

These live in `tools/hardware_validate.py`, `tools/hardware_record_review.py` and `tests/test_hardware_validation.py`. They are consistency checks only; closing them does not move the board toward manufacture.

### E-01. `--release` trusts ledger-declared readiness (open) [R1-031, FU-HW-01]

Line 19 seeds `blockers` from `d["release_blockers"]`. Line 96 blocks only on `physical_mapping_complete`, and line 158 only on the `hardware_implementation_status` string. A ledger copy that sets both flags, empties `release_blockers` and fills any MPN string still exits 0 under `--release`.

Change belongs in `tools/hardware_validate.py`:
- Derive mapping completeness from the pin and bank data.
- Require on-disk, hash-checked permission-circuit evidence before `reviewed_complete` is accepted.
- Seed from a validator-owned constant list of baseline blockers.
- Treat placeholder MPNs as unresolved.
- Add fault-injection tests.

Until then, `docs/ELECTRICAL_DESIGN.md:12` should say that `--release` checks ledger-declared status only.

### E-02. Negative or NaN `load_target_a` accepted (open) [R1-040, FU-HW-02]

Lines 78-80 check only the upper limit. The value is then summed into `bank_load` and into the `field_outputs` comparison, so a negative entry can hide an over-budget bank. Reject non-numeric, non-finite and negative values, and add tests.

### E-03. Non-channel terminal positions unchecked (open) [R1-034 residual, FU-HW-03]

Channel nets are reconciled, but supply, ground, reference and NC positions are not. Line 136 exempts any `*_5V_LIMITED` net. Nothing catches the `JANA`, `JDI`, `JDO` or `JPOWER.1-4/8` positions.

Fix: add an explicit `(connector, position) -> (net, domain)` table, shared with the generator's connector layout, and remove the regex exemption.

### E-04. Supply declarations optional for most parts (open) [R1-035 residual, FU-HW-04]

Lines 40-45 skip the supply check when `rail` or `allowed_supply_v` is missing. Require one of these on every part with an MPN:
- `rail` plus a valid `allowed_supply_v` pair, or
- an explicit `rail: "none"` for passives, set in the generator.

### E-05. Zero-padded component aliases bypass collision checks (open) [FU-HW-05]

`TX01` is accepted as a distinct key from `TX1`. Canonicalise with `(TX|RX|DI|DO|DAC)(0|[1-9][0-9]*)` before the collision and bank-load checks.

### E-06. RTL watchdog cross-check fails open; CORE_HZ not compared (open) [FU-HW-06]

Lines 150-153 add no error when `gateware/rtl/cnc_endpoint.v` is missing or the regex does not match. The regex still matches today (`parameter integer WATCHDOG_CYCLES = 250000`). `CORE_HZ` (`parameter [31:0] CORE_HZ = 50000000`) is not compared with `fpga.clock_hz`.

Fix: fail closed, and parse `CORE_HZ` in both the generator and the validator.

### E-07. Hardware tests do not check the checked-in ledger (open) [FU-HW-07]

All `tests/test_hardware_validation.py` cases validate a fresh `build()`. Add:
- a read-only test that the file equals `build()` and validates with `manufacturing_ready: false`;
- message-specific mutation tests;
- a `--release` exit-code test using a temporary output path.

Also convert the `tests/test_rx_abz.py` mutations to message fragments, as `test_tx_six.py` already does.

### E-08. `hardware/review-manifest.json` stale and incomplete (open) [R1-056 residual, FU-HW-00, FU-RV-11, FU-CD-07]

The manifest was recorded at 08:46:22Z. 8 of its 55 hashes no longer match: the ledger, the validation report, the `tx_six` and `rx_abz` `validation.json` files, `docs/ELECTRICAL_DESIGN.md`, `hardware_build_design.py`, `hardware_validate.py` and `test_hardware_validation.py`. `BLOCKS` in `tools/hardware_record_review.py:14` still lists only `tx_bank`, `tx_six` and `rx_abz`.

`reports/ENGINEERING_STATUS.md` now names `connected-hardware-20260928/review.json` as the current hardware record and this manifest as superseded.

Decision for the hardware owner: either re-record it through the recorder, after adding the new blocks, or formally retire it and point `docs/ELECTRICAL_DESIGN.md:119` at the connected review. Never hand-edit the hashes.

### E-09. Rate cap rounded in the generated report (open) [FU-CD-12]

Line 157 formats with `:g`, so `validation-report.json` shows `195312/s`, not `195312.5/s`. Format the value exactly and regenerate.

---

## B. Ledger content (generator `tools/hardware_build_design.py`)

### E-10. Host still recorded as ROCK 3C (open) [R1-037, FU-CD-08]

Line 49 `host.engineering_baseline` is "Radxa ROCK 3C RS112-D2". `docs/ELECTRICAL_DESIGN.md:16-18` and its `SBC[ROCK 3C]` mermaid node are also unchanged. `PROJECT_MEMORY.md` and `docs/COMPUTE_CARRIER_STRATEGY.md` record the compute choice as open (CM4/CM5/CB2 carrier family).

Change the host block to `candidate_not_selected` with the candidates listed. Keep a single 3 A `sbc_budget` row, reworded as a host-family envelope; do not add a second row, which would double-count. Generalise blocker line 172 ("ROCK3C PREEMPT_RT...") in the same way.

This is a documentation-of-decision change. It does not make the user's compute decision.

### E-11. Ledger scope and first blocker describe only the two-joint TX circuit (open) [FU-HW-14, FU-CD-14]

Line 48 scope and line 164 blocker are affected. Ten connected partial blocks now exist in `hardware/controller_assembly`. Reword both to "partial blocks exist; no complete controller schematic, layout or board DRC", ideally generated from the same block list the review uses. Keep it a release blocker.

### E-12. The 250 ksteps/s blocker cites only the DDS cap (open) [FU-CD-09]

Line 170, the validator warning and `docs/ELECTRICAL_DESIGN.md` (lines 35, 39 and 104) still name only the `0x01000000` cap (195,312.5 steps/s). The second limit is now documented in `gateware/PROTOCOL.md` and the status reports: with 100/100-tick defaults the minimum STEP period is 201 ticks, so no cap above `0x01460CBC` (248,756 steps/s) is fault-free. Add that to the ledger text. Do not change any limit.

### E-13. Useful-progress WDI now exists in RTL; ledger text and board coupling are stale (open) [R1-059]

The RTL now drives `progress_wdi`. It toggles once per accepted opcode-3 frame and does not toggle on ARM (`gateware/synthesis/manifest.json` `top_ports`). The ledger still says `watchdog_wdi_implementation: "Not exposed by current reference RTL"` (line 136) and carries the blocker "Useful-progress WDI absent from current reference RTL" (line 169).

Update the wording to "RTL output exists; board routing to the external watchdog and its timing are not drawn or measured", and keep a blocker for the board part. The toggle rate follows the accepted servo cadence, which the driver now bounds to at most half the 5 ms RTL watchdog. Record that as the WDI service-interval assumption for E-30.

### E-14. `rx_termination` rating below the drawn block (open) [FU-HW-08]

Line 214 still gives ">=0.125W" with no MPN. The `rx_abz` block fits CRCW1210120RFKEA (0.5 W, 1210), and its own 5.5 V bound needs 0.2585 W per resistor.

Sync the ledger row to the block. [`part-selections.json`](part-selections.json) group 1, `not_selected`, records this.

### E-15. No receiver decoupling rows (open) [FU-HW-09]

Add `rx_decoupling` (2 x 100 nF) and `rx_bulk` (2 x 1 uF) to `known_support` after `rx_termination`. The BOM grows from 62 to 64 groups; do not describe the BOM as complete.

### E-16. RS-422 reference return on JPOWER, not on the JTX connectors (open) [R1-039]

JTX0-2 carry only four pairs. `TX0-2_REFERENCE` sit on JPOWER positions 5-7 (terminal layout, lines 285-296). The ledger already declares this open.

Fixing it means re-allocating terminals, regenerating `terminal-map.csv`, updating the `tx_six` JREF mapping and its checks, and re-costing the connectors. This is a connector decision that should be made with the first machine's drive cabling (E-22).

### E-17. Rail headroom warnings (open, advisory) [R1-063]

`CORE_5V` is at 5.35/6.00 A and `CORE_24V` at 1.81/2.00 A. Both capacities are requirements, not selected parts. See E-33 for the input-path limit that any higher 5 V rating depends on.

### E-18. Value-fixed passive bundles have verified MPNs, not integrated (open) [R1-060]

[`part-selections.json`](part-selections.json) group 1 covers:
- `tx_series`, `tx_data_pulldown`, `tx_permit_pulldown`, `di_rsense`: CRCW0603 parts;
- `tx_decoupling`, `tx_bulk`, `di_decoupling`, `iso_decoupling`: CL10B series;
- `di_rthreshold`: MMA02040C1001FB300 MELF, per TI's 0.25 W MELF requirement;
- `do_pulldown`: value still provisional;
- `analog_gain`: ERA-3AEB303V and ERA-3AEB103V.

Adopt these as status `candidate`, keeping each row's open-qualification note. Surge coordination of the ISO1212 RTHR against the SMF36A TVS is still open. The MMA 0204 1.2/50 us rating (about 0.7-0.8 kV) was read from a graph.

### E-19. FPGA configuration flash, clock, JTAG and decoupling (open) [R1-061]

[`part-selections.json`](part-selections.json) group 2 covers:
- W25Q32JVSSIQ configuration NOR;
- ECS-2520MV-500-BN-TR 50 MHz XO (±50 ppm all-inclusive);
- Wurth 61201021621 2x5 JTAG header;
- the decoupling set copied from the Efinix T20F256 development-board schematic Rev 3.0, sheet 5.

The Efinix *Trion Hardware Design Checklist and Guidelines* could not be downloaded, so the decoupling set must be re-checked against it before freeze. Keep `support_decisions[4]` and the pin/bank and Efinity blockers.

A ±50 ppm oscillator shifts the RTL rate cap and the 5 ms watchdog by at most 50 ppm; no limit changes. See E-37 and E-38 for the configuration-mode and buffer decisions tied to these rows.

### E-20. Converter and support selections (partly resolved-by-Codex) [R1-065]

Codex's blocks now select parts for most of these rows:

| Function | Codex selection | File |
|---|---|---|
| Local bucks | TPS62901RPJR with XGL4020-222MEC | `hardware/logic_power/design-envelope.json` |
| Main 5 V | LM70660RRXR | `hardware/core_converter/requirements.json` |
| Field 5 V | LMR36506R5RPER | `hardware/field_power/design.json` |
| Encoder load switches | TPS2553DBVR-1 | `hardware/encoder_power/bom.csv` |
| Entry eFuses | TPS26630RGER + CSD19537Q3 | `hardware/power_entry/requirements.json` |
| Entry TVS | SMCJ30CA | `hardware/power_entry/requirements.json` |
| Supervisor | LTC2962HUD#TRPBF | `hardware/power_sequence/design-envelope.json` |

The ledger still lists `buck_*` as TPS62160DSGR, still names TPS62160 in the IO_3V3/ESP_3V3/CORE_1V2 rail `source` strings (generator lines 79-81), and keeps `local_buck_*`, `main_5v_converter`, `field_5v_converter`, `power_supervisor`, `encoder_load_switch`, `esp_branch_limit` and the entry-fuse rows as `required_unselected`.

Integrate the block choices into the generator.

Still unselected anywhere:
- `esp_branch_limit`: part-selections group 3 proposes TPS2553DBVR-1 with RILIM 29.4 k.
- `do_current_set` and `do_diag_support`: group 3, but see E-35, E-36 and the TPS4H160 overvoltage note.
- USB-C recovery and expansion: design tasks.

### E-21. Permission gate/latch block and analog zero clamp not drawn (open) [R1-062]

`permission.hardware_implementation_status` is `not_drawn`, and no permission block exists under `hardware/`.

Draw it with the existing block pattern (`tools/hardware_build_<block>.py` + `tools/hardware_validate_<block>.py` + a test). Record an intermediate status such as `block_drawn_erc_only`, never `reviewed_complete`. Keep the transient-network and physical clamp, propagation and glitch items as release blockers.

The latch set path must come only from the FPGA arm output, never from the ESP.

### E-22. First machine profile (open, user decision) [R1-072]

This needs the user's target machine, drive/VFD models with manuals, encoder types, loads and stop arrangement (`docs/HARDWARE_PRE_DESIGN.md` §18). Record the answers as a new machine profile file. Leave `config/machine-study.json` illustrative. Until then, the `interfaces[]` targets stay proposed.

### E-23. JTX connectors labelled "FIELD TERMINALS" (open) [FU-HW-12]

`tools/hardware_build_tx_six.py:116` puts this label on connectors the ledger places in the non-isolated LOGIC domain. The label reaches `hardware/tx_six/bom.csv` (3 rows) and `hardware/controller_assembly/tx_six.kicad_sch`.

Change the label in the generator and regenerate through the documented `tx_six` and assembly flows.

### E-24. Text defects in the power-entry requirements (open, cosmetic)

`hardware/power_entry/requirements.json` `release_blockers` still contain fused words, for example "selectedresistor", "mustbequalified" and "Core3A". The mojibake seen earlier is gone. Fix this in `tools/hardware_build_power_entry.py` and regenerate.

---

## C. Research engineering notes (desk datasheet work, 2026-09-28)

### E-30. TPS3431 external watchdog cannot meet the 20 ms study limit (open) [R1-064]

The ledger `watchdog` row is TPS3431SDRBR. `watchdog_timing` is `required_unselected`, and `external_watchdog_study_ms` is 20. The TPS3431 datasheet (SNVSB66A, Eq. 1: tWD = 77.4 x CCWD[nF] + 55 ms, boundaries 0.905x/1.095x) gives 56.77 / 62.74 / 68.7 ms at the smallest tested 100 pF capacitor. That is 3.4 times the 20 ms maximum. The factory options are 170-230 ms and 1360-1840 ms. The requirement (min > 5 ms RTL watchdog, max <= 20 ms) cannot be met with this part, and no timing capacitor was selected. No Codex block adds a watchdog; `hardware/power_sequence` supervises rails only.

Candidate alternative (not applied), corrected on 2026-09-28 after a second datasheet check: TI **TPS3851G18SDRBT** (250-piece reel) or TPS3851G18SDRBR, standard-timing `S` variant, both listed Active in TI's SBVS300B orderable addendum, with **CCWD = 4.7 nF C0G ±5 % (Samsung CL10C472JB8NNNC, 0603, 50 V; product page checked)**. Eq. 1 (standard timing) is tWD = 3.23 x CCWD[nF] + 0.381 ms with TI boundaries 0.905x/1.095x, giving **13.40 / 15.56 / 17.87 ms**. The extended-timing `E` parts (77.4 x C + 55 ms) and the fixed 170-230 ms / 1360-1840 ms settings cannot meet 20 ms.

**Correction:** an earlier version of this entry proposed 3.3 nF (9.51 / 11.04 / 12.67 ms). That is wrong for this design. TPS3851 WDI restarts the timer only on a falling edge (datasheet pin table and section 6.3.4.2), and `progress_wdi` inverts once per accepted UPDATE, so a falling edge arrives only every second UPDATE. The FPGA still accepts UPDATEs up to its 5 ms command-gap watchdog, so falling edges can legally be almost 10 ms apart. The external minimum timeout must therefore exceed about 10 ms, which 3.3 nF (9.51 ms minimum) does not.

Caveats:
- With 4.7 nF only 20 - 17.87 = 2.13 ms remains for everything after WDO (pull-up RC, latch, gates, isolators, output stage and the drive's enable response). If the measured downstream latency exceeds about 2 ms, use 3.9 nF C0G ±5 % (11.18 / 12.98 / 14.90 ms, 5.10 ms budget; MPN not yet verified), or change the RTL so `progress_wdi` produces one short pulse per accepted UPDATE (one falling edge per frame), which lowers the required minimum back to about 5 ms.
- Use the **G18** threshold variant supplied from IO_3V3 as a supply-present check only. The G33 variant (trip 3.143-3.193 V, release up to 3.219 V) and G50 on CORE_5V (release up to 4.877 V) overlap their rail minima. Rail supervision stays with the separate supervisor, and it must not conflict with Codex's LTC2962 windows (E-39).
- TPS3851 is a supervisor plus watchdog, so pinout, footprint and permission wiring differ from TPS3431. It is a plain timeout watchdog (no early-fault window). WDI is ignored while RESET or WDO is low; after power-up the watchdog is disabled for tRST (170-230 ms), so the permission latch must also be qualified by RESET, and a WDO fault must be latched because WDO is a pulse.
- WDO pull-up: 1-100 k to the pull-up rail (for example CRCW060310K0FKEA to IO_3V3). SET1 must be high to enable.
- Codex's `hardware/machine_permission` block currently uses TPS3431SDRBR at about 57.7-71.9 ms and treats it as clock-stall backup only (reports/MACHINE_PERMISSION.md). That replaces the 20 ms study value without a recorded decision; keeping about 72 ms or moving to TPS3851 with 4.7 nF is a user decision.

Choosing a part change or changing the 20 ms study value is a ledger decision for the owner and user. Do not relax the limit to make a check pass.

Where: `tools/hardware_build_design.py` `watchdog` (line 199), `watchdog_timing` (line 220) and the `permission.external_watchdog_*` fields (line 139), then `docs/ELECTRICAL_DESIGN.md` permission section. The permission block (E-21) consumes this output.

### E-31. DAC80501 power-up configuration fails to zero below 5.0 V (open) [R1-036 residual]

The ledger `dac` role reads "internal2.5Vref gain1 (0-2.5V full scale)". Per the DAC80501 datasheet:
- Section 7.3: with REF-DIV = 0, VREFIO is limited to 0.5 x VDD. The internal 2.5 V reference therefore needs VDD >= 5.0 V in that mode.
- ANALOG_5V may be as low as 4.85 V.
- Section 8.3.2: an improper divider setting raises a reference alarm that forces VOUT to 0 V.

The power-on default (REF-DIV = 0, BUFF-GAIN = 1, the 0-5 V range) is therefore a fail-to-zero state whenever ANALOG_5V is below 5.0 V. That direction is safe, but the spindle command would not work.

Required configuration: write GAIN register 4h with REF-DIV = 1 (divide by 2) and BUFF-GAIN = 1 (x2), a net x1 for 2.5 V full scale, before enabling the output, and check the reference alarm. The DAC then has 4.85 - 2.5025 = 2.35 V headroom against a 0.3 V specification at 10 mA. BUFF-GAIN = 0 with REF-DIV = 0 is not a listed output range.

Accuracy (untrimmed, desk estimate):
- 30.0 k / 10.0 k 0.1 % resistors give 10.00 V nominal, and about 9.968-10.031 V at 25 °C.
- Over a 45 K swing it falls to about 9.95 V.
- Guaranteeing 10.0 V needs calibration with a code clamp or a ratio-matched network.
- The zero end sits 5-25 mV above ground plus 4 x the DAC zero-code error, so the physical zero clamp is still required.

Where:
- `tools/hardware_build_design.py`: `dac` role (line 192) and `spindle_analog.output_swing_budget`. State the register write explicitly.
- `docs/ELECTRICAL_DESIGN.md`: spindle row.
- The future DAC initialisation in whichever gateware or driver owns the isolated analog link: none exists yet.

### E-32. TPS62160 accuracy and ramp versus the ledger (partly resolved-by-Codex) [R1-065]

TPS62160 initial accuracy is ±3 % in PWM and -3.5 %/+4 % in power-save mode:
- At 1.2 V this gives 1.164-1.236 V, outside the CORE_1V2 window of 1.17-1.23 V.
- At 3.3 V, power-save mode can reach 3.18 V, below the IO_3V3 minimum of 3.2 V.
- Its fixed soft-start of about 25 V/ms exceeds the T20 maximum ramp of 10 V/ms (T20 DS Table 71/87).

Resolved at block level by Codex: `hardware/logic_power/design-envelope.json` selects TPS62901RPJR (`replaces_study_candidate: TPS62160DSGR`) with forced PWM and SS/TR.

Still open: the ledger `buck_fpga_core`/`buck_io`/`buck_esp` rows and the rail `source` strings still name TPS62160 (generator lines 79-81 and 196). Integrate the TPS62901 choice. The loaded ramp and startup of the TPS62901 design are recorded by Codex as not physically qualified.

### E-33. Core input path limits the usable 5 V capacity (partly resolved-by-Codex) [R1-063, R1-065]

At an 18 V input, 85 % efficiency, a 2 A core entry and a 0.06 A analog reservation, CORE_5V can deliver at most about 5.94 A. The r0.1 core eFuse (RILIM 8.20 k) limits the input to 1.97-2.43 A. A 7 A-or-larger converter would therefore give no usable 7 A until the core source, wiring and eFuse are revised.

Codex's current files:
- `hardware/power_entry/requirements.json` r0.2 changes core R4 to 7.50 k and sets `core_qualified_source_and_wiring_capacity_target_a: 3`.
- `hardware/core_converter/requirements.json` carries `proposed_core_source_wiring_capacity_a: 3` and uses LM70660RRXR, rated 6 A.

Both files say the proposal is not yet accepted. The 7.50 k ILIM transfer is a 10 % screening assumption, not a TI guarantee. The 19 V minimum does not meet the ledger's 18-30 V requirement. No PSU or cable is selected.

The ledger still has CORE_24V at `capacity_a: 2` and CORE_5V at 6 A (lines 77-78).

A verified 8 A alternative, ADI LT8645SEV#PBF, is recorded in part-selections group 3 `not_selected`. It was not proposed over Codex's choice. The user or hardware owner decides the core PSU rating.

### E-34. Field fuse rating implies at least 10 A-class field wiring and terminals (open)

The field fuse must be at least 7.5 A (4.36 A / 0.75 = 5.81 A, next rating 7.5 A). Field wiring, the JPOWER FIELD_24V positions and their mating plug therefore need to withstand at least 10 A-class currents, more than the "6 A" capacity wording.

With a 6 A current-limited field PSU, or a 2-3 A core PSU, neither physical fuse will clear. Each fuse is only a backup against high-prospective-current sources. The shorted-eFuse or shorted-TVS case depends on the PSU.

Current files: `hardware/power_entry/requirements.json` sets `field_qualified_source_and_wiring_capacity_target_a: 6`, and its own blockers say the fuse MPN, holder, DC interrupt rating, time-current/I²t and source prospective fault current are unknown. The ledger FIELD_24V source text says 6 A (line 82).

Candidates in part-selections group 3:
- 099707.5WXN (7.5 A MINI, 58 VDC, 1000 A interrupting) for the field fuse;
- 0997003.WXN (3 A) for the core fuse;
- Keystone 3568 holder. Its confidence is "likely", not "verified".

The fuse time-current data were assumed ISO 8820-style because the Littelfuse PDF could not be fetched.

Where: `tools/hardware_build_power_entry.py` (fuse, holder, wiring rating), `tools/hardware_build_design.py` (FIELD_24V rail text, `physical_entry_fuse_field` line 245, JPOWER connector rating) and `docs/POWER_PROTECTION.md`.

### E-35. FIELD_5V can exceed the TPS4H160 recommended logic-pin maximum (open)

FIELD_5V is specified at 4.85-5.15 V, in the ledger and in `hardware/field_power/design.json` `output_target_v`. The TPS4H160 logic, FAULT and THER pins are recommended at 5 V maximum (7 V absolute). The part-selections pull-ups (20 k for DIAG_EN and THER, 10 k for FAULT) do not change the fact that the FAULT pull-up can reach 5.15 V.

Options, not applied:
- tighten the FIELD_5V upper bound for this load;
- pull the TPS4H160 pins up through a divider or from a lower rail;
- confirm from the datasheet that 5.15 V on these pins is inside recommended operation.

Where: `tools/hardware_build_field_power.py` and the future field-output block. Also the `do_diag_support` row in `tools/hardware_build_design.py`.

### E-36. No isolated channels left for TPS4H160 diagnostics, and an overvoltage gap (open)

14 of the 16 isolated command channels are used. None is left for DIAG_EN, SEL1/SEL2 or per-channel current-sense readback. The part-selections network therefore straps DIAG_EN on and routes CS only to a local test point. The FPGA sees only the aggregated FAULT through `iso_fault`.

Decide whether that is acceptable, or add an isolator (`logic_links` `output_commands`/`field_faults` and the isolator counts in `tools/hardware_build_design.py`).

Separately, Codex recorded in `research/FIELD_OUTPUT_PROTECTION_GAP.md` that:
- TPS4H160-Q1 is limited to 48 V for transients shorter than 400 ms;
- the entry SMCJ30CA clamps at 48.4 V at its reference pulse;
- so the current entry protection does not protect the driver.

That note may change the output stage itself. Resolve it before adopting any `do_current_set`/`do_diag_support` MPNs.

Current-limit resistors from part-selections group 3:
- 2.67 k for the 0.5 A general-output banks (Eq. 4: 0.8 x 2500 / I);
- 7.87 k for the drive-enable banks (0.254 A).

### E-37. T20 F256 active-SPI x1 has no multi-image support (open, user decision)

The ledger reserves "activeconfigurationSPI4plusstraps" (generator line 280). T20 datasheet v6.0, Table 67 note 13: F256 does not support multi-image in x1 mode. A golden image or safe remote update would need x2/x4 wiring or the AN010 internal reconfiguration flow. The W25Q32JVSSIQ candidate supports dual and quad output.

This is a product decision about field firmware update. Record it before the FPGA pin map is frozen in Efinity.

### E-38. T20 input limits require Ioff dual-supply buffers on the host and ESP links (open)

T20 VIN maximum is VCCIO + 0.3 V, and AN006 forbids driving Trion I/Os before VCCIO is up. A single-rail 74LVC125 could back-power an unpowered SBC through MISO.

Part-selections group 2 therefore uses SN74AVC4T774PWR (dual-supply, Ioff on both ports):
- for `host_spi_buffer`, with CRCW060333R0FKEA source-damping resistors;
- for `esp_uart_buffer`, with VCCA on IO_3V3 and VCCB on ESP_3V3.

This deliberately substitutes for the 74LVC/LV families the request named as examples.

Codex's `hardware/power_sequence` uses SN74LVC1G17 (Ioff) only for the FPGA and ESP reset outputs. No host SPI or UART buffer block exists.

Where: `host_spi_buffer`/`esp_uart_buffer` rows (generator lines 236-237) and the future host-interface block. The pinout depends on the compute decision (E-10).

### E-39. Supervisor threshold edge cases (resolved-by-Codex, with a residual Codex already records)

The audit's TPS386000 design had two problems:
- a CORE_1V2 UV low edge at 1.149 V, 0.7 mV below the T20 1.15 V minimum;
- an OV high edge at 1.256 V, 6 mV above the T20 1.25 V recommended maximum.

It also had uncontrolled power-down order.

Codex rejected TPS386000 for its ±1 % guaranteed threshold and up to 10 mV hysteresis (`research/power-sequence/SOURCES.md`). Codex instead drew `hardware/power_sequence` with four LTC2962HUD#TRPBF window supervisors and 0.01 %, 5 ppm PLT dividers.

Its `validation.json` gives these CORE_1V2 static corners, which are inside both the ledger window (1.17-1.23 V) and the T20 limits:
- UV: 1.1708-1.1842 V;
- OV: 1.2155-1.2295 V.

The TPS386000 part-selections record is therefore superseded.

Residual, recorded by Codex itself:
- The CORE_1V2 static margins are below 1 mV.
- The 400 ppm aging-sensitivity case fails (`static_acceptance_and_detection: false`).
- Shutdown order, brownout slew, arbitrary partial power and physical qualification are listed as unproven.

The ledger `power_supervisor` row is still `required_unselected` (generator line 232).

### E-40. Field eFuse current-limit margin (open, already flagged by Codex)

The field eFuse ILIM screening low of 4.42 A against a 4.36 A normal load leaves about 1.4 % margin (`hardware/power_entry/requirements.json`, RILIM 3.65 k). Codex already lists the interpolated ILIM limits as screening assumptions.

---

## D. What this handoff does not claim

- No MPN in [`part-selections.json`](part-selections.json) qualifies a circuit. SI, surge and EMC, thermal, layout, ERC/DRC and bench measurement are all still required.
- No prices or stock were recorded. PCBWay turnkey sourcing and quotation remain the cost authority.
- Closing every item above would still leave the board **not ready for PCBWay**. See the PCBWay section of [AUDIT_REPORT.md](AUDIT_REPORT.md) and `manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md`.
