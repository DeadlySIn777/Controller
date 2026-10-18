# CM4/CM5-family compute bay: pin audit and selector proposal

30 September 2026. **Source inspection complete; no carrier or motion profile is electrically released.** Scope: Raspberry Pi CM4, Raspberry Pi CM5, BTT CB2 and the published BTT CB1 SD revision. CB1 eMMC is a separate, partially documented profile. This continues the existing [carrier strategy](../../docs/COMPUTE_CARRIER_STRATEGY.md); it does not restart the architecture, add other compute families, change frozen IS-1, or change any circuit source.

The dual-100-contact, 40 × 55 mm module bay is a useful common mechanical direction. A shared subset can support one HDMI display, USB2 touch/adapters, Ethernet and a dedicated five-wire motion SPI path. **Pi-native chip selects, universal recovery wiring, and automatic pre-power module identification do not carry over to all four families.** A cold-start DIP selector can choose a preinstalled module profile; it cannot correct electrical conflicts or turn a Pi image into an Allwinner/Rockchip image.

## Evidence package

- [All 200 contacts in CSV](../../WORKSPACE_REFERENCES.md#artifact-fb125458d8fdd87e) and [JSON](../../WORKSPACE_REFERENCES.md#artifact-e09208b017ae96b8): 800 contact entries, connector-local numbering, individual Pi PDF-page references, BTT manual cross-checks, proposed routing rules, power direction and restricted-contact notes.
- [Per-module transport proposals](../../WORKSPACE_REFERENCES.md#artifact-610d0bb526b48626), [hashed source manifest](../../WORKSPACE_REFERENCES.md#artifact-5a612adeb508a436), [verification receipt](../../WORKSPACE_REFERENCES.md#artifact-8c75a7cdc588a4c0) and [reproducible comparison](../../WORKSPACE_REFERENCES.md#artifact-03fbd003ab1af509).
- Primary sources: [CM4 datasheet](https://datasheets.raspberrypi.com/cm4/cm4-datasheet.pdf), [CM5 DS-6](https://pip-assets.raspberrypi.com/categories/944-raspberry-pi-compute-module-5/documents/RP-008180-DS-6-cm5-datasheet.pdf), [CM4→CM5 transition guide](https://pip-assets.raspberrypi.com/categories/1261-transitioning/documents/RP-008924-WP/Transitioning-from-Compute-Module-4-to-Compute-Module-5), [CB1 table](https://global.bttwiki.com/CB1.html), [CB2 table](https://global.bttwiki.com/CB2.html), pinned [CB1 SD V2.2 schematic](https://github.com/bigtreetech/CB1/blob/38b117016699cf363ea2f452e828a5ce93c1de16/Hardware/BIGTREETECH_CB1_V22_220812_SCH.pdf), pinned [CB1 manual](https://github.com/bigtreetech/CB1/blob/38b117016699cf363ea2f452e828a5ce93c1de16/BIGTREETECH%20CB1%20User%20Manual.pdf) and [CB2 manual](https://github.com/bigtreetech/CB2/blob/a5fc72264062e27b603a024f08ade60eeba3f0ec/BIGTREETECH%20CB2%20User%20Manual.pdf).

Every table contains contacts 1–200 exactly once; all four have the same 51 ground contacts. The comparison retained all primary-file hashes unchanged. This is source/table verification, not ERC, DRC, target compilation, synthesis, signal-integrity simulation or physical measurement. No existing board has acquired a qualified compute bay through this report.

## Proposed fixed common subset

| Function | Global connector contacts | Proposed treatment |
|---|---|---|
| Ground | 51 positions; complete list in matrix | Connect all; maintain interface return paths |
| Main module input | 77, 79, 81, 83, 85, 87 | One protected, regulated 4.75–5.25 V supply shared across contacts |
| Module 3.3 V output | 84, 86 | Module-domain reference/light loads only; never parallel with MC/ESP regulators |
| Module 1.8 V output | 88, 90 | Unused in the initial common subset |
| Pi GPIO reference | 78 | Tie to the module's own 84/86 output for 3.3 V operation; BTT tables mark 78 NC |
| Ethernet PHY connection | 3/5, 4/6, 9/11, 10/12 | Reviewed 1:1 magnetics/ESD; CB1 has only two active pairs and a polarity discrepancy |
| USB2 | 103 D−, 105 D+ | Host touch and ordinary adapters; service/recovery role is module-specific |
| HDMI0 | 151 CEC; 153 HPD; 170/172 TX2; 176/178 TX1; 182/184 TX0; 188/190 clock; 199 SDA; 200 SCL | One common video interface with actual HDMI/ESD/backfeed review |
| Motion SPI | 38 clock, 40 MISO, 44 MOSI, **54 proposed CS_FB, 47 proposed CS_CMD** | Module-specific pinmux/driver; no shared TFT/CAN traffic |
| Manual boot request | 93 | Ground-only service candidate, qualified separately by module/revision |
| USB host/OTG selection | 101 | Pi/CB2 role input; CB1 SD NC; no direct powered-host connection during recovery |

These are proposed assignments, not net aliases already integrated into the controller. Pin 93 naming does not establish a universal boot procedure or LOW threshold. GPIO-VREF compatibility refers only to the documented BTT revisions; connector shape does not establish future-module support.

HDMI plus USB touch serves the 7-, 10-, 12-, 14-, 18- and 21-inch classes without changing motor capacity. Each exact screen still requires resolution, Linux touch, display power, mounting and combined-load qualification. A USB-C connector alone supplies neither DisplayPort alternate mode nor a universal one-cable screen connection.

## Dedicated dual-CS FPGA path

| Signal/contact | CM4 | CM5 | CB1 SD V2.2 | CB2 |
|---|---|---|---|---|
| Clock / 38 | GPIO11, SPI0 | GPIO11, RP1 SPI0 | PH6, SPI1 | GPIO3_C3, SPI1 M1 |
| MISO / 40 | GPIO9 | GPIO9 | PH8 | GPIO3_C2 |
| MOSI / 44 | GPIO10 | GPIO10 | PH7 | GPIO3_C1 |
| Proposed CS_FB / 54 | GPIO4 | GPIO4 | PC7 | GPIO3_A1 |
| Proposed CS_CMD / 47 | GPIO23 | GPIO23 | PC11 | GPIO4_C6 |
| Pi CE0 / 39 | GPIO8 | GPIO8 | **NC** | GPIO4_A2, ordinary GPIO assignment |
| Pi CE1 / 37 | GPIO7 | GPIO7 | PG8 | GPIO0_A6 |

Pins 54 and 47 are stronger common GPIO-CS candidates than copying Pi CE0/CE1. In the correct pinned [BTT CB2 device tree](https://github.com/bigtreetech/linux-rockchip/blob/340c270b968917f78c6ced356a4f0365b453f545/arch/arm64/boot/dts/rockchip/rk3566-bigtreetech-cb2.dts#L1449-L1457), SPI1 uses the M1 clock/data mux and GPIO chip selects: GPIO4_C6 at logical reg 0, GPIO3_A1 at reg 1. The controller is disabled by default. Its third listed select is not established as an available contact in the CB2 module table. The [matching pinctrl](https://github.com/bigtreetech/linux-rockchip/blob/340c270b968917f78c6ced356a4f0365b453f545/arch/arm64/boot/dts/rockchip/rk3568-pinctrl.dtsi#L2300-L2314) corroborates the clock/data assignments.

CB1's [pinned instructions](https://github.com/bigtreetech/CB1/blob/38b117016699cf363ea2f452e828a5ce93c1de16/readme.md#L140-L148) corroborate PH6/PH8/PH7 and PC7/PC11 for the SD version. Its eMMC version instead uses PI14/PI5 for those two CS roles in the 40-pin-header documentation. That does not supply a complete audited 200-contact eMMC schematic. Disable TFT35, MCP2515 and other clients on the motion bus. Pi profiles must also reserve GPIO4 against 1-Wire use and GPIO23 against competing functions.

The shared logical target remains frozen **IS-1's CS_FB/CS_CMD, 176-byte feedback and 96-byte command**. Mapping it to these contacts is a new carrier/driver proposal, not an ABI revision. At 5 MHz those 272 bytes alone take 435.2 µs, before guards, gaps, control computation or scheduler delay. CB2's supplied [spidev reg-0](https://github.com/bigtreetech/linux-rockchip/blob/340c270b968917f78c6ced356a4f0365b453f545/arch/arm64/boot/dts/rockchip/overlay/rk3566-spidev1_0.dts) and [reg-1](https://github.com/bigtreetech/linux-rockchip/blob/340c270b968917f78c6ced356a4f0365b453f545/arch/arm64/boot/dts/rockchip/overlay/rk3566-spidev1_1.dts) overlays request 1 MHz: 2.176 ms wire time alone, insufficient for the required 1 ms servo cycle. This is a default configuration finding, **not a measured maximum speed**.

All four SoCs need their own target transport qualification. A working spidev transfer is not a deadline proof; the present main CNC1 transport is a separate 64-byte historical backend, and the CNC3 host/model work does not establish physical dual-CS behavior. A Pi-recognizing HostMot2 driver is not automatically a driver for our custom endpoint. Measure actual chip-select continuity, transaction framing, read/write direction changes, clock/data setup/hold, full-cycle timing and the independent fault path under local graphics, storage, networking and thermal load. Use at least five qualified interface channels: four host→FPGA, one FPGA→host. The flash-restore path and separate CAN bus remain additional interfaces, not spare capacity on these two motion CS signals.

## Ethernet, USB and boot differences that need circuit decisions

CM4, CM5 and CB2 expose four Gigabit PHY pairs at the same positions. CB1 exposes 100 Mb Ethernet on 4/6 and 10/12, leaving 3/5 and 9/11 NC. Its table calls **10 RX+ / 12 RX−**, whereas Pi/CB2 call **10 pair0− / 12 pair0+**. Pi documents PHY polarity correction; equivalent CB1 behavior was not established here. The [BTT PI4B reference carrier schematic](https://github.com/bigtreetech/PI4B-Adapter/blob/3411b7207abd1d0d5806034a3bf041aafc0a24e9/Hardware/BIGTREETECH%20PI4B%20Adapter%20V1.0-SCH.pdf) uses a standard four-pair MagJack and module-matched reference treatment, which is useful vendor precedent, not our carrier's qualification. Resolve CB1 polarity/PHY magnetics against the exact revision and test it; do not silently declare the discrepancy harmless. Ethernet LEDs at 15/17/19 are not interchangeable control functions across profiles.

Pins **103/105** carry USB2 OTG on Pi/CB2 but **USB1 host** on published CB1 SD V2.2. CB1 SD's OTG/FEL USB0 is at **140/142**. Those same contacts are camera clock on CM4 and **SuperSpeed transmit on CM5**. They cannot be universally connected to a USB2 service port. A separate CB1-SD population/isolated service route, or recovery through its removable SD storage, is required. Do not route 140/142 as a common always-connected recovery pair. CB1 eMMC's documented Manta flashing procedure suggests different recovery availability but does not prove all contacts of that hardware revision. The names USB2/USB3 on BTT tables can refer to numbered USB2 controllers; they must not be interpreted as 5 Gb SuperSpeed.

CM5 supports USB host **boot** only through its additional USB3 ports, although the common 103/105 DWC2 pair supports USB2 host operation and rpiboot recovery. A thumb-drive recovery boot promised on the common pair would therefore be wrong. Pi eMMC modules can be provisioned through rpiboot; CB2 needs its Rockchip loader/OS procedure; CB1 SD boots removable storage. Compatible replacement modules should ship with their own correct image and retain the machine configuration on the independent configuration store. Storage pins 57/61/62/63/67/69 overlap, but SD power/voltage controls 73/75/76 do not form a universal wiring contract.

## Contacts excluded from the common population

| Contact(s) | Conflicting functions | Decision for common subset |
|---|---|---|
| 16 / 18 / 19 | Pi Ethernet timing / CM5 fan / BTT camera, SPDIF or PWM | Unrouted; no universal fan/LED circuit |
| 35 / 36 | Pi carrier-HAT ID GPIO / BTT GPIO or NC | Not a module auto-ID interface |
| 41 | CB2 wiki GPIO3_C4 versus manual GPIO0_C4 | Unresolved; unused |
| 76 | CM4 reserved / CM5 RTC battery / BTT SD detect | No universal battery or externally driven pull |
| 92 | CM4 RUN_PG / CM5 power button / BTT PWRON | No universal reset output from ESP |
| 94 / 96 | CM4 analog / CM5 USB-PD CC / BTT NC | Unused for the common DC-powered bay |
| 99 | Pi power-enable input / CB1 recovery / CB2 PMIC power control | No shared active reset/control driver |
| 100 | CM4 reset output / CM5 CAM_GPIO1 / BTT AP reset | No common push-pull tie or output-derived module identity |
| 104 / 106 / 111 | Pi reserved, PCIe or VBUS control / BTT analog audio, TV or GPIO | Unused |
| 128/130, 134/136, 140/142 | Pi camera or USB3 / BTT USB2, camera or microphone | Unused except a separately qualified population |
| HDMI1/MIPI/PCIe groups | Pi video/USB3 versus BTT audio/USB/camera/NC | Unused in initial common subset |
| 56/58 and 80/82 | Pi I2C GPIO and camera I2C; CB1 NC | Existing Pi I2C identity/cartridge wiring cannot establish CB1 support |

The full matrix also records all remaining NC/reserved/unused contacts. There is no claimed universal module-side I2C route for identity/cartridge/auxiliary devices here. A CB1 profile needs a separately reviewed route for those responsibilities. Extra SPI, UART, flash programming and identity circuits must be audited separately before claiming the complete compute carrier is covered.

## Power, voltage and insertion boundaries

Module input is 5 V nominal. CM5 DS-6 appendix B.3 and the transition guide retain **2.5 A module supply-design allowance**, with USB/peripheral loads additional; 400 mA idle and 900 mA operation are typical examples, not a complete supply rating. BTT manuals specify 5 V ±5% / 2 A input. These are whole-module figures, not 2 A for each of six contacts. Cost and qualify the selected upgrade envelope, fuse/eFuse, converter, cable drop, connector current, inrush and cooling separately from MC's logic-rail allowance.

Pi 84/86 and 88/90 are **outputs**: 600 mA total per voltage, 300 mA/contact. BTT manuals disagree between a 100 mA auxiliary-3.3-V headline and 200 mA table annotation; no higher current is adopted here. Do not power the FPGA or independent ESP branch from these assumed auxiliary ratings. Keep module-domain buffers/pulls inside a separately computed load allowance. Pi 3.3-V GPIO source sheets specify VIH ≥2 V, VIL ≤0.8 V, VOL ≤0.4 V and VOH at least VREF−0.4 V; maximum input leakage is 10 µA for CM4 and 3 µA at 3.3 V for CM5. These are **module-side facts**, not a completed host-buffer load/timing calculation. BTT public module tables do not establish equivalent guaranteed VIH/VOH/leakage values for the proposed path; exact SoC/bank limits remain a release gate.

Pi explicitly prohibits power on pins before the module's 5 V rail and external backfeeding when off. An independently powered FPGA/ESP must therefore use a qualified powered-off protected interface and appropriate output gating; matching nominal 3.3 V is insufficient. Module-output references/pulls must follow the module's own rails. Check externally powered USB/HDMI paths as well. No automatic ESP authority over boot/reset/motion is introduced.

The official Pi connectors changed supplier: CM4 references Hirose DF40 parts; CM5 references Amphenol 10164227-1001A1RLF at 1.5 mm stack and a distinct 4 mm option. Raspberry Pi describes compatibility with existing mating connectors, but we must freeze an exact carrier MPN/stack, mounting, keep-outs, antenna/cooling and all supported module revisions. BTT's mechanical drawings do not alone qualify an arbitrary connector purchase. Replacement remains powered-off, followed by compatibility and commissioning checks.

## Cold-start DIP selector: recommended behavior

The user has endorsed a **three-bit, labelled, retained selector**, with AUTO plus a DIP override and preinstalled supported profiles. Keep these requested codes. The electrical implementation remains a proposal; no switch, reader IC or arbitrary module GPIO is added by this audit.

| Proposed code | Expected module profile |
|---|---|
| 000 | AUTO; resolve a supported module/profile after compatible boot; outputs inhibited until checks pass |
| 001 | CM4 exact qualified SKU/revision |
| 010 | CM5 exact qualified SKU/revision |
| 011 | CB1 family; exact SD/eMMC subprofile still must be qualified and confirmed |
| 100 | CB2 exact qualified SKU/revision |
| 101 / 110 / 111 | Future/reserved; unsupported profile means no motion permission |

The service controller can report the raw stable code and expected profile through its existing bounded service interface. Keep switches in that controller's own electrical domain. They do not energize or probe module contacts, grant permission, alter electrical ratings, or identify the installed module before power. Changes while powered invalidate the selection and request a stopped service/restart sequence; they must not hot-switch pinmux, reset compute or resume motion. Reader firmware and any new power-control authority require their own reviewed implementation.

Power-off replacement flow: set AUTO or the labelled override, fit a compatible pre-imaged module, start with outputs inhibited, inspect the supported module identity/model, exact-revision record and selector, refuse a mismatch or unknown profile, select the installed profile, then run the required offline commissioning checks. A forced DIP code restricts the allowed family; it does not bypass identity, circuit or timing validation. The compatible image contains its pinmux, transport, kernel and recovery resources in advance. Loading a changed device-tree/boot configuration may require a controlled reboot. **The qualified module-swap goal is no FPGA, ESP or motherboard reflash**: they retain the stable FPGA-facing electrical/protocol interface, while the Linux module supplies its matching OS and transport. A new module with missing/wrong bootloader/kernel/OS still requires initial provisioning. Preinstalled profiles cannot manufacture driver support.

Pi ID_SC/ID_SD identify carrier accessories; CB1 lacks the matching ID_SD contact. No audited universal module EEPROM, strap or resistor code is accessible across all four modules before power. AUTO must use the supported module's actual available identity path after safe power-up; Linux device-tree text alone is an image declaration, not independent proof of physical hardware or exact revision. A wrong DIP setting must therefore be detected while machine outputs remain inhibited, and supported insertion must already be electrically safe by fixed wiring. A later adapter with dedicated passive identification contacts is a separate hardware proposal, not a feature of existing modules. Universal pre-power identification and automatic acceptance of arbitrary inserted modules are not implemented or promised by this audit.

## SD, eMMC and optional NVMe

| Audited module | SD/eMMC route | Native PCIe/NVMe route | Boot/provisioning limit |
|---|---|---|---|
| CM4 Lite | No fitted eMMC; external SD over 57/61/62/63/67/69 | PCIe 2.0 x1 available | Qualified SD circuit or correctly configured NVMe boot; Lite is a distinct population |
| CM4 with eMMC | Storage on module; external SD data signals are not the Lite interface | PCIe 2.0 x1 available | USB rpiboot provisioning; NVMe boot order can coexist with fitted eMMC |
| CM5 Lite | No fitted eMMC; external SD on the same six data/clock contacts | Official PCIe 2.0 x1; Gen3 is not officially supported | SD or configured NVMe boot; USB rpiboot service is separate from USB host boot |
| CM5 with eMMC | Storage on module | Same PCIe x1 | Compatible module image and bootloader; NVMe optional, not a prerequisite for motion |
| CB1 standard/SD (sometimes called Lite in listings) | No fitted eMMC in audited V2.2 schematic; external SD | **No native PCIe contacts** | External SD image; its separate USB0 FEL path is not the common Pi service wiring |
| CB1 eMMC | Published 32 GB eMMC variant; vendor documents SD-before-eMMC boot priority | **No established native PCIe route** | Own image/GPIO revision and eMMC/FEL procedure; full 200-contact audit still needed |
| CB2 standard | Published fitted eMMC; external SD also documented | PCIe 2.1 x1 published at the bay | Vendor NVMe Linux boot uses U-Boot first on SD/eMMC; not NVMe-only boot from reset |
| CB2 Lite / later revisions | Exact listing's fitted storage must be established | Do not inherit standard module audit automatically | Disabled until exact-revision/SKU record exists |

The [official Raspberry Pi boot-order documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#BOOT_ORDER) explicitly includes CM4 and CM5 NVMe boot. Its [compute-module provisioning documentation](https://www.raspberrypi.com/documentation/computers/compute-module.html) describes rpiboot and the mass-storage-gadget route for eMMC/NVMe. Those are supported manufacturer starting routes, not proof our custom carrier boots every SSD. SD/eMMC/NVMe selection must preserve the separate machine configuration and licence identity; a controller image backup is not itself the independent configuration cartridge.

The shared physical PCIe candidate contacts are **110/112 reference clock P/N, 116/118 module RX P/N, 122/124 module TX P/N, 102 CLKREQ# and 109 PERST#**. They are present for CM4/CM5/CB2 and **NC on CB1**. Optional storage must therefore report unavailable on CB1; a USB-storage adapter is a different peripheral path, not native NVMe. Pin 104 is reserved on CM4, wake on CM5 and line-out on CB2; pin 106 is reserved on CM4, power enable on CM5 and line-out on CB2. Do not wire those as universal M.2 wake/power control.

CM4 has reference-clock and TX AC coupling on the module; CM5 retains TX coupling but changes clock coupling, requiring a deliberately reviewed carrier population. An NVMe card normally supplies its own TX coupling; avoid duplicate or missing series capacitors. CB2's public module table does not close its coupling/3.3-V power design. Its pinned BSP sets GPIO1_B2 for reset, consistent with the pinctrl's PCIe PERST M2 function at contact 109, and lists GPIO4_B1 for a PCIe supply enable without documenting that GPIO as an exposed bay contact. Do not invent a socket power-enable pin from that device tree. Provide a separately rated, sequenced storage supply after the exact controller/profile review; module auxiliary 3.3 V is not an SSD power source.

The [BTT V3.0.2 release](https://github.com/bigtreetech/CB2/releases/tag/V3.0.2) introduced its NVMe start path in U-Boot and explicitly says RK3566 initially starts U-Boot from SD/eMMC. This is source evidence of an available route, not an observed target boot. Its installation steps change storage contents and are not run here. The CB2 manual also excludes M.2 hot insertion. Preserve power-off replacement for all storage profiles.

For the first complete prototype, pre-imaged eMMC is the simplest service baseline where the module has it; qualify the carrier SD population for Lite/CB1-SD and treat NVMe as an optional storage tier. If an M.2 connector is added, cost its 3.3-V converter/protection, reset/clock control, coupling population, 2230/2242/2280 mounting clearance, thermal load and production test. Storage traffic must be included in the loaded motion-timing test. A socket footprint alone does not establish NVMe boot or SSD compatibility.

### The cited 16/32 GB Intel Optane listing

Intel's original [16 GB](https://www.intel.com/content/www/us/en/products/sku/97544/intel-optane-memory-series-16gb-m-2-80mm-pcie-3-0-20nm-3d-xpoint/specifications.html) and [32 GB](https://www.intel.com/content/www/us/en/products/sku/99742/intel-optane-memory-series-32gb-m-2-80mm-pcie-3-0-20nm-3d-xpoint/specifications.html) Optane Memory products are **M.2 2280 PCIe 3.0 x2 NVMe storage**, with discontinued marketing status. They do not add DRAM, an NPU or AI compute to the module. The exact seller MPN is still needed to distinguish original Optane, M10 and combination H-series products; an Intel acceleration feature is not a claimed ARM-controller capability.

The original 16/32 GB pages list 3.5 W active and 1 W idle. At 3.3 V, 3.5 W corresponds to **about 1.06 A**, already above the Pi auxiliary-output 600 mA total and the disputed BTT allowance. This is a power screen, not a peak-current rating or final converter size. Neither page claims enhanced power-loss data protection. Treat an exact Optane unit as a possible bench storage candidate only after x1-link/Gen2 negotiation, NVMe enumeration, bootloader compatibility, capacity/headroom, thermal and interrupted-write checks. A Gen3 ×2 marketing bandwidth cannot be applied to a Gen2 ×1 host. Small discontinued drives are not frozen into the commercial base BOM simply because a used listing is cheap.

## Which profiles can proceed on one socket?

| Profile | Source-supported prototype route | Present release state |
|---|---|---|
| CM4, eMMC reference | Fixed common subset, pre-imaged module, rpiboot service, five-channel protected GPIO-CS path | Best first reference candidate; carrier circuit/target transport/timing not qualified |
| CM5, eMMC upgrade | Same common video/USB2/Ethernet/SPI contacts; different reset, power/cooling and RP1 driver | Same-socket common-subset candidate; qualify independently before customer upgrade |
| CB2 | Same selected clock/data/CS contacts by official table + proper BSP; shared HDMI0/USB2/Gigabit route | Keep active bench candidate; exact revision GPIO ratings/recovery/carrier and PREEMPT_RT/CNC3 qualification pending |
| CB1 SD V2.2 | Selected motion SPI/HDMI/USB2-host subset; 100 Mb Ethernet; removable SD route | Reduced-function experiment; shared Pi native-CS/OTG/I2C design must stay disabled; complete intended carrier not qualified |
| CB1 eMMC / CB2 Lite or undocumented revisions | Separate exact hardware source required | Disabled until pin/power/boot differences are documented and qualified |

No current custom-socket assembly is authorized as electrically safe by this source report alone. CM4/CM5 have a demonstrated manufacturer cross-carrier precedent and no fundamental conflict in the *selected* contact functions; they are the strongest common-subset prototype order. CB2 remains deliberately supported as a qualification target. CB1 can stay in the comparison without falsely inheriting Pi recovery and identity circuits. **Every physical machine-use profile remains disabled until its circuit, target build, actual FPGA exchange, loaded real-time and fault-response checks pass.**

The next concrete source change is a new common-subset compute-carrier circuit with explicit five-channel domain protection, host/service USB selection and rated SBC power, followed by exact-revision electrical review. Add selector metadata and preinstalled profile handling through the same service/CLI/UI contract. Keep current MC circuit/route receipts and the frozen shared specification intact; coordinate any affected interface proposal with the logic owner. No supplier upload, order, fabrication export or manufacture-readiness claim follows from this audit.

## Source discrepancies retained

CB2 pin 41 is unresolved between its official wiki and pinned manual. The manual's pin 102 signal wraps around the row in PDF extraction; it is normalized as PCIE20_CLKREQn_M2, not the isolated suffix “2.” CB2's table also repeats a local connector number near ground contact 198; global numbering remains complete. CB1 manual GPIO versus function aliases (e.g. PH5/SYS-LED and PI16/SDC0-DET) remain in both columns.

An archived BTT build file named `rk3566-bigtreetech-cb2.dts` declares the model/compatible of **OPi 3B**, so it is explicitly rejected as CB2 pin evidence. The actual pinned `bigtreetech/linux-rockchip` CB2 source is used. This source discrepancy is not a measured defect in CB2 hardware or a reason to remove it from the shortlist.
