# Workspace audit, 28 September 2026

This is the record of a multi-agent audit-and-fix pass over the CNC controller engineering workspace. It covers what was checked, what was changed, what evidence was regenerated, what is still open, and how far the repository is from a PCBWay turnkey submission.

Companion files in this folder:

- [`findings-ledger.json`](findings-ledger.json): one entry per confirmed finding (154), with outcome and fix location, plus every rejected candidate with a one-line reason.
- [`ELECTRICAL_HANDOFF.md`](ELECTRICAL_HANDOFF.md): every open electrical and hardware item, re-checked against the live hardware files, with the generator or file where each change belongs.
- [`part-selections.json`](part-selections.json): verified candidate MPNs from desk datasheet research. These are not integrated into the ledger.
- [`python-tests.txt`](python-tests.txt): raw output of the final full Python run.

**Bottom line:** the fixes improved the software, gateware and evidence records. The hardware is still a set of partial circuit blocks. **The repository is not ready for PCBWay manufacture**, and nothing in this audit changes that.

## 1. Scope and method

**Tree.** The audit covered `C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller` on 2026-09-28: gateware, the CNC1 LinuxCNC driver and runtime services, the configuration service and CLI, the LinuxCNC backend, the ESP32-S3 helper firmware, the electrical ledger and KiCad blocks, the release gate, research generators and the status documents.

The six-joint/two-encoder baseline was kept separate from the eight-motor/four-encoder candidate throughout. All hardware evidence discussed here is baseline evidence.

**Stages.**

1. **Round-1 finders.** Fifteen finder dimensions were audited: rtl, cnc1, config, backend, esp, electrical, docs-root, docs-reports, tools, tests, manufacturing, safety, security-hygiene, evidence-integrity and expanded-and-catalog. With the critic below, that makes the sixteen-part plan. Each finder recorded its own coverage and what it did not read (`coverage` in the audit record).
2. **Adversarial verification with different lenses.** Every round-1 candidate went to three independent verifiers: correctness (is the evidence in the live file?), materiality (does it matter?) and fix (is the proposed fix right and within the project rules?). A candidate was confirmed only if the verifiers did not refute it. Verifiers could correct the claim, the severity and the fix.
3. **Critic round.** A critic compared coverage with the tree. It found whole subsystems that no finder had read: the persistent runtime, the encoder receiver block, the synthesis/post-map flow, the root-verification package, current manifest drift, `.gitignore` gaps, cross-document numbers and the two LinuxCNC profiles. It proposed seven round-2 scopes.
4. **Round 2 and re-verification.** The original round-2 verifiers rejected all 25 round-2 candidates. A second, independent verification pass reversed 15 of those rejections (`R2-xx` in the ledger). The other three round-2 scopes produced no candidates in the original round 2: hardware blocks and validator refresh, root verification and manifest state, and cross-document numbers. They were run again as follow-up finders and produced 50 candidates, of which 42 were real (`FU-HW`, `FU-RV`, `FU-CD`).
5. **Fixes by seven owner groups.** Each group owned a disjoint set of files: gateware, cnc1, config, backend, esp, manufacturing and hygiene. Each group had an independent reviewer and then a repair pass. The reviewers raised 22 issues across all seven groups. The repair passes fixed 20 and deferred 2 as cross-owner follow-ups; both were closed in the final sync (see section 3.9). An integration check then ran the full suite and recomputed every current manifest hash against the tree.
6. **Final sync.** Four follow-up agents handled the cross-owner follow-ups:
   - **cnc1:** re-recorded CNC1 evidence, archiving the previous record in `cnc1/evidence/before-final-sync-2026-09-28`.
   - **config:** the servo-period bound in the runtime service and the host adapter mirror of the persistence gate.
   - **hygiene:** `.gitignore`, the expanded-target citation and the research-generator tests.
   - **docs-sync:** status documents and the raw 579-test run.

   This record was written last. Only the docs-sync agent's report was available to it. The other outcomes were confirmed by re-reading the live files (`verified_by` in the ledger).
