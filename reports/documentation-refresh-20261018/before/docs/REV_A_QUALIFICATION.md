# Rev A software baseline and qualification

**Later 4 October user extension:** the user expressly requests our own polished OS experience and preinstalled image/setup. [Controller OS](CONTROLLER_OS.md) is the authorized frontend/image addition to the preceding feature freeze; other roadmap features remain deferred. [Current deeper SIM2 evidence](../reports/deeper-runtime-20261004/README.md) now passes actual twelve- and eight-joint FREE-planner integration with all twelve fitted. This does not qualify Cartesian machining, physical homing/acquisition, loaded RT timing, a bootable/signed target OS or Efinity device fit/timing. The earlier refusal-only report below remains historical and source-bound.

The user's 4 October 2026 decision freezes new user-facing features. The current
setup, readiness, recovery, diagnostics, accounting and dark/red workbench are
the Rev A software feature baseline. Integration, defect correction, test
expansion and qualification are the current work. A frontend change requires a
demonstrated usability defect; roadmap features remain deferred.

The baseline is the [applied upgrade](../reports/deep-upgrade-20261004/README.md),
with its exact source/test receipts. New integration evidence belongs in
[one current gap report](../reports/rev-a-integration-20261004/README.md).
`tools/check_rev_a_baseline.py` captures and verifies byte preservation of the
frontend/service, retained regression tests, hardware/gateware/firmware sources,
the preserved external interface source and existing preview settings. Its PASS
means only that those bytes match; it does not execute or qualify a machine.
Evidence is written exclusively to new files, leaving historical receipts intact.

## Required next milestone

Exercise one continuous, source-bound path:

`LinuxCNC/HAL → CNC3 host driver → actual CNC3 serial transport → current FPGA RTL → virtual machine → encoder/limit/alarm feedback`

The same execution must cover all twelve motor channels simultaneously, four
ABZ encoders, 24 general DI, 16 general DO, probe/limit feedback, watchdog and
fault handling. Commanded motion, emitted STEP/DIR, encoder measurements and
reported state need separate observations. Refusal/stop/restart tests must prove
that missing or stale authority cannot be turned into permission. A capability
flag must describe implemented providers; it cannot be changed to make a host
driver accept an incomplete endpoint.

Historical six-joint/two-encoder CNC1 runtime, twelve-joint module loading,
isolated generator/encoder sweeps, structural CNC3 frame checks, read-only IOL1
replay and report-local stateful motion candidates remain separate evidence.
Passing these separately does not complete the continuous milestone. A new
simulation adapter/candidate is labelled as such until adopted and qualified.
Integrated motherboard regions do not acquire invented card-presence signals.
The frozen 96-byte command/176-byte feedback protocol and real limits remain
unchanged.

## Evidence classes

| Class | Required interpretation |
|---|---|
| SOFTWARE PASS | Exact-source executed host/HAL/service checks, with skips and refusal paths named. Compile/link is separately identified. |
| FPGA PASS | Actual-target Efinity synthesis, placement, routing and static timing, bound to the complete source, exact device/package, pin/bank assignment and clock/I/O constraints. Generic Yosys mapping is a separate screen. No FPGA PASS is claimed without this evidence. |
| SIMULATION PASS | Executed compiled RTL/transport/virtual-machine checks, with authored provider assumptions, included channels and missing integration boundaries named. |
| PHYSICAL VALIDATION REQUIRED | Live acquisition; actual MCU/FPGA execution; loaded LinuxCNC/transport timing; watchdog/inhibit propagation; electrical output limits, analog accuracy, thermals and brownout/power-fail; prototype and commissioned-machine tests. |

Simulation does not promote commissioning, safety, manufacturing readiness,
physical ratings or motion permission. Current diagnostic firmware compilation
needs current-source C/HDL replay and later target measurements. Vendor timing
needs the actual complete design, not a component top or a resource estimate.

Claude owns ROOT105/routing. This qualification work does not edit, adopt or
declare that routing complete. Source26/ROOT104/CAD30 remains the last verified
adopted board until exact new adoption evidence is supplied. Finishing routing,
vendor timing and physical build/qualification are distinct gates.
