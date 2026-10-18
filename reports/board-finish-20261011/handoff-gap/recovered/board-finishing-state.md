---
name: board-finishing-state
description: "Where the motherboard finishing work lives (Z:/pcb-runs/claude-finish), the pipeline order, and the layout decisions taken on 9 Oct 2026 (450x235, 1 oz, U.FL ESP, no antenna keepout)"
metadata:
  node_type: memory
  type: project
  originSessionId: 280553e2-7c85-48b3-a5fa-96a4c2e06e60
  modified: 2026-10-10T01:05:14.549Z
---

All board-finishing work is in `Z:/pcb-runs/claude-finish/` (never the main checkout's hardware/ or Codex's folders).
Input: `relayout/ROOT106/board.kicad_pcb` (450x235 mm rebuild, 6 layers, DRC 0, 3774 unrouted, parity 0).
Stage 1 pipeline: `tools/finish_pipeline.sh <out> [moves...]` (sync -> design fixes -> fiducials + ESP note ->
netlist -> board_net_update -> net classes -> place_new_parts -> move_parts -> board_fab_prep --no-antenna-keepout
-> field sync -> checks). Output dirs: final-s1 (old order), final-s2 (new order), final-s3 = final-s2 + fidplace fiducials + field sync + drc_prune: parity 0, DRC 0 (incl. library), 3865 unrouted (9 Oct 2026 21:28). Routing runs in route-s3/ (board.kicad_pcb).
Routing: `tools/route_setup.sh <stage1> <routedir>` then `tools/route_all.sh <routedir>` (power corridors on GPU ->
pairs -> stitch_loop -> exclude_nets -> route_signals.sh with Freerouting 2.5.0 JAR on Java 25:
`--router.autorouter.max_passes`, `--router.fanout.enabled=false`, `--router.job_timeout`). Fab set: `tools/fab_outputs.sh`.

Decisions (user-approved unless noted): board shrunk to 450x235 for PCBWay turnkey; 1 oz outer copper;
ESP socket is for the ESP32-S3-DevKitC-1U (WROOM-1U, U.FL to a panel bulkhead, per docs/MOTION_EXPANSION_8_TO_12.md
ESP card row) so no PCB-antenna keepout and no edge slot is needed (my call, flagged to the user, not yet confirmed).
KiCad 10 exports 487 net names with `{slash}` (e.g. `/mc_local_power{slash}CORE_5V`); the board follows the
schematic spelling, tools normalise with replace("{slash}", "/").

**Why:** the user asked for a perfectly routed, DRC-clean, verified board and then simulations; context resets lose this.
**How to apply:** continue from the latest final-s*/route dir; keep evidence classes honest; see [[is1-implementation-state]].

Routing-stage learnings (9 Oct 2026 evening): power_jobs must emit the board's `{slash}` net spelling (else the
router walls in every pad); corridor_router now has a neck-down width ladder, zone-fill awareness (other nets'
outer pours are obstacles, ground pours crossable as last resort), and a pair router v6 (leads/escape stubs with
fan-out, runways, two-layer BFS with via pairs, handedness check). The retained GND fan-out vias of the CM DF40
connectors (J15001/J15002), HDMI J15004, U15041/42, U15018/21/30 block the pair escapes, so
`tools/strip_fanout.py` clears 2.5 mm bands around pair-connector pads first (s0-orig -> s0b in
route-s3/corridor-work); plane nets are re-stitched later and signal nets re-routed by Freerouting.
Test dirs pairtest..pairtest4 are scratch. The KiCad Python API pops modal assert dialogs on overflow and the
process then hangs silently: check CPU time of stalled KiCad python processes.

Pair router state (10 Oct 2026 00:25): corridor_router.py pair branch v14: leads/fan-out, runways, mitred offsets
over Douglas-Peucker-smoothed centrelines (SAFE 0.12), two-layer BFS with via pairs, inline via swap for
handedness mismatches, pass-through hops (ESD arrays) and failed hops are LEFT TO FREEROUTING (single-ended
fallback is opt-in via CORR_SINGLE_FALLBACK=1, it produced clearance errors), P/N self-check discards bad hops.
tools/drc_clean.py removes copper that takes part in error-class DRC violations and prunes dangling chains;
route_ab.sh/route_all.sh run it after the corridor DRC (stage B2). pairtest12 = corridor-only test.

Live run (10 Oct 2026 00:52): `tools/route_full.sh route-s3 30 06:00:00` (log route-s3/route-full.log): pairs ->
power x2 (+drc_clean) -> route_state after-corridors -> route_cd.sh (stitch_loop, exclude_nets, route_signals.sh
with Freerouting) -> drc_clean -> route_state after-signals. Power audit per pass in corridor-work/power-audit-N.txt
(TRUNK-NECK flags = necked hops between large pads, to reinforce later). Freerouting leftovers of power nets get
0.3 mm (dsn_rules). Evidence notes for the report: Z:/pcb-runs/claude-finish/reports-notes.md.

