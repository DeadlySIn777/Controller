"""Scoped retained-route proof after separately audited unrelated PCB transactions.

Checks the literal twelve FLASH MISO and sixty-five ordinary-route objects,
their actual Source endpoints and current Source-owned returns. This report
does NOT authorize other copper changes or replace current power, bypass,
transaction-chain, whole-board connectivity or native DRC checks.
"""
from pathlib import Path
import sys,json,argparse,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as ordinary
import hardware_route_critical_digital_wip_r03 as critical
import hardware_scope_anchored_reference_pieces as pieces
from hardware_route_logic_return import identity
from hardware_validate_return_bridge_sources import review as ground_review
e=ordinary.engine
ap=argparse.ArgumentParser()
for k in('board','map','drc','out'):ap.add_argument('--'+k,type=Path,required=True)
a=ap.parse_args();a.out.mkdir(exist_ok=False)
root=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-larger-IO3-cleanup-trial-r87')
base=root/'motherboard-bounded-merged-candidate.kicad_pcb'
adopt=e.read(root/'adoption.json');assert adopt['adopted']and adopt['passed']and adopt['board_sha256']==e.sha(base)
assert e.sha(base)=='0a9e4975b2d9cd90f7853884d626427fb089809c45ae5ed749472c68235e2d13'
prior_seven=e.read(root/'combined-seven-pair-full-proof/review.json')
prior_flash=e.read(root/'combined-retained-FLASH-MISO-proof/review.json')
assert prior_seven['passed']and prior_flash['passed']and prior_seven['board_sha256']==prior_flash['board_sha256']==e.sha(base)
donor=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-OBS29-repair-trial-r86')
plan=e.read(donor/'proposed-groups.json');manifest=e.read(donor/'manifest.json');groups=plan['groups'];assert len(groups)==7
for report,cuts,key in((prior_seven,prior_seven['actual_persisted_route_cuts'],'disconnected'),):
 assert len(cuts)==7 and all(v[key]and e.sha(Path(v['path']))==v['sha256']for v in cuts)
assert len(prior_flash['original_actual_twelve_cut_negatives'])==12
paths=[base,root/'adoption.json',root/'combined-seven-pair-full-proof/review.json',root/'combined-retained-FLASH-MISO-proof/review.json',donor/'proposed-groups.json',donor/'manifest.json',a.board,a.map,a.drc,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]
frozen={str(p.resolve()):e.sha(p)for p in paths}
mapping=e.read(a.map);assert mapping['input_sha256'][str(a.board.resolve())]==e.sha(a.board)
native=e.read(a.drc);assert not native['violations']and not native['ignored_checks']
b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();before=pcbnew.LoadBoard(str(base))
source,_=e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
old={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()};pads={p.m_Uuid.AsString():p for p in b.GetPads()}
sevenids={u for g in groups for u in g['new_copper_UUIDs']};flashids=prior_flash['exact_native_twelve_signal_UUIDs']
assert len(sevenids)==65 and len(flashids)==12 and not sevenids&set(flashids)
assert all(u in cu and identity(cu[u])==old[u]for u in sevenids|set(flashids))
actual_pairs=[]
for g in groups:
 p,q=[pads[u]for u in g['source_pad_UUIDs']]
 assert p.GetNetname()==q.GetNetname()==g['net']
 assert [p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()]==g['source_pair']
 assert q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}
 actual_pairs.append(g['source_pair'])
ordinary.INPUT_BOARD=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb')
ordinary.MAPPING=mapping
ordinary_scope=ordinary.frozen_review_check(manifest,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
returns=ordinary.actual_return_check(b,{u for g in groups for u in g['signal_UUIDs']},manifest['nets'])
grounds=ground_review(b,[dict(net='/LOGIC_GND',new_copper_UUIDs=g['ground_UUIDs'])for g in groups if g['ground_UUIDs']],mapping['pads'])
pin={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()}
p,q=pin['U1001','N1'],pin['U1002','2'];assert p.GetNetname()==q.GetNetname()=='/fpga_core/FPGA_FLASH_MISO'
assert q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}
review_path=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json');review=e.read(review_path)
assert review['source_design_sha256']==e.sha('hardware/motherboard/design.json')and review['source_netlist_sha256']==e.sha('hardware/motherboard/netlist.xml')
frozen[str(review_path.resolve())]=e.sha(review_path)
row=review['nets'][p.GetNetname()];check=pieces.SourceAnchoredPiecesCheck(b,{p.GetNetname():row},mapping)
flash_returns=[dict(uuid=u,actual_own_reference=check.segment(cu[u],row))for u in flashids]
assert all(cu[u].Type()==pcbnew.PCB_TRACE_T and cu[u].GetLayer()==pcbnew.F_Cu for u in flashids)
length=sum(pcbnew.ToMM(cu[u].GetLength())for u in flashids);assert abs(length-prior_flash['actual_F_path_mm'])<1e-6
clusters=critical.clusters_preserved(critical.source_clusters(before),b)
assert all(e.sha(p)==h for p,h in frozen.items())
e.write(a.out/'review.json',dict(passed=True,board_sha256=e.sha(a.board),map_sha256=e.sha(a.map),input_sha256=frozen,scope='Only retained exact77 Cu/eight complete Source pairs/current actual returns',actual_retained_ordinary_pairs=actual_pairs,actual_ordinary65_identities_preserved=True,actual_ordinary_source_review=ordinary_scope,actual_ordinary_returns=returns,actual_ground_stitches=grounds,actual_complete_MISO_pair=['U1001.N1','U1002.2'],actual_MISO12_identities_preserved=True,actual_MISO_returns=flash_returns,actual_MISO_path_mm=length,source_population=source,prior_Source_clusters_retained=clusters,all_other_Cu_changes_require_independent_transaction_proof=True,current_power_proof_required=True,current_owned_bypass_proof_required=True,old_full_route_cut_proofs_preserved=True,physical_or_loaded_timing_qualified=False,manufacturing_ready=False))
print(json.dumps(dict(passed=True,exact_retained_Cu=77,actual_complete_pairs=8,current_power_and_transaction_proofs_separately_required=True)))
