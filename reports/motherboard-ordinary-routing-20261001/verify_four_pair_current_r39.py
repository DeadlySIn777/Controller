"""Current literal DI7/DI6/DI9/sensor-fault Source/return proof after audited merges.

The exact unrelated transaction chain, current power, full connectivity and
all other circuit proofs remain separately required. No source review changes.
"""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as ordinary
from hardware_route_logic_return import identity
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
from hardware_validate_return_bridge_sources import review as ground_review
e=ordinary.engine
ap=argparse.ArgumentParser()
for k in('board','map','drc','out'):ap.add_argument('--'+k,type=Path,required=True)
a=ap.parse_args();a.out.mkdir(exist_ok=False)
root=Path(__file__).parent
baseline=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb')
di7=root/'actual-source26-root87-DI7-In3-r26'
rows=[(di7,baseline,'native-full-proof-r27',1,7),
      (root/'actual-source26-In3-three-pair-corner-repair-r36',di7/'motherboard-ordinary-In2-batch-candidate.kicad_pcb','native-full-proof-r33',3,26)]
frozen={str(p.resolve()):e.sha(p)for p in(a.board,a.map,a.drc,baseline,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
mapping=e.read(a.map);assert mapping['input_sha256'][str(a.board.resolve())]==e.sha(a.board)
drc=e.read(a.drc);assert not drc['violations']and not drc['ignored_checks']
b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity()
population,_=e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
cu={t.m_Uuid.AsString():t for t in b.GetTracks()};pads={p.m_Uuid.AsString():p for p in b.GetPads()}
results=[];seen=set()
for folder,original_base,proofdir,count,copper_count in rows:
 donor_path=folder/'motherboard-ordinary-In2-batch-candidate.kicad_pcb';proof_path=folder/proofdir/'review.json'
 plan=e.read(folder/'proposed-groups.json');manifest=e.read(folder/'manifest.json');prior=e.read(proof_path)
 assert prior['passed']and prior['board_sha256']==e.sha(donor_path)and prior['actual_pair_count']==count and prior['actual_new_copper']==copper_count
 assert plan['base_sha256']==e.sha(original_base)
 assert len(prior['actual_persisted_route_cuts'])==count
 for cut in prior['actual_persisted_route_cuts']:assert cut['disconnected']and e.sha(Path(cut['path']))==cut['sha256']
 ordinary.INPUT_BOARD=original_base;ordinary.MAPPING=mapping
 scope=ordinary.frozen_review_check(manifest,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
 donor=pcbnew.LoadBoard(str(donor_path));expected={t.m_Uuid.AsString():identity(t)for t in donor.GetTracks()}
 ids=set(plan['new_copper_UUIDs']);assert len(ids)==copper_count and not seen&ids;seen|=ids
 assert all(u in cu and identity(cu[u])==expected[u]for u in ids)
 pairs=[]
 for g in plan['groups']:
  p,q=[pads[u]for u in g['source_pad_UUIDs']]
  assert p.GetNetname()==q.GetNetname()==g['net']
  assert [p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()]==g['source_pair']
  assert q.m_Uuid.AsString()in{v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(p)}
  pairs.append(g['source_pair'])
 returns=ordinary.actual_return_check(b,{u for g in plan['groups']for u in g['signal_UUIDs']},manifest['nets'])
 assert all(set(r['intended_reference_layers'])=={'In1.Cu','In4.Cu'}for r in returns['actual_signal_via_reference_audits'])
 grounds=ground_review(b,[dict(net='/LOGIC_GND',new_copper_UUIDs=g['ground_UUIDs'])for g in plan['groups']if g['ground_UUIDs']],mapping['pads'])
 results.append(dict(source_review=scope,actual_source_pairs=pairs,exact_Cu_count=copper_count,actual_returns=returns,actual_ground_source_witnesses=grounds,original_physical_cut_controls=prior['actual_persisted_route_cuts']))
 for path in(original_base,donor_path,proof_path,folder/'proposed-groups.json',folder/'manifest.json'):frozen[str(path.resolve())]=e.sha(path)
prior_clusters=clusters_preserved(source_clusters(pcbnew.LoadBoard(str(baseline))),b)
assert all(e.sha(path)==h for path,h in frozen.items())
e.write(a.out/'review.json',dict(passed=True,input_sha256=frozen,board_sha256=e.sha(a.board),map_sha256=e.sha(a.map),source_population=population,actual_completed_pairs=4,literal_route_Cu_count=len(seen),results=results,all_prior_Source_clusters=prior_clusters,current_power_and_other_circuit_and_exact_transaction_chain_separately_required=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,actual_completed_pairs=4,literal_route_Cu_count=len(seen))))
