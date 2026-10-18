# Global placement and routing setup review

The board needs a global routing and power/reference-plane plan before another local repair pass. The measured layout has substantial existing copper but still has long, distributed inter-block demand. The first review targets are FPGA escape, the compute connector region and the use of the inner power layer. These measurements do **not** establish that the placement is globally unroutable or that moving every component is necessary.

![Whole-board placement and routing demand](global-routability.png)

The reviewed native board is `combined-route-stage-r4/native/board.kicad_pcb`, SHA256 `ce8aa2cd5bb9c2128733618d5241a10acebdd637e4a0b5f726fea40801444c55`. Counts and discrete copper use this exact board/expected-Cu manifest. Filled-plane and physical partition measurements use the saved actual R299 native geometry/graph; stage4 changes seven zones and has no completed native AFTER qualification. The projected open count below is conditional on preserving old physical relationships and confirming staged via masks, not a fresh stage4 native ratsnest.

## What the geometry says

The outline is 450 × 235 mm (105,750 mm²). There are 2,723 footprints: 1,656 on the front and 1,067 on the back, with 9,971 native pads. Summed courtyards occupy about 38,093 mm² front and 10,081 mm² back (36.0% and 9.5% of board area). These are overlapping courtyard sums, **not** a free-routing-area calculation. They do not support a claim that the entire board is physically full.

The exact current board contains 86,456 track segments, 8,014 vias and 857 zones/rule areas. About 102.12 m of routed centreline is distributed as follows:

| Copper layer | Track segments | Routed length |
|---|---:|---:|
| F.Cu | 39,710 | 42.362 m |
| In1.Cu | 21 | 0.076 m |
| In2.Cu | 29 | 0.124 m |
| In3.Cu | 14,018 | 21.318 m |
| In4.Cu | 13 | 0.036 m |
| B.Cu | 32,665 | 38.201 m |

This is effectively three heavily used signal layers, two segmented reference layers and one split power layer. All six are declared `signal` in the native layer table; that software flag does not make all six electrically interchangeable routing channels.

The actual filled R299 In2 copper totals approximately 53,558 mm². `/IO_3V3` alone occupies 44,344 mm², followed by FIELD_GND (4,127), CORE_5V (2,503), FIELD_B_0V (1,375) and FIELD_5V (821). These are summed actual fill areas, not a union/free-space estimate. In2 is therefore **not an empty spare routing layer**. The global design must decide which power fills can be reconstructed around signal channels, then recheck supply conductance, source contacts, return paths and thermal/current budgets. Merely deleting those fills would trade opens for power failures.

## Where the remaining demand is concentrated

The actual R299 named-pad physical graph requires 1,172 minimum joins. Seven finite current-peer mergers reduce that to **1,165 conditional joins across 741 nets**. The remaining count is distributed: FPGA core 108; compute 104; motors 99; LOGIC_GND 91; general DO 84; status 66; power entry 65; analog output 64; analog input 62; operator interface 60; safety sensor 52. This is not a small set of stray endpoints.

The footprint incidence count below means the number of unresolved nets touching the footprint, including power/control/configuration; it is not a pin or airwire count:

| Footprint | Actual position, mm | Unresolved-net incidence | Review priority |
|---|---|---:|---|
| U1001, T20F256 | (161.290, 89.677), front | 148 | Escape and pin-group direction toward consumers |
| J15001, compute connector | (123.252, 168.715), front | 46 | Connector-to-peripheral routing corridors |
| J15002, compute connector | (123.252, 202.715), front | 40 | Connector-to-peripheral routing corridors |
| U14501, STM32G031 | (281.925, 90.249), back | 28 | Local control placement and crossings |
| U13001, STM32G031 | (116.386, 93.212), front | 27 | Local control placement and crossings |

A pad-centre minimum-spanning demand projection has median span 32.1 mm, 90th percentile 134.3 mm and maximum 297.5 mm. Existing route stubs can supply closer entry points, so these values are **not** predicted final route lengths. The whole-board plot nevertheless shows why choosing only short straight bridges misses most remaining work.

