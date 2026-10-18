# Historical six-joint core: terminal allocation and cost worksheet

Reviewed 18 October 2026. [Documentation index](README.md) · [current engineering evidence](../reports/ENGINEERING_STATUS.md).

This preserves the 28 September 2026 six-joint/two-encoder allocation and price worksheet. Its counts, circuit examples and dated USD references remain historical comparison inputs. The current [IS-2 motherboard](MOTHERBOARD_IS2.md) fits all twelve motor interfaces with individual enable/alarm, four ABZ, 24 general DI/16 smart DO and the remaining required I/O. US$400 is a preliminary controller-assembly reference; each screen/PSU/enclosure/harness/setup package needs a separate complete cost. The older display-inclusive Mesa-price envelope below is not the current offer.

## Historical six/two physical scope and direct signal count

Use external motor drives. Count independently driven joints, including separate gantry motors, rather than assuming six joints means six coordinate axes. The initial encoder proposal is one spindle A/B/index input and one auxiliary A/B/index input, usable for an encoder or an MPG. It does not provide six joint feedback channels.

| Function | Functional channels | Direct FPGA digital signals | External signal conductors |
|---|---:|---:|---:|
| Differential STEP/DIR | 6 joints; 12 differential transmitters | 12 outputs | 24 |
| Individual drive enable | 6, provisionally single-ended | 6 outputs | 6 |
| Individual drive alarm | 6 | 6 inputs | 6 |
| Differential encoder A/B/index | 2; 6 differential receivers | 6 inputs | 12 |
| General protected inputs | 16, additional to drive alarms | 16 inputs | 16 |
| General protected outputs | 8, additional to drive enables | 8 outputs | 8 |
| **Digital subtotal** | | **54: 26 outputs and 28 inputs** | **72** |

The spindle 0–10 V interface adds at least an output and reference terminal. Therefore this direct-wiring example requires at least **74 signal/reference positions**, before all field commons, encoder power, supply, shields, expansion and service connections. Connector count and terminal-position count are different. Differential enables would add six more conductors than this example.

On the logic side, add the host SPI bus, analog-control interface, expansion, clock/configuration/debug, fault monitoring and inhibit controls. For illustration, four host SPI signals and one PWM-based analog command raise 54 to **59 signals** before the other functions. A DAC implementation has a different interface count. Serial I/O can reduce FPGA pin use but introduces a bus, device cost, update latency and fault behavior. Neither count proves a package fits.

## Named allocations retained from the first costing exercise

| Input allocation | Count | Boundary |
|---|---:|---|
| DI00–DI05: joint home sensors | 6 | Independent joint homing; shared home/limit arrangements need an explicit machine profile |
| DI06: probe; DI07: toolsetter | 2 | Specify capture/filter delay separately from slow machine inputs |
| DI08: door status; DI09: machine protective-system status | 2 | Status monitoring does not replace the independent protective circuit |
| DI10: spindle fault; DI11: spindle ready | 2 | Actual drive signal type must match the input circuit |
| DI12: feed-hold request; DI13: cycle-start request | 2 | Requests handled by controller state and command-ownership rules |
| DI14: lubrication/pressure status; DI15: unassigned | 2 | Only one unassigned general input remains in this example |
| ALM0–ALM5: drive alarms | 6 additional | One per drive, independent of the sixteen general inputs |

Six homes plus separate positive and negative limits on every joint plus probe and toolsetter would require **20 general inputs**, before interlocks and spindle status. The proposed sixteen is not sufficient for that arrangement. An MPG's axis/scale selectors and enable switch also need inputs beyond its A/B/index connector.

| Output allocation | Count | Boundary |
|---|---:|---|
| DO00: spindle run; DO01: spindle direction | 2 of the 8 | This proposal uses run/direction semantics; FWD/REV is a distinct configuration |
| DO02: flood; DO03: mist; DO04: lubrication; DO05: air | 4 of the 8 | Actual load current/inrush and external relays must be defined |
| DO06–DO07: unassigned | 2 of the 8 | Six outputs remain after reserving run/direction; four are allocated above |
| EN0–EN5: individual drive enables | 6 additional | Drive command enables do not automatically provide a rated STO function |

## Electrical decisions required for a real cost

| Interface | Values that must be selected and documented |
|---|---|
| STEP/DIR | Line standard, output voltage, permissible common mode, drive input load, pulse widths/setup/hold, maximum rate, cable and fault/default behavior |
| Encoders | Differential/single-ended compatibility, common mode, maximum edge rate, termination, index capture, supplied encoder voltage/current |
| General inputs and alarms | Nominal 24 V is only a starting point: select operating/threshold ranges, PNP/NPN wiring, isolation groups, filtering, protection and fault response |
| Enables and outputs | Source/sink type, operating voltage, continuous/inrush current per channel and bank, inductive clamp energy, short-circuit handling, off-state leakage and reset state |
| Spindle analog | DAC versus filtered PWM, effective resolution, accuracy, load/current, settling, reference/isolation, output monitoring and fault value |
| Expansion | Named electrical interface and protocol, timing class, connector/power budget, configuration/versioning and removal behavior |

