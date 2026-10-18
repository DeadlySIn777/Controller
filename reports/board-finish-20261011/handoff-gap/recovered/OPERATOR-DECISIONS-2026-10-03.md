# ROOT104 operator decisions (2026-10-03)

The operator pasted these decisions in answer to the three open questions. They replace the
corresponding Claude-delegated defaults in every stream's DECISIONS.md.

1. **Via-in-pad.** Use filled and capped VIPPO for the 291 intentional vias inside SMD pads:
   resin fill, planarized, copper cap, written into the fab notes. Specify it for those
   locations only; ordinary vias stay as they are. Move those vias only if the fab quote or
   process limits require it.
2. **Isolation domains.** The 417 sub-island hits inside one functional isolated channel are
   NOT separate isolation domains. Group same-side functional subnets under their parent
   isolated domain, and enforce cross-domain clearance only across a real galvanic boundary.
   Document every exemption, so that unrelated isolated domains cannot merge by accident.
3. **Clearance.** Keep isolation checking on all copper layers.
   - Ordinary separated 24 V domains: 0.6 mm minimum.
   - True galvanic barriers (isolated DC/DCs, digital isolators): derive clearance and
     creepage from working voltage, insulation class and component/fab data, and raise the
     rule where required.
   - Never relax a true isolation boundary just to make routing easier.

## Scope expansion (operator, 2026-10-03 ~12:40: "it needs to be perfect", "do all manual")
Route everything, including the categories earlier treated as manual: BGA escapes, impedance-controlled
pairs, analog chains, and the long STEP/encoder/AO lines. Where a spec is missing, take the
conservative engineering choice in a Claude-authored draft spec and record it.
- Long lines: roadmap Q13 option (b), route as controlled lines without moving parts.
- Impedance geometry: computed from the board stackup by two independent methods and marked as
  pending fab field-solver confirmation.
- Never move parts. Never change pre-ROOT104 copper; additions only.
- A five-lens audit (DRC/manufacturing, isolation, return/signal integrity, power, completeness)
  with fix loops must come back clean before anything is called done.

## Final authority and definition of done (operator, 2026-10-03 ~12:50)
Finish ROOT104 completely. Everything is in scope, and nothing is deferred just because it
used to need manual routing.
- **Changes beyond additions.** Targeted component moves and rerouting of existing copper are
  allowed when an audit proves the current geometry prevents a correct result. Preserve
  validated work where possible, but correctness wins. Record every change and re-run the
  affected validations.
- **Gates.** Every promoted change passes the KiCad and project gates.

Done means all of the following:
1. 0 required missing joins.
2. 0 unresolved DRC violations.
3. All isolation-domain rules satisfied.
4. All return-path checks satisfied.
5. Power width, current and IR-drop checks satisfied.
6. BGA fan-out complete.
7. Controlled pairs routed, with provisional geometry clearly marked until the fab confirms the stackup.
8. Analog routing reviewed for return paths, noise and separation.
9. No drill/SMD-land issue unless covered by the VIPPO process.
10. Zone refill leaves no unintended islands or severed planes.
11. All critical and safety nets independently checked.
12. Silkscreen, courtyard and mechanical review done.
13. Gerbers, drills, BOM, CPL and assembly drawings generated.
14. Final manufacturing audit passes.

**Impedance-controlled nets:** route provisional geometry from the current stackup and mark the
final width/gap as pending the manufacturer's field-solver confirmation. Never claim a
production-qualified impedance.

**Final reviews:** after zero missing joins, run five independent reviews:
1. DRC/manufacturability
2. Isolation/creepage/clearance
3. Signal and return-path integrity
4. Power/current/IR-drop/thermal
5. Completeness against the frozen controller requirements

Any failure triggers a repair round and full revalidation, repeated until all five pass.

**Reporting:** no routine progress reports. Stop only for decisions that need a fabricator
choice, a physical measurement, or a change to product requirements. The next report is either
`ROOT104 ROUTING COMPLETE` or a short list of genuine external blockers with exact locations
and reasons.

