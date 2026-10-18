"""Actual CCK/local-cap candidate source/return/cut proof, retaining every failure."""
from pathlib import Path
import sys,copy,json,importlib.util
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_critical_digital_wip_r03 as c
import hardware_scope_anchored_reference_pieces as pieces
from hardware_route_logic_return import identity,mm
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
e=authority.engine
P=Path('reports/motherboard-critical-routing-20261001/actual-source26-root84-FPGA-CCK-C1022-F-In2-r06')
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb')
BP=P/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb';MAP=Path('reports/motherboard-domains-20261001/source26-r84-CCK-C1022-candidate-r06/domain-map.json')
REVIEW=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
OUT=P/'actual-native-source-return-r01';OUT.mkdir(parents=True,exist_ok=False)
plan=e.read(P/'proposed-delta.json');name=plan['source_net'];row=copy.deepcopy(e.read(REVIEW)['nets'][name]);row.update(via_diameter_mm=.6,via_drill_mm=.3,reference_layers={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu'})
board=pcbnew.LoadBoard(str(BP));board.BuildConnectivity();before=pcbnew.LoadBoard(str(BASE));before.BuildConnectivity();pop,_=e.native_source_check(board,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
padmap={p.m_Uuid.AsString():p for f in board.GetFootprints()for p in f.Pads()};pads={(f.GetReference(),p.GetNumber()):p for f in board.GetFootprints()for p in f.Pads()};cu={t.m_Uuid.AsString():t for t in board.GetTracks()};oldcu={t.m_Uuid.AsString():t for t in before.GetTracks()}
p,q=[padmap[u]for u in plan['actual_Source_pad_UUIDs']]
def connected(b,p,q):return q.m_Uuid.AsString() in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}|{p.m_Uuid.AsString()}
assert connected(board,p,q)
assert set(cu)-set(oldcu)==set(plan['new_signal_UUIDs']+plan['new_SOURCE_ground_UUIDs']+plan['new_C1022_local_power_UUIDs'])
assert all(identity(t)==identity(cu[u])for u,t in oldcu.items())
retained=c.clusters_preserved(c.source_clusters(before),board)
checker=pieces.SourceAnchoredPiecesCheck(board,{name:row},e.read(MAP));results=[];failures=[]
for u in plan['new_signal_UUIDs']:
 t=cu[u]
 try:
  r=checker.via(t,row)if t.Type()==pcbnew.PCB_VIA_T else checker.segment(t,row)
  results.append(dict(uuid=u,passed=True,proof=r))
 except Exception as ex:
  failures.append(dict(uuid=u,passed=False,error=str(ex),actual_type=t.Type(),layer=board.GetLayerName(t.GetLayer()),xy=mm(t.GetPosition())if t.Type()==pcbnew.PCB_VIA_T else [mm(t.GetStart()),mm(t.GetEnd())]))
cuts=[]
for u in plan['new_signal_UUIDs']:
 b=pcbnew.LoadBoard(str(BP));t=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==u);b.Remove(t);b.BuildConnectivity();pm={p.m_Uuid.AsString():p for f in b.GetFootprints()for p in f.Pads()};a,z=[pm[v]for v in plan['actual_Source_pad_UUIDs']];cuts.append(dict(uuid=u,actual_native_SOURCE_pair_disconnected=not connected(b,a,z)));del b
cap=pads['C1022','1'];ground=pads['C1022','2'];feed=cu[plan['new_C1022_local_power_UUIDs'][0]];oldground=cu['3376a140-028c-4a29-84f0-21540ab5865a']
assert feed.Type()==pcbnew.PCB_VIA_T and feed.GetNetname()=='/IO_3V3' and physical_reference_contact(feed,pcbnew.In2_Cu,board.GetConnectivity())
assert connected(board,cap,pads['U1001','L6']) and connected(board,ground,pads['U1001','N2'])
assert connected(board,ground,oldground)
e.write(OUT/'review.json',dict(passed=not failures and all(r['actual_native_SOURCE_pair_disconnected']for r in cuts),scope='Actual complete CCK Source pair plus physically fed relocated C1022; relative rail capacity remains unqualified',board_sha256=e.sha(BP),map_sha256=e.sha(MAP),source_design_sha256=e.sha('hardware/motherboard/design.json'),source_netlist_sha256=e.sha('hardware/motherboard/netlist.xml'),native_source_population=pop,all_old_native_Cu_identity_exact=True,prior_SOURCE_clusters_preserved=retained,signal_return_passes=results,signal_return_failures=failures,actual_eight_cut_negatives=cuts,complete_actual_SOURCE_pair=plan['actual_Source_pair'],C1022_actual_IO3_L6_connection=True,C1022_actual_GND_N2_original_via_connection=True,C1022_IO3_feed_annulus_source_connected_on_In2=True,C1022_owner_2mm_engineering_target_NOT_passed=True,C1022_owner_centre_distance_mm=plan['owner_power_pad_distance_mm'],full_reference_failure_ledger=checker.full_native_report['unanchored_components'],relative_CORE_capacity_NOT_qualified=True,relative_IO3_capacity_NOT_qualified=True,loaded_clock_and_cap_PDN_qualification_pending=True,manufacturing_ready=False))
print(json.dumps(dict(source_pair_connected=True,return_passes=len(results),return_failures=failures,physical_signal_cuts=cuts,C1022_real_power_and_ground_connected=True)))
