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
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-facing-health-U25-actual-composition-r07/motherboard-bounded-merged-candidate.kicad_pcb')
R=B.parent/'receipt.json';assert R.exists(),'Frozen exact composition required';assert sha(B)==json.loads(R.read_text())['board_sha256']
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-facing-health-C80-dedicated-feed-r08');assert not O.exists();O.mkdir()
inputs={str(q):sha(q)for q in[B,R,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};oldcu={u:identity(t)for u,t in cu.items()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(B);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};cl=native_pad_clusters(b,nets)
t=cu['d5258467-61e7-4fb2-b020-0b89d1d2a04e'];assert mm(t.GetStart())==(332.5,192.65)and mm(t.GetEnd())==(332.087499,192.65)and t.GetNetname()=='/motherboard_power_entry/FIELD_5V';t.SetStart(xy((332.087499,191.5)));t.SetEnd(xy((332.087499,191.85)))
n=pcbnew.PCB_TRACK(b);n.SetNet(t.GetNet());n.SetLayer(pcbnew.B_Cu);n.SetWidth(t.GetWidth());n.SetStart(xy((332.087499,191.85)));n.SetEnd(xy((332.5,192.65)));b.Add(n);added=n.m_Uuid.AsString();expected={t.m_Uuid.AsString():identity(t),added:identity(n)}
dest=O/'motherboard-facing-health-C80-dedicated-feed-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for q in B.parent.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
pcbnew.SaveBoard(str(dest),b);write(O/'generation.json',dict(input_sha256=inputs,modified_Cu_UUID=t.m_Uuid.AsString(),added_Cu_UUID=added,dedicated_cap_path_mm=[[332.087499,191.5],[332.087499,191.85],[332.5,192.65]],bend_to_actual_via_distance_mm=.900365,native_sliver_acute_angle_avoided=True,retained_old_distribution_branch='e7815e4d-590b-44a0-90fa-1224ae819e3f',distribution_is_not_part_of_qualified_local_cap_path=True))
print('Native dedicated C80 cap branch with exact via endpoint',flush=True);d=drc(dest,O,'native');counts=dict(errors=sum(v['severity']=='error'for v in d['violations']),warnings=sum(v['severity']=='warning'for v in d['violations']),ignored=len(d['ignored_checks']));write(O/'native-counts.json',counts);assert counts['errors']==counts['ignored']==0
after=pcbnew.LoadBoard(str(dest));after.BuildConnectivity();ac={q.m_Uuid.AsString():identity(q)for q in after.GetTracks()};assert set(ac)==set(oldcu)|{added}and all(ac[u]==v for u,v in oldcu.items()if u!=t.m_Uuid.AsString())and all(ac[u]==v for u,v in expected.items());assert oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}and oldzones==definitions(dest);now=native_pad_clusters(after,nets);assert clusters_survive(cl,now);write(O/'actual-Source-clusters.json',dict(passed=True,before=cl,after=now))
assert all(sha(Path(q))==h for q,h in inputs.items());write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[t.m_Uuid.AsString(),added],reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Exact dedicated C80 B cap-to-positive-via branch, with bend outside actual endpoint antipad and acute copper tip avoided. Existing long shared FIELD5 distribution preserved independently, not credited as this local bypass path. No Source/pad/pose/zone/array/rule/tolerance change.'))
write(O/'receipt.json',dict(passed=False,native=counts,before_board=str(B),before_sha256=sha(B),board=str(dest),board_sha256=sha(dest),actual_Source_preserved=True,remaining_new_C79_reference_warning_and_strict_controls_pending=True,manufacturing_ready=False));print(json.dumps(dict(board_sha256=sha(dest),**counts)),flush=True)
