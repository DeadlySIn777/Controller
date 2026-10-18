"""Independent native proof of one F/In2 permission path and retained power."""
from pathlib import Path
import json,sys
sys.path[:0]=[str(Path('tools').resolve()),str(Path(__file__).parent.resolve())]
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_route_critical_digital_wip_r03 as c
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_owned_bypass_loops_wip_r03 as w
import check_io3_backbone_preservation_r05 as power
from hardware_validate_return_bridge_sources import review as ground_review
from hardware_route_logic_return import identity,pad_identity
e=o.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81/motherboard-bounded-merged-candidate.kicad_pcb')
OUT=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root81-OUT-PERMIT-r06')
DEST=OUT/'motherboard-OUT-PERMIT-common-In1-candidate.kicad_pcb'
MAP=Path('reports/motherboard-domains-20261001/source26-OUT-PERMIT-r06-r01/domain-map.json')
CONTROL=Path(__file__).parent/'io3-relative-power-screen-native-r05/receipt.json'
controls=e.read(CONTROL);assert controls['passed']and controls['helper_sha256']==e.sha(power.__file__)
plan=e.read(OUT/'proposed-groups.json');man=e.read(OUT/'manifest.json');assert len(plan['groups'])==1;g=plan['groups'][0]
assert g['source_pair']==['R14401.1','U14402.1']and len(g['new_copper_UUIDs'])==9
frozen={str(p.resolve()):e.sha(p)for p in(BASE,DEST,MAP,CONTROL,OUT/'proposed-groups.json',OUT/'manifest.json',OUT/'native.json',Path(__file__),Path(power.__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
o.INPUT_BOARD=BASE;o.MAPPING=e.read(MAP)
assert o.MAPPING['input_sha256'][str(DEST.resolve())]==e.sha(DEST)
source=o.frozen_review_check(man,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
known=w.reviewed_wip_warnings(e.read(BASE.parent/'drc.json'),e.read(BASE.parent/'baseline-disposition.json'),e.sha(BASE));native=e.read(OUT/'native.json')
assert not w.new_route_defects(native,known)and not native['ignored_checks']
before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(DEST));before.BuildConnectivity();after.BuildConnectivity()
population,_=e.native_source_check(after,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
old={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};actual={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}
assert all(actual.get(u)==v for u,v in old.items())and set(actual)-set(old)==set(g['new_copper_UUIDs'])
assert {p.m_Uuid.AsString():pad_identity(p)for p in before.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}
clusters=c.clusters_preserved(c.source_clusters(before),after)
def joined(board):
 board.BuildConnectivity();pads={p.m_Uuid.AsString():p for p in board.GetPads()};p,q=[pads[u]for u in g['source_pad_UUIDs']]
 assert p.GetNetname()==q.GetNetname()==g['net']
 return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}
assert joined(after)and not joined(before)
returns=o.actual_return_check(after,set(g['signal_UUIDs']),man['nets'])
assert all(row['intended_reference_layers']==['In1.Cu']for row in returns['actual_signal_via_reference_audits'])
grounds=ground_review(after,[dict(net='/LOGIC_GND',new_copper_UUIDs=g['ground_UUIDs'])],o.MAPPING['pads'])
powerproof=power.review(before,after);e.write(OUT/'actual-IO3-power-geometry-proof.json',powerproof)
tree=e.parse(DEST.read_text());remove=set(g['new_copper_UUIDs']);cut_tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in('segment','via','arc')and e.value(e.child(v,'uuid')[1])in remove)]
cut_path=OUT/'actual-physical-route-cut.kicad_pcb';cut_path.write_text(authority.dump_native_board(cut_tree)+'\n');cut=pcbnew.LoadBoard(str(cut_path));assert not joined(cut)
assert all(e.sha(p)==h for p,h in frozen.items())
e.write(OUT/'review.json',dict(passed=True,input_sha256=frozen,board_sha256=e.sha(DEST),source_scope=source,source_population=population,actual_source_pair=g['source_pair'],actual_pair_closed=True,actual9_new_copper=g['new_copper_UUIDs'],old_exact_copper_and_lands_preserved=True,prior_SOURCE_clusters=clusters,actual_full_native_return_guard=returns,actual_SOURCE_ground_stitches=grounds,actual_power_geometry_proof_sha256=e.sha(OUT/'actual-IO3-power-geometry-proof.json'),actual_persisted_route_cut=dict(path=str(cut_path),sha256=e.sha(cut_path),disconnected=True),native_errors=0,exact_inherited_warnings=native['violations'],ignored_checks=[],all_old101_bypass_checks_separately_required=True,full_power_or_timing_qualification=False,manufacturing_ready=False))
e.write(OUT/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=g['new_copper_UUIDs'],reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Exact R14401.1 to U14402.1 ordinary OUT_PERMIT F/In2 path with common SOURCE-anchored In1 reference. Frozen .60/.30 signal vias/.20 width/.10 reference margin/.20 annuli and actual SOURCE-ground stitches remain. Native relative IO3 backbone/source neck/22 feeds preserved, CORE1V2 unchanged, all other copper/lands/pin nets retained. No global power or timing claim.',review_evidence_sha256={str(p.resolve()):e.sha(p)for p in(OUT/'review.json',OUT/'actual-IO3-power-geometry-proof.json',CONTROL,Path(__file__))}))
print(json.dumps(dict(passed=True,actual_source_pair=g['source_pair'],new_copper=9,native_errors=0,physical_cut_disconnected=True)))
