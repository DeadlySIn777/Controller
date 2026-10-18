# IS-2 differential fast-input receiver region

`motherboard_fast_inputs.kicad_sch` is an editable **on-motherboard** source region: four AM26LV32EIPWR PW16 receivers use all sixteen channels for ENC0–3 A/B/Z, FREQ0/1 and MPG A/B. It preserves the historical two-encoder `hardware/rx_abz` source and evidence separately. This region has no probes, pendant/status acquisition, accessory ID/presence logic or port-supply limiters; those remain explicit parent engineering work.

Native KiCad XML/independent checks cover every fitted pin, source model, differential polarity, channel assignment, hard enable, bypass, termination, protected-feed boundary, chassis separation and nonphysical boundary exclusion. Fresh native ERC has **zero violations and no ignored checks**. This is circuit evidence, not a complete controller, routed PCB, FPGA allocation or measured input capability.

There are **28 physical footprints: 26 fitted parts and two explicit DNP termination positions**. Four receivers, eight capacitors and fourteen fitted 120-ohm 0.5 W terminations form the baseline. MPG R15/R16 stay DNP/open because loading the requested 2.5 V, 1 mA TTL reference with 120 ohms would demand about 20.8 mA at 2.5 V differential. A differential MPG termination profile needs source/cable qualification. DNP means open, never a short/bypass.

The nine `B1`–`B9` symbols are **nonphysical schematic boundaries**, excluded from PCB/BOM with no selected MPN or footprint. They preserve logical XE0–3, XF and XH1 order and hand off protected feeds, logic, chassis, reference and missing frontend signals. They do not count as manufactured connectors, detectors or supply circuits. Encoder feeds must be independently protected by the parent; receiver outputs do not grant motion permission.

All receiver G and /G pins connect to IO_3V3: G high enables receivers. The outputs support partial power-down according to the component datasheet. Open-input fail-safe does not guarantee the state of a shorted or terminated disconnected pair; no hardware cable-loss detector is implemented here. Do not infer valid encoder feedback from a static logic level. These are differential interfaces, not general 12/24 V field inputs.

Source review and exact open gates are in [the report](../../reports/motherboard-fast-inputs-20260930/SOURCE_REVIEW.md). Stock KiCad PW16 pin order/pitch is verified, but its pad geometry differs from TI's example; land/mask/stencil and solder-joint qualification remain open. External surge protection, shield/return layout, decoupling placement, whole-board power/thermal/EMC, FPGA pins, cable/source loading and physical rate tests remain unfinished. No manufacturing release is claimed.

Reproduce the source, then native exports/checks and independent validation:

```powershell
python tools/hardware_build_motherboard_fast_inputs.py
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml --output hardware/motherboard_fast_inputs/netlist.xml hardware/motherboard_fast_inputs/motherboard_fast_inputs.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json --severity-all --exit-code-violations --output hardware/motherboard_fast_inputs/erc.json hardware/motherboard_fast_inputs/motherboard_fast_inputs.kicad_sch
python tools/hardware_validate_motherboard_fast_inputs.py
python -m unittest discover -s tests -p test_motherboard_fast_inputs.py -v
python -m unittest discover -s tests -p test_rx_abz.py -v
```
