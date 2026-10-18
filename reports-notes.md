
# Historical routing notes

Scope reviewed 18 October 2026. The route-s3 notes below record their 10 October candidate and tooling limits. For later source-bound work use [engineering status](reports/ENGINEERING_STATUS.md) and the [17 October continuation](reports/board-finish-20261017/README.md); these notes do not establish current routing, differential-pair qualification or manufacture readiness. [Documentation index](docs/README.md)

## Routing stage (route-s3, 10 Oct 2026 02:00; historical checkpoint)
- Fan-out strip: 153 retained tracks and 83 vias cleared from 12 connector/ESD escape bands (strip.json).
- Pairs (corridor-only policy, DRC-clean on test): 3 of 22 hops routed as coupled 100 ohm corridors
  (Ethernet pair 0 and pair 1 CM-to-magnetics, one with an inline via swap, plus one USB hop); the other
  19 hops (HDMI TMDS x4, Ethernet pairs 2/3, USB) are left single-ended to the autorouter. Class: raster
  router + kicad-cli DRC. HDMI/USB coupling therefore NOT achieved by tooling; flagged for a manual pass.
- Power pass 1 (old end-halo code): 707 hops, 321 removed by DRC clean-up; true unrouted 3865 -> 3502.
  Fixed router (no halo, width cap, legal end cells, cross-side vias, keepout exemptions, SAFE 0.2) used
  from pass 2 on. Power audit per pass: corridor-work/power-audit-N.txt (TRUNK-NECK = necked hop between
  large pads, to be reinforced or reported).
