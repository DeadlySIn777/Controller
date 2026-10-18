# FPGA core candidate review

29 September 2026. The editable candidate sheet is `hardware/fpga_core/fpga_core.kicad_sch`. It uses an Efinix T20F256I4 package allocation sourced from the manufacturer pin workbook and adds twelve STEP/DIR pin pairs, reserved enable/home/alarm capacity, four logical ABZ encoder groups, configuration flash, clock, host SPI and status boundaries.

The configuration reset and user-logic reset are separate. U3 combines the qualified upstream configuration reset with the service-run input for `FPGA_LOCAL_RESET_N`. U4 is a Schmitt buffer fed by the CDONE/10 kΩ/1 µF candidate delay network, and U5 ANDs that delayed signal with service-run to drive `FPGA_USER_RESET_N` at package ball D5. CDONE loss and the independent machine-permission gate still inhibit motion; the RC path is not a safety timer. The delay threshold, tolerance, discharge behavior, JTAG `ENTERUSER` handoff, partial-power behavior and HDL startup synchronizers remain qualification gates.

Current checks: native KiCad export reports zero ERC violations; the independent validator and its 26 mutation tests pass. The source is a candidate only: no Efinity package fit, placement, routed timing, bitstream, PCB layout/DRC, power-integrity simulation, physical measurement or industrial qualification exists. Twelve STEP/DIR pins are capacity, not twelve complete machine channels; individual enable stages, extra alarms/homes, receiver expansion, full I/O and runtime protocol support remain unfinished.

The T20, flash, clock, logic-gate, resistor and capacitor choices remain candidate parts with unassigned or manufacturer-review footprints where stated in the design manifest. The schematic is not a fabrication release.
