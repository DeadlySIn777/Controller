import sys,json,collections,shutil
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_stitch_owned_return_planes import definitions
from hardware_merge_bounded_pcb_delta import objects,parse,without_generated_fills,dump
base=Path('reports/motherboard-pcb-integration-20261001/source26-return-plane-r51/motherboard-bounded-merged-candidate.kicad_pcb')
p=Path('reports/motherboard-return-zoning-20261001/source26-root51-reference-conflicts-r03/motherboard-new-reference-conflicts-repaired-candidate.kicad_pcb')
out=Path('reports/motherboard-return-zoning-20261001/source26-root51-reference-conflicts-reviewed-r04')
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir();dest=out/p.name
shutil.copy2(p,dest)
for s in('.kicad_pro','.kicad_dru'):shutil.copy2(p.with_suffix(s),dest.with_suffix(s))
for v in p.parent.iterdir():
 if v.is_dir()and(v.suffix=='.pretty'or v.name=='3dmodels'):shutil.copytree(v,out/v.name)
 elif v.name=='fp-lib-table':shutil.copy2(v,out/v.name)
for n in('generation.json','native.json','native.txt','deferred-native-source-graph-proof.json'):
 q=p.parent/n
 if q.exists():shutil.copy2(q,out/n)
bs=[pcbnew.LoadBoard(str(q))for q in(base,dest)]
cs=[{t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}for b in bs]
retired={'22bb7970-7f8a-48b1-a00d-ced6aec2c839','556fca79-c649-4f73-b8d5-cb47da61a1db','d55efe31-b2c5-4c4e-9a3e-8afa1e4a95f2','6d6b64a9-595a-4566-a9f8-a9cba473219f'}
records=json.loads((out/'generation.json').read_text())['exact_repairs'];changed={u for r in records if r['action']=='move_exact_new_source_escape'for u in(r['via_uuid'],r['track_uuid'])}
assert set(cs[1])==set(cs[0])-retired
assert all(cs[1].get(u)==v for u,v in cs[0].items()if u not in retired|changed)
assert {p.m_Uuid.AsString():pad_identity(p)for p in bs[0].GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in bs[1].GetPads()}
assert definitions(base)==definitions(dest)
# The thirteen prior electrical isolation corrections are already inherited from r51, unchanged by this repair.
trees=[parse(without_generated_fills(q.read_text()))for q in(base,dest)];delta=[];derived=[]
for kind in('segment','via','arc'):
 old,new=[objects(t,kind)for t in trees]
 for u in set(old)|set(new):
  if u not in old or u not in new or dump(old[u])!=dump(new[u]):
   delta.append(u)
   if u not in retired|changed:
    assert kind=='via'
    f=lambda v:dump([r for r in v if not(isinstance(r,list)and r[0]=='zone_layer_connections')])
    assert f(old[u])==f(new[u]);derived.append(u)
scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Exact independent r51 repair: four newly added standalone reference drills retired, two newly added real source-ground vias and their paired F branches relocated. All other current51 actual Cu/pads/poses/zone definitions remain exact, including the thirteen already reviewed isolation corrections. Two actual short local CMOS source branches stay unchanged pending disjoint rated FIELD_GND B trunk jogs. This is a joint WIP donor, not a clean/adoptable PCB.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(delta),reviewed_added_zone_UUIDs=[])
write(out/'bounded-scope.json',scope)
d=json.loads((out/'native.json').read_text());errors=[r for r in d['violations']if r['severity']=='error']
receipt=dict(before_board=str(base.resolve()),before_board_sha256=sha(base),board_sha256=sha(dest),exact_repairs=records,derived_annulus_metadata_only_UUIDs=derived,all_current51_other_native_Cu_and_pads_poses_zone_definitions_preserved=True,full_source_cluster_annulus_proof_deferred_until_two_rated_trunk_jogs=True,native_errors=len(errors),native_DRC_types=dict(collections.Counter(r['type']for r in d['violations'])),ignored_checks=d['ignored_checks'],scope_sha256=sha(out/'bounded-scope.json'),passed=False,manufacturing_ready=False)
write(out/'receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k not in('exact_repairs','derived_annulus_metadata_only_UUIDs')},indent=2))
