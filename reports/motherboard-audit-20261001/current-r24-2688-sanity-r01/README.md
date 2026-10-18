# Current motherboard population sanity pass

2688 physical footprints: 2642 purchased fitted, 44 bare PCB geometry, 2 DNP.

| Function | Footprints | Purchased | Bare | DNP |
|---|---:|---:|---:|---:|
| 12 motor interfaces | 350 | 350 | 0 | 0 |
| 24 digital inputs | 120 | 120 | 0 | 0 |
| 16 smart outputs | 110 | 110 | 0 | 0 |
| Encoder / fast inputs | 28 | 26 | 0 | 2 |
| Rail regulation / receiving-rail monitoring | 117 | 117 | 0 | 0 |
| FPGA / configuration / clock | 70 | 70 | 0 | 0 |
| Watchdog / permission | 91 | 91 | 0 | 0 |
| I/O acquisition / control | 103 | 85 | 18 | 0 |
| Probe / pendant / port power | 198 | 198 | 0 | 0 |
| Power entry / distribution | 221 | 221 | 0 | 0 |
| Process / accessory acquisition | 119 | 113 | 6 | 0 |
| Analog / communications | 403 | 403 | 0 | 0 |
| Indicators | 290 | 290 | 0 | 0 |
| Isolated sensor power / acquisition | 176 | 175 | 1 | 0 |
| Terminals / chassis coupling | 44 | 43 | 1 | 0 |
| Compute / ESP / storage sockets and support | 214 | 206 | 8 | 0 |
| Diagnostics / motherboard identity | 34 | 24 | 10 | 0 |

2132 resistors/capacitors/diodes (79.32%). These are already included in the function rows.

No fitted rack connector/cage or duplicated commodity compute/ESP die appears in the actual source/BOM. The actual commodity interfaces are two CM connectors, two ESP headers and one microSD socket. Their presence does not qualify module interchange or boot.

Repeated active MPNs retain their distinct source-region, role and actual pin-net assignments in review.json. Equal MPNs do not authorize deleting distinct receiving rails, isolation domains, protection or permission logic. No rack-only fitted part has been proved removable.

Read-only source/native/BOM inspection. PCB connectivity, runtime, manufacturing and physical qualification are separate acceptance gates. Historical 880-footprint studies remain unchanged.
