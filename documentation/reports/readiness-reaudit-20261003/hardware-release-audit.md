# Hardware and manufacturing readiness reaudit

3 October 2026 (user date). **Not ready for prototype manufacture, supplier submission, production, or machine operation.** The routing owner is Claude. This audit changed no hardware, CAD, routing, source generator, historical evidence, external IS-1 archive, or machine configuration. It did not run KiCad or regenerate fabrication files.

## Fresh verification and its limits

`python -B reports/readiness-reaudit-20261003/hardware_release_readonly.py` performed **643 SHA-256 comparisons, all matching**: 16 release-manifest bindings, 160 live Source26 files against the Source27 freeze's before-snapshot, 163 staged Source27 candidate files, and all 304 hashed payload files in the Argus handoff. The handoff manifest excludes itself; this is not a fresh revalidation of routing or of the ZIP container. Reproducible results and exact paths are in [hardware-release-readonly-evidence.json](../../WORKSPACE_REFERENCES.md#artifact-e8741bec5d6c4c88).

The adopted ROOT104 and published CAD30 board match SHA-256 `70b71c36778e49600b77f382cf84df81ef3ac6dce442cc0e576b494d307979cc`. The live Source26 design remains `6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8`; the staged Source27 has not replaced it. Text object counts independently find 2,688 footprints, 8,727 segments, 3,080 vias and 1,544 zones/rule areas. These are textual inventory checks, not a native PCB parser or DRC rerun.

The existing release checker was imported read-only and returns **prototype ready=false with 17 blockers**, **production ready=false with 23 blockers**. Both lists are preserved in the evidence JSON. The checker expressly evaluates manifest consistency rather than physical truth (`tools/check_release.py:46`, `:156`, `:192`, `:239`). An incomplete artifact is rejected before its hash is checked; the independent comparisons above therefore add useful provenance coverage that the ordinary blocked release run does not provide. No checker defect that permits the present incomplete manifest to pass was observed.

| Evidence class | Verified/read result | Scope remaining open |
|---|---|---|
| Source inspection and hash provenance | Fresh 643 matching comparisons; Source26/Source27 distinction preserved | Electrical ratings and design completeness do not follow from hashes |
| Host tests | Historical full r08 records 1,895 host passes and five Windows symlink skips | Not rerun here; not target or physical evidence |
| Target compilation | Existing staged/older component evidence only | Complete current board firmware, compute image/pinmux and loaded runtime qualification |
| HDL simulation | r08 has bounded actual C/RTL, seeded SPI, plant and IS2 read-only profile evidence | Complete HAL/providers/output authority and simultaneous complete-machine behavior |
| FPGA synthesis | Family synthesis is distinct from exact device implementation | Efinity T20 package/resource fit, place/route, static timing and reproducible bitstream |
| Circuit ERC | Source26 recorded 0 errors and 70 unsuppressed warnings | Exact warning dispositions are source topology evidence; no fresh ERC here |
| Board DRC/connectivity | ROOT104 recorded 0 regular errors/warnings/no ignored checks, but 3,508 missing joins | No fresh DRC/refill/connectivity run here; connectivity completion still fails |
| Physical measurements | r08 physical stage NOT_RUN | Full electrical, 20 ms inhibit, loaded timing, thermal, EMC, mechanics and service |

The historical r08 record remains **25 PASS / 9 BLOCKED / 1 NOT_RUN / 0 FAIL** (`reports/pre-hardware-validation-20261002/full-bypass-PROC-seeded-IS2-r08/report.json:177`, `:1057`). A large pass count does not close a blocked class. Historical six-joint/two-encoder and 327-part MC evidence retain those labels.

## Findings requiring action

### H1 — P1: Source27 reset/health corrections remain outside the routing baseline

The staged plan explicitly says `adopted: false`, identifies 2,698 parts, changes U11032.6 and U11034.6 from the old clear nets to `MOTOR_FEED_CLEAR_FAST_N_A/B`, and retains unqualified loaded reset slew, partial-power, temperature and 20 ms behavior (`reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02/source27-successor-rebinding-plan-r02.json:2`, `:6`, `:11`, `:17`, `:76`). The routing handoff explicitly excludes these corrections (`reports/argus-routing-handoff-20261002/ROOT104-CAD30/START_HERE.md:27`). The fresh matching hash checks confirm this is a real source split, not documentation alone.

