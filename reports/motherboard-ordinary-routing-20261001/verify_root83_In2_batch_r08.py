"""Accept complete actual SOURCE pairs only after native source/return/power proof."""
from pathlib import Path
import sys,json
sys.path[:0]=[str(Path('tools').resolve()),str(Path(__file__).parent.resolve())]
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_route_critical_digital_wip_r03 as c
import hardware_route_critical_digital_wip_r05 as authority
import check_io3_backbone_preservation_r06 as power
from hardware_validate_return_bridge_sources import review as ground_review
from hardware_route_logic_return import identity,pad_identity
e=o.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb')
OUT=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root83-In2-batch-r08')
DEST=OUT/'motherboard-ordinary-In2-batch-candidate.kicad_pcb';MAP=OUT/'fresh-domain-map/domain-map.json'
CONTROL=Path(__file__).parent/'io3-relative-power-screen-native-r06/receipt.json'
PRECISION=Path(__file__).parent/'io3-precision-boundary-r06/receipt.json'
for cp in(CONTROL,PRECISION):
 controls=e.read(cp);assert controls['passed']and controls['helper_sha256']==e.sha(power.__file__)
plan=e.read(OUT/'proposed-groups.json');man=e.read(OUT/'manifest.json');groups=plan['groups'];assert len(groups)==7
frozen={str(p.resolve()):e.sha(p)for p in(BASE,DEST,MAP,CONTROL,PRECISION,OUT/'proposed-groups.json',OUT/'manifest.json',OUT/'native.json',Path(__file__),Path(power.__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
o.INPUT_BOARD=BASE;o.MAPPING=e.read(MAP)
assert o.MAPPING['input_sha256'][str(DEST.resolve())]==e.sha(DEST)
source=o.frozen_review_check(man,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
native=e.read(OUT/'native.json');assert not native['violations']and not native['ignored_checks']
before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(DEST));before.BuildConnectivity();after.BuildConnectivity()
population,_=e.native_source_check(after,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
old={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};actual={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}
new={u for g in groups for u in g['new_copper_UUIDs']}
assert all(actual.get(u)==v for u,v in old.items())and set(actual)-set(old)==new
assert {p.m_Uuid.AsString():pad_identity(p)for p in before.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}
clusters=c.clusters_preserved(c.source_clusters(before),after)
def joined(board,g):
 board.BuildConnectivity();pads={p.m_Uuid.AsString():p for p in board.GetPads()};p,q=[pads[u]for u in g['source_pad_UUIDs']]
 assert p.GetNetname()==q.GetNetname()==g['net']
 return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}
for g in groups:assert joined(after,g)and not joined(before,g),g['source_pair']
try:returns=o.actual_return_check(after,{u for g in groups for u in g['signal_UUIDs']},man['nets'])
except Exception as ex:
 e.write(OUT/'actual-return-failure.json',dict(passed=False,reason=str(ex),board_sha256=e.sha(DEST)));raise
assert all(row['intended_reference_layers']==['In1.Cu']for row in returns['actual_signal_via_reference_audits'])
grounds=ground_review(after,[dict(net='/LOGIC_GND',new_copper_UUIDs=g['ground_UUIDs'])for g in groups if g['ground_UUIDs']],o.MAPPING['pads'])
powerproof=power.review(before,after);e.write(OUT/'actual-IO3-power-geometry-proof.json',powerproof)
tree=e.parse(DEST.read_text());cut_evidence=[];cut_boards=[]
for i,g in enumerate(groups):
 remove=set(g['new_copper_UUIDs']);cut_tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in('segment','via','arc')and e.value(e.child(v,'uuid')[1])in remove)]
 cut_path=OUT/f'actual-physical-route-cut-{i:02d}.kicad_pcb';cut_path.write_text(authority.dump_native_board(cut_tree)+'\n');cut=pcbnew.LoadBoard(str(cut_path));cut_boards.append(cut)
 assert not joined(cut,g),g['source_pair']
 cut_evidence.append(dict(pair=g['source_pair'],path=str(cut_path),sha256=e.sha(cut_path),disconnected=True))
assert all(e.sha(p)==h for p,h in frozen.items())
e.write(OUT/'review.json',dict(passed=True,input_sha256=frozen,board_sha256=e.sha(DEST),source_scope=source,source_population=population,actual_source_pairs=[g['source_pair']for g in groups],all7_actual_pairs_closed=True,actual_new_copper=len(new),old_exact_copper_and_lands_preserved=True,prior_SOURCE_clusters=clusters,actual_full_native_return_guard=returns,actual_SOURCE_ground_stitches=grounds,actual_power_geometry_proof_sha256=e.sha(OUT/'actual-IO3-power-geometry-proof.json'),actual_persisted_route_cuts=cut_evidence,native_errors=0,native_warnings=0,ignored_checks=[],all_old101_bypass_checks_separately_required=True,full_power_or_timing_qualification=False,manufacturing_ready=False))
e.write(OUT/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(new),reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Exact seven ordinary SOURCE-pair F/In2 paths with actual SOURCE-anchored In1 reference, unchanged .60/.30 signal vias, .20 signal width and true return annuli. Native relative1mm IO3 backbone/source44pins/22 receiving feeds retained; CORE1V2 unchanged. No source/lands/other copper changes; no global current or timing qualification.',review_evidence_sha256={str(p.resolve()):e.sha(p)for p in(OUT/'review.json',OUT/'actual-IO3-power-geometry-proof.json',CONTROL,PRECISION,Path(__file__))}))
print(json.dumps(dict(passed=True,actual_pairs=7,new_copper=len(new),native_errors=0,physical_cut_controls=len(cut_evidence))))
