# Controller status indicators

30 September 2026. Explicit user direction for the motherboard/front panel. This records required behavior; the LEDs, drivers, fault overrides and front-panel mechanics are not yet in the fitted 327-part motion-card candidate. It does not freeze a GPIO allocation or add machine capabilities.

| Label | Indicator | Reported scope |
|---|---|---|
| SYSTEM | Ordinary RGB | Whole-controller health, with a candidate front-panel light pipe |
| COMPUTE | Ordinary RGB | Selected/detected compute module and host startup/provisioning state |
| FPGA | Ordinary RGB | Configuration, gateware compatibility and actual endpoint state |
| ESP | Ordinary RGB | Service/helper availability and approved service activity |
| MOTION | Ordinary RGB | Motion subsystem state; ready is not automatic motion authorization |
| EXPANSION | Ordinary RGB | Required expansion presence, identity, power and compatibility |
| NETWORK | Ordinary RGB | Actual link/provisioning/service state; offline machining remains supported |
| IN1–IN24 | Single-color | Actual qualified input state |
| OUT1–OUT16 | Single-color | Actual observed output state, not merely the requested software value |
| M1–M12 ALM | Single-color | Actual drive-alarm input state for each present channel |
| WDT | Independent fault indication | Watchdog trip/inhibit evidence, available without Linux |

Use consistent front-panel one-based labels and an explicit map to internal zero-based signal names (IN1→DI0, OUT1→DO0, M1→motor0). Missing/unfitted expansion channels must be visibly identified as unavailable; an unlit absent channel is not evidence of no alarm. Do not add RGB to every field channel. The seven RGB and 52 single-channel indicators require 73 LED emitter paths before the separate WDT indicator; they do not require 73 FPGA GPIOs. Driver allocation and real supply current belong in the full pin/power/BOM accounting.

| RGB pattern | Meaning |
|---|---|
| Solid green | Ready/healthy within the indicated subsystem's qualified scope |
| Pulsing green | Normal operation |
| Yellow | Attention or incomplete setup |
| Red | Fault |
| Blue | Provisioning, approved update or configuration |
| Cyan | Connected/service activity |
| White | Boot/self-test |
| Purple | Service/recovery |

Print durable labels beside the indicators. The screen, CLI and exported diagnostics explain the same subsystem state with a stable fault code and actual measured/observed facts, validity and age. Color must not be the only distinction: retain readable labels and text and qualify blink/pulse patterns for accessibility and workshop visibility. Example progress percentages must come from a real bounded operation; do not display invented installation progress, module detection or compatibility ticks.

## Electrical and ownership rules

Use ordinary independently controlled RGB emitters for these status positions. An addressable WS2812-style chain is not the only critical indication. A noncritical LED driver can reduce host/FPGA pins; its serial traffic stays off the precision motion transport. Choose exact LED/driver orderable parts, resistor/current limits, thermal/loading behavior and connector/light-pipe geometry before layout freeze.

Independent hardware rail/reset/watchdog/permission faults should force red on the relevant powered critical indicators where practical and suppress green/other normal patterns. This override cannot depend on Linux, a running ESP application or an LED animation task. Review the actual priority circuit so a fault cannot combine red plus green into a misleading yellow. Define indication when the fault-override or LED supply is itself unpowered: darkness is not a safe/healthy claim. A LED is diagnostic evidence, not the output inhibit or a safety function.

Input/alarm LEDs must reflect the protected, qualified receive path without materially loading or bypassing it. Output indication must distinguish command, driver/readback state and valid load measurements where the selected stage supports them; one LED cannot claim current flow from a command bit. Loss of feedback makes status unavailable and the group indication fault/attention as appropriate. Preserve field isolation, return paths and creepage: no indicator wire bridges a galvanic barrier merely to reach a panel.

Loss/staleness of software status must remove a healthy animation rather than freeze a green claim. Physical tests must cover host crash, stopped service/FPGA reporting, watchdog/rail trips, absent and wrong expansion identity, partial power, shorted LED/driver, daylight readability and simultaneous full-brightness power/thermal load. Include their fitted cost and standby/max current in the complete controller model. The user's examples describe desired UX, not implemented provisioning or fault-detection evidence.
