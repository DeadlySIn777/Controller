# Touchscreen sizes and product packages

28 September 2026. **User requirement:** offer different screen levels in the 7-, 10-, 12-, 14-, 18- and 21-inch classes, with room for additional sizes. These are planned product options, not qualified display SKUs or a commitment to launch every size simultaneously. The earlier 21.5-inch reference is one large-screen option; it no longer sets the whole product's screen requirement.

## One controller platform, multiple screen packages

Keep screen size, compute capability and machine I/O capacity as separate configuration dimensions. A smaller screen must not, by itself, remove supported CNC functions. The common application, profiles, saved setups and UI/CLI service remain shared. A package can use a different compute module when measured workload and complete cost justify it; screen diagonal alone does not decide CPU or RAM requirements.

| Requested screen class | Initial layout study | Selection still required |
|---|---|---|
| 7 inch | Compact, focused task panels with a readily accessible machine view | Exact diagonal, native resolution, touch, interface, power, mounting and complete cost |
| 10 inch | Compact; expand panels when usable viewport permits | Same qualification and cost record |
| 12 inch | Medium; evaluate machine view beside active task controls | Same qualification and cost record |
| 14 inch | Medium; evaluate persistent secondary information | Same qualification and cost record |
| 18 inch | Large; evaluate simultaneous setup, status and job views | Same qualification and cost record |
| 21 inch | Large; the supplied 21.5-inch FHD monitor is one candidate | Same qualification and cost record |
| Additional sizes | Use the same responsive layout and qualification process | Add an explicit package; do not assume compatibility from diagonal |

These are nominal size classes. Actual panel dimensions, resolution, aspect ratio and orientation belong to the selected part's record. Layout groups above are starting proposals, not hard breakpoints. Use available viewport, scaling and physical touch usability to decide layout; a high-resolution 7-inch panel must not receive tiny desktop controls.

## Interface behavior across sizes

Preserve the preferred Octopus/MR-1 visual language and workflow. Adapt panel arrangement, information density and navigation instead of shrinking a large-screen layout uniformly. The exact reference UI still needs confirmation; this requirement does not claim it has been adapted already.

- Make machine selection, wiring/setup guidance, model import/placement, registration, job review/run, diagnostics and recovery reachable on every supported size. Compact screens can show these as focused panels; large screens can show more at once.
- Keep machine identity, mode, active tool/work offset, current machine state, active faults and the relevant Hold/Stop controls understandable and accessible during operation. Software controls do not replace the machine's independent emergency-stop system. Specify physical touch-target sizes and spacing during the UI audit, then verify them on real panels.
- Offer a file picker alongside drag-and-drop for touchscreen-only import. Provide touch alternatives to hover, right-click, keyboard shortcuts and any gesture unavailable on a selected touch controller.
- Check on-screen keyboard, dialogs, numeric entry, units, text scaling, model selection and long error messages. They must not obscure a required action or create ambiguous input.
- Cancel interactive jog on lost/canceled touch, control-context change or lost command freshness. Resizing, rotating, reconnecting or changing display settings must not replay commands or start motion. A screen change does not alter motor calibration, machine profiles or work offsets.
- Preserve the controller-owned local-job policy if the display/browser fails, while expiring interactive jog authority as specified by the supervisory contract. A returning UI shows actual controller state.

## Electrical and mechanical approach

Study HDMI video plus USB touch as the common display path across sizes, with an explicitly rated display supply. A compact DSI panel is an optional qualified configuration when its exact module, carrier wiring, panel and kernel support are established. An SPI display must not be assumed to consume or share the dedicated motion bus. A shared connector or a USB-C socket does not prove video, touch or power compatibility; a one-cable option needs a deliberately implemented host and display path.

Keep display connectors, cable routing and mounting sufficiently independent of the motion/I/O core to support different front panels. Cost each bezel, enclosure/bracket, cable set and power arrangement. A common controller PCB is the design objective; verify layout, signal integrity, thermal clearance and power limits before promising it fits every enclosure.

Each approved display record must identify the exact panel/monitor and revision, touch controller/firmware, native mode and orientation, display/touch interfaces and Linux support, input voltage/current/inrush, brightness and intended environment, mechanical drawings, cable retention, cooling/keep-outs and package contents. Do not apply a front-panel ingress claim to the whole enclosure.

Screen replacement is powered-off service initially. Qualification includes startup, shutdown, missing/reconnected touch, wrong coordinates/rotation, false touches, display supply faults and interference in the intended machine environment. Panel-specific failures must meet the controller's defined fault policy.

## Cost every complete package

Maintain a base-controller cost for each I/O/compute configuration and add the exact screen package. Price the display/touch electronics, any interface/backlight boards, cables, converters or PSU changes, mounting/enclosure, assembly, programming/configuration, functional test, packaging and delivered procurement costs. Do not count a panel alone as a complete touchscreen.

For each size, compare complete-monitor, open-frame assembly and separate-panel approaches where they are realistic. Use quantities **1, 10, 100 and 1,000** consistently. Hold the exact display package constant when comparing compute or I/O alternatives within that tier. Unknown costs stay unknown; do not infer unquoted volume discounts or assume price is proportional to diagonal.

The Mesa-like included-screen price remains the affordability objective. Exact currency, entry package, selling prices and margins remain open. US$249 is an illustrative comparison, not a requirement that every screen size sell at the same price. Publish each package's included hardware and price transparently.

The [existing display study](../research/DISPLAY_COST_STUDY.md) and [cost workbook/report](../research/HARDWARE_COST_COMPARISON.md) preserve earlier sourcing observations and the 21.5-inch/six-joint scenario. They do not establish costs for this new size range. No new screen price or supplier quote is claimed by this update.

The later [compute/carrier/display matrix](../research/COMPUTE_DISPLAY_MATRIX.md) now records exact source candidates for all six classes and 144 comparison cases across compute, I/O and quantity choices. It includes dated screen/module merchandise prices while keeping complete manufactured costs unknown. It is the current multi-size sourcing reference; no listed panel is qualified or selected for manufacture.

## Work and acceptance before offering a tier

1. Audit the existing UI and choose representative compact, medium and large viewport/scaling cases, including the most constrained 7-inch target. Define the minimum supported viewport and physical touch targets from the workflow study.
2. Produce responsive setup and operation prototypes with the same controller service. Check all proposed sizes in software before narrowing the launch range; do not make one-off UI forks for each diagonal.
3. Build exact display/compute/package records and complete cost comparisons. Select launch configurations from measured usability, availability, integration effort and economics.
4. On later bounded hardware prototypes, measure native-resolution graphics, representative CAD/model conversion, memory and thermal load alongside real-time behavior. Highest pixel workload and worst enclosure cooling may occur in different packages; validate both. A physically larger screen is not automatically a heavier graphics workload.
5. Demonstrate touch-only setup and operation, readable status/faults, reconnect behavior and recovery on each offered panel/host combination. Browser viewport emulation is useful early evidence, not physical touch, electrical, thermal or environmental qualification.

This update records product requirements and the validation plan. No responsive UI implementation, selected display BOM or physical screen qualification is complete here.
