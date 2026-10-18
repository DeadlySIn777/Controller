"""Source/return/cut proof only. Current-board power qualification is required separately."""
from pathlib import Path
import sys,json,argparse
sys.path[:0]=[str(Path('tools').resolve()),str(Path(__file__).parent.resolve())]
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_route_critical_digital_wip_r03 as c
import hardware_route_critical_digital_wip_r05 as authority
import check_io3_backbone_preservation_r07 as power
from hardware_validate_return_bridge_sources import review as ground_review
from hardware_route_logic_return import identity,pad_identity
e=o.engine;p=argparse.ArgumentParser()
for k in('board','map','drc','out'):p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args();a.out.mkdir(exist_ok=False)
root=Path(__file__).parent;donor=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-OBS29-repair-trial-r86')
assert e.sha(donor/'motherboard-bounded-merged-candidate.kicad_pcb')=='282e0e5b6cf7684ea844f693fd184d70ab18b72ac2c4a0b5a3c8064d4e817cb7'
BASE=root/'IO3-literal-unused-tip-cleanup-r01/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb'
ORIGINAL=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb')
CONTROL=root/'io3-relative-power-screen-native-r07/receipt.json';PRECISION=root/'io3-precision-boundary-r07/receipt.json'
for cp in(CONTROL,PRECISION):
 controls=e.read(cp);assert controls['passed']and controls['helper_sha256']==e.sha(power.__file__)
plan=e.read(donor/'proposed-groups.json');man=e.read(donor/'manifest.json');groups=plan['groups'];assert len(groups)==7
paths=(BASE,ORIGINAL,a.board,a.map,a.drc,CONTROL,PRECISION,donor/'proposed-groups.json',donor/'manifest.json',donor/'motherboard-bounded-merged-candidate.kicad_pcb',Path(__file__),Path(power.__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
frozen={str(path.resolve()):e.sha(path)for path in paths}
o.INPUT_BOARD=ORIGINAL;o.MAPPING=e.read(a.map);assert o.MAPPING['input_sha256'][str(a.board.resolve())]==e.sha(a.board)
source=o.frozen_review_check(man,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'));native=e.read(a.drc);assert not native['violations']and not native['ignored_checks']
before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(a.board));donor_board=pcbnew.LoadBoard(str(donor/'motherboard-bounded-merged-candidate.kicad_pcb'))
before.BuildConnectivity();after.BuildConnectivity()
population,_=e.native_source_check(after,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
old={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};actual={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()};original_new={t.m_Uuid.AsString():identity(t)for t in donor_board.GetTracks()}
new={u for g in groups for u in g['new_copper_UUIDs']};assert len(new)==65
assert all(actual.get(u)==v for u,v in old.items())and set(actual)-set(old)==new
assert all(actual[u]==original_new[u]for u in new)
assert {q.m_Uuid.AsString():pad_identity(q)for q in before.GetPads()}=={q.m_Uuid.AsString():pad_identity(q)for q in after.GetPads()}
clusters=c.clusters_preserved(c.source_clusters(before),after)
def joined(board,g):
 board.BuildConnectivity();pads={q.m_Uuid.AsString():q for q in board.GetPads()};s,t=[pads[u]for u in g['source_pad_UUIDs']];assert s.GetNetname()==t.GetNetname()==g['net']
 return t.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(s)}
for g in groups:assert joined(after,g)and not joined(before,g),g['source_pair']
returns=o.actual_return_check(after,{u for g in groups for u in g['signal_UUIDs']},man['nets']);assert all(row['intended_reference_layers']==['In1.Cu']for row in returns['actual_signal_via_reference_audits'])
grounds=ground_review(after,[dict(net='/LOGIC_GND',new_copper_UUIDs=g['ground_UUIDs'])for g in groups if g['ground_UUIDs']],o.MAPPING['pads'])
e.write(a.out/'actual-source-return-proof.json',dict(passed=True,board_sha256=e.sha(a.board),returns=returns,grounds=grounds,source_population=population))
# The full r15 guard failure is preserved. This checker proves only Source,
# exact routed Cu, actual reference and cuts; adoption needs independent power.
tree=e.parse(a.board.read_text());cut_evidence=[];cut_boards=[]
for i,g in enumerate(groups):
 remove=set(g['new_copper_UUIDs']);cut_tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in('segment','via','arc')and e.value(e.child(v,'uuid')[1])in remove)]
 cut_path=a.out/f'actual-physical-route-cut-{i:02d}.kicad_pcb';cut_path.write_text(authority.dump_native_board(cut_tree)+'\n');cut=pcbnew.LoadBoard(str(cut_path));cut_boards.append(cut);assert not joined(cut,g),g['source_pair'];cut_evidence.append(dict(pair=g['source_pair'],path=str(cut_path),sha256=e.sha(cut_path),disconnected=True))
assert all(e.sha(path)==h for path,h in frozen.items())
e.write(a.out/'review.json',dict(passed=True,scope='Seven actual Source pairs, exact native Cu, own reference and physical cut controls only; no power qualification',input_sha256=frozen,board_sha256=e.sha(a.board),source_scope=source,source_population=population,all7_actual_pairs_closed=True,actual_source_pairs=[g['source_pair']for g in groups],actual_new_copper=len(new),old_exact_copper_and_lands_preserved=True,prior_SOURCE_clusters=clusters,actual_full_native_return_guard=returns,actual_SOURCE_ground_stitches=grounds,includes_power_verification=False,current_board_composed_power_proof_separately_required=True,actual_persisted_route_cuts=cut_evidence,native_errors=0,native_warnings=0,ignored_checks=[],separate_literal_cleanup_qualification_required=True,all_old101_bypass_checks_separately_required=True,full_power_or_timing_qualification=False,manufacturing_ready=False))
print(json.dumps(dict(passed=True,actual_pairs=7,new_copper=65,physical_cut_controls=7)))
