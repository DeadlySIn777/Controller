from pathlib import Path
import sys,json,shutil
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity,xy,mm
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-facing-health-C80-dedicated-feed-r08/motherboard-facing-health-C80-dedicated-feed-candidate.kicad_pcb');PREF=Path('reports/motherboard-return-zoning-20261001/ROOT101-C79-actual-own-Source-Ground-search-r12/search.json');O=Path('reports/motherboard-return-zoning-20261001/ROOT101-facing-health-C79-own-domain-Ground-r13');assert not O.exists();O.mkdir();assert sha(B)=='01699de616bd217fa06de4ef63a81c478afe765014e4f0f95af9bb236ea5ef7e';assert json.loads(PREF.read_text())['candidates'][0]['Ground_mm']==[337.05,173.75]
inputs={str(q):sha(q)for q in[B,PREF,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};oldcu={u:identity(t)for u,t in cu.items()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldz=definitions(B);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldcl=native_pad_clusters(b,nets)
v=cu['4b393b84-561e-44d7-a13c-f7dd8ec81ce5'];t=cu['94bb0469-3da0-4a99-aede-4c078d864c83'];assert mm(v.GetPosition())==(337.4125,173.45)and v.GetNetname()==t.GetNetname()=='/LOGIC_GND';assert mm(t.GetStart())==(338.1625,173.45)and mm(t.GetEnd())==(337.4125,173.45);v.SetPosition(xy((337.05,173.75)));v.SetIsFree(True);t.SetEnd(v.GetPosition());changed=[v.m_Uuid.AsString(),t.m_Uuid.AsString()];wanted={u:identity(cu[u])for u in changed}
dest=O/'motherboard-facing-health-C79-own-domain-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for q in B.parent.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
pcbnew.SaveBoard(str(dest),b);g=json.loads((B.parent/'generation.json').read_text());g.update(input_sha256=inputs,exact_C79_modified_Cu_UUIDs=changed,new_C79_Ground_mm=[337.05,173.75],prior_C79_Ground_mm=[337.4125,173.45],actual_foreign_In4_FIELD_GND_projection_avoided=True);write(O/'generation.json',g);print('Exact C79 Ground annulus moved out of real foreign Source projection',flush=True);n=drc(dest,O,'native');counts=dict(errors=sum(r['severity']=='error'for r in n['violations']),warnings=sum(r['severity']=='warning'for r in n['violations']),ignored=len(n['ignored_checks']));write(O/'native-counts.json',counts);assert counts['errors']==counts['ignored']==0
after=pcbnew.LoadBoard(str(dest));after.BuildConnectivity();ac={q.m_Uuid.AsString():identity(q)for q in after.GetTracks()};assert set(ac)==set(oldcu)and all(ac[u]==val for u,val in oldcu.items()if u not in changed)and all(ac[u]==val for u,val in wanted.items());assert oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}and oldz==definitions(dest);now=native_pad_clusters(after,nets);assert clusters_survive(oldcl,now);write(O/'actual-Source-clusters.json',dict(passed=True,before=oldcl,after=now));assert all(sha(Path(q))==h for q,h in inputs.items());write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=changed,reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Move only the new C79 conventional Ground barrel and dedicated same-net cap leaf out of actual FIELD_GND Source-metal projection on In4. Actual drilled-land registration screen remains >=0.15 mm; no filled/capped process, Source/pose/land/old-copper/zone or rule change.'))
write(O/'receipt.json',dict(passed=False,before_board=str(B),before_sha256=sha(B),board=str(dest),board_sha256=sha(dest),native=counts,Source_clusters_preserved=True,actual_Source_collar_and_receiving_reference_proof_pending=True,manufacturing_ready=False));print(json.dumps(dict(board_sha256=sha(dest),**counts)),flush=True)