7. **Repair review.** An independent reviewer checked the final-sync state and raised seven issues (`review-1` to `review-7` in the ledger). All seven were confirmed against the live files. Five were fixed in owned files. The other two (`review-5`, `review-6`) needed files outside the final-sync owned set and were closed afterwards by the coordinating session. The gateware recorder gained a read-only `--check`, and the RTL regression and the ESP evidence were re-recorded with their previous records archived.

**Electrical findings.** The 23 electrical findings from round 1 were not assigned to a fix group, because Codex was editing `hardware/` and `tools/hardware_*` at the same time. They were re-checked for this record against the current files and are either marked as already fixed or handed off.

**Evidence classes.** This record distinguishes source inspection, host tests, target compilation, HDL simulation, FPGA family synthesis, circuit ERC, board DRC and physical measurement. No board DRC or physical measurement exists anywhere in the repository. The only FPGA synthesis evidence is Yosys Efinix-family mapping; there is no Efinity place-and-route, timing or bitstream.

## 2. Headline counts

| Stage | Candidates | Confirmed (real) | Rejected |
|---|---|---|---|
| Round 1 | 123 | 90 | 33 |
| Round 2 (original verdicts) | 25 | 0 | 25 |
| Round 2 (re-verification) | 25 | 15 (2 are duplicates) | 10 |
| Follow-up scopes | 50 | 42 (2 already resolved when verified) | 8 |
| Repair review | 7 | 7 | 0 |

Verification lowered most severities. Of the 154 ledger entries:

- **Reported by finders and the repair reviewer:** 18 high, 72 medium, 64 low.
- **After verification:** 1 high, 36 medium, 117 low.

The one high-severity entry after verification is FU-CD-00: status documents presented superseded CNC1 runs as evidence for the current driver. It is fixed.

Outcomes of the 154 ledger entries:

| Outcome | Round 1 | Round 2 | Follow-up | Repair review | Total |
|---|---|---|---|---|---|
| fixed | 32 | 14 | 17 | 7 | 70 |
| already_fixed_during_audit | 41 | 1 | 3 | 0 | 45 |
| open_handoff | 11 | 0 | 17 | 0 | 28 |
| deferred | 6 | 0 | 5 | 0 | 11 |
| not_a_defect | 0 | 0 | 0 | 0 | 0 |

FU-CD-06 (the `PROJECT_BRIEFING.md` sentence that said the FPGA/ESP source hashes still match) was first recorded as already fixed. The repair reviewer showed the sentence was false again after the `controller_lab/service_health.py` docstring change (`review-3`). The sentence was corrected, and FU-CD-06 is now counted as fixed.

- **Already fixed during the audit:** the tree moved while the audit ran. Codex rewrote the ledger and validator at 08:48Z, and other owners corrected documents between the finder and fix stages. These entries were re-verified, not taken on trust.
- **Open handoffs:** the 28 entries correspond to 24 distinct problems, because four follow-up entries restate round-1 items. Of the 24:
  - 22 belong to the hardware owner; R1-063 also needs a user PSU decision.
  - R1-072 needs the user's first machine profile.
  - FU-RV-01 (CNC1 build source identity) belongs to the cnc1 owner.

## 3. What was fixed, by subsystem

### 3.1 Gateware (`gateware/`)

- **Inhibit clock-domain crossing (R1-000).**
  - *The problem:* the external inhibit pin is asynchronous to the 50 MHz core clock. The raw pin, and two flip-flops it clears asynchronously, fed synchronous logic directly: the six step generators' enable, the fault/arm block and the status snapshot. An inhibit edge that lands inside a clock's setup/hold window could therefore be captured differently by different flip-flops. The worst case is a step counter that is neither `n` nor `n±1`, and the driver uses that counter as position feedback.
  - *The fix:* the asynchronous capture is kept, so inhibit still takes effect immediately. Every clocked consumer now reads the capture only through two-flip-flop synchronizers (`inhibit_ok_ff`, `authorized_ff`).
  - *Check:* a Yosys structural check (`gateware/synthesis/cdc_check.ys`) confirms that no clocked cone reads the raw pin. It is recorded as `inhibit_cdc_structural_check` in the synthesis manifest.
  - *Evidence class:* HDL simulation plus structural synthesis. It is not a timing or metastability measurement.
