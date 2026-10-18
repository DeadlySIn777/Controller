# Product experience: keep the existing interface, make setup approachable

Status: proposed product requirements, updated 28 September 2026 for multiple screen sizes. The existing Octopus/MR-1 interface is the user-approved experience to preserve. Its source and implemented capabilities are still being located/audited; this document does not claim the features below already exist. It specifies behavior to implement or verify before calling the controller shippable.

## 1. Product promise

An ordinary user connects to the controller, selects their machine, drops in models of the machine, mounting plate, vise, stock, or tools, and prepares a usable setup through guided controls. Routine setup and operation require no terminal, code editing, firmware compilation, pin-number editing, or CAD knowledge.

Preserve the existing interface's layout, styling, navigation, machine view, controls, and terminology wherever they already serve this workflow. Add missing capabilities within those patterns. Do not start a replacement UI or redesign the product because another framework is convenient.

The product is a controller appliance with a bundled application and supported machine profiles. Geometry makes setup understandable; a machine profile and actual machine registration make control trustworthy. The interface must make those distinctions clear without making users learn the implementation.

Offer screen packages in the **7-, 10-, 12-, 14-, 18- and 21-inch classes**, with room for other qualified sizes. Use one responsive application and service contract. Compact layouts may use focused panels and large layouts may show more at once; preserve the same supported setup and operation functions. Define usable resolution, scaling and physical touch targets for each panel instead of shrinking the large-screen controls. The [display-tier plan](DISPLAY_TIERS.md) covers hardware, cost and acceptance. The earlier 21.5-inch reference is one option in this range.

## 2. What the user receives

| Deliverable | Required content |
|---|---|
| Controller appliance | Compatible firmware, local application, job/profile storage, recovery path, identified hardware revision |
| Supported machine profile | Tested machine/drive/I/O definition, kinematics, limits, homing, spindle behavior, required interlocks, setup instructions, compatible firmware/hardware versions |
| Machine visual bundle | Model assets, meaningful moving parts, joint-to-part associations, model frame/units, verified visual pose conventions |
| Setup library | Reusable plate, vise, fixture, tool and stock models; dimensions, attachment surfaces and saved placements when known |
| Guided commissioning | Connection, machine identity check, required physical checks, homing/reference, setup placement and registration |
| Recovery/service experience | Actionable faults, configuration restore, update recovery, exportable diagnostic bundle; no coding required |

A downloadable profile may include the visual bundle and optional setup examples. A geometry-only upload remains usable as a visual asset without silently becoming a motion configuration.

## 3. Supported-machine first use

The normal flow must be short, resumable, and expressed in the user's machine language:

1. **Connect:** open the controller's local address or discovery link; identify the physical controller by its label/indicator.
2. **Choose the machine:** select the detected compatible profile or choose from the supported list. Show the exact machine variant and connected controller identity.
3. **Check the connection:** present a guided checklist with live results for required hardware, drive status, interlocks, and emergency-stop indication. Any required movement check is explicit and bounded.
4. **Reference the machine:** use the existing home/reference controls with profile-specific guidance and observable results.
5. **Add the setup:** drag in plate/vise/stock models or select library items; confirm their role and dimensions only when information is missing.
6. **Place and locate it:** place visually, then use a supported probing, known-mounting-location, or guided manual-reference workflow to establish actual location.
7. **Review and run:** show the job, tool, stock/setup, work origin, and readiness in the existing interface; the user explicitly starts the job.

Finish each step with a saved state. Closing the browser, losing Wi-Fi, or restarting the service must not erase completed setup work. Reconnection displays the controller's actual current state rather than replaying a browser's old command.

## 4. Machine profile bundle contract

The profile is the bridge between a generic appliance and a specific machine. Users select it; machine integrators author and qualify it.

| Bundle area | Contents and validation |
|---|---|
| Identity | Profile ID/version, machine family/variant, controller/module compatibility, author/source, support status |
| Motion | Joint/axis mapping, kinematics, travel and rate limits, gearing/scales, directions, homing sequence, feedback roles |
| Machine functions | Spindle modes, probing, tool changing, coolant, lubrication, clamps, doors/interlocks, fault behavior |
| Interfaces | Typed module assignments and required signals matched to installed hardware; no inferred voltage or polarity from CAD |
| Visuals | Assets, units, model frames, moving-part hierarchy, joint bindings, optional collision bodies, home/reference pose |
| Setup guides | Machine-specific illustrations, clear physical checks, supported registration methods, named attachment locations |
| Compatibility | Firmware/application/schema requirements, migration rules, integrity/authenticity information, required extensions |
| Qualification | Tested feature scope, known limitations, representative job/fault checks, profile revision approval record |

