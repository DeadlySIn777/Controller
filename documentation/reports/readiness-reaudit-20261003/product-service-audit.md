# Product, setup, AI and service readiness re-audit

Audit started 3 October 2026 in the client's time context. Scope is readiness and software/product contracts while Claude owns active routing. This audit changed no routing, KiCad, hardware source, firmware, runtime, machine configuration or external UI files. Only this report and its isolated parser probe were created by this workstream. Required project memory, build plan, roadmap, engineering status, IS-2 and display requirements were read first. Main-audit document corrections may change the live line numbers below; pre-correction statements are deliberately identified.

**Result: the existing work is useful engineering infrastructure, but the promised easy setup/frontend and CNC setup expert are not implemented as one product.** The CLI truthfully exposes disconnected fixtures; the actual-runtime configuration service truthfully supports a separate six-channel/XYZ laboratory scope. The biggest newly reproduced issue is in the external, unconfirmed FluidCNC UI candidate: ordinary negated/explanatory chat can reach raw machine commands. That assistant must not be adopted unchanged.

Severity means P1 = blocks adopting/releasing the affected customer workflow, P2 = material readiness or evidence gap. No P0 emergency is claimed, and no physical behavior was exercised.

## Findings

### PS-01 — P1: the external reference assistant treats explanatory or negated text as an execution request

This is a **fresh reproduced software defect in the unconfirmed external UI candidate**, not a claim about adopted Controller firmware. `research/UI_REFERENCE_AUDIT.md:3` identifies the candidate as `Z:/Programming Projects/Genmitsu1030Cnc/fluidcnc`; the exact intended Octopus/MR-1 reference remains unconfirmed. No application was launched.

`Z:/Programming Projects/Genmitsu1030Cnc/fluidcnc/ai-assistant.js:76` uses an unanchored home regex. `:161` tries patterns before conversational handling, `:166` immediately invokes the action, `:236` generates `$H`, and `:367` sends generated G-code through the supplied adapter. `app.js:483` supplies the actual Grbl adapter. `app.js:565` dispatches the assistant's `runJob` action to `startJob`. There is no shared Controller configuration preview/apply boundary on that route.

The isolated Node VM probe had an empty `window`, no browser bootstrap, no network/serial implementation and an inert capture-only adapter. It produced:

| Input | Captured behavior |
|---|---|
| `do not home` | `$H` |
| `explain home` | `$H` |
| `do not start spindle` | `M3 S12000` |
| `do not run the job` | `runJob` callback |
| `emergency stop` | Generic `stop` callback; the later estop pattern is shadowed |

