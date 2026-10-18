# CNC1 compiled LinuxCNC / actual RTL integration

This package proves the six-step/two-encoder reference end to end without machine access:

```text
LinuxCNC motion -> compiled cnc1.write -> CNC1 frames -> Verilator endpoint RTL
LinuxCNC feedback <- compiled cnc1.read <- CNC1 frames <- RTL emitted counters
```

The simulation profile maps three LinuxCNC joints to mask 7. The separate compiled harness exercises all six generators. `src/cnc1.c` contains bounded common protocol/state/scaling code, `src/hal_cnc1.c` exposes separate read/write functions, and `src/sim_transport.cpp` is the replaceable software-only transport. The HAL build still links only simulation; [experimental SPI transport](../reports/SPI_TRANSPORT_IMPLEMENTATION.md) has separate evidence. Python remains outside the cyclic path.

The [actual-runtime configuration service](../reports/RUNTIME_CONFIGURATION.md) now discovers that runtime, previews stopped XYZ scale changes and commits through a compiled inhibit/guard. The real LinuxCNC acceptance run changes 200 to 250 steps/mm, clears homing, then demonstrates a separately commanded 1 mm move producing 250 returned pulses. A structured CLI uses the same service. Complete profile persistence and physical machine commissioning remain separate work.

[Durable XYZ calibration](../reports/PERSISTENT_RUNTIME.md) now adds a default persistent startup inhibit and checksummed journal/generation witness. Nine independent LinuxCNC launches demonstrate saved calibration, explicit startup activation, abrupt client-process interruption and wrong/missing/corrupt/older authority rejection. `tools/run_persistent.sh` runs that workflow. The older `run_linuxcnc.sh` explicitly opts into volatile laboratory mode to preserve its 26 regression cases. Full machine-profile/cartridge integration remains separate.

See [integration evidence](../reports/CNC1_INTEGRATION.md) and [ABI v2](PROTOCOL_V2.md). Baseline ABI v1 remains available with default RTL parameters. No eight/four implementation or target timing qualification is claimed.

On this workstation, with the existing isolated Debian rootfs described by `controller_backend`:

```powershell
wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/build.sh
wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/run_linuxcnc.sh
```

Build prerequisites: WSL Verilator 5.048 and its include files; GCC/G++/make and `linuxcnc-uspace-dev=1:2.9.4-2+deb13u1` inside the task rootfs. Exact package versions are in `evidence/build-packages.tsv`. Installing those build prerequisites required a 67.1 MB download and 256 MB inside that isolated filesystem. No host machine drivers or devices are used.

The launcher uses private network, IPC, PID and mount namespaces, no host machine-device mounts, an explicit simulation environment flag and a new run ID. It loads only the dedicated simulation profile. `cnc1.fault` connects to actual LinuxCNC joint amplifier-fault inputs. It never launches the user's existing machine UI or profile. Generated build output stays under ignored `build/`; checked-in logs/JSON and SHA-256 manifests preserve the evidence.
