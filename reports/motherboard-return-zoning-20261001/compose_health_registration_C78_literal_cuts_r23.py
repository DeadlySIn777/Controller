"""Compose disjoint reviewed actual health Cu/outline corrections once, then reprove current geometry."""
from pathlib import Path
import sys,json,copy,shutil,subprocess
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-return-zoning-20261001')]
import pcbnew
from hardware_build_assembly import parse,dump,children,child,value
from hardware_merge_bounded_pcb_delta import objects,dump_board,without_generated_fills,merge_reviewed_existing_zone_outlines
from hardware_map_motherboard_domains import sha,write,native,classify,positioned
from hardware_route_logic_return import identity,pad_identity
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_validate_motherboard_return_planes_r06 import validate
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
R=Path('reports/motherboard-return-zoning-20261001')
BASE=R/'ROOT101-facing-health-actual-Source-collars-r14/motherboard-facing-health-Source-collars-candidate.kicad_pcb'
C78=R/'ROOT101-facing-health-C78-terminal-barrel-r22/motherboard-facing-health-C78-terminal-candidate.kicad_pcb'
REG=Path('reports/motherboard-power-entry-20261001/ROOT101-health-six-registration-r366/motherboard-health-registration-candidate.kicad_pcb')
CUT1=R/'ROOT101-facing-health-seven-literal-unused-cuts-r16/motherboard-facing-health-seven-unused-cuts-candidate.kicad_pcb'
CUT2=R/'ROOT101-facing-health-one-followup-unused-cut-r20/motherboard-facing-health-one-unused-cuts-candidate.kicad_pcb'
CLEAN=R/'health-IO3-baseline-cleanup-r02/motherboard-health-unused-IO3-candidate.kicad_pcb'
O=R/'ROOT101-health-C78-registration-literal-cuts-r23';assert not O.exists();O.mkdir()
assert json.loads((C78.parent/'receipt.json').read_text())['passed']
assert json.loads((REG.parent/'receipt.json').read_text())['passed']
assert json.loads((R/'health-IO3-baseline-cleanup-independent-r01/receipt.json').read_text())['passed']
inputs={str(q):sha(q)for q in(BASE,C78,REG,CUT1,CUT2,CLEAN,C78.parent/'receipt.json',REG.parent/'receipt.json',R/'health-IO3-baseline-cleanup-independent-r01/receipt.json',Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
trees={str(q):parse(without_generated_fills(q.read_text()))for q in(BASE,C78,REG,CUT1,CUT2,CLEAN)};tree=copy.deepcopy(trees[str(C78)])
regscope=json.loads((REG.parent/'bounded-scope.json').read_text());delta=[]
for kind in('segment','via','arc'):
 old=objects(trees[str(BASE)],kind);new=objects(trees[str(REG)],kind);current=objects(tree,kind)
 for uid in sorted(set(old)|set(new)):
  first,last=old.get(uid),new.get(uid)
  if first is not None and last is not None and dump(first)==dump(last):continue
  assert first is not None and last is not None and dump(current[uid])==dump(first)
  tree[tree.index(current[uid])]=copy.deepcopy(last);delta.append(uid)
assert set(delta)==set(regscope['reviewed_copper_delta_UUIDs'])
zonechanges=[]
for first,last in((BASE,CUT1),(CUT1,CUT2)):
 scope=json.loads((last.parent/'bounded-scope.json').read_text())
 zonechanges+=merge_reviewed_existing_zone_outlines(trees[str(first)],trees[str(last)],tree,scope['reviewed_existing_zone_outline_deltas'])
pr=json.loads((CLEAN.parent/'proposal.json').read_text());zones=objects(trees[str(CLEAN)],'zone');nowz=objects(tree,'zone');ruleids=[]
for row in pr['regions']:
 uid=row['UUID'];assert uid not in nowz;tree.append(copy.deepcopy(zones[uid]));ruleids.append(uid)
dest=O/'motherboard-health-composed-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(C78.with_suffix(ext),dest.with_suffix(ext))
for q in C78.parent.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
dest.write_text(dump_board(tree));write(O/'generation.json',dict(input_sha256=inputs,before_board=str(BASE),exact_registration_Cu_UUIDs=delta,C78_Cu_scope=json.loads((C78.parent/'bounded-scope.json').read_text()),literal_zone_correction_sequence=zonechanges,exact_IO3_cleanup_rule_UUIDs=ruleids,cleanup_review=str(R/'health-IO3-baseline-cleanup-independent-r01/receipt.json')))
print('Native composed health correction refill',flush=True)
n=drc(dest,O,'native');counts=dict(errors=sum(v['severity']=='error'for v in n['violations']),warnings=sum(v['severity']=='warning'for v in n['violations']),ignored=len(n['ignored_checks']));write(O/'native-counts.json',counts);assert counts['errors']==counts['ignored']==0
b=pcbnew.LoadBoard(str(BASE));a=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();a.BuildConnectivity()
oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};newcu={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()}
c78scope=json.loads((C78.parent/'bounded-scope.json').read_text());allowed=set(delta)|set(c78scope['reviewed_copper_delta_UUIDs'])
assert all(newcu.get(u)==v for u,v in oldcu.items()if u not in allowed)
assert {q.m_Uuid.AsString():pad_identity(q)for q in b.GetPads()}=={q.m_Uuid.AsString():pad_identity(q)for q in a.GetPads()}
nets={q.GetNetname()for q in b.GetPads()if q.GetNumber()};oldcl=native_pad_clusters(b,nets);newcl=native_pad_clusters(a,nets);assert clusters_survive(oldcl,newcl);write(O/'all-prior-Source-clusters.json',dict(passed=True,before=oldcl,after=newcl))
S=Path('hardware/motherboard');parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,fn=native(S/'netlist.xml');ds,bar,_,_=classify(parts,nodes,nc);mp=positioned(a,parts,nodes,nc,fn,ds,bar);assert not mp['errors'];mp.update(actual_board_sha256=sha(dest));write(O/'domain-map.json',mp)
resource=validate(a,mp);resource.update(board_sha256=sha(dest));write(O/'full-native-resource-review.json',resource)
fps={f.GetReference():f for f in a.GetFootprints()};pads={(f.GetReference(),p.GetNumber()):p for f in a.GetFootprints()for p in f.Pads()if p.GetNumber()};decls={}
for owner in('U11020','U11026'):
 ret=pads[owner,'2'].GetNetname();decl=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4)
 decls.update({pads[owner,pin].GetNetname():decl for pin in('1','3')})