**Next gate:** the routing owner must reconcile the returned exact ROOT104 successor with the reviewed Source27 delta, including seven changed existing references, two receiving CLR endpoints and ten added real parts. Rebind source, netlist, 727 capacitor owners, exact board nets/footprints, routing proofs and successor cost before adoption. Do not overwrite new routing with an older Source27 candidate or silently mark Source26 electrically frozen. This audit performs none of that merge.

### H2 — P1: Clean ordinary DRC is not routing or assembly readiness

The current published board reports 3,508 required joins remaining (`hardware/board_review/revisions/20261002-30/publication.json:11`). The drill audit, already bound to the ROOT104 hash despite its ROOT103 directory name, reports **277 same-net paste-land intersections involving 274 drilled vias** (`reports/motherboard-pcb-integration-20261002/ROOT103-bypass-PROC-full-drill-SMD-r01/receipt.json:3`, `:8`). It explicitly leaves all assembly dispositions open (`:6292`). This count excludes tangency and registration margin and cannot be interpreted as a complete process clearance review. Tenting alone is not acceptance.

**Next gate:** routing-owner completion followed by exact-source native ERC/DRC, uncapped independent connectivity, retained-copper and actual reference-return checks, and complete drill/land/stencil/mask registration review. Every drill overlap needs reviewed geometry correction or an exact qualified filled/capped fabrication and assembly process. The 460 × 340 mm / six-layer / 1.6 mm specification remains provisional.

### H3 — P1: Complete power and independent 20 ms fault-to-inhibit proof remain absent

The current acceptance register retains open G04 and G07 (`docs/CURRENT_ACCEPTANCE_GATES.md:26`, `:29`). The numerical watchdog study's 17.44145 ms screen includes an **unmeasured 4.31 ms downstream allocation**, conditional leakage/capacitor assumptions, and no guaranteed maximum SET1 setup. Its nominal-only self-test screen has approximately **89 microseconds** upper clearance (`reports/next-implementation-20260930/WATCHDOG_NUMERICAL_REVIEW.md:9`, `:20`, `:26`, `:30`). These are useful screening results, not a guaranteed end-to-end bound.

The r08 register blocks complete power/permission and coupled load corners, SI/cables and electrothermal qualification (`reports/pre-hardware-validation-20261002/full-bypass-PROC-seeded-IS2-r08/report.json:199`, `:223`, `:231`) and records no assembled prototype (`:247`). The older whole-board power arithmetic is tied to a **1,394-footprint snapshot**, not current Source26 (`reports/motherboard-power-entry-20260930/load-closure/whole-board-power-audit.json:3`); its allocations must not be copied as current board maxima.

**Next gate:** source-bound complete rail/startup/partial-power/load and fault budgets, target FPGA current assumptions, regulator stability/thermal/transient and copper/contact limits, then measured worst-case fault-to-last-STEP and motor enable, DO, PWM, process and AO responses. Include clock stall, invalid/stale link, brownout/reset, external permission loss and loaded outputs. Keep the 1 ms servo deadline, 700 microsecond completion margin, endpoint watchdog and 20 ms electrical inhibit separate (`docs/MOTHERBOARD_IS2.md:67`, `:69`). Preserve the active 0.5 A/channel and 2 A/four-output-group DO limits (`:86`).

### H4 — P1: Production mechanics, programming/test and turnkey release package are incomplete

The manifest contains no fabrication outputs (`manufacturing/release-manifest.json:222`) and leaves final stackup, production CPL, assembly drawing, bring-up, programming images/scope and PCBWay quote blocked (`:19` onward). A native render does not verify connector access, exact mating/keying, chassis/isolation, mounting, enclosure cooling, harness loads, module servicing or whole-board replacement. IS2 specifically requires its own measured whole-board service verification (`docs/MOTHERBOARD_IS2.md:25`) and compute compatibility qualification (`:29`).

**Next gate:** freeze the reconciled electrical/physical revision and exact module/package scope; establish final fabrication/process rules and mechanical/assembly review; qualify device build and target images; define a inhibited bring-up and factory-test fixture/limits; produce actual Gerbers/drills, complete BOM, verified CPL and drawings from that accepted board. Obtain the file-hash-bound PCBWay quote only once the package is complete. Production additionally requires physical hardware, loaded real-time, factory/system integration, complete cost and compliance evidence. No upload or supplier action was performed.

