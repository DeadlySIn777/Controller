"""Actual exact SDO Source coupling/own-reference checks on a combined board."""
from pathlib import Path
import argparse,sys,json
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_critical_digital_wip_r03 as c
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_owned_bypass_loops_wip_r03 as w
e=authority.engine
ROOT=Path('reports/motherboard-critical-routing-20261001/actual-AO1-SDO-root74-corridor-r03')
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
SOURCE=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
def cu(tree):return{e.value(e.child(n,'uuid')[1]):e.dump(n)for k in('segment','via','arc')for n in e.children(tree,k)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',required=True);ap.add_argument('--map',required=True);ap.add_argument('--drc',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 bp,mp,dp,out=[Path(p).resolve()for p in(a.board,a.map,a.drc,a.out)];out.mkdir(exist_ok=False,parents=True)
 prior=e.read(ROOT/'review.json');inventory=e.read(ROOT/'independent-connectivity/review.json');source=e.read(SOURCE)
 if not prior['passed']or not inventory['source_net_checks_pass']or inventory['orphan_copper_items']or len(prior['new_copper_UUIDs'])!=4:raise ValueError('Exact accepted four-Cu SDO donor required')
 if source['source_design_sha256']!=e.sha('hardware/motherboard/design.json')or source['source_netlist_sha256']!=e.sha('hardware/motherboard/netlist.xml'):raise ValueError('Actual source26 critical identity changed')
 frozen={str(p.resolve()):e.sha(p)for p in(bp,mp,dp,ROOT/'review.json',ROOT/'new-fragment-retirement.json',SOURCE,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
 old=cu(e.parse((ROOT/'motherboard-AO1-SDO-corridor-candidate.kicad_pcb').read_text()));actual=cu(e.parse(bp.read_text()))
 if any(actual.get(u)!=old[u]for u in prior['new_copper_UUIDs']):raise ValueError('Literal four SDO net/land/UUID/geometries changed')
 mapping=e.read(mp)
 if mapping['input_sha256'].get(str(bp))!=e.sha(bp):raise ValueError('Fresh actual combined-board map binding failed')
 native=e.read(dp);known=w.reviewed_wip_warnings(e.read(BASE.parent/'drc.json'),e.read(BASE.parent/'baseline-disposition.json'),e.sha(BASE))
 if native.get('ignored_checks')or w.new_route_defects(native,known):raise ValueError('Actual combined native defects/ignored checks remain')
 b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity();pop,_=e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
 pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()};p,q=pads['U14626','3'],pads['U14623','10'];name='/motherboard_analog_output/AO1_DAC_SDO'
 if p.GetNetname()!=name or q.GetNetname()!=name or q.m_Uuid.AsString()not in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}:raise ValueError('Actual DAC SDO Source endpoints disconnected')
 row=source['nets'][name];check=pieces.SourceAnchoredPiecesCheck(b,{name:row},mapping);tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};returns=[]
 for u in prior['new_copper_UUIDs']:returns.append(dict(uuid=u,actual_SOURCE_owned_reference=check.segment(tracks[u],row)))
 retained=c.clusters_preserved(c.source_clusters(pcbnew.LoadBoard(str(BASE))),b)
 if frozen!={p:e.sha(p)for p in frozen}:raise ValueError('Frozen actual combined Source/board/evidence changed')
 e.write(out/'review.json',dict(passed=True,scope='One actual DAC SDO Source pair/four F segments only',inputs=frozen,board_sha256=e.sha(bp),map_sha256=e.sha(mp),tool_sha256=e.sha(__file__),source_population=pop,prior_SOURCE_clusters=retained,actual_SOURCE_pair=['U14626.3','U14623.10'],actual_SOURCE_pair_joined=True,actual_full_native_SOURCE_owned_reference_proofs=returns,complete_failed_reference_piece_ledger=check.full_native_report['unanchored_components'],eligible_piece_audit=check.eligible_piece_audit,original_persisted_physical_cut_negative=prior['persisted_actual_route_cut_negative'],original_SOURCE_empty_fragment_proof=prior['new_SOURCE_empty_fragment_retirement'],all_unsuppressed_native_warnings=native['violations'],no_new_native_defects=True,no_ignored_checks=True,own_return='/motherboard_analog_output/AO1_COM',unchanged_reference_margin_mm=.40,loaded_waveform_qualification=False,whole_board_reference_qualification=False,manufacturing_ready=False))
 print(json.dumps(dict(passed=True,actual_SOURCE_pairs=1,exact_copper_items=4)),flush=True)
if __name__=='__main__':main()
