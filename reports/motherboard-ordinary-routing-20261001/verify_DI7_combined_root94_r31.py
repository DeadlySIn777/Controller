"""Independent full Source/return/power and persisted route-cut check for an additive batch."""
from pathlib import Path
import sys,argparse,json
sys.path[:0]=[str(Path('tools').resolve()),str(Path(__file__).parent.resolve())]
import pcbnew
import hardware_route_ordinary_wip_r05 as ordinary
import hardware_route_critical_digital_wip_r03 as critical
import hardware_route_critical_digital_wip_r05 as authority
import check_io3_backbone_preservation_r07 as power
from hardware_route_logic_return import identity,pad_identity
from hardware_validate_return_bridge_sources import review as ground_review
from hardware_merge_bounded_pcb_delta import zone_definition
e=ordinary.engine
ap=argparse.ArgumentParser()
for k in('before','donor','board','map','drc','out'):ap.add_argument('--'+k,type=Path,required=True)
a=ap.parse_args();a.out.mkdir(exist_ok=False)
root=Path(__file__).parent
plan=e.read(a.donor/'proposed-groups.json');manifest=e.read(a.donor/'manifest.json');groups=plan['groups']
assert len(groups)==1
assert plan['base_sha256']=='0a9e4975b2d9cd90f7853884d626427fb089809c45ae5ed749472c68235e2d13'
assert e.sha(a.before)=='3e2eb216ac1ba569162ede8c137bde6584705eaf714304997089f8ee3bb987fe'
original=e.read(a.donor/'native-full-proof-r27/review.json')
assert original['passed']and original['board_sha256']==e.sha(a.donor/'motherboard-ordinary-In2-batch-candidate.kicad_pcb')
assert original['actual_pair_count']==1 and original['actual_new_copper']==7
donor_board=a.donor/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'
if not donor_board.exists():donor_board=a.donor/'motherboard-ordinary-F-batch-candidate.kicad_pcb'
controls=[root/'io3-relative-power-screen-native-r07/receipt.json',root/'io3-precision-boundary-r07/receipt.json']
for path in controls:
 c=e.read(path);assert c['passed']and c['helper_sha256']==e.sha(power.__file__)
files=[a.before,donor_board,a.board,a.map,a.drc,*controls,a.donor/'proposed-groups.json',a.donor/'manifest.json',a.donor/'native-full-proof-r27/review.json',Path(__file__),Path(power.__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]
frozen={str(path.resolve()):e.sha(path)for path in files}
ordinary.INPUT_BOARD=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb');ordinary.MAPPING=e.read(a.map)
assert ordinary.MAPPING['input_sha256'][str(a.board.resolve())]==e.sha(a.board)
source=ordinary.frozen_review_check(manifest,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
native=e.read(a.drc);assert not native['violations']and not native['ignored_checks']
before=pcbnew.LoadBoard(str(a.before));after=pcbnew.LoadBoard(str(a.board));donor=pcbnew.LoadBoard(str(donor_board))
before.BuildConnectivity();after.BuildConnectivity()
population,_=e.native_source_check(after,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
old={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};current={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()};wanted={t.m_Uuid.AsString():identity(t)for t in donor.GetTracks()}
new=[u for g in groups for u in g['new_copper_UUIDs']]
assert len(new)==len(set(new))and set(new)==set(plan['new_copper_UUIDs'])
assert all(current.get(u)==v for u,v in old.items())and set(current)-set(old)==set(new)
assert all(current[u]==wanted[u]for u in new)
assert {p.m_Uuid.AsString():pad_identity(p)for p in before.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}
def zones(path):
 tree=e.parse(path.read_text());return{e.value(e.child(z,'uuid')[1]):zone_definition(z)for z in e.children(tree,'zone')}
assert zones(a.before)==zones(a.board)
assert e.sha(a.before.with_suffix('.kicad_dru'))==e.sha(a.board.with_suffix('.kicad_dru'))
clusters=critical.clusters_preserved(critical.source_clusters(before),after)
def joined(board,g):
 board.BuildConnectivity();pads={p.m_Uuid.AsString():p for p in board.GetPads()};p,q=[pads[u]for u in g['source_pad_UUIDs']]
 assert p.GetNetname()==q.GetNetname()==g['net']
 assert [p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()]==g['source_pair']
 return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}
for g in groups:assert joined(after,g)and not joined(before,g),g['source_pair']
returns=ordinary.actual_return_check(after,{u for g in groups for u in g['signal_UUIDs']},manifest['nets'])
# This literal Source26 DI7 pair uses F/In3 with transfers into both adjacent grounds.
assert len(groups)==1 and groups[0]['source_pair']==['U13001.13','R8208.1']
assert len(groups[0]['new_copper_UUIDs'])==7
assert all(set(r['intended_reference_layers'])=={'In1.Cu','In4.Cu'}for r in returns['actual_signal_via_reference_audits'])
assert len(returns['actual_signal_via_reference_audits'])==2
ground_groups=[dict(net='/LOGIC_GND',new_copper_UUIDs=g['ground_UUIDs'])for g in groups if g['ground_UUIDs']]
grounds=ground_review(after,ground_groups,ordinary.MAPPING['pads'])if ground_groups else []
e.write(a.out/'actual-source-return-proof.json',dict(passed=True,board_sha256=e.sha(a.board),returns=returns,grounds=grounds,source_population=population))
powerproof=power.review(before,after);assert powerproof['passed'];e.write(a.out/'actual-IO3-power-geometry-proof.json',powerproof)
tree=e.parse(a.board.read_text());cuts=[]
for i,g in enumerate(groups):
 remove=set(g['new_copper_UUIDs']);cut_tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in('segment','via','arc')and e.value(e.child(v,'uuid')[1])in remove)]
 path=a.out/f'actual-physical-route-cut-{i:02d}.kicad_pcb';path.write_text(authority.dump_native_board(cut_tree)+'\n')
 cut=pcbnew.LoadBoard(str(path));assert not joined(cut,g),g['source_pair']
 cuts.append(dict(pair=g['source_pair'],path=str(path),sha256=e.sha(path),disconnected=True))
assert all(e.sha(path)==h for path,h in frozen.items())
e.write(a.out/'review.json',dict(passed=True,input_sha256=frozen,board_sha256=e.sha(a.board),source_scope=source,source_population=population,actual_all_pairs_closed=True,actual_pair_count=len(groups),actual_source_pairs=[g['source_pair']for g in groups],actual_new_copper=len(new),old_exact_copper_lands_zone_definitions_and_rules_preserved=True,prior_SOURCE_clusters=clusters,actual_full_native_return_guard=returns,actual_SOURCE_ground_stitches=grounds,actual_power_geometry_proof_sha256=e.sha(a.out/'actual-IO3-power-geometry-proof.json'),actual_persisted_route_cuts=cuts,native_errors=0,native_warnings=0,ignored_checks=[],all_prior_retained_circuit_checks_separately_required=True,full_power_or_timing_qualification=False,manufacturing_ready=False))
print(json.dumps(dict(passed=True,actual_pairs=len(groups),new_copper=len(new),physical_cut_controls=len(cuts))))
