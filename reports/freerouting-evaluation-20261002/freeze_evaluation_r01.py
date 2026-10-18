"""Record actual routing/import outcomes, without promoting process success to PCB success."""
from pathlib import Path
import hashlib,json
root=Path.cwd();base=root/'reports/freerouting-evaluation-20261002';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
names=['ROOT103-visual-actual-router-r01','ROOT103-visual-actual-router-r02','ROOT103-GPIO-config-convex-actual-router-r03','ROOT103-GPIO-config-bounded-fanout-actual-router-r04','ROOT103-GPIO-config-window-direct-actual-router-r05','ROOT103-visual-local-window-actual-router-r06','ROOT103-visual-local-diagnostic-actual-router-r07']
rows=[];inputs={}
for name in names:
 p=base/name/'receipt.json';d=read(p);inputs[str(p.relative_to(root))]=sha(p)
 rows.append(dict(trial=name,process_completed=bool(d['passed']),seconds=d['seconds'],session_sha256=d['session_sha256'],inputs_unchanged=d['inputs_unchanged'],error=d.get('error'),routing_accepted=False))
rej=base/'ROOT103-visual-local-native-import-r01/no-improvement-rejection.json';r=read(rej)
assert r['status']=='REJECTED_NO_IMPROVEMENT' and r['actual_added_signal_or_return_Cu']==0 and not r['actual_candidate_emitted']
ad=root/'reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01/adoption.json';a=read(ad)
board=Path(a['board']);published=root/'hardware/board_review/revisions/20261002-30/motherboard-native-candidate.kicad_pcb'
assert sha(board)==sha(published)==a['board_sha256']=='70b71c36778e49600b77f382cf84df81ef3ac6dce442cc0e576b494d307979cc'
inputs.update({str(p.relative_to(root)):sha(p)for p in [rej,ad,board,published,Path(__file__),base/'RouterSettings-v2.4.1.java']})
out=base/'evaluation-r01';out.mkdir(exist_ok=False)
result=dict(status='EVALUATED_NO_ACCEPTABLE_ROUTING_OUTPUT',routing_accepted=False,adopted_Freerouting_Cu=0,input_sha256=inputs,trials=rows,strict_native_import=r,live_working_board='ROOT104',live_required_joins=3508,live_board_sha256=a['board_sha256'],live_board_and_published_bytes_match=True,full_regression_for_empty_route_session='NOT_RUN: session rejected before any additive candidate; exact current board has separate fresh full r08 validation.',whole_board_complete=False,manufacturing_ready=False)
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
(out/'README.md').write_text('''# Freerouting evaluation — 2 October 2026

**Actual duplicate-board trials and native import completed; no Freerouting copper accepted.** The current board remains ROOT104/CAD30, with3,508 required joins. Its13-join improvement came from separately controlled routing, not Freerouting.

The test base is the exact ROOT103 board with11,759 copper objects. Protected source pads, placements, existing copper and manufacturing rules remain immutable. Power, FPGA escapes, clocks/CNC3/SPI, motor and encoder paths, analog, watchdog and permission routes were excluded from autorouter goals.

| Trial | Actual result |
|---|---|
| Initial visual run | Rejected startup/configuration attempt; retained. |
| Original whole-board visual export |900-second timeout, no session. |
| Convex full-board export | Independently covered every protected obstacle;900-second timeout. |
| Convex export with bounded fanout |900-second timeout; no session. Its0.50mm fanout search setting was inconsistent with ordinary0.60mm vias and was corrected in the successor, without changing native acceptance. |
| Legal polygon/window full-board export | Independent zero-undercoverage proof passed;900-second parsing timeout, no session. |
| Local30×30mm protected window | Parsed and ran four passes in113.21seconds. Wrote a real SES; both selected joins remained unrouted. |
| Same local window, diagnostic one-pass run |33.02seconds; exactly the same SES hash and zero new routing. |

The complete initial reviewed low-speed inventory contained64 rows, of which27 nets had48 unfinished joins. That does not mean all3,521 baseline joins were eligible for autorouting. The local workflow test selected only OBS8_INVERTED and OBS9_INVERTED and all four of their actual Source pads.

The initial KiCad filled-zone export contained110 fractured contours unsuitable as simple polygons. Successive report-only transformations retained conservative coverage. The final local export contains5,247 convex objects; independent reconstruction proves coverage of all7,053 original obstacles with no area tolerance. Space outside the local region is deliberately blocked. Native board geometry was never cropped or changed.

## Native import result

The strict importer rejected the actual session with `Session contains no new approved route geometry`. The SES network output is empty. Its native donor and no-route placement control both have zero copper: protected netless copper was omitted by the writer. **The donor must never replace the original PCB.** The additive workflow retains the exact original11,759 copper objects and accepts only separately validated additions. None existed here, so no candidate was emitted and no complete candidate regression was warranted.

Freerouting’s51,088 diagnostic violations belong to the restricted exported model. They are not KiCad DRC results and have not been established as the cause of the routing failure. Independent endpoint checks show that the four pad centers and outward F-layer escape envelopes are clear of polygon/reference-void blockers; complete native-metal path access remains under investigation.

One export-rule discrepancy was found: ordinary classes offered0.50/0.20mm and0.40/0.20mm vias as well as the required0.60/0.30mm. The importer rejects unauthorized new sizes. Future exports must restrict new route choices while retaining existing small-via padstack definitions. No new via was returned in these trials.

The current ROOT104 board has native regular DRC0 errors/0 warnings, zero orphan copper, and native/independent agreement on3,508 required joins. Its separate fresh full r08 run reports25 PASS,9 BLOCKED,1 physical NOT_RUN and0 FAIL. Neither the controller nor the manufacturing package is complete.

Official configuration reference: [Freerouting2.4.1 RouterSettings](https://github.com/freerouting/freerouting/blob/v2.4.1/src/main/java/app/freerouting/settings/RouterSettings.java). Exact local receipts, tool hashes, failed attempts and unchanged-input witnesses are retained beside this report.
''',encoding='utf8',newline='\n')
print(json.dumps(dict(status=result['status'],adopted_copper=0,live_board='ROOT104',required_joins=3508)))