The initial expansion cost block stays open until its timing class is chosen. Slow auxiliary I/O and synchronized axis feedback must not be priced as interchangeable extensions.

## Historical cost blocks and reusable costing method

Keep separate sheets of evidence for quantity 1, 10, 100 and 1,000. Every completed row requires exact MPNs, fitted quantities, selected options, source/date, unit prices, subtotal, availability and exclusions. **Unknown means unknown, not zero.** Prices below are only the already recorded quantity-one component references in the [build plan](BUILD_PLAN.md).

| Block | Historical quantity/scope to price | Evidence recorded for that study |
|---|---|---|
| Linux compute | One module, RAM/eMMC/wireless | CM5 SC1588 reference $97.50; alternatives remain open |
| FPGA silicon | One, exact package/grade pending | T20F256C4 reference $12.75; no fit/timing proof |
| Service processor | One module | ESP32-S3-WROOM-1-N8 reference $5.66 |
| Compute carrier support | Module connectors, boot/recovery, thermal mounting | Unknown |
| FPGA support | Rails, clock, configuration storage, debug/programming | Unknown; avoid duplicate flash cost if selected package includes it |
| Internal motion link | Dedicated SPI candidate: physical path, protection/buffering as required | Unknown; no assumed Ethernet PHY savings booked yet |
| External service interfaces | Ethernet connector/magnetics/protection, USB data/power roles, ESP connection and antenna | Unknown; CM5 PHY does not include the carrier connector assembly |
| Differential outputs | 12 transmitter channels plus enable/default circuitry | Unknown |
| Differential inputs | 6 receiver channels plus termination/protection/supply | Unknown |
| Field inputs | 22 protected channels: 16 general plus 6 alarms | Unknown; fast capture inputs may have different front ends |
| Field outputs | 8 general plus 6 enable channels | Unknown; enable and general-load circuits may differ |
| Analog spindle | One complete 0–10 V path with required reference/isolation | Unknown |
| Expansion | One defined interface | Unknown; type and resources unselected |
| Fault and power supervision | Reset, useful-progress watchdog, inhibit gates, status, ESP power branch | Unknown |
| Main power conversion/protection | Supply input protection, logic rails, isolation where selected, backfeed prevention | Unknown |
| Connectors and harness | All terminals and mating plugs, display/service harnesses, shielding connections | Unknown; include the external conductor count above |
| PCB and assembly | Fabrication, placement, programming, good-unit test, yield/rework | Unknown |
| Touchscreen assembly | Complete monitor OR LCD/backlight/touch/controller assembly, cables and delivered freight | [Display study](../research/DISPLAY_COST_STUDY.md); no binding production quote |
| Final product hardware | Power supply, cooling, enclosure, display bezel/mounts, packaging | Unknown |
| Per-sale operating costs | Fulfillment, transaction fees, warranty and support allowance | Unknown; account consistently outside/inside the selected margin basis |
| Fixed development costs | Engineering, tooling, qualification, factory test fixtures | Unknown; report separately and explicitly if amortized |

Do not count a complete touchscreen monitor and its internal panel/controller twice. Do not count an included module PHY/RAM/eMMC twice. Include the supporting carrier parts that the module does not supply. Yield cost must be the cost per good saleable unit, not merely the cost per assembled PCB.

For a transparent zero-profit calculation, define advertised pre-tax price P, sales-channel discount d, percentage payment fee f applied to collected revenue, complete variable cost C excluding those payment fees, fixed transaction fee k, and fixed-cost recovery F/Q per sold unit:

`P_break_even = (C + k + F/Q) / ((1 - d) * (1 - f))`

This is a cost identity under those definitions, not a forecast or suggested margin. A selected profit target is separate. The historical Mesa-price bundle never established a complete cost; the current all-twelve motherboard and complete packages also require exact fitted cost evidence. SPI feasibility does not close either gap.

## Next deliverables

1. Cost the exact all-twelve motherboard population, protection, connectors and mating harnesses at 1/10/100/1,000 units; do not scale the six/two figures or omit four fitted motors for an eight-motor machine profile.
2. Include the actual FPGA/package, purchased compute/ESP/storage modules and all circuit support. Keep source pin checks, core mapping, full-device fit and physical timing separate.
3. Cost each complete screen/PSU/enclosure/harness/setup package and whole-motherboard service spare. No rack or custom motor-card purchase is required by the adopted architecture.
4. Carry unknown prices, fabrication, assembly, programming/test, yield, support and qualification explicitly. The [current board continuation](../reports/board-finish-20261017/README.md) is incomplete engineering evidence, not a PCBWay quote or production release.
