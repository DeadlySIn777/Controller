# CNC controller market landscape

> **Commercial direction (29 September 2026):** our original software is a commercial, licensed product. It is not freeware and no open-source release is promised. Third-party components keep their own licences (LinuxCNC is GPL-2.0). Where this study says a competitor is open or closed, it describes that competitor's licensing. Our differentiator is documented, scriptable, reversible configuration and published module/interface specifications, together with tested compatibility lists for off-the-shelf peripherals that customers can buy anywhere.

Research date: 28 September 2026. Primary sources were opened on that date. Reseller prices are labelled as such. Figures for this project are design targets from [PROJECT_MEMORY.md](../PROJECT_MEMORY.md), not measured capability. The per-product records with every source URL are in [market-landscape.json](../WORKSPACE_REFERENCES.md#artifact-14087d5a96af4ce8).

**Market positioning: CNC controller (PROJECT_MEMORY.md read on 28 Sep 2026; research sources checked 28 Sep 2026)**

This project has no qualified product yet. Every "our product" item below is a design target from PROJECT_MEMORY.md, not measured evidence. The 8-channel target has replaced the 6-joint/2-encoder baseline, and none of the baseline's evidence carries over. Prices marked "est." are the researchers' own estimates. DDCS and Asian OEM prices come from resellers or marketplaces, not the makers.

---

**1. Verdict on "nothing out there like this, only non-industrial 3D-printer boards"**

As stated, the claim is false. A narrower version is true for the sources checked.

It is false because several PC-free controllers sold with a screen are real CNC products, not printer boards:
- **DDCS Expert (M350):** it uses the same basic design as this project, an ARM running Linux with an FPGA generating the step pulses. It outputs 1 MHz per axis on 5 differential step/dir channels, has 24 isolated inputs and 21 isolated outputs at 24 V, a 7-inch screen, parameter backup/restore and power-cut recovery. A reseller sells it for about US$430 (https://www.amazon.com/Axis-Controller-Standalone-Engraving-DDCSE/dp/B09WLDLP22, https://www.nvcnc.net/ddcs-expert.html).
- **DDCS V4.1:** US$334-389 from resellers (https://www.amazon.com/s?k=DDCS+V4.1+controller).
- **MASSO G3 Touch:** 15-inch touchscreen, 24 isolated inputs, US$890-2,090 (https://www.masso.com.au/controller-portfolio/).
- **Centroid Acorn family:** isolated inputs, relay outputs, a setup wizard and backup/restore (https://shopcentroidcnc.com/shop/cnc-controllers/acornsix-cnc-controller-kit/).
- **Mesa 7I96S and 7I95T:** industrial-grade FPGA boards with isolated 5-36 V I/O and 10 MHz step rates. They have been the standard LinuxCNC hardware for years (https://store.mesanet.com/index.php?route=product/product&product_id=374).
- **Chinese and Taiwanese OEM controls** (GSK, Weihong, Syntec): 24 V I/O with PLC, sold for about US$1,500-5,000.

The strongest counter-example is DDCS Expert. It already delivers a screen, isolated 24 V I/O and FPGA pulse generation inside or just above the illustrative US$249-400 band.

What is true, within the sources checked: no product combines all of the following:
- standalone operation
- an included touchscreen
- at least 8 differential step/dir motor channels
- axis encoder inputs at the controller
- isolated 24 V I/O
- documented, scriptable configuration and published interfaces
- a price near US$400

The highest channel count on any PC-free product found is 5. That covers MASSO, DDCS Expert, Redline/RealTime and Buildbotics (4). None of those PC-free products takes axis encoders at the controller. This is "not found in the sources checked", not proof that nothing exists.

A more accurate wording: "Industrial standalone controllers with screens exist. None I found combines 8-12 differential channels, axis encoders, isolated 24 V I/O, an included touchscreen and documented, scriptable configuration at DDCS-class prices."

---

**2. Comparison of the closest competitors**

Channel counts are motor outputs, not axes. A dual-motor gantry uses two.

| Product | Price to run, with a screen (USD) | Motor channels | Axis encoders at controller | Field I/O | Standalone? | Openness / scripting | Repair / modularity | Setup experience | Key sources |
|---|---|---|---|---|---|---|---|---|---|
| DDCS Expert (M350) | ~$430 reseller; 7" 1024x600 screen with 40 keys included (touch not confirmed); 24 V supplies extra | 5 differential, 1 MHz | None found (not confirmed) | 24 isolated in / 21 isolated out, 24 V | Yes (ARM Linux + FPGA) | Closed; I/O mapping | One panel unit | Parameter screens, parameter backup/restore; no wizard found | amazon.com/…/B09WLDLP22; nvcnc.net/ddcs-expert.html |
| DDCS V4.1 | $334-389 reseller; 7" screen with keys, not touch | 4, 500 kHz | None documented | 18 isolated in / 3 isolated out | Yes | Closed | One unit | Probing, power-cut recovery | amazon.com/s?k=DDCS+V4.1+controller; hlt-cnc.com/…/DDCS-V4.1-English-manual.pdf |
| MASSO G3 Touch | $890 (3-axis) / $1,090 (5-axis + slaving) / $2,090 (Lua); 15" touch included | 5, 110 kHz | Spindle only (60 kHz); servo encoders connect to the drive | 24 isolated in (5-24 V); 18 outputs are 5 V TTL, so 24 V loads need a relay module | Yes | Closed; Lua only in the $2,090 tier | All-in-one unit | Wizards, load/save settings | masso.com.au/product/masso-g3-touch-cnc-controller/; masso.com.au/controller-portfolio/; docs.masso.com.au/MASSO_FAQ/encoders |
| Buildbotics (+ Onefinity 10.8" touch) | $499 with no screen; ~$640 with the $139.50 Onefinity screen (sold to Onefinity owners only) | 4 onboard drivers, 250 k steps/s | None documented | 10 in / 5 out at 5 V; not 24 V | Yes (Pi) | Open: GPL firmware, CERN-OHL-S PCB, REST/WebSocket API, YAML config schema | Monolithic board | Web settings, backup/restore | store.buildbotics.com/buildbotics-cnc-controller/; github.com/buildbotics/bbctrl-firmware; onefinitycnc.com/product-page/10-8-hi-def-touch-screen |
| Redline HMI + RealTime | Controller not sold separately; $1,575 kit on sale (HMI, controller and closed-loop motors; trade-in required); 15" touch | 5 driver outputs (4 axes), 100 kHz | None; uses the drive error input | 8 isolated in / 4 isolated out; I/O expansion bus | Yes, with the HMI | Proprietary | Separate HMI and controller; expansion bus | OTA updates, power-fail recovery | redlinecnc.com/redlinecontrollerspecification; onefinitycnc.com/…/elite-redline-upgrade-kit… |
| Centroid Acorn + CNC12 Pro | $369 + $179 licence; est. $850-1,200 with a Windows PC and touch monitor | 4 | 1 (spindle) | 8 isolated in / 8 relay out | No (Windows PC) | Closed; PLC and macros editable | Separate relay module | Wizard, automatic firmware install, backup/restore | shopcentroidcnc.com/acorn-cnc-controller/ |
| Centroid AcornSix | $999 + $249 licence; est. $1,550-1,900 with a PC and touch monitor | 6 | 1, or 9 with the SCOUT expansion | 16 isolated in / 16 relay out | No | Closed | Plug-in Relay8 modules | Wizard, auto-squaring, backup/restore | shopcentroidcnc.com/shop/cnc-controllers/acornsix-cnc-controller-kit/ |
| Centroid Hickory / Oak | $1,999 / $1,495, plus PC and licence (Hickory also needs EtherCAT drives) | Hickory: 8 over EtherCAT, no step/dir. Oak: 4, expandable to 8 | Hickory through the EtherCAT drives; Oak: 6 | Oak: 16 isolated in / 9 relay out | No | Closed | Relay modules | Wizard, backup/restore | shopcentroidcnc.com/shop/cnc-controllers/hickory-cnc-controller-kit/; …/oak-cnc-controller-kit/ |
| Mesa 7I96S + Pi 5 + 10" Touch Display 2 (DIY) | est. $385-420 in parts, no enclosure | 5, 10 MHz | 1 | 11 isolated in / 6 isolated out (36 V) | Yes, once assembled | LinuxCNC is GPL and Mesa's FPGA firmware source is published; board hardware closed; HAL/INI/Python | Whole-card swap; config lives on the host | Third-party Mesa Configuration Tool II GUI; no backup tool | store.mesanet.com/…product_id=374; github.com/jethornton/mesact |
| Mesa 7I95T + Pi 5 + touch (DIY) | est. $500-520; board out of stock | 6, 10 MHz | 6 | 24 isolated in / 6 isolated out | Yes, once assembled | Same as 7I96S | Whole-card swap | Same as 7I96S | store.mesanet.com/…product_id=383 |
| BTT Manta M8P + CB2 + HDMI7 | ~$341 at sale prices, before drivers and power supply | 8 StepStick sockets (onboard drivers), single-ended | None | Printer-grade: inputs clamped to 5 V, no isolation | Yes (Klipper on CB2) | Klipper GPL; text config | Socketed drivers; swappable compute module | printer.cfg; no CNC setup | biqu.equipment/products/manta-m4p-m8p; biqu.equipment/products/bigtreetech-hdmi5-v1-0-hdmi7-v1-0 |
| Duet 3 6XD + DuetScreen | $242.99 + $122.99 ≈ $366 with no power supply; extra axes need CAN boards (1HCL $105.99; 1XD price not found) | 6 external-driver ports (single-ended 5 V) plus CAN-FD expansion | Only through a 1HCL board per axis (closed loop in the drive board) | 4 opto-isolated in/out pairs (12-50 V) | Yes | Open schematic; RepRapFirmware open; macros | CAN-FD expansion boards, the strongest modular design found | config.g files; online config tool | docs.duet3d.com/…/Duet_3_Mainboard_6XD_Hardware_Overview; filastruder.com/products/duet3d-duetscreen |
| PoKeys57CNC | $162.85 board; est. $700-1,150 with Mach4, breakout board, PC and monitor | 8, 125 kHz | Several (exact count not found) | Mostly logic-level; 4 isolated open-collector outputs | No | Closed firmware; onboard PLC | Board plus PoExtBus add-ons | Configuration utility | poscope.com/product/pokeys57cnc/; cnc4pc.com/…pokeys57cnc… |
| PlanetCNC Mk3 9-axis | ~$285 ex VAT with licence; est. $550-650 with isolation boards, Pi and display | 9, 110 kHz | Spindle only | Not isolated on the board | No | Closed; licensed | Separate accessory boards | TNG GUI | shop.planet-cnc.com/product/cnc-controller-mk39/ |
| Sienci SLB-EXT + gControl | $240 + $75 power supply + $795 ≈ $1,110; 15.6" touch Windows PC | 5 differential, with alarm | None | 5/24 V selectable limit inputs; isolation not stated | No (gControl is a Windows PC) | Sienci says it will open-source it later; not yet released | Separate board and PC | gSender comes preconfigured | sienci.com/product/slb-ext-closed-loop-controller/; sienci.com/product/gcontrol/ |
| Flexi-HAL | $108 board; Pi and screen extra (not priced) | 5 isolated differential | 1 (differential spindle encoder) | Isolated machine I/O; alarm inputs | With a Pi (LinuxCNC via Remora) | Open hardware (CERN-OHL-S); grblHAL | RJ45 limit-switch breakouts | No wizard | expatria.myshopify.com/en-us/products/flexihal-isolated-cnc-controller-rev-a7… |
| Tormach PathPilot | $919.05 + $589 17" touch kit = $1,508; operator console $2,529 | None on the controller (uses the Tormach machine's control module) | On the machine | On the machine's control module | Yes | GPL LinuxCNC fork, officially for Tormach machines only | Separate replaceable parts | Conversational programming | tormach.com/pathpilot-controller-51718.html; tormach.com/1100m-mx-pathpilot-operator-console.html |
| GSK 980MDi (Asian OEM class) | $1,938 controller from a reseller; bus servos extra | Up to 5 (6 optional), servo bus | 2 encoder inputs, plus 17-bit servo encoders over the bus | 48 in / 38 out (isolation not stated) | Yes | Closed; ladder PLC | Panel, bus drives and I/O units | Backup/recovery | paycnc.com/gsk980mdi_p0063.html |
| This project (design target only, not built or measured) | Illustrative US$249 comparison; complete price per screen tier not yet set | 8 differential with enable and alarm, expandable to 12 | 4 (target) | Protected, isolated 24 V (target) | Yes (LinuxCNC on a compute module) | Open, one contract for CLI, API and UI, preview/diff, reversible changes (target) | Modules replaced without rewiring; removable settings cartridge (target) | Profiles, generated wiring guidance, guided checks (target) | PROJECT_MEMORY.md |

Two related products were not tabulated:
- **Weihong NK300CX PLUS:** up to 10 axes on a servo bus, about US$1,500-2,000 (reported), sold mainly to machine builders (https://www.weihong.com.cn/en/products/detail/145).
- **Siemens 808D Advanced:** US$5,167 for the panel alone (https://www.machinetoolproducts.com/sinumerik-808d-advanced-milling-ppu-161-3-horizontal/).

---

**3. What is unoccupied at the target price, and what others already offer**

Unoccupied in the sources checked:
- **8+ differential channels, standalone, with an included touchscreen, under about $1,000.** Products with 8 or more channels are one of these:
  - printer-grade: Manta M8P
  - PC-bound: PoKeys, PlanetCNC, Hickory
  - OEM bus systems at $1,500+: Weihong
- **Axis encoder inputs at a standalone controller with a screen, near $400.** Encoder-capable boards need a PC (7I95T, Oak) or come as a bus servo package ($1,938+ for GSK).
- **Documented, scriptable configuration with published interfaces, isolated 24 V I/O and an included screen together.** (Competitors' licensing is noted for comparison only; our original software is commercial and licensed, see the note at the top.)
  - Buildbotics is open but has 5 V I/O and no screen.
  - Flexi-HAL is open and isolated but has 5 axes and no screen.
  - DDCS has isolated I/O and a screen but is closed.
- **Repair by module without rewiring, a removable settings cartridge, and CAD-guided setup.** No product states any of these.
- **Published measured I/O ratings.** None of the vendors checked cites IEC 61131-2 or a similar I/O standard.

Already offered by others, so these cannot be headline claims:
- **Standalone touchscreen, no PC:** MASSO (15-inch), Redline (15-inch), the Tormach console, DDCS (7-inch with keys), and the SainSmart pendant ($149, 7-inch touch).
- **Isolated 24 V I/O plus a screen at about $400:** DDCS Expert and V4.1.
- **FPGA pulse generation with Linux:** DDCS, and Mesa with LinuxCNC.
- **Setup wizard, automatic firmware/driver install, config backup/restore, auto-squaring:** Centroid CNC12. Backup/restore is also offered by DDCS, Buildbotics, GSK and Syntec. The research found no product that auto-detects drives. Centroid's "automatic" refers to firmware and driver installation.
- **Open API and published config schema:** Buildbotics (REST/WebSocket and YAML). YAML config without compiling is also offered by FluidNC and PiBot.
- **Scripting:** MASSO Lua ($2,090 tier), Mach4 Lua, UCCNC macros, and LinuxCNC HAL/Python.
- **Modular expansion:** Duet CAN-FD boards, Centroid relay and I/O modules, the Redline expansion bus, FluidNC I/O modules.
- **Power-loss recovery:** DDCS, GSK, Redline.
- **Pi 5 + LinuxCNC + touchscreen:** available DIY with Mesa and the official LinuxCNC Pi 4/5 image. Tormach sells a packaged version, but only for its own machines.

---

**4. Differentiators to build around (all still need evidence)**

1. **Channel count, standalone.** 8 differential step/dir channels with individual enable and alarm, expandable to 12, with no PC. The highest PC-free count found elsewhere is 5.
2. **Axis encoders at the controller.** 4 encoder inputs on a standalone unit. No PC-free product checked has this.
3. **Open and scriptable from one contract.** The CLI, API, configuration schema and touchscreen UI use the same service, with validation, preview/diff and reversible changes. The point is doing this with industrial I/O. Buildbotics already proves open plus API on its own.
4. **Repair without rewiring.** Keyed pluggable module groups, plus a protected removable settings cartridge that holds the versioned configuration. No product checked states either.
5. **Published measured I/O, EMC and protection figures instead of an "industrial" label.** The competitors checked use "industrial" as marketing without a cited standard.

Keep these out of the headline: CAD-guided setup, AI configuration and the six-screen range. They are proposals with no evidence yet, and the screen range is a packaging choice, not a capability.

Positioning statement these support:
"A standalone LinuxCNC controller with an included touchscreen, 8 differential motor channels (expandable to 12), axis encoder inputs and isolated 24 V I/O. Every setting is documented, scriptable and reversible from the screen or a command line, and a failed section can be swapped without rewiring or losing the machine setup. It is priced against DDCS-class standalone controllers, not PC-based kits costing $1,000 or more."

Do not say "first industrial standalone controller", "only non-printer option" or "certified industrial".

---

**5. Risks**

**Price pressure**
- **Buyers already have cheaper options:**
  - DDCS Expert: ~$430 with 24/21 isolated I/O and a screen.
  - DDCS V4.1: $334-389.
  - BTT Manta M8P + CB2 + HDMI7: ~$341 for 8 printer-grade channels with a touchscreen.
  - Mesa 7I96S DIY build: est. $385-420.
  - FluidNC and PiBot boards: under $100.
- **Our bill of materials is heavier:** 8-12 differential channels, 4 encoders, protected isolated I/O, pluggable modules, a cartridge, an enclosure, a power supply and a touchscreen. Built by PCBWay turnkey at low volume, that package may land above DDCS pricing, and the 12-channel expansion adds cost on top.
- **The price band is not settled:** US$249 is illustrative, and each screen tier's complete package has not been costed.
- **Upper bound:** GSK and Weihong already sell 5-10 axis controls at $1,500-2,000, and they could move down-market.

**Competitors closing the gap**
- PlanetCNC Mk4 has been announced but its shipping status is unconfirmed (reported as Ethernet, 8 axes, about 50 in / 50 out).
- Sienci says it will open-source the SLB-EXT.
- Mesa Configuration Tool II and the official Pi image make the DIY route easier.
- DDCS could add axes.

**"Industrial" expectations and certification**
- Buyers who hear "industrial" may expect the following. These names are general regulatory context, not from the research:
  - CE/UKCA EMC and low-voltage conformity
  - UL/CSA listing or panel-builder acceptance in North America
  - IEC 61131-2-style I/O ratings
  - IEC 61000 immunity levels
  - documented safety behaviour
- PROJECT_MEMORY.md records no certification claim, and it requires machine safety functions to stay independent of the controller.
- Until the whole unit's power, I/O, EMC and environmental behaviour has been measured, "industrial" should describe design intent only.

**Support burden**
- **Large configuration matrix:** user-editable configuration, scripting, third-party Modbus and USB adapters, many screen sizes, 8-12 channels, plasma modules and user-built machines.
- **Established competitors:** Centroid and MASSO have mature ecosystems, and GSK and Siemens rely on distributors and integrators.
- **Modification and warranty:** Sienci's warranty requires unmodified firmware. Our warranty and support terms need an equivalent position on user configuration and scripting.
- **Promises this creates:** the module-swap promise commits us to keeping affordable spares available and to guided re-verification after each swap.

**Evidence gap**
- **Nothing is built:** no board DRC or physical measurements exist for the 8-channel design, and the current 64-byte CNC1 frame cannot carry 12 channels.
- **Claims must wait:** every differentiator above is a target until it passes tests and measurements.

Sources: C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/PROJECT_MEMORY.md, plus the product URLs above.
