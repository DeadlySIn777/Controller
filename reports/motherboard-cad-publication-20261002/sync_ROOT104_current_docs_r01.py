"""Replace current evidence paragraphs, preserving source decisions and exact prior docs."""
from pathlib import Path
import json,hashlib,os,re
root=Path.cwd();out=root/'reports/motherboard-cad-publication-20261002/ROOT104-current-docs-r01';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def prose(s):
 s=re.sub(r',(?=[A-Za-z])',', ',s)
 s=re.sub(r'\b(all|the|cover|baseline|revision|includes|with|is|at|of|in)(?=\d)',r'\1 ',s)
 s=re.sub(r'(?<=\d)(?=MHz\b|mm\b|ms\b)', ' ',s)
 s=re.sub(r'(?<=[;:,])(?=\d)', ' ',s)
 return s
ad='reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01/adoption.json'
full='reports/pre-hardware-validation-20261002/full-bypass-PROC-seeded-IS2-r08/report.json'
char='reports/pre-hardware-characterization-20261002/characterization-register-r06/requirements-and-coverage.json'
drill='reports/motherboard-pcb-integration-20261002/ROOT103-bypass-PROC-full-drill-SMD-r01/receipt.json'
erc='reports/motherboard-erc-20261002/source26-exact-warning-disposition-r01/receipt.json'
cost='reports/motherboard-cost-20260930/source-r26-2688-complete-cost-v11/README.md'
assert json.loads((root/ad).read_text())['adopted']
assert json.loads((root/'hardware/board_review/board-view.json').read_text())['current_revision']=='20261002-30'
receipt={}
for name in ['PROJECT_MEMORY.md','reports/ENGINEERING_STATUS.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','docs/CURRENT_ACCEPTANCE_GATES.md','hardware/board_review/README.md']:
 p=root/name;s=p.read_text(encoding='utf8');backup=out/name;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(p.read_bytes())
 link=lambda label,path:'['+label+']('+os.path.relpath(root/path,p.parent).replace('\\','/')+')'
 current='**Current adopted board — Source26/ROOT104, published CAD30:** '+link('Exact adoption',ad)+' and the published board share SHA-256 `70b71c36778e49600b77f382cf84df81ef3ac6dce442cc0e576b494d307979cc`. There are **2,688 footprints, 11,807 track/via items, 1,544 zones/rule areas and 3,508 required joins remaining**. Native and independent uncapped connectivity agree: 633 fully joined and 1,101 incomplete multi-pad nets, zero orphan copper. Native regular DRC is **0 errors/0 warnings/no ignored checks**; Source26 ERC is **0 errors/70 unsuppressed warnings**, with '+link('exact warning dispositions',erc)+'. The 48 controlled additions preserve all prior copper, lands, poses and zone definitions. Actual saved/refilled removal of all48 restores the baseline3521 joins. Scoped proofs cover120 bypass loops,245 receiving returns and188 Source-anchored filled resources. Source27 corrections remain staged; no Freerouting copper has been adopted.'
 validation=link('Fresh full r08',full)+' has **25 PASS, 9 BLOCKED, 1 physical NOT_RUN and 0 FAIL**, with **1,895 host and238 native KiCad cases passing**, five Windows symlink skips and all4,041 scoped source hashes unchanged. Fresh evidence includes2,048 actual SPI seeded trials in eight fault classes,18 reset/fault mechanical-model scenarios,the four-stage diagnostic IOL1 replay,the five-stage read-only IS2 CAP3 profile and eleven-stage stateful replay. These are compiled C/RTL and ideal-mechanics proofs,not complete HAL,target timing,electrical safety or measured hardware ratings.'
 characterize=link('Characterization r06',char)+' preserves all15 subsystem,22 fault and nine complete-machine requirements. No complete machine profile is yet validated. The original transport CAP3 gap and the bounded IS2 read-only implementation are distinct; the new profile deliberately remains unqualified and cannot authorize motion. Frozen CNC3 rate limits remain unchanged; the requested2MHz/channel target is not implemented/qualified. Complete IOL1 authority,record trust/provisioning,analog-chain convergence,vendor FPGA fit/timing and full-load operation remain open. The staged record-acquisition mapping exceeds the coarse T20 resource budget and is undergoing implementation optimization; HDL simulation alone does not prove capacity.'
 assembly=link('Current native drill/land audit',drill)+' finds **274 drilled vias intersecting277 same-net paste SMD lands**,zero foreign-net intersections and no added overlap in ROOT104. This lower bound excludes tangency and registration margins. Layout correction or exact qualified filled/capped fabrication and assembly is still required; tenting and clean ordinary DRC do not close it. The **460×340mm,six-layer,1.6mm** stackup remains provisional. Final routing,power distribution,complete20ms inhibit,mechanics,manufacturing outputs and physical validation are unfinished. **Manufacturing readiness remains false.**'
 costing=link('Unchanged Source26 partial BOM v11',cost)+' has known-priced consumed parts at1/10/100 units of **US$1,091.51/$877.37/$796.51**;105 exact MPNs are priced and185 MPNs/720 fitted pieces remain unpriced. Plug-in modules,screens,fabrication,assembly,programming/test,enclosure and packaging remain separate unknowns. This is not a complete product cost or PCBWay quote.'
 paragraphs=s.split('\n\n');replacements={
 '**Current adopted board —':current,'[Fresh full r07]':validation,'[Characterization r04]':characterize,'[Exact native drill/land audit]':assembly,'[Unchanged Source26 partial BOM v11]':costing}
 seen=set();new=[]
 for q in paragraphs:
  match=next((k for k in replacements if q.startswith(k)),None)
  if match:new.append(prose(replacements[match]));seen.add(match)
  elif q.startswith('**Current integrated implementation:**') or q.startswith('**Current implementation boundary:**'):
   new.append('**Current implementation boundary:** Source26/ROOT104 and CAD30 are bound above. All twelve motor interfaces and the required I/O remain on one motherboard. The current scoped routing evidence is120 bypass loops/245 receiving returns/188 filled resources;3508 joins remain. Source27 corrections,complete transport/providers/HAL,assembly,vendor fit/timing and physical qualification are open. Historical six-joint/two-encoder runtime remains distinct. No manufacturing release is implied.')
  elif q.startswith('- **Current engineering execution:**'):
   new.append('- **Current engineering execution:** Source26/ROOT104 is the adopted routing baseline above. Continue routing,Source27 corrections and actual CNC3/IOL1/HAL integration within the existing architecture. Freerouting runs are protected duplicate-board evaluations; their copper is not adopted without all native and regression gates.')
  elif q.startswith('- **Live physical CAD view:**'):
   new.append('- **Live physical CAD view:** revision20261002-30 matches ROOT104 exactly. It includes92 checked footprint land patterns and both native local model references,including the manufacturer compute socket. The exact candidate was rendered and visually inspected. It remains an incomplete,editable PCB.')
  else:new.append(q)
 assert len(seen)==5,(name,seen)
 s='\n\n'.join(new)
 if name=='reports/ENGINEERING_STATUS.md':s=s.replace('# Controller engineering status — 1 October 2026','# Controller engineering status — 2 October 2026',1)
 if name=='docs/CURRENT_ACCEPTANCE_GATES.md':
  s=re.sub(r'\*\*Current evidence boundary:\*\*.*?(?=\n\n)','**Current evidence boundary:** Source26/ROOT104 and CAD30 use the exact evidence above. The9 blocked full-bench stages and physical NOT_RUN remain open; no readiness follows from scoped passes.',s,count=1,flags=re.S)
 if name=='hardware/board_review/README.md':
  begin=s.index('## Current published revision:');end=s.index('## Historical published revision:',begin)
  s=s[:begin]+'## Current published revision: 20261002-30; working PCB: Source26/ROOT104\n\n'+link('Native KiCad project','hardware/board_review/revisions/20261002-30/motherboard-native-candidate.kicad_pcb')+', '+link('native render','hardware/board_review/revisions/20261002-30/motherboard-3d.png')+' and '+link('publication proof','hardware/board_review/revisions/20261002-30/publication.json')+' share the adopted board bytes. Publication reruns native DRC and uncapped connectivity; the499-item native display cap is not the3508 required-join total. The package retains92 checked footprint patterns and both local model references. This is an incomplete editable design,not a fabrication package.\n\n'+s[end:]
 p.write_text(s,encoding='utf8',newline='\n');receipt[name]=dict(before_sha256=sha(backup),after_sha256=sha(p))
(out/'receipt.json').write_text(json.dumps(dict(passed=True,documents=receipt,board='ROOT104',CAD='20261002-30',manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,updated=len(receipt))))
