# Connect the existing controller pieces

**Reviewed 18 October 2026.** [Documentation index](README.md) · [Current engineering status](../reports/ENGINEERING_STATUS.md). The current disconnected integration is actual LinuxCNC task/NML/FREE-joint planners → HAL → compiled CNC3 C driver → serial SPI → selected current SIM2 RTL → independent virtual STEP/DIR feedback. [Fresh twelve- and eight-joint executions](../reports/board-finish-20261017/README.md) pass with all twelve interfaces fitted. Four ABZ and the I/O/fault providers retain their declared authored simulation assumptions; this is not physical discovery, coordinated Cartesian/G-code machining or homing qualification.

The verified registered RAM/prefetch bypass, seven-producer event FIFO and command-alignment changes are applied reversibly to canonical disconnected SIM2. The full functional core maps at **15,805 LUT4 + 2,107 ADD = 17,912**, with 10,441 FF, 63 RAM5K and one multiplier. The original 256-event capacity, seven simultaneous producers, protocol buffers, fitted functions and limits remain intact. Actual mapped-event vendor-primitive comparisons and fresh LinuxCNC runs cover the selected implementation. Core mapping and the separate 135-pin/seven-bank vendor interface check leave the complete physical wrapper, place/route, static timing and physical measurements open. Production adoption remains false.

**Historical starting milestone, 28 September 2026.** The user's [integration-priority note](../WORKSPACE_REFERENCES.md#artifact-fafb7925e0eff029) first requested LinuxCNC commands through CNC1 into the six-step/two-encoder FPGA implementation, meaningful feedback and link-failure behavior. That connection was achieved below. The later adopted base is one active motherboard with all twelve motor interfaces, four ABZ, 24 general DI and 16 smart DO; an eight-motor fixture is no longer a proposal to omit fitted motors 9–12. Display tiers remain independent of this capacity.

This is the acceptance contract. Completed execution evidence belongs in the component reports and [engineering status](../reports/ENGINEERING_STATUS.md); a proposed row below is not a passed test.

**Historical first functional connection:** the [CNC1 integration report](../reports/CNC1_INTEGRATION.md) records actual LinuxCNC → compiled HAL/common driver → actual simulated RTL → returned pulse-count feedback, including movement/reversal, varying ABZ/index and link-loss handling without automatic restart. The [configuration demo](../reports/CONFIGURATION_DEMO.md) is its independent shared file-only service. The [compute/display matrix](../research/COMPUTE_DISPLAY_MATRIX.md) retains dated sourcing candidates. The [persistent runtime implementation](../reports/PERSISTENT_RUNTIME.md) binds only its historical XYZ-scale subset across restarts. The current [setup workbench](SETUP_WORKBENCH.md) and [appliance](CONTROLLER_OS.md) share the newer simulation service; complete production machine-profile/cartridge/runtime authority and physical transport remain unfinished.

## Historical CNC1 integration boundary

```text
Touchscreen / CLI / assistant
             |
      operator service
             |
        LinuxCNC motion
             |
      compiled HAL read/write
             |
   common CNC1 codec and state
             |
   replaceable transport backend
       /          |          \
 RTL simulation  Pi SPI   Rockchip SPI
  software proof   future qualified targets
```

The common driver owns frame validation, capability checks, units/scaling, counter wrap handling, command/acknowledgment state, deliberate session recovery and fault latching. Target backends own their specific bus transaction and timing implementation. Ordinary Python operator/configuration code stays outside cyclic motion. A simulator backend must identify itself and never acquire physical-device access.

LinuxCNC's documented `hm2_spix` design has dedicated Raspberry Pi implementations and a generic fallback, with other board/configuration combinations requiring testing. It does not implement our CNC1 protocol; its separation of common behavior and board-specific transport is relevant to this design. LinuxCNC documents Python HAL components as non-real-time and provides compilation support for C components. These upstream facts establish a development route, not qualification of our driver. [hm2_spix](https://linuxcnc.org/docs/html/man/man9/hm2_spix.9.html), [component compilation](https://linuxcnc.org/docs/html/hal/comp.html), [Python HAL components](https://linuxcnc.org/docs/html/hal/halmodule.html)

Use separate read and write functions around the relevant LinuxCNC motion calculations. Respect the protocol's response snapshot: a command's own transaction cannot acknowledge the state it changes at transaction end. Do not use the return of a transport call as evidence that an ARM or UPDATE was accepted.

FPGA-generated pulse counts, external encoder counts and commanded position are different signals. Closing a simulated step-generation loop with emitted counts exercises the driver but does not prove motor position, drive acceptance or a physical servo loop.

