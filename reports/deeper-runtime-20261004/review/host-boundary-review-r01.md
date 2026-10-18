# Independent final host boundary review

The new current-source SIM2 host runtime was inspected read-only after the
provider watchdog correction and successful final twelve/eight-joint runs.
No remaining actionable defect was found in the reviewed startup, transport,
rate, session-event or adoption boundaries. This review does not repeat the
LinuxCNC execution; it verifies and attributes the recorded execution evidence.

The actual client issues NML commands to LinuxCNC's task and FREE joint planners.
HAL commands and enable come from motion-controller pins. The C driver shifts
96-byte command and 176-byte feedback transactions on the compiled RTL SPI pins;
the independent provider observes emitted STEP/DIR/enable and supplies ABZ and
authored sensors. The transport contains no physical-device path and does not
substitute host-ideal feedback frames. The four encoder and twelve fitted motor
inventory belong to this explicit derivative and simulation context; they do
not retroactively qualify the original archive or ordinary structural endpoint.

Startup requires explicit disconnected opt-in, the reviewed complete current
source closure and exact six-field saved binding. The C decoder additionally
refuses malformed/duplicate JSON, unsupported sense/masks/encoder mapping,
nonfinite numerical values and invalid timing/rate values. The verifier's
environment-selected executable is a trusted lab orchestration input, not an
authenticated arbitrary-caller security boundary. All physical/production
authority remains false.

The callbacks constrain periods and HAL stimulus widths. Saved maximum
velocity limits command change and pulse correction; the final DDS word is
checked against high+low+carry timing without consuming an UPDATE sequence on
failure. The first host fault remains latched. Deliberate stopped reset creates
a new motion session and keeps the provider's independent immutable identity
and advancing sequence. The current C driver still clears per-session event
ACK/deduplication fields only after successful SYNC, preserving historical
captures. The previously reproduced old/new event control is retained as
historical evidence bound to its own earlier C source; it is not represented
as execution of the entire final C source.

Final evidence has real concurrent positive task velocities and independently
observed/accepted rises for every selected lane: twelve in `nml-r07`, eight in
`nml-eight-r02` with unused fitted lanes at zero. Serial ABZ/index/probe records,
24 DI and 16 DO application feedback, an individual alarm stop and inhibited,
unhomed explicit restart are recorded. These are short, low-rate, ideal integer
plant trajectories and authored HAL sensor stimuli. They do not prove customer
Cartesian kinematics, G-code coordination, G38 probing, physical index homing,
physical sensor wiring or loaded real-time deadlines. The adapter output
seqlock does not make separately read motion inputs and later NML statistics a
single atomic combined snapshot.

Temporary module publication uses complete-copy/fsync/atomic-link semantics and
cleanup after an attempted partial install. Both recorded before/after module
inventories preserve all 183 existing modules. This reviewer verifies those
recorded inventories; the hardware review separately verified the live rootfs
inventory. No installed rootfs module or current source is modified here.

The [receipt](host-boundary-review-r01.json) binds current sources, final copied
sources, canonical and raw receipts, execution logs and supporting reviews.
No FPGA device fit, signed binary distribution, physical qualification or
manufacturing readiness is promoted.
