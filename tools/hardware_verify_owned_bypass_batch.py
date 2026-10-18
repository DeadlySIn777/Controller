"""Check retained bypass transactions on one immutable native filled board.

The exact frozen annulus/corridor methods are reused. A checker instance keeps
only native filled polygon unions across groups on that same immutable board;
its row map and per-group audits reset. No source, geometry, anchor or layer
gate is weakened. Optional donor comparison requires literal equality with
the previously recorded individual frozen-checker results.
"""
import argparse,hashlib,json
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck,dependencies
from hardware_route_owned_bypass_loops_r02 import actual_receiving_return_anchors

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('board','owners','receipt','out'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--compare-original-results',action='store_true')
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh immutable report required')
    inputs={str(p.resolve()):sha(p) for p in (a.board,a.owners,a.receipt,Path(__file__))}
    deps=dependencies();receipt=json.loads(a.receipt.read_text());owners=json.loads(a.owners.read_text())
    groups=[g for g in receipt['owned_loops'] if g['retained']]
    original={r['ref']:r for r in receipt['actual_filled_supply_branch_return_reviews']}
    if a.compare_original_results and sha(a.board)!=receipt['board_sha256']:
        raise ValueError('Literal original comparison needs the exact recorded donor')
    board=pcbnew.LoadBoard(str(a.board.resolve()));board.BuildConnectivity()
    exact={t.m_Uuid.AsString():t for t in board.GetTracks()};fps={f.GetReference():f for f in board.GetFootprints()}
    rows_by_ref={r['ref']:r for r in owners['capacitors']};checker=NativeCollectedAnnulusCheck(board,{})
    reviews=[]
    for group in groups:
        row=rows_by_ref[group['ref']];fp=fps[row['ref']]
        supply=next(p.GetNetname() for p in fp.Pads() if p.GetNumber()==row['cap_power'])
        ret=next(p.GetNetname() for p in fp.Pads() if p.GetNumber()==row['cap_return'])
        declaration=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10)
        ids=[u for u in group['new_UUIDs'] if exact[u].GetNetname()==supply]
        checker.rows={supply:declaration};checker.audits={};items=[]
        for uid in sorted(ids):
            t=exact[uid]
            items.append(checker.via(t,declaration) if isinstance(t,pcbnew.PCB_VIA) else checker.segment(t,declaration))
        actual=dict(ref=group['ref'],passed=True,new_copper_items_checked=len(items),items=items,
          actual_signal_via_reference_audits=list(checker.audits.values()),
          exact_same_net_antipad_exceptions_only=True,real_numbered_source_pad_anchor_required=True,
          actual_flashed_and_native_connected_reference_annuli_required=True,
          exact_sequential_native_nonempty_BooleanAdd_and_final_Simplify=True,
          physical_signal_integrity_qualified=False,measured_return_impedance=False,no_source_or_PCB_mutation=True,
          independent_original_geometric_dependency_guard=True)
        if a.compare_original_results and actual!=original.get(group['ref']):
            raise ValueError('Reused exact context differs from recorded individual check: '+group['ref'])
        reviews.append(actual)
    anchors=actual_receiving_return_anchors(board,{'owned_loops':groups},owners)
    if any(sha(Path(p))!=h for p,h in inputs.items()):raise ValueError('Immutable board/input changed during checks')
    result=dict(passed=True,input_sha256=inputs,board_sha256=sha(a.board),frozen_dependencies=deps,
      retained_local_loops_checked=len(groups),actual_return_corridor_reviews=reviews,
      actual_receiving_return_anchor_reviews=anchors,
      literal_individual_result_equality_checked=a.compare_original_results,
      actual_per_board_native_fill_union_cache=True,source_or_PCB_mutated=False,
      full_power_distribution_or_measured_inductance_qualified=False,manufacturing_ready=False)
    write(a.out,result);print(dict(passed=True,loops=len(groups),receiving_endpoints=len(anchors),literal_equality=a.compare_original_results),flush=True)
if __name__=='__main__':main()
