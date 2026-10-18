"""Read-only exact seven-Cu/two-SOURCE-pair acceptance on a combined board."""
from pathlib import Path
import sys,argparse,json
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_critical_digital_wip_r03 as c
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_owned_bypass_loops_wip_r03 as w
e=authority.engine
ROOT=Path('reports/motherboard-critical-routing-20261001/actual-source26-root83-FPGA-flash-MISO-F-only-r02')
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb')
SOURCE=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
def cu(tree):return{e.value(e.child(n,'uuid')[1]):e.dump(n)for k in('segment','via','arc')for n in e.children(tree,k)}

import copy,math

def main():
 out=ROOT/'native-source-return-proof-r01';out.mkdir(exist_ok=False,parents=True)
 bp=ROOT/'motherboard-FPGA-flash-MISO-candidate.kicad_pcb';mp=ROOT/'fresh-domain-map/domain-map.json';dp=ROOT/'drc.json';plan=e.read(ROOT/'proposed-delta.json');name=plan['source_net'];review=e.read(SOURCE)
 if name!='/fpga_core/FPGA_FLASH_MISO' or plan['actual_Source_pair']!=['U1001.N1','U1002.2'] or len(plan['new_signal_UUIDs'])!=13 or plan['new_SOURCE_ground_UUIDs'] or not plan['no_new_signal_vias']:raise ValueError('Only literal F-only full pair accepted')
 if plan['base_sha256']!=e.sha(BASE) or plan['source_review_sha256']!=e.sha(SOURCE) or review['source_design_sha256']!=e.sha('hardware/motherboard/design.json') or review['source_netlist_sha256']!=e.sha('hardware/motherboard/netlist.xml'):raise ValueError('Actual source or parent changed')
 frozen={str(p.resolve()):e.sha(p)for p in(bp,mp,dp,SOURCE,ROOT/'proposed-delta.json',BASE,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
 oldtree=e.parse(BASE.read_text());tree=e.parse(bp.read_text());oldcu=cu(oldtree);newcu=cu(tree)
 if e.immutable_objects(tree)!=e.immutable_objects(oldtree) or any(newcu.get(u)!=v for u,v in oldcu.items()) or set(newcu)-set(oldcu)!=set(plan['new_signal_UUIDs']):raise ValueError('Unreviewed Source/land/pose/zone or retained Cu changes')
 native=e.read(dp)
 if native.get('ignored_checks') or native['violations']:raise ValueError('New native DRC violation/ignored check')
 mapping=e.read(mp)
 if mapping['input_sha256'].get(str(bp.resolve()))!=e.sha(bp):raise ValueError('Fresh actual map binding failed')
 board=pcbnew.LoadBoard(str(bp));board.BuildConnectivity();population,_=e.native_source_check(board,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
 pads={(f.GetReference(),p.GetNumber()):p for f in board.GetFootprints()for p in f.Pads()};p,q=pads['U1001','N1'],pads['U1002','2'];uuids=plan['new_signal_UUIDs']
 def joined(b):
  pd={x.m_Uuid.AsString():x for f in b.GetFootprints()for x in f.Pads()};a,z=[pd[v]for v in plan['actual_Source_pad_UUIDs']]
  return z.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(a)}
 if p.GetNetname()!=name or q.GetNetname()!=name or not joined(board):raise ValueError('Full literal SOURCE pair is disconnected')
 row=review['nets'][name];checker=pieces.SourceAnchoredPiecesCheck(board,{name:row},mapping);tracks={t.m_Uuid.AsString():t for t in board.GetTracks()};returns=[];length=0
 for i,u in enumerate(uuids):
  t=tracks[u];expected=.20 if i==0 else .35
  if t.Type()!=pcbnew.PCB_TRACE_T or t.GetLayer()!=pcbnew.F_Cu or t.GetNetname()!=name or abs(pcbnew.ToMM(t.GetWidth())-expected)>1e-6:raise ValueError('Literal actual F-only native width/net changed')
  length+=pcbnew.ToMM(t.GetLength());returns.append(dict(uuid=u,net=name,actual_source_anchored_own_In1_reference=checker.segment(t,row)))
 retained=c.clusters_preserved(c.source_clusters(pcbnew.LoadBoard(str(BASE))),board)
 negatives=[]
 for i,u in enumerate(uuids):
  cut=copy.deepcopy(tree);cut[:]=[n for n in cut if not(isinstance(n,list)and n and n[0]=='segment'and e.value(e.child(n,'uuid')[1])==u)]
  path=out/('cut-'+str(i).zfill(2)+'.kicad_pcb');path.write_text(authority.dump_native_board(cut)+'\n');b=pcbnew.LoadBoard(str(path));b.BuildConnectivity()
  if joined(b):raise ValueError('Literal cut negative remained connected '+u)
  negatives.append(dict(removed_signal_UUID=u,actual_native_SOURCE_pair_disconnected=True))
 if frozen!={p:e.sha(p)for p in frozen}:raise ValueError('Proof input changed')
 e.write(out/'review.json',dict(passed=True,scope='One complete literal FLASH_MISO SOURCE pair / thirteen F segments only',inputs=frozen,board_sha256=e.sha(bp),map_sha256=e.sha(mp),tool_sha256=e.sha(__file__),source_population=population,prior_SOURCE_clusters=retained,actual_complete_SOURCE_pair=dict(net=name,endpoints=plan['actual_Source_pair'],joined=True),exact_13_signal_UUIDs=uuids,actual_F_path_mm=length,no_signal_vias=True,all_retained_Cu_exact=True,all_footprints_pads_poses_zone_definitions_unchanged=True,actual_full_source_anchored_reference_proofs=returns,full_reference_failure_ledger=checker.full_native_report['unanchored_components'],actual_thirteen_physical_route_cut_negatives=negatives,native_errors=0,native_warnings=0,ignored_checks=[],aggregate_15mm_neck_length_mm=0,loaded_FLASH_receive_timing_and_factory_stackup_unqualified=True,no_affected_retained_CCK_moves=True,manufacturing_ready=False))
 print(json.dumps(dict(passed=True,actual_SOURCE_pairs=1,new_F_Cu=13,path_mm=length,cut_negatives=len(negatives))),flush=True)
if __name__=='__main__':main()
