# CNC1 compiled LinuxCNC / actual RTL integration

This package proves the six-step/two-encoder reference end to end without machine access:

```text
LinuxCNC motion -> compiled cnc1.write -> CNC1 frames -> Verilator endpoint RTL
LinuxCNC feedback <- compiled cnc1.read <- CNC1 frames <- RTL emitted counters
```

The simulation profile maps three LinuxCNC joints to mask 7. The separate compiled harness exercises all six generators. `src/cnc1.c` contains bounded common protocol/state/scaling code, `src/hal_cnc1.c` exposes separate read/write functions, and `src/sim_transport.cpp` is the replaceable software-only transport. There is no physical SPI implementation. The existing Python operator adapter is not used in the cyclic path.

See [integration evidence](../reports/CNC1_INTEGRATION.md) and [ABI v2](PROTOCOL_V2.md). Baseline ABI v1 remains available with default RTL parameters. No eight/four implementation or target timing qualification is claimed.

On this workstation, with the existing isolated Debian rootfs described by `controller_backend`:

```powershell
wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/build.sh
wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/run_linuxcnc.sh
```

Build prerequisites: WSL Verilator 5.048 and its include files; GCC/G++/make and `linuxcnc-uspace-dev=1:2.9.4-2+deb13u1` inside the task rootfs. Exact package versions are in `evidence/build-packages.tsv`. Installing those build prerequisites required a 67.1 MB download and 256 MB inside that isolated filesystem. No host machine drivers or devices are used.

The launcher uses private network, IPC, PID and mount namespaces, no host machine-device mounts, an explicit simulation environment flag and a new run ID. It loads only the dedicated simulation profile. `cnc1.fault` connects to actual LinuxCNC joint amplifier-fault inputs. It never launches the user's existing machine UI or profile. Generated build output stays under ignored `build/`; checked-in logs/JSON and SHA-256 manifests preserve the evidence.