Factory or integrator defaults are distinct from a customer's setup data. Updating the machine profile must preserve compatible fixtures/jobs/work offsets and explain changes requiring renewed verification. Imports never execute scripts or acquire motion permission merely because they contain a profile.

For an unsupported machine, offer a structured integrator/configuration workflow using supported components and measurements. The user never edits raw source files, but complete commissioning cannot be inferred from an arbitrary machine model. The first release must name its supported machine/controller combinations rather than claiming universal automatic commissioning.

## 5. Drag-and-drop model import

Accept files in the machine view and asset library using existing UI conventions. Supply a file-picker/import action alongside drag-and-drop so a touchscreen-only user can complete the same flow. Show upload/conversion progress, a preview, and a cancel action. Keep the original file and a derived display model so conversion does not destroy the source.

The intended import path covers common mechanical CAD exchange and mesh assets. Freeze a tested file/version compatibility matrix after the UI/converter audit. STEP/STP, STL and GLB/glTF are candidate first-release requirements; OBJ, IGES and other assemblies/formats are evaluated explicitly. These are proposed support targets, not statements that a parser is already installed.

"Drop in your CAD" means guided handling of varied files, not a promise to parse every proprietary format. Use a bundled local converter where necessary. Unsupported files receive a specific explanation and a supported model-acquisition/conversion path; never send the user to install developer tools or change source code. Any optional external conversion service requires an explicit choice before uploading machine/job data.

Import handling must:

- Distinguish a single object, an assembly, and a bundle of related files; preserve useful part names/hierarchy when available.
- Validate type, size, complexity, archive paths and contents; impose documented processing limits and allow cancellation.
- Run parsing/conversion outside motion-critical work; a malformed or huge file must not stall motion or exhaust the controller.
- Present dimension/orientation checks; never quietly accept an implausibly tiny or huge machine because unit metadata was absent.
- Generate display geometry and optional simplified collision geometry separately; identify missing or failed parts.
- Avoid deleting unsupported parts silently. Show a partial-import result and what is missing.
- Keep repeated imports deterministic; identify duplicates and let the user replace a model without losing its placement unnecessarily.

## 6. Guided units, role, orientation and placement

Ask only for missing or ambiguous information, with a live preview at every step:

| User-facing choice | Internal result | Product behavior |
|---|---|---|
| "What is this?" | Machine / plate / vise / fixture / stock / tool / reference object | Suggested role from context; user can correct it |
| "Are these dimensions right?" | Explicit source-unit conversion | Show overall dimensions in preferred units; offer a known-distance check if metadata is absent |
| "Which side is up?" | Model orientation | Click a face or use named orientation controls; preview axes and part before accepting |
| "Where does it attach?" | Parent object and mounting relationship | Select a table/plate surface or profile-defined location; show contact/offset clearly |
| "Where is it on the real machine?" | Registration method and measured/reference transform | Offer only methods the machine/profile can support |
| "Where is the work zero?" | Selected work coordinate system and offset | Use existing work-offset controls; show origin and tool/stock relationship |

Do not require users to type matrices, Euler angles, joint indices, or machine signal names. Permit familiar numeric distances and rotations for deliberate placement, plus face/edge/point selection and snapping when geometry supports them. Meshes without meaningful faces need a simple point/bounds-based alternative.

Changing units means interpreting source dimensions, not stretching a calibrated machine. After registration, edits to scale, orientation, parent attachment or geometry that affect placement mark dependent verification stale. A mirrored/reversed model cannot silently change the machine's physical travel direction.

## 7. Keep four meanings separate

| Layer | What it answers | What it does not establish |
|---|---|---|
| Geometry | What the machine, fixture or stock looks like and its nominal shape | Wiring, drive limits, homing, actual installed location |
| Kinematics | How coordinated axes/joints move and relate to moving bodies | Electrical compatibility or physical measurement accuracy |
| Electrical/machine configuration | Which qualified interfaces drive/read the machine and how functions behave | Where a vise was bolted down today |
| Measured registration | Where an object/work origin is relative to a referenced machine, using a recorded method | That a visual model perfectly matches every physical surface |