## Controlled-impedance process (operator, 2026-10-03 ~13:10; supersedes the diffpairs tier spec where they differ)
- Fabricator: PCBWay, 6-layer, 1.6 mm. Their production stackup and recommended width/gap will
  be requested BEFORE the final controlled-pair geometry is locked. Their online calculator is
  approximate; PCBWay calculates final values and compensates for process.
- Required impedance comes from each interface's own datasheet/specification (driver, receiver,
  cable), NOT from a net looking differential. Candidates: USB 90 ohm differential; CAN (120 ohm
  cable system; PCB pair per transceiver guidance); RS-485 per transceiver; fast single-ended
  lines at 50 ohm only where warranted; encoder differential at 100 ohm only if the interface
  requires it; HDMI/MDI 100 ohm differential. Each assignment cites the datasheet line used.
- Routing is PARAMETRIC: controlled nets are assigned to net classes IMP_50, DIFF_90, DIFF_100
  (more only if an interface needs it). Width/gap live ONLY in those classes and in custom
  .kicad_dru rules keyed on them. The router reads geometry from the classes, never hard-codes it.
  When PCBWay returns numbers, update the classes and reroute/tune only those nets, then rerun
  the audits.
- Until confirmation: provisional width/gap from the current board stackup by two independent
  formulas. Continuous reference plane under every controlled net (no splits/voids/anchored-piece
  boundaries); length match and skew targets per interface. Mark everything
  "PROVISIONAL — FAB STACKUP CONFIRMATION REQUIRED".
- Fab notes request impedance control/testing and coupons if PCBWay requires or recommends them.
- The PCBWay request package and the controlled-net list are built under Z:/pcb-runs/impedance/
  (read it before routing any controlled net). Sending the request is the operator's action.

## Board size: placement-density study before final routing (operator, 2026-10-03 ~16:30)
- The current 460 x 340 mm outline is provisional and too large. Before final routing, optimize
  placement to minimize board area and internal route length.
- Target about 320 x 240 mm; 350 x 250 mm is a soft upper bound unless analysis proves more area
  is electrically or mechanically necessary.
- Preserve electrical architecture, isolation requirements (creepage/clearance never degraded),
  connector usability, thermal requirements and serviceability.
- Placement priorities:
  - perimeter field connectors stay accessible;
  - motor interface circuitry next to its connectors;
  - encoder receivers next to encoder connectors;
  - analog circuitry next to analog terminals;
  - switching regulators close to their loads;
  - FPGA support circuitry compact around the FPGA;
  - short compute-to-FPGA paths;
  - true isolation barriers preserved;
  - plane integrity and thermal copper;
  - compute and ESP modules physically replaceable.
- Evaluate 350x250, 330x250 and 320x240 mm. For each, report component density, the longest
  STEP/DIR, encoder and analog runs, estimated routing congestion and area reduction BEFORE
  committing.
- Pick the smallest candidate that keeps good routing channels, thermal performance, isolation
  and terminal access. Do not optimize purely for size.
