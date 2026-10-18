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
ROOT=Path('reports/motherboard-critical-routing-20261001/actual-source26-root75-local-critical-r01')
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-ordinary9-r75/motherboard-bounded-merged-candidate.kicad_pcb')
SOURCE=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
def cu(tree):return{e.value(e.child(n,'uuid')[1]):e.dump(n)for k in('segment','via','arc')for n in e.children(tree,k)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',required=True);ap.add_argument('--map',required=True);ap.add_argument('--out',required=True);ap.add_argument('--drc',required=True);a=ap.parse_args()
 bp,mp,out,dp=[Path(p).resolve()for p in(a.board,a.map,a.out,a.drc)];out.mkdir(exist_ok=False,parents=True)
 plan=e.read(ROOT/'proposed-local-groups.json');prior=e.read(ROOT/'review.json');inventory=e.read(ROOT/'independent-connectivity/review.json')
 if not prior['passed']or not inventory['source_net_checks_pass']or inventory['orphan_copper_items']or len(plan['groups'])!=2 or len(plan['actual_added_copper_UUIDs'])!=7:raise ValueError('Only exact independently accepted seven-Cu donor is accepted')
 review=e.read(SOURCE)
 if plan['exact_critical_review_sha256']!=e.sha(SOURCE)or review['source_design_sha256']!=e.sha('hardware/motherboard/design.json')or review['source_netlist_sha256']!=e.sha('hardware/motherboard/netlist.xml'):raise ValueError('Source26 critical review changed')
 frozen={str(p.resolve()):e.sha(p)for p in(bp,mp,dp,SOURCE,ROOT/'review.json',ROOT/'proposed-local-groups.json',Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
 donor=cu(e.parse((ROOT/'motherboard-critical-local-candidate.kicad_pcb').read_text()));actual=cu(e.parse(bp.read_text()))
 if any(actual.get(u)!=donor[u]for u in plan['actual_added_copper_UUIDs']):raise ValueError('Exact donor seven source-net/UUID/geometries changed')
 mapping=e.read(mp)
 if mapping['input_sha256'].get(str(bp))!=e.sha(bp):raise ValueError('Fresh actual combined-board map binding failed')
 native=e.read(dp);known=w.reviewed_wip_warnings(e.read(BASE.parent/'drc.json'),e.read(BASE.parent/'baseline-disposition.json'),e.sha(BASE))
 if native.get('ignored_checks')or w.new_route_defects(native,known):raise ValueError('Actual combined native defects/ignored checks remain')
 board=pcbnew.LoadBoard(str(bp));board.BuildConnectivity();pop,_=e.native_source_check(board,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
 padmap={p.m_Uuid.AsString():p for f in board.GetFootprints()for p in f.Pads()};positive=[]
 for g in plan['groups']:
  p,q=[padmap[u]for u in g['SOURCE_pad_UUIDs']]
  if p.GetNetname()!=g['net']or q.GetNetname()!=g['net']or q.m_Uuid.AsString()not in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}:raise ValueError('Actual literal critical SOURCE pair disconnected')
  positive.append(dict(net=g['net'],SOURCE_pair=g['SOURCE_pair'],joined=True))
 rows={g['net']:review['nets'][g['net']]for g in plan['groups']};checker=pieces.SourceAnchoredPiecesCheck(board,rows,mapping);tracks={t.m_Uuid.AsString():t for t in board.GetTracks()};returns=[]
 for u in plan['actual_added_copper_UUIDs']:
  t=tracks[u];returns.append(dict(uuid=u,net=t.GetNetname(),actual_own_reference=checker.segment(t,rows[t.GetNetname()])))
 retained=c.clusters_preserved(c.source_clusters(pcbnew.LoadBoard(str(BASE))),board)
 if frozen!={p:e.sha(p)for p in frozen}:raise ValueError('Actual combined-board/source/ledger input changed during verification')
 e.write(out/'review.json',dict(passed=True,scope='Two local critical SOURCE pair groups/seven F segments only',inputs=frozen,board_sha256=e.sha(bp),map_sha256=e.sha(mp),tool_sha256=e.sha(__file__),source_population=pop,prior_SOURCE_clusters=retained,actual_COMPLETE_SOURCE_pair_checks=positive,actual_full_native_source_anchored_reference_proofs=returns,complete_failed_reference_piece_ledger=checker.full_native_report['unanchored_components'],eligible_piece_audit=checker.eligible_piece_audit,original_persisted_physical_cut_controls=prior['actual_physical_route_cut_negatives'],all_unsuppressed_native_warnings=native['violations'],no_new_native_defects=True,no_ignored_checks=True,whole_clock_and_MOSI_nets_not_claimed_complete=True,loaded_timing_unqualified=True,whole_board_reference_qualification=False,manufacturing_ready=False))
 print(json.dumps(dict(passed=True,actual_SOURCE_pairs=2,literal_copper_items=7)),flush=True)
if __name__=='__main__':main()
