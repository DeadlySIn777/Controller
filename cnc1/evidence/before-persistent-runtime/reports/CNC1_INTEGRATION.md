# CNC1: actual LinuxCNC to actual FPGA RTL

28 September 2026. **The previously separate pieces now communicate end to end.** Actual LinuxCNC commands pass through compiled HAL read/write functions and the CNC1 protocol into the existing FPGA endpoint compiled by Verilator. Returned emitted-pulse counters provide the simulated joint feedback. A link failure during commanded motion produces real LinuxCNC amplifier faults, removes machine enable, and cannot restart on reconnection.

This is a functional software integration. The HAL acceptance build uses only simulated RTL; there is no FPGA bitstream, target deadline measurement, board connection or machine qualification. Experimental physical-transport development has separate evidence. The preferred eight-motor/four-encoder candidate remains separate.

**Later completed extension:** [actual-runtime stopped configuration](RUNTIME_CONFIGURATION.md) adds 15 checks to the original 11 below: read-only active scales, discovered-resource validation, compiled inhibit/commit, unhoming, stale/unsafe refusals, deliberate rehome/new-scale motion and CLI reversal/recovery. The current complete run has **26 LinuxCNC checks and 179 compiled C/RTL assertions**. The original 11/157 milestone's sources and evidence are preserved under `cnc1/evidence/before-runtime-configuration/`; its historical claims below remain identifiable.

## Implemented path

- `cnc1/src/cnc1.c`: fixed-size C codec, capability validation, session/state/acknowledgement handling, scaling, counter/index unwrapping, plausibility/freshness checks and fault latching. No allocation, file I/O, network calls or Python in the common cyclic logic.
- `cnc1/src/hal_cnc1.c`: compiled `cnc1.read` before LinuxCNC motion calculation and `cnc1.write` afterward. This dedicated XYZ profile uses mask 7. Fault output is wired to all three actual LinuxCNC joint amplifier-fault inputs.
- `cnc1/src/sim_transport.cpp`: clocks the actual `cnc_endpoint`, `cnc_spi_frame`, `cnc_stepgen` and `cnc_encoder` RTL; exchanges every frame through their SPI pins. It also supplies simulated quadrature/index waveforms and deliberate communication faults. No physical transport is implemented.
- Opt-in ABI v2 discovery returns **six STEP channels, two ABZ encoders and zero frequency channels**, plus defined feature/timing parameters. Default ABI v1 is retained. [Protocol extension](../cnc1/PROTOCOL_V2.md)

The integer pulse-error position controller is deliberately a bounded functional demonstration. Its digital feedback is emitted STEP counts, not measured mechanical motion. Production velocity/acceleration handling, loop tuning, configurable real interfaces and position reconciliation remain engineering work.

## Executed evidence

| Evidence class | Result and limit |
|---|---|
| Actual LinuxCNC + compiled HAL + actual RTL | **11 acceptance checks passed**; XYZ homing, coherent multi-joint command, signed reversal, ABZ speed change/index/scaling, actual machine fault response and stopped recovery |
| Compiled C/C++ integration harness | **157 checks passed**, including repeated setup assertions; mixes actual RTL protocol cases and explicitly labeled common-code boundary fixtures |
| Original default ABI v1 regression | **180 checks passed again**, independent Python decoding, default elaboration and clean Verilator lint |
| Compilation | Common C and C harness compile with strict warnings as errors; HAL module links against the real LinuxCNC uspace interface; v2 RTL compiles under Verilator `-Wall` |
| FPGA synthesis / place-and-route / timing closure | Not run |
| Physical transport, electrical or machine measurements | Not performed |

The LinuxCNC test commands `G21 G90 G1 X2 Y-1 Z0.5 F600`, obtaining returned counts `[400,-200,100]` at 200 steps/mm. It then commands `G1 X-1 Y1 Z-0.5 F600`, obtaining `[-200,200,-100]`. These are actual interpreted LinuxCNC moves whose feedback comes from the protocol/RTL chain; there is no ideal position-command-to-feedback HAL loopback.

Simulated ABZ edge intervals change from 10,000 to 2,500 core ticks. The real RTL reports the resulting positive and negative encoder counts, index latches and scaled positions through CNC1 and HAL. This demonstrates the feedback path. **No G33/G76/G33.1 synchronized operation was executed**, and these stimulus counts are not a physical spindle measurement.

