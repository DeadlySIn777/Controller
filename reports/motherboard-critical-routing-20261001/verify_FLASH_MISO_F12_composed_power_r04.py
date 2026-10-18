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
ROOT=Path('reports/motherboard-critical-routing-20261001/actual-source26-root83-FPGA-flash-MISO-F-only-r03')
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb')
SOURCE=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
def cu(tree):return{e.value(e.child(n,'uuid')[1]):e.dump(n)for k in('segment','via','arc')for n in e.children(tree,k)}

import importlib.util,math

from decimal import Decimal

def same_literal_new_segment(expected,actual):
 # Only exact decimal notation is canonicalized. No coordinate/width tolerance,
 # default insertion, net/pad/layer changes or missing fields are admitted.
 a,b=e.parse(expected),e.parse(actual)
 if a[0]!=b[0]or a[0]!='segment':return False
 if len(a)!=len(b):return False
 for x,y in zip(a[1:],b[1:]):
  if not isinstance(x,list)or not isinstance(y,list)or x[0]!=y[0]or len(x)!=len(y):return False
  if x[0]in('start','end','width'):
   try:
    if tuple(Decimal(z)for z in x[1:])!=tuple(Decimal(z)for z in y[1:]):return False
   except Exception:return False
  elif x!=y:return False
 return True