## Historical six/two acceptance cases

| Case | Required evidence |
|---|---|
| Discovery | Read version, implemented step/encoder counts and supported functions from the endpoint. Unsupported frequency/analog/process features remain absent. Reject an incompatible version or capability layout before enabling. |
| Actual command path | A real LinuxCNC program produces commands through compiled HAL and CNC1 into actual simulated RTL. Returned generated counts affect the simulated feedback path; command-to-feedback loopback cannot substitute for this. |
| Scaling and direction | Positive/negative commands and multiple scales match returned counts within specified quantization/timing tolerance. Reject non-finite or out-of-range configuration/commands. |
| Counter wrap and reset | Verify modulo counter/timestamp wrap arithmetic and discontinuity detection. Endpoint reset creates a new recovery requirement, not an apparently valid wrap. |
| Coherent update | Multiple affected channels accept the same validated command sequence; no half-update becomes active. |
| Spindle feedback | Drive varying quadrature speed and index pulses into RTL, return counts/index through CNC1 and verify direction, scale and index behavior. This alone does not qualify threading or rigid tapping. |
| Invalid traffic | Bad CRC, reserved fields, stale sequence, wrong session and malformed/truncated traffic cannot become a new motion command. Corrupted or stale responses latch host failure. |
| Missing traffic | Lost updates exercise the endpoint watchdog and host fault handling. Record the stop/inhibit behavior accurately: permission removal is not controlled deceleration. |
| Restart/reconnect | Returning traffic, a restarted component and a held-high enable request cannot automatically restore motion. Require the defined stopped/disarmed recovery, fresh session and deliberate enable. |
| Bounds of proof | Record code/tool versions, exact profile, source hashes, commands, logs, assertions and simulated versus wall-clock timing. Preserve failures until explained; do not infer physical deadlines from WSL simulation. |

A new capability page or protocol version needs explicit framing, compatibility, reserved-field and invalid-response tests. Preserve original v1 evidence with its exact sources. The newer eight-/twelve-joint/four-ABZ SIM2 implementation has executed disconnected tests, separately from this CNC1 table. Advertise only that tested simulation scope; physical expanded support still requires full implementation and qualification.

## One configuration service

The first executable configuration slice is explicitly disconnected simulation. The current workbench implements profile selection, resource conflict detection, illustrative wiring, validation/diff, inhibited transactions, backup and restore through one callable service, CLI and UI. It cannot claim real machine commissioning or infer physical disarmed state from editable files.

Use versioned device records with identity/revision, electrical capabilities, available functions, required connections, calibration status, compatible profiles, permitted commands, startup/loss behavior and required commissioning checks. Record observed identity separately from selected downstream equipment and verified wiring/calibration. Identifying a USB serial adapter does not identify or authorize the VFD behind it.

Reject unknown fields/resources, incompatible capability/rating assignments, duplicate exclusive resources, malformed backups and stale configuration revisions. Validate again at apply; save a recoverable prior state; use atomic persistence. Restoring configuration does not restore motion permission or completed physical checks. The implemented UI and optional review-only assistant adapter use the same validation/transaction service. Production identity, telemetry and physical commissioning must preserve that contract.

## Parallel compute, carrier and display comparison

Maintain exact CM4, CM5 and CB2 candidates with a used-pin/function matrix: power/reset/recovery, display/touch, Ethernet/service USB, dedicated FPGA link, reproducible Linux image and loaded operation. A connector fit is neither electrical nor software compatibility. Avoid paying for unrelated host peripherals unless a product requirement justifies them. Computer connector pins do not set FPGA-controlled machine terminal capacity.

The [display tiers](DISPLAY_TIERS.md) remain 7/10/12/14/18/21-inch classes and additional qualified options. Compare exact compute/carrier alternatives at the same screen and I/O scope, then compare packages. Include protection, connectors, storage, thermal hardware, power, PCB/assembly, programming/test, screen integration, enclosure, packaging and procurement costs at 1/10/100/1,000 units. Record source dates, exact variants and unknowns. No manufactured total exists while required blocks are unpriced.

## After software integration

Continue pin/power and target-driver feasibility alongside costing. The later bounded physical link prototype must measure actual SPI signals, emitted pulses, encoder input, loaded servo-cycle timing and deliberate loss/reset/inhibit behavior before final production layout. Include the local UI, representative CAD workload, storage/network load and enclosure thermal conditions. The correct response to a successful software simulation is that a functional connection has been demonstrated; physical timing, electronics and machine qualification remain separate gates.

No orders, physical connections or manufacturer submissions are authorized by this milestone. The existing PCBWay turnkey route remains the manufacturing plan after design and review.
