# Independent final qualification review

The final [receipt](receipt.json) binds the root report/gap register, canonical
host/RTL/vendor receipts, retained evidence and current source bytes. This is a
read-only source and evidence review with fresh independent decoding of all 22
boundary-case wire responses. It is not another HAL, FPGA, target or physical
execution.

The actual recorded HAL scheduler run passes six cases and 124 assertions. The
same IS-2 module refuses without explicit simulation opt-in and executes actual
POSIX non-realtime HAL callbacks with opt-in. Its incomplete CAP3 profile still
refuses qualification despite ideal bench providers. Twelve commands, twelve
feedback pins and four encoder pins exist; feedback is invalid, all simulated
STEP counters remain zero, and no CONFIGURE/ARM/UPDATE or authority appears.
This proves the inhibited path, not a coordinated LinuxCNC trajectory or a
complete twelve-channel machine.

The distinct stateful motion bench uses twelve generators/four encoders and
authored logical qualification fixtures. The independently decoded final
176-byte feedback frames confirm refusal of six unsupported commands, individual
trips for all twelve alarms and faults for all four unavailable encoder ports.
These logical fixtures and simulated RTL pins do not establish motherboard
presence, general I/O acquisition, actual target timing or physical measurements.
Source adoption is false. Efinity device qualification remains BLOCKED for the
actual T20F256I4; generic family synthesis is a separate screening result.

Two findings were corrected before binding the final evidence:

- A partial temporary-module installation could skip caller cleanup. The
  [before control](module-install-negative-control.json) reproduces the defect
  using inert files and binds the preserved pre-correction run-r05 sources.
  [Four corrected Linux controls](module-install-corrected-controls.json) exercise
  failed/torn pending copies, failed fsync and a lost acknowledgment after actual
  publication. Completed modules publish without replacement, no pending or torn
  module remains, and the original inert inventory is restored. They access no
  real installed rootfs modules.
- The host report described simulated monitors as physical-pin monitors. The
  final wording identifies them as RTL output-pin monitors; no execution receipt
  changes for this wording correction.

The independently executed [preservation check](preservation-r01.json) found no
differences in 24 feature/service/UI files, 3,308 protected sources, 20 external
archive sources, 21 existing settings or 20 retained regression tests. The final
root preservation receipt also passes. No routing, source, machine settings,
device connection or paid API call was introduced by this review. No further
actionable defect was found within the reviewed scope.

[The verifier](verify_final_evidence.py) rechecks recorded hashes, refusal
assertions and the actual retained boundary response bytes. It requires a fresh
output receipt and edits no source or sealed qualification artifact.