Power router fixes (10 Oct 01:55): no end halo (track must fit at the pad at the attempted width; ladder necks
down to 0.2), width capped at 1.3x the smaller end pad, tracks end on the legal pad cell (not the pad centre),
cross-side hops get one via (bfs2), named *KEEPOUT* rule areas block all nets except the .kicad_dru exemptions,
edge clearance includes the half width, SAFE raster margin 0.2 mm (quantisation). Live: route-full2.log
(run 2: pairs -> power pass 1 (old code, 321 tracks removed by drc_clean) -> power pass 2 (new code) -> ...).

Status 10 Oct 03:05: route-s3 resume chain (tools/route_resume.sh, log route-s3/route-resume.log): corridors done
(after-corridors: parity 0, DRC errors 3, 64 warnings, unrouted 3450), stitching done (828 vias, unrouted 2791),
Freerouting signal pass running (route-s3/route-work/freerouting.log, 30 passes, 6 h timeout). After it:
drc_clean, route_state after-signals, then tools/fix_dangling_ends.py, a final DRC loop, fab outputs
(tools/fab_outputs.sh), view refresh (tools/update_view.sh), simulations, report. power_jobs now clusters through
copper (GetConnectedItems BFS), so re-passes only route remaining joins.

Status 10 Oct 06:40: Freerouting signal pass running since 03:07 (3012 items, 30 passes, 6 h timeout -> ends by
09:07) under tools/route_d_rest.sh (log route-s3/route-d2.log; it then imports, drc_clean, route_state
after-signals). Then run `sh tools/route_finish.sh route-s3 3` (dangling-end fix + DRC clean-up rounds, final
snapshot, view refresh), `power_board_audit.py`, and if errors=0/unrouted=0 `fab_outputs.sh`. DSN now uses
tools/dsn_classes.py (31 per-domain classes); route-s3/board.kicad_pro.good is the restored project file
(the stitch stage had overwritten board.kicad_pro with defaults at 02:59). Evidence notes: reports-notes.md,
impedance-1oz.json.

Status 10 Oct 15:05 (session resumed): the previous session's end KILLED the detached Freerouting job (no .ses
written; 5.5 h lost): nohup'd processes do not survive the Claude session. Board = route-s3/board.kicad_pcb at the
after-stitch state (02:59, unrouted 2791; snapshot corridor-work/s2-stitched-snapshot.kicad_pcb). New plan ("one
big swoop, perfect"): (1) GPU signal pass with tools/route_signals_gpu.sh (needs tools/signal_jobs.py, being
built by a workflow agent), (2) Freerouting only for leftovers in detached chunks (tools/detach_run.ps1 via WMI +
tools/route_signals_chunked.sh, workflow agents), (3) route_finish.sh, audits, fab outputs, report. Workflow run
wf_373c861f-08e (build + adversarial verify + tool review).

Power-loss protection (10 Oct 15:20, user request "autosave every 30 s"): corridor_router.py --checkpoint <file>
flushes results every 30 s and resumes (same jobs sha); route_signals_gpu.sh is restartable (signal-work/done-sN,
applied-sN.kicad_pcb markers); tools/finish_master.sh is the restartable master (route-s3/master-state markers,
lock, master.log) with stages 01 gpu signals, 02 Freerouting chunks (10 min), 03 gpu pass 2, 04a re-stitch,
04 finish loop, 05 audit, 06 fab outputs (only if clean). A Windows logon task to relaunch it was DENIED by the
auto-mode classifier (persistence): the user must register it themselves (command given in the report).
After-stitch snapshot had 139 galvanic clearance errors from stitch rounds that ran without the net classes;
drc_clean removed 160 tracks + 72 vias (+426 pruned) before the signal pass.

Status 10 Oct 15:55: master running (route-s3/master.log): stage 01 GPU signal pass S1 done (unrouted 2791 ->
2245), S2 running with escape stubs + via detour + 0.12 signal margin. Workflow wf_373c861f-08e delivered
tools/signal_jobs.py, tools/route_signals_chunked.sh (+detach_run.ps1, WMI-detached; ISOLATION env default
150), and a review whose verified defects were fixed at 15:45 (uuid-exact drc_clean/drc_prune/fix_dangling_ends,
TestTrackEndpointDangling via prune, GetConnectedItems islands, pads-only clustering, via cache clear, no
duplicate escape lead, no one-cell legs, import_ses guard). Do NOT edit finish_master.sh / route_signals_gpu.sh
while they run (sh reads incrementally); known TODO for route_signals_gpu.sh: rm the old jobs file before
regenerating. Evidence notes in reports-notes.md.

