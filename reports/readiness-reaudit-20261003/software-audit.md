# Software, firmware and RTL readiness re-audit

Audit completed 4 October 2026, 00:00–00:01 UTC−04. The folder retains the parent audit's 3 October identifier. This is a read-only engineering re-audit while routing proceeds separately. No CAD, hardware source, production source, existing evidence, configuration, or external IS-1 archive was edited. The only persistent outputs from this work are new files in this audit folder. Tests use explicit source fixtures or temporary copies; no physical interface was opened.

**Result: the existing software evidence is useful, but neither a complete eight-/twelve-motor IS-2 machine nor production setup/commissioning is ready.** The latest compiled C/RTL candidates deliberately refuse incomplete qualification. Do not weaken those refusals to make a setup assistant appear successful. The public historical HAL is six-motor/two-encoder simulation, and the current diagnostic motherboard wrapper retains that scope. Twelve-channel component/stateful RTL proofs are separate evidence.

The most significant new audit observations are (1) a verified newer report-local FPGA optimization passes the coarse resource screen, contrary to current umbrella summaries, but leaves only **251 of 19,728 cells (1.272%)** before missing functions; (2) the historical RTL evidence checker now returns a source-inventory failure for one added characterization bench; and (3) several current status paragraphs still contain superseded or stale instructions. None of these observations establishes vendor fit, a target timing result, or physical readiness.

## Fresh checks and boundaries

The reproducible source-preserving runner is `software_audit_checks.py`; raw results, commands, exit codes and log hashes are in `software-checks.json`. `software-source-snapshot.json` binds **619 scoped files** before and after the run: all unchanged. The snapshot deliberately excludes build trees, retained evidence/results and caches; it is not a whole-workspace/CAD integrity claim.

| Fresh action | Result | What it establishes |
| --- | --- | --- |
| `tests/test_cnc3_rtl.py` | 6 tests PASS | Frozen-input hashes, read-only generated-source reproduction, temporary-copy negative controls, correspondence to retained compiler/family receipts |
| `tests/test_motherboard_iol1_readonly.py` | 19 tests PASS | Actual source/pin-map consistency and source mutation negatives; these tests inspect source strings and do **not** execute target MMIO/DMA/IRQ instructions |
| CNC1 runtime manifest `--check` | PASS | Retained 28 September historical source/evidence identities and summary consistency; no new LinuxCNC run |
| CNC1 spidev manifest `--check` | PASS | Retained mocked-syscall C test/build/header evidence remains consistent; no physical SPI transfer |
| Historical RTL manifest `--check` | FAIL | One newly inventoried bench is absent from the historical manifest: `tests/tb_stepgen12_characterization.sv`; no old RTL hash change was reported |
| Historical synthesis and post-map `--check` | Both PASS | Retained Efinix-family mapping and mapped-circuit evidence is consistent; no synthesis, vendor implementation or HDL simulation rerun |
| IS-2 profile-r02, optimized motion, optimized record bundles | 44 + 45 + 101 hashes PASS | Those immutable candidate bundles remain byte-consistent; no replay rerun |
| Handoff/addendum referenced evidence | 18 + 3 + 5 references PASS | Linked retained receipts/reports still match their recorded digests |
| ESP service manifest source map | 14/14 match | The specific historical warning about one changed source no longer describes the present source map; no new ESP build or flash |

No target compilation, HDL simulation, FPGA synthesis, vendor device fit/static timing, circuit ERC, PCB DRC, electrical measurement or mechanical test was run in this audit. The source-negative tests are not additional machine cases. They must not be added to the older 1,895-host/238-native totals as though they were disjoint tests.

## Prioritized findings and closure gates

### SW-01 — P1: There is no complete IS-2 CNC3/HAL runtime to commission

