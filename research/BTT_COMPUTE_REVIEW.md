# BTT compute-module review

Observed 28 September 2026. This is a source and current-retail-price review, not a target build, latency test or procurement quotation. No hardware purchased, supplier contacted, machine connected or existing configuration changed.

## Engineering conclusion

**Add CB2 to the active compute shortlist.** Its module form, published 2 GB RAM / 32 GB eMMC configuration, Rockchip RK3566 and available display/network interfaces make it a relevant alternative for our custom carrier. The user's inexpensive-module approach is valid: designing around a purchased compute module avoids designing the processor/DDR subsystem. Whether CB2 becomes our choice depends on exact procurement price, carrier requirements, a reproducible real-time software route and measured application load.

Keep CB1 as a lower-memory comparison, not the assumed replacement for a 2 GB host running the local 3D interface. CB1's one-gigabyte priced variant must demonstrate the same workload before accepting its lower memory. A cheap genuine supplier/volume offer could change the economics; today's retail pages neither prove nor rule out that offer.

## Reported estimates versus observed prices

The user supplied these estimates: CB1 Standard $23–28, CB1 eMMC $35–40, CB2 module $40–45, and approximately $90 for a Pi 2 bundle. The supplied dollar currency, vendor, quantity, date and exact bundle were not established. Retain these as **user-provided procurement scenarios**, not verified quotations and not automatically USD.

The following are **USD quantity-one prices returned by BIQU's official product-variant data on the observation date**, excluding delivery, tax and duties. A Shopify `available` flag is a storefront observation, not a warehouse guarantee. `compare_at_price` is marketing comparison data, not an order price.

| Exact official variant | Current USD | Available flag | Scope |
|---|---:|---|---|
| CB1 (1GB RAM), SKU 1020000405 | $66.59 | Yes | Module; storage additional |
| CB1 eMMc (1GB+32GB), SKU 1020000430 | $33.68 | **No** | Module with storage |
| CB1+PI4B | $88.74 | Yes | Module/carrier bundle |
| PI4B, SKU 1030000103 | $28.98 | Yes | Carrier only |
| CB1 heatsink | $5.90 | Yes | Cooling accessory |
| BIGTREETECH CB2, SKU 1020000449 | $125.99 | Yes | Dedicated Pi 2/CB2 listing |
| BIGTREETECH CB2 Lite, SKU 1020000487 | $89.56 | Yes | Exact Lite RAM/storage specification still needs confirmation |
| CB2 Lite + MicroSD 32GB | $102.48 | Yes | Module/storage bundle; carrier additional |
| CB2 heatsink | $5.90 | Yes | Different mechanical part from CB1 heatsink |
| BIGTREETECH Pi 2, SKU 1020000459 | $153.98 | Yes | Assembled SBC, not a bare CB2 module |
| BIGTREETECH Pi 2 Lite | $95.48 | Yes | Separate SBC variant |