- **MISO turnaround margin (R1-001).** MISO used to change 2-3 core clocks after the host's falling SCLK edge, because that edge passes through a synchronizer first. At the documented maximum of core/8, that left the host sampling close to the change. MISO now updates on the delayed rising edge instead. The nominal margin is derived in `gateware/PROTOCOL.md:27`. It is source arithmetic and has not been measured on a board.
- **Progress watchdog output (R1-059).** The RTL now has a `progress_wdi` output. It toggles only on an accepted motion frame (opcode 3: armed, fault-free, authorized, sequence good), not on ARM. That gives an external watchdog a signal tied to useful progress rather than to a free-running clock. It is not yet routed to any board circuit, and the ledger text still says it is absent (handoff E-13).
- **Plain Verilog compatibility (R1-006).** The `.v` sources used SystemVerilog size casts and loop-scoped declarations, so they failed `iverilog -g2005`. They now elaborate in Verilog-2005 mode, and `run_tests.sh` checks this.
- **Rate bound documented (R1-003).** With the 100/100-tick pulse/space defaults, the minimum STEP period is 201 ticks. No rate cap above `0x01460CBC` (248,756 steps/s) is fault-free, and a 250 ksteps/s increment latches a timing fault in the testbench. Raising the 195,312.5 steps/s cap alone therefore cannot reach 250 ksteps/s. No limit was changed (R1-066 is deferred for a decision).
- **Capability page on a bad frame (R1-004).** A rejected frame now clears the pending capability page.
- **Recorders and line endings (R2-00, R1-077).** All synthesis and validation recorders write LF, and `gateware/.gitattributes` pins LF.
- **Post-map summary (R2-04, R2-02).** The post-map summary is re-derived by `checked_summary()`. The report now says the 179 post-map assertions run a frozen pre-persistence driver: about 30 are host-only, inhibit is held deasserted, and the fault/ready/progress pins are not observed.

### 3.2 CNC1 driver and LinuxCNC runtime (`cnc1/`)

- **Persistence gate (R1-011, R2-06).** The compiled driver used to allow stage (op 4) → acknowledge (op 5) → release (op 3) → ARM without any scale commit. It now refuses acknowledgement, release and ARM until a stopped op-2 commit has advanced the configuration revision past the staged base.
  - The documents state exactly what this guarantees: the revision has advanced. It does not guarantee that the values differ from the defaults. A compiled test case shows that an explicit commit of the defaults is accepted.
  - The host adapter double in `tests/test_persistent_runtime.py` now mirrors the rule (`COMPILED_GUARD_REJECTED`).
- **Watchdog-derived servo period (R2-09).** The driver accepted any servo period up to a fixed 10 ms, although the RTL watchdog is 5 ms. It now computes `watchdog_ns` from the discovered `watchdog_ticks` and `core_hz` and refuses any period above half of it (2.5 ms for the default RTL). The runtime service applies the same bound (`servo_period_bound_ns` in `controller_config/runtime.py`), and 10 ms remains only as an outer ceiling.
- **Documentation of the stopped transaction and result codes (R1-009, R1-010).**
- **Evidence regeneration (R1-074, R2-14, R2-16, R1-050).**
  - The launchers start from a clean work copy.
  - Earlier manifests were archived byte-for-byte before each re-record: `before-audit-fixes-2026-09-28`, `before-audit-repair-2026-09-28` and `before-final-sync-2026-09-28`.
  - A recorder for the spidev evidence was added, and the spidev tests were rerun against the current header.

### 3.3 Configuration service and runtime (`controller_config/`)

- **Audit trail and diffs.**
  - A module replacement now writes a same-revision `replace_module` audit entry through an internal, lock-held helper; the public entry point was removed after review (R1-014).
  - A no-op apply returns the same key set as a changing apply (R1-016).
  - A number stored as 5 vs 5.0 is now reported as a change, consistent with the digests (R1-017).
