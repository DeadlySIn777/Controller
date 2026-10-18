# CNC3 structural RTL

This directory implements the first real CNC3 hardware layer, preserving the frozen IS-1 wire format: 96-byte CS_CMD and 176-byte CS_FB frames, big-endian fields and CRC-16/CCITT-FALSE. The original six-axis/two-encoder CNC1 RTL remains unchanged in `gateware/rtl`.

Implemented here:

- `cnc3_spi_transport.v`: dual active-low selects, mode-0/MSB-first SPI sampled in the core-clock domain, assertion-time feedback snapshot, streamed RX/TX CRC, exact-length rejection, eight-tick chip-select guards, four-tick high/low clock guards and overlap/handoff rejection. It also calculates the embedded MAINT frame's actual CRC-32C.
- `cnc3_command_validate.v`: complete frozen stateless command validation, including opcode/select matching, reserved/zero fields, structural session/sequence rules, all twelve rate fields, unmasked-rate rejection, configuration ranges/relations and embedded IOL1 validation. The generated rules match the original compiled C codec. Stateful session continuity and permission checks belong to the next hardware layer.
- `cnc3_frame_endpoint.v`: one-entry, byte-preserving atomic request boundary with backpressure/overrun rejection. `request_valid` means structurally valid; it does **not** mean semantically accepted or permitted to move. It exports all twelve rates and the complete output-image bytes together. It has no actuator outputs or assumed healthy providers. Its diagnostic link-fault latch currently clears only on reset.
- `cnc3_feedback_pack.v` and `cnc3_status_pack.v`: exact CNF3/CNS3 field packing from explicit provider inputs, with literal magic/ABI and mandated reserved zeros. They include twelve counter slots without claiming twelve physical encoders are present. The transport snapshots the continuously prepared payload and supplies its CRC. The `snapshot_start` notification follows capture; a provider must not wait for that notification to prepare the current response.

The `frozen` directory is a byte-verified local copy of the original specification/reference codec, not a modified specification. Its manifest records original provenance and exact hashes. These sources carry their existing proprietary notices; this directory makes no release/licensing promise.

Run a disconnected compiler/simulator check into a fresh output directory:

```powershell
python gateware/v3/tools/generate_protocol_rtl.py --check
python tools/check_cnc3_rtl.py --out reports/cnc3-rtl-validation-my-run
```

The second command actually compiles the original C oracle and new RTL. It tests golden and mutated commands, exact serial CRC/snapshot behavior, short/long frames, both select overlaps and zero-gap handoffs, 7/8-tick guard boundaries, 20 relative core-clock phases, reset, and queue overflow. Immutable inputs and logs accompany the result. One retained Verilator unused-CRC-bit warning is explicitly reviewed; any other warning fails the checker. `generate_protocol_rtl.py --write` regenerates only the three generated validator/packer files from the hash-verified frozen inputs.

Actual scoped evidence is recorded in `reports/cnc3-rtl-implementation-20261001`: original C/RTL checks, six compiled-copy fault controls, and Yosys Efinix-family synthesis with no-latch/mapped assertions. Family synthesis is distinct from T20 package fit, placement, routing and static timing. The synthesis top has large internal parallel buses; those are not physical FPGA pins.

Remaining work is concrete: the real stateful endpoint must enforce current session/next sequence, configuration generations, qualified physical I/O/identity/freshness, alarms, ARM/self-test/rearm, watchdogs, event/page scheduling, clean-stop continuity and atomic permitted application. Then connect the actual twelve generators/four base encoders, IOL1 providers and CNC3 LinuxCNC/HAL/Verilated transport. No full twelve-joint machine, 2 MHz product rating, loaded real-time behavior, electrical waveform or physical 20 ms inhibit qualification is established here. There is no deployment/bitstream target or fabrication release.
