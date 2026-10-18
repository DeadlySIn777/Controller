# Board CAD viewer QA — 30 September 2026

Viewer: `hardware/board_review/index.html`  
Local review URL: `http://127.0.0.1:8788/index.html`  
Final observed source revision: **20260930-03**.

This record covers the read-only browser presentation of the editable placement studies. It does not establish electrical correctness, PCB DRC, FPGA fit, physical dimensions, timing, machine operation or manufacturing readiness.

## Actual browser observations

The viewer was exercised through the Codex in-app browser using CUA's documented browser APIs and Playwright locators. Browser screenshots were visually inspected during QA. **No browser screenshot files were saved**, so this record does not cite screenshot artifacts.

| Check | Observed result |
|---|---|
| Initial manifest and latest revision | Revision `20260930-03` loaded; the motion-card SVG contained 70 component groups. |
| Desktop viewport, 1280 × 720 | The complete proposed board outline was visible within the bounded CAD viewport; no horizontal document overflow. |
| Narrow viewport, 440 × 900 | Responsive stacked layout showed the board and controls without horizontal document overflow. |
| SVG footprint selection | Clicking the actual U4 footprint opened its inspector. |
| U4 source nets | Inspector displayed pad 1 NC, pad 2 `/FPGA_USER_RESET_RC`, pad 3 `/LOGIC_GND`, pad 4 `/FPGA_USER_RESET_DELAYED`, and pad 5 `/IO_3V3`. This observes presentation of imported nets, not a new electrical validation. |
| Change context | U4 displayed `review-focus` with the reason that its current engineering focus was unchanged from the preceding CAD revision. |
| Zoom and pan | The + button changed the SVG viewBox; a coordinate drag changed its origin; Fit restored the proposed board view. |
| Board switching | The watchdog study loaded with 22 native source footprints, zero placement-only candidates and zero routed tracks. |
| Native 3D images | Both revision-03 image elements completed loading with nonzero natural width. |
| Missing model disclosures | MC reported 68/70 available models and missing U1/Y1 body models; WD reported 20/22 and missing U1/U2. The text explicitly retained those footprints in editable CAD. |
| Revision history | Selecting revision `20260930-01` retained the watchdog board selection and displayed the return-to-latest button. |
| Return to latest | The return button restored revision `20260930-03` and its watchdog image path. |
| Component search | Searching `TPS3851` returned watchdog U1 and U2. |
| Browser console | Captured error-level browser logs were empty during these checks. |
| Cleanup | Search cleared; MC top view restored; temporary viewport override reset to normal 1280-pixel width; temporary QA tab closed. The parent's queued user-facing side panel was untouched. |

The first desktop inspection found that an unconstrained flex height pushed part of the board below the visible viewport. The viewer was corrected to bound the CAD viewport height, reloaded, and the desktop and narrow observations above were performed on the corrected viewer.

## Source checks

- The final inline JavaScript compiled with Node's `vm.Script` without a syntax error.
- Inspection found zero external HTTP script or stylesheet references. The viewer uses local manifest and image assets without a third-party library or CDN.
- The implementation polls the stable manifest every three seconds. This interval was inspected in source; this QA did **not** publish another revision during the test to independently measure live-update latency.
- The interface distinguishes source-assigned footprints from placement-only package candidates, and engineering review focus from an actual revision change. It displays proposed outline assumptions, open engineering work, source records and unrouted/unqualified status.

## Native-render follow-up

The browser's low-resolution fitted view initially made the package bodies appear unusually flat. The parent subsequently inspected the full-resolution revision-03 native render and confirmed visible watchdog SOT bodies U3/U4/U5 plus passive bodies, and the MC U2 SOIC body. That separate visual inspection attributed the flat appearance to camera angle, low package heights and the proposed card proportions. Missing model bodies remain explicitly disclosed. This is visual artifact inspection, not a physical measurement or qualification of those parts.
