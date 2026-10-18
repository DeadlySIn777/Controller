# Compute and CORE power review, 30 September 2026

This review requires a bounded CORE converter correction. It does not qualify a manufactured board. Compute r05 remains **191 physical parts / 183 purchased parts / eight bare test pads**, unchanged. Twenty exact input files are copied and hashed here; the parent snapshot has **2,359 physical footprints**. The separately reviewed status source has 290 parts and is not present in that parent snapshot. Do not describe this inventory as the latest complete parent or transfer the old 1,394-part current calculation to it.

## Normal operation and faults are different

The reproduced [calculation](audit.py) and [results](power-capacity-review.json) separate normal allocations, startup and fault limits. The CM5 **2.5 A manufacturer supply-design allowance** is retained; its 900 mA consumption row is typical and cannot replace that allowance. External module AUX consumption is excluded from the quoted module-current table and is counted upstream separately. USB/HDMI power is supplied directly from SBC_5V and does not travel through the module's six 5 V contacts.

| Existing required load | Normal design allocation used | Qualification remaining |
| --- | ---: | --- |
| CM5 | 2.5 A at module 5 V input | Actual selected variant/workload, socket IR/temperature, startup |
| Module AUX | 0.287 A at 3.3 V | 0.250 A SD branch plus 0.037 A other reservation; exact card maximum/startup not qualified |
| USB bank | 0.350 A including 5 mA bleed | About 0.345 A external; profile/descriptor enforcement not implemented; no guaranteed 500 mA service |
| HDMI | 55 mA source plus 50 µA conditional IC row | Running quiescent and profile/panel power; display has its own PSU |
| IO3 | Compare 1.2 A and full existing 2 A regulator envelope | Native power-pin inventory is included; full mixed static/dynamic FPGA and peripheral current still needs reconciliation |
| FPGA core | 0.8 A at 1.25 V | Inherited reservation, not Efinity power proof |
| Purchased ESP board | 0.7 A at CORE5 | Actual board/LDO/startup/loaded service current |
| Status | 0.55 A at CORE5 | Planning screen; TLC59116F ICC is typical-only and TTL transition conditions do not give a full maximum |
| Loaded RS-485/CAN | 0.341 A at CORE5 | Primary loaded-bus rows; source/rate/termination profile applies |

Conversion uses an explicit **85% efficiency screen**, not a guaranteed lower bound. The 1.2 A IO3 case gives **5.97826 A CORE5**, only 21.74 mA below the existing 6 A rating before unresolved loads. Reserving the actual 2 A IO3 converter envelope gives **6.63708 A**, exceeding 6 A by 0.63708 A. These are legitimate normal design-envelope calculations. They justify correcting the source; they do not prove a maximum for every consumer.

The separate all-short SBC screen is 3.58484 A using SD/AUX, USB and HDMI protection maxima. It is **not** a promised normal operating requirement. During real overloads, safe shutdown/inhibit is acceptable. The design must still survive the exact current, thermal, transient and restart conditions. Recovery cannot automatically rearm motion or field outputs.

## Bounded CORE source correction

Use the existing CORE converter region with **LM706A0RRXR** in place of LM70660RRXR, a reviewed **5 mΩ Kelvin shunt**, **XAL1010-472MED 4.7 µH** candidate and one additional **16SVPG330M 330 µF** output capacitor. The proposed continuous board envelope is **7 A**, not the silicon's full 10 A. MOTION5 is unchanged. The source owner must select the exact shunt MPN, verify the new coil footprint and native pin map, and reconcile the actual compensation/input capacitor/ripple/layout facts before adoption.