Use an explicit internal frame graph: machine reference → moving table/fixture attachment → plate → vise/fixture → stock/work origin, plus spindle/tool frames. Actual graph structure depends on machine kinematics; do not assume the table is stationary. Store units, parent frame, transform, method, timestamp and validity dependencies for each placement.

A machine visual model animates from the qualified kinematic/joint mapping. A whole-machine CAD assembly does not automatically tell us which part is a servo joint. Supply those bindings in supported profiles; provide a guided integrator mapping tool for new profiles.

Registration can use known repeatable mounting geometry, probing, a tool/edge reference, or a validated manual measurement process. Record which was used and its relevant uncertainty. A visual drag establishes a proposed placement; it does not count as physical measurement.

## 8. Visible state and control readiness

| State shown to user | Meaning | Permitted behavior |
|---|---|---|
| Added | Model loaded successfully | View and arrange; no new motion authority |
| Placed | Nominal visual position exists | Preview setup; show that location still needs confirmation if control checks depend on it |
| Located | Actual placement established by a supported method | Use for the functions explicitly qualified by that method |
| Needs checking | Homing, model, mounting, tool or configuration change invalidated relevant evidence | Explain exactly what changed and provide one guided recovery action |
| Ready | All required machine/job conditions for the requested operation are satisfied | Existing explicit Start/Jog controls can request permitted motion |

Readiness belongs to the operation and its dependencies, not a blanket green mark for the entire model. A fixture may be located sufficiently for a visual preview but not qualified for tight collision clearance. Show an understandable reason beside a blocked action, and take the user directly to the necessary step.

The machine must report actual/homed/commanded position distinctions accurately. Display telemetry that becomes stale as stale. Browser refresh, reconnect, opening a saved workspace, or loading a familiar model never constitutes an Enable or Start command.

On each screen size, keep machine identity, mode, active tool/work offset and relevant faults/control state understandable when panels collapse or an on-screen keyboard opens. Keep relevant Hold/Stop controls accessible during operation. Provide touch paths for functions otherwise exposed through hover, right-click or keyboard shortcuts. Cancel interactive jog on touch cancellation, control-context loss or expired freshness. Resizing, rotation and screen replacement change presentation, not calibration, offsets or motion authority.

## 9. Preview, collision checking and job execution

Reuse the existing preview/run workflow and show machine/setup geometry in it. Before promising collision protection, define exactly what is modelled: tool, holder, spindle/head, clamps, vise, stock, table, travel limits and moving joints. Mark missing assets and geometry/registration uncertainty.

Visual path rendering, material-removal simulation, geometric collision checking and real machine protection are separate capabilities. Do not label a job "collision free" when only the tool centerline or nominal fixture mesh was checked. Collision checks use the registered setup revision and state what they cover.

Each queued/running job records its program revision, machine-profile revision, tool data, work offsets, setup/registration revision and relevant control configuration. Changes that affect execution require revalidation at a defined stopped state. The active controller owns execution; multiple browser sessions do not become simultaneous motion operators.

## 10. Save, reuse, share and recover

Save a complete setup bundle with geometry, roles, placements, registration evidence, tools/work offsets as appropriate, and compatible machine identity. Separate reusable nominal placement from the claim that today's physical setup still matches it.

On another machine, imported geometry/library items remain useful while machine-specific offsets and registration become proposals requiring the target machine's verification. Never copy pin assignments or high-voltage interface assumptions merely because a fixture bundle was imported.

Offer useful names, thumbnail previews, recent setups, duplicate/rename, and a clear restore point before destructive edits. Export/import should work offline. Diagnostics should be downloadable through the application without a terminal, and distinguish recoverable service failure from loss of machine reference.

## 11. Appliance and compute implications

- Bundle the existing browser application with the controller, versioned together with its API and compatible profiles. Essential configuration and running supported jobs must work without a cloud account or internet connection.
- Keep the laptop machine-independent: a supported modern browser, normal USB/network connectivity as selected, and no required Linux installation or development environment.
- Budget embedded application compute/storage for model conversion, geometry preparation, job files, profiles, thumbnails, logs and update recovery. Audit the existing interface and realistic assets before selecting MCU-only versus embedded Linux compute.
- The browser may render interactive geometry; define what work happens in the browser versus on the appliance. Optional laptop-side conversion must not make motion timing depend on laptop performance.
- An ESP helper can provide provisioning, local status, panel functions, diagnostics and recovery. Do not assign large CAD conversion or 3D assembly processing to it without measured resource evidence.
- Isolate conversion/rendering/service failures from the motion executor. Publish finite import size/complexity limits with helpful behavior when exceeded.
- Updating the UI/profile must preserve saved setups and controller compatibility. Provide a local recovery route when the application cannot load.

