# Executed SIM2 provider/plant qualification

[Current run-r07](run-r07/receipt.json) passes458 meaningful checks normally and
with AddressSanitizer/UndefinedBehaviorSanitizer. Ten copied-source mutations are
compiled successfully and detected by execution: removed CRC, full source SHA,
full configuration SHA, freshness, ordered sequence, independent motor gate,
independent output gate, motor gate-before-OPI causality, separate output domain
and consumed-reset protection. Mutation copies never change actual sources.
Normal and sanitized checks overlap and are not additive.

The [implementation](../../../cnc3_runtime/providers/README.md) provides actual
twelve-channel emitted-pin mechanics, four ABZ/index waveforms, explicit24DI and
16DO application/fault feedback, geometry-derived homes/limits/probe, timed
watchdog drop/recovery, deliberate reset and CRC/full-digest/sequence/freshness
validation. Both eight- and twelve-channel gate domains are checked. Sources
match the executed copies; compiler, command, binary, input and mutation hashes
are retained. This is standalone provider execution, not a completed LinuxCNC
trajectory, FPGA target, real IOL1 identity, electrical test or physical machine.

The tests reject missing opt-in/identity, foreign sessions/configuration/source
digests even with matching shortened identifiers, missing or unavailable
providers, invalid field bits, CRC corruption, future/reversed/old timestamps,
skipped/replayed/conflicting sequence and reset reuse. Freshness is checked at
21999/22000/22001 ticks and latched rejection cannot be repaired by a later valid
record. A new context preserves time lineage and must acquire new facts.

Integration review found and corrected causal boundaries before final source
binding: raising modeled motor gates only after OPI rearm deadlocked the actual
RTL handshake; the four historical motor domains also required a separate
general-output gate. The model now witnesses request, gate observation, rearm
and OPI restoration as distinct phases. An unexpected applied output is observed
independently of its request. No modeled phase grants physical authority.

All attempts remain preserved. run-r01 found no native WSL g++; run-r02 had a
passing Clang normal run but lacked native sanitizer libraries. run-r03's chroot
sanitizer had no private /proc and produced unusable exception/stack diagnostics;
run-r04 mounted /proc inside a new private PID/mount namespace and passed the same
428 normal/sanitized checks plus six controls. The extended run-r05/run-r06 each
passed458 normal/sanitized checks but stopped when a mutation copy failed strict
compilation, so neither claims those incomplete controls passed. run-r07 fixes
only mutation syntax and executes all ten negative controls successfully. No
installed module, source, existing configuration, routing or archive is changed
by this runner. New UUID-keyed rootfs work and report directories retain evidence.

The provider fixture assumes ideal mechanics, one encoder edge per accepted
STEP, authored geometry and virtual gate/watchdog timing. It does not claim
motor torque, physical sensor quality, loaded real-time deadlines or measured
inhibit propagation. Production authority remains false. No device connection
or paid API call occurs.