- Moving parts is explicitly allowed for this.
- Routing on 460 x 340 is paused until the outline decision.
- UPDATE (operator, ~16:40): "it really needs to be a lot smaller, 4090-sized max".
  - New ceiling: RTX 4090 Founders Edition footprint, about 304 x 137 mm (~41,600 mm², 27 % of
    today's area).
  - Evaluate 304x137 as a single board, as dense double-sided placement, and as a two-board stack
    (main + mezzanine) in that footprint. Report 336x140 (large partner-card length) and 320x240
    for reference only.
  - If 304x137 is infeasible, say exactly which constraint breaks (connector perimeter, area,
    isolation, thermal) and the smallest relaxation that works.
- OPERATOR PREFERENCE (~17:05, "2"): variant 2 — ONE board, dense double-sided placement, inside
  304 x 137 mm. Evaluate it first and most thoroughly; still report the single-sided and
  two-board-stack variants for comparison.
  Double-sided rules:
  - Only SMT parts on the bottom side; through-hole parts and connectors stay on the top.
  - Bottom-side parts must survive a second reflow: no heavy or tall parts there (state a mass
    or height limit you assume).
  - Isolation clearance applies on the bottom side too; creepage across the board edge or
    through slots is counted.
  - Hot parts get thermal-via relief to the planes.
  - Allow F/B flips only for SMT-only blocks; record every flipped block.
- ARCHITECTURE DECISION (operator, ~17:20; supersedes the variant preference above): ONE BOARD,
  DENSER TERMINALS, parts on both sides. Today's 45 edge parts need about 1,486 mm of edge;
  connectors and module sockets are 38 % of the part area.
  - Replace field terminals with denser pluggable terminals: double-deck (two-level) blocks
    and/or 3.5/3.81 mm pitch.
  - Every replacement must keep, per terminal:
    - the current rating (worst-case continuous current from design.json/datasheets, with
      derating);
    - the wire range;
    - the working voltage and the clearance/creepage between adjacent terminals (the galvanic
      0.6 mm rule and the barrier requirements);
    - pin count and order;
    - field-wiring access.
  - Keep each RJ45/USB/HDMI/microSD/power-entry part unless a denser equivalent is clearly
    better.
  - Find the SMALLEST legal single board: evaluate about 300x230, 270x200 and 250x180 mm, plus
    304x137 as a stretch.
- AUTO-COMMIT (operator, ~18:45): when the placement study finishes, commit the outline it
  recommends without waiting. That outline is the smallest legal one; use its confirmed legal
  metrics, and if the verification flagged it, fall back to the smallest confirmed-legal one.
  Build ROOT105 from it, then route it to completion with the parallel lanes and run the five
  final reviews.

## Conditions on automation

## Conditions on automation
- Fix the four routing-loop defects before trusting automatic promotion (see
  `Z:/pcb-runs/loop/tests/unit/README.md` and `DEFECTS-census.md`).
- A candidate cannot pass if the no-net-loses-a-join gate is vacuous (see
  `critical/tools/post_gates_critical.py`, which reads a key the inventory never writes) or if
  the zone/fill gates are bypassed.
- Continue P1–P5 and keep routing and merging candidates that pass the gates, until only the
  genuinely manual nets remain: BGA, impedance-controlled, analog and placement-sensitive.

## Board size FINAL (operator, 2026-10-03 23:20): 365 x 280 mm
The user picked option A: keep ROOT105 as built.
- 365 x 280 mm, 102,195 mm², 34.7 % smaller than ROOT104.
- Rigid blocks with their copper kept, F2 dense terminals, no waivers.
- B-ROOT105-01 is closed. Route ROOT105 to completion with the lanes, then run the five final reviews.
- The smaller re-laid-block options and the 4090 two-board stack were declined for now.

## Rule decisions (operator, 2026-10-04 ~01:20, chosen in chat; each resolves a relayout blocker)
1. **B-ROOT105-SIGB-01, LOGIC vias: allow the ledgered neck.** The zone census treats the In2 /IO_3V3 neck that
   disappears between a LEDGERED new signal via and its LEDGERED return stitch as intended. Bounds:
   - only inside the convex hull of that via+stitch pair grown by 0.2 mm;
   - at most 0.005 mm2 of loss per pair;
   - no zone piece may split (piece count and connectivity unchanged);
   - any loss outside the bound, or beyond it, still fails;
   - the router's one-pair-per-zone budget is lifted only under the same bounds.
2. **B-SIGA-01, through-hole pin endpoints: bounded pin exception.** The return gate treats the net's OWN plated
   through-hole pin at a segment end like its own new via. Bounds:
   - only the segment that terminates on that pin;
   - only inside that pin's own antipad (plane clearance hole) plus the same margin the via exception uses;
   - only where the surrounding reference fill is SOURCE-anchored;
   - another net's pin, a non-terminal segment, or any corridor outside that antipad is checked as before.
3. **B-ISO-01, USB-C shell J15006: accept the part exemption.** Keep the GCT USB4105-GF-A land pattern. The 0.32 mm
   between the CHASSIS shell stakes and its own LOGIC_GND lands is accepted for J15006 only (component-only exemption,
   own pads only), because 0.32 mm meets the derived 0.2 mm functional-insulation requirement (barriers.json). The 0.6 mm
   rule stays everywhere else.

## Coordinator decision 2026-10-04 ~02:25: SBC_5V IR drop (B-PWRB-01), under the operator's copper-change authority
Claude-authored, reversible. The operator granted authority for controlled reroutes and copper changes when an audit
proves them necessary, and asked for a conservative draft spec wherever a spec is missing.
- DRAFT budget: SBC_5V drop from U11012's output to J15001's SBC pins <= 100 mV at 3.6 A (2 % of 5 V).
- Fix: option (c), a dedicated SBC_5V copper pour (zone) from U11012 pins 8-10 to J15001 pins 77-87.
  - It goes on an outer layer, or on In3 outside the CORE_1V2 region, wherever gates allow.
  - It may use parallel F.Cu/B.Cu pours joined by via arrays of >= 5 vias per transition.
  - Width is sized by IR calculation: about 8 mm x 150 mm of 1 oz gives about 0.011 ohm, i.e. about 40 mV at 3.6 A.
  - It must never cut a reference plane (In1/In4) or cross a galvanic barrier.
- The 1.8 mm trunk stays as the fallback until the pour candidate passes every gate plus a return and IR audit.

## Coordinator decisions 2026-10-04 ~06:40 (under the operator's controlled-change authority; reversible)
1. RS485_COM reference: the RS-485 pair's reference is 4 disjoint pieces (gaps 35.5 mm and 120.8 mm). Fix with the
   smallest change that makes it continuous along the pair. First choice: extend the RS485_COM zone along the pair
   corridor on In1/In4, inside the RS-485 isolated domain, with every barrier clearance kept. Fallback: move the
   transceiver block toward its connector. CHANGE-MODE gates; ledger in CHANGES.json.
2. Pair reference islands (In4: U6003 escape region vs JD03 region; In3: the 69 mm2 R7013 island under FREQ0/1).
   Make each controlled pair's reference continuous with ledgered zone changes (bridges/merges of same-net reference
   pieces) or a reroute onto a continuous reference. Never cut a different domain's plane or cross a barrier.
