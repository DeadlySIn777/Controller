# Electrical design review package

Revision electrical-r0.1, 28 September 2026. This advances the six-joint study into a machine-readable electrical design and editable KiCad circuit blocks (two-joint review circuit, six-joint transmitter block, two-ABZ receiver block). **The complete controller remains unreleased.** Numerical limits below are proposed acceptance targets; none is a qualified product rating.

## What exists and how to review it

- [Electrical ledger](../hardware/electrical-design.json): interfaces, actual device-channel assignments, power domains, estimated rail reservations, component/support inventory, permission contract and blockers.
- [Channel allocation](../hardware/channel-map.csv), [terminal allocation](../hardware/terminal-map.csv), [power budget](../hardware/power-budget.csv), and [BOM snapshot](../hardware/bom-snapshot.csv): generated views. The BOM contains candidate parts and required support bundles, including unresolved MPNs; it is not a purchasing BOM.
- [Two-joint transmitter schematic](../hardware/tx_bank/tx_bank.kicad_sch), [project](../hardware/tx_bank/tx_bank.kicad_pro), [PDF](../hardware/tx_bank/tx_bank.pdf), [netlist](../hardware/tx_bank/netlist.xml), [circuit BOM](../hardware/tx_bank/bom.csv), and [ERC report](../hardware/tx_bank/erc.json). The embedded/project-local symbols make the circuit editable without downloading a symbol library.
- [Six-joint transmitter block](../hardware/tx_six/tx_six.kicad_sch): three AM26C31 banks and all twelve STEP/DIR channels, with [PDF](../hardware/tx_six/tx_six.pdf), [netlist](../hardware/tx_six/netlist.xml), [circuit BOM](../hardware/tx_six/bom.csv), [ERC report](../hardware/tx_six/erc.json) and [validation record](../hardware/tx_six/validation.json); described in [SIX_JOINT_TRANSMITTER.md](../reports/SIX_JOINT_TRANSMITTER.md). Regenerate with `python tools/hardware_build_tx_six.py`, validate with `python tools/hardware_validate_tx_six.py`.
- [Two-ABZ receiver block](../hardware/rx_abz/rx_abz.kicad_sch) with its [ERC report](../hardware/rx_abz/erc.json) and [validation record](../hardware/rx_abz/validation.json); described in [ENCODER_RECEIVERS.md](../reports/ENCODER_RECEIVERS.md).
- [Executable review](../tools/hardware_validate.py) and [fault-injection tests](../tests/test_hardware_validation.py). A passing consistency result is distinct from manufacturing release. `--release` fails while design/qualification blockers remain.

Regenerate the ledger with `python tools/hardware_build_design.py`; regenerate the review circuit with `python tools/hardware_build_tx_schematic.py`. Regeneration overwrites generated artifacts, so commit/edit the generator when changing their authoritative definitions, or preserve manual schematic changes before regenerating. Never replace a finished manually reviewed board with this circuit generator.

## Architecture decision for this work