Evidence: [reproduction](../../WORKSPACE_REFERENCES.md#artifact-f0aad318ddd60609), [captured results](../../WORKSPACE_REFERENCES.md#artifact-11b0be102a5ab312). The source SHA-256 was `90a6624e36cba2bd0ab28e77eda844e605edfd17b20a25323f186eb03f32e948`. This proves command generation/callback dispatch only; whether a live downstream Grbl instance would accept a command was neither attempted nor inferred. No software phrase should be represented as a safety-rated emergency stop.

**Decisive gate:** setup assistance receives no raw G-code, jog, spindle or run sink. It returns typed configuration proposals through the shared validator. Test negation, questions, quotations, pasted manuals, contradictory context, stale plan/replay and repeated submissions with a zero-actuation expectation. Machine operation, if later provided through conversational intent, requires its own explicit, versioned authority path. A regex word match is insufficient.

### PS-02 — P1: the current public configuration schema cannot describe or commission the adopted motherboard

`controller_config/model.py:77` fixes board identity to `virtual-baseline-6j-2enc`; `:95` offers only `sim-mill-3axis` and `sim-lathe-2axis`; `:101` defines only virtual step drives and home switches. `:120` creates six motor resources and `:125` creates sixteen input resources. The schema has no twelve-motor IS-2 identity/capability model, four-ABZ assignments, 24/16 field-I/O configuration, real drive timing/polarity, spindle/VFD/accessory profiles or commissioned physical evidence. `:193` intentionally rejects completed commissioning claims. `:252` produces illustrative virtual terminals.

The separate actual-runtime adapter explicitly requires the isolated CNC1 simulator (`controller_config/runtime.py:283`), exactly the XYZ profile (`:310`) and six discovered channels (`:341`). `controller_config/persistent_runtime.py:3` explicitly says its durable schema contains the XYZ calibration subset, not a full cartridge. This separation is honestly documented and must be preserved as historical evidence rather than relabeled as IS-2 readiness.

**Impact:** adding a polished frontend or model agent over the current public schema cannot set up the real promised platform. Making the UI silently substitute a twelve-channel fixture or edit INI/HAL directly would split authority and violate the existing contract.

**Decisive gate:** add a versioned service slice for the current topology, initially under explicit simulation. Represent motherboard regions separately from actual replaceable modules; distinguish fitted, observed, implemented, configured, qualified and enabled capability. Preserve all twelve installed motor interfaces regardless of screen/licence and retain genuine unqualified states. A single machine profile must generate wiring, backend configuration, limits, dependent verification and saved state. UI, CLI and assistant proposals must produce identical normalized data, validation errors, revisions and diffs. At least one eight-motor and one twelve-motor configuration must be representable without inventing hardware proof.

### PS-03 — P1: there is no implemented expert setup or API cost-control layer to support the user's AI promise

The current Controller Python/service/schema sources have no provider client, expert knowledge retrieval, model tool orchestration, token/cost accounting, budget reservation, retry policy or AI setup evaluation suite. The external `CNCAssistant` is a regex parser plus canned responses (`ai-assistant.js:64`, `:151`, `:388`), not a model-backed setup expert. Its machine defaults are generic (`:21`) and feeds/speeds tables are authored constants (`:31`), not exact qualified drive/tool/machine profiles. Its bounded-looking conversation array (`:142`) is not cost metering or durable setup progress.

The basic deterministic foundation is useful: strict unknown-key rejection, capability-limit checks and commissioning-evidence rejection already exist in `controller_config/model.py:139`, `:185` and `:191`; revision/epoch-bound apply and audit exist in `controller_config/service.py:295`, `:311` and `:327`. Reuse these ideas. Do not spend model calls recomputing deterministic electrical/motion bounds or debating the user's already recorded choices.

**Decisive gate:** one persisted setup record contains requested machine/drive/sensor identities, observed facts, explicit user choices, missing evidence, decision provenance and pending verification. Exact approved profiles and pinned source references supply facts. A deterministic dependency check decides the minimum missing questions; previously answered facts are not repeatedly requested. The model proposes typed changes, while code calculates and rejects electrical/motion limits. Uncertain hardware remains unresolved instead of guessed.

For paid calls, reserve a conservative maximum cost before each request, account for input/output/tool/retry usage, enforce the authorized total budget before dispatch, cap retry loops, and cache results by normalized inputs plus exact profile/source/model revision. Timeouts and repeated clicks need idempotency. Persist progress before calling and resume without redoing the intake. Exhaustion, absent credentials and offline use retain the deterministic wizard and exportable work. A fresh API cap is not an excuse to drop mandatory checks or authorize motion.

Evaluate a fixed corpus of supported, ambiguous and deliberately misleading setups before calling this an expert: correct first complete proposal, unnecessary clarification count, repeated-question count, unsupported-fact rate, cost per completed setup, interruption/resume and budget overrun. Every accepted safety-relevant value must trace to approved evidence or an explicitly required measurement. There should be no unsupported actuation, silent capability inflation or spending above the cap. Successful setup is complete configuration plus required verification, not merely well-formed JSON. These are acceptance requirements, not measured success rates.

### PS-04 — P1: guided first boot, diagnostics and touchscreen commissioning are requirements without an integrated implementation

The live CLI command tree (`controller_config/__main__.py:29`) provides capabilities/schema/init/audit/profile/config/wiring/backup/cartridge/recovery. There is no implemented public `commission`, `diagnose`, `power status`, device discovery or firmware inspect/stage/activate/rollback family. `docs/CONFIGURATION_AND_CLI.md:8` correctly labels the wider surface proposed. `controller_backend/profiles/sim/display-client:2` and `cnc1/profiles/sim/display-client:5` launch Python integration demos, not the product UI. `README.md:15` and `docs/BUILD_PLAN.md:131` still treat the preferred UI source as unconfirmed.

The ESP target program prints advisory host-seen/link/progress fields (`firmware/esp32_service/main/service_main.c:49`), and default configuration leaves the receiver unassigned (`firmware/esp32_service/sdkconfig.defaults:4`). This is not a customer-visible whole-board diagnostic service with terminal-specific measured values and recovery steps. `controller_lab/service_health.py:6` only encodes observations and opens no transport.

**Decisive gate:** implement and record one disconnected vertical workflow: offline first boot → correct machine/profile selection → generated terminal guidance → input evidence → bounded direction/scale/homing commissioning under the proper authority → save → power/reconnect recovery → same actual state. Include a no-CAD route. At each blocked step show the exact unmet requirement, observed evidence/age and next valid action. Do not show fresh-looking zero values for missing/stale measurements. Retain the existing user target of eight of ten first-time users reaching verified low-speed jog within fifteen minutes (`docs/CURRENT_ACCEPTANCE_GATES.md:32`); establish the starting point and required checks before running that study.

`docs/DISPLAY_TIERS.md:29` requires the same workflows on all sizes and `:32` requires lost-touch jog cancellation. Before usability claims, exercise 800×480 as a candidate compact viewport plus medium, ultrawide and high-pixel-count layouts; test touch-only file selection, numeric entry/keyboard overlap, errors, long labels, scaling, reconnect and cancellation. Emulated viewport results do not qualify real touch targets, display power/EMI or loaded real-time behavior.

### PS-05 — P1: supported whole-board recovery, mirror authority and offline entitlement are still absent from the implemented service

The current recovery model names `SIM.INPUT_BANK0` (`controller_config/recovery.py:23`), constrains restored inputs to the first eight virtual inputs (`:101`), stores a virtual configuration in two file slots (`:112`), and implements only bootstrap and `replace_input_bank` (`:281`). It does reject foreign/equal-generation conflicts and stale plans, but does not implement actual motherboard exchange, module/board calibration identities, protected media, full-profile mirror/export arbitration or offline licence preservation.

`docs/MODULAR_REPAIR_AND_MEMORY.md:3` requires commodity-module exchange and a distinct whole-motherboard procedure with retained terminal groups. `:81` requires deliberate cartridge/mirror/export authority; `:118` requires image/configuration rollback compatibility. `docs/COMMERCIAL_MODEL_AND_LICENSING.md:43` requires an offline-verifiable entitlement and `:48` the same capability/licence result in UI/CLI/assistant. No entitlement implementation was found in current Controller runtime/service/test sources.

**Decisive gate:** first extend disconnected recovery with motherboard replacement and compute/ESP/media replacement as separate dependency graphs. Show precisely which terminal groups, factory calibration and commissioned checks changed; preserve unaffected machine settings and legitimate entitlement; invalidate position/homing/permission. Inject interrupted save/mirror/export/import stages and stale/foreign/conflicting identities. Later qualify exact physical media, hardware write protection, every supported spare image and actual power-off service, measuring board service separately. Old virtual input-card tests are retained regression evidence, not physical board-service proof.

### PS-06 — P1: the retained ESP build cannot provide the specified update/rollback workflow

Fresh source inspection finds `firmware/esp32_service/sdkconfig:422` has `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` unset, `:585` selects single-app partitions and `:587` leaves two OTA slots unset. `:404` leaves reproducible application builds unset. This agrees with the diagnostic-build limitation in `firmware/esp32_service/README.md:49`; it does not satisfy the desired update contract in `docs/MODULAR_REPAIR_AND_MEMORY.md:118–120`. No production programming bundle exists yet.

**Decisive gate:** build a versioned offline update bundle bound to exact motherboard/compute/ESP compatibility and image authenticity; stage only with independent inhibit and enough validated storage/power; preserve a permitted known-good image and compatible settings. Inject interruption at staging, activation, first boot, validation and schema migration. A successful boot alone must neither accept an incompatible migration nor restore run permission. Target compilation, flashed update trials and physical power-loss behavior need separate evidence. Do not change the current diagnostic build into a release merely by enabling one flag.

### PS-07 — P2: current-looking readiness/cost text still mixes obsolete source snapshots and architecture

At inspection, `reports/ENGINEERING_STATUS.md:68` said the one-PCB direction was a pending clarification and described confirmed passive-base/removable FPGA history as if current. `docs/BUILD_PLAN.md:57` called the 980-part US$379.67/$314.26/$280.60 snapshot current even though its own banner names Source26 v11. `docs/CURRENT_ACCEPTANCE_GATES.md:23` and `:44` retained ROOT102/3,524-join wording while their banner names ROOT104/3,508. Root is reconciling these current summaries with preserved before-copies; the archival evidence itself should remain unchanged.

A deeper generation gap remains: `tools/build_compute_display_matrix.py:102–104` contains only historical six/two and eight/four I/O scopes, still calls eight/four the preferred next candidate, and `:116` generates all comparison cases from that list. `:81` labels the field-circuit cost block six/two or eight/four. The display sourcing observations can be reused as dated candidates, but this generator cannot produce a current twelve-motor motherboard complete package estimate. `:61` and `:128` correctly keep complete installed-display cost unknown.

**Decisive gate:** preserve the dated 144-case study, and later create a versioned current basket for the all-twelve motherboard × exact compute × exact screen/package × quantities 1/10/100/1,000. Carry unpriced parts, modules, enclosure, PSU/harness, assembly/programming/test, yield/warranty/support and physical replacement cost explicitly. No refreshed prices or vendor quotes were fetched in this audit. Current partial priced parts alone remain US$1,091.51/$877.37/$796.51 at 1/10/100, with 185 exact MPNs/720 fitted pieces unpriced (`docs/BUILD_PLAN.md:23` as inspected); they are neither total manufacture cost nor selling price.

### PS-08 — P2: manufacturing manifest consistency is not a machine-readable product acceptance gate

`tools/check_release.py:17–26` requires 17 prototype and 23 production artifacts. It checks hashes/revisions/reviewer fields and specific quotation structure; `:156` explicitly says it cannot establish evidence's physical truth, and `:239` returns readiness from its blockers. Product requirements G09–G21, including novice setup, display packages, offline service/licensing and common-service parity, are only indirectly represented by broad `system_integration_test`/`software_validation` artifacts. The checker does not consume a per-product-gate result schema or assert all required setup/AI/display cases exist.

The fresh read-only production check remained blocked with 23 entries. This is correct; no current false ready result was observed. The hardware/readiness workstream retains the authoritative release-check captures for this audit.

**Decisive gate:** add explicit product gate IDs, exact configuration/revision, evidence class, test method, result and accepted limitations to a machine-readable acceptance register. Map them to release artifacts and refuse incomplete/unknown gates for the actual offered package. Keep the manufacturing checker honest as a manifest-consistency tool; never treat a hash-valid generic document as proof of successful customer commissioning or AI correctness.

## Evidence and work performed

This workstream performed source/document inspection; read-only CLI help and capability/schema calls; a read-only release-manifest check; and the isolated host mock reproduction above. The CLI reported `urn:controller:disconnected-config:1`, `virtual-baseline-6j-2enc`, six virtual motors, sixteen virtual inputs, no motion commands and the two simulation profiles. No store was initialized and no configuration was applied.

The pre-existing regression counts cited in engineering status remain historical retained evidence. This workstream did not rerun the full suite, compile target firmware, run LinuxCNC, simulate HDL, synthesize an FPGA, run ERC/DRC, launch the external UI, touch routing or make physical measurements. A parser probe is not hardware qualification. The new setup/AI acceptance design from the main audit must likewise remain labeled unimplemented until its evidence exists.

Recommended next implementation order is PS-02's common service/model slice, PS-04's deterministic guided workflow, then PS-03's grounded optional assistant around that same service. PS-01 is a mandatory exclusion/regression test for any reference-UI reuse. Recovery and update contracts should be designed with the profile schema now so that first setup does not create data that cannot later be serviced offline.
