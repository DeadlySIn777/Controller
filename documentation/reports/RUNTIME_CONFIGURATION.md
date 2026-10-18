# Actual-runtime stopped configuration

**Later completed extension:** [durable runtime calibration](PERSISTENT_RUNTIME.md) now adds a default compiled startup inhibit, journal/witness authority and verified activation across independent LinuxCNC launches. The original volatile subset and its first evidence are described below; its prior files/module are archived under `cnc1/evidence/before-persistent-runtime/`. The current launcher for these original 26 cases, plus a 27th pulse-rate margin boundary check added in the final sync, explicitly opts into volatile laboratory mode. Current durable evidence and limits are in the linked report.

28 September 2026. The shared runtime configuration service now changes X/Y/Z step scales in **actual LinuxCNC, through the compiled CNC1 driver and actual simulated FPGA RTL**. It does not change disconnected fixture flags to claim that the machine is stopped. At this milestone the complete acceptance run passed 26 checks: the previous 11 CNC1 cases and 15 runtime configuration cases. The current run has 27; see below.

## Implemented operation and evidence

`controller_config/runtime.py` contains `RuntimeConfigurationService`, `LinuxCNCRTLAdapter` and its JSON CLI. It discovers the existing six-step/two-encoder reference through the compiled HAL driver's actual RTL capability page. The explicit LinuxCNC XYZ profile maps only the first three step channels; changes to the other discovered channels are refused because no corresponding machine joint/velocity contract exists. No field input, electrical rating, output bank or cartridge is invented by this adapter.