checker=ExactEndpointUnionCheck(a,decls);controls=[]
for t in a.GetTracks():
 if t.GetNetname()not in decls:continue
 try:r=checker.via(t,decls[t.GetNetname()])if t.Type()==pcbnew.PCB_VIA_T else checker.segment(t,decls[t.GetNetname()]);controls.append(dict(uuid=t.m_Uuid.AsString(),passed=True,review=r))
 except ValueError as e:controls.append(dict(uuid=t.m_Uuid.AsString(),passed=False,error=str(e)))
write(O/'actual-controls-proof.json',dict(passed=all(r['passed']for r in controls),board_sha256=sha(dest),margin_mm=.40,rows=controls))
manifest=json.loads((C78.parent/'current108-final-bypass-manifest.json').read_text());manifest['board_sha256']=sha(dest)
for g in manifest['owned_loops']:
 if g['ref']in('C11078','C11079','C11081'):g['explicit_registration_rebind_reason']='Exact six off-land barrel corrections and attached leaf endpoints separately reviewed; all current native annuli/corridors/Source receiving anchors rechecked.'
write(O/'current108-final-bypass-manifest.json',manifest)
run=subprocess.run([sys.executable,'tools/hardware_verify_owned_bypass_batch.py','--board',str(dest),'--owners','reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json','--receipt',str(O/'current108-final-bypass-manifest.json'),'--out',str(O/'current108-actual-strict-loop-proof.json')],capture_output=True,text=True)
(O/'current108-command.txt').write_text(run.stdout+run.stderr);write(O/'current108-status.json',dict(passed=run.returncode==0))
assert all(sha(Path(q))==h for q,h in inputs.items())
write(O/'receipt.json',dict(passed=not counts['warnings']and resource['passed']and all(r['passed']for r in controls)and run.returncode==0,before_board=str(BASE),before_board_sha256=sha(BASE),board=str(dest),board_sha256=sha(dest),native=counts,Source_clusters=True,resource_passed=resource['passed'],actual_controls_passed=all(r['passed']for r in controls),current108_passed=run.returncode==0,relative_global_power_pending=True,registration_final_combined_proof_pending=True,manufacturing_ready=False))
print(json.dumps(dict(board_sha256=sha(dest),native=counts,resources=resource['passed'],controls=all(r['passed']for r in controls),current108=run.returncode==0)),flush=True)