The executable HAL still links only to actual RTL **simulation**, has six position/scale arrays and two encoder arrays, and creates `cnc1_sim`. The motherboard diagnostic wrapper exposes twelve output positions but ties the upper six STEP/DIR outputs low and enables inactive. This is correct historical/diagnostic behavior, not twelve-axis support. Separately, the report-local IS-2 profile explicitly sets `IS2_PROFILE_COMPLETE=0`, masks qualification with it and keeps the C driver retrying a bounded discovery before refusing configuration. A fitted count or static inventory cannot substitute for that missing qualification.

Evidence: `cnc1/src/hal_cnc1.c:1`, `:23`, `:26`, `:27`, `:101`, `:152`; `gateware/motherboard_iol1_target_bringup/cnc_motherboard_iol1_target_bringup.v:27`, `:41`, `:43`; `reports/cnc3-is2-profile-20261002/profile-candidate-r02/rtl/cnc3_motion_spi.v:37`, `:72`, `:89`; `reports/cnc3-is2-profile-20261002/profile-candidate-r02/driver/cnc3.c:185`; `tools/validate_controller.py:634`.

Close with an explicitly adopted, versioned IS-2 board-region/provider contract and one actual CNC3 C/HAL-to-RTL integration. Exercise all twelve fitted motors (and an eight-active configuration), all four base encoders, individual enable/alarm, atomic commands, valid/age data, fault/recovery and retained settings. Qualify physical providers before installed/qualified capability is asserted. Keep the frozen 96-byte command/176-byte feedback frames and avoid fictitious MX4/card presence. Do not “fix” the constant-false completion gate by tying it true.

### SW-02 — P1: Ordinary field output, analog and trusted identity/provisioning paths remain incomplete

The target diagnostic firmware holds authority GPIOs low. Its analog path correctly marks reset-held converters unavailable; it does not acquire live AI/DAC data. The diagnostic FPGA wrapper drives general output, PWM, process and permission requests low. Newer report-local record acquisition verifies actual C/RTL wire transactions, CRC/shape and configuration echoes, but expressly does not establish factory signatures, hardware UID authentication, ACTIVE permission or actual flash/IRQ execution. CRC detects corruption; it does not establish the origin or calibration authority of a machine record.

Evidence: `firmware/motherboard_iol1_readonly/target.c:35`, `:40`, `:127`, `:130`; `gateware/motherboard_iol1_target_bringup/cnc_motherboard_iol1_target_bringup.v:46`; `firmware/motherboard_iol1_readonly/README.md:3`, `:9`, `:11`, `:15`; `reports/cnc3-iol1-integrated-records-20261002/arithmetic-sharing-handoff-r01/receipt.json:162`; `reports/cnc3-iol1-integrated-records-20261002/prefix-record-candidate-r01/replay_record_acquisition.py:26`.

Close with the actual production local-controller application and IS-2 identity/calibration/provisioning policy: frame/class/port/epoch/sequence/freshness validation before output changes or watchdog refresh; real permission/rearm/readback behavior; correct unavailable analog/current observations; interrupted-write recovery; explicit board replacement and affected recommissioning. Preserve current 0.5 A/channel and 2 A/four-output-group limits until the electrical design and physical qualification jointly support a revision. Assistant-generated values cannot confer a circuit rating or a verified calibration.

### SW-03 — P1: FPGA fit remains a release blocker, with very little demonstrated capacity margin

The newer optimized report-local composition maps **16,779 LUT4 + 2,698 adders = 19,477** against the cited 19,728-LE device count. The coarse screen passes, with 251 cells spare. It omits the dormant IS-2 CAP3 mux and missing factory/provider/output/event functions; the mapping is not the complete controller. There is no accepted Efinity placement/routing/static-timing/bitstream result. A passing lower-bound count cannot prove the missing logic will fit or meet timing.

