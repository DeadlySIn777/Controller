# Controller readiness reaudit

Started 3 October 2026; checks continued across local midnight. **Manufacturing, complete-machine operation and automatic commissioned setup remain unready.** This review covers hardware/release evidence, firmware/RTL/runtime, product/service/frontend and the user's AI setup priority. Claude owns active routing. No hardware, PCB/layout, gateware, firmware, machine configuration, external UI or frozen IS-1 source was changed by this audit.

The desired product is still one active motherboard with all twelve motor interfaces fitted, four base ABZ, 24 general DI, 16 smart DO and the remaining specified interfaces; qualified commodity modules remain replaceable. Historical six-joint/two-encoder tests remain historical. The last verified adopted board is Source26/ROOT104/CAD30; in-progress routing elsewhere is not evaluated or overwritten here.

## Most important findings

| Priority | Finding | Required next result |
| --- | --- | --- |
| P1 | **The unadopted external UI assistant misinterprets negated/informational requests.** An inert test captures `$H` for “do not home” and “explain home”, `M3 S12000` for “do not start spindle”, and a run callback for “do not run the job”. This is not adopted Controller firmware. | Exclude that direct-command assistant from reuse. Setup AI proposes typed configuration through the shared service; add negation/quotation/intent tests with zero actuation. See [PS-01](product-service-audit.md). |
| P1 | **The promised easy frontend and AI setup expert are not integrated.** Current public configuration is a six-motor/sixteen-input simulated fixture with two virtual profiles; historical XYZ runtime configuration is separate. No approved physical equipment catalog, AI orchestration or budget enforcement exists in Controller. | Build one versioned IS-2 service and one complete supported setup workflow, then attach the grounded assistant. See [PS-02–PS-04](product-service-audit.md) and [the new AI contract](../../docs/AI_SETUP_CONTRACT.md). |
| P1 | **No complete CNC3/HAL/IS-2 machine is ready.** Diagnostic wrappers deliberately inhibit upper motion channels and field outputs; the read-only IS-2 profile correctly refuses qualification. Nine complete machine profiles remain NOT_RUN. | Adopt and test the complete retained 96/176-byte protocol, providers, HAL, twelve motors/four encoders, full I/O and fault/recovery behavior; never tie unqualified flags true. See [SW-01/SW-02/SW-07](software-audit.md). |
| P1 | **FPGA capacity is tighter than the umbrella status suggested.** A newer report-local optimized composition passes a partial coarse screen at 19,477/19,728, leaving 251 cells (1.272%); missing functions and vendor fit/timing remain open. | Complete resource accounting for every required block and exact device/package implementation before freezing capability. The candidate remains unadopted. See [SW-03](software-audit.md). |
| P1 | **Source27 electrical corrections are not in the routing handoff.** Their hashes remain distinct from live Source26. | Routing owner reconciles the reviewed electrical delta with the returned native successor and reruns affected source/native/firmware gates. Do not replace ongoing routing with the staged old candidate. See [H1](hardware-release-audit.md). |
| P1 | **Native cleanliness is not board completion.** Last adopted ROOT104 has 3,508 required joins and 274 vias intersecting 277 paste SMD lands; stackup/process/mechanics remain provisional. | Complete native routing, uncapped connectivity, actual returns/power and drill/land/process qualification after Claude's work. See [H2/H4](hardware-release-audit.md). |
| P1 | **Whole-controller limits are unqualified.** Complete power/analog, 20 ms inhibit, 1 kHz loaded transport, 700 µs margin and physical timing/thermal/EMC proof remain open; 2 MHz/channel is a target. | Source-bound budgets and complete simulations, exact target implementation, then loaded physical measurements with explicit denominators/faults. See [H3](hardware-release-audit.md) and [SW-04](software-audit.md). |
| P1 | **Whole-board recovery, offline entitlement and production update/rollback are not implemented.** Retained ESP diagnostic build uses single-app partitions without rollback. | Versioned full-profile service/recovery/update design, compatible images and interrupted-operation tests, followed by actual media/power-off service qualification. See [PS-05/PS-06](product-service-audit.md). |
| P2 | **Readiness documents and metadata drifted.** Stale architecture, board counts, partial cost, ESP-hash and recorder instructions could mislead engineering or AI retrieval. | Current summaries corrected below; historical evidence preserved. Hardware-owned stale metadata remains for its owner. See [H5–H7](hardware-release-audit.md), [SW-06](software-audit.md), [PS-07](product-service-audit.md). |
| P2 | **Release checking does not explicitly enforce all product/AI/setup gates.** It validates evidence manifest structure and hashes. The historical RTL manifest also has an unrecorded added characterization bench. | Bind explicit per-product gate results to actual release evidence; resolve baseline/characterization scope with a new actual regression, preserving historical logs. See [PS-08](product-service-audit.md) and [SW-05](software-audit.md). |

