# Hardware sourcing comparison — 28 September 2026

The three requested procurement approaches are now in an editable cost model. All retain a 21.5-inch FHD capacitive-touch target and the same protected six-joint interface. **None yet has a complete manufactured cost.** Public sample parts already exceed the illustrative US$249 selling price; production feasibility remains unresolved because compute, assembly and other quotes are missing.

The user has selected **PCBWay turnkey board manufacture after design**. Public parts prices below are procurement references, not PCBWay quotes. AI compute is an optional, separately costed upgrade; it is excluded from the base configurations. No supplier has been contacted and nothing has been ordered.

**Scope notice:** the later [7/10/12/14/18/21-inch screen tiers](../docs/DISPLAY_TIERS.md), [eight-motor/four-encoder proposal](../docs/EXPANDED_HARDWARE_TARGET.md) and [CM4/CM5/BTT carrier investigation](../docs/COMPUTE_CARRIER_STRATEGY.md) are separate next comparisons. This report/workbook and its source datasets still describe the historical 21.5-inch/six-joint configurations below, not a fixed screen requirement for the platform. New screen/module prices or extra channels cannot be substituted into its totals without rebuilding the complete fitted cost. No price for the new tiers is established here.

## Configurations held constant for comparison

| Approach | Linux compute | Display | Integration still required |
|---|---|---|---|
| A — module / complete monitor | Radxa CM3 SODIMM RM117-D2E16, 2 GB RAM / 16 GB eMMC; heatsink and fan | OSCY OTM-2150 advertised 21.5-inch FHD touch monitor | Custom module carrier, both module connectors, Ethernet PHY/magnetics, HDMI/USB interfaces |
| B — SBC / complete monitor | Radxa ROCK 3C RS112-D2, 2 GB RAM; 64 GB microSD; AE007 cooling | Same OSCY monitor lead | Motion/I/O board, retained board-to-board wiring and mounting |
| C — module / separate panel parts | Same compute as A | Innolux M215HGE-L21 LCD; NJY HDMI/LVDS board; Grahowlet HX2151801 touch candidate | Panel-specific wiring, touch fit/price, backlight package, glass retention/bonding, bezel |

The OSCY listing advertises a $100 sample and describes capacitive touch, but also offers other touch configurations. **The $100 exact capacitive package is not confirmed.** It is a sourcing lead, not a qualified monitor quotation. The separate-panel route likewise has no verified complete matched assembly.

The identical electrical scope is six differential STEP/DIR pairs, six enables, six alarms, two A/B/index encoder inputs, sixteen additional isolated nominal-24-V inputs, eight additional protected nominal-24-V sourcing outputs, and an isolated 0–10 V spindle stage. Spindle run/direction consume two of the eight outputs. The reference basket includes 96 terminal positions and mating plugs. Counts are preserved across approaches; supported voltage, current, fault energy and timing ratings still need circuit design and verification.

Some implementation choices are deliberately explicit costing provisions: isolated output controls/status, a 16-bit DAC, per-input TVS provisions and the connector allocation. They are not proof of the cheapest implementation or frozen user requirements. STEP/DIR and encoder lines in this basket are differential, not galvanically isolated.

## What is actually priced

**USD per controller, before unpriced rows, tax, freight and duties. These are partial reference subtotals, not manufactured-cost estimates.** Numbers in parentheses are the count of required unpriced worksheet rows; each row may contain several parts or services.

| Approach | 1 controller | 10 controllers | 100 controllers | 1,000 controllers |
|---|---:|---:|---:|---:|
| A | $335.27 (25) | $125.37 (30) | $204.75 (29) | $198.70 (29) |
| B | $339.20 (24) | $121.39 (30) | $201.60 (29) | $195.79 (29) |
| C | $350.26 (28) | $210.37 (33) | $191.75 (33) | $187.70 (33) |
| **Complete manufactured cost** | **INCOMPLETE** | **INCOMPLETE** | **INCOMPLETE** | **INCOMPLETE** |

The apparent drop at 10 units is **not a volume saving**: the unquoted Linux compute, FPGA and monitor prices are absent from that subtotal. Different columns have different quote coverage. Do not rank production options using these partial sums. The workbook exposes the missing rows and refuses to label their subtotal as the complete manufactured cost.