Use the assembled **ROCK 3C RS112-D2** as the engineering host and develop a separate motion/I/O board. Its existing network, video and USB hardware reduces first-carrier work. **CM3 SODIMM RM117-D2E16 remains a production-carrier alternative**, requiring its two connector interfaces, Ethernet PHY path, boot/power and mechanical review. The small current merchandise difference does not establish a lower completed module-carrier cost. This is an integration judgment, not a LinuxCNC qualification result. [Radxa ROCK 3C](https://radxa.com/products/rock3/3c/), [CM3S schematic](https://dl.radxa.com/cm3s/docs/hw/RADXA_CM3S_V1.5_SCH.pdf)

The host runs local LinuxCNC, services and the preserved UI. Motion SPI is a dedicated internal link; the host's Ethernet/Wi-Fi/USB serve the customer interface. The Raspberry Pi-specific SPI driver cannot simply be assumed to work on Rockchip. The new gateware reference is a custom protocol, not HostMot2 compatibility. No host GPIO or FPGA ball is assigned until the real peripheral/package review is complete.

The ESP uses a separate 3.3 V branch. Its proposed board signals are UART TX/RX, observed `PGOOD`, observed `MOTION_DISARMED`, and local recovery/debug. **No STEP, enable, host-reset, watchdog-service, or analog-command authority connects to the ESP.** Its optional GPIO configuration defaults to disconnected in firmware. Hardware must prevent backfeeding through UART/status when either side loses power.

## Interface proposal and allocation

| Interface | Proposed electrical contract | Capacity / remaining gate |
|---|---|---|
| STEP/DIR | 5 V-supplied differential transmitters; 3.3 V logic inputs; no galvanic isolation | 6 joints / 12 signals. Initial target 250 ksteps/s, 2 µs minimum STEP high/low and DIR guard; actual drive and cable can impose slower limits. |
| Encoder | Differential A/B/Z, 3.3 V receiver logic; two protected 5 V, 200 mA encoder supplies | Two encoders / 6 signals; 1 Medge/s per signal study target. These are not six joint feedback ports. Receiver termination, common mode, open-wire state and cable tests remain open. |
| Inputs | 22 sinking nominal-24-V DC channels for PNP outputs or contacts switching field positive | 0–30 V input target; low 0–5 V, high 15–30 V, intermediate undefined. Group isolation to logic; no NPN/AC/universal-voltage claim. |
| General outputs | Eight nominal-24-V sourcing channels, 18–30 V field supply | 0.5 A continuous target/channel, 2 A per four-channel bank. Load inrush, clamp energy and thermal limits unqualified. |
| Drive enables | Six separate sourcing channels, same field supply | 50 mA target/channel; drive must accept this electrical type. These do not provide rated STO. |
| Spindle analog | Isolated 0–10 V, minimum 10 kΩ receiver load | One DAC/amplifier path: DAC80501 internal 2.5 V reference at gain 1 (0–2.5 V) into an OPA197 gain-four stage (30k/10k) on the 12 V rail, leaving ≥2.35 V DAC headroom at the 4.85 V analog-5 V minimum and ≥1.4 V amplifier headroom at 11.4 V; a 0–5 V DAC range with gain two cannot reach 10 V below a 5 V rail. Physical zero clamp, accuracy, filtering, monitoring and short protection incomplete. Separate spindle run must also turn off. |

Six homes, probe, toolsetter, door/protective-system status, spindle fault/ready, hold/start, lubrication status and one spare use all sixteen general inputs. Six drive alarms are additional. Eight general outputs include spindle run/direction, flood, mist, lubrication, air and two spares. Separate positive/negative limits on every joint need expanded input capacity.

**The 250 ksteps/s electrical goal is unachieved.** The current reference gateware caps the accumulator increment at `0x01000000`, giving **195,312.5 steps/s at 50 MHz**. Keep that implementation limit separate from the desired electrical capability. Neither number is a measured end-to-end machine rate; changing the cap or pulse timing needs renewed implementation and electrical validation.

The ledger maps 54 direct digital signals plus 30 support/reserved signals: **84 proposed GPIO uses**, before resolving dedicated configuration resources and bank restrictions. The current endpoint reference itself exposes 31 pad signals: clock/reset/inhibit, four SPI wires, twelve STEP/DIR, six ABZ, motion permission, endpoint-ready and four fault indications. `spi_miso_oe` belongs inside the board wrapper; it is not another external pad.

The 96-position terminal study preserves the earlier 12 × 8 pricing provision. It includes 74 necessary signal/reference positions, power/commons and six explicitly unconnected reserve positions. Connector positions are proposed terminal labels; they are not footprint/package approval. The mixed supply/reference allocation at `JPOWER` needs keying/layout review and may split into multiple connectors. The schematic's J1/J2 are boundary connectors for a standalone two-joint circuit, not that final terminal product.

## Actual transmitter circuit and voltage compatibility

The retained two-joint review circuit (`hardware/tx_bank`) implements one **AM26C31IPWR** bank with four series-resistor provisions, four data pulldowns, one enable pulldown, 100 nF bypass and 1 µF local bulk. The six-joint block (`hardware/tx_six`, [report](../reports/SIX_JOINT_TRANSMITTER.md)) now draws that bank three times as U1/U2/U3 for ledger TX0/TX1/TX2 with all 24 JTX positions; it passes KiCad ERC and exact netlist/ledger checks, but it is still a block, not the controller schematic. U1 pins 1/7/9/15 are data, 2/6/10/14 noninverting outputs, 3/5/11/13 inverting outputs, 4 active-high enable, 12 active-low enable, 16 supply and 8 ground. The exported netlist is checked against this PW16 map. [TI AM26C31 Rev. P](https://www.ti.com/lit/ds/symlink/am26c31.pdf)

Tie active-low enable high; pull active-high enable low. With permission absent, the driver pair becomes **high impedance**. That does not establish a defined low level at an arbitrary drive. Specify remote receiver fail-safe/bias and remove drive permission independently. Enabling/disabling can create a transition at the receiver; no glitch-free claim exists without the actual load/cable test.

The 5 V driver accepts TTL thresholds (high ≥2 V, low ≤0.8 V). A properly configured 3.3 V FPGA bank can therefore drive its logic inputs; no 5 V pull-up belongs on an FPGA net. The T20 reference offers 3.3 V I/O but is not a 5 V-tolerant GPIO device. Its advertised F256 GPIO count is 195, not evidence that our placement/bank/configuration plan fits. The C4 reference is commercial grade. [Efinix T20 v6.0](https://www.efinixinc.com/docs/trion20-ds-v6.0.pdf)

Initial 33 Ω source damping and 10 kΩ defaults require signal-integrity review. They do not provide external surge protection or prevent every partial-power injection path. The circuit has no FPGA, hardware-permission latch, line protection, or approved connectors. ERC checks its drawn connections; it does not qualify those missing blocks or the complete controller.

## Isolation and power tree

```mermaid
flowchart LR
    CP[Controller 18–30 V] --> CF[Physical fuse / reverse and transient protection / eFuse]
    CF --> C5[5 V converter, 6 A proposal]
    C5 --> SBC[ROCK 3C]
    C5 --> FL[FPGA 1.2 V and I/O 3.3 V]
    C5 --> ESP[Protected ESP 3.3 V branch]
    C5 --> TX[5 V transmitters / protected encoder supplies]
    FP[Separate field 18–30 V] --> FF[Field physical fuse / eFuse]
    FF --> DO[Protected sourcing outputs]
    FF --> F5[Field 5 V converter]
    FL -. isolated digital control .-> DO
    CF --> ISO[Isolated analog converter]
    ISO --> ANA[12 V amplifier / 5 V DAC]
    FL -. isolated SPI .-> ANA
```

`LOGIC_GND`, `FIELD_GND`, `ANALOG_GND` and chassis/PE are distinct nets. Inputs share their field domain, not channel-to-channel isolation. STEP/DIR and encoders are unisolated and refer to logic ground. An external drive that ties its signal and 24 V commons can bridge those domains outside the board; the compatible machine wiring must disclose that rather than promising complete system isolation.

ISO1212 already supplies input isolation: do not price another isolator per input. Its proposed Type-3-style network uses 562 Ω sense resistance and 1 kΩ threshold resistance; the manufacturer specifies pulse-capable 0.25 W MELF threshold resistors and local bypass. Filter values and probe/toolsetter delay require a separate tolerance/timing calculation. [TI ISO1212 Rev. G](https://www.ti.com/lit/ds/symlink/iso1212.pdf)

Four ISO7740F devices carry sixteen forward command channels, fourteen used. A fifth device faces the opposite direction for four aggregate bank faults. A sixth carries analog SPI/control. ISO7740 has four same-direction channels; it is not a three-forward/one-return device. Power both sides from their respective domains and retain external command pulldowns. Its F suffix supplies default-low behavior under specified loss-of-input conditions. [TI ISO7740](https://www.ti.com/product/ISO7740)

The T20 needs sequenced core and I/O rails, external configuration storage, clock, reset/configuration straps, debug and bypass for its exact package. No FPGA pin map, oscillator, flash MPN or complete sequencing circuit is frozen. Follow the manufacturer's unused-resource connections as well as active-power sequencing; do not invent a spare 2.5 V rail from another package's block diagram.

| Rail reservation | Estimated budget | Proposed capacity | Meaning |
|---|---:|---:|---|
| Main 5 V | 5.35 A | 6 A | SBC 3 A, transmitters 0.6 A, encoders 0.4 A, local conversion inputs (computed at 85% efficiency plus an explicit 0.05 A reserve each) and miscellaneous remainder. Less than 20% capacity headroom. |
| FPGA/I/O 3.3 V | 0.40 A | 1 A | Unmeasured allowance; FPGA switching estimate absent. |
| ESP 3.3 V | 0.70 A | 1 A | Separate branch and radio/startup allowance. |
| FPGA 1.2 V | 0.80 A | 1 A | Reservation, not a synthesized power estimate. |
| Field 24 V | 4.36 A | 6 A | Includes maximum proposed output loads; supplied separately from compute/display. |
| Field 5 V | 50 mA | 100 mA | Isolators, gate and diagnostic allowance. |
| Analog 12 V | 30 mA | 83 mA candidate | Includes downstream analog 5 V load; do not add it again at parent rail. |

With assumed 85% main-converter efficiency and 18 V minimum input, the 5 V reservation requires about 1.75 A input; analog provision raises core entry to 1.81 A. Converter efficiency is a calculation assumption. The 90 W adapter in the old costing basket is not approved: monitor voltage/power/startup behavior and remaining losses/headroom still need closure.

The power review changes two earlier cost provisions: **TPS62160 quantity 2 → 3**, for core, I/O and independent ESP rails; **TLV76050 quantity 2 → 1**, retaining only the analog rail. At 50 mA the former field LDO would dissipate 0.95 W from 24 V and 1.25 W from 30 V. Replace that role with an unselected field buck pending thermal design. TPS62160 accepts 3–17 V input; never connect it directly to nominal 24 V. [TI TPS62160](https://www.ti.com/lit/ds/symlink/tps62160.pdf)

## Entry fuses, eFuses and output defaults

Provide separately coordinated physical DC entry fuses for core and field power. Electronic branch protection controls overload/inrush and exposes useful diagnostics; the existing TPS4H160 channels already provide protected switching. Fuse voltage/current/breaking capacity, cable ampacity, source foldback, time-current/I²t, inrush, semiconductor SOA and inductive energy remain explicit selection inputs. Do not infer that a fuse will clear from its ampere marking alone.

TPS2663 is a candidate family, not a selected complete circuit: 4.5–60 V operating input, adjustable 0.6–6 A current limit and configurable latch-off. Reverse-polarity protection requires the external FET arrangement. Field protection should latch off; recovery must leave motion disarmed. Exact variant, resistors/FETs/TVS, limit tolerance, power dissipation and fuse coordination are unresolved. [TI TPS2663](https://www.ti.com/product/TPS2663), [project protection strategy](POWER_PROTECTION.md)

The hardware permission expression is `RAILS_OK AND CONFIG_VALID AND EXTERNAL_PERMIT AND HW_WATCHDOG_OK AND FPGA_ARM_LATCH`. It must act on STEP enable, all fourteen field commands and spindle permission. The FPGA clears its arm latch on fault/reset and requires explicit rearming. Hold arm-related controls low during boot/update; direction and analog state alone never confer permission.

The FPGA watchdog monitors accepted motion progress. The separate TPS3431 protects against lost FPGA execution/clock/configuration; its WDI must represent useful completed control work, not a free-running toggle or ESP/network heartbeat. The reference endpoint implements a 5 ms timeout (`WATCHDOG_CYCLES = 250000` at 50 MHz, recorded in the ledger as `permission.rtl_watchdog_ms` and derived from the RTL by the generator and checked by the validator); 20 ms is the separate external/supervisory study value (`permission.external_watchdog_study_ms`). Their physical timing, tolerance and total machine response are unapproved. Hardware gate/latch circuitry is still missing; software tests do not implement it. [TI TPS3431](https://www.ti.com/lit/ds/symlink/tps3431.pdf)

The current reference RTL does not expose the required external useful-progress WDI signal. Endpoint-ready and a clock-running signal cannot substitute for it. This is a named integration blocker in the electrical ledger.

| Condition | Required field behavior | Evidence still needed |
|---|---|---|
| Boot, reset, unconfigured FPGA | Driver G low; output commands low; spindle run off | Actual partial-power ramp and pin-default tests |
| Motion watchdog expires | Permission removed and fault latched | Complete gate/latch schematic, propagation and loaded test |
| FPGA clock stops | External watchdog removes permission | WDI coupling, clock-stall injection and timeout tolerance |
| Field power disappears/returns | Outputs remain off until deliberately rearmed | No backfeed; status isolation; latch persistence/reset policy |
| ESP crashes or loses power | Diagnostic service unavailable; no parallel output authority | Branch-short and UART/status partial-power tests |
| Analog command fails | Spindle run withdrawn; command-zero mechanism evaluated | Zero clamp, physical output monitoring and compatible VFD behavior |

These are operational controls. Machine E-stop/STO, brakes and stored-energy control need their own machine-level design. A sudden loss of pulses or power is not coordinated deceleration.

## Release gates and manufacturing handoff

The canonical manufacturing manifest belongs in [manufacturing](../manufacturing/). Hardware evidence, including hashes of every schematic block, is summarized in [review manifest](../hardware/review-manifest.json), regenerated by `python tools/hardware_record_review.py`. No empty Gerber/CPL/PCB files are supplied to satisfy filenames.

PCBWay requires an actual fabrication/assembly Gerber set, BOM and SMT centroid file. The centroid needs reference designators, X/Y, rotation and side; assemble the release package in one revision. Add actual drill/outline data, stackup/fabrication specification, DNP/approved alternatives, assembly polarity/orientation drawings, programming images/instructions, test fixture and quantitative acceptance criteria. Stencil is included in the assembly quotation; programming and functional testing need explicit scope. [PCBWay files](https://www.pcbway.com/assembly-file-requirements.html), [programming](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/What_document_is_needed_for_IC_program_.html), [testing](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Can_you_do_test_after_assembly__What_documents_should_I_offer_.html)

Before a complete schematic freezes: close the exact device/package/footprint map, all power/default paths, rated circuit support networks, real machine interface/load limits and configuration/recovery plan. Before layout release: close synthesized FPGA fit/timing, reviewed host pinmux, full schematic ERC and controlled geometry/routing/return paths. Before manufacturing authorization: complete board DRC, BOM/CPL/Gerber cross-checks, pricing and programming/test scope. Final product claims additionally require physical bring-up, fault/SI/EMC/thermal tests and machine acceptance.

Editable hardware and firmware remain part of the product. The CLI/UI capability record must report port class, range, load limit, ground/isolation domain, installed option and evidence status. Guided wiring can derive labels and compatible profiles from that record. Neither a custom configuration nor an AI suggestion can turn the current 24 V sourcing output into a dry contact or an arbitrary-voltage port.
