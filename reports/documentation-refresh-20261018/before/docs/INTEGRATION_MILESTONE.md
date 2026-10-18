# Connect the existing controller pieces

28 September 2026. The user's [integration-priority note](../research/user-notes/2026-09-28-integration-priority.txt) sets the next milestone: actual LinuxCNC commands must pass through our CNC1 protocol to the FPGA implementation, return meaningful feedback and produce the defined response when the connection fails. Use the existing six-step/two-encoder implementation to establish this connection before expanding it. Keep the preferred eight/four candidate and all screen tiers in their separate design/cost studies.

This is the acceptance contract. Completed execution evidence belongs in the component reports and [engineering status](../reports/ENGINEERING_STATUS.md); a proposed row below is not a passed test.

**First functional connection achieved:** the [CNC1 integration report](../reports/CNC1_INTEGRATION.md) records actual LinuxCNC → compiled HAL/common driver → actual simulated RTL → returned pulse-count feedback, including movement/reversal, varying ABZ/index and link-loss handling without automatic restart. The [configuration demo](../reports/CONFIGURATION_DEMO.md) works independently through its shared file-only service. The [compute/display matrix](../research/COMPUTE_DISPLAY_MATRIX.md) adds exact sourcing candidates across all requested screen classes. A later [persistent runtime implementation](../reports/PERSISTENT_RUNTIME.md) now binds the implemented XYZ-scale subset to actual LinuxCNC/compiled HAL/RTL across restarts. The complete machine-profile/cartridge schema and physical transport remain separate unfinished integrations.

## Motion integration boundary

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

## Six/two acceptance cases

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

A new capability page or protocol version needs explicit framing, compatibility, reserved-field and invalid-response tests. Preserve the original v1 evidence as history; rerun affected RTL checks when source changes. Keep expanded eight/four support unadvertised until that implementation and its tests exist.

## One configuration service

The first executable configuration slice is explicitly disconnected simulation. It must demonstrate profile selection, resource conflict detection, wiring guidance, validation/diff, disarmed/stopped apply, backup and restore through one callable service and CLI. It cannot claim real machine commissioning or infer physical disarmed state from editable files.

Use versioned device records with identity/revision, electrical capabilities, available functions, required connections, calibration status, compatible profiles, permitted commands, startup/loss behavior and required commissioning checks. Record observed identity separately from selected downstream equipment and verified wiring/calibration. Identifying a USB serial adapter does not identify or authorize the VFD behind it.

Reject unknown fields/resources, incompatible capability/rating assignments, duplicate exclusive resources, malformed backups and stale configuration revisions. Validate again at apply; save a recoverable prior state; use atomic persistence. Restoring configuration does not restore motion permission or completed physical checks. The future UI and assistant call the same validation/transaction functions rather than reimplementing them.

## Parallel compute, carrier and display comparison

Maintain exact CM4, CM5 and CB2 candidates with a used-pin/function matrix: power/reset/recovery, display/touch, Ethernet/service USB, dedicated FPGA link, reproducible Linux image and loaded operation. A connector fit is neither electrical nor software compatibility. Avoid paying for unrelated host peripherals unless a product requirement justifies them. Computer connector pins do not set FPGA-controlled machine terminal capacity.

The [display tiers](DISPLAY_TIERS.md) remain 7/10/12/14/18/21-inch classes and additional qualified options. Compare exact compute/carrier alternatives at the same screen and I/O scope, then compare packages. Include protection, connectors, storage, thermal hardware, power, PCB/assembly, programming/test, screen integration, enclosure, packaging and procurement costs at 1/10/100/1,000 units. Record source dates, exact variants and unknowns. No manufactured total exists while required blocks are unpriced.

## After software integration

Continue pin/power and target-driver feasibility alongside costing. The later bounded physical link prototype must measure actual SPI signals, emitted pulses, encoder input, loaded servo-cycle timing and deliberate loss/reset/inhibit behavior before final production layout. Include the local UI, representative CAD workload, storage/network load and enclosure thermal conditions. The correct response to a successful software simulation is that a functional connection has been demonstrated; physical timing, electronics and machine qualification remain separate gates.

No orders, physical connections or manufacturer submissions are authorized by this milestone. The existing PCBWay turnkey route remains the manufacturing plan after design and review.
