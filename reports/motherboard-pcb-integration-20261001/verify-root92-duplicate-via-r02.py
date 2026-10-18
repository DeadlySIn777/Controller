"""Literal identical-barrel union and actual Source paths after duplicate removal.

The r01 audit is preserved as failed: two coincident via objects supplied each
other with apparent six-layer contacts. A via peer is not a power-plane feed.
This audit requires identical native primitive definitions (except UUID),
retained F/B physical contacts, all real Source clusters and clean native DRC.
"""
from pathlib import Path
import sys,json,copy
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as ordinary
from hardware_route_logic_return import identity,pad_identity
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_merge_bounded_pcb_delta import zone_definition
e=ordinary.engine
p=Path('reports/motherboard-pcb-integration-20261001')
before_path=p/'source26-BankA-health-supply-merged-trial-r91/motherboard-bounded-merged-candidate.kicad_pcb'
out=p/'source26-BankA-health-duplicate-via-repair-r92';after_path=out/before_path.name
remove='00ab4e38-02eb-4059-9a89-1b617985437c';keep='864617ea-0ed9-4c88-b0bb-1017d6e7da65'
before_tree=e.parse(before_path.read_text());after_tree=e.parse(after_path.read_text())
def via_without_uuid(tree,u):
 n=next(n for n in e.children(tree,'via')if e.value(e.child(n,'uuid')[1])==u)
 return [v for v in n if not(isinstance(v,list)and v[0]=='uuid')]
assert via_without_uuid(before_tree,remove)==via_without_uuid(before_tree,keep)==via_without_uuid(after_tree,keep)
assert not any(e.value(e.child(n,'uuid')[1])==remove for n in e.children(after_tree,'via'))
def zones(tree):return {e.value(e.child(n,'uuid')[1]):zone_definition(n)for n in e.children(tree,'zone')}
assert zones(before_tree)==zones(after_tree)
b=pcbnew.LoadBoard(str(before_path));a=pcbnew.LoadBoard(str(after_path));b.BuildConnectivity();a.BuildConnectivity()
old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};current={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()}
assert current=={u:d for u,d in old.items()if u!=remove}
assert {p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in a.GetPads()}
clusters=clusters_preserved(source_clusters(b),a)
v=next(t for t in a.GetTracks()if t.m_Uuid.AsString()==keep)
contacts=[a.GetLayerName(l)for l in a.GetEnabledLayers().CuStack()if physical_reference_contact(v,l,a.GetConnectivity())]
assert contacts==['F.Cu','B.Cu']
ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in a.GetPads()}
source=ps['C11055','1'];assert source.GetNetname()==v.GetNetname()=='/motherboard_power_entry/FIELD_5V'
assert source.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in a.GetConnectivity().GetConnectedItems(v)}
drc=e.read(out/'drc.json');assert not drc['violations']and not drc['ignored_checks']
inputs=[before_path,after_path,out/'drc.json',out/'proposed-exact-delta.json',Path(__file__),p/'repair-root91-duplicate-health-via-r01.py',p/'root92-duplicate-repair-command.txt']
e.write(out/'receipt.json',dict(passed=True,input_sha256={str(f):e.sha(f)for f in inputs},board_sha256=e.sha(after_path),before_sha256=e.sha(before_path),removed_exact_duplicate_UUID=remove,identical_retained_barrel_UUID=keep,exact_native_barrel_primitive_except_UUID_preserved=True,geometric_union_of_barrels_unchanged=True,actual_F_B_contacts=contacts,actual_supply_SOURCE='C11055.1',all_prior_SOURCE_clusters=clusters,all_other_Cu_pads_poses_and_zone_definitions_preserved=True,earlier_r01_six_layer_contact_assertion_rejected='Duplicate via peer contacts were incorrectly counted as real inner power-plane connections. No inner FIELD5 power-plane feed is credited.',native_errors=0,native_warnings=0,ignored_checks=[],track_via_count=len(a.GetTracks()),full_health_and_bypass_review_required=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,board_sha256=e.sha(after_path),actual_contacts=contacts)))