[TI SNVSCD4](https://www.ti.com/lit/ds/symlink/lm70660.pdf) uses the same RRX package/pin map for both devices. Its 8 A application explicitly uses 5 mΩ (Figure 7-12, document page 33; current-sense selection on page 35). The table's nominal 4 mΩ entry is not a universal requirement for every bounded application. The current-limit threshold is 50–62 mV; the short-circuit delay has no guaranteed maximum. External compensation is present on the actual board.

The inherited conservative screen uses L = 2.632–5.64 µH, fs ≥ 398 kHz, 5.05 V, shunt ±2% and protected VIN ≤ 30 V normally. At **7 A**, peak current is 9.00466 A against a minimum-limit screen of 9.80392 A. At **8 A**, that margin is already negative. Therefore the proposed components must not earn an 8 A/10 A continuous claim simply because the regulator is rated 10 A.

Four bulk parts plus the three existing ceramic effective values give **906.3 µF minimum**, with a conditional 3.9167 mΩ ESR budget. A 7 A load release gives 5.11973 V using a phase-correlated energy corner and 5.13498 V using a stronger noncorrelated screen, both below the inherited 5.15 V ceiling. The old three-capacitor stronger screen is 5.15975 V. These are energy/ESR calculations, not a control-loop simulation or measurement. The existing 9.53 kΩ/22 nF/330 pF compensation has a nominal calculated crossover about 6.426 kHz at the four-cap minimum; actual gain/phase/ramp stability remains a required engineering and physical check.

[Coilcraft Document 804, revised 25 February 2026](https://www.coilcraft.com/getmedia/dd74e670-e705-456a-9a69-585fe02eaf3c/xal1010.pdf) gives the candidate 4.7 µH part 5.7 mΩ maximum DCR at the specified condition, 25.4 A typical 30%-drop saturation current and 17.5 A reference current for 20°C rise. Those are not guaranteed hot L/Isat limits. Its land pattern changes; the old XAL7070 footprint cannot be reused. Maximum CS threshold plus a **75 ns typical**, not maximum, delay gives about 14.36 A at the 60 V transient screen. Hot saturation and fault heating need actual qualification, without treating a typical value as a guaranteed bound.

## Protected 24 V source

CORE5 and MOTION5 share protected C24 with the independently powered analog converters. They are counted as separate loads; analog converter input must not also appear under CORE5. The actual source has four 1 W TMR1 converters plus one 3.5 W RECOM, all directly on protected C24: 7.5 W summed output capacity. Reserving that capacity at 80% efficiency yields about **3.57524 A** total at a provisional 17.7 V protected input, compared with a 4.083 A resistor-drift screen from the eFuse's 4.185 A testpoint minimum. **The isolated supplies are being corrected by their owner; rerun this input budget with the replacements and preserved load allocations before freeze.** The nominal eFuse tolerance cannot silently become a guarantee at every resistor/temperature/testpoint.

The actual analog 18–36 V-input modules cannot satisfy an external 18 V input after entry losses. This is a **source violation to repair**, not a physical-test-only exception. The analog source owner is reviewing exact wide-input converters while preserving outputs, limits, isolation, returns and pin/land checks. The product's 18 V minimum is not changed here. Source folding, wiring, fuse/TVS coordination and actual eFuse/converter temperature still need quantified checks.

## Compute connector evidence

The actual sockets are **Amphenol 10164227-1001A1RLF**, the same exact MPN named in the official CM5 IO schematic. The [manufacturer complete-pair specification GS-12-1404 Rev E](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/gs-12-1404.pdf) covers 10164227/10164228 and related pairs. Its 0.3 A rating is tested with all contacts carrying current simultaneously. This blanket test alone gives 1.8 A for six contacts; it does not publish a selective-contact thermal rating.

The [official CM5 datasheet](https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf), Appendix B.1.2, separately states that the new connector brand was tested at higher currents for CM5, and recommends the CM5 IO design as the carrier starting point. Consequently it is incorrect to declare the official identical pair categorically incapable of the CM5 design allowance. It is equally incorrect to claim an unpublished high-current/temperature/auxiliary envelope. Preserve the exact reference pair and prove carrier/module IR drop and temperature for the supported load. No verified higher-current same-mating Hirose substitution was found; DF40HC examined is also 0.3 A and changes stacking height.

CM5 3.3 V AUX is limited to 600 mA total / 300 mA per contact. The two AUX contacts and the upstream module power are both accounted for. Those Pi limits do not establish CB1/CB2 AUX capability. BTT profiles remain electrically and target-software unqualified.

## SD supply candidate: not adopted

The actual SD switch IN remains CM_AUX_3V3. Changing only that pin to IO_3V3 was inspected but not adopted. TPS2553's independent EN voltage/leakage ratings support a low default when the module is off, but they do not prove the SD mux's full functional/ramp behavior.

The [TS3A27518E Rev F](https://www.ti.com/lit/ds/symlink/ts3a27518e.pdf) recommended analog signal range really is **0–3.6 V** at 3–3.6 V supply. A card HIGH above a valid module-AUX voltage is therefore not evidence of damage. However, §8.1 describes transmission up to VCC and guaranteed RON is specified for VIN ≤ VCC. Independently powered card-HIGH versus lower mux VCC has no established functional transmission/ramp guarantee here. Ioff applies at VCC = 0, not all intermediate supply levels. Moving mux VCC to IO3 reverses the same module-driven-HIGH question. This is a bounded unqualified functional candidate, not an impossible or damaging topology claim.

No normal-capacity proof is claimed for arbitrary consumer SD cards. An ordinary supported-card profile needs published or measured maximum/startup current at the actual 3.3 V/50 MHz mode, and a compatibility list. Typical-current catalogue entries and an unrelated high-speed 1.8 V mode cannot be substituted for that evidence.

## Evidence and next adoption step

This folder contains source inspection, manufacturer review, exact native power-pin inventory and reproducible calculations. It contains **no source/PCB mutation, no new firmware image, no vendor FPGA power estimate, no circuit transient model and no physical measurement**. The native compute r05 ERC and its 54 disconnected mutation tests remain the exact earlier scope. The required next step is the source owner's bounded CORE and analog supply corrections, native validation and a refreshed complete source budget. Cold-boot/reset overlap, actual module/capacitor startup, source loss/temperature, regulator stability and supported-media behavior then require physical prototype validation.