Sources: [official PI4B/CB1 variants](https://biqu.equipment/products/pi4b-adapter-v1-0.js), [official CB2/Pi 2 variants](https://biqu.equipment/products/bigtreetech-pi-2-cb2.js). Exact IDs and observed data are in [the source snapshot](btt-compute-sources.json).

There is a material listing inconsistency: SKU 1020000449 also appears at **$178.45** in the PI4B and Manta product selectors, versus $125.99 on its dedicated page. The US storefront API returned the same variant prices during this check. Do not average these or treat either as a negotiated manufacturing price. The collection's low “from” price includes the $5.90 heatsink; it is not a compute-module offer. [PI4B page](https://biqu.equipment/products/pi4b-adapter-v1-0), [CB2 page](https://biqu.equipment/products/bigtreetech-pi-2-cb2)

## Hardware fit and limitations

| Candidate | Source-supported facts | Project consequence |
|---|---|---|
| CB1 | Allwinner H616, four Cortex-A53 cores up to 1.5 GHz; published 512 MB/1 GB family; priced standard SKU explicitly 1 GB; HDMI, USB 2.0, 100 Mb Ethernet, 2.4 GHz Wi-Fi | Separate SD and eMMC variants. HDMI can suit the complete-monitor path; do not assume sufficient local 3D/CAD memory. |
| CB2 | Rockchip RK3566, four Cortex-A55 cores up to 1.8 GHz; published standard 2 GB LPDDR4/32 GB eMMC; broader family documentation also mentions 4 GB; Gigabit Ethernet, dual-band Wi-Fi, HDMI and MIPI DSI/CSI; two 100-pin board connectors | Suitable module/carrier study candidate. The listing does not establish that the priced SKU is the larger-memory family option. |
| Pi 2 | Assembled BTT RK3566 SBC with physical interfaces; distinct product from CB2 | Potential engineering host; do not count a CB2 plus a Pi 2 as though Pi 2 were only its carrier. |

Sources: [CB1 manual](https://global.bttwiki.com/CB1.html), [CB2 manual](https://global.bttwiki.com/CB2.html), [current CB2 overview](https://neo.bttwiki.com/en/docs/board-docs/iot-series/iot-cb2/).

CB1 does **not** support the PI4B's DSI/CSI connectors; the carrier documentation limits those to the compatible host. CB2 documents DSI support with matching overlays/panels. The CB2 manual currently describes one selected display type at a time. No qualified DPI display route was established in this review. For the historical 21.5-inch complete-monitor study, the cost path remains HDMI plus the monitor's actual touch connection and power. The new [screen-tier requirement](../docs/DISPLAY_TIERS.md) covers compact through large packages: qualify each exact display/host/interface, cost all required electronics and preserve the dedicated motion transport. A low-cost panel listing alone establishes neither compatibility nor a complete package price. [PI4B documentation](https://biqu.equipment/products/pi4b-adapter-v1-0), [CB2 display configuration](https://global.bttwiki.com/CB2.html)

**CM4-style mechanical connectors do not establish generic CM4 pin/software compatibility.** Both published pin tables contain their own signal assignments and unconnected positions. Review the exact module, revision and carrier schematic; do not copy Raspberry Pi GPIO numbers or assume all CM4 peripheral functions. Manta M4P/M8P are printer control/carrier boards that accept supported modules, not alternate names for the compute module or our FPGA board. Our product should use the purchased module on our reviewed carrier rather than paying for an unnecessary printer motherboard. [CB1 pin table](https://global.bttwiki.com/CB1.html), [CB2 pin table](https://global.bttwiki.com/CB2.html), [Manta product family](https://biqu.equipment/products/manta-m4p-m8p)

Documentation itself needs normalization: CB2 pages list Bluetooth 5.2 in one paragraph and 5.0 in another, and differ on the auxiliary 3.3 V output allowance. Do not use either disputed value as a frozen board rating. The published 0.8 TOPS NPU is not evidence of an adequate local language-model service; optional AI remains outside the base requirement.

## Linux, real-time and SPI evidence

- CB1 V3.1.0, published 30 April 2026, documents Debian 13 with mainline Linux 7.0. Older claims that CB1 is restricted to its early 4.9/5.16 images are stale. [Official CB1 release](https://github.com/bigtreetech/CB1/releases/tag/V3.1.0)
- CB2 V3.1.0, published 3 July 2026, documents Debian 13 and the BTT Rockchip Linux 6.1 branch. Its build source is inspectable. The pinned build repository commit reviewed here is `555de9b208cb136b26a9c9d2d40aec952abbc444`. [Official CB2 release](https://github.com/bigtreetech/CB2/releases/tag/V3.1.0)
- The BTT-specific `linux-rk35xx-btt.config` contains `CONFIG_PREEMPT=y` and Rockchip SPI support. This is ordinary kernel preemption, not proof of PREEMPT_RT. No CB2 target image was built or booted, and no shipped-image kernel configuration or loaded latency was measured. [Pinned kernel configuration](https://github.com/bigtreetech/build/blob/555de9b208cb136b26a9c9d2d40aec952abbc444/config/kernel/linux-rk35xx-btt.config)
- CB1 documents SPI1 and multiplexing with TFT/MCP2515 functions. CB2 releases document SPI overlays and a corrected `spi1` overlay. The shop's statement that “Pi 2 does not have an SPI interface” conflicts with newer peripheral documentation and must not be applied wholesale to CB2. Select the exact exposed bus/pins from the schematic and device tree; reserve the motion bus independently of display/CAN traffic. [CB1 SPI notes](https://github.com/bigtreetech/CB1), [CB2 release history](https://github.com/bigtreetech/CB2/releases)
- LinuxCNC's Raspberry Pi-specific SPI implementation is not a Rockchip or Allwinner driver. Its generic SPI documentation also separates protocol support from real-time transport performance. Our endpoint uses **CNC1**, so an unmodified HostMot2 driver is not its driver on any module. [hm2_spi](https://linuxcnc.org/docs/stable/html/man/man9/hm2_spi.9.html), [hm2_rpspi](https://linuxcnc.org/docs/stable/html/man/man9/hm2_rpspi.9.html)

The next software evidence is a pinned minimal host image, PREEMPT_RT configuration/build, working local graphics, a CNC1 real-time transport implementation, and loaded read/compute/write timing. Source compatibility is only the start of this path.

## Comparable cost scope

Our previous study recorded ROCK 3C 2 GB at $44.90, or **$64.79 with its 64 GB microSD and reference cooling**; CM3 SODIMM 2 GB/16 GB eMMC was $55, or **$60.86 with reference cooling** before its custom carrier. These are the existing study snapshots, not prices newly verified here. [Existing comparison and vendor links](HARDWARE_COST_COMPARISON.md)

For BTT's observed listings:

- CB1+PI4B plus heatsink: **$94.64 before storage**, supply and final enclosure cooling.
- CB1 eMMC + PI4B + heatsink: **$68.56**, but the module is listed unavailable, so this is an unavailable-parts subtotal.
- CB2 plus its heatsink: **$131.89 before carrier**, supply and final thermal design.
- CB2 Lite + 32 GB microSD bundle + heatsink: **$108.38 before carrier**; confirm the Lite specification first.

A CB2 custom carrier still needs two mating 100-pin connectors, power entry/regulation, Ethernet magnetics/connector and protection as applicable to the selected module, HDMI/USB/touch connections, boot/recovery, mounting and cooling. **Exact mating-connector MPNs, fitted prices and total BTT carrier cost remain unpriced.** A PI4B retail carrier price does not price our custom PCB, and CB2's compatibility with a proposed carrier needs an exact schematic audit. Do not add separate eMMC to the standard CB2 storage cost, or count complete carrier ports twice.

The user's $40–45 CB2 scenario should stay in the cost model as an unverified scenario alongside observed retail. If verified with the required memory/storage and supply terms, it could improve the module route materially. Neither scenario includes the display, FPGA/I/O, manufacturing, power supply, enclosure, test or delivered-unit cost. Keep pilot and production quantities separate and obtain an actual supplier/PCBWay quotation only at the authorized procurement stage.

## Next decision package

1. Keep CB2 and ROCK 3C/CM3 SODIMM as parallel candidates; preserve the existing board work until a choice passes its gates.
2. Identify the exact inexpensive BTT offer/SKU/currency/quantity and distinguish module, carrier and printer-board bundle.
3. Audit CB2 carrier pinout, dedicated SPI availability, boot recovery and output-voltage limits; cost the complete carrier.
4. Establish a reproducible PREEMPT_RT and CNC1 driver route. Benchmark the real UI/model corpus in 1 GB versus 2 GB only where meaningful.
5. Select on complete cost and qualified behavior, retaining a measured fallback if the cheaper module fails a required workload or timing test.

Evidence completed here: official source inspection and price arithmetic. Evidence not completed: host application tests on BTT, target compilation, real-time measurements, schematic ERC, board DRC or physical qualification.