def composed_power_chain(bp,mp,board,route_path,power_path):
 # Three literal transitions, not a waiver of any power or SOURCE guard:
 # adopted84 retained-MISO/r01 proof -> reviewed local IO3 cleanup -> actual
 # current route/unchanged-r07 proof relative to that exact cleanup baseline.
 adopted=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/adoption.json')
 original=ROOT/'root84-combined-proof-r03/review.json'
 cleanup_receipt=Path('reports/motherboard-return-zoning-20261001/IO3-literal-tip-cleanup-independent-r07/receipt.json')
 cleanup_board=Path('reports/motherboard-ordinary-routing-20261001/IO3-literal-unused-tip-cleanup-r01/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb')
 root84=adopted.parent/'motherboard-bounded-merged-candidate.kicad_pcb'
 expected={adopted:'ab18eeb96999da598868b597a339414a9b7d2639657137f9eaf068a51206aa83',original:'d67d7c20f269e2c72b792b01d55111654c8af3f79b3126c4d018a33f830e41d0',cleanup_receipt:'4e4694a05226ebd022ce125dc28fd9c77029a4f80fe7a5a94da6abdd0e55a44b',cleanup_board:'3d355fb835429de778e56745fee7926403ede31122f3ea3be63caa2861498119',root84:'64c1ed28edeca443dad6dc7f8e16ac5c0038419c880b6ed0e23896d8aebbab9c'}
 if any(e.sha(p)!=h for p,h in expected.items()):raise ValueError('Literal adopted84/cleanup/original power chain changed')
 adoption,old,clean,route,provided=[e.read(p)for p in(adopted,original,cleanup_receipt,route_path,power_path)]
 if not adoption['passed']or not adoption['adopted']or adoption['board_sha256']!=e.sha(root84)or not old['passed']or old['board_sha256']!=e.sha(root84)or not old['actual_relative_IO3_CORE_power_preservation']['passed']:raise ValueError('Original donor/adopted84 retained actual power proof required')
 if not clean['passed']or clean['board_sha256']!=e.sha(cleanup_board)or clean['native_errors']or clean['native_warnings']or clean['ignored_checks']or clean['orphan_copper']or not all(clean.get(k)is True for k in('existing_Cu_pads_lands_poses_zone_rules_preserved','actual_full_native_IO3_topology_502um_cores_Source44_feeds22_proved','all_definite_old_thin_features_outside_exact_region_retained','all_Source_clusters_retained','original_r07_routing_guard_bytes_unchanged')):raise ValueError('Exact independently qualified literal IO3 cleanup required')
 def normalized_inputs(record):
  result={str(Path(p).resolve()):h for p,h in record.items()}
  for path,h in result.items():
   if e.sha(path)!=h:raise ValueError('Composed power evidence dependency changed '+path)
  return result
 ci=normalized_inputs(clean['input_sha256']);ri=normalized_inputs(route['input_sha256']);oi=normalized_inputs(old['inputs'])
 if ci.get(str(root84.resolve()))!=e.sha(root84)or ci.get(str(cleanup_board.resolve()))!=e.sha(cleanup_board):raise ValueError('Cleanup chain before/after binding differs')
 if not route['passed']or route['board_sha256']!=e.sha(bp)or route['native_errors']or route['native_warnings']or route['ignored_checks']or route['actual_power_geometry_proof_sha256']!=e.sha(power_path):raise ValueError('Actual current routing power proof required')
 for p in(bp,mp,cleanup_board,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')):
  if ri.get(str(p.resolve()))!=e.sha(p):raise ValueError('Current route proof lacks exact adopted source/map/cleanup binding '+str(p))
 helper=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py')
 if e.sha(helper)!='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'or ri.get(str(helper.resolve()))!=e.sha(helper)or ci.get(str(helper.resolve()))!=e.sha(helper):raise ValueError('Unchanged actual r07 power helper chain required')
 for path in('io3-relative-power-screen-native-r07/receipt.json','io3-precision-boundary-r07/receipt.json'):
  p=helper.parent/path;controls=e.read(p)
  if not controls['passed']or controls['helper_sha256']!=e.sha(helper)or ri.get(str(p.resolve()))!=e.sha(p):raise ValueError('Actual frozen native r07 controls missing')
 spec=importlib.util.spec_from_file_location('actual_composed_r07_power',helper);power=importlib.util.module_from_spec(spec);spec.loader.exec_module(power)
 fresh=power.review(pcbnew.LoadBoard(str(cleanup_board)),board)
 if fresh!=provided or not fresh['passed']or not fresh['CORE1V2_exact_filled_geometry_preserved']or not fresh['old_exact_rail_copper_preserved']or len(fresh['actual44_receiver_endpoints'])!=44 or len(fresh['actual22_receiving_annuli'])!=22:raise ValueError('Actual current power review differs from frozen route evidence')
 tracked={str(p.resolve()):e.sha(p)for p in[*expected,route_path,power_path,helper]}
 return dict(passed=True,scope='Exact adopted84 power proof -> independent literal cleanup -> actual unchanged-r07 route proof; no complete ampacity/timing claim',evidence_sha256=tracked,initial_ROOT84_board_sha256=e.sha(root84),cleanup_board_sha256=e.sha(cleanup_board),current_board_sha256=e.sha(bp),original_donor_power_proof_retained=old['actual_relative_IO3_CORE_power_preservation'],literal_cleanup_proof=clean,fresh_actual_current_r07_power_preservation=fresh)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',required=True);ap.add_argument('--map',required=True);ap.add_argument('--drc',required=True);ap.add_argument('--out',required=True);ap.add_argument('--power-route-review',required=True);ap.add_argument('--power-proof',required=True);a=ap.parse_args();bp,mp,dp,out=[Path(p).resolve()for p in(a.board,a.map,a.drc,a.out)];out.mkdir(exist_ok=False,parents=True)
 donor_path=ROOT/'motherboard-FPGA-flash-MISO-candidate.kicad_pcb';proof_path=ROOT/'native-source-return-proof-r01/review.json';plan_path=ROOT/'proposed-delta.json';plan=e.read(plan_path);proof=e.read(proof_path);name=plan['source_net'];review=e.read(SOURCE)
 if not proof['passed']or proof['board_sha256']!=e.sha(donor_path)or proof['exact_12_signal_UUIDs']!=plan['new_signal_UUIDs']or len(proof['actual_twelve_physical_route_cut_negatives'])!=12 or not all(v['actual_native_SOURCE_pair_disconnected']for v in proof['actual_twelve_physical_route_cut_negatives']):raise ValueError('Exact twelve native physical cuts/full donor proof required')
 if name!='/fpga_core/FPGA_FLASH_MISO'or plan['actual_Source_pair']!=['U1001.N1','U1002.2']or plan['base_sha256']!=e.sha(BASE)or plan['source_review_sha256']!=e.sha(SOURCE)or review['source_design_sha256']!=e.sha('hardware/motherboard/design.json')or review['source_netlist_sha256']!=e.sha('hardware/motherboard/netlist.xml'):raise ValueError('Actual Source26, literal endpoint or parent binding changed')
 frozen={str(p.resolve()):e.sha(p)for p in(bp,mp,dp,SOURCE,donor_path,proof_path,plan_path,BASE,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
 donor=cu(e.parse(donor_path.read_text()));actual=cu(e.parse(bp.read_text()));old=cu(e.parse(BASE.read_text()))
 if any(actual.get(u)!=v for u,v in old.items())or any(u not in actual or not same_literal_new_segment(donor[u],actual[u])for u in plan['new_signal_UUIDs']):raise ValueError('Retained old or exact twelve new native Cu changed')
 native=e.read(dp)
 if native.get('ignored_checks')or native['violations']:raise ValueError('Actual combined native error/warning/ignored check')
 mapping=e.read(mp)
 if mapping['input_sha256'].get(str(bp))!=e.sha(bp):raise ValueError('Actual combined map binding failed')
 board=pcbnew.LoadBoard(str(bp));board.BuildConnectivity();pop,_=e.native_source_check(board,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
 padmap={p.m_Uuid.AsString():p for f in board.GetFootprints()for p in f.Pads()};p,q=[padmap[u]for u in plan['actual_Source_pad_UUIDs']]
 if p.GetNetname()!=name or q.GetNetname()!=name or q.m_Uuid.AsString()not in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}:raise ValueError('Actual complete FLASH_MISO SOURCE pair disconnected')
 rows={name:review['nets'][name]};checker=pieces.SourceAnchoredPiecesCheck(board,rows,mapping);tracks={t.m_Uuid.AsString():t for t in board.GetTracks()};returns=[];length=0
 for i,u in enumerate(plan['new_signal_UUIDs']):
  t=tracks[u]
  if t.Type()!=pcbnew.PCB_TRACE_T or t.GetLayer()!=pcbnew.F_Cu or t.GetNetname()!=name or abs(pcbnew.ToMM(t.GetWidth())-(.20 if i==0 else .35))>1e-6:raise ValueError('Actual F-only signal scope/width changed')
  length+=pcbnew.ToMM(t.GetLength());returns.append(dict(uuid=u,net=name,actual_own_reference=checker.segment(t,rows[name])))
 if abs(length-proof['actual_F_path_mm'])>1e-6:raise ValueError('Exact actual path length changed')
 retained=c.clusters_preserved(c.source_clusters(pcbnew.LoadBoard(str(BASE))),board)
 powerproof=composed_power_chain(bp,mp,board,Path(a.power_route_review).resolve(),Path(a.power_proof).resolve())
 if frozen!={p:e.sha(p)for p in frozen}:raise ValueError('Combined proof input changed')
 e.write(out/'review.json',dict(passed=True,scope='One complete FLASH_MISO literal SOURCE pair, twelve F segments only',inputs=frozen,board_sha256=e.sha(bp),map_sha256=e.sha(mp),tool_sha256=e.sha(__file__),source_population=pop,prior_SOURCE_clusters=retained,actual_COMPLETE_SOURCE_pair=['U1001.N1','U1002.2'],actual_F_path_mm=length,exact_native_twelve_signal_UUIDs=plan['new_signal_UUIDs'],exact_new_segment_numeric_notation_only=True,all_old_Cu_raw_AST_unchanged=True,actual_full_Source_anchored_return_proofs=returns,original_actual_twelve_cut_negatives=proof['actual_twelve_physical_route_cut_negatives'],actual_relative_IO3_CORE_power_preservation=powerproof,full_reference_failure_ledger=checker.full_native_report['unanchored_components'],no_signal_vias=True,no_new_native_defects=True,no_ignored_checks=True,loaded_FLASH_receive_timing_unqualified=True,manufacturing_ready=False))
 print(json.dumps(dict(passed=True,actual_SOURCE_pairs=1,literal_F_signal_items=12,path_mm=length)),flush=True)
if __name__=='__main__':main()
