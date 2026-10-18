"""Recheck the exact frozen nine-group ordinary donor on a combined board.

No board, source, warning, reference or routing rule is edited. The complete
fresh native failed-piece ledger stays visible; eligibility is piece-local.
"""
from pathlib import Path
import argparse, json, sys
sys.path.insert(0, str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_route_critical_digital_wip_r03 as clusters
e = o.engine
ROOT = Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root71-local-clipped-r02')
BASE = Path('reports/motherboard-pcb-integration-20261001/source26-four-reference-closures-r71/motherboard-bounded-merged-candidate.kicad_pcb')

def copper(tree):
    return {e.value(e.child(n, 'uuid')[1]): e.dump(n)
            for kind in ('segment', 'via', 'arc') for n in e.children(tree, kind)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--board', required=True)
    ap.add_argument('--map', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--drc'); a = ap.parse_args()
    bp, mp, out = [Path(p).resolve() for p in (a.board, a.map, a.out)]
    if out.exists(): raise ValueError('A new immutable verification directory is required')
    out.mkdir(parents=True)
    frozen = {str(p.resolve()): e.sha(p) for p in
              (bp, mp, ROOT/'manifest.json', ROOT/'proposed-local-groups.json',
               ROOT/'review.json', Path('hardware/motherboard/design.json'),
               Path('hardware/motherboard/netlist.xml'))}
    manifest, plan, prior = [e.read(ROOT/n) for n in
                            ('manifest.json', 'proposed-local-groups.json', 'review.json')]
    if not prior['passed'] or len(plan['groups']) != 9 or len(plan['added_copper_UUIDs']) != 56:
        raise ValueError('Only the independently reviewed exact nine/56 donor is accepted')
    o.INPUT_BOARD = BASE
    source = o.frozen_review_check(manifest, Path('hardware/motherboard/design.json'),
                                 Path('hardware/motherboard/netlist.xml'))
    o.MAPPING = e.read(mp)
    if o.MAPPING['input_sha256'].get(str(bp)) != e.sha(bp):
        raise ValueError('Fresh actual combined-board source-map hash does not match')
    donor = copper(e.parse((ROOT/'motherboard-ordinary-local-candidate.kicad_pcb').read_text()))
    actual = copper(e.parse(bp.read_text()))
    for uid in plan['added_copper_UUIDs']:
        if actual.get(uid) != donor[uid]:
            raise ValueError('Literal ordinary donor copper geometry/net/identity changed: '+uid)
    board = pcbnew.LoadBoard(str(bp)); board.BuildConnectivity()
    population, _ = e.native_source_check(board, e.read('hardware/motherboard/design.json'),
                                         Path('hardware/motherboard/netlist.xml'))
    padmap = {p.m_Uuid.AsString(): p for f in board.GetFootprints() for p in f.Pads()}
    positive = []
    for g in plan['groups']:
        p, q = [padmap[uid] for uid in g['source_pad_UUIDs']]
        if p.GetNetname() != g['net'] or q.GetNetname() != g['net']:
            raise ValueError('Actual ordinary SOURCE endpoint net changed')
        connected = {x.m_Uuid.AsString() for x in board.GetConnectivity().GetConnectedItems(p)}
        if q.m_Uuid.AsString() not in connected:
            raise ValueError('Literal completed ordinary SOURCE pair disconnected: '+g['net'])
        positive.append(dict(net=g['net'], source_pair=g['source_pair'], actual_joined=True,
                             new_copper_UUIDs=g['new_copper_UUIDs']))
    retained = clusters.clusters_preserved(clusters.source_clusters(pcbnew.LoadBoard(str(BASE))), board)
    # Recomputes the full actual native source-anchor report and grants only
    # genuinely passed filled pieces to the unchanged corridor/annulus guard.
    returns = o.actual_return_check(board, set(plan['added_copper_UUIDs']), manifest['nets'])
    native = None
    if a.drc:
        dp = Path(a.drc).resolve(); native = e.read(dp)
        if native.get('ignored_checks') or any(v.get('severity') == 'error' for v in native['violations']):
            raise ValueError('Combined actual native errors/ignored checks remain')
        native = dict(path=str(dp), sha256=e.sha(dp), all_unsuppressed_violations=native['violations'])
    if frozen != {p: e.sha(p) for p in frozen}:
        raise ValueError('Frozen combined-board/source/ledger input changed during verification')
    r = dict(passed=True, scope='Exact nine ordinary SOURCE pairs/56 F segments only',
             board_sha256=e.sha(bp), map_sha256=e.sha(mp), inputs=frozen,
             tool_sha256=e.sha(__file__), source_review=source, source_population=population,
             literal_copper_identity_and_geometry_preserved=True, prior_SOURCE_clusters=retained,
             actual_complete_SOURCE_pairs=positive, actual_full_native_return_guard=returns,
             complete_failed_reference_piece_ledger=returns['full_failed_reference_piece_ledger'],
             native_drc=native, original_nine_persisted_route_cut_controls=prior['actual_progressive_route_cut_negative_checks'],
             combined_alternative_routes_do_not_waive_original_cut_controls=True,
             whole_return_net_qualification=False, whole_board_reference_qualification=False,
             manufacturing_ready=False)
    e.write(out/'review.json', r)
    print(json.dumps(dict(passed=True, SOURCE_pairs=9, actual_copper_items_checked=56,
                          complete_failed_reference_pieces=len(r['complete_failed_reference_piece_ledger']))), flush=True)

if __name__ == '__main__': main()
