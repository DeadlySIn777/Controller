# Rev A software baseline and qualification

**Reviewed 18 October 2026.** [Documentation index](README.md) · [Current engineering status](../reports/ENGINEERING_STATUS.md). [The current continuation record](../reports/board-finish-20261017/README.md) now includes fresh actual eight-/twelve-joint LinuxCNC/HAL/C/SPI/selected-RTL/virtual-feedback runs and reversible adoption of the three verified SIM2 resource fixes. The canonical disconnected core maps at 15,805 LUT4 + 2,107 ADD = 17,912, with 10,441 FF, 63 RAM5K and one multiplier. Its 256 records, seven simultaneous producers, buffers and fitted functions/limits are retained. Complete physical-wrapper fit, place/route/static timing and machine qualification remain open.

**Later 4 October user extension:** the user expressly requests our own polished OS experience and preinstalled image/setup. [Controller OS](CONTROLLER_OS.md) is the authorized frontend/image addition to the preceding feature freeze; other roadmap features remain deferred. [Current deeper SIM2 evidence](../reports/deeper-runtime-20261004/README.md) now passes actual twelve- and eight-joint FREE-planner integration with all twelve fitted. This does not qualify Cartesian machining, physical homing/acquisition, loaded RT timing, a bootable/signed target OS or Efinity device fit/timing. The earlier refusal-only report below remains historical and source-bound.

The user's 4 October 2026 decision freezes new user-facing features. The current
setup, readiness, recovery, diagnostics, accounting and dark/red workbench are
the Rev A software feature baseline. Integration, defect correction, test
expansion and qualification are the current work. A frontend change requires a
demonstrated usability defect; roadmap features remain deferred.

The baseline is the [applied upgrade](../reports/deep-upgrade-20261004/README.md),
with its exact source/test receipts. The [original qualification gap report](../reports/rev-a-integration-20261004/README.md)
retains the earlier refusal-only scope. Read subsequent execution in [deeper runtime](../reports/deeper-runtime-20261004/README.md)
and the [current continuation](../reports/board-finish-20261017/README.md); do not restamp older receipts as current.
`tools/check_rev_a_baseline.py` captures and verifies byte preservation of the
frontend/service, retained regression tests, hardware/gateware/firmware sources,
the preserved external interface source and existing preview settings. Its PASS
means only that those bytes match; it does not execute or qualify a machine.
Evidence is written exclusively to new files, leaving historical receipts intact.

## Continuous integration evidence and remaining qualification

The current disconnected FREE-joint runs exercise this source-bound path:

`LinuxCNC/HAL → CNC3 host driver → actual CNC3 serial transport → current FPGA RTL → virtual machine → encoder/limit/alarm feedback`

Production qualification must retain all twelve motor channels simultaneously, four
ABZ encoders, 24 general DI, 16 general DO, probe/limit feedback, watchdog and
fault handling. Commanded motion, emitted STEP/DIR, encoder measurements and
reported state need separate observations. Refusal/stop/restart tests must prove
that missing or stale authority cannot be turned into permission. A capability
flag must describe implemented providers; it cannot be changed to make a host
driver accept an incomplete endpoint.

Historical six-joint/two-encoder CNC1 runtime, twelve-joint module loading,
isolated generator/encoder sweeps, structural CNC3 frame checks, read-only IOL1
replay and report-local stateful motion candidates remain separate evidence.
Passing these separately did not complete the continuous milestone. The later
SIM2 runs close the exercised disconnected FREE-joint path, including its explicit
virtual providers; they do not close coordinated machining, physical acquisition,
homing, full target timing or commissioned-machine acceptance. A new
simulation adapter/candidate is labelled with its exact adoption and qualification scope.
Integrated motherboard regions do not acquire invented card-presence signals.
The frozen 96-byte command/176-byte feedback protocol and real limits remain
unchanged.

## Evidence classes

| Class | Required interpretation |
|---|---|
| SOFTWARE PASS | Exact-source executed host/HAL/service checks, with skips and refusal paths named. Compile/link is separately identified. |
| FPGA PASS | Actual-target Efinity synthesis, placement, routing and static timing, bound to the complete source, exact device/package, pin/bank assignment and clock/I/O constraints. The executed 17,912-LUT4+ADD functional SIM2 map and separate 135-pin/seven-bank interface check are vendor evidence within narrower scopes; neither is complete physical-wrapper fit/timing or FPGA PASS. Generic Yosys mapping is a separate screen. |
| SIMULATION PASS | Executed compiled RTL/transport/virtual-machine checks, with authored provider assumptions, included channels and missing integration boundaries named. |
| PHYSICAL VALIDATION REQUIRED | Live acquisition; actual MCU/FPGA execution; loaded LinuxCNC/transport timing; watchdog/inhibit propagation; electrical output limits, analog accuracy, thermals and brownout/power-fail; prototype and commissioned-machine tests. |

Simulation does not promote commissioning, safety, manufacturing readiness,
physical ratings or motion permission. Current diagnostic firmware compilation
needs current-source C/HDL replay and later target measurements. Vendor timing
needs the actual complete design, not a component top or a resource estimate.

Claude's external ROOT105/ROOT106 routing work remains distinct from this software qualification.
The current isolated R299 continuation is documented in the 17 October report;
Source26/ROOT104/CAD30 remains the verified adopted board baseline. Finishing routing,
vendor timing and physical build/qualification are distinct gates.
