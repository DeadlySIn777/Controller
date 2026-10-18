# Compute carrier r03: actual HDMI0 source

The live source has 97 actual footprints: 93 purchased parts and four bare PCB test pads. Eight fitted parts extend the reviewed89 SD/host carrier. All previous89 physical MPNs, footprints and electrical pin assignments are preserved. The new port is an EDAC690-019-298-412 HDMI-A receptacle with an actual TI TPD12S016PWR companion, module-powered enable Schmitt, four100nF bypasses and a4.7k enable pulldown. This is native schematic source; its PCB placement, routing and physical qualification are unfinished.

Native KiCad ERC is zero errors, zero warnings, no ignored checks. Independent full pin/land checks pass;31 disconnected host mutation tests pass. The report does not establish target image, LinuxCNC deadline, video, current, EMC, thermal or20ms watchdog operation. Those require target/physical evidence.

## Primary electrical review

TI SLLSE96F page4 PW graphic has pin15 CLK− and pin16 CLK+, followed by17 D0−/18 D0+,20 D1−/21 D1+,22 D2−/23 D2+. The grouped pin table is not an ordering rule. The independent validator fixes this exact polarity and rejects a plus/minus table guess. Native module contacts151 CEC/153 HPD/170–190 TMDS/199 SDA/200 SCL are independently checked against the inherited primary pin matrix.

U15018 pin24 VCCA is the compute module's own AUX3V3; pin11 VCC5V is SBC_5V. Its pin13 output supplies connector pin18. LS_OE and CT_HPD require the actual supervised compute rail via U15019, an AUX-powered SN74LVC1G17 with Ioff. Its output has4.7k LOW; this avoids loading the inherited raw reset divider with a100k control pulldown. At VCC=0 the buffer's guaranteed10uA Ioff alone produces47mV at the default. The complete compound-chip input leakage during partial ramps is not guaranteed by that calculation and remains a measured power-sequence task. At powered VCC, control VIH=1.0V/VIL=.4V and the buffer's documented logic output levels provide a bounded control interface. No module-absent or hotplug timing qualification is claimed.

The compound chip's three GND contacts and HDMI signal shields retain LOGIC_GND, its manufacturer reference. All four connector metal anchors use the real CHASSIS boundary. Parent circuitry must provide the reviewed local ESD return/coupling and actual panel/PE bond; naming those nets does not implement a bond. No redundant second set of12 TVS channels was added. Pin14 is the actual non-HEAC reserved contact, explicitly NC.

TI's advertised55mA describes normal HDMI5V output service; page7 electrical table specifies actual short current100–200mA. The allocation is .070A normal/.210A fault on SBC5 plus .005A additional AUX, all planning screens rather than a comprehensive guaranteed maximum for every enabled state. Total carrier AUX allocation is .415A including protected SD. The CM5 consumption figures explicitly exclude external AUX peripherals, so this load cannot be silently included in the earlier2.5A compute figure. The prior3A SBC plan cannot serve2.5A compute+.5A USB+these loads simultaneously. Power-source closure remains required before fabrication.

## Primary mechanical review

EDAC issue5 manufacturer drawing requires19 lands at.5mm pitch, .28mm width,2.6mm length, centre y−.76mm relative to front anchors. Front anchor slots are .9×2.7mm with1.5×3.3mm lands; rear anchors x±7.25/y5.96 use .9×2.1mm holes with1.5×2.7mm lands. The official Raspberry Pi CAD had1.7mm rear holes/2.3mm lands and y−.73; these deviations were corrected from the manufacturer drawing. Independent mutations reject the old rear hole and a mirrored pin1. Connector PCB thickness allowance1.2–1.6mm accommodates the nominal1.6mm board, subject to fabrication tolerance and actual assembly. Panel exit, front overhang, card/module clearance and enclosure fitting remain actual layout work.

## Remaining work

USB host/recovery role routing, hub, purchased ports and shared power cap; actual Ethernet MagJack/protection/centre-taps; optional NVMe with separate protected CORE5-fed3V3 and qualified SSD load; parent integration and board routing/returns/chassis/power capacity; original socket selective current and complete Molex exclusion/mechanics; module-specific BSP/pinmux/SD images; physical video/SD/hotplug/partial-power/EMC/thermal/watchdog qualification. No extra custom daughterboard is introduced.