3. Census-states: zone a1b60087 (MOTION_5V_RAW, F.Cu) refills chaotically on R1-pwra-2. Add its measured states to the
   pinned census-states library with the existing method (20+ base refills, admit only hairline-scale XOR).
   Router-maintenance lane.
4. Impedance classes: install the parametric IMP_50/DIFF_90/DIFF_100/DIFF_120 net classes and impedance-rules.kicad_dru
   into the chain's project files (review finding R-003), marked PROVISIONAL. Done by the merge, so every lane sees them.

## Rule decisions D4-D5 (operator, 2026-10-04 ~06:45, chosen in chat)
- **D4 dense fan-out return rule.** Applies ONLY inside the courtyards of U1001 (Efinix T20F256 FPGA, 0.8 mm BGA) and
  of J15001/J15002 (compute-module connectors).
  - A new signal via's return requirement is met by an existing or new via of that SAME part's own /LOGIC_GND
    ball/pin within 1.2 mm centre-to-centre, provided that via connects to the SOURCE-anchored In1/In4 reference.
  - Via-to-via spacing there follows the board DRC clearances (standard dog-bone grid) instead of the 0.8 mm
    project rule.
  - Everywhere else the 0.90-1.0 mm stitch window and the 0.8 mm via spacing are unchanged.
  - Every use is accounted per via (rule_decisions_applied.D4).
- **D5 FPGA escape layers.** B.Cu first: cut ledgered routing channels into the B.Cu /LOGIC_GND pour under and
  around U1001. In1/In4 stay intact.
  - Only if the B.Cu channels are measured insufficient: shrink the In3 /CORE_1V2 region to the core-supply balls
    and their decoupling, then route In3 channels outside it. CORE_1V2 must still feed every consumer pad within its
    IR-drop budget.
  - Every zone edit is ledgered (zone uuid, before/after outline) and gated in CHANGE-MODE. The census excuses only
    the copper inside the ledgered cut regions. No plane piece may be left isolated.