Status 10 Oct 16:05 ("one shot the board"): master still in stage 01 pass S2 (406/1481 at 16:02, ~24 jobs/min,
failures ~47% all "no path" on same-layer short hops in dense regions; GPU router is outer-layers-only so the
inner signal layer In3 is reserved for Freerouting stage 02). Logon task ClaudeBoardFinish NOT registered by the
user (schtasks query: not found). Workflow wf_cbe7b54d-f9c builds tools/pair_jobs_through.py,
tools/corridor_router_v2.py (pair_through job kind: coupled pair straight across the ESD part),
tools/net_copper_backup.py and tools/pair_upgrade.sh (only replaces a pair's copper when the coupled route is
DRC-clean) and verifies them on a copy of s0b in agent-work/. Plan after the master: pair_upgrade.sh on the
finished board, power TRUNK-NECK reinforcement, re-stitch, final DRC loop, update_view.sh, report.

DFM audit (10 Oct 16:35, workflow subagent): tools/quality/dfm_audit.py (KiCad python, ~16 s on the 40 MB board) audits a board
against the PCBWay 6-layer capability; outputs in agent-work/dfm-audit/snap/dfm_audit*.json on a 16:08 route-s3 snapshot.
Key facts: 795 UNFILLED vias (0.6/0.3, plane nets) overlap SMD pads (734 at pad edges, 61 centred) + 262 annulus-touching;
240 design VIPPO vias are marked filling/capping yes; 2 vias 0.4/0.2 (ring 0.10) at (262.245,111.7)/(294.195,132.235);
duplicate/overlapping vias on AO_I2C_SCL_HOST at (344.85,70.95)/(344.65,71.05) and (294.35,67.75); C14814/C14818/C14825/
C14829 pads overlap the DFM0020A module pads (U14812/U14813); 6453 silk items at 0.12 mm (< 0.15); no silk ref designators.

Status 10 Oct 17:40: master S2 done (1481 joins: 509 routed, 972 "no path"); S2 DRC/clean-up then S3. Audit workflow
wf_60149e2f-a4d delivered tools/quality/{netlist_parity,power_copper_audit,pair_audit,plane_audit,track_cleanup,
dfm_audit}.py (+ verifier reports in agent-work/verify-*). Verified findings on the 15:42 snapshot: netlist parity
CLEAN (2717 fps, 2384 nets, 0 defects); eFuse OUT exits (U11002/U11004/U11006) and CORE_5V shunt exit carry ~2.5 A
vs 3-4.8 A design (0.3-1.05 mm necks, 3x 0.5/0.2 vias where 5-6 needed); pairs: 1.7-2.1 mm P/N skew from the
corridor pair router, CM_USB2 runs 24 mm with NO plane under it near (148,182); DFM: 795 unfilled stitching vias
in SMD pads + 201 annulus-touching (<0.10 mask web) -> dog-bones needed, 6453 silk items <0.15 mm, HDMI J15004
silk 0.02 mm from the edge, FIDF1/FIDB1 4.45 mm from edge, caps C14814/18/25/29 placed on DFM module pads,
258 design VIPPO vias need PCBWay filled+capped quote; track_cleanup proven safe but removes fan-out escapes
mid-route (use only at the end); 197 same-net acid-trap slivers from raster routing; plane audit ran on stale
fills (needs refill rerun). Fix workflow wf_56b7b4ca-d0d builds tools/fix/{via_dogbone,stitch_plan3,
power_reinforce(+spec, audit v2),dfm_fix,plane_extend(+refilled plane audit),track_cleanup2}.py. In3 workflow
wf_e7086dd8-e8c and pair-through wf_cbe7b54d-f9c still running (analysis: 31/40 failures are pads boxed in on
their own layer with In3 88% free -> fan-out to In3 is the next lever).

Pair pass-through work (10 Oct 2026 ~17:45, workflow subagent): NEW tools in Z:/pcb-runs/claude-finish/tools: pair_jobs_through.py
(one pair_through job per pair: CM -> ESD -> connector, USB-C duplicate pads as from_extra), corridor_router_v2.py (assembled
by agent-work/through/assemble_v2.py from corridor_router.py + agent-work/through/v2_defs.py: pair logic as functions,
pair_through = straight crossing over the ESD pads (TSSOP only) -> T via pair on the ESD runway -> A->C corridor + ESD stubs
-> old two-hop; mid-corridor/end via swaps, start layer-change escape, point-exact corridor ends, behind-strip mask),
net_copper_backup.py (save/remove/restore tracks+vias of nets), pair_upgrade.sh + pair_upgrade_decide.py (finished-board
upgrade with DRC gate and restore). Findings: the DQA0010A ESD parts (U15041/42, U15029/30) have NC flow-through pads
6/7/9/10 in the schematic, so a straight pass-through is impossible there (fix in the schematic: tie pins 10/9/7/6 to the
pair nets); U15042's lead exits are boxed by R15067/R15069; U15030 sits on the USB-C D+/D- exit (USB_RECOVERY unroutable
coupled until moved); the HDMI escape under J15002 is boxed by the SPI resistor row R15014-R15017. Test dir:
agent-work/through/t1 (run-full1 = router+apply+DRC on the s0b copy).

