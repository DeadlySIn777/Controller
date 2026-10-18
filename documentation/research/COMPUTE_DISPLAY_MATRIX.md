# Compute, carrier and touchscreen comparison

Study snapshot: 2026-09-28; all prices USD before tax, shipping and duties. This extends the [display tiers](../docs/DISPLAY_TIERS.md) across 7/10/12/14/18/21-inch classes. The 21.5-inch screen is one tier. No hardware has been selected, ordered or qualified by this study.

The [machine-readable matrix](../WORKSPACE_REFERENCES.md#artifact-98beb87d352306c8) contains 144 cases: three exact compute candidates × six displays × two I/O scopes × four quantities. **Every complete manufactured-cost field is INCOMPLETE.** Actual listed merchandise is distinguished from missing carrier, power, protection, integration and manufacturing work. Screen size does not reduce I/O capability.

## Exact compute and reference carriers

| Compute variant | RAM / eMMC | Module, qty 1 | Retail carrier reference, qty 1 | Supply / compatibility limit |
|---|---|---:|---:|---|
| [CM4 CM4102016 / SC0669](https://www.pishop.us/product/raspberry-pi-compute-module-4-wireless-2gb-16gb-cm4102016/) | 2 / 16 GB | $87.50 | [Official CM4 IO Board, Adafruit 4787](https://www.adafruit.com/product/4787) $35.00 | OutOfStock microdata; no purchasable stock established; Manufacturer-matched reference carrier; CNC1/SPI and complete product remain unqualified |
| [CM5 CM5102016 / SC1588](https://www.pishop.us/product/raspberry-pi-compute-module-5-wireless-2gb-ram-16gb-emmc-cm5102016/) | 2 / 16 GB | $97.50 | [Official CM5 IO Board REV 2 SC1967](https://www.pishop.us/product/raspberry-pi-compute-module-5-io-board-rev-2/) $26.95 | OutOfStock microdata; Manufacturer-matched reference carrier; live/indexed availability conflicts; CNC1 remains unqualified |
| [BTT CB2 1020000449](https://biqu.equipment/products/bigtreetech-pi-2-cb2.js) | 2 / 32 GB | $125.99 | [BTT PI4B V1.0 1030000103 candidate](https://biqu.equipment/products/pi4b-adapter-v1-0.js) $28.98 | available=true; stock quantity not supplied; PRICE REFERENCE ONLY: exact CB2-to-PI4B pin/power/SPI support not established by this review; not a compatible ready-to-use package claim |

Both selected Pi module offers are out of stock. Adafruit separately lists the same 2GB/16GB/wireless CM4 configuration at $55, also out of stock; it is not a procurable low-cost assumption. CB2 provides 32GB eMMC versus 16GB in these Pi variants, so the table is not an equal-storage performance comparison. BIQU also lists the same CB2 SKU at $178.45 on another page; the $125.99 dedicated-page observation is preserved without averaging. The user's cheaper CB2 scenario remains unverified.

No published 10/100/1,000-unit module or carrier prices were established. All are null. Retail IO boards are engineering references, not the price of our custom carrier. CB2 + PI4B is specifically an unqualified pairing whose listed merchandise can be added arithmetically, not a claim of compatible CNC operation.

## Exact screen candidates and observed assembly prices

These include a manufacturer-matched screen/touch/control assembly or an enclosed monitor, not a bare LCD. They still exclude installation into the controller product. Regional US plug variants are comparison conventions only. Published 100+ tiers are carried to 1,000 without another discount; stock and capacity at that quantity are unverified.

| Class / actual size | Exact item / SKU | Native pixels | Qty 1 | Qty 10 | Qty 100 | Qty 1,000 |
|---|---|---|---:|---:|---:|---:|
| 7 / 7 in | [Waveshare 7inch HDMI LCD (B) / 10829](https://www.waveshare.com/product/7inch-HDMI-LCD-B.htm) | 800 × 480 | $45.99 | $44.99 | $44.29 | $44.29 |
| 10 / 10.1 in | [Waveshare 10.1DP-CAPLCD / 23739](https://www.waveshare.com/10.1dp-caplcd.htm) | 1280 × 800 | $78.99 | $77.39 | $76.27 | $76.27 |
| 12 / 12.3 in | [Waveshare 12.3inch 1920x720 LCD / 28481](https://www.waveshare.com/12.3inch-1920x720-lcd.htm) | 1920 × 720 | $109.99 | $107.99 | $106.59 | $106.59 |
| 14 / 14 in | [Waveshare 14inch 2160x1440 LCD (US) / 28504](https://www.waveshare.com/14inch-2160x1440-lcd.htm) | 2160 × 1440 | $179.99 | unknown | unknown | unknown |
| 18 / 18.5 in | [Luckfox 18.5-Touch-Monitor (US) / 32186](https://www.luckfox.com/18.5inch-Touch-Monitor) | 1920 × 1080 | $129.99 | unknown | unknown | unknown |
| 21 / 21.5 in | [Luckfox 21.5-Touch-Monitor (US) / 34985](https://www.luckfox.com/21.5-Touch-Monitor) | 1920 × 1080 | $159.99 | unknown | unknown | unknown |

The 10.1-inch page now returns $78.99 in live JSON-LD and its visible price, superseding the $74.99 search-index observation. The three smaller Waveshare pages expose actual quantity-price rows. The larger options have no verified bulk pricing. These are public offers observed during this study, not negotiated supplier or PCBWay quotations.

| Display | Package and unresolved integration |
|---|---|
| 7 in | matched LCD/touch/control assembly; HDMI cable and micro-HDMI adapter; USB-A to micro-B cable; RPi screw pack. **Power:** USB/5V-powered display; actual current/inrush and independent branch remain to specify. **Open:** No standalone PSU or finished bezel/enclosure included; 800x480 minimum viewport/touch-only workflow must pass UI audit; do not assume it is adequate; USB host sourcing and touch/power backfeed behavior. |
| 10.1 in | optically bonded LCD/touch/control assembly; HDMI 1m and USB-A/USB-C 1m cables; button board/cable, adapters and screws. **Power:** Exact display power/inrush and protected supply branch need approval; PSU is absent from listed package. **Open:** Finished bezel/enclosure, retention and power arrangement; Exact host native mode, touch revision, USB current and EMI qualification. |
| 12.3 in | in-cell capacitive LCD/control assembly; HDMI/USB-A-to-C/C-to-C cables and micro-HDMI adapter; stand, button board/cable, touch pen and cleaning cloth. **Power:** Wiki specifies 4.75–5.25V and 5W maximum; source current >=1A. Inrush and branch design unmeasured. **Open:** No PSU listed; final supply and enclosure/mounting cost unknown; Wide 8:3 layout needs workflow study; not a conventional 12-inch desktop aspect ratio. |
| 14 in | bonded capacitive LCD/control assembly; HDMI/DP/USB cables and micro-HDMI adapter; stand, button board/cable and small accessories; listed regional 5V 3A USB-C adapter; US variant selected in source. **Power:** Listed 5V 3A display adapter; board supply sharing/inrush remains unqualified. **Open:** Final bezel/enclosure, cable retention and final assembly; 3.11M pixels: higher native pixel workload than 18.5/21.5 FHD; validate scaling and thermal/memory load. |
| 18.5 in | enclosed capacitive monitor with stand and VESA mounting provision; mini-HDMI/HDMI, USB-C/C and USB-A/C cables; micro-HDMI adapter; listed regional 20W PD adapter; US SKU 32186. **Power:** Wiki lists 5V/11.1W and a 5V3A connection example, while package specifies 20W PD adapter; reconcile exact adapter profiles/inrush before integrating. **Open:** Controller enclosure/bracket and retained cable integration still separate; Wiki/store brightness/gamut differ; freeze exact revision; Native 60Hz starting qualification, not an untested 120Hz CNC UI promise. |
| 21.5 in | enclosed capacitive monitor with stand and VESA mounting provision; mini-HDMI/HDMI, USB-C/C and USB-A/C cables; micro-HDMI adapter; listed regional 35W PD adapter; US SKU 34985. **Power:** Wiki gives PD20V/0.87A (17.4W); store also says power input 5V. Use listed adapter for study; resolve supported input profiles before common-power design. **Open:** Controller enclosure/bracket, retained cables and final integration; Exact Linux touch/EDID and hardware revision qualification; 144Hz advertising is not a required or validated controller refresh rate. |

The 18.5-inch $129.99 and 21.5-inch $159.99 Luckfox prices refer to exact capacitive-touch variants. Cheaper similarly named non-touch monitors are excluded. Their manufacturer lists enclosed displays, cables and regional adapters; that improves sourcing clarity over the old ambiguous OSCY sample. It does not establish coolant/dust tolerance, EMC immunity, reliable touch near a VFD or a controller enclosure rating. Factory internal panel and touch-controller revisions still require control.

## Comparable priced basket, quantity one

**Three merchandise items only: selected module + retail reference carrier + selected display assembly.** This omits compute cooling/supply, CNC electronics, qualified installation and manufacturing. Pi baskets contain unavailable module offers; the CB2 carrier pairing is unqualified. No value below is a working controller price, a selected prototype order or a production estimate. Within a screen row the display is held constant; CB2 storage differs. Both I/O scopes have the same three-item arithmetic because neither I/O board is included.

| Display class | CM4 + CM4IO | CM5 + CM5IO REV 2 | CB2 + PI4B candidate |
|---|---:|---:|---:|
| 7 in | $168.49 | $170.44 | $200.96 |
| 10 in | $201.49 | $203.44 | $233.96 |
| 12 in | $232.49 | $234.44 | $264.96 |
| 14 in | $302.49 | $304.44 | $334.96 |
| 18 in | $252.49 | $254.44 | $284.96 |
| 21 in | $282.49 | $284.44 | $314.96 |

For the custom-carrier route, module + screen alone ranges from $133.49 (selected CM4/7-inch) to $305.98 (CB2/14-inch); the custom carrier and all machine electronics are unknown. At quantities 10/100/1,000, even the same two- or three-item subtotal remains unknown because compute/carrier prices were not quoted. Do not add only the known display tier and call the smaller number a volume saving. No complete profitable Mesa-priced package has been demonstrated.

## Compatibility work applies to every package

| Boundary | CM4 | CM5 | CB2 |
|---|---|---|---|
| Connector / power / recovery | Exact CM4102016 carrier matrix and RUN_PG behavior | Same mechanical family, changed pin functions; pin 92 power-button input; USB/MIPI and power/cooling review | Exact BTT pin table and revision; no universal CM4 socket claim |
| Screen path | HDMI + USB host touch | HDMI + USB host touch | HDMI + USB host touch, driver/pinmux audit required |
| Hard real-time path | Qualified Pi CNC1 SPI backend required | Own Pi peripheral/driver qualification required | Qualified Rockchip CNC1 SPI backend required |
| OS / graphics / thermal | Pinned PREEMPT_RT image, UI/model load and complete timing unmeasured | Same tests plus CM5 power/thermal envelope | Ordinary PREEMPT source setting is not PREEMPT_RT proof; GPU/kernel/CNC1 route open |

The display path is a plausible source-supported interface choice, not tested compatibility. Qualify exact native mode/EDID, USB touch identity/firmware, rotation/scaling, recovery, supply sequencing and partial-power behavior on each offered host. Do not infer USB-C DisplayPort output from a connector. Keep display traffic off dedicated motion SPI. Qualify 60Hz initially; monitor advertising of 120/144Hz does not establish that controller mode. The 14-inch panel has more pixels than FHD 18/21-inch options; size alone does not set compute load. The 7-inch 800×480 and wide 12.3-inch candidates need particularly careful UI acceptance.

Sources: [Raspberry Pi compute documentation](https://www.raspberrypi.com/documentation/computers/compute-module.html), [CM4/CM5 transition guide](https://pip-assets.raspberrypi.com/categories/1261-transitioning/documents/RP-008924-WP/Transitioning-from-Compute-Module-4-to-Compute-Module-5), [BTT CB2 manual](https://global.bttwiki.com/CB2.html), [existing BTT source review](BTT_COMPUTE_REVIEW.md). Shared shape is not electrical or real-time compatibility. PINE64 explicitly specifies a [204-pin SO-DIMM for SOEdge](https://pine64.org/2020/02/03/fosdem-2020-and-hardware-announcements/); its old tentative price is not used.

## Keep the machine hardware scopes separate

| Scope | Six/two baseline | Eight/four candidate |
|---|---|---|
| Motor / ABZ ports | 6 / 2 | 8 / 4 |
| Additional general DI / DO | 16 / 8 | 24 / 16 |
| Enable topology / alarms | 6 sourcing enables / 6 alarms | 8 floating isolated switches / 8 alarms |
| Specialized functions | One analog output; probes use general DI | Two AO, four AI, dedicated probes/frequency/PWM/process paths, isolated buses and backplane |
| Direct digital signals | 54 before support | 92 before support |
| Complete fitted cost | Unknown | Unknown; cannot scale baseline by 8/6 |

The [earlier costing](HARDWARE_COST_COMPARISON.md) stays a historical six/two/21.5-inch scenario. The later power correction and unpriced field buck/protection mean it is not a fitted BOM. The expanded design changes enable technology and simultaneous field power: 16 × 0.5A already totals 8A before other loads. Screen choice does not fix those gaps or inherit their qualification.

## Complete quote scope

Every matrix case carries these required blocks. Quotes must replace or reconcile existing parts, not double-count them. An included display adapter/cable is part of that SKU price; a custom common-power or retained-cable substitution needs an explicit replacement cost.

| Block | Required closure |
|---|---|
| Exact module incl. fitted RAM/eMMC | module quote, revision, storage endurance and lifecycle |
| Module mates, carrier signal connectors and protection | exact MPNs/stack height/pin matrix; avoid counting retail carrier ports twice |
| HDMI/USB/Ethernet magnetics and support | exact module-owned vs carrier-owned functions, hub and USB power |
| Carrier regulation, sequencing, boot/reset/recovery | worst-case power/inrush and fitted parts |
| Compute cooling, interface material, mounting | fitted heatsink/fan/harness and enclosure thermal proof |
| FPGA, flash, clocks, debug, rails and decoupling | selected package/grade, synthesis and exact support BOM |
| Dedicated CNC1 SPI electrical connection | pinmux, cable/connector, protection, retained routing and driver |
| Complete selected six/two or eight/four field circuits | separate fitted BOM, protection/isolation/defaults and terminal mates |
| Analog circuits and selected buses/expansion | ADC/DAC/reference/filter/calibration/isolation/power allocations |
| Independent useful-progress watchdog, gates and inhibits | exact hardware and quantitative fault behavior; cannot omit to hit price |
| ESP module, protected independent branch and wired diagnostics | regulator/decoupling/partial-power support, sensors and wiring |
| Proposed ESP accessory sensors/drivers/feedback | NOT IMPLEMENTED; decide base versus optional module, exact loads and single-output ownership |
| Physical fuses, reverse/transient and electronic branch protection | coordinated source/cable/fuse/FET/eFuse/TVS circuit; use existing protected outputs where sufficient |
| Controller adapter/conversion and power harness | screen/core power combined only after budget; field-load power scope explicit |
| Exact LCD/touch/controller/backlight assembly or monitor | quoted exact variant and package inclusions |
| Display adapter or protected converter branch | avoid double-counting included adapter; common supply replacement needs new price |
| Video/touch/power cables, retention and extensions | included cable set may need different lengths and retained connectors |
| Controller enclosure, screen mounting/bezel, shielding/bonding | per-tier drawing/BOM; HDPE is not assumed to provide EMC shielding |
| Actual PCB stackup/area/finish and fabrication | separate carrier/motion or combined board quotes |
| PCBWay sourcing, minimums/overbuy and procurement losses | reconcile inclusions with component basket; no duplicate parts total |
| PCBWay setup/assembly/inspection/rework/yield | quote 1/10/100/1000 good units; stencil scope; setup vs recurring |
| Host/FPGA/ESP images, identity and programming labor | versioned images and supported station interfaces |
| Fixtures, test time, calibration and records | quantitative electrical/functional procedure and serial/revision traceability |
| Display/controller mechanical and harness integration | explicit turnkey scope; PCBA alone does not include this |
| Thermal, power/fault, timing, EMC/environment and compliance work | intended markets and required testing; separately allocate nonrecurring cost |
| Packaging, inbound freight/duties and delivered procurement | avoid duplicate charges already inside supplier/PCBWay quote |

Warranty/support, payment or sales-channel fees, outbound fulfillment, development recovery and the selected margin remain separately defined business costs. No final sales currency or per-tier retail target is assumed. Optional AI remains outside the base. ESP accessory automation is a new proposal: protected branches, sensors, drivers and feedback are neither implemented nor free, and base/accessory allocation must be decided before a complete quote. Industrial reliability requires the protection and qualification blocks; they cannot be deleted to improve the displayed cost.

## Next decisive gaps

1. Choose bounded launch/test candidates from this matrix after UI viewport review; keep all requested classes represented as options. Confirm actual module supply, exact SKU and carrier/recovery pin matrix. No order is authorized here.
2. Finish separate six/two and eight/four fitted circuits, pin/power budgets and BOMs. Resolve display power contradictions and mechanical/cable retention per tier; define ESP accessory ownership and base/accessory cost allocation.
3. Prepare PCBWay fabrication/assembly files, fitted/DNP BOM and approved alternatives, placement, programming and quantitative test/fixture scope. Quote good units at 1/10/100/1,000 with setup separated. Final enclosure/display integration must be explicitly included or separately quoted.
4. Prove a reproducible host/CNC1 route and later loaded physical timing with representative UI, storage, network and thermal load before final production layout. Only then can complete cost and capability select a production package.

## Evidence and reproduction

This work performs source inspection plus offline matrix/arithmetic checks. It makes no new target compilation, LinuxCNC target test, HDL simulation, FPGA synthesis, circuit ERC, board DRC or physical measurement claim. It leaves older workbook and hashed engineering evidence unchanged.

Sources were read directly over HTTPS with Python urllib.request; JSON-LD offers, official Shopify variant JSON, PiShop price/currency/availability microdata and Waveshare quantity table rows were inspected. The JSON records exact URLs, evidence dates and selected variants; no full HTML is stored. Some web-tool requests returned 403, while direct public HTTPS retrieval succeeded. Where an exact retrieval timestamp was not retained, the record states only its date. Storefront availability is not a guaranteed stock commitment.

`python tools/build_compute_display_matrix.py --check` validates all 144 cases and generated-file equality without network or mutation. `--write` deliberately regenerates only the new JSON and this report from the dated observations in that script. Neither command refreshes prices. Review new primary evidence before changing those constants.
