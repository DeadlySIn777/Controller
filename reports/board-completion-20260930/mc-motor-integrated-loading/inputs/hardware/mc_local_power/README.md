# Motion-card local power candidate

30 September 2026, `mc-local-power-r0.1`. This is an editable circuit implementation and source-backed component population. It supplies the replaceable motion card locally from its **switched CORE_5V slot feed**. It preserves the older central three-regulator and four-window studies as history. It is not a release to manufacture.

The source generator creates `mc_local_power.kicad_sch`, exact-part `bom.csv`, `design.json` and three manufacturer land-pattern candidates. Native KiCad XML export is in `netlist.xml`; independent expected topology is in `tools/hardware_validate_mc_local_power.py`, with mutation checks in `tests/test_mc_local_power.py`. A passing check records circuit consistency and bounded arithmetic; it cannot certify assembled behavior.

## Implemented circuit

Two TPS62901RPJR converters derive 1.2 V and 3.3 V. The core converter retains 1 MHz forced PWM and a 2.2 µH XGL4020-222MEC. The I/O converter uses 2.5 MHz forced PWM and a 1 µH XGL4020-102MEC. Both use a 6.8 nF C0G ramp capacitor and exact input/output-capacitor order codes.

Three LTC2962HUD#TRPBF supervisors independently qualify the input, core and I/O windows. The 5 V window enables the core; the core window enables I/O; the I/O window releases reset. Every stage has a 160–240 ms release delay. Regulator power-good signals are diagnostics and do not substitute for window supervision. Reset reaches the FPGA through a SN74LVC1G17DBVR powered from the destination I/O rail.

This is an **IS-2 hardware proposal**, not silent compliance with frozen IS-1. [The proposal](IS2_LOCAL_POWER_PROPOSAL.md) records the supervisor component deviation and increased slot power allowance. Frozen IS-1 is unchanged; logic-owner agreement and integrated reset/permission behavior remain open.

## Integration boundary

`B1` is explicitly excluded from board and purchasing BOM. It represents internal schematic wiring, not a selected connector.

| B1 pin | Net | Meaning |
|---|---|---|
| 1 | CORE_5V | Switched slot feed; broad interface 4.85–5.15 V, normal static source 4.95–5.05 V |
| 2, 9 | LOGIC_GND | Shared logic return |
| 3 | CORE_1V2 | Locally regulated FPGA core/PLL source; downstream package filters and decoupling remain with FPGA |
| 4 | IO_3V3 | Locally regulated FPGA I/O, flash, clock and card support source |
| 5 | FPGA_CRESET_N | Destination-rail buffered rails-good/reset output, active high when valid |
| 6 | MC_RAILS_OK_5V | Raw supervisor qualifier; a **5 V domain node** that must never directly drive FPGA/3.3 V permission inputs |
| 7 | CORE_1V2_PG_OD | Raw converter open-drain diagnostic; external pull-up required |
| 8 | IO_3V3_PG_OD | Raw converter open-drain diagnostic; external pull-up required |

`FPGA_CRESET_N` can be the rails-good input to the existing FPGA reset AND chain or a separately integrated permission gate. It is push-pull: additional programming/reset requests must be combined upstream. Never wire another push-pull reset driver against it. Reset is not authorization to operate motors. Power-off card replacement and independent inhibition remain required.

The destination is 3.3 V logic, including the current reset-AND input; it is not an additional direct T20 reset driver. External high-state load is constrained to 1 mA and external low-state sink load to 100 µA. Including the fitted pull-down, the buffer's stated test-condition guarantees give high at least 2.4 V and low at most 0.1 V, leaving 0.4/0.7 V margins against the existing AND input's 2.0/0.8 V levels. These guarantees apply while the destination rail is valid. Zero-rail Ioff plus the pull-down is separately screened; intermediate partial-power behavior remains a measurement gate.

## Whole-card capacitance and power screen

The current FPGA source contributes **8.60 µF core and 35.51 µF I/O nominal**, including package bulk capacitors. Counting only the converter's 22 µF would miss this load. I/O at 1 MHz would exceed the converter's 50 µF effective limit at tolerance/temperature corners. The new 2.5 MHz selection allows the source's 100 µF effective ceiling, while the core stays at 1 MHz/50 µF.

The screen reserves another 2 µF nominal on the core and 10 µF nominal on I/O for integration, constrained to at most 10% initial and 15% temperature increase. Every added component must be charged to those allocations, including watchdogs, buffers and card identity electronics. These are bounded allocations, not permission to add capacitance without checking actual part limits.

The validator recomputes the complete capacitor upper bounds, startup output-charge current model, inductor peak model and converted slot current from the actual FPGA source. It reports **0.46735 A steady and 0.69205 A concurrent downstream startup** under 85% efficiency and 50 mA overhead per converter plus 10 mA supervision. The resulting proposal is **0.50 A steady reservation, at least 0.80 A downstream-startup allowance**. The frozen 0.45 A slot budget is exceeded by 17.35 mA and is preserved as a separate field. These arithmetic reservations are not measured efficiencies or guaranteed instantaneous inrush bounds.

The two regulator input capacitors plus three supervisor bypasses add **25.6795 µF maximum** under their stated initial/temperature bounds. Charging this input capacitance is a separate slot-limiter calculation and measurement; it is not included in the downstream ramp model. Preserve input-cap charging, retained-charge restart and all other module loads in PSM sizing.

Static initial/temperature threshold corners retain actual rail limits: CORE_5V 4.85–5.15 V, T20 CORE_1V2 **1.15–1.25 V** and IO_3V3 3.20–3.40 V. Some allowed broad input extremes intentionally hold reset. The historical 1.17–1.23 V ledger's sub-mV margins fail its recorded 400 ppm aging screen; that earlier result remains historical. This new circuit insets UV/OV thresholds within the actual T20 operating limits and passes initial/TCR **plus 400 ppm independent precision-resistor drift**, leaving more than 7 mV core margin at the worst modeled corner. This is not a relaxed FPGA electrical rating. Precision part numbers follow the manufacturer ordering scheme; price, availability and assembled lifetime suitability still need qualification.

## Remaining engineering gates

FPGA dynamic current and support loads, minimum effective capacitance versus DC bias, loaded startup slope/delay, switching frequency lower bound, transient regulation, magnetic temperature behavior, arbitrary partial power, retained-charge restart, shutdown ordering/discharge, brownout assertion delay/slew and lifetime drift are unfinished. Slot current-limit coordination, connector allocation, machine permission, PCB routing/DRC, assembled measurements and production pricing remain open. The current circuit has no physical validation and no supplier submission.

## Rebuild

Run from the repository root with the installed KiCad CLI and Python:

```powershell
python -X utf8 tools/hardware_build_mc_local_power.py
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml -o hardware/mc_local_power/netlist.xml hardware/mc_local_power/mc_local_power.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json -o hardware/mc_local_power/erc.json hardware/mc_local_power/mc_local_power.kicad_sch
python -X utf8 -m unittest discover -s tests -p test_mc_local_power.py -v
python -X utf8 tools/hardware_validate_mc_local_power.py
```

Source hashes include the external FPGA decoupling inventory. Refresh and revalidate after any changed FPGA load or capacitance source. Native ERC's four default ignored checks are explicitly recorded; no new ignored checks or waivers were added.