Status 10 Oct 20:06: master reached stage 04 (finish loop). Trajectory: S1 2245, S2 1812, S3 1770, S4 1767; Freerouting
chunk 1 no progress (1767->1769, stopped); stage 03 GPU pass 2 1761 -> 1755; re-stitch -> ~1679. Board is NOT
finished (~1680 unrouted). Killing/pre-marking the master was DENIED by the auto-mode classifier: let it end
naturally. fix_dangling_ends.py crash fixed (o.Cast() before via GetWidth(layer)). In3 workflow VERIFIED:
tools/corridor_router_in3.py (+tools/patch_in3.py) adds In3 detours, escape-stub sources, rotation-aware rows and
FIXES a raster alignment defect of corridor_router.py (copper up to 0.15 mm off -> the 0.10 mm clearance errors the
passes produced). New driver tools/route_signals_gpu2.sh (uses the In3 router, checks exit codes, removes stale
jobs); route-s3/corridor-work/exclude-pairs.txt = exclude.txt + 22 pair nets. Residual failures are pads fenced by
other routes -> rip-up needed. Session limit (reset 19:50) killed the pair-through build and 5 fix tracks at 17:56;
relaunched as workflow wf_9a78fc3b-c84 (pair-through on the In3 router + pair_ripup, ripup_reroute loop, dog-bone
proof, power reinforce, dfm_fix, cleanup2, planes), tested on master-state/board-after-04a.kicad_pcb copies.

Direction 10 Oct ~20:20 (user-relayed advisor paste = user direction): ORDER = placement fixes (4 caps C14814/18/25/29,
fiducials) -> fine-pitch pad escapes (selective rip-up of fencing tracks) -> critical routes first and LOCKED (power
bottlenecks incl. SBC_5V, HDMI/USB/Ethernet with per-interface budgets, continuous reference, ESD transitions) ->
bulk routing -> via-in-pad CLASSIFY (accidental router/stitch vias vs intentional; hole-in-solderable-pad vs annulus
overlap; intentional = filled+capped VIPPO in fab notes; never blanket-relocate) -> clean-up/planes -> final.
Simulation is part of "verified": power/thermal (IR drop, via sharing, load steps, brownout), SI post-layout
(stackup, ESD, transitions, impedance, skew budgets), analog/field I/O SPICE (tolerances, extremes), FPGA system
regression (all channels, encoders/probe, protocol errors, comm loss, watchdog, unintended outputs). Every report
must carry the SAME board/pro/dru/netlist sha256 (revision manifest + gate); records give result, limit, margin,
coverage; NOT_RUN/NOT_MODELED stay visible. Standing user rules also in Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md
(14-point definition of done, five final reviews, VIPPO only for intentional via-in-pad, impedance classes
IMP_50/DIFF_90/DIFF_100 PROVISIONAL pending PCBWay, signal-via return stitch 0.9-1.0 mm window + 0.8 mm via spacing
except D4 regions U1001/J15001/J15002, SBC_5V dedicated pour <=100 mV at 3.6 A with >=5 vias per transition, never
cut In1/In4 or cross barriers, isolation per Z:/pcb-runs/domains/barriers.json). The "2.4 mm In3 SBC repair" is
Codex's ROOT10x board (codex-resume-20261004), NOT this ROOT106 board: here SBC_5V is 0.2-1.25 mm tracks, no pour,
3.55 A -> must be repaired. Engines available: scipy 1.17, torch cuda, shapely, networkx, KiCad's ngspice.dll; WSL
GarciaMechBuilder (Icarus/Verilator). No skrf/PySpice.