- **Windows store replacement (R1-020).** `os.replace` is retried for about 0.38 s on `PermissionError`, for example when a reader or OneDrive holds the file. The lock is held throughout, and the call fails closed as `IO_ERROR`.
- **Pulse-rate margin (R2-15).** A scale is accepted only with a 2-count margin below the discovered rate cap. The servo period is carried outside the persisted capability identity, so existing saved authorities stay valid.

### 3.4 LinuxCNC backend (`controller_backend/`)

- **Rootfs extraction filter (R1-075).** The Debian rootfs fetcher runs as root and extracts container layers. Its tar filter now:
  - requires every non-symlink member's resolved path to stay inside the destination;
  - refuses device nodes;
  - closes a `p -> .` then `p/..` symlink bypass that the reviewer found in the first fix.

  The check is recorded in `controller_backend/evidence/rootfs-layer-filter-check.json`.
- **Profile check (R1-021).** The profile-identity check was comparing a path with itself. It now compares the controller-reported INI with the expected profile.
- **Adapter proof (R2-13).** The isolated LinuxCNC adapter proof was rerun: run `bac564b6`, 12 checks, 3,118 status samples.
- **Commands (R1-081).** The documentation now gives repository-relative `wsl` commands first.

### 3.5 ESP32-S3 helper (`firmware/esp32_service/`)

- **Evidence retention (R1-026).**
  - *The problem:* the images and logs were kept only in the git-ignored `.build/` folder. The retained copies came from an older build whose source hashes no longer matched.
  - *The fix:* a recorder now does a clean build of both variants. It refuses stale images and retains the images, logs, effective sdkconfig and a manifest in `evidence/`. The pre-fix images are archived byte-exact.
  - *What the record says:* the build is not reproducible by design, because an app timestamp is embedded, and no device was flashed.
- **Freshness deadlines (R1-027).** The deadlines are named constants (1000 ms link, 500 ms progress), and the required 4-10 Hz host cadence is documented. Values are unchanged.
- **Corruption test (R1-030).** The corruption test now asserts that no accepted state changes on a rejected frame.

### 3.6 Release gate (`manufacturing/`, `tools/check_release.py`)

- **Distinct evidence (R1-052).** Evidence must be distinct per artifact id, by path and by bytes. One placeholder file can no longer satisfy several ids.
- **Structured PCBWay quote record (R1-070).** The record lists 11 prerequisites and the study quantities 1/10/100/1,000. The checker rejects:
  - blank or non-text identity fields;
  - a `quoted_at` that is not ISO 8601;
  - figures that do not match the quoted quantities.
- **Link prototype measurement (R1-071).** A new release item, `link_prototype_measurement`, requires a physical measurement on an engineering host and an FPGA evaluation board. Host tests or simulation cannot satisfy it.
- **BOM status (R1-057).** The BOM status records that a designator-level export with PCBWay columns does not exist yet.
- **Checklist.** The new `manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md` lists what PCBWay asks for and the state of each item in this repository.

### 3.7 Hygiene, research generators and repository protection

- **Line endings (R2-01).** The root `.gitattributes` now defaults to byte-exact (`* -text`) and pins LF for execution-critical sources. Hashed evidence therefore keeps its bytes on any clone.
- **Ignore rules (R1-078, FU-RV-13).**
  - Evidence logs are re-included in `.gitignore`.
  - `cnc1/.gitignore` is anchored to `/build/`, so the hashed archived spidev binaries are no longer ignored.
  - `controller_backend/.gitignore` no longer hides the cited raw log.
- **Generators (R1-047, R1-048, R1-080, R1-088).**
  - The feature-catalog generator hashes all archived user notes and has a read-only `--check`.
  - The cost generator records a price source for every line and marks the one unsourced line.
  - The grblHAL scripts record the actual compiler and distro.
  - The expanded-target citation is corrected to lines 372-750.
  - `tests/test_research_generators.py` was added.

### 3.8 Status documents

The root documents now cite the current records:

