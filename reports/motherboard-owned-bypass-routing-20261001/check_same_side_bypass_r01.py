"""Separate exact same-side bypass proof; never replaces prior loop guards.

A complete surface supply branch with no supply via returns to its adjacent
plane. A connection to the far plane is not a condition of that local loop.
Every accepted branch still needs literal SOURCE-anchored reference copper,
native circuit continuity, and short actual surface ground traces to flashed,
connected adjacent-plane annuli. This is not a power-distribution proof.
"""
import heapq
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import pcbnew
from hardware_check_return_corridors import circle, covered
from hardware_scope_anchored_reference_pieces import SourceAnchoredPiecesCheck


def uid(item):
    return item.m_Uuid.AsString()


def point(item):
    return tuple(item.GetPosition())


def surface_path(board, net, layer, start, end, maximum_mm, allowed=None):
    """Exact endpoint graph of real native surface traces; no plane/via jumps.

    A conservative refusal of an offset pad entry or a mid-track junction is
    intentional here. Such geometry needs a separately reviewed direct path.
    """
    graph = {}
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_TRACE_T or t.GetNetname() != net or t.GetLayer() != layer:
            continue
        if allowed is not None and uid(t) not in allowed:
            continue
        if t.GetWidth() < pcbnew.FromMM(.20):
            continue
        a, b = tuple(t.GetStart()), tuple(t.GetEnd())
        length = math.dist(a, b) / 1e6
        if not length:
            continue
        graph.setdefault(a, []).append((b, length, uid(t)))
        graph.setdefault(b, []).append((a, length, uid(t)))
    todo = [(0., start, ())]
    best = {start: 0.}
    while todo:
        cost, node, path = heapq.heappop(todo)
        if cost > best[node]:
            continue
        if node == end:
            return dict(length_mm=cost, actual_surface_trace_UUIDs=list(path))
        for nxt, length, ident in graph.get(node, []):
            total = cost + length
            if total <= maximum_mm and total < best.get(nxt, math.inf):
                best[nxt] = total
                heapq.heappush(todo, (total, nxt, path + (ident,)))
    raise ValueError('No complete bounded actual surface trace path')


def check_group(board, group, row, mapping, checker=None):
    """Accept an explicitly identified complete local supply branch only."""
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    def pad(ref, number):
        matches = [p for p in fps[ref].Pads() if p.GetNumber() == number]
        if len(matches) != 1:
            raise ValueError('Exact single native SOURCE pad required')
        return matches[0]
    cp = pad(row['ref'], row['cap_power'])
    cr = pad(row['ref'], row['cap_return'])
    owners = [pad(n['ref'], n['pin']) for n in row['power_nodes']]
    returns = [pad(n['ref'], n['pin']) for n in row['return_nodes']]
    if not owners or not returns or group['ref'] != row['ref']:
        raise ValueError('Exact reviewed capacitor owner required')
    supply, ground = cp.GetNetname(), cr.GetNetname()
    layer = cp.GetParentFootprint().GetLayer()
    if layer not in (pcbnew.F_Cu, pcbnew.B_Cu) or supply == ground:
        raise ValueError('Distinct supply/return and one outer surface required')
    if any(p.GetParentFootprint().GetLayer() != layer for p in [cr, *owners, *returns]):
        raise ValueError('Opposite-side owner/return is outside the same-side proof')
    if any(p.GetNetname() != supply for p in owners) or any(p.GetNetname() != ground for p in returns):
        raise ValueError('Actual owner supply/return identity mismatch')
    source_pads = {p['uuid']: p for p in mapping['pads']}
    for p in [cp, cr, *owners, *returns]:
        source = source_pads.get(uid(p))
        if source is None or source['net'] != p.GetNetname() or source.get('native_nc'):
            raise ValueError('Missing, foreign or NC SOURCE endpoint')
    branch = group.get('complete_supply_branch_UUIDs', [])
    if not branch or len(set(branch)) != len(branch):
        raise ValueError('Explicit nonempty unique complete supply branch required')
    exact = {uid(t): t for t in board.GetTracks()}
    for ident in branch:
        t = exact.get(ident)
        if t is None or t.Type() != pcbnew.PCB_TRACE_T or t.GetNetname() != supply or t.GetLayer() != layer:
            raise ValueError('Supply branch contains missing/foreign/via/opposite-layer copper')
    pair = None
    for owner in owners:
        try:
            path = surface_path(board, supply, layer, point(cp), point(owner), 8., set(branch))
        except ValueError:
            continue
        if set(path['actual_surface_trace_UUIDs']) == set(branch):
            pair = owner, path
            break
    if pair is None:
        raise ValueError('Declared supply branch is not one complete <=8 mm surface path')
    owner, path = pair
    if uid(owner) not in {uid(t) for t in conn.GetConnectedItems(cp)}:
        raise ValueError('Actual native supply endpoints are disconnected')
    adjacent = pcbnew.In1_Cu if layer == pcbnew.F_Cu else pcbnew.In4_Cu
    declaration = dict(return_net=ground,
                       reference_layers={board.GetLayerName(layer): board.GetLayerName(adjacent)},
                       allow_vias=False, reference_corridor_margin_mm=.10)
    checker = checker or SourceAnchoredPiecesCheck(board, {supply: declaration}, mapping)
    route_reviews = [checker.segment(exact[ident], declaration) for ident in branch]
    fill = checker.reference(ground, adjacent)
    actual_vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    endpoint_reviews = []
    return_connected = {uid(t) for t in conn.GetConnectedItems(cr)} | {uid(cr)}
    for endpoint in [cr, *returns]:
        if uid(endpoint) not in return_connected:
            raise ValueError('Native capacitor and receiving return circuit is open')
        peers = {uid(t) for t in conn.GetConnectedItems(endpoint)}
        anchors = []
        for via in actual_vias:
            if uid(via) not in peers or via.GetNetname() != ground:
                continue
            if math.dist(point(via), point(endpoint)) > pcbnew.FromMM(2.):
                continue
            if not (via.IsOnLayer(adjacent) and via.FlashLayer(adjacent) and conn.IsConnectedOnLayer(via, adjacent)):
                continue
            if not covered(circle(point(via), via.GetWidth(pcbnew.F_Cu)/2-pcbnew.FromMM(.01)), fill):
                continue
            try:
                ground_path = surface_path(board, ground, layer, point(endpoint), point(via), 2.)
            except ValueError:
                continue
            anchors.append(dict(uuid=uid(via), reference_layer=board.GetLayerName(adjacent),
                                actual_flashed_native_connected_annulus=True,
                                actual_surface_ground_path=ground_path))
        if not anchors:
            raise ValueError('Receiving return lacks bounded surface path to actual adjacent SOURCE reference')
        endpoint_reviews.append(dict(ref=endpoint.GetParentFootprint().GetReference(),
                                     pin=endpoint.GetNumber(), anchors=anchors))
    return dict(passed=True, capacitor=row['ref'], supply_net=supply, return_net=ground,
                surface=board.GetLayerName(layer), adjacent_reference=board.GetLayerName(adjacent),
                complete_supply_path=path, no_supply_layer_transition=True,
                full_SOURCE_anchored_reference_segment_reviews=route_reviews,
                actual_return_endpoint_reviews=endpoint_reviews,
                complete_failed_reference_piece_ledger=checker.full_native_report['unanchored_components'],
                previously_accepted_loop_guards_unchanged=True,
                physical_impedance_or_global_power_qualified=False, manufacturing_ready=False)