Evidence: `reports/cnc3-iol1-integrated-records-20261002/arithmetic-sharing-handoff-r01/receipt.json:92`, `:99`, `:103`, `:163`, `:169`; `reports/cnc3-iol1-integrated-records-20261002/arithmetic-sharing-peer-addendum-r01/receipt.json:18`. All candidate bundle and handoff evidence hashes checked above match.

Close the **complete** composed resource budget before implying the T20 is sufficient. Run exact target/package/pin-bank implementation and clock/I/O constraints in the vendor tools, inspect timing and CDC/reset behavior, and retain synthesis-to-bitstream provenance. Continue optimization or a reviewed resource decision against all mandatory functions; do not drop fitted channels or required I/O to make a partial fit pass. The optimized candidate has not been adopted into the public bench/source.

### SW-04 — P1: Neither 2 MHz/channel nor loaded real-time operation nor whole-controller 20 ms inhibit is established

The production-default source retains `MAX_RATE=0x01000000` and 100-tick timing values; at the assumed 50 MHz clock that is the historical 195,312.5 pulses/s DDS limit. The optimized stateful candidate explicitly preserves the same protocol limit. The historical HAL uses a simulation-specific 500 ms wall-age override. The separate spidev backend remains synchronous with no enforced ioctl deadline. These are disclosed engineering boundaries, not safe settings to expose as measured machine capability.

Evidence: `gateware/rtl/cnc_endpoint.v:5`; `cnc1/src/hal_cnc1.c:170`; `cnc1/src/spidev_transport.h:8`; `cnc1/src/spidev_transport.c:142`; `reports/cnc3-iol1-integrated-records-20261002/arithmetic-sharing-handoff-r01/receipt.json:160`; `reports/pre-hardware-characterization-20261002/characterization-register-r06/requirements-and-coverage.json:197`.

Close with actual target LinuxCNC/CNC3 transport under simultaneous UI/network/storage/ESP/field-I/O load, a 1 ms servo deadline and separate 700 µs completion-margin result, drive-specific pulse/direction limits, and target-plus-physical fault timing. Independent watchdog/permission circuits and all motor/DO/PWM/process/AO endpoints must meet the retained 20 ms fault-to-inhibit contract, including clock stall. A simulator clock timer, target compilation or MCU IWDG arithmetic cannot establish whole-controller physical inhibit timing. Preserve the experimental 2 MHz sweeps as component evidence only.

### SW-05 — P2: Historical RTL manifest verification is no longer clean against the present inventory

The fresh command `python -B gateware/tools/record_evidence.py --check` returns exit 1 and names only `unrecorded tests/tb_stepgen12_characterization.sv`. The checker inventories every `tests/*` file, so adding the separate twelve-generator characterization bench changes the source set even though old RTL was not reported changed. Historical 252+27 results remain historical evidence; they are not a clean current-manifest result.

Evidence: `software-baseline-rtl-manifest.log:1`; `gateware/tools/record_evidence.py:54`, `:66`; `gateware/tests/tb_stepgen12_characterization.sv:1`.

Close by defining the intended baseline-versus-characterization evidence scope explicitly and regenerating a *new* manifest only after the relevant actual regression, while preserving old logs/manifests. Do not merely add the new hash to imply the older run tested it. The existing manifest was not edited during this audit.

### SW-06 — P2: Current status prose has conflicting/stale statements that should not feed setup reasoning

The authority documents' new summary and old body disagree. Specific corrections required:

- `reports/ENGINEERING_STATUS.md:7` and `reports/motherboard-readiness-20261002/ROOT104/README.md:26` say the staged composition exceeds the coarse screen. The newer verified optimization above passes the partial screen, while full fit remains open. Its addendum already explains an inherited stale “capacity failure” sentence in the frozen replay report.
- `reports/ENGINEERING_STATUS.md:68` calls the one-board direction a pending clarification; `:83` repeats the old eight-plus-four plug-in motor architecture. Those are superseded by the explicit 30 September single motherboard/all-twelve-fitted decision, even though the broad section is labelled historical. They must not become current setup recommendations.
- `reports/ENGINEERING_STATUS.md:29` says one ESP source hash differs. This audit verifies all 14 current source hashes match its retained manifest. That does not establish a new build.
- `reports/ENGINEERING_STATUS.md:127` says the RTL recorder has no read-only mode. `gateware/tools/record_evidence.py:5` and `:23` implement `--check`, and this audit used it without writes. Running the recorder without that flag does write evidence and must still follow an actual regression.

