"""Remove the acute redundant same-rail diagonal at the actual U25 cap feed.

Retain its native UUID and connect it orthogonally into the existing same-net
vertical cap branch. No pour tolerance or DRC threshold is changed.
"""
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
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-U13-actual-Source-return-r05/motherboard-U25-U13-Source-return-candidate.kicad_pcb')
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-orthogonal-Source-feed-r06');assert not O.exists();O.mkdir()
assert sha(B)=='bc60c904ae1e4a8e4cdb915811182a43678abb0905a3a7a8f8d4935365d56e64'
inputs={str(q):sha(q)for q in[B,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};oldcu={u:identity(t)for u,t in cu.items()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldz=definitions(B);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldcl=native_pad_clusters(b,nets)
t=cu['d5258467-61e7-4fb2-b020-0b89d1d2a04e'];branch=cu['e7815e4d-590b-44a0-90fa-1224ae819e3f'];assert t.GetNetname()==branch.GetNetname()=='/motherboard_power_entry/FIELD_5V' and t.GetLayer()==branch.GetLayer()==pcbnew.B_Cu;assert mm(t.GetStart())==(332.5,192.65)and mm(t.GetEnd())==(332.087499,191.5);assert mm(branch.GetStart())==(332.087499,193.6)and mm(branch.GetEnd())==(332.087499,191.5)
t.SetEnd(xy((332.087499,192.65)));expected=identity(t)
dest=O/'motherboard-U25-orthogonal-Source-feed-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for q in B.parent.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
pcbnew.SaveBoard(str(dest),b);write(O/'generation.json',dict(input_sha256=inputs,modified_Cu_UUID=t.m_Uuid.AsString(),before=oldcu[t.m_Uuid.AsString()],after=expected,actual_retained_same_net_cap_branch=branch.m_Uuid.AsString(),primary_sliver_locator='ROOT101-U25-native-B-sliver-location-r01/location.json',no_DRC_tolerance_change=True))
print('Exact redundant diagonal repaired; native refill/DRC',flush=True);n=drc(dest,O,'native');counts=dict(errors=sum(r['severity']=='error'for r in n['violations']),warnings=sum(r['severity']=='warning'for r in n['violations']),ignored=len(n['ignored_checks']));write(O/'native-counts.json',counts);assert counts['errors']==counts['ignored']==0
after=pcbnew.LoadBoard(str(dest));after.BuildConnectivity();ac={q.m_Uuid.AsString():identity(q)for q in after.GetTracks()};assert set(ac)==set(oldcu)and all(ac[u]==v for u,v in oldcu.items()if u!=t.m_Uuid.AsString())and ac[t.m_Uuid.AsString()]==expected;assert oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}and oldz==definitions(dest);now=native_pad_clusters(after,nets);assert clusters_survive(oldcl,now);write(O/'actual-native-Source-cluster-proof.json',dict(passed=True,before=oldcl,after=now))
assert all(sha(Path(q))==h for q,h in inputs.items());write(O/'bounded-scope-from-U25-r05.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[t.m_Uuid.AsString()],reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Correct the exact redundant same-rail diagonal responsible for native B copper sliver. The unchanged UUID now meets the real retained FIELD5 vertical cap branch orthogonally. No pads, poses, Source, other copper, zones, tolerances or arrays change.'))
write(O/'receipt.json',dict(passed=counts['warnings']==0,full_health_qualification=False,before_board=str(B),before_sha256=sha(B),board=str(dest),board_sha256=sha(dest),native=counts,Source_clusters_preserved=True,manufacturing_ready=False));print(json.dumps(dict(board_sha256=sha(dest),**counts)),flush=True)