- 220 compiled CNC1 assertions;
- runs `551cc0bd` (27 checks) and `5cd2bcb5` (68 checks in 9 launches);
- 252 + 27 RTL checks;
- 9,426 mapped cells;
- 3,118 adapter samples;
- 579 Python tests.

Older figures are labelled historical. A "Current and superseded review records" table was added to `reports/ENGINEERING_STATUS.md`. "Not ready for PCBWay manufacture" is stated in `README.md`, `PROJECT_BRIEFING.md`, `docs/BUILD_PLAN.md`, `reports/ENGINEERING_STATUS.md` and `reports/VALIDATION.md`.

### 3.9 Review and repair outcomes

The independent reviewers raised 22 issues across the seven groups. The repair passes fixed 20. Two were deferred as cross-owner follow-ups, and both were later closed in the final sync:

| Deferred issue | Closed by |
|---|---|
| `docs/EXPANDED_HARDWARE_TARGET.md` citation | Now cites lines 372-750 |
| Stale 10 ms servo-period comment in `controller_config/runtime.py` | Now mirrors the watchdog bound |

Review findings that changed the outcome included:

- the symlink bypass in the first rootfs filter;
- persisted capability identity broken by the first pulse-margin fix;
- an ESP recorder that could pair new source hashes with stale images;
- a public audit-entry method with no binding checks;
- overstated persistence-gate wording.

**Repair review of the final sync.** A later reviewer raised seven issues against the final-sync state. All were confirmed against the live files:

| Id | Issue | Outcome |
|---|---|---|
| review-1 | `PROJECT_BRIEFING.md` said the FPGA/ESP source hashes still match their manifests | Fixed: the briefing now says the FPGA and ESP manifests match; the ESP record was re-recorded (review-6) |
| review-2 | `PROJECT_BRIEFING.md` gave 32 configuration-service tests | Fixed: 40 tests in the 579-test run; 32 labelled historical |
| review-3 | FU-CD-06 was marked already fixed although its sentence was false again | Fixed: sentence corrected and FU-CD-06 re-counted as fixed |
| review-4 | Section 5 still listed the pulse-rate margin check as an open cnc1 item | Fixed: row closed with run `551cc0bd`; the remaining gap is actual-runtime coverage of `SERVO_PERIOD_LIMIT` |
| review-5 | `gateware/validation/manifest.json` re-recorded (only `recorded_utc` changed) without archiving the previous manifest; `reports/GATEWARE_VALIDATION.md` still gives 19:42:45Z | Fixed after the final sync: the recorder gained a read-only `--check`; the previous record was archived in `gateware/validation/before-final-sync-2026-09-28`, the regression rerun (252 + 27 checks, status encoder byte-identical) and re-recorded at 21:47:55Z; `--check` passes on the tree and fails on a tampered copy |
| review-6 | ESP manifest and `reports/ESP_SERVICE_BUILD.json` still record the old `controller_lab/service_health.py` hash | Fixed after the final sync: previous record archived in `firmware/esp32_service/evidence/before-final-sync-2026-09-28`; re-recorded at 21:48:07Z with the host core test rerun and the retained images unchanged; all hashes match |
| review-7 | Section 4 compared `check_release` output with "committed" reports, but the repository has no commits | Fixed: now compares with the working-tree reports |

## 4. Evidence regenerated (before → after)

