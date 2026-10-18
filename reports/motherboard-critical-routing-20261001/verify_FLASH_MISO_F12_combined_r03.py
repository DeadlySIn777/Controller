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

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',required=True);ap.add_argument('--map',required=True);ap.add_argument('--drc',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();bp,mp,dp,out=[Path(p).resolve()for p in(a.board,a.map,a.drc,a.out)];out.mkdir(exist_ok=False,parents=True)
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
 power_path=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r01.py');power_receipt=e.read('reports/motherboard-ordinary-routing-20261001/io3-relative-power-screen-native-r01/receipt.json')
 if not power_receipt.get('passed') or power_receipt.get('helper_sha256')!=e.sha(power_path):raise ValueError('Native-qualified relative power dependency changed')
 spec=importlib.util.spec_from_file_location('actual_relative_power',power_path);power=importlib.util.module_from_spec(spec);spec.loader.exec_module(power)
 powerproof=power.review(pcbnew.LoadBoard(str(BASE)),board)
 if not powerproof['passed']:raise ValueError('Actual retained power geometry rejected')
 if frozen!={p:e.sha(p)for p in frozen}:raise ValueError('Combined proof input changed')
 e.write(out/'review.json',dict(passed=True,scope='One complete FLASH_MISO literal SOURCE pair, twelve F segments only',inputs=frozen,board_sha256=e.sha(bp),map_sha256=e.sha(mp),tool_sha256=e.sha(__file__),source_population=pop,prior_SOURCE_clusters=retained,actual_COMPLETE_SOURCE_pair=['U1001.N1','U1002.2'],actual_F_path_mm=length,exact_native_twelve_signal_UUIDs=plan['new_signal_UUIDs'],exact_new_segment_numeric_notation_only=True,all_old_Cu_raw_AST_unchanged=True,actual_full_Source_anchored_return_proofs=returns,original_actual_twelve_cut_negatives=proof['actual_twelve_physical_route_cut_negatives'],actual_relative_IO3_CORE_power_preservation=powerproof,full_reference_failure_ledger=checker.full_native_report['unanchored_components'],no_signal_vias=True,no_new_native_defects=True,no_ignored_checks=True,loaded_FLASH_receive_timing_unqualified=True,manufacturing_ready=False))
 print(json.dumps(dict(passed=True,actual_SOURCE_pairs=1,literal_F_signal_items=12,path_mm=length)),flush=True)
if __name__=='__main__':main()