There are local concentrations rather than a uniformly saturated board. The busiest 20 × 20 mm via tiles contain 78 vias at x100–120/y140–160, 76 at x140–160/y80–100 and 73 at x220–240/y180–200. F.Cu routed length peaks at 359 mm per tile at x140–160/y140–160; B.Cu peaks at 440 mm at x180–200/y140–160. These are density indicators, not measured channel capacity. The FPGA fanout and compute-to-centre paths deserve detailed placement/escape review before moving unrelated perimeter interfaces.

## Constraints the global route must actually preserve

The project has 109 actual native rule areas; 94 disallow tracks directly and 95 disallow vias directly. There are 81 ISO-named areas, mounting/standoff restrictions and five TMR4WI converter areas whose unrelated-copper prohibition is applied through the custom DRU rather than the area's no-track flag. The TMR locations occupy the right-side analog region around x324–417/y31–130. Domain copper has 0.6 mm inter-domain clearance on every layer, including unflashed barrel effects. These restrictions are functional isolation and assembly constraints, not cosmetic route obstacles.

The effective ordinary track minimum is **0.20 mm**, despite the project-wide lower bound showing 0.15 mm. Exact FPGA/converter neck rules have restricted areas/nets/lengths. Default same-domain clearance is 0.15 mm; ordinary netclass via defaults are 0.60/0.30 mm. Actual vias comprise 5,984 of 0.60/0.30, 2,018 of 0.50/0.20, ten of 0.80/0.40 and two exact 0.40/0.20. General hole-to-hole and hole-clearance minima are 0.25 mm, with the existing exact USB exception; inner drill-to-copper clearance is 0.205 mm. Export/import must preserve the effective custom rules rather than routing from the looser project lower bounds alone.

The source-rooted logic-ground fill spans approximately 41,387 mm² on In1 and 46,236 mm² on In4. Its unions have 727 and 414 **two-dimensional** components; the source group connects these through other layers/barrels, so those numbers do not mean that every component is electrically floating. However, they explain why a route cannot assume an uninterrupted logic return plane through any visually empty corridor. There are also 91 conditional named-pad-group joins still required on LOGIC_GND itself. Ground completion and signal layer transitions need a common plan.

The historical relayout pipeline explicitly removed inter-unit copper for later rerouting (`Z:/pcb-runs/claude-finish/relayout/scripts/plan_refine.py`). Its `pipeline.py` stops at “DRC clean except unconnected items”. That is a clearance-clean partial-layout criterion, not evidence of global routed closure. The present native geometry and open-group distribution are consistent with substantial inter-block work still being unfinished.

## Concrete global setup changes to evaluate first

1. **Define routing corridors and layer ownership before route generation.** Keep In1/In4 as the intended domain returns; make an explicit power/corridor plan for In2. Protect required current paths and real source contacts while permitting reviewed pour reconstruction around signals. Do not present historical fill polygons as both immutable obstacles and an allegedly available signal layer.
2. **Review U1001 escape and group direction as one placement problem.** Map its 148 open-net incidences to actual destinations and reserve continuous logic-referenced channels. Move or rotate surrounding interface/control groups where that shortens crossings and opens channels; preserve the already audited ball/power mapping, real inhibit paths and local decoupling. A placement change needs a new routing/plane rebuild, not arbitrary transplantation of old track ends.
3. **Treat the two compute connectors and nearby peripherals as one corridor problem.** Their fixed mating/mechanical envelope remains a constraint. Reposition movable level translators, protection and peripherals along their net flow before filling long cross-board paths. Review the concentrated central/back routing tiles as channel bottlenecks rather than judging empty courtyard area alone.
4. **Route by electrical class, with power and returns planned first.** The 91 logic-ground joins, 20 IO_3V3 joins and 18 MOTION_5V_RAW joins cannot be completed as generic 0.20 mm signals. After a full global route, reimport to an isolated native board and measure actual joins, full source/pin parity, finite contacts, domain clearances, mask/drill/SMD manufacturing constraints, return references and current/thermal/SI budgets. A successful router session alone does not close those gates.

This review made no PCB, footprint, rule, source, archive or settings changes and launched no native refill or router. The earlier local FPGA search is frozen with zero new qualified join credit. [Measured setup](measured-setup.json) contains the compact computed counts; `global_routability_audit.py` is the read-only reproduction script.