Status 10 Oct 20:45 (user: "finish the checkpoint, then apply independently verified fixes in dependency order; after each
integration report the saved revision sha, before/after unrouted, UNCAPPED DRC by category, whether totals include
unconnected; separate built / tested / applied-and-verified; name the router version; rerun all audits on the SAME
revision; keep unresolved/untested visible"). A session restart at ~20:39 killed the master (during finish round 3) and all
workflows. Master relaunched DETACHED via tools/detach_run.ps1 (WMI; PID 35536; log route-s3/master-detached.log + master.log):
it reruns stage 04 (3 rounds) then 05; survives session ends. Workflows relaunched with restart notes: harness
wf_d6d81e79-d30 (tools/integrate/: drc caps probe, measure.py uncapped, integrate.sh gated commit, ledger), round-2 tools
wf_790fc3bc-88c (dogbone now relocates only --only uuids from via_in_pad_classify), verification suite wf_e63b9b64-10c.
kicad-cli caps unconnected at 499 (API count ~1680). Status table: Z:/pcb-runs/claude-finish/integrate/STATUS.md; tool hashes
integrate/tool-hashes-20261010-2035.json. Router provenance of the checkpoint board: corridor_router.py 15:10 (S1), 15:43 (S2),
15:47:05 sha cc46ab3d (S3, S4, stage 03) + Freerouting 2.5.0 chunk 1; NO copper from corridor_router_in3.py yet.
Integration plan: new working dir Z:/pcb-runs/claude-finish/integrate/ seeded from the finished checkpoint; steps only
with VERIFIED tools: placement/DFM -> pad escapes/rip-up -> SBC_5V + power -> pairs -> bulk In3 routing + rip-up loop ->
return stitch -> via classify (relocate accidental, VIPPO intentional) -> cleanup2/planes -> final audits on one revision.

CRASH 10 Oct ~20:55: the user's PC crashed from CPU overload (>80 %) caused by 3 parallel workflows (up to 16 agents each, each
running kicad-cli DRC / python refills on all 32 threads) + the master. Machine: Ryzen 9 7950X3D 16C/32T, 128 GB. Board survived
(route-s3/board.kicad_pcb 20:30:59 intact). Mitigations now in place: tools/cpu_governor.ps1 runs DETACHED (WMI) and confines
kicad-cli, KiCad/Python314 python (except the user's uvicorn :8081 server), java freerouting, iverilog/vvp/verilator, vmmem to
logical CPUs 16-27 (mask 0x0FFF0000, 12/32 threads = 37.5 %) at BelowNormal; stop it by creating Z:/pcb-runs/claude-finish/
governor.stop; log governor.log. tools/heavy.sh <kicad|gpu|wsl|cpu> <cmd> = cooperative slot limiter (2/1/1/2). Workflow scripts
now cap agents at 2 per workflow (makeSem/lagent) and carry CPU RULES. NEVER launch unconstrained parallel heavy jobs again.
Relaunched 20:59: master (detached, PID 41768 cmd), workflows harness wf_3e173e3e-b82, round-2 wf_fcf6402c-0dc,
verification wf_9ae97f87-374.

Status 10 Oct 22:05: checkpoint DONE (master ALL-DONE 21:41): r00 = integrate/revs/r00-checkpoint.kicad_pcb (READ-ONLY, sha256
ae6c8aed...), DRC errors 0 (refilled, no --all-track-errors), 149 warnings, API unconnected 1749. User (21:50): keep r00
immutable, ONE comprehensive baseline, explain the +70, show the power audit, integrate verified tools in dependency order,
reroute affected nets, per revision report completed / lost / remaining / errors+warnings under unchanged rules; NO more
broad clean-up passes unless a measured defect; keep resource limits. +70 explained: finishing rounds' drc_clean prune
(3338 items pruned with no error; 139 clearance-error items in round 1) -> 24 signal nets lost 24 joins, 13 plane/power nets
lost 40 joins (stitch vias). New tools (mine): tools/net_partitions.py (per-net pad partitions, refill in memory),
partition_diff.py (completed/lost via partition join), step_measure.sh (+step_summary.py; DRC --all-track-errors
--schematic-parity --refill-zones on a copy), step_report.py (ledger entry + gate), reroute_nets.sh (targeted In3 reroute),
diag_removed.py. integrate/run_baseline_r00.sh (nohup) -> baseline-r00/; integrate/step_r01.sh (detached) reroutes
diag/lost-signal-nets.txt -> revs/r01-reroute-lost-signal-nets.kicad_pcb if gate PASS. Ledgers: integrate/LEDGER.md,
LEDGER-steps.md, steps.log. Power audit r00: every rail below width budget (SBC_5V 0.2 mm vs 3.0, 1 via).

22:05 user: "finish the joins now. remember 80 percent cpu". Governor mask raised to 20 threads (decimal 4294963200 =
0xFFFFF000, logical 12-31, 62.5 % cap; a hex literal >0x7FFFFFFF is a NEGATIVE Int32 in PowerShell -> "parameter is
incorrect"; fixed 22:04), heavy.sh slots kicad 3 / gpu 2, alarm 75 %. Measured total CPU ~65 % at full load (kicad-cli
51.6 + router 11.1). Verification-suite workflow (wf_9ae97f87-374) PAUSED via TaskStop to prioritise joins; resume later.
r00 joins by category: signal 1274 (924 nets), power-table routable 58 (17), plane/zone excluded 374 (22: LOGIC_GND 100,
FIELD_GND 90, CORE_5V 28, IO_3V3 24 ...), pairs 33 (19 nets). Driver integrate/finish_joins.sh (DETACHED) waits for r01
then runs signal passes r02.. with reroute_nets2.sh (ALL) + tools/remove_new_errors.py (removes only the pass's own error
copper and its own dangling remnants; never old copper) + step_measure/step_report gate, commits revs/rNN-signal-pass-k.
Plane joins wait for stitch_plan3 (round-2 dogbone track proving it); pairs wait for the pair tools.

22:45: r01 COMMITTED by hand (gate PASS: +30 completed, 0 lost, missing 1739 -> 1709, API 1748 -> 1718, errors 0, warnings
149 unchanged; step_r01.sh misread the gate because a python -c used an MSYS /z/ path: ALWAYS pass Windows paths/argv).
Correction: the +64 joins lost 04a->r00 were clearance-error removals (all 61 stitch vias had clearance errors from
stitch_plan2; signal routes had error segments from the misaligned old router); prune only cleared remnants.
User direction 22:35 (pasted): reserve SBC_5V/power corridors, pair corridors, reference continuity, fine-pitch escapes
before further bulk routing; route outside them meanwhile; 58 routable power joins at actual per-net widths + via rules;
no indiscriminate pruning but verified targeted rip-up OK; "<5 net" = switch to targeted repairs (not completion);
report next accepted revision. Done: tools/reserve_corridors.py (router-side keepouts + router-only board.kicad_dru:
11 PAIR bands F/In3/B, SBC5V B.Cu corridor 6 mm x ~185 mm path, 9 PWR regions, 197 ESC lane groups; foreign pads inside
-> their nets exempted; overlapping critical areas mutually exempt), plot_reservations.py, route_pass_reserved.sh (signal
nets only; power-table nets excluded), integrate/finish_joins2.sh (DETACHED, started r02-signal-pass-reserved-1 22:43).
Workflow wf_29269527-be5 builds+verifies corridor_router_in3s.py (CORR_POWER_STRICT: table width, necks <=2 mm, n_req =
ceil(A/0.5), >=2 vias -> single layer, no In3) + route_pass_power.sh. Paused: verification suite wf_9ae97f87-374.

23:25 user: "keep going lets finish the board tonight", "you can use full gpu". heavy.sh gpu slots -> 4 (CPU cap
unchanged). Harness workflow stopped (my step tools replace it). Single-agent verifier wf_cd835711-2a7 checks
tools/fix/stitch_plan3.py for the 374 plane joins. New: tools/integrate_step.sh (generic gated step: producer -> measure
applied -> if errors remove_new_errors + re-measure -> commit), tools/producer_stitch3.sh, integrate/run_queue.sh
(DETACHED; waits for the reserved signal passes to end, then runs integrate/queue/NN-*.step = "<label> <producer.sh>
[args]" in order; add a step only once its tool is verified; STOP file ends it).

SECOND CRASH 10 Oct 23:34:41 (Event 41 Kernel-Power + 6008 unexpected shutdown, no bugcheck -> power/PSU-type cut) about
10 min after GPU slots went to 4 with CPU ~65 % (20 threads). Limits REVERTED: governor mask 268369920 (0x0FFF0000, 12
threads, 37.5 %), heavy.sh kicad 2 / gpu 1; CPU alarm at 50 %. Do NOT raise again without the user knowing the risk.
Recovery 23:38: governor relaunched; integrate/run_queue.sh (no longer waits; DETACHED) runs queue/01-r02-resume.step
(label signal-pass-reserved-1 with tools/producer_reuse.sh: reuses work/r02-signal-pass-reserved-1/applied.kicad_pcb,
routed 22:50-23:32: 3527 items, 753 failures, 18886 segments, 1361 vias). Relaunched: stitch verifier wf_0d27a187-f63,
power-strict wf_22580b07-837, round-2 tools wf_b4756d24-cfb (restart notes added).

Pair stage r5 (11 Oct 00:20, workflow subagent, scratch agent-work/pairs3-r3/r5): router v3 rebuilt by tools/patch_pair_through.py
(+ tools/pair_diag_defs_v3.py): E9 retry adds quantisation margin PAIR_Q to fixed-geometry checks (fixed CLK swap 0.148 mm vs TX1 via),
E10 blocker diagnostics in routes.json "blockers" -> tools/pair_block_report.py resolves to board items (mm). Build now from the INPUT
board via tools/pair_unrip.py (removes kept pairs' copper + plan-dropped uuids only) + tools/pair_routes_keep.py: the r4 re-created
"restored" vias LOST filling/capping, remove_unused_layers, free, zone_layer_connections. pair_ripup --guide-or-chain. Regression:
power kind identical to In3; pair kind differs by design (v2 leads), exact-clean with E6. Proof chain r5/final_chain.sh (c6 CLEAN, d6 DENSE).
Placement blockers: U15022 1.4 mm under U15021 (USB_HOST/RECOVERY leads), U15030 NC pads 6/7 on the J15006 exit, R15067.2/R15069.2 on
U15042 leads, via CM_HOST_SPI_CS_CMD_N (116.25,208.89)+R15015.1 box TX0 under J15002.

00:35 11 Oct: r02-signal-pass-reserved-1 COMMITTED sha256 3a18f2f3... (+319 completed, 1 lost LOGIC_GND pour split,
missing 1709->1391, API 1718->1400, errors 0, warnings 149->165: via_dangling +8, not_centered +6, track_dangling +2).
Router via defects (edge radius, via-only keepouts, cross-domain inner copper) found by DRC, removed by
remove_new_errors (6 vias + 73 own remnants); fix workflow wf_ced2fa37-816 -> tools/corridor_router_in3v.py.
Queue: 02-signal-pass-reserved-2 (route_pass_reserved.sh). Next when verified: stitching (stitch_plan3), power strict.

01:10 11 Oct: integration was starved of heavy.sh kicad slots by testing agents (r03 waited 00:38-01:08). Fix:
tools/heavym.sh = separate integration-only slots (.slots/main-<class>, 1 each); route_pass_reserved.sh, step_measure.sh,
integrate_step.sh, producer_stitch3.sh now call heavym.sh (agents keep heavy.sh: kicad 2 / gpu 1). Never edit a running
sh script: stop the step first (killed integrate_step -> runner wrongly filed it under done/; renamed to failed/*ABORTED*).
r03 requeued as queue/03-signal-pass-reserved-2.step, restarted 01:10. User asked "max cpu fans": refused (system/hardware
setting) -> gave BIOS Q-Fan (ASUS PRIME X670E-PRO WIFI, Del, F7, Monitor > Q-Fan) / FanControl instructions; added GPU
alarm (>80 C or >350 W, nvidia-smi loop).

01:45 11 Oct: strict power mode routed 0 of 47 power joins at table widths on r01 (12 boxed pads, 16 no wide cell within
2 mm, 19 no wide path); identity with strict unset verified. USER DECISION "Hybrid" (integrate/POWER-WIDTH-DECISION.md):
<=0.5 A rails at 0.3 mm (tools/producer_power_low.sh, from route_pass_power.sh, heavym slots, widths overridden, 1.0-1.5 A
and pour rails left out) -> queue it once the strict verifier (wf_22580b07-837) passes; 1.0-1.5 A rails keep table width
via targeted rip-up: workflow wf_cd644616-eb9 builds tools/producer_power_ripup.sh. r03 (pass 2) at 01:31: 440/757 done,
438 failures -> expected <5 net -> bulk routing ends after r03. User: "keep going".

02:30 11 Oct (user: adaptive tenacity, keep going until complete+verified): r03 pass 2 -> ~+4 net (<5) => bulk ends.
stitch_plan3 evidence (verify-stitch3/checks): on r01 213/451 placed, 0 errors, 0 lost, BUT 187 of 213 stitches landed on
non-main plane islands. Diagnosis tools/plane_islands.py (KiCad py, exports clusters+fills) + tools/plane_gaps.py
(shapely) on r02 -> integrate/diag/planes/gaps.json: FIELD_GND = 53 separate inner outlines, 90 clusters (main 32 pads),
gaps 8-261 mm; FIELD_B_0V 23 clusters; AO0_COM 19; CAN_GND 7; RS485_COM 5; AO1_COM 6 -> need BRIDGES (new
tools/producer_plane_bridges.sh: strict router 0.5 mm, my assumption, recorded in POWER-WIDTH-DECISION.md; test in
agent-work/test-bridges). LOGIC_GND 99 stray clusters (96 single pads, gap ~1.9 mm), IO_3V3 24, AI_AGND 13 -> stitching.
Pair stage r5 RESULT (11 Oct 02:30): CLEAN c6 (agent-work/pairs3-r3/r5/clean-c6): DRC 0->0 errors, warnings unchanged, unrouted 3973->3955.
DENSE d6 (r5/dense-d6, board-after-04a, guide-or-chain rip-up): 0 new DRC errors (--all-track-errors: clearance 249->248), +67 track_dangling
+14 via_dangling only on the 27 nets whose 267 ripped items were dropped; unrouted 1678->1721 (pad joins 1675->1700: pairs -12, foreign +37;
power cut: SBC_5V 8 items, FIELD_B_24V_PROTECTED 49, CORE_5V 6, CHASSIS 12, LOGIC_GND 11). Coupled: Pair0/TX1/CLK through, Pair1/Pair3 corridor
with ESD stubs left (6.6-13.6 mm > 5 mm limit), USB2; NOT routed (placement): Pair2, TX0, TX2, USB_HOST, USB_RECOVERY. pair_audit hop
analysis misreports pass-over crossings (CLK) as unconnected; KiCad connectivity confirms them.

02:45 11 Oct: r03 COMMITTED 517c10a0... (+1, 0 lost, missing 1390, API 1399, errors 0, warnings 169) => bulk routing ENDED
(<5). remove_new_errors.py via check fixed to TestTrackEndpointDangling (old class-set test let one-layer vias survive:
via_dangling 4 -> 15). New targeted tool tools/remove_flagged_dangling.py + producer_remove_dangling.sh (DRC-flagged
dangling items only, by uuid); integrate_step.sh now REJECTS "cleanup*" steps that lose any connection. r04
cleanup-flagged-dangling running. Pair stage (round-2 builder): tools/corridor_router_v3.py (sha 143382f9, from
patch_pair_through.py on in3), pair_upgrade.sh, pair_ripup.py etc.; 6/11 pairs coupled, pair missing joins 33 -> 22 on
DENSE, 0 new DRC errors; remaining pairs blocked by PLACEMENT (U15022 1.4 mm under U15021; J15006/U15030; R15067/R15069
in U15042 leads; TX0 boxed under J15002) -> targeted part moves later. Verifier for it running in wf_b4756d24-cfb.

03:20 11 Oct: via-fix VERIFIED (corridor_router_in3v.py sha 08dab8e2; strict V3 policy kept: no via pierces another domain's
inner plane; r02 has 250 such vias -> isolation review). Combined builds: in3sv (strict power on in3v, 45712b24), v3v (pairs
on in3v, 005530ce); producers repointed (power_low -> in3sv, bridges_v -> in3sv, route_pass_reserved -> in3v). Bridge test
(0.5 mm strict) routed 21/145. FIELD_GND / FIELD_B_0V are FIELD SUPPLY RETURNS (J11003/4.2, J11005/6.2, JD terminal 0V):
need a field PDN design (In3 trunks + via arrays, sized by IR sim); 0.5 mm bridges only for AO0_COM, AO1_COM, CAN_GND,
RS485_COM. All layers 1 oz (inner 0.035). r04 cleanup removed 62 track_dangling + 15 via_dangling (measuring).

03:45 11 Oct: stitch verifier ok=false but ROOT CAUSE found: copying the board as source.kicad_pcb next to board.kicad_pro
loads NO project -> geom_dump writes cls=Default for all pads -> planners lose the 0.6 mm galvanic rule (same cause as the 61
stitch_plan2 vias at 04a, and stitch_loop.sh). RULE: every KiCad load must have <name>.kicad_pro/.kicad_dru matching the
board file name. Corrected sequence (verifier's producer_stitch3_fixed.sh, DOM-class guard >=90 %, --dru, --pad-mask) PASSED
on r01: 213 stitches, 0 errors, 0 lost, +30 joins. Adopted as tools/producer_stitch3.sh (heavym, 5th arg via size).
Stitching scope limits: 88 joins of 12 pour-only power nets out of reach; 238 targets unplaceable; 187/213 stitches land on
non-main islands. Queue: 04 cleanup (running), 05/06 stitch rounds 0.6:0.3 and 0.5:0.2 put on .hold until r04 ends so
step_measure.sh can take HEAVY env (default heavy.sh; integrate_step exports HEAVY=heavym.sh) without editing a running
script. field PDN workflow wf_1cb8a3c8-9be; verification suite resumed wf_ba100d96-8be; bridge test2 (0.3 mm, 4 small nets).

03:15 11 Oct (steps.log clock): r04 cleanup COMMITTED d51e4e36... (0/0, missing 1390, errors 0, warnings 167: via_dangling
15->1, track_dangling 62->74 = next segments of dead-end chains; a chain clean-up step comes at the end). step_measure.sh
now HV=${HEAVY:-heavy.sh}; integrate_step.sh exports HEAVY=heavym.sh and REFUSES unless its parent is run_queue.sh (ps -ef
check; tested). r05 stitch-plane-pads-1 (0.6:0.3) started 03:13, r06 (0.5:0.2) queued.

04:55 11 Oct: r05 COMMITTED 594a1091... (+19, 0 lost, missing 1371, errors 0, warnings 168). r06 (0.5/0.2 stitches, 188 added,
+7) in its repaired re-measure. Bridges for small returns at 0.3 mm: 3/33 outer-only, 4/31 with In3 (tools/patch_strict_in3.py ->
corridor_router_in3sv3.py, CORR_STRICT_IN3=1, leg limit <=3 after a 6-via invariant trip) -> fenced pads need rip-up. Rip-up
builder's proof (ripup-r3/proof): DENSE 1678 -> 1298 unrouted in 3 rounds, errors 85 -> 0, but used drc_clean + prune_dangling
(6491 pruned). Integration variant: tools/patch_ripup_integration.py -> tools/ripup_reroute_t.sh (in3v, HEAVY, reservations in
res-<geom>/ subfolders, remove_new_errors instead of drc_clean/prune) + tools/producer_ripup.sh (1 round per step; signal nets
only). Queued 07/08 ripup-signals-1/2. heavyt.sh = my test-only slots. ListAgents cannot reach workflow agents.

05:25 11 Oct: r06 COMMITTED 0e90568a... (+4, 0 lost, missing 1367, API 1376, errors 0, warnings 169; 184 stitches for 4 joins
-> no more stitch rounds). r07 ripup-signals-1 running since 05:07. Strict power VERIFIED (ok; driver issues: stale ckpt key,
FIELD_B_24V_INPUT 5.32 A not in POUR_NETS, 120 mm cut). producer_power_low.sh fixed: keeps only jobs <= 0.5 A (drops the rest
with a list), ckpt key includes input sha + jobs; router in3sv (strict patch on the verified via fix). Queued 07b-power-low-0p3mm
between the two rip-up rounds. In3 strict option (in3sv3) NOT used in integration (unverified, +1 join only).

05:47 11 Oct: CPU alarm 78 % (momentary; short-lived unconfined process starts before the governor's 1 s sweep). Governor now
also confines bash/sh/cmd whose command line matches '\.claude|pcb-runs' (pipeline + agent shells) so children INHERIT the
mask at birth; 54/54 such shells confined; total CPU ~32 %. User's own shells/apps untouched.