During `G1 X15 F300`, the test removes the simulated communication link after motion starts. The common driver faults, LinuxCNC logs joint amplifier errors and disables motion, and the RTL watchdog removes its permission. Restoring the link leaves both sides disabled. An explicit reset with enable low establishes a new session and restores communication without enabling motion.

The compiled harness separately exercises all six signed outputs, corrupt command/response CRC, truncated UPDATE, wrong session, duplicate old UPDATE, stale valid response, missing link, watchdog, FPGA reset, discovery mismatch/retry, sequence exhaustion, host-age checks, impossible count discontinuity, configuration mutation and acknowledgement sequencing. Timestamp/count/index wrap boundary cases use a CRC-correct synthetic frame fixture; the short RTL run does not clock through an entire 32-bit timestamp period. Check counts must not be described as independent physical operating scenarios.

## Identity, timing and reproducibility

The actual run uses Debian LinuxCNC `1:2.9.4-2+deb13u1` and matching development headers in the existing isolated rootfs, WSL kernel `6.18.33.2-microsoft-standard-WSL2`, Verilator 5.048 and Debian GCC/G++ 14.2. Package identities are saved in `cnc1/evidence/build-packages.tsv`.

`cnc1/evidence/linuxcnc.json` contains the final run ID, check details, sampled trace, elapsed wall time and elapsed simulated RTL time. **These times differ:** evaluating 50 MHz RTL is slower than real hardware. The 1 ms configured servo period and 500 ms simulation-only host freshness allowance are not target real-time acceptance. LinuxCNC explicitly reports POSIX non-realtime and task-loop scheduling excursions. No latency result here qualifies a Pi or Rockchip image.

From the workspace root, exact successful command forms:

```powershell
wsl -d GarciaMechBuilder -- sh -c 'sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/build.sh > /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/evidence/compiled-rtl-tests.log 2>&1 && sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/run_linuxcnc.sh'
wsl -d GarciaMechBuilder -- sh -c 'cd /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/gateware && sh tools/run_tests.sh > /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/evidence/baseline-regression.log 2>&1'
```

The launcher verifies a newly generated run ID and passing JSON result rather than accepting stale evidence. Source/evidence/module SHA-256 values are in `cnc1/evidence/manifest.json`. Re-recording hashes does not rerun tests; source changes require appropriate reruns first.

Original v1 identity is preserved in `cnc1/evidence/baseline-v1-before-extension/`: prior manifest, original changed endpoint/protocol/recorder and report. The current default-v1 manifest is regenerated against the successful regression. The extension changes only the selected protocol version/capability page; it does not expand motion channels or claim new field I/O.

Two initial orchestrator issues were fixed before the passing runs: waiting for LinuxCNC's initial status identity, and creating a read-only Python HAL observer before reading pins. The observer and Python MDI/test logic are outside the compiled cyclic functions.

## Remaining engineering

1. Implement and qualify one replaceable physical SPI transport for an exact compute module/image; then separately qualify other modules. Preserve exclusive ownership, bounded read/write calls, response-age limits and complete-cycle measurement under display/storage/network/thermal load.
2. Refine the functional pulse-position controller into a validated physical motion implementation, with actual drive timing, acceleration/velocity limits, feedback policy and stopping/recovery behavior. Pulse accounting and external encoders remain different evidence.
3. Add required machine I/O, probe capture, external useful-progress output and broader versioned configuration. A bounded runtime step-scale transaction now exists for the explicit XYZ profile; full profile persistence, physical reconciliation and encoder/mask reconfiguration remain unimplemented. Direct scale/mask mutation outside the supported guard still faults in common-code checks.
4. Complete target FPGA wrapper, pin/bank assignments, constraints, synthesis and routed timing. The clocked watchdog cannot detect loss of its own clock; independent output gating remains essential.
5. Extend the runtime configuration service to durable machine profiles and the UI/operator service. The earlier Python supervisor and file-only full-profile service remain separate models. This milestone does not implement production authentication, a complete public motion API, physical commissioning or an ESP accessory controller.

Fault cause stays latched; `cnc1.feedback-valid` marks loss of trust. Retained status during a long outage is not authoritative live feedback. Index unwrapping assumes less than 2^31 counts since the captured index and does not supply an event FIFO. Abrupt watchdog/inhibit faults may truncate a STEP pulse and do not implement controlled deceleration or preserve verified machine position. These limits remain explicit before hardware procurement.
