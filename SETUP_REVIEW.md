# Setup and bulk-routing review

Local micro-repairs did not materially reduce the remaining 1,172 joins. The next routing revision needs coordinated plane/source planning, placement review and global rerouting, followed by native refill/DRC and electrical validation.

1. Assign source-connected per-domain reference regions on In1/In4 and current-sized power paths on In2. In2 is already a split power layer, not spare signal capacity. Source polygons and inherited fill caches cannot prove source-rooted current paths.
2. Review historical copper locks and bank-level placement. The actual export census has 82,946 locked copper objects; forcing all old routes to remain immutable prevents useful global rip-up. Preserve the electrical/fault contract and assess lost/new connections after a redesign.
3. Translate the real custom rules into the routing setup. The 26 project classes share nominal 0.15 mm clearance / 0.2 mm track / 0.6 mm via / 0.3 mm drill defaults. Cross-domain 0.6 mm rules, plated-barrel isolation and scoped exceptions live in the `.kicad_dru`; nominal defaults do not qualify domain isolation or current capacity.
4. Review the 109 keepout areas (107 board-level plus two footprint areas), high-density banks, escape paths and layer transitions. Hard safety/isolation constraints remain; optional host planning margins need separate justification.
5. Reconcile the stackup with a real manufacturer stackup: nominal six 35 µm copper layers plus dielectric/masks total 1.55 mm, while board general thickness is 1.6 mm. This affects impedance/current/thermal qualification.
6. Run the global router on an isolated candidate. Re-import results, refill all zones, compare physical connectivity, run full native DRC/parity and check source/current/return paths. Freerouting completion alone is insufficient.

These findings identify setup obstacles; they do not establish that the present placement is globally routable or impossible. No global routing completion or manufacturing readiness is claimed.
