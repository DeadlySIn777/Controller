# Requirements and evidence register

27 September 2026. The user wants a shippable controller whose setup and operation feel as seamless as the existing Octopus/MR-1 UI. “Shame the rest” is translated here into measurable outcomes, not an unverified superiority claim. Hardware purchasing is outside this stage.

## Product acceptance targets

Read this original register alongside the [latest engineering status](../reports/ENGINEERING_STATUS.md) for subsequent implementation evidence and the [platform roadmap](PLATFORM_ROADMAP.md) for the later 200-feature/module/compute requirements. The eight-motor proposal is separate from the implemented six-channel reference; no existing result qualifies the expanded hardware.

Targets below are proposals for engineering and usability trials, not achieved results or approved machine specifications.

| ID | Requirement | Acceptance evidence | Current state |
|---|---|---|---|
| UX-01 | Preserve the existing MR-1/Octopus UI foundation | User-confirmed source/build reference and visual comparison | Exact reference awaiting confirmation; candidate sources located read-only |
| UX-02 | Import a supported machine bundle without hand editing | Fresh install loads geometry, kinematics and capabilities; no code or configuration-file edits | Product contract drafted |
| UX-03 | Drop a plate, vise or stock model into the setup | Correct units/scale; guided ambiguity resolution; face-based placement and fixture anchors | Manifest validation study; CAD importer/placement UI pending |
| UX-04 | Make ordinary setup possible without CAD knowledge | Representative novice completes supported-machine setup using visible controls; record intervention count and completion time | Trial protocol needed; no invented timing promise |
| UX-05 | Keep visual and physical setup aligned | Probe/manual registration agrees within the selected profile tolerance; moving a fixture invalidates affected results | Registration contract proposed; no metrology implemented |
| UX-06 | Preserve a complete reusable job setup | Save/reopen machine profile, asset identities, frames, tools, offsets and job; changed dependencies invalidate stale checks | Dependency rules proposed |
| UX-07 | Work through modern laptops/tablets | Supported-browser trials, offline assets, responsive interaction under telemetry and model load | Existing UI to be audited |
| UX-08 | Show meaningful machine state | Distinguish commanded/estimated/measured position; stale telemetry visibly expires | Product requirement; not yet integrated |
| MOT-01 | Execute a local job without laptop pulse timing | Actual chosen backend completes a stored job; induced HMI loss follows its documented policy | Upstream native motion simulation and abstract supervisor studies; target hardware pending |
| MOT-02 | Handle the advanced machine feature envelope | Demonstrate selected threading, synchronized motion, kinematics, probing, tool-change and process cases in the intended backend | Pinned source audit; no universal feature promise |
| MOT-03 | Prevent stale requests from starting/resuming | Replay, delayed/reordered packets, reconnect and reboot tests | Abstract contract implemented and tested |
| MOT-04 | Never equate a hold request with stopped motion | Backend acknowledgment, bounded timeout, machine-specific deceleration/brake behavior | Abstract acknowledgment/timeout model; physical behavior pending |
| SYS-01 | Give ESP useful service/recovery duties | Radio/service failure cannot become a second actuator owner; diagnostics survive defined failures | Architecture contract; hardware and transport pending |
| IO-01 | Support broad electrical ecosystems | Each interchangeable interface has exact voltage/current/isolation/load/environment limits and compatibility tests | Module taxonomy and pre-design; no qualified modules |
| ENG-01 | Do substantial engineering before orders | Reproducible calculations, source builds, offline simulations, resource budgets and reviewed design package | In progress; no parts ordered |

## Capability levels shown to the user

1. **Viewable:** geometry imported with known or visibly unresolved units. No physical registration implied.
2. **Placed:** objects have explicit roles and coordinate frames. Snapping is a geometric operation.
3. **Registered:** a specific setup has independent commissioning/measurement evidence tied to its revision. A file cannot self-certify this by declaring a flag.
4. **Checked:** a specific job has passed the implemented checks against its profile, tools and setup. List precisely which checks exist and their limits.
5. **Accepted by controller:** the real backend has accepted that exact job and configuration and currently permits the requested operation.

Changing geometry, placement, machine profile, tool dimensions or relevant offsets invalidates dependent results. A pretty model must never obscure an unknown field. Normal supported-machine operation should make these transitions through short guided steps.

## MASSO as an evidence-based benchmark

MASSO's official documentation describes standalone embedded control with motion, spindle, Wi-Fi and I/O integration. Standalone operation itself is therefore not a new differentiator. Its G3/G3 Touch I/O documentation describes 24 optically isolated 5–24 V inputs and 18 TTL outputs. These are model-specific comparison points. [MASSO FAQ](https://docs.masso.com.au/MASSO_FAQ/about_masso)

MASSO documents spindle encoder feedback and threading synchronization, and offers an isolated relay module with explicitly bounded contact ratings. Advanced spindle support and expansion must be evaluated against their actual implementation, rather than treated as absent. [Spindle encoder](https://docs.masso.com.au/wiring-and-setup/setup-and-calibration/spindle-rpm-encoder), [relay module](https://docs.masso.com.au/wiring-and-setup/setup-and-calibration/masso-relay-module)

Our intended differentiators are the model-based setup flow, preservation of the user's preferred UI, clear machine/profile portability, and integrated setup verification. Current competitor support for equivalent flows has not been fully audited. A fair comparison needs the same machine, fixtures and task, with measurements such as setup interventions, time to an accepted setup, recovery steps, supported operations and documented failure behavior.

## Evidence levels

| Label | What it proves | What it does not prove |
|---|---|---|
| Manufacturer documentation | A documented claim for a specific product/version | Behavior of our design |
| Source inspected | A code path or target exists at a pinned revision | Complete enabled feature or successful build |
| Native build | That specific source/options compile for the host | MCU build, electrical outputs or real-time timing |
| Native motion simulation | The exercised parser/planner/step simulation path produced the recorded result | Physical pulse timing, servo stability or all G-code features |
| Contract tests | Proposed state/data rules handle the tested cases | A production implementation or complete fault coverage |
| Analytical budget | Demand under stated formulas and assumptions | Worst-case measured latency or hardware schedulability |
| Physical measurement | Behavior of a specific tested setup | Untested machines, environments or arbitrary voltages |

## Next reviewable milestones

1. Confirm the exact UI reference and identify its existing renderer, importers, backend adapter and mock/offline mode.
2. Connect scene validation to an isolated copy/extension of that UI. Demonstrate one complete synthetic setup with no machine connection.
3. Implement geometry import, guided placement and setup invalidation with real sample assets; add independent registration evidence rather than trusting imported declarations.
4. Demonstrate the hardest required machining cases on candidate backends. Use that evidence to choose local compute and deterministic I/O architecture.
5. Freeze concrete resource and electrical requirements, then develop schematics/layout and a targeted prototype verification plan.

These milestones continue the pre-order work. An import demo, passing tests or a parts shortlist is not the completed controller.
