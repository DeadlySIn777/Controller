# Actual-runtime stopped configuration

28 September 2026. The shared runtime configuration service now changes X/Y/Z step scales in **actual LinuxCNC, through the compiled CNC1 driver and actual simulated FPGA RTL**. It does not change disconnected fixture flags to claim that the machine is stopped. The complete acceptance run passes 26 checks, including the previous 11 CNC1 cases and 15 runtime configuration cases.

## Implemented operation and evidence

`controller_config/runtime.py` contains `RuntimeConfigurationService`, `LinuxCNCRTLAdapter` and its JSON CLI. It discovers the existing six-step/two-encoder reference through the compiled HAL driver's actual RTL capability page. The explicit LinuxCNC XYZ profile maps only the first three step channels; changes to the other discovered channels are refused because no corresponding machine joint/velocity contract exists. No field input, electrical rating, output bank or cartridge is invented by this adapter.

The successful run changed X from 200 to 250 steps/mm after prior interpreted movement and an injected link fault. The returned raw counts were `[8, 200, -100]` both before and after commit. All three LinuxCNC homed flags were cleared; the machine and FPGA permission stayed off. After **separate, deliberate enable and homing commands**, `G91 G1 X1 F60` changed the returned X count from 8 to 258 and LinuxCNC reported X=1.0 mm. This is a 250-pulse increment at the new scale, not ideal feedback or a substituted counter model.

The same service rejected an enabled machine, an executing move, an old preview after an actual enable/disable cycle, replay of an already committed preview, unmapped-channel changes and a scale that exceeds the discovered pulse ceiling at the profile's configured maximum velocity. Direct external writes to the active scale HAL output pin failed. Writing a staged scale alone left the active scale unchanged. A separately attempted transaction bypassing Python's state check was rejected by the compiled guard while enabled.

The public JSON CLI was exercised as separate processes in the running simulator: `snapshot`; `preview` to an exported plan; `apply` reversing the scale back to 200; and `recover-inhibit` after a deliberately acquired but unfinished transaction. Reversal advanced the revision to 2 and again left the machine disabled and unhomed. No operation silently enabled, homed or resumed the machine.

| Evidence class | Result |
|---|---|
| Actual LinuxCNC + compiled HAL + Verilator RTL | 26 checks; run `fc802fbe-42b8-41fb-9fcc-0aa57cdc4951`; 1,252 trace rows |
| Compiled C/RTL harness | 179 assertions, including repeated setup and labeled synthetic boundary cases |
| Runtime service host policy tests | 24 tests; these use an explicit adapter double and are separate from actual-runtime evidence |
| Elapsed execution | 16.3147 seconds wall time; 3.1161 seconds simulated RTL time |
| Physical transport / machine measurements | None; the HAL build still links only the RTL simulation transport |

The 1 ms configured period and 500 ms simulation-only host-age allowance are not physical real-time performance evidence. FPGA synthesis, routed timing, electrical commissioning and target ARM memory ordering remain unqualified.

## Transaction contract

1. `snapshot` reads actual LinuxCNC status and a coherently published HAL snapshot. A preview includes exact before/after values and a diff, the profile identity, kernel boot ID plus module instance timestamp, protocol session, configuration revision, runtime epoch, and observed capabilities. A preview expires after 60 seconds of that host's monotonic time.
2. Validation requires actual disabled/machine-off status, interpreter idle, in-position, trustworthy returned feedback, compiled READY state, no FPGA permission and no existing configuration inhibit. LinuxCNC reports the disabled/estop-released condition as `STATE_ESTOP_RESET`; the adapter recognizes this and `STATE_OFF`, always in conjunction with the other checks. It does not treat `STATE_ON` as stopped.
3. The service takes a cooperative process lock, validates the binding again and requests the compiled guard to acquire an inhibit. The guard independently checks the current driver session/revision/epoch, enable/reset inputs, READY state and endpoint enable/mask. An enable racing an acquired inhibit becomes a latched configuration fault before ARM.
4. While inhibited, the service requests manual/free mode and unhomes the actual LinuxCNC joints. It rechecks the stopped state, all homed flags, the binding and expiry before commit. The bounded compiled operation validates all six staged numbers before changing any active scale and advances the configuration revision atomically with that change.
5. The service verifies returned scale/revision and stopped state before explicitly releasing the inhibit. An exception or interrupted client after acquisition leaves the inhibit acquired. `recover-inhibit` independently verifies stopped state, unhomes and releases it. If an enable attempt already faulted the driver, explicit stopped driver fault recovery is also needed before this release. Neither path supplies machine enable.

Active step scale pins are HAL outputs. Staged scale pins and the request tuple are distinct HAL inputs; request sequence is published last, monotonically increasing, and acknowledged with a guard result. The cyclic implementation uses only bounded scalar copies/checks and existing CNC1 calls; no Python, file locking, allocation or disk access was inserted into `cnc1.read`/`cnc1.write`. HAL snapshot publication uses sequentially consistent atomic sequence increments. Cross-process staging order has been exercised on this x86 LinuxCNC simulator, **not qualified on a Pi/Rockchip target**.

Pulse ceilings come from the RTL's core clock and maximum DDS rate. The service checks each mapped joint's installed INI maximum velocity against that ceiling. It cannot increase firmware capabilities. This is a necessary consistency check, not physical drive/motor velocity or acceleration qualification. Encoder calibration and channel mask remain outside this new writable subset; their pre-existing mutation fault handling is retained.

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

## Persistence and remaining limits

This is a **runtime-only step-scale transaction**. Restarting the driver restores its default scale. It does not edit a user's INI, the disconnected full-profile configuration store, the machine-memory cartridge or a live machine configuration. Reversal requires a newly validated stopped preview of the old values. Combining this with durable profile/cartridge authority needs a separately designed journal/reconciliation transaction so a crash cannot make storage and the active controller silently disagree.

The current homing profile is software-only, with no physical switches or machine attached. Clearing and reacquiring LinuxCNC homed flags does not establish physical position. Local HAL access is a privileged engineering interface, not an authentication boundary; a malicious local writer is not a supported threat model for this prototype. Public authentication, operator ownership, physical transport qualification, production calibration ranges, and target memory-order testing remain open.

The [current CNC1 manifest](../cnc1/evidence/manifest.json) links sources, executable module and evidence. The preceding 11-case milestone's covered sources/evidence and original manifest were copied byte-for-byte and hash-verified under [before-runtime-configuration](../cnc1/evidence/before-runtime-configuration/manifest.json) before edits. Its original compiled module hash is retained in that historical manifest; that prior binary is not separately archived. The unchanged 180-check ABI-v1 RTL regression is retained as historical baseline evidence, not relabeled as a new run.