| Evidence | Before the fix pass | Current record | Class |
|---|---|---|---|
| Full Python suite | 283 tests (04:42 run); 290 in the frozen root-verification snapshot | **579 tests, OK, 5 skipped** (Windows Python 3.14.6, 20:58Z; `python-tests.txt`). Much of the growth is Codex's new hardware-block tests, not audit tests. | host tests |
| RTL regression (`gateware/validation/manifest.json`) | 180 v1 checks (06:30Z) | **252 v1 + 27 ABI-v2 checks**, rerun and recorded 21:47:55Z; verified read-only by `python gateware/tools/record_evidence.py --check` | HDL simulation |
| Yosys Efinix-family mapping | 9,420 cells, 3,215 FF | **9,426 cells** (4,072 LUT4, 2,132 ADD, 3,221 FF, 1 GBUFCE), 19:22:22Z; structural CDC check added | family synthesis only |
| Post-map functional run | 179 assertions | 179 assertions, frozen pre-persistence driver (19:24:08Z) | simulation of mapped netlist |
| CNC1 compiled harness | 192 assertions (08:41Z manifest) | **220** (`cnc1/evidence/manifest.json`, 20:56:18Z) | compiled C/RTL simulation |
| CNC1 LinuxCNC volatile run | run `89f626bb`: 26 checks, 1,233 rows | run `551cc0bd`: **27 checks**, 1,124 rows, 14.819 s wall / 3.162 s simulated | real LinuxCNC in WSL, simulated RTL |
| CNC1 persistent run | run `04c7b257`: 59 checks, 9 launches | run `5cd2bcb5`: **68 checks**, 9 launches | same |
| Runtime / persistent host tests | 26 / 27 | **41 / 33** | host tests (adapter double) |
| Linux spidev backend | 892 + 892 assertions against header `601b8a46` (stale) | 892 + 892 against current header `0e244ab0` (20:30:34Z) | mocked device, host compile + sanitizers |
| LinuxCNC adapter | run `0544b28f`, 3,167 samples, tautological profile check | run `bac564b6`, **12 checks, 3,118 samples** (19:03:22Z); adapter tests 30 → 49 | real LinuxCNC in WSL |
| ESP32-S3 images | older images, mismatched source hashes, no manifest | clean builds 19:17:08Z, record refreshed 21:48:07Z with the same images; not reproducible, not flashed | target compilation + host test |
| Release gate | 22 ids; 16 prototype / 22 production blockers; 15 tests | **23 ids; 17 / 23 blockers; 36 tests** | manifest consistency only |
| Current-manifest hash mismatches | 16 in the pre-fix snapshot | 0 at the integration check | source inspection |

Checks rerun for this record (read-only, 2026-09-28 ≈21:15-21:25Z):

| Command | Result |
|---|---|
| `python cnc1/tools/record_evidence.py --check` | 0 problems (manifest 20:56:18Z) |
| `python cnc1/tools/record_spidev_evidence.py --check` | 0 problems (manifest 20:30:34Z) |
| `python gateware/synthesis/record_results.py --check` | verified, 26 files |
| `python gateware/synthesis/postmap/record_results.py --check` | verified, 179 assertions re-derived, 18 files |
| `python tools/check_release.py` (`--stage prototype`, `--stage production`, stdout only) | exit 2, `ready: false`, 17 and 23 blockers, identical to `reports/prototype-release-check.json` and `reports/production-release-check.json` in the working tree (rechecked in the repair review) |
| `python gateware/tools/record_evidence.py --check` (added after the final sync) | verified, 12 source and 2 evidence hashes, 252 + 27 checks (record 21:47:55Z) |
| Recompute of `firmware/esp32_service/evidence/manifest.json` and `reports/ESP_SERVICE_BUILD.json` | all hashes match after the 21:48:07Z re-record |

Hash state not repaired by this pass:

- `hardware/review-manifest.json` has 8 of 55 hashes stale. It belongs to the hardware owner, and the status report now names the connected-hardware review as current.
- Historical records such as `cnc1/evidence/post-manifest-review/pre-rerun-source-freeze.json` drift by design and are archived, not current.

## 5. What remains open, and who owns it

### Hardware owner (Codex): 22 distinct ledger items, plus datasheet notes

See [`ELECTRICAL_HANDOFF.md`](ELECTRICAL_HANDOFF.md), items E-01 to E-40. The main groups:

- **Validator and recorder hardening (E-01 to E-09).**
  - `--release` still trusts ledger-declared readiness.
  - Negative loads are accepted.
  - Non-channel terminals are unchecked.
  - Supply declarations are optional.
  - Component aliases can bypass collision checks.
  - The RTL cross-check fails open.
  - Tests cover only the generated ledger, not the checked-in file.
  - The review manifest is stale.
  - A rounded rate cap appears in the report.
