"""Build/check a dated sourcing study, offline. Does not contact vendors or price orders.

Prices below are explicit observations, never fetched or silently refreshed by this tool.
Edit observations only after reviewing new primary evidence. --check is read-only.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/compute-display-matrix.json"
REPORT = ROOT / "research/COMPUTE_DISPLAY_MATRIX.md"
QUANTITIES = [1, 10, 100, 1000]
DATE = "2026-09-28"


def prices(one=None, ten=None, hundred=None, thousand=None):
    return dict(zip(map(str, QUANTITIES), [one, ten, hundred, thousand]))


def source(url, observed, method, facts, availability=None):
    return {"url": url, "observed_at_utc": observed, "method": method,
            "facts": facts, "availability": availability, "currency": "USD"}


SOURCES = {
    "cm4": source("https://www.pishop.us/product/raspberry-pi-compute-module-4-wireless-2gb-16gb-cm4102016/", "2026-09-28", "Direct HTTPS HTML: exact title, price/priceCurrency/availability microdata", {"mpn": "CM4102016", "manufacturer_code": "SC0669", "seller_sku": "1400", "unit_price": 87.50}, "OutOfStock microdata; no purchasable stock established"),
    "cm4_alt": source("https://www.adafruit.com/product/4791", "2026-09-28T06:06:42.764480Z", "Direct HTTPS JSON-LD and visible exact product description", {"seller_id": "4791", "configuration": "CM4 2GB/16GB/wireless", "unit_price": 55.00}, "OutOfStock; separate unavailable-price observation, not primary basket input"),
    "cm5": source("https://www.pishop.us/product/raspberry-pi-compute-module-5-wireless-2gb-ram-16gb-emmc-cm5102016/", "2026-09-28T06:09:07.709221Z", "Direct HTTPS HTML: exact product and price/currency/availability microdata", {"mpn": "CM5102016", "manufacturer_code": "SC1588", "unit_price": 97.50}, "OutOfStock microdata"),
    "cb2": source("https://biqu.equipment/products/bigtreetech-pi-2-cb2.js", "2026-09-28T06:06:10.827068Z", "Direct official Shopify product JSON; USD currency corroborated by official storefront and prior btt-compute-sources.json", {"variant_id": 41018191839330, "sku": "1020000449", "unit_price": 125.99, "quantity_price_breaks": []}, "available=true; stock quantity not supplied"),
    "cb2_alt": source("https://biqu.equipment/products/pi4b-adapter-v1-0.js", "2026-09-28T06:06:10.859946Z", "Direct official Shopify product JSON", {"variant_id": 41053017866338, "sku": "1020000449", "unit_price": 178.45}, "available=true; conflicting listing for same SKU retained separately"),
    "cm4io": source("https://www.adafruit.com/product/4787", "2026-09-28", "Direct HTTPS product JSON-LD and visible specification", {"seller_id": "4787", "name": "Raspberry Pi Compute Module 4 IO Board", "unit_price": 35.00}, "InStock JSON-LD"),
    "cm5io": source("https://www.pishop.us/product/raspberry-pi-compute-module-5-io-board-rev-2/", "2026-09-28T06:09:07.677560Z", "Direct HTTPS price/currency/availability microdata; exact REV 2 title", {"mpn": "SC1967", "seller_sku": "182-1", "unit_price": 26.95}, "OutOfStock microdata; indexed page says IN STOCK, so availability conflict remains"),
    "pi4b": source("https://biqu.equipment/products/pi4b-adapter-v1-0.js", "2026-09-28T06:06:10.859946Z", "Direct official Shopify product JSON", {"variant_id": 39919128969314, "sku": "1030000103", "unit_price": 28.98, "quantity_price_breaks": []}, "available=true; not an exact CB2/carrier qualification"),
    "ws7": source("https://www.waveshare.com/product/7inch-HDMI-LCD-B.htm", "2026-09-28T06:06:44.418386Z", "Direct HTTPS JSON-LD, package list and actual waveshare_view_price/waveshare_view_num table rows; comments removed", {"sku": "10829", "mpn": "7inch HDMI LCD (B)", "quantity_tiers_usd": {"1-9": 45.99, "10-49": 44.99, "50-99": 44.49, "100+": 44.29}}, "InStock JSON-LD; production capacity not established"),
    "ws10": source("https://www.waveshare.com/10.1dp-caplcd.htm", "2026-09-28T06:06:46.791470Z", "Direct HTTPS JSON-LD, package list and quantity table rows", {"sku": "23739", "mpn": "10.1DP-CAPLCD", "quantity_tiers_usd": {"1-9": 78.99, "10-49": 77.39, "50-99": 76.59, "100+": 76.27}, "indexed_price_superseded": 74.99}, "InStock JSON-LD"),
    "ws12": source("https://www.waveshare.com/12.3inch-1920x720-lcd.htm", "2026-09-28T06:06:48.071001Z", "Direct HTTPS JSON-LD, package list and quantity table rows", {"sku": "28481", "mpn": "12.3inch 1920x720 LCD", "quantity_tiers_usd": {"1-9": 109.99, "10-49": 107.99, "50-99": 106.99, "100+": 106.59}}, "InStock JSON-LD"),
    "ws14": source("https://www.waveshare.com/14inch-2160x1440-lcd.htm", "2026-09-28T06:09:07.680816Z", "Direct HTTPS visible USD price/package list and waveshare_sku_attributes; default waveshare_selected_attributes is US", {"sku": "28504", "mpn": "14inch 2160x1440 LCD (US)", "unit_price": 179.99, "us_unsaleable": False, "other_plug_skus": {"EU": "28505", "UK": "28506"}}, "US variant unsaleable=false; no stock count"),
    "lf18": source("https://www.luckfox.com/18.5inch-Touch-Monitor", "2026-09-28T06:09:09.424956Z", "Direct HTTPS ProductGroup JSON-LD exact US hasVariant entry and package list", {"sku": "32186", "mpn": "18.5-Touch-Monitor (US)", "variant_url": "https://www.luckfox.com/18.5inch-Touch-Monitor?ci=707", "unit_price": 129.99}, "InStock exact variant JSON-LD"),
    "lf21": source("https://www.luckfox.com/21.5-Touch-Monitor", "2026-09-28T06:09:09.473004Z", "Direct HTTPS ProductGroup JSON-LD exact US hasVariant entry and package list", {"sku": "34985", "mpn": "21.5-Touch-Monitor (US)", "variant_url": "https://www.luckfox.com/21.5-Touch-Monitor?ci=758", "unit_price": 159.99}, "InStock exact variant JSON-LD"),
}

COMPUTES = [
    {"id": "cm4-2g16g-w", "name": "CM4 CM4102016 / SC0669", "ram_gb": 2, "emmc_gb": 16, "wireless": True, "module_usd": prices(87.50), "source_id": "cm4", "prototype_carrier": {"name": "Official CM4 IO Board, Adafruit 4787", "source_id": "cm4io", "usd": prices(35), "status": "Manufacturer-matched reference carrier; CNC1/SPI and complete product remain unqualified", "input_power": "External carrier supply; reference board exposes 12V/5V power; exact fitted input policy to specify"}, "software_gate": "Pinned Pi PREEMPT_RT/LinuxCNC route plus custom CNC1 transport; module carrier, graphics and loaded timing not tested here", "carrier_specific_gaps": ["CM4 power/reset/RUN_PG and boot-recovery wiring", "USB2 host/hub budget for touch and accessory adapters", "HDMI, Ethernet magnetics/RJ45/protection and exact SPI pinmux"]},
    {"id": "cm5-2g16g-w", "name": "CM5 CM5102016 / SC1588", "ram_gb": 2, "emmc_gb": 16, "wireless": True, "module_usd": prices(97.50), "source_id": "cm5", "prototype_carrier": {"name": "Official CM5 IO Board REV 2 SC1967", "source_id": "cm5io", "usd": prices(26.95), "status": "Manufacturer-matched reference carrier; live/indexed availability conflicts; CNC1 remains unqualified", "input_power": "External 5V USB-C supply; separately cost exact supply/current/USB power allocation"}, "software_gate": "Pinned Pi PREEMPT_RT/LinuxCNC route plus custom CNC1 transport; CM5 peripheral access and loaded thermal/graphics timing need their own tests", "carrier_specific_gaps": ["CM5 pin 92 is power-button input, not CM4 RUN_PG", "USB/MIPI changes and supported common subset", "Higher module power/cooling; no automatic CM4 thermal envelope"]},
    {"id": "cb2-2g32g", "name": "BTT CB2 1020000449", "ram_gb": 2, "emmc_gb": 32, "wireless": True, "module_usd": prices(125.99), "source_id": "cb2", "prototype_carrier": {"name": "BTT PI4B V1.0 1030000103 candidate", "source_id": "pi4b", "usd": prices(28.98), "status": "PRICE REFERENCE ONLY: exact CB2-to-PI4B pin/power/SPI support not established by this review; not a compatible ready-to-use package claim", "input_power": "Carrier-specific 5V input, USB power and recovery must be audited"}, "software_gate": "BTT kernel CONFIG_PREEMPT=y is not PREEMPT_RT proof; reproducible target image, Rockchip CNC1 transport, GPU and loaded timing remain open", "carrier_specific_gaps": ["Audit every used CB2 pin against exact carrier revision; dual connectors alone are insufficient", "Dedicated Rockchip SPI bus and pinmux, USB ports and eMMC recovery", "Resolve published auxiliary 3.3V and Bluetooth specification inconsistencies"]},
]


def display(identifier, size, actual, resolution, name, sku, usd, source_id, contents, power, omissions, documentation):
    return {"id": identifier, "class_inches": size, "diagonal_inches": actual,
            "native_resolution": resolution, "name": name, "sku": sku,
            "touch": "capacitive; manufacturer claim, controller/firmware revision unverified",
            "interface_plan": "HDMI video + USB touch + separate rated display power; no USB-C video assumed on custom host",
            "assembly_usd": usd, "source_id": source_id, "package_contents": contents,
            "power": power, "missing_or_unqualified": omissions, "documentation": documentation,
            "complete_installed_display_package_usd": prices(), "qualified": False}


DISPLAYS = [
    display("screen7-ws10829", 7, 7, [800,480], "Waveshare 7inch HDMI LCD (B)", "10829", prices(45.99,44.99,44.29,44.29), "ws7", ["matched LCD/touch/control assembly", "HDMI cable and micro-HDMI adapter", "USB-A to micro-B cable", "RPi screw pack"], "USB/5V-powered display; actual current/inrush and independent branch remain to specify", ["No standalone PSU or finished bezel/enclosure included", "800x480 minimum viewport/touch-only workflow must pass UI audit; do not assume it is adequate", "USB host sourcing and touch/power backfeed behavior"], ["https://www.waveshare.com/wiki/7inch_HDMI_LCD_(B)"]),
    display("screen10-ws23739", 10, 10.1, [1280,800], "Waveshare 10.1DP-CAPLCD", "23739", prices(78.99,77.39,76.27,76.27), "ws10", ["optically bonded LCD/touch/control assembly", "HDMI 1m and USB-A/USB-C 1m cables", "button board/cable, adapters and screws"], "Exact display power/inrush and protected supply branch need approval; PSU is absent from listed package", ["Finished bezel/enclosure, retention and power arrangement", "Exact host native mode, touch revision, USB current and EMI qualification"], ["https://www.waveshare.com/wiki/10.1DP-CAPLCD"]),
    display("screen12-ws28481", 12, 12.3, [1920,720], "Waveshare 12.3inch 1920x720 LCD", "28481", prices(109.99,107.99,106.59,106.59), "ws12", ["in-cell capacitive LCD/control assembly", "HDMI/USB-A-to-C/C-to-C cables and micro-HDMI adapter", "stand, button board/cable, touch pen and cleaning cloth"], "Wiki specifies 4.75–5.25V and 5W maximum; source current >=1A. Inrush and branch design unmeasured", ["No PSU listed; final supply and enclosure/mounting cost unknown", "Wide 8:3 layout needs workflow study; not a conventional 12-inch desktop aspect ratio"], ["https://www.waveshare.com/wiki/12.3inch_1920x720_LCD"]),
    display("screen14-ws28504", 14, 14, [2160,1440], "Waveshare 14inch 2160x1440 LCD (US)", "28504", prices(179.99), "ws14", ["bonded capacitive LCD/control assembly", "HDMI/DP/USB cables and micro-HDMI adapter", "stand, button board/cable and small accessories", "listed regional 5V 3A USB-C adapter; US variant selected in source"], "Listed 5V 3A display adapter; board supply sharing/inrush remains unqualified", ["Final bezel/enclosure, cable retention and final assembly", "3.11M pixels: higher native pixel workload than 18.5/21.5 FHD; validate scaling and thermal/memory load"], ["https://www.waveshare.com/wiki/14inch_2160x1440_LCD"]),
    display("screen18-lf32186", 18, 18.5, [1920,1080], "Luckfox 18.5-Touch-Monitor (US)", "32186", prices(129.99), "lf18", ["enclosed capacitive monitor with stand and VESA mounting provision", "mini-HDMI/HDMI, USB-C/C and USB-A/C cables", "micro-HDMI adapter", "listed regional 20W PD adapter; US SKU 32186"], "Wiki lists 5V/11.1W and a 5V3A connection example, while package specifies 20W PD adapter; reconcile exact adapter profiles/inrush before integrating", ["Controller enclosure/bracket and retained cable integration still separate", "Wiki/store brightness/gamut differ; freeze exact revision", "Native 60Hz starting qualification, not an untested 120Hz CNC UI promise"], ["https://wiki.luckfox.com/Display/18.5inch-Touch-Monitor/"]),
    display("screen21-lf34985", 21, 21.5, [1920,1080], "Luckfox 21.5-Touch-Monitor (US)", "34985", prices(159.99), "lf21", ["enclosed capacitive monitor with stand and VESA mounting provision", "mini-HDMI/HDMI, USB-C/C and USB-A/C cables", "micro-HDMI adapter", "listed regional 35W PD adapter; US SKU 34985"], "Wiki gives PD20V/0.87A (17.4W); store also says power input 5V. Use listed adapter for study; resolve supported input profiles before common-power design", ["Controller enclosure/bracket, retained cables and final integration", "Exact Linux touch/EDID and hardware revision qualification", "144Hz advertising is not a required or validated controller refresh rate"], ["https://wiki.luckfox.com/Display/21.5-Touch-Monitor/"]),
]

COST_BLOCKS = [
    ("module", "Exact module incl. fitted RAM/eMMC", "module quote, revision, storage endurance and lifecycle"),
    ("carrier_connectors", "Module mates, carrier signal connectors and protection", "exact MPNs/stack height/pin matrix; avoid counting retail carrier ports twice"),
    ("carrier_ports", "HDMI/USB/Ethernet magnetics and support", "exact module-owned vs carrier-owned functions, hub and USB power"),
    ("carrier_power", "Carrier regulation, sequencing, boot/reset/recovery", "worst-case power/inrush and fitted parts"),
    ("carrier_thermal", "Compute cooling, interface material, mounting", "fitted heatsink/fan/harness and enclosure thermal proof"),
    ("fpga_core", "FPGA, flash, clocks, debug, rails and decoupling", "selected package/grade, synthesis and exact support BOM"),
    ("motion_link", "Dedicated CNC1 SPI electrical connection", "pinmux, cable/connector, protection, retained routing and driver"),
    ("machine_io", "Complete selected six/two or eight/four field circuits", "separate fitted BOM, protection/isolation/defaults and terminal mates"),
    ("analog_buses", "Analog circuits and selected buses/expansion", "ADC/DAC/reference/filter/calibration/isolation/power allocations"),
    ("watchdog_permission", "Independent useful-progress watchdog, gates and inhibits", "exact hardware and quantitative fault behavior; cannot omit to hit price"),
    ("esp_service", "ESP module, protected independent branch and wired diagnostics", "regulator/decoupling/partial-power support, sensors and wiring"),
    ("esp_accessory_automation", "Proposed ESP accessory sensors/drivers/feedback", "NOT IMPLEMENTED; decide base versus optional module, exact loads and single-output ownership"),
    ("entry_protection", "Physical fuses, reverse/transient and electronic branch protection", "coordinated source/cable/fuse/FET/eFuse/TVS circuit; use existing protected outputs where sufficient"),
    ("controller_power", "Controller adapter/conversion and power harness", "screen/core power combined only after budget; field-load power scope explicit"),
    ("display_assembly", "Exact LCD/touch/controller/backlight assembly or monitor", "quoted exact variant and package inclusions"),
    ("display_power", "Display adapter or protected converter branch", "avoid double-counting included adapter; common supply replacement needs new price"),
    ("display_harness", "Video/touch/power cables, retention and extensions", "included cable set may need different lengths and retained connectors"),
    ("enclosure_mounts", "Controller enclosure, screen mounting/bezel, shielding/bonding", "per-tier drawing/BOM; HDPE is not assumed to provide EMC shielding"),
    ("pcb_fabrication", "Actual PCB stackup/area/finish and fabrication", "separate carrier/motion or combined board quotes"),
    ("turnkey_procurement", "PCBWay sourcing, minimums/overbuy and procurement losses", "reconcile inclusions with component basket; no duplicate parts total"),
    ("pcba", "PCBWay setup/assembly/inspection/rework/yield", "quote 1/10/100/1000 good units; stencil scope; setup vs recurring"),
    ("programming", "Host/FPGA/ESP images, identity and programming labor", "versioned images and supported station interfaces"),
    ("factory_test", "Fixtures, test time, calibration and records", "quantitative electrical/functional procedure and serial/revision traceability"),
    ("final_assembly", "Display/controller mechanical and harness integration", "explicit turnkey scope; PCBA alone does not include this"),
    ("qualification", "Thermal, power/fault, timing, EMC/environment and compliance work", "intended markets and required testing; separately allocate nonrecurring cost"),
    ("packaging_logistics", "Packaging, inbound freight/duties and delivered procurement", "avoid duplicate charges already inside supplier/PCBWay quote"),
]

IO = [
    {"id": "baseline-6j-2enc", "status": "Existing study/reference implementation; not qualified product", "motor_channels": 6, "abz_ports": 2, "general_di": 16, "general_do": 8, "enable_topology": "6 sourcing outputs", "drive_alarms": 6, "analog_outputs": 1, "direct_digital_signals": 54, "complete_fitted_cost_usd": prices(), "cost_reference": "research/HARDWARE_COST_COMPARISON.md: old 21.5-inch partial baskets only; +1.53 known old-price power adjustment plus unknown field buck/protection; not added to this matrix", "notes": "Spindle run/direction consume two general DO; probes consume general DI; six drives do not have six external ABZ feedback ports."},
    {"id": "expanded-8j-4enc", "status": "Preferred next candidate, not implemented or priced", "motor_channels": 8, "abz_ports": 4, "general_di": 24, "general_do": 16, "enable_topology": "8 proposed floating isolated switches, parts/rating unselected", "drive_alarms": 8, "analog_outputs": 2, "analog_inputs": 4, "dedicated_probe": 2, "frequency": 2, "pwm": 2, "process_enable": 2, "buses": ["isolated RS485", "isolated CAN", "short timing backplane"], "direct_digital_signals": 92, "complete_fitted_cost_usd": prices(), "cost_reference": "docs/EXPANDED_HARDWARE_TARGET.md; no 8/6 scaling of baseline costs", "notes": "16 proposed 0.5A outputs =8A simultaneous field load before other loads; baseline 6A entry is insufficient. Scope requires fresh enable/power/pin/protocol/BOM work."},
]


def add_known(*values):
    if any(v is None for v in values):
        return None
    return float(sum(Decimal(str(v)) for v in values))


def build():
    cases = []
    for c, d, io, q in itertools.product(COMPUTES, DISPLAYS, IO, QUANTITIES):
        k = str(q)
        cases.append({
            "id": f"{c['id']}__{d['id']}__{io['id']}__q{q}",
            "compute_id": c["id"], "display_id": d["id"], "io_id": io["id"], "quantity": q,
            "module_usd_per_unit": c["module_usd"][k],
            "display_assembly_usd_per_unit": d["assembly_usd"][k],
            "two_item_reference_usd_per_unit": add_known(c["module_usd"][k], d["assembly_usd"][k]),
            "prototype_retail_carrier_reference_usd_per_unit": c["prototype_carrier"]["usd"][k],
            "prototype_three_item_reference_usd_per_unit": add_known(c["module_usd"][k], c["prototype_carrier"]["usd"][k], d["assembly_usd"][k]),
            "custom_carrier_fitted_cost_usd_per_unit": None,
            "complete_io_fitted_cost_usd_per_unit": None,
            "complete_installed_display_package_usd_per_unit": None,
            "complete_manufactured_bundle_usd_per_unit": None,
            "complete_cost_status": "INCOMPLETE",
            "compatibility_status": "SOURCE-CANDIDATE ONLY; not target-tested or approved",
            "unclosed_cost_blocks": [b[0] for b in COST_BLOCKS if b[0] not in {"module", "display_assembly"}]
                + (["module"] if c["module_usd"][k] is None else [])
                + (["display_assembly"] if d["assembly_usd"][k] is None else []),
        })
    return {
        "schema_version": 1, "study_date": DATE, "currency": "USD", "quantities": QUANTITIES,
        "requested_screen_classes_inches": [7,10,12,14,18,21],
        "status": "Dated source observations and quote-preparation matrix; not procurement authorization or a selected BOM",
        "rules": ["Screen size, compute and I/O are independent dimensions.", "USD is source currency, not a confirmed user sales currency.", "null means unknown, never zero; all full costs remain null.", "Retail unit observations do not create volume prices. Only recorded 100+ display tiers extend to 1000; quantity/lead time still need confirmation.", "US power-plug variant is an explicit comparison convention, not a destination-market decision.", "Retail carrier basket and custom-carrier cost are alternative routes; never add both.", "No finished cost combines the old six-joint basket with new module prices or expanded hardware.", "Optional AI and external machine motors/drives/field-load supplies are outside base-controller cost; scope-specific sensors/accessories must be allocated before quoting.", "No supplier contacted, cart submitted, hardware ordered, physical machine connected or existing evidence rebuilt."],
        "evidence_level": {"source_inspection": True, "arithmetic_schema_checks": True, "target_compile": False, "target_runtime": False, "hdl_simulation_for_new_scope": False, "fpga_synthesis": False, "new_circuit_erc": False, "board_drc": False, "physical_measurements": False},
        "sources": SOURCES, "computes": COMPUTES, "displays": DISPLAYS, "io_candidates": IO,
        "cost_blocks": [{"id": i,"scope": s,"closure_needed": g,"quote_usd": prices()} for i,s,g in COST_BLOCKS],
        "cases": cases,
        "compatibility_sources": ["https://www.raspberrypi.com/documentation/computers/compute-module.html", "https://pip-assets.raspberrypi.com/categories/1261-transitioning/documents/RP-008924-WP/Transitioning-from-Compute-Module-4-to-Compute-Module-5", "https://global.bttwiki.com/CB2.html", "research/BTT_COMPUTE_REVIEW.md", "docs/COMPUTE_CARRIER_STRATEGY.md"],
        "soedge_correction": {"connector_pins": 204,"connector_family": "SO-DIMM", "verified_on": DATE,"source": "https://pine64.org/2020/02/03/fosdem-2020-and-hardware-announcements/", "schematic": "https://files.pine64.org/doc/SOEdge/SOEdge-Schematic-v2.0-190919.pdf", "scope": "Connector correction only; 2020 tentative pricing is not current cost evidence."},
        "historical_leads": [{"item": "OSCY OTM-2150 21.5 inch", "source": "research/display-cost-sources.json", "status": "Earlier $100 sample / $96 at 100 / $94 at 1000 advertised lead; exact capacitive package unconfirmed. Excluded from comparable baskets."}, {"item": "User CB2 $40–45 scenario", "source": "research/btt-compute-sources.json", "status": "Currency/vendor/SKU/quantity unverified; excluded from numerical baskets."}, {"item": "Waveshare 21.5inch FHD LCD", "source": "https://www.waveshare.com/21.5inch-FHD-LCD.htm", "status": "Directly re-observed $239.99 on 2026-09-28; distinct open-frame assembly from Luckfox enclosed monitor. Remains an alternative, not the baseline for all sizes."}],
        "commercial_costs_separate": ["warranty/support", "payment/sales-channel fees", "outbound fulfillment", "development recovery", "chosen profit/margin; no percentage accepted"],
    }


def money(v):
    return "unknown" if v is None else f"${v:.2f}"


def render(data):
    lines = ["# Compute, carrier and touchscreen comparison", "", f"Study snapshot: {DATE}; all prices USD before tax, shipping and duties. This extends the [display tiers](../docs/DISPLAY_TIERS.md) across 7/10/12/14/18/21-inch classes. The 21.5-inch screen is one tier. No hardware has been selected, ordered or qualified by this study.", "", "The [machine-readable matrix](compute-display-matrix.json) contains 144 cases: three exact compute candidates × six displays × two I/O scopes × four quantities. **Every complete manufactured-cost field is INCOMPLETE.** Actual listed merchandise is distinguished from missing carrier, power, protection, integration and manufacturing work. Screen size does not reduce I/O capability.", "", "## Exact compute and reference carriers", "", "| Compute variant | RAM / eMMC | Module, qty 1 | Retail carrier reference, qty 1 | Supply / compatibility limit |", "|---|---|---:|---:|---|"]
    for c in COMPUTES:
        s=SOURCES[c["source_id"]]; carrier=c["prototype_carrier"]
        lines.append(f"| [{c['name']}]({s['url']}) | {c['ram_gb']} / {c['emmc_gb']} GB | {money(c['module_usd']['1'])} | [{carrier['name']}]({SOURCES[carrier['source_id']]['url']}) {money(carrier['usd']['1'])} | {s['availability']}; {carrier['status']} |")
    lines += ["", "Both selected Pi module offers are out of stock. Adafruit separately lists the same 2GB/16GB/wireless CM4 configuration at $55, also out of stock; it is not a procurable low-cost assumption. CB2 provides 32GB eMMC versus 16GB in these Pi variants, so the table is not an equal-storage performance comparison. BIQU also lists the same CB2 SKU at $178.45 on another page; the $125.99 dedicated-page observation is preserved without averaging. The user's cheaper CB2 scenario remains unverified.", "", "No published 10/100/1,000-unit module or carrier prices were established. All are null. Retail IO boards are engineering references, not the price of our custom carrier. CB2 + PI4B is specifically an unqualified pairing whose listed merchandise can be added arithmetically, not a claim of compatible CNC operation.", "", "## Exact screen candidates and observed assembly prices", "", "These include a manufacturer-matched screen/touch/control assembly or an enclosed monitor, not a bare LCD. They still exclude installation into the controller product. Regional US plug variants are comparison conventions only. Published 100+ tiers are carried to 1,000 without another discount; stock and capacity at that quantity are unverified.", "", "| Class / actual size | Exact item / SKU | Native pixels | Qty 1 | Qty 10 | Qty 100 | Qty 1,000 |", "|---|---|---|---:|---:|---:|---:|"]
    for d in DISPLAYS:
        lines.append(f"| {d['class_inches']} / {d['diagonal_inches']} in | [{d['name']} / {d['sku']}]({SOURCES[d['source_id']]['url']}) | {' × '.join(map(str,d['native_resolution']))} | " + " | ".join(money(d['assembly_usd'][str(q)]) for q in QUANTITIES) + " |")
    lines += ["", "The 10.1-inch page now returns $78.99 in live JSON-LD and its visible price, superseding the $74.99 search-index observation. The three smaller Waveshare pages expose actual quantity-price rows. The larger options have no verified bulk pricing. These are public offers observed during this study, not negotiated supplier or PCBWay quotations.", "", "| Display | Package and unresolved integration |", "|---|---|"]
    for d in DISPLAYS:
        lines.append(f"| {d['diagonal_inches']} in | {'; '.join(d['package_contents'])}. **Power:** {d['power']}. **Open:** {'; '.join(d['missing_or_unqualified'])}. |")
    lines += ["", "The 18.5-inch $129.99 and 21.5-inch $159.99 Luckfox prices refer to exact capacitive-touch variants. Cheaper similarly named non-touch monitors are excluded. Their manufacturer lists enclosed displays, cables and regional adapters; that improves sourcing clarity over the old ambiguous OSCY sample. It does not establish coolant/dust tolerance, EMC immunity, reliable touch near a VFD or a controller enclosure rating. Factory internal panel and touch-controller revisions still require control.", "", "## Comparable priced basket, quantity one", "", "**Three merchandise items only: selected module + retail reference carrier + selected display assembly.** This omits compute cooling/supply, CNC electronics, qualified installation and manufacturing. Pi baskets contain unavailable module offers; the CB2 carrier pairing is unqualified. No value below is a working controller price, a selected prototype order or a production estimate. Within a screen row the display is held constant; CB2 storage differs. Both I/O scopes have the same three-item arithmetic because neither I/O board is included.", "", "| Display class | CM4 + CM4IO | CM5 + CM5IO REV 2 | CB2 + PI4B candidate |", "|---|---:|---:|---:|"]
    for d in DISPLAYS:
        lines.append(f"| {d['class_inches']} in | " + " | ".join(money(add_known(c['module_usd']['1'],c['prototype_carrier']['usd']['1'],d['assembly_usd']['1'])) for c in COMPUTES) + " |")
    lines += ["", "For the custom-carrier route, module + screen alone ranges from $133.49 (selected CM4/7-inch) to $305.98 (CB2/14-inch); the custom carrier and all machine electronics are unknown. At quantities 10/100/1,000, even the same two- or three-item subtotal remains unknown because compute/carrier prices were not quoted. Do not add only the known display tier and call the smaller number a volume saving. No complete profitable Mesa-priced package has been demonstrated.", "", "## Compatibility work applies to every package", "", "| Boundary | CM4 | CM5 | CB2 |", "|---|---|---|---|", "| Connector / power / recovery | Exact CM4102016 carrier matrix and RUN_PG behavior | Same mechanical family, changed pin functions; pin 92 power-button input; USB/MIPI and power/cooling review | Exact BTT pin table and revision; no universal CM4 socket claim |", "| Screen path | HDMI + USB host touch | HDMI + USB host touch | HDMI + USB host touch, driver/pinmux audit required |", "| Hard real-time path | Qualified Pi CNC1 SPI backend required | Own Pi peripheral/driver qualification required | Qualified Rockchip CNC1 SPI backend required |", "| OS / graphics / thermal | Pinned PREEMPT_RT image, UI/model load and complete timing unmeasured | Same tests plus CM5 power/thermal envelope | Ordinary PREEMPT source setting is not PREEMPT_RT proof; GPU/kernel/CNC1 route open |", "", "The display path is a plausible source-supported interface choice, not tested compatibility. Qualify exact native mode/EDID, USB touch identity/firmware, rotation/scaling, recovery, supply sequencing and partial-power behavior on each offered host. Do not infer USB-C DisplayPort output from a connector. Keep display traffic off dedicated motion SPI. Qualify 60Hz initially; monitor advertising of 120/144Hz does not establish that controller mode. The 14-inch panel has more pixels than FHD 18/21-inch options; size alone does not set compute load. The 7-inch 800×480 and wide 12.3-inch candidates need particularly careful UI acceptance.", "", "Sources: [Raspberry Pi compute documentation](https://www.raspberrypi.com/documentation/computers/compute-module.html), [CM4/CM5 transition guide](https://pip-assets.raspberrypi.com/categories/1261-transitioning/documents/RP-008924-WP/Transitioning-from-Compute-Module-4-to-Compute-Module-5), [BTT CB2 manual](https://global.bttwiki.com/CB2.html), [existing BTT source review](BTT_COMPUTE_REVIEW.md). Shared shape is not electrical or real-time compatibility. PINE64 explicitly specifies a [204-pin SO-DIMM for SOEdge](https://pine64.org/2020/02/03/fosdem-2020-and-hardware-announcements/); its old tentative price is not used.", "", "## Keep the machine hardware scopes separate", "", "| Scope | Six/two baseline | Eight/four candidate |", "|---|---|---|", "| Motor / ABZ ports | 6 / 2 | 8 / 4 |", "| Additional general DI / DO | 16 / 8 | 24 / 16 |", "| Enable topology / alarms | 6 sourcing enables / 6 alarms | 8 floating isolated switches / 8 alarms |", "| Specialized functions | One analog output; probes use general DI | Two AO, four AI, dedicated probes/frequency/PWM/process paths, isolated buses and backplane |", "| Direct digital signals | 54 before support | 92 before support |", "| Complete fitted cost | Unknown | Unknown; cannot scale baseline by 8/6 |", "", "The [earlier costing](HARDWARE_COST_COMPARISON.md) stays a historical six/two/21.5-inch scenario. The later power correction and unpriced field buck/protection mean it is not a fitted BOM. The expanded design changes enable technology and simultaneous field power: 16 × 0.5A already totals 8A before other loads. Screen choice does not fix those gaps or inherit their qualification.", "", "## Complete quote scope", "", "Every matrix case carries these required blocks. Quotes must replace or reconcile existing parts, not double-count them. An included display adapter/cable is part of that SKU price; a custom common-power or retained-cable substitution needs an explicit replacement cost.", "", "| Block | Required closure |", "|---|---|"]
    lines.extend(f"| {s} | {g} |" for _,s,g in COST_BLOCKS)
    lines += ["", "Warranty/support, payment or sales-channel fees, outbound fulfillment, development recovery and the selected margin remain separately defined business costs. No final sales currency or per-tier retail target is assumed. Optional AI remains outside the base. ESP accessory automation is a new proposal: protected branches, sensors, drivers and feedback are neither implemented nor free, and base/accessory allocation must be decided before a complete quote. Industrial reliability requires the protection and qualification blocks; they cannot be deleted to improve the displayed cost.", "", "## Next decisive gaps", "", "1. Choose bounded launch/test candidates from this matrix after UI viewport review; keep all requested classes represented as options. Confirm actual module supply, exact SKU and carrier/recovery pin matrix. No order is authorized here.", "2. Finish separate six/two and eight/four fitted circuits, pin/power budgets and BOMs. Resolve display power contradictions and mechanical/cable retention per tier; define ESP accessory ownership and base/accessory cost allocation.", "3. Prepare PCBWay fabrication/assembly files, fitted/DNP BOM and approved alternatives, placement, programming and quantitative test/fixture scope. Quote good units at 1/10/100/1,000 with setup separated. Final enclosure/display integration must be explicitly included or separately quoted.", "4. Prove a reproducible host/CNC1 route and later loaded physical timing with representative UI, storage, network and thermal load before final production layout. Only then can complete cost and capability select a production package.", "", "## Evidence and reproduction", "", "This work performs source inspection plus offline matrix/arithmetic checks. It makes no new target compilation, LinuxCNC target test, HDL simulation, FPGA synthesis, circuit ERC, board DRC or physical measurement claim. It leaves older workbook and hashed engineering evidence unchanged.", "", "Sources were read directly over HTTPS with Python urllib.request; JSON-LD offers, official Shopify variant JSON, PiShop price/currency/availability microdata and Waveshare quantity table rows were inspected. The JSON records exact URLs, evidence dates and selected variants; no full HTML is stored. Some web-tool requests returned 403, while direct public HTTPS retrieval succeeded. Where an exact retrieval timestamp was not retained, the record states only its date. Storefront availability is not a guaranteed stock commitment.", "", "`python tools/build_compute_display_matrix.py --check` validates all 144 cases and generated-file equality without network or mutation. `--write` deliberately regenerates only the new JSON and this report from the dated observations in that script. Neither command refreshes prices. Review new primary evidence before changing those constants.", ""]
    return "\n".join(lines)


def validate(data):
    assert len(data["cases"]) == 144
    assert len({r["id"] for r in data["cases"]}) == 144
    assert {d["class_inches"] for d in DISPLAYS} == {7,10,12,14,18,21}
    for row in data["cases"]:
        assert row["complete_manufactured_bundle_usd_per_unit"] is None
        assert row["complete_cost_status"] == "INCOMPLETE"
        assert row["custom_carrier_fitted_cost_usd_per_unit"] is None
        assert row["complete_io_fitted_cost_usd_per_unit"] is None
        assert row["unclosed_cost_blocks"]
        assert row["two_item_reference_usd_per_unit"] == add_known(row["module_usd_per_unit"],row["display_assembly_usd_per_unit"])
        assert row["prototype_three_item_reference_usd_per_unit"] == add_known(row["module_usd_per_unit"],row["display_assembly_usd_per_unit"],row["prototype_retail_carrier_reference_usd_per_unit"])
        if row["quantity"] > 1:
            assert row["two_item_reference_usd_per_unit"] is None
            assert row["prototype_three_item_reference_usd_per_unit"] is None
    assert add_known(0,1) == 1 and add_known(None,1) is None
    for group in (COMPUTES,DISPLAYS):
        for item in group:
            assert item["source_id"] in SOURCES
    return {"case_count":144,"computes":3,"screen_classes":6,"io_scopes":2,"quantities":QUANTITIES,"complete_costs":0,"evidence":"source/arithmetic/data consistency only"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=parser.parse_args()
    data=build(); result=validate(data)
    outputs={OUT:json.dumps(data,indent=2,ensure_ascii=False)+"\n",REPORT:render(data)}
    if args.write:
        for path,text in outputs.items():
            path.write_text(text,encoding="utf-8",newline="\n")
        result["action"]="wrote only new matrix and report"
    else:
        for path,text in outputs.items():
            if path.read_text(encoding="utf-8") != text:
                raise SystemExit(f"Generated data differs: {path}")
        result["action"]="read-only check passed"
    print(json.dumps(result))


if __name__ == "__main__":
    main()

