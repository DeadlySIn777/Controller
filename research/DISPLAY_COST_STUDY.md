# Included touchscreen: sourcing and product cost

Researched 28 September 2026 UTC. Prices are USD public listing observations, excluding freight, tax and duty. The user's currency is not yet specified. No vendor has been contacted and no order placed.

**Scope update:** the user now wants 7-, 10-, 12-, 14-, 18- and 21-inch product classes and further sizes. The [display-tier plan](../docs/DISPLAY_TIERS.md) is the current requirement. The sourcing observations and arithmetic below are retained as dated scenarios; this report does not cost or qualify the new range.

## Earlier reference and retained sourcing evidence

The user supplied [Bosunre B0G8HWTNGT](https://www.amazon.com/dp/B0G8HWTNGT): 21.5-inch, 1920×1080, ten-point capacitive touch, open-frame mounting, HDMI/VGA. The $190 amount comes from the conversation; a current checkout price was not independently verified. Its seller advertises front IP65, which does not establish protection of the entire eventual controller enclosure.

A 21.5-inch FHD capacitive assembly remains a candidate for the large-screen tier. Smaller panels are deliberate product options, not fallbacks. For each tier, compare an OEM open-frame assembly against a complete monitor: omitting a retail stand/case may help, but does not guarantee savings after mounting, glass, electronics, assembly and qualification. The previously researched 15.6- and 10.1-inch options remain sourcing leads; exact panels, launch sizes and prices require the new per-tier comparison.

## Concrete candidates

| Candidate | Advertised USD | What the listing establishes | What remains unresolved |
|---|---:|---|---|
| [OSCY OTM-2150, 21.5-inch FHD](https://www.alibaba.com/product-detail/OSCY-21-5-Inch-Raspberry-Pi_1600113065577.html) | $100 sample; $98 at 50–99; $96 at 100–299; $95 at 300–999; $94 at 1,000+ | Supplier lists a complete 1920×1080 touch monitor with HDMI/USB and capacitive touch, with resistive touch as an alternative. Open-frame applications are listed. | Exact capacitive configuration at the advertised price, enclosure/mount drawing, touch controller, Linux behavior, included PSU/cables and delivered cost. Treat as a supplier lead, not a qualified BOM price. |
| [Elecrow CrowVi CRV15624T / VF156T, 15.6-inch FHD](https://www.elecrow.com/crowvi-15-6inch-portable-usb-c-monitor-touchscreen.html) | $129 advertised for the 15.6-inch touch version | Manufacturer's comparison table explicitly assigns $129 to the touch model; complete IPS monitor, mini-HDMI and USB-C, capacitive touch. | Final selected option/checkout price, production availability and mounting. Portable construction is not equivalent to a sealed industrial panel. Linux touch and the exact included package need acceptance verification. |
| [Elecrow DIS85101D, 10.1-inch 1280×800](https://www.elecrow.com/elecrow-10-1-inch-display-ips-1280x800-acrylic-case-touch-screen-compatible.html) | $66.90, quantity one | Complete capacitive HDMI/USB display with acrylic case, cables and mounting brackets. | Manufacturer explicitly specifies single-touch on Raspberry Pi OS/Linux and five-point touch on Windows. Its resolution and Linux touch behavior need acceptance against compact-layout requirements. Wall PSU is not in the listed package. |

OSCY evidence was retrieved from the search index of the supplier's own listing; direct page extraction was empty. Its indexed content was approximately four months old. Manufacturer Elecrow pages were accessible through indexed content (approximately two weeks old); direct fetches sometimes returned HTTP 403. These are useful sourcing evidence, not contemporaneous binding quotes. No shipping banner or certification logo has been treated as a verified delivered-price or compliance claim.

The low prices above refer to advertised functioning displays. Bare LCD panels, separate touch overlays and multi-size listing minimums have not been substituted for a complete touchscreen assembly.

## Cost consequences

The historical [compute/FPGA/ESP study](../docs/BUILD_PLAN.md) totals **$115.91** at quantity one: CM5 SC1588 $97.50, T20F256C4 $12.75, ESP32-S3-WROOM-1-N8 $5.66. This excludes their support electronics and all other board costs.

| Display assumption | Display + those three parts | Revenue remaining at illustrative $249 sale price, before all other cost or profit |
|---|---:|---:|
| User's $190 screen reference | $305.91 | −$56.91 |
| OSCY $100 sample, if the required configuration is confirmed | $215.91 | $33.09 |
| CrowVi $129 | $244.91 | $4.09 |
| DIS85101D $66.90 | $182.81 | $66.19 |

Do not combine a screen volume price with quantity-one electronics and label the result a production BOM. Quote whole product quantities consistently. Remaining costs include industrial I/O, connectors, power conversion, motion-link circuits, PCB and assembly, programming/testing, power supply, mounting/enclosure, thermal parts, freight and packaging. Warranty/support, selling fees and development recovery also affect business viability.

For an illustrative 40% manufacturing gross margin, a $249 net sale allows $149.40 manufacturing cost. At $100 for the screen, only $49.40 remains for everything else. Therefore a cheaper display alone does not qualify the current CM5 architecture for the desired selling price. The compute and full I/O board must be costed again; no specific cheap alternative is qualified yet.

## Display integration requirements before selection

- Prefer HDMI video and USB HID touch for the first cost study, with explicitly rated display power. A USB-C connector alone does not establish video support; the host must implement the appropriate video and power functions for a one-cable configuration.
- Require the exact display, touch controller/firmware, mounting drawing, power consumption and package contents. For production sourcing, request separate pricing for sample, 10, 100 and 1,000 identical capacitive assemblies, including freight terms and replacement policy.
- Verify touch coordinates, rotation, multi-touch gestures used by the UI, boot/reconnect behavior and operation with the selected Linux image. Marketing claims of ten-point touch do not replace this test.
- Test representative machine/fixture scenes at native resolution on the included local computer while measuring loaded real-time latency. The same board now needs to serve a local kiosk browser, not merely expose a service to the user's laptop.
- Evaluate mounting stiffness, readable contrast, cable retention, cleaning, coolant exposure appropriate to the mounting location, and false touches under spindle/VFD interference. Qualify the final enclosure and bezel together.

These are pre-order selection requirements and later physical acceptance measurements. They are not completed validation. The immediate direction is now a multi-size screen/package matrix and responsive-layout study, with compute and I/O comparisons held consistent within each tier. The earlier 21.5-inch emphasis is superseded as a product-wide requirement; its price observations remain historical evidence.