- **Ledger content (E-10 to E-24).**
  - ROCK 3C is still recorded as the host.
  - The scope string and the 250 k and WDI blocker texts are stale.
  - Receiver termination and decoupling rows are missing or understated.
  - The JTX reference is on JPOWER, and the JTX label reads "FIELD TERMINALS".
  - Headroom warnings remain.
  - Verified MPNs are not integrated.
  - The permission block is not drawn.
- **Datasheet findings (E-30 to E-40).** The most consequential:
  - The TPS3431 cannot meet the 20 ms external-watchdog limit. The minimum achievable timeout is about 57-69 ms. TPS3851G18 standard timing with 4.7 nF C0G (13.40-17.87 ms) is the corrected candidate; an earlier 3.3 nF suggestion was withdrawn because WDI is falling-edge triggered (see E-30).
  - The DAC80501 powers up in a fail-to-zero configuration below 5.0 V unless a GAIN register write is made.
  - FIELD_5V can exceed the TPS4H160 recommended logic-pin maximum.
  - No isolated channels remain for TPS4H160 diagnostics.
  - Codex's own finding that the entry TVS does not protect the TPS4H160 against transients.
- **Resolved or partly resolved by Codex's newer blocks:** the TPS62160 accuracy and ramp issues (TPS62901 in `logic_power`), the supervisor threshold edge cases (LTC2962 in `power_sequence`), and the input-path limit (power-entry r0.2 proposal). The ledger still has to be updated to match.

### Other owners

| Owner | Open item |
|---|---|
| cnc1 | FU-RV-01: builds record no source identity, so the recorder binds the tree as it is at record time. The documented rerun → archive → record sequence reduces the risk but does not close it. |
| Report owners / Codex | `reports/power-protection-python-source-inventory.json` predates later edits. Re-record it or annotate it; never hand-edit it. `reports/platform-plan-review.json` could optionally be re-recorded against the six-note feature roadmap. |
| gateware (optional) | Refresh the frozen post-map driver so post-map checks cover the persistence gate, the watchdog-derived period and `progress_wdi`. |
| cnc1 (optional) | Closed: `runtime_preview_refuses_scale_above_margin_adjusted_ceiling` is in `cnc1/integration.py` and passed in run `551cc0bd` (27/27). Still open: `SERVO_PERIOD_LIMIT` is covered by host tests only, with no actual-runtime check. |
| Hardware documents | `docs/ELECTRICAL_DESIGN.md` (unchanged since 04:49 local) still needs: the 201-tick bound, the release-gate items (`fabrication_spec`, `programming_bundle`, `programming_test_scope`, `link_prototype_measurement`, `pcbway_quote`) with a checklist link, the host wording, and an accurate review-manifest sentence. |

### User decisions

- **R1-066:** accept 195,312.5 steps/s as the baseline rate, or fund a pulse-timing re-derivation with drive evidence.
- **R1-083:** Git LFS or plain objects for about 17 MB of hashed netlists.
- **E-37:** T20 configuration mode (x1 has no multi-image, which matters for safe field updates).
- **E-33:** the core PSU rating.
- The decisions in section 6.

### Deferred by rule

Six historical records were not edited because they are archives: R1-086 and FU-RV-03, -04, -06, -16 and -17. The status report's review-records table marks them superseded. `cnc1/evidence/post-manifest-review/archive.py` must not be run again.

## 6. PCBWay readiness: not ready

As of 2026-09-28 the answer is **no**. Every one of the 23 release-manifest artifact ids has a non-complete status, and none has a path or hash.

- `python tools/check_release.py` exits 2 with `ready: false` and **17 prototype blockers**.
- `--stage production` reports **23 blockers**.
- No `.kicad_pcb`, Gerber, drill, centroid or assembly drawing exists.
- No supplier contact, quote request or order has been made.

The source of the list below is `manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md` together with the current release-check output. The classes are those used in the checklist.

**User decisions (needed first; nothing can be frozen without them).**

