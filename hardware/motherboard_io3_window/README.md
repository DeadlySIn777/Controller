# Source-backed IO3 monitor-window revision

MB-IO3-WINDOW-001 is an explicit, bounded correction to the implementation-only 3.20–3.40 V monitoring window. It preserves the actual machine contract, watchdogs, inhibits, health truth, isolation, all ICs/pins, delay and default wiring. Retained sources are unchanged. Parent integration must apply and verify the ledger; these isolated candidates are not PCB files or a manufacturing release.

Efinix T20 v6.0 Table 69 gives a 3.14–3.47 V recommended operating range for the current FPGA's 3.3 V I/O. Abracon ASE's fitted 50 MHz oscillator gives 3.135–3.465 V. Their intersection is 3.14–3.465 V. The older MC statement calling 3.20–3.40 V the actual T20 rating was mistaken; that narrower interval was an implementation choice. The archived IS-1 interface specification contains no numerical 3.20–3.40 V rail requirement. Ordinary logic, receiver, flash and controller operating ranges are broader; a future added device must be checked again against this intersection. T20 core limits, configuration/pin-bank voltage rules and input absolute ratings are unchanged.

Apply `apply_io3_monitor_window(tree, model, scope)` from `tools/hardware_apply_motherboard_io3_window.py` to copied native source trees before flattening/promotion. For `scope='mc'`, apply after MB-IO3-001, while R2061/R2069 still retain their original source MPNs. For `scope='motor'`, apply to the frozen 9xxx health source. The helper rejects unexpected original parts, connections and repeat application; it returns copies and a ledger. New series nodes remain private. No new library is needed; three additional standard 0603 resistor footprints are required.

Exact changes:

| Existing UV top | Existing OV top | New series ref | New exact parts |
| --- | --- | --- | --- |
| R2061 | R2069 | R18003 | UV TNPW060353K6BEEA 53.6k; OV TNPW060357K6BEEA 57.6k; series TNPW0603698RBEEA 698Ω |
| R9005 | R9007 | R18004 | Same exact parts |
| R9015 | R9017 | R18005 | Same exact parts |

Only the original OV top's pin 1 moves from IO_3V3 to its new private intermediate node. Each new 698Ω resistor connects from the original receiving IO3 rail to that node. The effective OV top is 58.298k. Bottom 10k PLT precision resistors, comparator sense endpoints, ground returns and all other component records are retained. A single 58.3k precision top was not silently assigned a guessed stock MPN: the composite uses three verified stocked catalogue parts. The attached direct DigiKey pages show all three exact MPNs in cut-tape stock; prices are an observation, not inventory held or a turnkey quote.

The independent corner screen uses LTC2962 H-grade sense bounds 0.4975–0.5025 V, ±15 nA sense current, 0.1% initial top tolerance, ±25 ppm/K over resistor temperature 0–85°C, and Vishay's 500 ppm / 1000 h general-operation drift bound with film ≤125°C. Top error screen is therefore 0.3%. Retained PLT bottoms use their existing conservative 0.1% total initial/TCR/drift screen; their exact lifetime and procurement qualification remain separately open.

All three UV trip intervals are 3.152642668–3.207490796 V; OV intervals are 3.385363941–3.444581221 V. Lower and upper guards before the actual operating limits are 12.642668 and 20.418779 mV. Against MB-IO3-001's conservative source/damping bounds, additional distribution/noise allowance becomes 42.722929 mV lower and 37.430837 mV upper. Actual PCB losses, sense-node noise, output ripple/load steps, current profile and thermal limits must still be verified. No maximum shallow-brownout delay is invented: LTC2962's 40 µs maximum still requires 10% overdrive. Voltage supervision is not surge clamping. Existing reset and permission responses remain unchanged; intermediate-power/photorelay timing still require qualification.

Native isolated MC: 51 fitted footprints / 164 physical pads; motor health: 65 / 216. All footprints load with KiCad 10.0.4. Both native ERC results have 0 errors, 0 warnings and no ignored checks. Independent native/model endpoint reviews pass. The combined source regression suite passes 114 tests, including bypassed series trim, wrong tolerance/MPN, reset mutation, independent net mismatch and unchanged original sources. There is no routed-PCB DRC or physical proof from these results.

Evidence: [T20 manufacturer datasheet](https://www.efinixinc.com/docs/trion20-ds-v6.0.pdf), [Abracon ASE](https://abracon.com/Oscillators/ASE.pdf), [LTC2962](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC2962-2963-2964.pdf), [Vishay TNPW e3](https://www.vishay.com/docs/28758/tnpw_e3.pdf). Exact ledger, independent arithmetic, procurement snapshot, native footprint inventory, tests and hashes are in `reports/motherboard-io3-upgrade-20260930/voltage-window-review/`.
