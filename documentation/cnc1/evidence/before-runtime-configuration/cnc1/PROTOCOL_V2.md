# CNC1 ABI v2 discovery extension

The actual `gateware/rtl/cnc_endpoint.v` implements this opt-in extension with `ENABLE_DISCOVERY=1`. Default `0` retains ABI v1 and its independently rerun 180 checks. Neither ABI is Mesa HostMot2. The v2 driver accepts exactly the fitted six-step/two-encoder reference; it does not advertise the proposed eight/four design.

All existing [v1 framing, CRC, command fields, atomic commit, authority, pulse generation and watchdog rules](../../../../WORKSPACE_REFERENCES.md#artifact-51699d32fb16ba61) remain, except byte 4 must be **2** in every v2 command and response. No automatic v1/v2 fallback is implemented. Unsupported versions fail closed. Ordinary status keeps magic `CNS1` and its previous layout, with version byte 2.

**Opcode 5: read capabilities.** Command bytes 6–61 must be zero. It is accepted only while disarmed. It does not arm, establish a session, clear faults or feed the watchdog. Its own simultaneous response still describes the prior snapshot. The following NOP returns the capability page, then ordinary status resumes. Asking for capabilities while armed is a protocol fault.

| Capability response bytes | Encoding/value |
|---|---|
| 0–3 | ASCII `CNC2` |
| 4 | ABI 2 |
| 5 / 6 / 7 | STEP channels 6 / ABZ encoders 2 / frequency channels 0 |
| 8–11 | Big-endian feature bitmap `0x0000001f` |
| 12–15 | Core clock parameter in Hz: 50,000,000 |
| 16–19 | Maximum signed rate magnitude: `0x01000000` |
| 20–21 / 22–23 | STEP high / minimum low ticks: 100 / 100 |
| 24–25 / 26–27 | DIR setup / hold ticks: 100 / 100 |
| 28–31 | Watchdog ticks: 250,000 |
| 32–61 | Reserved zero |
| 62–63 | CRC-16/CCITT-FALSE over bytes 0–61 |

Feature bits 0–4 mean STEP generation, AB quadrature, index latch, atomic multi-channel update and watchdog. No general I/O, frequency measurement, analog, probing, spindle actuator or physical-board identity is advertised. Descriptor values come from the actual compiled RTL parameters; they are not a physical measurement or permission to exceed drive/cable limits.

The C state machine distinguishes discovery, OFF, pending SYNC, READY, pending ARM, ACTIVE, pending DISARM and FAULT. SYNC requires an explicit reset edge with enable low. ARM requires a subsequent enable edge and zero rates; nonzero updates wait for its later acknowledgement. Returning communication or a held-high enable never clears FAULT. Discovery failure permits an explicit stopped retry; sequence exhaustion faults rather than wrapping. A reset creates a different session. This is an accidental-stale-command contract, not cryptographic replay protection across complete host/FPGA resets.

The common driver checks CRC/version/reserved fields, expected session/sequence, core-time advancement and host sample age. It unwraps counters using modulo deltas; emitted-count changes must fit the advertised DDS limit plus quantization margin. Encoder plausibility uses the RTL logical ceiling of one transition per core tick, **not a qualified electrical input rate**. Index values use the nearest modulo epoch relative to the continuous count, valid only while the latch is less than 2^31 counts old. The sticky index flag is not a timestamped event queue.

Configuration scales and axis mask freeze with the first ordinary feedback sample. Later mutation faults before rescaling feedback or publishing another command. This milestone permits startup configuration; changing scaling for actual operation requires a future disarmed configuration/reconciliation service, or reload of this simulation profile. Error cause remains latched until explicit reset, and `cnc1.feedback-valid` drops on faults. Other displayed positions/status may be retained last samples during an outage and must not be treated as current verified position.

## Replaceable transport boundary

`cnc1_transport.exchange(context, tx[64], rx[64])` is the common C boundary. It exchanges exactly one frame and returns success/failure. The only supplied implementation clocks the actual Verilated RTL. The compiled HAL read function obtains feedback before LinuxCNC motion calculations; the write function publishes rates afterward. Python is only the acceptance-test orchestrator.

The simulation clocks the 50 MHz RTL in 20 ns ticks and implements mode-0 SPI at core/8, with the specified CS guards. One simulated servo period is 1 ms. It advances the core even when the simulated link is removed, so watchdog failure is exercised. Its wall-clock freshness allowance is explicitly relaxed to 500 ms; common-code defaults/tests use 5 ms. Simulation clock progress and host wall time are recorded separately.

Pi SPI, Rockchip SPI, spidev and direct peripheral mappings are deliberately absent. Physical transports need measured exclusive bus ownership, bounded calls, response age and loaded-cycle qualification before use. The current position-to-rate calculation is a functional one-cycle integer pulse-error controller, not a mature tuned physical step/servo implementation. It closes emitted pulse accounting, not a mechanical feedback loop.
