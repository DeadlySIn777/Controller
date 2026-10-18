# Rev A qualification and integration gaps — 4 October 2026

The current setup/readiness/recovery/diagnostics/accounting/dark-red UI is the
**frozen Rev A feature baseline**. This pass adds qualification evidence and a
disconnected HAL integration candidate. It does not add frontend features,
change machine settings or touch Claude's ROOT105/routing.

[Machine-readable gap register](../../WORKSPACE_REFERENCES.md#artifact-57f66a1b77ec2d54) binds the canonical host, RTL, vendor
and preservation receipts. Its independent recheck verifies **440 source and
artifact hashes**, with no mismatch. [Final byte-preservation verification](../../WORKSPACE_REFERENCES.md#artifact-e10dc54e3c799045)
passes for every captured group. [Independent review](../../WORKSPACE_REFERENCES.md#artifact-ad41e5782d4f1bf9)
records the final source/evidence boundaries and corrected runner failure controls.

[Documentary correction](../../WORKSPACE_REFERENCES.md#artifact-39e2850551fc7416) preserves the exact
original host report matching its sealed receipt's document hash, and binds
the current wording that explicitly names simulated RTL pins and the retained
IS-2-compatible C-host candidate. Execution/source receipts and outcomes are
unchanged. The [first independent review](../../WORKSPACE_REFERENCES.md#artifact-dc77c44d19038dae) remains historical;
the amended review binds this clarification rather than restamping old evidence.

**The requested complete twelve-channel milestone remains BLOCKED.** The real
CNC3 host requires a complete capability/provider contract. The report-local
motion candidate has twelve generators/four encoders but lacks CAP3 discovery;
the separate IS-2 CAP3 candidate explicitly marks its full profile incomplete
and reports no installed motion channels. Qualification must preserve that
refusal. Neither endpoint is an adopted, complete motherboard runtime.

## SOFTWARE PASS

- The 24 service/frontend baseline files exactly match the source pinned by the
  [last executed regression](../../WORKSPACE_REFERENCES.md#artifact-e242f50fde88d11e): **508
  passes, one Windows privilege skip, zero failures/errors**. That run is retained
  evidence, not a newly repeated 509-case run.
- [The preservation checker](../../WORKSPACE_REFERENCES.md#artifact-4c5ab94872e73f03) verifies those
  24 files, 3,308 main hardware/gateware/firmware/config/schema files, 20 preserved
  external CNC3/specification files, 21 existing preview/settings files and 20
  regression-test files. [Initial verification](../../WORKSPACE_REFERENCES.md#artifact-09c1f73262c14d28)
  passes. [Seven executed negative controls](../../WORKSPACE_REFERENCES.md#artifact-0beac726fe2326fc)
  reject changed expected hashes, existing-output overwrite and an output path
  outside reports. Actual source/settings are never mutated by those controls.
- [Current diagnostic replay](../../WORKSPACE_REFERENCES.md#artifact-c2a5999b39bd37bd) executes **5,441
  C checks** and compile/links **DIC, DOA, DOB and ACC ARM targets**. Target
  execution and physical timing remain untested.
- [New report-local HAL integration](../../WORKSPACE_REFERENCES.md#artifact-d9d08fa053a1291c) passes **six executed
  cases/124 assertions** using the actual LinuxCNC 2.9.4 HAL scheduler, retained
  IS-2-compatible C-host candidate and actual serial RTL pins. Twelve commands,
  twelve feedback outputs, twelve independent simulated STEP monitors and four
  encoder pins are exported. The incomplete profile produces a bounded
  qualification refusal; reset/enable cannot bypass it. CRC-corrupted feedback,
  unavailable resources, unchanged IS-1 driver incompatibility and absent
  simulation opt-in also refuse. No CONFIGURE/ARM/UPDATE or STEP edge/authority
  is observed. This is an executed inhibited path, with no trajectory planner,
  ACTIVE motion or valid encoder feedback.
- All 38 HAL-run input hashes remain unchanged, seven original C/H copies match
  the external archive, and **183 existing rootfs modules** are restored byte
  for byte. Independent review reproduced a partial-install cleanup defect;
  the corrected runner restores after partial failures and publishes completed
  modules atomically without replacement. [Four executed inert Linux failure
  controls](review/module-install-corrected-controls.json) pass. Earlier failed
  build/runner attempts and the pre-correction pass remain preserved; final
  `host/run-r06` binds the corrected current sources.

## FPGA PASS

**BLOCKED — no FPGA vendor PASS is claimed.** Current motherboard source selects
`T20F256I4`; historical C4 prose is not the present target identity. Efinity and a
qualified complete-design vendor project/pin-bank/timing flow have not been
demonstrated in this environment.

[Vendor audit and exact unblocking steps](vendor/README.md) record the actual
tool-search scope/errors, all 256 native balls, source bank/rail/function ledger
and clock evidence. Entitlement remains not demonstrated. These are source
observations, without applied vendor pin/timing legality or physical proof.

[Fresh structural Efinix-family mapping](../../WORKSPACE_REFERENCES.md#artifact-cafdc4f979a25ace)
is a **generic synthesis screen only**. Its top contains large internal parallel
buses and is not the complete pin-ready motherboard top. It cannot qualify
actual-device capacity, placement, routing, timing or a bitstream.

## SIMULATION PASS

| Executed evidence | Result | Boundary |
|---|---|---|
| [Current structural CNC3 C/RTL/SPI](../../WORKSPACE_REFERENCES.md#artifact-d62b9e65de143499) | 743 C-oracle cases; actual serial checks and rejection cases pass | Frozen 96/176 frames, structural validation/packing; no stateful motion or HAL proof |
| [Current C ↔ HDL diagnostic replay](../../WORKSPACE_REFERENCES.md#artifact-c2a5999b39bd37bd) | 78 watchdog/progress/failure checks pass | Four real compiled C diagnostic peers; historical six/two bringup wrapper; GPIO fixtures and all output authority LOW |
| [Twelve-generator timing](../../WORKSPACE_REFERENCES.md#artifact-f3d576021bf9f7e3) | Original-algorithm equivalence and dynamic drain/reversal pass | Twelve instances in compiled RTL; component evidence |
| [Four ABZ/filter checks](../../WORKSPACE_REFERENCES.md#artifact-4ea090660faec98b) | Position/filter/illegal-transition checks pass | Base four algorithms; no completed index one-shot/event path or physical receiver qualification |
| [Actual serial twelve-output/four-encoder plant](../../WORKSPACE_REFERENCES.md#artifact-38b8cca8031d0b2e) | All 18 retained scenarios pass | Real compiled serial/state/generator/encoder RTL with ideal mechanics; no actual LinuxCNC task/HAL integration, general I/O authority or probe/limit event acquisition |
| [Individual channel faults and unsupported functions](../../WORKSPACE_REFERENCES.md#artifact-34bc1119b9d2429f) | 22 cases pass: 12 alarms, four encoder losses, six unsupported commands | All twelve actual simulated STEP channels emit before each injection. Six DO/probe/index/PWM/I/O requests are structurally valid in the frozen C oracle and refuse at the stateful boundary; DI/AI remains unavailable |

[Motion-source provenance](../../WORKSPACE_REFERENCES.md#artifact-681df7bcfd80ff0e) identifies the
unchanged report-local stateful candidate and current frozen-protocol validator.
Its authored legacy qualification signals are logical simulation fixtures, not
IS-2 soldered-region/card discovery or evidence of actual modules. Commanded
motion, actual simulated STEP edges and virtual encoder position remain distinct.
General DI/AI observations remain unavailable; general DO/process authority is
not completed. Home/limit/probe values computed by ideal mechanics do not prove
that an FPGA acquisition path consumed them.

## PHYSICAL VALIDATION REQUIRED

**No physical measurements or device connections occur in this pass.** Physical
commissioning, safety and manufacturing readiness remain unchanged and open.
The next hardware evidence must cover live acquisition, actual firmware/FPGA
execution, loaded target transport/servo timing, independent watchdog/inhibit
propagation, output current limits, analog accuracy, thermals and brownout/
power-fail behavior. Simulation cannot qualify the 20 ms electrical inhibit
requirement, 2 MHz/channel product target or a physical touchscreen/machine.

The required order is: complete the versioned IS-2 runtime/provider integration;
prove the whole twelve-channel virtual machine through the unmodified host
guards; run the actual complete-design Efinity flow; finish and independently
verify Claude's routing/adoption; build and qualify hardware. Signed updates,
replacement provisioning, discovery and novice/paid-model studies remain open
product gates; they do not authorize more frontend features during this freeze.

Historical six-joint/two-encoder CNC1 results and previous report-local receipts
remain preserved. Passing independent component runs is never added together to
claim the continuous milestone. [Qualification policy](../../docs/REV_A_QUALIFICATION.md)
records this distinction and the feature freeze.

The first boundary fixture incorrectly required motion `permit_out_req` LOW
while armed. Its failed [r01 receipt](../../WORKSPACE_REFERENCES.md#artifact-9c2d506f9d8221b5)
remains preserved; the corrected test checks general-I/O request/progress and
independently decodes fault feedback. All eight RTL hashes match between those
runs. This was a test correction, with no production source edit.
