# PCBWay turnkey submission checklist

Snapshot: 2026-09-28T19:03Z. Board revision in the release manifest: `motion-io-r0`.

**Status: not ready for PCBWay.** No supplier submission, quote request or order has been made. `manufacturing/release-manifest.json` records `manufacturing_order_placed: false`, and `python tools/check_release.py` returns `ready: false` with 17 prototype blockers. This checklist lists every file and decision a PCBWay turnkey order needs, the state of each one in this repository, and the order in which to close them. It does not mark anything as complete.

Evidence classes are kept separate throughout. The classes are source inspection, host tests, target compilation, HDL simulation, FPGA family synthesis, vendor place-and-route, ERC, DRC and physical measurement. A green `check_release.py` result only means the manifest is consistent. It does not qualify hardware and does not authorize an order or machine operation.

## 1. What PCBWay asks for (fetched 2026-09-28)

Sources: [assembly file requirements](https://www.pcbway.com/assembly-file-requirements.html), [IC programming](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/What_document_is_needed_for_IC_program_.html), [test after assembly](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Can_you_do_test_after_assembly__What_documents_should_I_offer_.html), [PCB assembly service](https://www.pcbway.com/pcb-assembly.html) and the [online quote form](https://www.pcbway.com/QuickOrderOnline.aspx). The same pages are cited in `docs/ELECTRICAL_DESIGN.md` (Release gates).

- **Gerber:** RS-274X, the same set used for fabrication. The assembly minimum is silkscreen, copper and solder paste. A complete fabrication order also needs solder mask, board outline and drill data.
- **BOM:** .xls, .xlsx or .csv. A turnkey or partial-turnkey BOM needs these columns: Line#, Quantity Per Part Number, Reference Designator, Part Number, Part Description, Package, Type (surface mount, thru-hole or hybrid), Manufacturers Name, Manufacturers Part Number and Distributors Part Number.
- **Centroid / pick-and-place (XY):** reference designator, X, Y, rotation and side (top or bottom). List surface-mount parts only.
- **Assembly drawings, special instructions and photos:** strongly recommended but not normally required.
- **IC programming:** mark in the BOM which parts need programming and supply the image file (usually .hex). A PCBWay engineer checks feasibility and quotes a separate programming fee.
- **Testing:** AOI is standard. X-ray for BGA/IC areas is available on request, and LED testing is offered. Functional test follows the customer's written method: steps with pictures, ideally a video, and any special equipment. The customer must supply that equipment because the factory has only ordinary meters. Test time is billed after testing.
- **Fabrication form decisions:** board type/panelization, X/Y size, quantity, layer count, material and Tg, thickness, min track/spacing, min hole, solder mask and silkscreen colours, surface finish, finished outer and inner copper weight, via process (tented/plugged), impedance control, custom stackup, via-in-pad, and other options.
- **Assembly form decisions:** turnkey, kitted or combo; single or panelized; sides assembled; quantity; number of unique parts, SMD parts, BGA/QFP parts and through-hole parts; sensitive-components flag; accept substitutes; depanel; function test; firmware loading; conformal coating; flying probe; X-ray quantity; box build and harness options. The stencil is included with assembly.

## 2. Current repository state (read, not edited)

**`manufacturing/release-manifest.json`:** every one of the 23 artifact ids is a non-complete status. None has a path or hash.

- 17 ids are prototype-stage.
- 6 ids are production-only: `hardware_test`, `loaded_realtime_test`, `factory_test`, `system_integration_test`, `final_cost`, `compliance_review`.
- `pcbway_quote` carries a structured, empty record: `requires` (11 prerequisite ids), study `quantities` [1, 10, 100, 1000] and `submission: null`.

**`hardware/review-manifest.json`** (recorded 2026-09-28T08:46Z):

- `status: partial_design_review_only`, `manufacturing_ready: false`, `erc_violations: 0`.
- `schematic_blocks` lists only `hardware/tx_bank`, `hardware/tx_six` and `hardware/rx_abz`.
- All 13 `release_items` are `blocked`.
- `no_supplier_contact`, `no_order` and `no_physical_connection` are all true.

**`hardware/validation-report.json`:**

- `consistency_pass: true`, `manufacturing_ready: false`, 0 errors.
- 3 warnings: CORE_5V 5.35/6 A headroom, CORE_24V 1.81/2 A headroom, and a STEP goal of 250 k/s against an RTL cap of 195,312/s.
- 54 `release_blockers`: 10 design items, 42 `MPN unresolved`, the GPIO bank-map item and the permission-circuitry item.
- Ledger counts: 55 channels, 84 FPGA signal/reserve GPIO, 96 terminals, 62 BOM groups.

**`hardware/bom-snapshot.csv`:**

- 62 groups: 20 `candidate` MPNs and 42 `required_unselected`.
- All 62 carry an `unresolved` note.
- The header is `id,mpn,qty,package,role,status,rail,unresolved`. It is a ledger view, not a PCBWay BOM.

**Schematic blocks present under `hardware/`.** These are separate KiCad projects, not a combined schematic, and no `.kicad_pcb` exists anywhere. A separate tool is still changing `hardware/`, so re-read these before relying on them.

| Block | Scope | KiCad ERC (`erc.json`) | Designator BOM | In review-manifest |
|---|---|---|---|---|
| `hardware/tx_bank` | Retained two-joint AM26C31 review circuit | 0 violations (2026-09-28T01:00) | 14 lines, 1 with MPN | yes |
| `hardware/tx_six` | Six-joint baseline, three AM26C31 banks, 12 differential STEP/DIR | 0 (04:18) | 41 lines, 3 with MPN | yes |
| `hardware/rx_abz` | Two-ABZ encoder receivers (baseline) | 0 (04:26) | 16 lines, 8 with MPN | yes |
| `hardware/encoder_power` | Two encoder supply branches, TPS2553DBVR-1 candidate | 0 (14:57) | 21 lines, 4 with MPN | **no** |
| `hardware/power_entry` | Two 24 V entry branches (CORE/FIELD), TPS26630 eFuse candidate. `requirements.json` status `design_draft_not_qualified`, 9 own release blockers | 0 (14:57; `exclusion` severity not included) | 46 lines, 8 with MPN | **no** |

All of this is six-joint/two-encoder baseline evidence. None of it covers the eight-motor/four-encoder candidate (`docs/EXPANDED_HARDWARE_TARGET.md`), which needs its own board revision, ledger, blocks and quote.

**Other evidence:**

- `gateware/synthesis/manifest.json` is Yosys Efinix-family mapping only: 4,072 LUT4, 2,132 ADD and 3,215 FF. It has no vendor place-and-route, package fit, static timing or bitstream.
- `reports/ESP_SERVICE_BUILD.json` records two ESP-IDF 5.5.4 esp32s3 images, compiled and linked, with `flashed: false`, `physical_hardware_tested: false` and `gpio_approved_for_hardware: false`.
- The Efinity toolchain is not installed on this host or in the WSL distro.

## 3. Checklist

Closure class codes:

- **D:** can be closed at a desk with the existing repository tools.
- **L:** needs PCB layout tooling on a frozen full schematic.
- **E:** needs the Efinix Efinity toolchain.
- **U:** needs a user decision.
- **P:** needs physical hardware or measurement.
- **S:** needs a supplier action that the user performs.

### 3.1 User decisions (close first)

| # | Decision | Current state / evidence | What closes it | Class |
|---|---|---|---|---|
| U1 | Which scope is `motion-io-r0`: the six-joint/two-encoder baseline, or the eight-motor/four-encoder candidate | Manifest does not bind a scope. All hardware evidence is baseline (`hardware/electrical-design.json` scope "Six-joint costing profile"). `docs/BUILD_PLAN.md` names the eight/four candidate as preferred next | User states the board scope. If eight/four, a new revision and fresh ledger, power, pin, BOM and timing work (no inherited totals) | U |
| U2 | First machine profile: drives, sensors, loads, spindle | `validation-report.json` blocker "Actual drive/sensor/load and first-machine profile compatibility not frozen"; `docs/HARDWARE_PRE_DESIGN.md` §18 item 1 | User names the machine, drives and spindle; ratings and rates are frozen against it | U |
| U3 | Compute module and host interface on this board | Engineering host ROCK 3C RS112-D2 with production alternative CM3 SODIMM (`electrical-design.json` `host`). CM4/CM5/CB2 carrier study (`docs/COMPUTE_CARRIER_STRATEGY.md`). None selected | User chooses a separate SBC with a link header, or a module carrier on this board. Carrier connectors, power and pinmux then enter the schematic | U |
| U4 | Display package for the first build and whether its power/interface is on this board | `docs/DISPLAY_TIERS.md`: 7–21 inch classes, none qualified. Display branch excluded from the ledger | User picks the first package. Display power/mounting is costed per package, independent of I/O capacity | U |
| U5 | Quote and order quantities | Study quantities 1/10/100/1,000 in `pcbway_quote.quantities` (from `docs/BUILD_PLAN.md`). Order quantity undecided | User states the quantities to quote, and later the quantity to order | U |
| U6 | Turnkey vs combo (customer-supplied parts), and whether substitutes are accepted | Not recorded | User decides which parts PCBWay sources (e.g. compute module, display) and the substitute policy per BOM line | U |
| U7 | Programming at PCBWay or in-house at bring-up | Not recorded | User decides per programmable part (FPGA configuration flash, ESP32-S3 module) | U |
| U8 | Functional test at PCBWay (fixture shipped to them) or in-house; X-ray for BGA | Not recorded | User decides the test scope. It feeds `programming_test_scope` | U |
| U9 | FPGA package: F256 0.8 mm BGA or the LQFP option | Candidate `T20F256C4` (`FBGA256 13x13mm 0.8mm`). `docs/BUILD_PLAN.md` asks to compare BGA and LQFP total board/assembly cost | Engineering comparison, then user cost acceptance. BGA drives layer count, via-in-pad/fan-out and X-ray | U + D |

### 3.2 Engineering evidence the project gate requires before submission

| Manifest id | PCBWay use | Current status (manifest) / evidence path | What closes it | Class |
|---|---|---|---|---|
| `full_schematic` | Source of BOM and CPL | `partial-circuits-only`. Five separate blocks (table above), no combined hierarchy | Desk-closable selections first (exact MPNs and footprints for the 62 groups; permission latch/gates; transient networks; analog zero clamp; FPGA/SBC/ESP pin map from E1). Then capture sheets 00–10 per `docs/HARDWARE_PRE_DESIGN.md` §13, reusing the existing blocks as hierarchical sheets through the `tools/hardware_build_*.py` generators | D (after U1–U4, E1) |
| `erc` | Not sent; release gate | `full-board-check-pending`. Only per-block ERC exists | `kicad-cli sch erc` on the full hierarchy with zero unexplained violations, recorded as erc.json | D |
| `electrical_review` | Not sent; release gate | `partial-block-review-only` | Named human review of the full schematic against the ledger ratings | D (human reviewer) |
| `fpga_build` | Source of the programming image | `family-mapping-and-functional-simulation-pass-device-fit-and-timing-unproved` (`gateware/synthesis/manifest.json`) | E1: install Efinity, T20 package pin CSV, IO placement per 3.3 V bank for all 84 signal/reserve GPIO, fit, 50 MHz static timing, power estimate, reviewed pin map fed back through `tools/hardware_build_design.py`. The useful-progress WDI RTL change lands first | E |
| `software_validation` | Not sent; release gate | `engineering-tests-in-progress` (`reports/VALIDATION.md`, `reports/ENGINEERING_STATUS.md`) | Host and simulation results bound to the released board revision and pin map | D |
| `link_prototype_measurement` | Not sent; gates final layout | `requires-engineering-host-and-fpga-evaluation-board-physical-measurement` | `docs/BUILD_PLAN.md` stage 5: measure the full read/compute/write cycle and fault behaviour under representative load on real host hardware and an FPGA evaluation board, recorded as physical measurement. The purchase is a user action | P (+U purchase) |
| `bringup_procedure` | Not sent; basis for the test method | `requires-final-board-map` | Staged power-on/programming/check procedure for the actual board map | D (after L) |

### 3.3 Files sent to PCBWay

| Manifest id | PCBWay requirement | Current status / evidence | What closes it | Class |
|---|---|---|---|---|
| `fabrication_spec` | Layers, material/Tg, thickness, copper weights, finish, min track/space/hole, via process, impedance control/custom stackup, outline, panelization | `blocked-by-layout`. No stackup recorded | Choose a stackup that PCBWay offers. Impedance targets come from the SPI/differential interface guides; BGA fan-out rules come from U9. Record it as its own file | D to draft, L to freeze |
| `pcb_layout` | Source of all outputs | `not-created`. No `.kicad_pcb` in the repository | Layout on the frozen schematic, after `link_prototype_measurement` | L |
| `drc` | Not sent; release gate | `blocked-by-layout` | KiCad DRC against the `fabrication_spec` rules with zero unexplained violations | L |
| `fabrication_zip` | Gerber RS-274X (copper, mask, silk, paste, outline) and Excellon drill | `blocked-by-layout` | Export from the approved layout only. No placeholder files | L |
| `bom` | .xlsx/.csv with the 10 turnkey columns | `draft-requires-exact-fitted-parts-and-designator-level-pcbway-column-export`. Only the ledger view `hardware/bom-snapshot.csv` and per-block designator BOMs exist, and these lack Manufacturer, Type and Distributor columns | Exact fitted MPNs, DNP and approved alternates. Then a KiCad BOM export from the full schematic with fields Manufacturer, MPN, Distributor PN, Type and Description, plus programmed-part marking (U7) | D (MPNs) + L (final designators) |
| `placement` | CPL: designator, X, Y, rotation, side; SMT only | `blocked-by-layout` | `kicad-cli pcb export pos` in mm from the approved layout, cross-checked against BOM designators | L |
| `assembly_drawing` | Recommended: polarity/orientation, special instructions | `blocked-by-layout` | Drawings from the approved layout | L |
| `programming_bundle` | Image file(s) and marked BOM lines | `requires-final-board-map`. The ESP images exist but are not bound to a board revision or approved GPIO. No FPGA bitstream or NOR image exists | Revisioned FPGA configuration-flash image (from E1 plus a proven boot/CRESET_N sequence) and ESP image for this board revision, with file hashes and the BOM lines to program | E + D |
| `programming_test_scope` | Programming instructions; functional-test method (steps, pictures, video), fixture and equipment; AOI/X-ray/flying-probe choice | `requires-final-board-map` | Written scope with quantitative acceptance limits, derived from `bringup_procedure` and U7/U8. Any fixture is built and shipped by us | D + P (fixture) |
| Assembly form counts | Unique, SMD, BGA/QFP and THT part counts; sides; sensitive parts | Not derivable yet | Count from the released BOM and CPL | D (after L) |

### 3.4 Quote and cost record

| Manifest id | Current status | What closes it | Class |
|---|---|---|---|
| `pcbway_quote` | `not-requested-design-incomplete`, `submission: null` | The user submits the released package. The user records `quote_id`, `quoted_at` (ISO 8601 date), `submitted_by` and `board_revision` as non-blank text, `quantities`, `package_sha256` (fabrication_zip, bom, placement) and `figures`: one entry per quoted quantity with `quantity`, `currency` (ISO 4217), `unit_price`, `setup_cost` and `lead_time_days`, copied from PCBWay's quote, plus the quote file itself as the hashed evidence. No figures are prefilled. `tools/check_release.py` rejects the record if it is marked complete while any of the 11 prerequisites is not complete, if an identity field is blank or not text, if the date is not ISO 8601, if the figures do not cover exactly the quoted quantities or hold a negative or non-numeric amount, if hashes differ from the released files, or if it is for another board revision | S (user) |
| `final_cost` (production) | `incomplete-quotes` | PCBWay's actual fabrication, parts, assembly, programming and test figures plus the display/enclosure package cost. The checker rejects `complete` while the quote is not complete | S + D |

### 3.5 Production-stage only (not needed for the first prototype submission)

These need a physical prototype, host and fixture:

- `hardware_test`: `requires-physical-prototype`
- `loaded_realtime_test`: `requires-selected-host-and-motion-link`
- `factory_test`: `requires-fixture-and-accepted-board`
- `system_integration_test`: `ui-display-motion-integration-pending`
- `compliance_review`: `requires-final-product-and-intended-markets`

All are class P or U.

## 4. Order of work

1. **User decisions U1–U4 (U):** board scope, first machine profile, compute/host interface and display package. Nothing in the schematic can be frozen without them. Then settle U9 with the user's cost input.
2. **Desk-closable ledger items (D):** exact MPNs and footprints for all 62 BOM groups, and the power-entry questions in `hardware/power_entry/requirements.json`: 18–30 V vs the proposed 19–30 V, core 2 A vs 3 A, and fuse data. Also the permission latch/gates, transient networks and analog clamp. Regenerate through `tools/hardware_build_design.py`, then run `tools/hardware_validate.py` and the hardware tests.
3. **In parallel, link measurement (P):** the user acquires an engineering host and FPGA evaluation board and runs the bounded motion-link prototype (`link_prototype_measurement`). This must finish before final layout.
4. **Efinity (E):** add the useful-progress WDI to the RTL. Then run fit, timing and power for the T20 package chosen in U9 and produce the reviewed pin/bank map, which is fed back through the generator.
5. **Full schematic and ERC (D):** capture the remaining sheets, integrate the existing blocks, run full-board ERC, then the human `electrical_review`.
6. **Fabrication specification (D, then L):** draft the stackup and rules against PCBWay's options before routing.
7. **Layout and DRC (L).**
8. **Exports (L):** Gerber/drill zip, CPL, assembly drawings and the PCBWay-column BOM, all from the approved design only.
9. **Programming bundle and test scope (E, D, P):** revisioned images bound to the board, the programmed BOM lines, and the bring-up procedure. Then the functional-test method, fixture and acceptance limits.
10. **Record each artifact in the manifest.** Each entry needs `complete`, `board_revision`, `reviewed_by`, `reviewed_at`, a relative path and SHA-256. Every id must have its own file; the checker rejects shared paths and identical bytes. Run `python tools/check_release.py` until it reports consistency. That result still is not an order authorization.
11. **User submits to PCBWay (S)** and records the quote in `pcbway_quote.submission`. PCBWay confirms programming/test feasibility and fees. Any order is a separate, explicit user decision.
12. **Production stage (P):** build and test the prototype (section 3.5), then record the final cost.

## 5. Commands

```sh
python tools/check_release.py --output reports/prototype-release-check.json               # exits 2 while blocked
python tools/check_release.py --stage production --output reports/production-release-check.json
python -m unittest discover -s tests -p test_release.py -v
```
