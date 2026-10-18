"""Restore the real U13 Ground dependency after the off-land U25 correction.

This is a bounded low-current Source return escape, not a claim that the
U13 local high-frequency bypass loop is qualified.
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
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r04/motherboard-U25-two-local-barrels-candidate.kicad_pcb')
OLD=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb')
PREF=Path('reports/motherboard-return-zoning-20261001/ROOT101-U13-actual-Ground-native-preflight-r01/search.json')
GEN=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r04/generation.json')
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-U13-actual-Source-return-r05')
assert not O.exists();O.mkdir()
assert sha(B)=='5748851670cb1af0be698a0ddc4765603035b9a33b5b7ba813cc16af1f922861'
inputs={str(q):sha(q)for q in[B,OLD,PREF,GEN,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]}
assert sha(Path('hardware/motherboard/design.json'))=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();beforecu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};beforepads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};beforezones=definitions(B)
old=pcbnew.LoadBoard(str(OLD));old.BuildConnectivity();nets={p.GetNetname()for p in old.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(old,nets)
pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};source=pads['U11013','2'];ret=source.GetNetname();assert ret=='/motherboard_motors/FIELD_GND'
path=json.loads(PREF.read_text())['candidates'][0]['points'];assert path==[[333.8625,191.0],[334.8625,191.0],[334.8625,192.8],[333.4,192.8]]
added=[]
for start,end in zip(path,path[1:]):
 t=pcbnew.PCB_TRACK(b);t.SetNet(source.GetNet());t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(.25));t.SetStart(xy(start));t.SetEnd(xy(end));b.Add(t);added.append(t.m_Uuid.AsString())
dest=O/'motherboard-U25-U13-Source-return-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for q in B.parent.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
pcbnew.SaveBoard(str(dest),b)
write(O/'generation.json',dict(input_sha256=inputs,added_Cu_UUIDs=added,actual_Source_return_path_mm=path,return_net=ret,width_mm=.25,length_mm=4.2625,Source_pin='U11013.2',actual_Source_ground_via='9557a691-472b-4af0-87c3-b0e91cf52409',high_frequency_bypass_qualification=False))
print('Restored exact U13 same-field Source return; native refill/DRC',flush=True)
n=drc(dest,O,'native');counts=dict(errors=sum(v['severity']=='error'for v in n['violations']),warnings=sum(v['severity']=='warning'for v in n['violations']),ignored=len(n['ignored_checks']));write(O/'native-counts.json',counts)
assert counts['errors']==0 and counts['ignored']==0
after=pcbnew.LoadBoard(str(dest));after.BuildConnectivity();ac={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()};assert set(ac)==set(beforecu)|set(added) and all(ac[u]==v for u,v in beforecu.items());assert beforepads=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()};assert beforezones==definitions(dest)
now=native_pad_clusters(after,nets);assert clusters_survive(oldclusters,now),'Actual Source split remains';write(O/'actual-native-Source-cluster-proof.json',dict(passed=True,before_board_sha256=sha(OLD),before=oldclusters,after=now))
ap={(f.GetReference(),p.GetNumber()):p for f in after.GetFootprints()for p in f.Pads()if p.GetNumber()};co=after.GetConnectivity();items={t.m_Uuid.AsString():t for t in after.GetTracks()};ground=items['9557a691-472b-4af0-87c3-b0e91cf52409'];assert ground.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in co.GetConnectedItems(ap['U11013','2'])};assert ground.GetNetname()==ap['U11013','2'].GetNetname()
g=json.loads(GEN.read_text());scope=dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=g['exact_modified_Cu_UUIDs']+g['exact_added_Cu_UUIDs']+added,reviewed_added_zone_UUIDs=g['added_zone_UUIDs'],reviewed_scope_reason='Necessary off-land U25 low-current pair correction and exact attached positive leaves, plus actual U13.2 same-field Source return restoration. The old cap drill had physically provided this shared ground handoff. No Source/land/pose/rated-array/older-zone change; C80 receiving manifest explicitly rebinds, U13 bypass qualification is not claimed.')
write(O/'bounded-scope-from-health-r01.json',scope);write(O/'bounded-scope-from-U25-r04.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=added,reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Exact three-segment U11013.2 same-field Source ground dependency restored to the actual off-land U25 return barrel. Source continuity only; no U13 local bypass qualification.'))
assert all(sha(Path(q))==h for q,h in inputs.items())
write(O/'receipt.json',dict(passed=counts['warnings']==0,full_health_qualification=False,Source_clusters_preserved=True,before_board=str(B),before_board_sha256=sha(B),board=str(dest),board_sha256=sha(dest),native=counts,added_Cu_UUIDs=added,Source26_unchanged=True,Source27_adopted=False,manufacturing_ready=False))
print(json.dumps(dict(board_sha256=sha(dest),Source_preserved=True,**counts)),flush=True)
