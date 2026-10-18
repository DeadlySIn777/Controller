# MC permission review and resulting repair

30 September 2026. The original MC permission r0.1 was independently inspected against frozen IS-1, retained manufacturer PDFs and native KiCad pin/net exports. That review found an actual watchdog-trip defect despite the original ideal-digital checks passing. The parent then assigned this same reviewer to implement r0.2. **The repaired circuit and its qualification are therefore reviewer-authored; they are not a second fully independent sign-off.** Integration topology/loading were subsequently reviewed read-only against the root-owned four-sheet candidate.

## Original finding

The original “healthy-state” watchdog flip-flops asynchronously cleared on any WD_x_OK LOW, including startup or an idle/disarmed health cycle. Their complemented outputs consequently asserted watchdog trip even when actual timer SET1 was LOW. Frozen IS-1 section 5.2 instead requires a sticky trip **when WD_x_OK falls while SET1 is HIGH**. A rising request while health is already LOW must not manufacture a new falling-health event.

The original 4,145 ideal-digital checks passed because they omitted those counterexamples. The original 48-part files and receipt remain archived at [r0.1 before repair](mc-permission-r01-before-trip-fix/review.json). They are historical evidence for that circuit and are not relabelled as repaired results.

The initial validator also did not comprehensively check native MPN/value/footprint/DNP, pin-function/type, duplicate native pins or mandatory components. Mirrored graph expectations alone could miss a physical device-map defect.

## Concrete r0.2 repair

The actual SET1-qualified event is now implemented with sourced physical gates:

1. U16 (`SN74LVC2G04DBVR`) inverts WD_M_OK and WD_O_OK, so a falling health event creates a rising flip-flop clock.
2. U17 (`SN74LVC2G32DCUR`) drives each trip D input with **stored TRIP_Q OR actual WD_x_SET1_BUF**. Feedback preserves an already recorded trip through later disarmed health cycles.
3. U14/U15 (`SN74LVC2G74DCUR`) capture that D value on the falling-health event; Q_N is the active-LOW external trip status. No clock event is manufactured by a request/SET1 rise while health is already LOW.
4. U18 inverts explicit active-HIGH `WD_REARM_M/O` record-clear strobes. U19 combines the resulting clear terms with `MC_RAILS_OK`, defining power clear and deliberate record clear.

Both actual SET1 nodes are the conditioned gate outputs that also reach TPS3851 pin 5. This preserves arm-latch and OPI equations while fixing the trip record. Added U16–U19 and C16–C19 increase the fitted circuit from 48 to **56 parts**. Historical source results remain intact.

`WD_REARM_M/O` are now short explicit **record-clear** pulses after the host has stored the event, while disarmed. Holding either clear asserted can suppress trip capture, so that software/logic protocol must still be implemented and reviewed. Proposed conditioning, control endpoints and sequencing have not become an agreed IS-2 contract merely because the circuit passes ideal checks.

## Physical maps and separate oracle

Pin tables were independently extracted from page 3 of five retained manufacturer PDFs and compared against explicit test fixtures:

| Physical part/package | Required map |
|---|---|
| SN74LVC1G11 DBV | A1, GND2, B3, Y4, VCC5, C6 |
| SN74LVC2G08 DCU | 1A1, 1B2, 2Y3, GND4, 2A5, 2B6, 1Y7, VCC8 |
| SN74LVC2G32 DCU | Same dual-gate map as 2G08 |
| SN74LVC2G04 DBV | 1A1, GND2, 2A3, 2Y4, VCC5, 1Y6 |
| SN74LVC2G74 DCU | CLK1, D2, Q_N3, GND4, Q5, CLR_N6, PRE_N7, VCC8 |

The 2G74 DCU device is **one D flip-flop**, despite its family name and historical “half package” prose. The repaired source counts actual whole physical devices rather than relying on that prose.

The validator evaluates the physical graph and compares permission outputs to separately written frozen IS-1 equations. New tests cover disarmed/startup health LOW, a first unrelated drive with an already LOW health input, request rise without a falling-health edge, actual SET1 qualification versus raw request, sticky preservation and explicit clear. Circuit initialization now records the settled inverted clock levels before the first driven input, preventing simulator initialization from manufacturing a watchdog fall. Mutation checks remove/invert qualification terms, clock polarity, feedback or clear logic and alter physical pin maps, native metadata, duplicate pins or compulsory parts.

The tests also preserve the separate raw-inhibit and final TX permission semantics, asynchronous arm clear, endpoint-ready qualification, output arm clear, process permission and all three MC OPI clears. Upstream qualified boundary names are treated as assumptions, not implemented filters.

## Retained result and evidence boundary

[The immutable r0.2 receipt](mc-permission-r02/review.json), captured 2026-09-30 12:00:28 UTC, records:

- **19 copied host test methods**, zero failures/errors/skips.
- **4,159 ideal-digital checks** against the permission/event oracle.
- **Two fresh matching native exports**, native KiCad ERC zero violations.
- **27 copied/hashed inputs** unchanged during verification; frozen IS-1 unchanged.

These are source, host graph/event tests, native export and circuit ERC observations. They do not prove physical race behavior, metastability, actual CLK/CLR pulse widths, reset recovery/removal, output loading, FPGA fit, PCB routing or measured machine response.

The retained 2G74 table requires D setup 1.9 ns, D hold 0.5 ns, asynchronous CLR inactive before clock 1.8 ns and minimum clock/CLR pulse width 3.5 ns at the cited 3.3 V ±0.3 V / -40 to 125 °C conditions. The event model does not simulate those limits. The 2G04 and 2G32 propagation maxima are 4.6 ns and 4.8 ns at their stated CL=50 pF test condition; finite edge rates and SET1/WD transition ordering need target qualification rather than counting ideal event checks as timing closure.

## Read-only integrated review

The root's exported candidate now connects the proposed independent `RAW_INHIBIT_N` to FPGA A2; TX_PERMIT independently reaches FPGA E6 and the TX OPI clear. That satisfies the specific topology requirement that final TX permission must not feed the endpoint's raw inhibit input. The proposed alias changes a missing control allocation and requires versioned interface coordination; historical FPGA core/175-pin-budget files remain preserved.

The native candidate uses qualified destination-3V3 `FPGA_CRESET_N` for `MC_RAILS_OK`, keeping raw 5 V power health local to its buffer input. Delayed `FPGA_USER_RESET_N` is the proposed CDONE qualifier and actual SET1 guard. Both trip inputs reach actual timer SET1. Fitted counts and explicit review-marker exclusion match the intended **203-part** source candidate.

[The separate whole-net loading review](MOTION_CARD_LOADING_REVIEW.md) records the retained original pulls, all fitted LVC receiver allowances and the power-block external reset budget. It finds ordinary loaded-LVC DC screens compatible with their cited receiver levels, but withdraws invalid 100 µA light-load assumptions on several nets. The approximately 1.1 mA FPGA HIGH loads, TPS3851 unspecified SET1/WDI current, raw health-node thresholds and analog reset behavior remain unqualified. Standalone receipts were not rewritten to imply that this later integrated loading had already been covered.

No finished card or manufacture release follows. Unassigned FPGA output/status/strobe endpoints, DIC/presence/tamper qualification, actual bank-B Ioff gating and readback, field permit-output driver, identity/slot behavior, connectors, self-test/recovery firmware, vendor FPGA timing and physical proof remain open. The repair is a concrete validated source advance; full circuit acceptance still requires another independent review and those implementation/measurement gates.
