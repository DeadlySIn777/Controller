# Board CAD increment — 30 September 2026

The user requested an updated board CAD view in the Codex side panel, retained as the design evolves. The [live review package](../../hardware/board_review/README.md) implements this with editable native KiCad placement studies, actual imported pad nets, native 3D renders and an offline interactive viewer. The latest published revision is `20260930-03`; older published revisions remain selectable.

- [Source and package review](SOURCE_REVIEW.md): what existed before this increment, independently checked placement-only BGA/ASE candidates, omitted boundaries and required circuitry.
- [Actual browser QA](VIEWER_QA.md): desktop/narrow views, component/pin inspection, pan/zoom, board/3D/revision controls and evidence limits.
- [Independent native placement QA](PLACEMENT_QA.md) and [machine-readable results](PLACEMENT_QA.json): exact source pin sets, imported pad nets/geometry, manifest and source hashes, and conservative placement-envelope checks. No checked envelope intersections; two watchdog footprints lack courtyards, so that check is incomplete.
- [Final receipt](review.json): file hashes, source-hash freshness, imported geometry counts, source/native checks and the actual queued right-panel request.
- [MC native DRC](motion-card-03-drc.json) and [watchdog native DRC](watchdogs-03-drc.json): zero other reported violations but **197/50 unconnected items**. The result is unrouted, not a DRC pass.

No new electrical design was integrated, target firmware compiled, FPGA fitted, physical board measured or fabrication package exported. MC includes only the existing core component candidates, not the full controller assembly. Watchdogs remain separate/unintegrated; proposed outlines, missing body models and pending circuitry are visible. Screens, required eight/twelve motor capability, fixed wiring-base architecture and commercial terms are unchanged.

The viewer is served at `http://127.0.0.1:8788/index.html`; the native app's right-panel open request returned `queued`, which is recorded rather than reported as proof that the panel was already visible. This browser view refreshes published CAD revisions; schematic-to-CAD rebuilding is the explicit engineering update procedure, not an unattended background action.