P1 denotes a blocker to the affected release/customer workflow, not a claim that a currently operating machine is unsafe. No physical machine was connected or exercised.

## Fresh evidence from this audit

| Check | Result | Evidence boundary |
| --- | --- | --- |
| Source, staged-source, adopted/published PCB and routing-handoff provenance | **643 SHA-256 comparisons match** | 16 release bindings, 160 live Source26 files, 163 staged Source27 files and 304 handoff payload files; not a fresh ZIP-container, electrical or native routing validation |
| Source/negative host tests | **25 passed**; **619 scoped source hashes unchanged** | Six CNC3 source and nineteen diagnostic local-I/O source tests; no target MMIO/IRQ execution or new HDL replay |
| Retained software candidate provenance | **44 + 45 + 101 bundle hashes and 26 evidence references match** | IS-2 profile and optimized motion/record candidates; receipt verification, not rerunning those compiled simulations |
| Historical manifests | CNC1 runtime, mocked spidev, family synthesis and post-map checks pass; ESP 14/14 source hashes match | Retained results stay dated; no new target build, runtime, synthesis or flash |
| Historical RTL manifest check | **Fails:** one unrecorded characterization bench | `tests/tb_stepgen12_characterization.sv` relative to gateware; no old RTL change reported; no evidence re-stamping performed |
| External assistant parser | **Five behavior captures**, including four negated/informational command-dispatch defects | Inert Node VM/capture adapter; no UI boot, network, serial or hardware; [probe and captured source hash](../../WORKSPACE_REFERENCES.md#artifact-11b0be102a5ab312) |
| Manufacturing release consistency | **17 prototype blockers; 23 production blockers; ready=false** | Fresh read-only evaluation; no artifact status promoted |
| Release-check regression after metadata correction | **37 passed**; seven inspected source/manifest/CAD inputs unchanged | [Test receipt](../../WORKSPACE_REFERENCES.md#artifact-6c746c992a769bd3); the preserved first invocation failed test discovery and ran zero tests, then the corrected discovery command passed |

Raw commands, scope, hashes and output are in [software-checks.json](../../WORKSPACE_REFERENCES.md#artifact-40ccc4b3979cdf45), [hardware-release-readonly-evidence.json](../../WORKSPACE_REFERENCES.md#artifact-e8741bec5d6c4c88), and the component reports. [Exact manifest comparison](../../WORKSPACE_REFERENCES.md#artifact-46f94102ff1842dc) confirms the one-field correction and unchanged blocked release results. Counts are scoped and may overlap historical suites; do not add them into an invented new full-suite total.

The earlier full r08 remains **25 PASS / 9 BLOCKED / 1 physical NOT_RUN / 0 FAIL**, with 1,895 host and 238 native cases passing and five Windows symlink skips. That retained run was not rerun. This audit did not perform target compilation, HDL simulation, synthesis, vendor FPGA fit/timing, ERC, DRC, board refill, electrical simulation or physical measurement. The complete design has not been independently re-proven net by net.

The [machine-readable audit register](../../WORKSPACE_REFERENCES.md#artifact-cd02f43733547dc6) captures all G01–G26 with their required evidence and current limits; it is an audit snapshot, not a live capability manifest or implemented release enforcer. [Final report verification](../../WORKSPACE_REFERENCES.md#artifact-deb32e10910bb816) checks local links, complete gate/case IDs, preserved before-copies, all 619 scoped software hashes, all 643 hardware provenance comparisons and the unchanged external assistant source. It does not promote a product gate.

## AI setup: what “do it once, correctly” now means

The [AI setup contract](../../docs/AI_SETUP_CONTRACT.md) converts the user's priority into a reviewable build specification and nineteen acceptance scenarios, tracked by **G26**:

- Read exact board/software/equipment facts, retain answers and request only unresolved dependencies. Unknown ratings or wiring stay unknown.
- Let deterministic code calculate scales, allocate resources, enforce actual limits and produce the wiring plan. AI selects/explains; it cannot manufacture capability or completed checks.
- Use one UI/CLI/AI validation, preview and transaction service. Configuration approval does not grant motion permission; physical commissioning has separate bounded authority.
- Protect the discussed roughly **US$15 allowance** with a visible ceiling, durable cost ledger, worst-case reservations, bounded retries/repair and a no-progress stop. Preserve uncertain billing reservations. The allowance is not a target to spend.
- Reopen unchanged setup with zero paid calls, preserve progress across interruption and retain the full deterministic offline workflow.
- Measure first-plan correctness, unnecessary questions, unsafe accepted proposals, actual cost and novice completion. No universal “most advanced” or perfect-first-attempt claim is made.

No paid API call was made, no model/provider was selected and no AI runtime was implemented in this audit. These controls must be built and evaluated before promising the experience.

## Readiness corrections made

Nine existing readiness/documentation files were preserved byte-for-byte in [before-docs](../../WORKSPACE_REFERENCES.md#artifact-7dd332dc4b0cfdee) with [their original hashes](../../WORKSPACE_REFERENCES.md#artifact-d26a4e021f260a2b), then reconciled without changing release status:

- Project memory, build plan and roadmap record Claude's routing ownership and the AI setup/cost priority; they point to this audit.
- Engineering status corrects the superseded pending-architecture/eight-plus-four claims, ESP source-hash observation and RTL recorder instructions, and separates the newer partial FPGA screen from the older blocked composition.
- Acceptance gates G01/G22 now use the verified ROOT104 counts; new G26 records AI setup acceptance. Existing G01–G25 are retained.
- The common configuration document links the AI contract; display costing labels the six/eight-motor matrix as historical; the build plan labels the old 980-part cost subset historical.
- The PCBWay checklist now names Source26/ROOT104/CAD30, current partial cost, staged Source27 and drill/land limitations.
- `manufacturing/release-manifest.json` changes only the erroneous total zone/rule-area count **1,521 → 1,544**. No status, geometry, hash binding or qualification changes.

`hardware/motherboard/pcb-open-items.json`, dated reports, old cost-generation source and historical manifests remain untouched. They contain the documented stale or scope-limited items; do not feed them to setup reasoning as current authoritative capability. The external candidate UI remains untouched and unadopted.

## Next implementation work, independent of active routing

| Order | Work package | Concrete acceptance |
| --- | --- | --- |
| 1 | IS-2 setup service and exact reference equipment profiles | One typed complete setup model with genuine identity/qualification, all required resources and limits; same normalized result/error/diff through UI/CLI; versioned away from historical fixtures |
| 2 | Deterministic first-use frontend and recovery flow | One supported no-code/no-CAD setup from intake to saved plan, actionable diagnostics and offline resume; missing physical checks remain explicit; intended UI source confirmed before adaptation |
| 3 | AI adapter and persistent budget controls | Fake-provider tests first; exact grounded tools, retained facts, intent isolation, bounded retries and crash/concurrency cost controls; then separately budgeted model evaluation of AI01–AI19 |
| 4 | Complete firmware/runtime and FPGA composition | Actual CNC3/HAL/providers/RTL integration and complete device fit/timing; source-bound fault/load/analog characterization; no admission by fabricated qualification flags |
| 5 | Recovery/update/entitlement and product evidence | Machine and board/module identity-aware restore, compatible image/configuration rollback, offline entitlement, explicit per-package acceptance evidence |
| Routing-owner handoff | Reconcile native routing with staged electrical correction, then final manufacturing/physical gates | Exact-source successor review, native/independent connectivity, drill/land/return/power/mechanics, complete quote/package and later measured hardware qualification |

Current partial priced parts remain US$1,091.51/$877.37/$796.51 at 1/10/100 controllers, with 185 exact MPNs/720 purchased fitted pieces unpriced and complete package/manufacturing costs unknown. No new prices, supplier communications, upload, order or manufacturing files were produced.

The review does not claim exhaustive source verification or readiness from pass counts. It records actionable gaps, fresh bounded checks, preserved evidence and corrected current requirements while leaving routing to its owner.