In the archived first run `fc802fbe-42b8-41fb-9fcc-0aa57cdc4951`, the service changed X from 200 to 250 steps/mm after prior interpreted movement and an injected link fault. The returned raw counts were `[8, 200, -100]` both before and after commit. All three LinuxCNC homed flags were cleared; the machine and FPGA permission stayed off. After **separate, deliberate enable and homing commands**, `G91 G1 X1 F60` changed the returned X count from 8 to 258 and LinuxCNC reported X=1.0 mm. This is a 250-pulse increment at the new scale, not ideal feedback or a substituted counter model. The current final sync rerun `551cc0bd-9363-42b6-8a66-fa6adc27d7ab` (`cnc1/evidence/linuxcnc.json`) shows the same: raw counts `[8, 200, -100]` before and after commit, and X from 8 to 258 after the deliberate rehome and move. The repair-round rerun `c4357707-45e3-439a-8c38-7145cef75b3a` (archived under [before-final-sync-2026-09-28](../WORKSPACE_REFERENCES.md#artifact-ef50ba16d8ffa307)) showed the same counts. The first audit-fix rerun `3ed8e8db-743d-4917-83db-db5ea47bcb34` (archived under [before-audit-repair-2026-09-28](../WORKSPACE_REFERENCES.md#artifact-11cbb45a0ab924da)) recorded `[7, 200, -100]` and 7 to 257. The starting count depends on where earlier interpreted motion stopped; the increment is 250 pulses in every run.

The same service rejected an enabled machine, an executing move, an old preview after an actual enable/disable cycle, replay of an already committed preview, unmapped-channel changes and a scale that exceeds the discovered pulse ceiling at the profile's configured maximum velocity. Direct external writes to the active scale HAL output pin failed. Writing a staged scale alone left the active scale unchanged. A separately attempted transaction bypassing Python's state check was rejected by the compiled guard while enabled. Since the final sync, the run also checks the margin boundary against the actual RTL, using figures read from the live snapshot. A preview of X=19,331.25 steps/mm returns a plan and applies nothing. X=19,331.26 is refused with `PULSE_RATE_LIMIT`, although it is below the raw DDS ceiling scale of 19,531.25. Session, revision, epoch, scales, lock, permission and enable are unchanged.

The public JSON CLI was exercised as separate processes in the running simulator: `snapshot`; `preview` to an exported plan; `apply` reversing the scale back to 200; and `recover-inhibit` after a deliberately acquired but unfinished transaction. Reversal advanced the revision to 2 and again left the machine disabled and unhomed. No operation silently enabled, homed or resumed the machine.

The table below is the **archived first volatile run** of this milestone (run `fc802fbe-42b8-41fb-9fcc-0aa57cdc4951`); its manifest and files are under [before-persistent-runtime](../WORKSPACE_REFERENCES.md#artifact-ac407032c9414679).

| Evidence class (archived first run, historical) | Result |
|---|---|
| Actual LinuxCNC + compiled HAL + Verilator RTL | 26 checks; run `fc802fbe-42b8-41fb-9fcc-0aa57cdc4951`; 1,252 trace rows |
| Compiled C/RTL harness | 179 assertions, including repeated setup and labeled synthetic boundary cases |
| Runtime service host policy tests | 24 tests; these use an explicit adapter double and are separate from actual-runtime evidence |
| Elapsed execution | 16.3147 seconds wall time; 3.1161 seconds simulated RTL time |
| Physical transport / machine measurements | None; the HAL build still links only the RTL simulation transport |

An intermediate rerun of the same 26 cases, run `89f626bb-63e0-4136-8067-cb0cd585243e` (1,233 trace rows, 16.1227 s wall / 3.1141 s simulated, 192 compiled assertions, 26 host tests), is also historical. It is archived under [before-audit-fixes-2026-09-28](../WORKSPACE_REFERENCES.md#artifact-4ebedc4f9a329ca2).

The first audit-fix rerun, run `3ed8e8db-743d-4917-83db-db5ea47bcb34` (1,116 trace rows, 14.8190 s wall / 3.1791 s simulated, 219 compiled assertions), is historical and archived under [before-audit-repair-2026-09-28](../WORKSPACE_REFERENCES.md#artifact-11cbb45a0ab924da).

The audit-fix repair rerun, run `c4357707-45e3-439a-8c38-7145cef75b3a` (26 checks, 1,122 trace rows, 14.8122 s wall / 3.1701 s simulated, 220 compiled assertions, 32 runtime-service host tests), is historical and archived under [before-final-sync-2026-09-28](../WORKSPACE_REFERENCES.md#artifact-ef50ba16d8ffa307).

**Current volatile regression (final sync rerun, 28 September 2026):** **27 cases** pass in run `551cc0bd-9363-42b6-8a66-fa6adc27d7ab`: the 26 above plus the pulse-rate margin boundary check. The run has 1,124 trace rows and took 14.8190 s wall time for 3.1621 s of simulated RTL time. It ran against the service with the servo-period bound described below. The **220 compiled C/RTL assertions** are carried forward from the repair-round build, because the C sources, RTL and module are unchanged. **41 runtime-service host tests** pass. See `cnc1/evidence/linuxcnc.json`, `compiled-rtl-tests.log` and `runtime-service-tests.log`. None of these runs is physical or real-time evidence.

The 1 ms configured period and 500 ms simulation-only host-age allowance are not physical real-time performance evidence. The 500 ms allowance is set explicitly in `hal_cnc1.c` through the driver's `simulation_age_override` flag. Without it, the common driver limits sample age to the discovered RTL watchdog (5 ms). It also refuses a servo period above half that watchdog with `CNC1_CONFIG` before sending any SYNC, ARM or UPDATE frame; the check is compiled-harness tested with synthetic capability pages. FPGA synthesis, routed timing, electrical commissioning and target ARM memory ordering remain unqualified. The service/driver servo-period mismatch recorded in the repair round is closed. `controller_config/runtime.py` now reads `cnc1.watchdog-ticks` and the discovered `core_hz`. It uses the driver's integer arithmetic, `period <= (watchdog_ticks * 10^9 // core_hz) // 2`, and refuses a larger period with `SERVO_PERIOD_LIMIT` before any preview, plan validation, activation or saved-record load. A missing watchdog or `core_hz` gives `CAPABILITIES_UNAVAILABLE`. At 250,000 ticks exactly 2.5 ms is accepted and 2.500001 ms is refused; 10 ms remains an outer ceiling. That boundary is host-test and source-inspection evidence with adapter doubles. The actual LinuxCNC run shows that the service reads 250,000 ticks and a 2.5 ms bound from the actual RTL and accepts the profile's 1 ms period. No profile above the bound was launched.

## Transaction contract

1. `snapshot` reads actual LinuxCNC status and a coherently published HAL snapshot. A preview includes exact before/after values and a diff, the profile identity, kernel boot ID plus module instance timestamp, protocol session, configuration revision, runtime epoch, and observed capabilities. A preview expires after 60 seconds of that host's monotonic time.
2. Validation requires actual disabled/machine-off status, interpreter idle, in-position, trustworthy returned feedback, compiled READY state, no FPGA permission and no existing configuration inhibit. LinuxCNC reports the disabled/estop-released condition as `STATE_ESTOP_RESET`; the adapter recognizes this and `STATE_OFF`, always in conjunction with the other checks. It does not treat `STATE_ON` as stopped.
3. The service takes a cooperative process lock, validates the binding again and requests the compiled guard to acquire an inhibit. The guard independently checks the current driver session/revision/epoch, enable/reset inputs, READY state and endpoint enable/mask. An enable racing an acquired inhibit becomes a latched configuration fault before ARM.
4. While inhibited, the service requests manual/free mode and unhomes the actual LinuxCNC joints. It rechecks the stopped state, all homed flags, the binding and expiry before commit. The bounded compiled operation validates all six staged numbers before changing any active scale and advances the configuration revision atomically with that change.
5. The service verifies returned scale/revision and stopped state before explicitly releasing the inhibit. An exception or interrupted client after acquisition leaves the inhibit acquired. `recover-inhibit` independently verifies stopped state, unhomes and releases it. If an enable attempt already faulted the driver, explicit stopped driver fault recovery is also needed before this release. Neither path supplies machine enable.

Active step scale pins are HAL outputs. Staged scale pins and the request tuple are distinct HAL inputs. The request sequence is published last, increases monotonically and is acknowledged with a guard result on `cnc1.config-result`.

`cnc1.config-op` selects one of five operations:

- 1: acquire the configuration inhibit.
- 2: commit all six staged step scales while the inhibit is held.
- 3: release the inhibit.
- 4: stage the persistent-pending inhibit. This is persistent profile only. It records the current revision as the stage base.
- 5: persistent acknowledgement, routed to `cnc1_persistence_commit`.

| Code | Raised by | Meaning |
|---|---|---|
| 0 | driver | Success |
| 1 | driver | Unsafe state: undiscovered, feedback invalid, not READY, enable/reset edge, endpoint enabled or mask set, inhibit already held (op 1) or not held (any other op, including an unknown one), or op 5 while not persistent-pending/locked |
| 2 | driver | Stale session/revision/epoch binding (checked first) |
| 3 | driver | Invalid operation or scales: op not 1-5 while the inhibit is held, null/non-finite/out-of-range scale, revision exhausted, op 4 without persistence required; op 5 with null hash, zero or regressed generation, or same generation with a different hash |
| 4 | HAL wrapper only | Request sequence zero or not greater than the last accepted request; the driver is not called |
| 5 | driver | Persistent-authority gate: op 3 while persistence is pending; op 2 while persistence is required but not staged; op 5 without a stopped op-2 scale commit since the gate was staged by op 4 or at HAL load |
| 6 | HAL wrapper only | Request deadline zero or already expired when the cyclic thread processed the request; the driver is not called |

The service treats every non-zero code as a rejected transaction and reports it as `COMPILED_GUARD_REJECTED` with the message `Cyclic guard rejected operation N (<name>): code R`. Codes outside 1-6 are named `unknown result`, and the message always ends in `code R`.

Coverage differs by code:

- The compiled harness (`cnc1/tests/test_driver.c`) covers driver codes 1, 2, 3 and 5, including the op 4/5/3-without-2 refusal and the normal 4/2/5/3 path. It also asserts the limit of code 5: an explicitly committed set of 200-step values is acknowledged with an arbitrary hash, because the driver checks only that a commit followed the stage, not the values.
- The actual persistent LinuxCNC suite exercises code 5 through HAL at startup and code 6 through an expired HAL request.
- Code 4 has no automated test. It is established only by source inspection of `hal_cnc1.c`.

The cyclic implementation uses only bounded scalar copies/checks and existing CNC1 calls; no Python, file locking, allocation or disk access was inserted into `cnc1.read`/`cnc1.write`. HAL snapshot publication uses sequentially consistent atomic sequence increments. Cross-process staging order has been exercised on this x86 LinuxCNC simulator, **not qualified on a Pi/Rockchip target**.

Pulse ceilings come from the RTL's core clock and maximum DDS rate. The service checks each mapped joint's installed INI maximum velocity against that ceiling. Since the configuration owner's audit fix, that check uses the `[EMCMOT]SERVO_PERIOD` read from the same INI and a two-count correction margin (`scale * MAX_VELOCITY <= ceiling - 2e9 / period_ns`; 193,312.5 steps/s at 1 ms). This is host-test and source-inspection evidence in `controller_config/runtime.py`. The final sync adds an actual LinuxCNC/RTL check at the boundary: 19,331.25 steps/mm previews and 19,331.26 is refused before any change, at `MAX_VELOCITY` 10. It cannot increase firmware capabilities. This is a necessary consistency check, not physical drive/motor velocity or acceleration qualification. Encoder calibration and channel mask remain outside this new writable subset; their pre-existing mutation fault handling is retained.

## CLI and reproduction

Inside the explicitly running isolated RTL profile, the following commands use the same service as the tested Python API:

```sh
python3 -m controller_config.runtime snapshot
python3 -m controller_config.runtime preview --scales 250 200 200 200 200 200 --output /tmp/new-scale-plan.json
python3 -m controller_config.runtime apply /tmp/new-scale-plan.json
python3 -m controller_config.runtime recover-inhibit
```

The last command is only for an acquired, stopped configuration inhibit; ordinary execution does not require it. The CLI refuses absent simulation opt-in and the wrong profile. Outside the LinuxCNC environment, missing HAL/LinuxCNC modules produce a structured `RUNTIME_UNAVAILABLE` error. It is not a public network service or installed global `cncctl` executable.

From the Windows workspace, reproduce the entire acceptance flow—including its real CLI subprocesses—with:

```powershell
wsl -d GarciaMechBuilder -- sh -c 'sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/build.sh > /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/evidence/compiled-rtl-tests.log 2>&1 && sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/run_linuxcnc.sh'
python -m unittest discover -s tests -p test_runtime_configuration.py -v
```

`run_linuxcnc.sh` starts from a clean work copy of the profile, orchestrator and `controller_config`, so an earlier run's LinuxCNC `simulation.var` or evidence JSON cannot carry over. It honours `CONTROLLER_LAB_ROOTFS`.

## Persistence and remaining limits

This is a **runtime-only step-scale transaction**. Restarting the driver restores its default scale. It does not edit a user's INI, the disconnected full-profile configuration store, the machine-memory cartridge or a live machine configuration. Reversal requires a newly validated stopped preview of the old values. Combining this with durable profile/cartridge authority needs a separately designed journal/reconciliation transaction so a crash cannot make storage and the active controller silently disagree.

The current homing profile is software-only, with no physical switches or machine attached. Clearing and reacquiring LinuxCNC homed flags does not establish physical position. Local HAL access is a privileged engineering interface, not an authentication boundary; a malicious local writer is not a supported threat model for this prototype. Public authentication, operator ownership, physical transport qualification, production calibration ranges, and target memory-order testing remain open.

The [current CNC1 manifest](../WORKSPACE_REFERENCES.md#artifact-8474095096839423) covers the current volatile run `551cc0bd-9363-42b6-8a66-fa6adc27d7ab`, the persistent run, the compiled module and this report as a source file. It can be checked with `python cnc1/tools/record_evidence.py --check`. The archived first-run figures in the table above are covered by the [before-persistent-runtime manifest](../WORKSPACE_REFERENCES.md#artifact-ac407032c9414679). The preceding 11-case milestone's covered sources/evidence and original manifest were copied byte-for-byte and hash-verified under [before-runtime-configuration](../WORKSPACE_REFERENCES.md#artifact-957ccac8dfa8d305) before edits. Its original compiled module hash is retained in that historical manifest; that prior binary is not separately archived. The 180-check ABI-v1 RTL regression cited at that time is historical. The current `cnc1/evidence/baseline-regression.log` is a fresh rerun against the changed RTL: 252 default-v1 checks and 27 ABI v2 checks (HDL simulation and lint only).