## 12. Release acceptance: low-friction use must be demonstrated

These are proposed acceptance targets to refine with the existing UI and actual supported hardware; they are not reported test results.

| Scenario | Acceptance evidence |
|---|---|
| Familiar UI preserved | Side-by-side review against the located Octopus/MR-1 reference; existing navigation/control paths retained; changes justified by a named workflow need |
| Screen-tier usability | Same touch-only setup, model import, offsets, jog, job review/run and fault recovery on compact/medium/large layouts; verify each offered panel's native mode, scaling and touch behavior; no hidden required action behind keyboard/dialogs |
| First supported setup | At least five users without coding/CAD experience complete the documented flow without terminal/code editing or engineer intervention; record failures and revise the flow |
| App interaction burden | Target at most seven major guided stages and under ten minutes of active application interaction for a prewired supported machine/profile, excluding physical installation, probing/homing travel and job preparation |
| Drop-in supplied bundle | Machine, plate and vise assets appear at the correct scale/orientation with names/roles preserved; only unresolved physical registration requires input |
| Unfamiliar model | Missing units/orientation are resolved using dimensions and visual controls; no user must learn a CAD package or enter a transformation matrix |
| Placement honesty | A dragged vise remains nominal until located; moving/remounting it or changing dependent frames visibly invalidates affected checks |
| Repeat setup | A previously saved compatible setup opens without repeating solved metadata questions; required reference/registration checks remain explicit |
| Offline operation | Cold boot, supported profile selection, stored model/job use, setup review and operation work with internet unavailable |
| Service load isolation | Maximum supported model import/conversion and several browser sessions cannot violate the motion execution's independently defined timing/fault requirements |
| Bad input | Corrupt/oversized/unsupported/partial CAD import produces a clear result, can be canceled, and leaves existing setup/control state intact |
| Connection loss | Jog freshness expires as designed; reconnect shows true controller/job status; no stale command replay or automatic restart |
| Wrong profile/module | Incompatible hardware/profile combination is identified with a specific remedy and cannot silently arm |
| Update/recovery | Interrupted service update has a documented local recovery; saved valid setups remain recoverable; reboot never restarts motion |
| Replace a failed section | Power down, exchange a qualified electronics module while keeping individual conductors attached, power up and restore compatible assignments; show changed hardware and required affected checks, with outputs inhibited |
| Replace compute or recover damaged settings | Supplied recovery image plus complete machine-memory records reconstruct supported settings offline; wrong-machine, corrupt or conflicting records produce actionable errors and never silently enable motion |
| Honest preview | Coverage and missing geometry are visible; preview output is tied to exact setup/tool/job revisions |

For import responsiveness, freeze representative real model bundles and a target appliance/browser before setting numerical load-time, memory and frame-rate limits. Measure those limits rather than selecting processor hardware from an empty demo.

## 13. Implementation order once the UI source is found

The [repair/memory plan](MODULAR_REPAIR_AND_MEMORY.md) extends the recovery experience: identify slot and replacement, state compatibility, show preserved assignments, distinguish the replacement's own factory calibration, and offer guided verification for affected functions. Do not force users through every axis-calibration step after replacing an unrelated I/O bank. A power cycle still loses live reference confidence as defined by the machine, so stored axis scale and current homing are shown separately. Unknown or incompatible modules remain inhibited with a specific supported replacement or recovery route. A service screen does not issue a motion/output command simply by opening or completing configuration import.

1. Inventory and run the existing interface; record supported workflows, data structures, asset formats and licensing/deployment dependencies.
2. Preserve a reference build and a realistic machine/plate/vise setup as the visual and functional baseline. Define compact, medium and large responsive layouts; exercise all requested size classes and their intended resolutions without creating separate application forks.
3. Define profile/setup/asset/registration schemas and map existing state to them with minimal UI changes.
4. Implement or verify local asset import, metadata checks, role/placement flow and persistent setup bundles.
5. Connect live machine state and the readiness/registration lifecycle through a simulator before physical motion.
6. Test the supported-machine walkthrough with users; fix friction and ambiguous state before adding more machines/formats.
7. Qualify the selected hardware/profile combination, publish support boundaries, and complete recovery/offline/performance checks before shipment.

The immediate product deliverable is a convincing, testable end-to-end workflow in the existing interface. Electronics and compute choices must support that experience and its motion requirements.