### H5 — P2: Current manufacturing checklist describes an obsolete snapshot

At audit capture, `manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md:5` calls 1,585 footprints and 72 ERC warnings the reconciled source; `:7` presents CAD21's 880 footprints/1,600 joins; `:11` says only the old 980-part subset is costed. Current Source26/CAD30 is 2,688 footprints, 70 warnings and 3,508 joins, with a newer immutable v11 partial cost audit. The checklist correctly blocks manufacture, but its live inventory and missing-circuit narrative are stale and omit the current Source27/drill-land caveats.

**Correction:** replace its current-state summary with exact Source26/ROOT104/CAD30 evidence and v11 cost scope; retain old snapshots as labelled history. Preserve all remaining release requirements and `manufacturing_ready: false`.

### H6 — P2: Release metadata contains an internally inconsistent zone count

At audit capture, `manufacturing/release-manifest.json:176` says 1,521 total native zones/rule areas while adjacent `:177` and `:178` specify 1,453 copper zones plus 91 rule areas, totaling **1,544**. Independent textual object inventory confirms 1,544 in the exact SHA-bound published board. This does not change connectivity or readiness.

**Correction:** reconcile that summary field to the exact existing inventory without touching CAD. The capture manifest SHA is retained in the audit evidence. If the root consolidation fixes the field, that is a documentation correction after this observation, not new board validation.

### H7 — P2: Hardware-owned open-item metadata still describes very old source geometry

`hardware/motherboard/pcb-open-items.json:2` refers to 327/701 parts; `:4` says analog/process/comms and compute/ESP/storage are not fully implemented; `:5` gives an obsolete 161/183 FPGA proposal; `:8` retains the old 220 × 100 mm region. The matching hash check proves it was already part of the retained Source26 before-snapshot. It is not evidence that today's integrated board has that old population or allocation.

**Correction after routing coordination:** issue reviewed current open-item metadata through the hardware owner, keeping old source receipts immutable. Do not edit this hardware-owned file during Claude's routing. The safe current readiness records should clearly supersede it in the meantime.

## Work that can proceed without routing edits

1. Reconcile current manufacturing summaries and the release zone count while preserving blocked status and immutable historical records.
2. Build a concrete qualification matrix for full power/defaults/20 ms responses, exact compute/module images, and complete target load; identify required measurement endpoints and evidence classes before hardware exists.
3. Prepare the factory bring-up/test and whole-board exchange/recommissioning requirements, exact package cost gaps, and assembly/process review questions. Do not issue production geometry, a manufacturing package or a supplier quote request prematurely.
4. Accept Claude's returned routing only against exact baseline bytes, then carry out the explicitly reviewed Source27 reconciliation and affected native/source/HDL/target regressions. Existing unchanged-board hashes and passes cannot be reused as proof of changed routing.

This audit is an evidence and release-readiness review. It does not certify every individual net/component, rerun vendor physics models, qualify current electrical limits, or close the identified blockers.

## Verification after readiness-document correction

The root consolidation corrected H5's current checklist summary and H6's zone count, preserving originals under `before-docs/`. The release-manifest comparison contains exactly one semantic and textual value change: `/partial_candidate/published_viewer/native_zone_or_rulearea_count`, **1,521 to 1,544**. No artifact status or manufacturing-readiness flag changed. [Exact diff](../../WORKSPACE_REFERENCES.md#artifact-99ad5649d977cf76) and [structured comparison](../../WORKSPACE_REFERENCES.md#artifact-46f94102ff1842dc) retain both hashes and the unchanged gate results: **17 prototype blockers, 23 production blockers, both ready=false**. H1–H4 and hardware-owned H7 remain open.

The focused release-checker host suite then passed **37 tests** with `python -B -m unittest discover -s tests -p test_release.py -v`. Seven inspected source/manifest/CAD inputs remained byte-identical during execution. [Test log](../../WORKSPACE_REFERENCES.md#artifact-d21f9f4b3d1020e6) and [hash receipt](../../WORKSPACE_REFERENCES.md#artifact-6c746c992a769bd3) are report-local; the original 643-comparison evidence is preserved. The initial module-style invocation failed to import `tests.test_release` before any real release tests ran; that discovery failure remains in `hardware-release-tests.log` and `hardware-release-tests.json`, and was resolved by using unittest discovery. This is host validation of release rules and live provenance bindings, not new hardware qualification.
