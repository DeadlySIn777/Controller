"""Replace superseded current evidence; preserve exact previous documents in reports."""
from pathlib import Path
import json,hashlib,os,re
root=Path.cwd();out=root/'reports/motherboard-cad-publication-20261001/ROOT103-current-docs-r01';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ad='reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/adoption.json'
full='reports/pre-hardware-validation-20261001/full-health-stateful-plant-r07/report.json'
char='reports/pre-hardware-characterization-20261001/characterization-register-r04/requirements-and-coverage.json'
drill='reports/motherboard-pcb-integration-20261001/health-r31-full-drill-SMD-audit-r01/receipt.json'
plant='reports/controller-plant-20261001/actual-spi-reset-fault-plant-r06/receipt.json'
driver='reports/controller-plant-20261001/actual-C-driver-SPI-probe-r02/receipt.json'
iol='reports/cnc3-iol1-acquisition-20261001/diagnostic-replay-full-r01/report.json'
cost='reports/motherboard-cost-20260930/source-r26-2688-complete-cost-v11/README.md'
receipt={}
for name in ['PROJECT_MEMORY.md','reports/ENGINEERING_STATUS.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','docs/CURRENT_ACCEPTANCE_GATES.md','hardware/board_review/README.md']:
 p=root/name;s=p.read_text(encoding='utf8');original=s
 backup=out/name;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(p.read_bytes())
 link=lambda label,path:'['+label+']('+os.path.relpath(root/path,p.parent).replace('\\','/')+')'
 current='**Current adopted board — Source26/ROOT103, published CAD29:** '+link('Exact adoption',ad)+' and the published native board share SHA-256 `639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053`. There are **2,688 footprints, 11,759 track/via items, 1,544 zones/rule areas and 3,521 required joins remaining**. Native and independent uncapped connectivity agree: 633 fully joined and 1,101 incomplete multi-pad nets, zero orphan copper. Native regular DRC is **0 errors/0 warnings/no ignored checks**; Source26 ERC is **0 errors/70 unsuppressed warnings**. Six health-region component poses and exact reviewed copper/zone changes preserve all 5,899 prior Source-pad clusters and both ROOT102 capacitor corrections. The scoped proofs now cover 110 owned bypass loops, 225 receiving returns and 188 Source-anchored filled resources. The remote health producer and staged Source27 circuit corrections remain unfinished.'
 validation=link('Fresh full r07',full)+' has **22 PASS, 9 BLOCKED, 1 physical NOT_RUN and 0 FAIL**, with **1,887 host and 235 native KiCad cases passing**, five Windows symlink skips and all 3,765 scoped source hashes unchanged. It includes the eleven-stage stateful replay and nine original serial/mechanics scenarios. A later separately hashed '+link('18-scenario fault/reset replay',plant)+' passes, preserving physical-model position across FPGA counter reset and refusing restart after a fresh valid UPDATE. The '+link('four-stage diagnostic IOL1 replay',iol)+' also passes. These are disconnected compiled C/RTL/ideal-mechanics proofs, not complete HAL, target timing, actual electrical safety or hardware ratings.'
 characterize=link('Characterization r04',char)+' preserves all 15 subsystem, 22 fault and nine full-machine requirements. The '+link('actual original C-driver probe',driver)+' exposes missing CAP3 READ_PAGE support in the actual RTL and correctly remains inhibited. All nine complete machine profiles remain unrun. Frozen CNC3 MAX_RATE still permits 195,312.5 steps/s at assumed 50 MHz; the requested 2 MHz target remains unimplemented/unqualified. Full analog convergence and the encrypted ADC model remain open, with all failed analyses retained. Ordinary I/O, factory identity and full output authority are separate from read-only diagnostic acquisition.'
 assembly=link('Exact native drill/land audit',drill)+' finds **274 drilled vias intersecting 277 same-net paste SMD lands**, with zero foreign-net intersections. This is a lower bound excluding tangency and registration margins. Layout correction or a qualified filled/capped assembly process is required; tenting and clean ordinary DRC do not close it. The **460 × 340 mm, six-layer, 1.6 mm** stackup remains provisional. Final routing, power distribution, complete 20 ms inhibit, vendor fit/timing, mechanics, manufacturing outputs and physical validation are unfinished. **Manufacturing readiness remains false.**'
 costing=link('Unchanged Source26 partial BOM v11',cost)+' has known-priced consumed parts at 1/10/100 units of **US$1,091.51 / $877.37 / $796.51**; 105 exact MPNs are priced and 185 MPNs / 720 fitted pieces remain unpriced. Plug-in modules, screens, fabrication, assembly, programming/test, enclosure and packaging are separate unknowns. This is not a complete product cost or PCBWay quote.'
 paragraphs=s.split('\n\n')
 oldprefixes=('**Latest verified increment','[Updated characterization]','[Native drill/land screening]','**Bounded simulation evidence:','**Current CNC3 rate boundary:','**Current CNC3 rate contract,','**CNC3 rate boundary:')
 paragraphs=[x for x in paragraphs if not x.startswith(oldprefixes)]
 s='\n\n'.join(paragraphs)
 heading,body=s.split('\n',1)
 if name=='reports/ENGINEERING_STATUS.md':
  body='\n\n'+body[body.index('## Historical runtime and circuit records'):]
 if name=='PROJECT_MEMORY.md':
  # Replace only the two obsolete current implementation bullets; decisions stay intact.
  body=re.sub(r'^- \*\*Live physical CAD view .*?(?=\n- \*\*)','- **Live physical CAD view:** revision 20261001-29 now matches ROOT103. Its local resources include 92 checked footprint land patterns and the restored manufacturer compute-socket STEP model. CAD28 omitted that model despite its older prose; exact restoration is recorded in the CAD29 preparation receipt. The image is freshly rendered and visually inspected; the app queued the right-panel opening.\n',body,flags=re.M|re.S,count=1)
  body=re.sub(r'^- \*\*Current engineering execution .*?(?=\n- \*\*)','- **Current engineering execution:** Source26/ROOT103 is the adopted routing baseline described above. The actual source retains all twelve motor interfaces and required I/O on one motherboard; historical six-joint/two-encoder runtime is separate. Continue routing, Source27 electrical corrections and actual CNC3/IOL1/HAL integration without replacing the architecture.\n',body,flags=re.M|re.S,count=1)
 if name=='docs/CURRENT_ACCEPTANCE_GATES.md':
  body=re.sub(r'\*\*Current evidence boundary \(1 October 2026\):\*\*.*?(?=\n\n)','**Current evidence boundary:** Source26/ROOT103 and CAD29 are bound to the current evidence above; all routing/electrical/target/physical gates remain open as specifically recorded. Older source/PCB/runtime counts are historical.',body,count=1,flags=re.S)
 if name=='hardware/board_review/README.md':
  begin=body.index('## Current published revision:');end=body.index('## Historical published revision:',begin)
  viewer='## Current published revision: 20261001-29; working PCB: Source26/ROOT103\n\n'+link('Native KiCad project','hardware/board_review/revisions/20261001-29/motherboard-native-candidate.kicad_pcb')+', '+link('native render','hardware/board_review/revisions/20261001-29/motherboard-3d.png')+' and '+link('publication proof','hardware/board_review/revisions/20261001-29/publication.json')+' use exactly the adopted board bytes. The publication reruns native DRC and independent uncapped connectivity; the capped 499-item display is not the routing total.\n\nNinety-two actual footprint land patterns and all referenced local project models are packaged. The manufacturer compute-socket STEP omitted by CAD28 is restored from the exact vendor source; CAD29 was rendered and visually inspected. The app queued the side-panel opening; visible navigation is not independently confirmed. Earlier attempted and published revisions remain retained. This is an editable incomplete design, not a fabrication package.\n\n'
  body=body[:begin]+viewer+body[end:]
 s=heading+'\n\n'+'\n\n'.join([current,validation,characterize,assembly,costing])+body
 p.write_text(s,encoding='utf8',newline='\n')
 assert b'\r\r\n'not in p.read_bytes()
 receipt[name]=dict(before_sha256=sha(backup),after_sha256=sha(p))
(out/'receipt.json').write_text(json.dumps(dict(passed=True,documents=receipt,board='ROOT103',CAD='20261001-29',manufacturing_ready=False),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,updated=len(receipt))))