At quantity one, the common priced motion/I/O parts are $132.765 before rounding. Common external power, mains cord and HDMI cable add $41.64. The $5.89 mains-cord (Phihong AC30UNA-R) unit price was carried from earlier research with no recorded source listing; the model marks it `price_source: unrecorded` with an empty URL, so re-verify it before quotation. A/C compute and reference cooling add $60.86. B compute, storage and cooling add $64.79. A/B add the $100 monitor lead; C adds $85 for the LCD and $29.99 for the video board, with touch and several display requirements still unpriced. Subtotals are rounded only after aggregation.

The module route's $3.93 lower priced basket does not establish that it is cheaper: its missing Ethernet and carrier circuits could reverse that difference. The separate-panel route already has $114.99 in LCD/video parts before touch, versus the unconfirmed $100 complete-monitor lead. This particular bare-panel combination provides no demonstrated saving.

## Source evidence and qualification limits

| Item | Public price evidence | What it does not establish |
|---|---|---|
| [CM3 SODIMM RM117-D2E16](https://shop.allnetchina.cn/products/radxa-rock3-computing-module-sodimm?variant=39735504109670) | $55; exact 2 GB / 16 GB / no-wireless variant available when checked | Production quantities, complete carrier cost, real-time performance |
| [ROCK 3C RS112-D2](https://arace.tech/products/radxa-rock-3c?variant=42476867059892) | $44.90; exact 2 GB variant available when checked | Storage, cooling or LinuxCNC qualification |
| [ALLNET 64 GB microSD](https://shop.allnetchina.cn/products/allnet-micro-sd), [AE007 cooling](https://shop.allnetchina.cn/products/heatsink-for-rock5-model-a) | $16.99 and $2.90 | Industrial storage lifetime or enclosure thermal performance |
| [OSCY OTM-2150 listing](https://www.alibaba.com/product-detail/OSCY-21-5-Inch-Raspberry-Pi_1600113065577.html) | Indexed sample $100; 100–299 $96; 1,000+ $94; no verified 10-unit tier | Exact capacitive option, package contents, Linux touch behavior or firm current quote |
| [M215HGE-L21 LCD](https://cl-lcd.en.made-in-china.com/product/UvuQTtAPjkRg/China-Original-21-5-Inch-M215hge-L21-LED-Computer-LCD-Panel-From-Chimei-Innolux.html) | $85 at 1–29, $83 at 30+ | Exact revision, matching touch assembly, included backlight driver |
| [NJY HDMI/LVDS board](https://www.ebay.com/itm/372759013382) | $29.99; seller explicitly names M215HGE-L21 | Cable, backlight, firmware and bulk supply inclusions |
| [HX2151801 touch candidate](https://www.grahtouch.com/touch-screen/21-5-inch-capacitive-touch-panel.html) | Manufacturer drawing lead; no verified price | Final fit or a supplied matched stack |
| [GST90A24-P1M power supply](https://www.digikey.com/en/products/detail/mean-well-usa-inc/GST90A24-P1M/7703720) | $30.80 at 1; $28 at 10; $27.20 at 25+ | Completed system power budget or required DC converters |

The CM3 SODIMM provides an Ethernet MAC, not a complete Ethernet port. Its [schematic](https://dl.radxa.com/cm3s/docs/hw/RADXA_CM3S_V1.5_SCH.pdf) places the Ethernet interface on the additional J1 connector; both carrier connectors and the PHY path must be counted. The [ROCK 3C](https://radxa.com/products/rock3/3c/) has assembled Gigabit Ethernet, HDMI and USB interfaces. Neither candidate has passed PREEMPT_RT/LinuxCNC, custom FPGA transport, loaded browser/GPU or enclosure thermal tests here. Raspberry Pi-specific driver support is not evidence that the same driver works on Rockchip.

A previously found $115 touch overlay was excluded because its published viewing width is smaller than the selected LCD active width. Other unusually low display listings with mismatched dimensions or uncertain kit contents were also excluded. The named HX2151801 is only a fit candidate pending full drawings.

## PCBWay costing and remaining work

The model separates A/C carrier fabrication and assembly from B motion-board fabrication and assembly. They require different quotes. Turnkey pricing must replace the public component basket or explicitly reconcile against it; adding a complete turnkey quote on top of the existing parts total would double-count parts.

Required unpriced scope includes FPGA flash/clock/rails, support passives, rated protection networks, remaining power conversion and isolation, host/ESP links, expansion, USB/power harnesses, PCB manufacture, PCBWay sourcing/assembly/inspection, programming, test fixtures and labor, rework/yield, final cooling/mounts, enclosure/bezel, final assembly, packaging, and inbound freight/duties. A full board assembly service does not establish that display integration, enclosure assembly or CNC functional testing is included.

To make the quotes comparable, the release package must identify exact fitted and not-fitted BOM items; approved alternatives; PCB stackup, dimensions and finish; fabrication/drill data; placement and assembly drawings; revision-controlled programming images; and the electrical acceptance procedure. Quote 1, 10, 100 and 1,000 finished-good quantities with setup/tooling separated from recurring cost. Include sourcing minimums/overbuy, inspection, programming and functional-test scope rather than assuming they are free.

PCBWay's [assembly file requirements](https://www.pcbway.com/assembly-file-requirements.html) call for fabrication/assembly Gerbers, BOM and centroid placement data; its [production-file guidance](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/What_files_are_requested_for_assembly_production_.html) specifies placement reference, coordinates, rotation and board side. Our release manifest, hashes, approved alternatives and quantitative electrical limits are additional project requirements.

The [assembly MOQ is one](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/What_s_the_min_quantity_of_assembly_.html). The [assembly quotation includes the stencil](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Should_I_submit_a_stencil_order_for_SMT_project_made_by_PCBWay_.html); no separate JLCPCB stencil/setup charge belongs here. PCBWay says [component quotations can include procurement shipping, customs, procurement labor and excess parts](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Why_the_unit_cost_of_components_is_higher_than_suppliers_such_as_Digiky_.html). Reconcile those inclusions before adding freight or yield allowances again. No universal sourcing markup has been assumed.

[Programming is separately scoped and quoted](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/What_document_is_needed_for_IC_program_.html). [Functional testing needs our procedure and any special tools, with charges tied to test time](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Can_you_do_test_after_assembly__What_documents_should_I_offer_.html). Assembly inspection alone does not establish correct FPGA/ESP/Linux provisioning or CNC behavior. Final board quotes must specify that coverage.

Prices beyond the final published component tier are held at that last tier as an explicitly unquoted reference, without invented further discounts. Parts with only a single unit-price observation have blank bulk columns. Identical MPN demand is aggregated before choosing tiers. Stock, minimum reels, overbuy and PCBWay sourcing differences remain unverified.

The shared 24 V / 90 W adapter is only a power-cost reference; it requires conversion and a validated load budget. External motor drives and machine field-load power are outside the controller bundle. Warranty, selling fees, outbound fulfillment and product development also require commercial accounting before a retail target can be called viable.

## Decision from this comparison

Keep the three approaches open. B is the most convenient compute candidate for software/transport evaluation because its ports are already assembled; that is an integration judgment, not a production selection. The next cost-closing work is a qualified capacitive monitor package, compute supply quotes and sufficiently developed schematics/BOM/board outlines for PCBWay to quote both board variants. Reducing the controller's feature count is not assumed.

The editable workbook covers every identified cost category and quantity. Its full-price cells remain incomplete until the required costs are provided. Twelve subtotals and missing-price counts reconcile independently; input changes, blank-price handling and numeric zero were checked; the artifact calculation engine found no formula errors. The sheets were rendered and visually reviewed. This is workbook verification, not hardware validation or Excel-native application testing.

Related: [optional AI expansion](AI_ADDON_PLAN.md), [build plan](../docs/BUILD_PLAN.md), [source model](../WORKSPACE_REFERENCES.md#artifact-ba06fec3cbbe1439).

## Electrical review addendum — engineering r0

The later [electrical design review](../docs/ELECTRICAL_DESIGN.md) changes two reference quantities: TPS62160DSGR increases from two to three to provide a separate ESP 3.3 V branch, and TLV76050DBZR decreases from two to one, retaining only the isolated analog 12 V-to-5 V role. The field-side 18–30 V-to-5 V supply needs a switching regulator; the prior small-LDO provision is not accepted without thermal proof. At the 50 mA field-side budget, it would dissipate 0.95 W at 24 V and 1.25 W at 30 V.

The workbook above remains the dated sourcing comparison, not the fitted schematic BOM. At its quantity-one piece prices, the known arithmetic adjustment alone is +$1.53 per controller, **plus the unquoted replacement field converter and support/protection circuits**. This does not produce a complete updated manufacturing cost. Physical fuses, electronic protection, reverse-polarity FETs and branch telemetry must be included when the power design is finalized. Preserve this distinction until a complete fitted BOM replaces the reference basket.
