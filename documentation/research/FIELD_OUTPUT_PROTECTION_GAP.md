# Field-output protection gap found during integration

28 September 2026. Source review only; no output circuit or substitution is released.

The frozen six-joint ledger proposes four TPS4H160BQPWPRQ1 quad high-side drivers. TI's [TPS4H160-Q1 Rev E, June 2025](https://www.ti.com/lit/ds/symlink/tps4h160-q1.pdf), page 6, limits supply voltage to 48 V for transients shorter than 400 ms; its operating maximum is 40 V. The current entry candidate uses SMCJ30CA, whose specified reference pulse clamp is 48.4 V. That number already exceeds 48 V before wiring/ringing and temperature allowances. The eFuse overvoltage cutoff has finite response and does not establish an instantaneous clamp at the downstream driver.

**Do not approve TPS4H160 protection from the current input TVS/eFuse alone.** The remaining design must provide a source- and load-energy-qualified clamp below the driver's limit, or select another output stage with sufficient voltage withstand, then recalculate power, channel protection, isolated controls and cost. Sustained overvoltage and returned inductive energy are separate cases.

The similarly named TPS274C65 is not a 65 V replacement: [TI's product specification](https://www.ti.com/product/TPS274C65) lists a 6-36 V operating range; 65 refers to the nominal milliohm on-resistance. No replacement is selected by this note. The frozen ledger is retained as historical design input, with this finding an explicit integration release blocker.

A change of driver cannot be justified by nominal voltage alone. Check its absolute versus operating limits, local negative output clamp, short circuit and repetitive inductive energy, current-limit tolerances at the actual 0.05 A / 0.5 A channels, power-off defaults and backfeed behavior. Field permission remains a separate unimplemented circuit function.
