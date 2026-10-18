"""Exact final C78 .15mm off-land correction, no part/Source/reference waiver."""
import sys,json,shutil,subprocess
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from hardware_map_motherboard_domains import sha,write,native,classify,positioned
from hardware_route_logic_return import identity,pad_identity,xy
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_stitch_owned_return_planes import definitions
from hardware_validate_motherboard_return_planes_r06 import validate
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-health-C78-registration-literal-cuts-r23/motherboard-health-composed-candidate.kicad_pcb');D=B.parent;O=D.with_name('ROOT101-health-final-C78-registration-r24');assert not O.exists();O.mkdir();assert sha(B)=='8015ebe8fef2c447db9126cdd44604e944186e60ebd52def8dbbc45d6060c03b'
M=D/'current108-final-bypass-manifest.json';S=Path('hardware/motherboard');inputs={str(q):sha(q)for q in(B,M,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),Path(__file__),S/'design.json',S/'netlist.xml')}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={q.m_Uuid.AsString():pad_identity(q)for q in b.GetPads()};nets={q.GetNetname()for q in b.GetPads()if q.GetNumber()};oldcl=native_pad_clusters(b,nets);cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
barrel='9d7ff79f-eaf2-47e4-b28d-6b7138e8acf8';terminal='0e678fe0-3353-45a1-ae9c-5e720d87de74';back='2c3fb5ed-2496-489e-9df0-6ddc143bd63b';ids=[barrel,terminal,back]
assert tuple(cu[barrel].GetPosition())==tuple(xy((343,176.65)))
for uid in(terminal,back):assert tuple(cu[uid].GetEnd())==tuple(xy((343,176.65)));cu[uid].SetEnd(xy((343,176.6)))
cu[barrel].SetPosition(xy((343,176.6)));cu[barrel].SetIsFree(True)
dest=O/'motherboard-health-final-registration-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for q in D.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
pcbnew.SaveBoard(str(dest),b);write(O/'generation.json',dict(input_sha256=inputs,before_board=str(B),before_board_sha256=sha(B),modified_Cu_UUIDs=ids,barrel_before_mm=[343,176.65],barrel_after_mm=[343,176.6],terminal_turn_preserved_mm=[342.8,175.85],reason='Move only the final new positive barrel and attached F/B endpoint leaves 50um upward to meet the actual fitted B SMD registration gap while retaining the legal SC6 escape and outside-antipad terminal turn.'))
write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=ids,reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Exact three actual C78 objects only; .15mm drill/SMD registration screen, all current Source/corridor/108/reference/power proof repeated without acceptance relaxation.'))
print('Native final C78 registration refill',flush=True);n=drc(dest,O,'native');assert not n['violations']and not n['ignored_checks']
a=pcbnew.LoadBoard(str(dest));a.BuildConnectivity();now={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()};assert set(now)==set(oldcu)and all(now[u]==v for u,v in oldcu.items()if u not in ids);assert oldpads=={q.m_Uuid.AsString():pad_identity(q)for q in a.GetPads()}and definitions(B)==definitions(dest);newcl=native_pad_clusters(a,nets);assert clusters_survive(oldcl,newcl);write(O/'all-prior-Source-clusters.json',dict(passed=True,before=oldcl,after=newcl))
parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,fn=native(S/'netlist.xml');ds,bar,_,_=classify(parts,nodes,nc);mp=positioned(a,parts,nodes,nc,fn,ds,bar);assert not mp['errors'];mp.update(actual_board_sha256=sha(dest));write(O/'domain-map.json',mp);resource=validate(a,mp);resource.update(board_sha256=sha(dest));write(O/'full-native-resource-review.json',resource)
pads={(f.GetReference(),p.GetNumber()):p for f in a.GetFootprints()for p in f.Pads()if p.GetNumber()};decls={}
for owner in('U11020','U11026'):
 d=dict(return_net=pads[owner,'2'].GetNetname(),reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4);decls.update({pads[owner,p].GetNetname():d for p in('1','3')})
checker=ExactEndpointUnionCheck(a,decls);rows=[]
for t in a.GetTracks():
 if t.GetNetname()not in decls:continue
 try:r=checker.via(t,decls[t.GetNetname()])if t.Type()==pcbnew.PCB_VIA_T else checker.segment(t,decls[t.GetNetname()]);rows.append(dict(uuid=t.m_Uuid.AsString(),passed=True,review=r))
 except ValueError as e:rows.append(dict(uuid=t.m_Uuid.AsString(),passed=False,error=str(e)))
write(O/'actual-controls-proof.json',dict(passed=all(r['passed']for r in rows),board_sha256=sha(dest),margin_mm=.4,rows=rows))
manifest=json.loads(M.read_text());manifest['board_sha256']=sha(dest);g=next(g for g in manifest['owned_loops']if g['ref']=='C11078');g['exact_modified_Cu_UUIDs']=list(dict.fromkeys(g.get('exact_modified_Cu_UUIDs',[])+ids));g['explicit_registration_rebind_reason']='Exact final positive barrel/endpoints move upward50um, preserving Source/SC6/corridor contract; actual all-current proof is required.';write(O/'current108-final-bypass-manifest.json',manifest)
command=[sys.executable,'tools/hardware_verify_owned_bypass_batch.py','--board',str(dest),'--owners','reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json','--receipt',str(O/'current108-final-bypass-manifest.json'),'--out',str(O/'current108-actual-strict-loop-proof.json')];run=subprocess.run(command,capture_output=True,text=True);(O/'current108-command.txt').write_text(run.stdout+run.stderr)
assert all(sha(Path(q))==h for q,h in inputs.items());write(O/'receipt.json',dict(passed=resource['passed']and all(r['passed']for r in rows)and run.returncode==0,board=str(dest),board_sha256=sha(dest),before_board=str(B),before_board_sha256=sha(B),native_errors=0,native_warnings=0,Source_Cu_pad_pose_and_zone_preservation=True,resource_passed=resource['passed'],actual_controls_passed=all(r['passed']for r in rows),current108_passed=run.returncode==0,combined_registration_and_global_power_pending=True,ROOT102_two_cap_composition_pending=True,manufacturing_ready=False));print(json.dumps(dict(board_sha256=sha(dest),resources=resource['passed'],controls=all(r['passed']for r in rows),current108=run.returncode==0)),flush=True)
