# Existing UI candidate: static source audit

Audited 28 September 2026 UTC. Candidate: `Z:/Programming Projects/Genmitsu1030Cnc/fluidcnc`. **The user has not confirmed this is the exact Octopus/MR-1 UI they mean.** Its [README:154](../WORKSPACE_REFERENCES.md#artifact-e6759b65d6c9fa01) links the adjacent Octopus Pro firmware project; no MR-1/Langmuir identification was found in the reviewed README/app/index/3D-renderer files.

Only source was read. No app, server, browser, machine connection, firmware build, or machine command was run. No files on Z: were changed. This is an implementation audit, not visual acceptance or a redesign proposal.

## What is implemented and what is connected

| Area | Source evidence | Result |
|---|---|---|
| Existing page | [index.html:228](../WORKSPACE_REFERENCES.md#artifact-053acf5661809aa3), [index.html:281](../WORKSPACE_REFERENCES.md#artifact-50cea906708c8f19) | Existing “3D View” tab, toolbar, and canvas provide the natural location for scene setup; preserve the surrounding controls/layout. |
| Script graph | [index.html:714](../WORKSPACE_REFERENCES.md#artifact-2f9bc2c0ab977e5a) | Loads Three.js r128 from CDN, parser, both renderers, controller adapter, vector importer, simulator, then app. Loading a class is not evidence that the page instantiates it. |
| Active renderer | [app.js:460](../WORKSPACE_REFERENCES.md#artifact-7796e813ce3df500), [visualizer.js:29](../WORKSPACE_REFERENCES.md#artifact-42def58291e13ba9) | `setupVisualizer()` constructs `GCodeVisualizer`, whose context is Canvas2D. It has projected/rotatable views, toolpath, grid, envelope, and a tool marker. |
| Available WebGL renderer | [visualizer-3d.js:69](../WORKSPACE_REFERENCES.md#artifact-e42750c61f6faf14), [visualizer-3d.js:115](../WORKSPACE_REFERENCES.md#artifact-892620cc02797107) | Implements a Three.js scene, camera, inline orbit controls, lighting, grid, path group, and tool geometry. No `new GCodeVisualizer3D` was found in the candidate's JS. README's Three.js preview claim is therefore not established as the current app path. |
| Machine representation | [app.js:43](../WORKSPACE_REFERENCES.md#artifact-5bb2156d28f84141), [visualizer-3d.js:308](../WORKSPACE_REFERENCES.md#artifact-768eead8a5389e96) | Configurable numeric work envelope; 3D renderer draws a box. No articulated machine model, axes/joints tree, MR-1 mesh, or machine-model importer established. |
| Tool representation | [visualizer-3d.js:320](../WORKSPACE_REFERENCES.md#artifact-af706f4132dfba8a) | Procedural cylinders/sphere form spindle, collet, cutter, and glow. This is a visual marker, not verified physical tool/holder collision geometry. |
| Toolpath loading | [app.js:1775](../WORKSPACE_REFERENCES.md#artifact-9e5e056a18499b60), [visualizer.js:96](../WORKSPACE_REFERENCES.md#artifact-a3eea858c1abe9b0), [visualizer-3d.js:385](../WORKSPACE_REFERENCES.md#artifact-c42bc36a1ffea6dd) | Local file text becomes G-code lines; both renderers can parse and accept `toolPath`. This is a reusable seam for controller-generated motion traces. |
| SVG/DXF import | [vector-importer.js:42](../WORKSPACE_REFERENCES.md#artifact-f5b76fa69779d4e3), [vector-importer.js:522](../WORKSPACE_REFERENCES.md#artifact-e77829975b40428d), [vector-importer.js:892](../WORKSPACE_REFERENCES.md#artifact-886446c734637a82) | Implements text SVG/DXF parsing into 2D paths and G-code generation. No `new VectorImporter` or vector import binding was found in app/index; the README feature is present as a module, with app integration unverified. |
| Fixture/stock/mesh import | Search of candidate JS and index for STL/GLTF/OBJ loaders, mesh extensions, fixture/stock/machine-model APIs | No implementation found. SVG/DXF-to-G-code is not 3D fixture loading. No stock-removal or geometric fixture-collision engine was found in the requested files. |
| Local analysis | [gcode-simulator.js:58](../WORKSPACE_REFERENCES.md#artifact-9293b2a245c87b17), [gcode-simulator.js:84](../WORKSPACE_REFERENCES.md#artifact-252f00b3a22127db), [gcode-simulator.js:187](../WORKSPACE_REFERENCES.md#artifact-cf0648dd6d697520) | Parses browser G-code, compares bounds with numeric limits, checks common issues, estimates independent triangular/trapezoidal segment times. This is not execution of LinuxCNC/grblHAL's actual planner. |
| Local playback | [gcode-simulator.js:262](../WORKSPACE_REFERENCES.md#artifact-caba5d87e12b59e7), [gcode-simulator.js:350](../WORKSPACE_REFERENCES.md#artifact-f7881e2d088ded01) | Playback uses per-frame segment progress and straight endpoint interpolation. `dryRun()` iterates local parsed segments and does not send them to the controller. It provides no physical clearance proof. |
| Live position | [app.js:430](../WORKSPACE_REFERENCES.md#artifact-d0848e41d4de831e), [grblhal.js:479](../WORKSPACE_REFERENCES.md#artifact-1131847a958648e9) | Parsed controller status feeds work position to the current visualizer. Preserve explicit distinction between work coordinates and machine coordinates. |
| Controller boundary | [app.js:150](../WORKSPACE_REFERENCES.md#artifact-0c69ffa3b70bf8ac), [grblhal.js:161](../WORKSPACE_REFERENCES.md#artifact-d01e3430781c0a33), [grblhal.js:689](../WORKSPACE_REFERENCES.md#artifact-46f93a3356825f6f) | `GrblHAL` combines transport, state parsing, events, command validation, and streaming. It is a natural initial adapter, but transport and protocol are not yet separate abstractions. |

## Connection behavior relevant to offline work

- Page initialization constructs the whole app on DOM ready: [app.js:2202](../WORKSPACE_REFERENCES.md#artifact-82f768c4c039b7c2).
- If saved connection type is WebSocket and a saved IP exists, init schedules a connection after 500 ms: [app.js:81](../WORKSPACE_REFERENCES.md#artifact-774beb9f4e4d2df5). `loadSettings()` restores the IP field before that call: [app.js:1933](../WORKSPACE_REFERENCES.md#artifact-a196a5382948ee94).
- The adapter creates a real WebSocket: [grblhal.js:285](../WORKSPACE_REFERENCES.md#artifact-d406a7da86596016). On open it starts heartbeat and sends `?`, `$I`, `$G`: [grblhal.js:330](../WORKSPACE_REFERENCES.md#artifact-d1cd39f61ef785db). App connection handling additionally queries `$$`: [app.js:263](../WORKSPACE_REFERENCES.md#artifact-6e74581071485fbb).
- Unexpected WebSocket closure can schedule reconnection: [grblhal.js:354](../WORKSPACE_REFERENCES.md#artifact-167931c8661ea8c7), [grblhal.js:380](../WORKSPACE_REFERENCES.md#artifact-da1b44eaa6e66a6a). USB requests a user-selected port and then opens it: [grblhal.js:201](../WORKSPACE_REFERENCES.md#artifact-6b71497652353088).
- No automatic motion-on-page-load was established. Automatic connection and queries are enough to make launching the unchanged page unsuitable for this read-only task. An offline scene editor should inject a disconnected adapter before app initialization, rather than relying on not pressing Start.

## Integration gaps to account for

1. Renderer selection is not wired to the available WebGL class. `app.visualizer3D` is referenced by shortcuts at [app.js:1595](../WORKSPACE_REFERENCES.md#artifact-675594883d6dfd8d) but is not constructed. The 3D constructor takes a container, while the active constructor takes a canvas.
2. Simulation callback signatures do not agree: [app.js:726](../WORKSPACE_REFERENCES.md#artifact-689bd3d37fd61ffb) expects `(pct, pos)` and calls `setSimulatedPosition(pos)`, but [gcode-simulator.js:296](../WORKSPACE_REFERENCES.md#artifact-83564c60e0831d29) emits one object. Neither reviewed renderer defines `setSimulatedPosition`; both provide `setToolPosition(x,y,z)`. This is a static finding, not a reproduced runtime result.
3. Workspace settings update the visualizer and AI only: [app.js:1956](../WORKSPACE_REFERENCES.md#artifact-3dbf2ea22b4f5061). Simulator defaults are independently `400×400×100`: [gcode-simulator.js:18](../WORKSPACE_REFERENCES.md#artifact-aec75cbda9d7621b), while app defaults are `400×400×200`. Its `setGrbl()` can copy machine limits, but no call was found in app.js. One machine profile should feed these consumers.
4. [app.js:1814](../WORKSPACE_REFERENCES.md#artifact-bf48ecf3365ecbb4) starts controller streaming directly after checking loaded lines and idle state; it does not require `simulateGCode()` first. Imported setup geometry must not silently alter or authorize this path.
5. Three.js geometry uses CNC-to-renderer axis conversion `(x,z,y)`: [visualizer-3d.js:443](../WORKSPACE_REFERENCES.md#artifact-13c16e4094222858). New models need an explicit units/orientation/placement conversion shared with toolpath and status rendering.

## Minimum additions while preserving the UI

1. **Confirm the candidate** before adapting source. Preserve page layout, control names, colors, toolbar behavior, and existing workflows once the exact reference is identified.
2. **Inject a controller interface** at `setupGrbl()`: existing adapter for deliberate live use; inert offline adapter for scene setup and trace playback. Keep connection creation/reconnection outside rendering/import code. No machine command methods in scene objects.
3. **Add one scene data model** containing machine profile, coordinate frames, stock, fixture instances, tool/holder geometry, and external asset references. Store millimeters and transforms explicitly; keep scene persistence separate from live controller settings.
4. **Normalize a renderer interface** around existing `setToolpath`, `setToolPosition`, `setView`, resize, and envelope updates. Make Canvas2D and Three.js selectable behind the existing viewport; do not replace the entire app to gain model loading.
5. **Add setup editing within the current visualization tab**: import model, choose units/orientation, set placement, toggle visibility, save/load setup. Use dedicated mesh loaders for fixtures/machine geometry; retain SVG/DXF import for its existing 2D-path role.
6. **Consume an immutable simulation trace** from the actual upstream controller engine for playback. Keep browser preview/estimate explicitly distinguishable from actual planner traces and from future collision checking.
7. **Add offline contract checks** for no transport calls during setup, coordinate/units transforms, persistence round trips, imported geometry bounds, renderer method compatibility, and trace-position agreement. Runtime visual review remains outstanding because the app was not launched.

## Snapshot identifiers

These hashes identify the entrypoint files reviewed; the candidate itself was not edited or copied.

- `app.js` SHA-256: `42046D390D6610B691DFFEA9BAC669D6599F8E4A176441F94D5E2E5943253BDB`
- `index.html` SHA-256: `B8EAF9E63EB4082BF0A04B7729E528A08436A2EC67938CA0CADEABBBCE82DC56`

Decision: the candidate offers reusable UI and visualization boundaries, but its source does not yet establish a connected Three.js model/fixture workflow. The minimum extension is an offline scene/renderer adapter inside the existing UI, pending confirmation that this is the user's intended reference.