Close with an explicit current readiness/capability index that identifies exact adopted versus report-local candidates and evidence classes. Preserve old snapshots; annotate or replace current summary assertions coherently rather than silently rewriting historical receipts. Setup assistants should consume that typed current index and authoritative limits, not merge every paragraph found in the repository into one supposed machine.

### SW-07 — P1 product acceptance gate: No complete operator/machine setup profile is validated

The latest characterization register has nine machine profiles, all `NOT_RUN`, and `full_machine_profiles_completed=0`. Its setup requirement covers identification, offline provisioning, verified hardware profiles, wiring, homing/jog/G-code, injected faults and recovery through the shared UI/CLI. Existing ideal mechanics, source checks and historical LinuxCNC simulation do not close those complete workflows.

Evidence: `reports/pre-hardware-characterization-20261002/characterization-register-r06/requirements-and-coverage.json:246`, `:378`, `:475`; `tools/validate_controller.py:649`.

For the requested expert setup assistant, first select a bounded supported machine/profile and make its entire disconnected setup and recovery workflow reproducible before physical commissioning. Each answer that proposes a setting needs an exact compatible hardware/drive/profile basis, units and validated limits. Missing identity, unknown wiring or absent measurements must remain named missing evidence; further fluent discussion cannot resolve them. A failed or unavailable qualification is a deterministic backend state, not something the model can override. The parent audit defines the broader API budget and shared-service acceptance work separately.

## Retained evidence, accurately labelled

| Layer | Current usable evidence | Still outside that evidence |
| --- | --- | --- |
| Historical six/two | Compiled CNC1 driver and actual LinuxCNC/RTL simulation, persistence/recovery; retained manifests verify except expanded RTL test inventory noted above | Eight/twelve machine runtime, physical SPI, real-time target deadlines |
| Twelve/four component and stateful work | Actual twelve pulse generators/four encoder algorithms, stateful serial fault/mutation/ideal-mechanics proofs; r08 retains 2,048 seeded SPI fault trials and 18 reset/fault scenarios | A complete CNC3 HAL machine and physical plant |
| IS-2 profile-r02 | Actual SPI capability page and original/derivative C driver checks, four compiled refusal mutation controls; static supported inventory 12 motors/4 encoders | Qualified installed count remains zero; no CONFIGURE/ARM authority, full provider qualification or HAL |
| Local STM32 firmware | Retained four real ARM builds, protocol C tests and C/HDL VPI diagnostics | VPI does not execute actual DMA/ISR/MMIO/sensor hardware; no target flashed or measured ISR deadline |
| Optimized composed FPGA | Eleven retained motion stages plus four record stages and formal/mutation evidence; partial coarse mapping screen passes | Missing blocks, vendor fit/static timing/bitstream, actual hardware |
| ESP helper | Diagnostic-only source and retained target builds; all 14 sources match | Motion permission, live qualified accessory automation, flashed/physical evidence |
| Umbrella r08 | 25 PASS, 9 BLOCKED, 1 physical NOT_RUN, no recorded FAIL; 1,895 host and 238 native cases were passed in that retained run | Does not include adoption of the newer optimized candidate or establish completed machine/readiness gates |

The root audit should retain **manufacturing readiness=false**, **complete-machine readiness=false**, and **automatic commissioned setup readiness=false**. Development can proceed on source-backed profiles, deterministic validation, preview/diff and inhibited recovery while routing proceeds independently.
