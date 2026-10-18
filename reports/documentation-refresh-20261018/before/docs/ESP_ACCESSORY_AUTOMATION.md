# ESP32 accessory automation and condition monitoring

28 September 2026. The user's [latest direction](../research/user-notes/2026-09-28-esp-industrial-direction.txt) gives the ESP32 a substantial supporting-equipment role. This extends the product requirements. **Current ESP32-S3 firmware remains read-only diagnostics:** it configures no accessory output, reset or motion pin. Its existing ESV1 diagnostic frames are not an actuator-command protocol or verified service-readiness channel.

## Responsibilities and ownership

| Layer | Responsibility |
|---|---|
| LinuxCNC and main machine logic | Program execution, coordinated motion, spindle synchronization and motion-dependent sequences; decide whether required services permit the operation |
| FPGA | Precisely timed pulses, encoder/event capture, validated update acceptance and hardware command timeout; exact implemented scope remains versioned |
| ESP32 accessory service | Approved auxiliary state machines, selected direct sensor measurements, readiness/fault reporting, diagnostics and service access |
| Independent hardware | Reviewed output defaults, power supervision, watchdog/inhibition and interfaces to the machine's separate safety system |

Assign exactly one execution owner to each output. LinuxCNC may request an ESP-owned coolant sequence but must not also drive its relay through another route. The resource registry, wiring plan and FPGA/ESP pin maps must reject duplicate ownership. Motion/torch firing, drawbar release, workholding release, brake release and toolchanger sequencing are not autonomous ESP sensor actions; they require the machine's specific control and protection design.

The controller stays local: a wireless session, browser or AI is not required to execute a qualified accessory sequence. Ordinary timers, thresholds and state machines perform these functions. AI can explain evidence through the common service; it cannot replace missing feedback or override a machine fault.

## Candidate services

| Service | Request and observation | Policy that must be qualified |
|---|---|---|
| Cabinet fans | Requested cooling level; temperature, tachometer and sensor health | Approved bounded after-run cooling; define behavior if host, ESP, sensor or supply fails |
| Coolant/air supply | Prepare/stop request; flow/pressure/level with units, age and quality | Ready only after valid conditions persist for the configured qualification time; start timeout, loss threshold and restart procedure |
| Lubrication | Approved timed/usage cycle; level, delivery/pressure and consumption evidence | Bound maximum cycle/duty; prevent duplicate delivery after replay/reboot; required-delivery failure affects the permitted job |
| Work lights/extraction | Approved request and available contact/flow/status feedback | Distinguish advisory indication from an operation-critical extraction requirement |
| Electrical/thermal health | Direct supply/temperature measurements and supervisor/protection flags | Name the failed domain and measurement quality; no claim of independent observation when only relaying a Linux flag |

These are candidate services, not allocated pins or fitted sensors. Sensor ranges, isolation, conditioning, threshold tolerances, calibration and failure diagnostics belong in the BOM and device profile. A signal above threshold is not proof of correct sensor wiring or actual delivery without suitable commissioning and plausibility checks.

## Request, confirmation and loss semantics

Use a new, versioned **wired** accessory interface. It must bind controller/ESP boot identities, session, device/configuration revision, command sequence, requested action and expiry. Define bounded queues, transport latency, monotonic freshness, acknowledgment and replay rejection. CRC alone is not authentication or freshness; the current ESV1 queue-age limitations make it unsuitable for authorizing an essential service.

A normal sequence is:

1. The main controller validates the selected machine/profile and requests `prepare` for the named service.
2. The ESP accepts only the current authorized request, enters `starting` and drives the one permitted output sequence.
3. Direct, valid sensor observations satisfy thresholds for a specified interval; the ESP reports `ready` with measurement, units, quality, sample age and request identity.
4. The main controller verifies current readiness before continuing the operation and monitors it while required.
5. Missing/invalid feedback, timeout or a contradictory condition moves the service to `fault` or `unavailable` as defined by its profile. Report readiness separately as `not_ready` when valid evidence disproves it, or `unknown` when the evidence is missing/invalid; a commanded-on output never substitutes for confirmed readiness.

Define service states `unavailable`, `off`, `starting`, `ready`, `stopping`, `after-run` and `fault`, with only applicable states enabled by a profile. Invalid transition requests fail explicitly. Commands cannot remain queued across reboot, reconnection or configuration replacement. Recovery clears a diagnosed fault only under the required stopped state; it never starts the job automatically.

If essential coolant loses confirmed flow, report the observable facts: pump requested on, measured flow below the minimum or measurement invalid, sample age, hold requested, stopped acknowledgment pending/received, and the remaining restart checks. Do not label the cause “failed pump” when a dry tank, blocked line or sensor fault has not been distinguished.

## Essential-service dependencies change fault policy

| Event | Required design response |
|---|---|
| ESP failure while only advisory diagnostics are used | Record lost diagnostics; follow the qualified machine policy without granting new motion authority |
| ESP/readiness link failure while an essential service is required | Readiness expires; main machine logic requests the defined response and blocks restart. Qualify maximum detection and response times for that machine/process. |
| Sensor disconnected, stuck or implausible | Report invalid/unknown readiness with the supported diagnostics; an old good sample cannot renew it |
| Linux unavailable | Stop accepting new requests. Execute only specifically qualified local after-run/failure behavior; independent hardware handles obligations that software can no longer guarantee. |
| ESP application frozen or ESP power lost | A firmware timer is insufficient. Independent circuitry and output defaults must implement the required failure behavior; continued cooling may require a separate default-on/hardware-controlled path. |
| Host requests controlled hold | Request is not proof of a stopped machine. Monitor backend acknowledgment and a bounded deadline; escalate through the machine-specific fault path if stopping fails. |
| Power returns or fault clears | New identities/freshness and deliberate recovery; no automatic pump cycle, motion, torch or spindle restart from old requests |

“Everything off” is not a universal machine response. Specify cooling, pressure/workholding, gravity-loaded axes and stored-energy behavior per machine. A software hold depends on a functioning executor; the FPGA's current permission removal is abrupt and cannot substitute for a qualified controlled stop.

## Hardware and implementation gates

Provide a separately protected, adequately sized ESP regulator branch and reviewed direct fault/sensor inputs. Shared upstream power, grounds and communication still create common failures; a separate regulator does not make the entire system independent. Size radio current transients, decoupling, reset/brownout and antenna placement together. Espressif's hardware guide discusses supply collapse during radio current transients and power monitoring. [ESP32-S3 hardware guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html)

Select an independent watchdog from actual timeout, fault-latch, power and output-gating requirements. A simple periodic GPIO toggle can conceal a stalled service state machine: monitor meaningful completion and design failure detection accordingly. TI's TPS3431 is one external-watchdog example, not a frozen part selection. [TPS3431](https://www.ti.com/product/TPS3431)

Before enabling accessory GPIO: define service criticality and responses; allocate/price exact circuits and sensors; implement the shared device configuration/authority contract; test state machines with simulated sensors/failures; then build and qualify a separately identified ESP firmware mode and bounded bench setup. Preserve the current diagnostic build as a usable baseline. Prove freeze, power loss, corrupt/stale feedback, stuck outputs, sensor faults, duplicate commands and restart behavior. Integrate required-service readiness into LinuxCNC only after these interfaces and response deadlines are defined.

This work follows the current CNC1 integration and configuration foundation; it does not insert another motion planner or delay that functional connection milestone.
