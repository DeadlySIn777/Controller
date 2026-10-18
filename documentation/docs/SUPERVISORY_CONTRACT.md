# Proposed supervisory contract

**Reviewed 18 October 2026.** [Documentation index](README.md) · [Current engineering status](../reports/ENGINEERING_STATUS.md). This original offline model remains a separate evidence class. The implemented shared setup service and [Motion X12 application/kiosk recovery](CONTROLLER_OS.md) do not implement its authenticated machine-command authority or prove motion continuity. [Current eight-/twelve-joint SIM2 runtime](../reports/board-finish-20261017/README.md) has its own tested session/watchdog/fault semantics and virtual providers; do not treat this model's example clocks as its deployed limits.

Version 1; offline behavioral model, not a transport, firmware or safety implementation. Reference: `controller_lab/supervisor.py`; message shape: `schemas/control-envelope.schema.json`.

## Ownership

One local motion backend owns actuator timing. One authenticated operator session at a time may request state changes. The service/authentication layer is assumed by this model and still needs implementation. Observers may eventually watch without acquiring command authority.

A browser or ESP must use the same checked request boundary. Neither a wireless connection nor a recovery processor may bypass a latched fault, inject GPIO pulses, or claim that the machine has homed. A reset and a new connection never mean resume.

## Command envelope

| Field | Meaning |
|---|---|
| `version` | Exact contract version, currently 1 |
| `boot_id` | Controller-issued identity that changes on reboot |
| `session_id` | Authority lease returned by `connect()`; unique per boot (reuse is refused). Production must have the controller mint it; the reference model also accepts a caller-supplied string as a test seam, as `reboot()` does for `boot_id` |
| `sequence` | Strictly increasing 32-bit unsigned value; no wrap in a session |
| `deadline_ms` | Expiry in the controller clock, bounded by its granted lease |
| `action` | `heartbeat`, `arm`, `start`, `hold`, `resume`, or `disarm` |

The model rejects missing/extra fields, malformed types, stale boot/session identities, expired or ungranted deadlines and duplicate/reordered sequences. A fresh valid envelope consumes its sequence even when the requested action is refused. A previously refused `start` therefore cannot become valid merely because conditions improve later.

Production transport still needs authenticated pairing, message-size limits, connection admission, version negotiation, persistence boundaries, telemetry timestamps and a robust clock/lease exchange. Hashes establish identity/integrity; they are not authentication.

## States

| State | Behavior in this model |
|---|---|
| Disarmed | No enable or motion request; staging and qualification allowed |
| Ready | Enable requested if physical inputs permit; a job can start after backend acceptance and position qualification |
| Running | Local backend executes; the HMI does not generate pulse timing |
| Hold requested | Deceleration requested; machine is not assumed stopped |
| Held | Backend has acknowledged stopped; a new explicit request is required to resume |
| Fault | Logical output requests withdrawn; authority and position qualification invalidated |

Logical enable withdrawal does not model brake sequencing, gravity-loaded axes, stored energy, a physical safety circuit or the actual state of a motor drive. Those belong to a machine-specific design and validation.

## Job and position qualification

Staging accepts bytes within a configured size limit and checks SHA-256. It does not parse G-code. A separate local backend must attest that the specific staged digest is accepted. Replacing a job invalidates that acceptance; replacement while running or held is prohibited.

Likewise, `report_position_trusted()` is a local injected event, not a homing procedure. Production qualification must account for the selected machine's encoders, homing, offsets and faults. A dropped CAD model must never call this attestation by itself.

An eventual execution record must bind job digest, profile revision, tool/offset state and relevant setup revision. The setup workbench already binds configuration transactions and observations to exact store/epoch/revision/digests; complete job/tool/offset and physical execution binding remains a requirement, not something this supervisor implements.

## Distinct failure clocks

| Clock | Provisional study default | What it means |
|---|---:|---|
| HMI lease | 1000 ms | Communication authority expires without renewal |
| Motion watchdog | 20 ms | No completed backend control-cycle event inside this interval faults the model |
| Stop acknowledgment | 500 ms | A requested hold without a stopped acknowledgment faults the model |

These values are examples, not approved machine limits. HMI heartbeat never refreshes the motion watchdog. Boot and reboot do not count as backend progress: at least one actual local completed-cycle event is required before arming. The backend event must eventually correspond to completed valid motion work, not a timer interrupt or a healthy networking thread.

The default studied policy requests hold when the HMI disconnects or its lease expires. An alternative `continue_local` policy exists to study autonomous local-job completion; selecting it for an actual machine requires a defined local-control and interruption policy. Neither reconnects nor a second browser automatically resume motion.

Deadline processing uses simulated controller time and deterministic ordering. A motion-watchdog expiry wins a simultaneous lease or stop deadline. These are model semantics, not measured scheduling guarantees.

## Fault and recovery

An asserted E-stop input, asserted drive fault, removed physical enable while armed, expired motion watchdog, or missing stop acknowledgment latches a fault. The model drops the session, backend acceptance and position trust.

Reset is a local event and is refused while the modeled physical fault inputs remain active. It returns to disarmed. A reboot changes identity and drops job/position/execution state; active physical fault inputs still prevent normal operation. ESP recovery may expose diagnostics or request an authorized reset path later, but may not resume from stale position knowledge.

## Evidence and remaining integration

Unit tests exercise malformed messages, replay, state transitions, deadline boundaries, reconnect/reboot, physical fault inputs, and seeded event sequences. Scenario traces are reviewable examples. They do not cover an actual network, cryptography, motor mechanics or hardware failure containment.

Before a production implementation: bind this contract to the actual backend; define jog and pendant ownership separately from program start; add bounded storage/queues and authentication; verify physical interlocks; perform fault injection on the selected hardware; and map every displayed state to evidence from the machine.

## Later accessory-service requirement

The [ESP accessory contract](ESP_ACCESSORY_AUTOMATION.md) adds per-operation readiness dependencies and separate sensor/service freshness deadlines. This original offline supervisor does not yet implement them. A future integration must distinguish requested outputs from confirmed flow/pressure/temperature, expire missing readiness, await actual stop acknowledgment and apply the machine-specific loss/after-run policy. Diagnostic-only ESP failure and failure of an essential ESP-managed service cannot share an assumed harmless response. Keep one output owner, prohibit automatic restart and validate independent behavior when either processor or its power fails.