| # | Decision |
|---|---|
| U1 | Board scope: six-joint/two-encoder baseline, or the eight-motor/four-encoder candidate. The eight/four candidate would need a new ledger, blocks, power, pin map and BOM, with no inherited totals. |
| U2 | First machine profile: drives, VFD, sensors, loads, stop arrangement (also E-22). |
| U3 | Compute module and host interface: a separate SBC with a link header, or a CM4/CM5/CB2 carrier on this board (also E-10). |
| U4 | Display package for the first build, and whether its power is on this board. |
| U5 | Quote and order quantities. The study quantities are 1/10/100/1,000. |
| U6 | Turnkey or combo, and the substitute policy. |
| U7 | Programming at PCBWay or in-house. |
| U8 | Functional test, X-ray and fixture scope. |
| U9 | FPGA package: F256 BGA or the LQFP option, compared on total board and assembly cost. |
| — | Configuration mode (E-37) and core PSU rating (E-33). |
| — | Purchase of an engineering host and an FPGA evaluation board for the link measurement. |

**Desk-closable (repository tools only; after U1-U4 where noted).**

- Exact MPNs and footprints for all BOM groups. The ledger still has 42 "MPN unresolved" blockers. Codex's block choices and `part-selections.json` cover many of them, but none is integrated.
- The permission latch and gates, the transient networks and the analog zero clamp.
- Validator and ledger corrections E-01 to E-24.
- Full-schematic capture from the existing blocks through the `tools/hardware_build_*.py` generators, then full-board KiCad ERC, then a named human electrical review.
- A draft fabrication specification (stackup and rules against PCBWay's options).
- Bring-up procedure, programming/test scope document and software validation, each bound to the board revision.

**Toolchain.** Efinix Efinity is not installed on this host or in WSL. It is needed for:

- T20 fit;
- the reviewed pin/bank map for the 84 signal/reserve GPIO;
- 50 MHz static timing;
- the power estimate;
- the configuration bitstream.

These feed `fpga_build` and `programming_bundle`. The `progress_wdi` RTL output already exists; its board coupling does not.

**Layout and DRC (need a frozen full schematic).**

- `pcb_layout`, `drc`, a frozen `fabrication_spec`;
- `fabrication_zip` (Gerber RS-274X and Excellon drill);
- `placement` (CPL), `assembly_drawing`;
- the designator-level BOM with PCBWay's ten turnkey columns.

All of these are exported from the approved layout only. No placeholder files.

**Physical tests.**

- `link_prototype_measurement`: a bounded motion-link measurement on real host hardware and an FPGA evaluation board, before final layout.
- Power sequencing, backfeed and short-circuit behaviour.
- TPS4H160 transient protection.
- Converter ramps.
- Production stage: `hardware_test`, `loaded_realtime_test`, `factory_test`, `system_integration_test`, `compliance_review`, and `final_cost` after an actual quote.

**Supplier step (user).** Submitting the released package and recording the quote in `pcbway_quote.submission` is a user action. Any order is a separate, explicit user decision.

## 7. Repository state and a recommendation

`git rev-parse HEAD` fails: **the repository has no commits yet.** Every top-level path is untracked. Several tools and agents have edited the tree in parallel today, and without a baseline commit there is no way to diff or revert one tool's changes without affecting another's.

Recommendation: commit a baseline before any further parallel edits. This audit made no git changes. Before that first commit:

1. Settle R1-083 (Git LFS or plain objects for the netlists, and the 25 MB `reports/root-verification-20260928` package).
2. Confirm with `git check-ignore -v` that every cited evidence log and hashed archive is included. The rules are in place (root `.gitignore` negations, `cnc1/.gitignore` anchored `/build/`, `controller_backend/.gitignore`).
3. Keep the byte-exact root `.gitattributes`, so hashed files keep their bytes.

After that, give each concurrent tool its own branch or commit sequence.

## 8. Limits of this record

- Outcomes for the cnc1, config and hygiene final agents were confirmed by reading live files and rerunning the read-only `--check` commands above. Those agents' own reports were not available to this record.
- The 579-test run is a working-tree observation: no source inventory was hashed with it.
- No hardware was connected, flashed or measured by any stage of this audit.
