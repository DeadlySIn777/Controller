"""Use only literal, physically SOURCE-anchored native reference pieces.

This is a local routing eligibility check, not whole-net qualification. The
complete native report and every unanchored piece remain in the receipt. The
unchanged geometric/annulus checker receives a smaller subset of real filled
copper; an isolated same-named island can never cover a proposed route.
"""
from pathlib import Path
import copy, json
import pcbnew
from hardware_scope_critical_reference_qualification import sha, read, anchor_check
from hardware_validate_motherboard_return_planes_r02 import validate
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck, dependencies


def eligible(full, nets, layers):
    rows = []
    for row in full['filled_components']:
        if row['net'] in nets and row['reference_layer'] in layers and row['passed']:
            anchor_check(row)
            rows.append(copy.deepcopy(row))
    if not rows or any(not any(r['net'] == n and r['reference_layer'] == l
                              for r in rows) for n in nets for l in layers):
        raise ValueError('A requested side/domain has no real SOURCE-anchored native piece')
    return rows


def qualify(full_report, source_map, board_path, nets, layers):
    full_report, source_map, board_path = [Path(p).resolve() for p in
                                          (full_report, source_map, board_path)]
    full = read(full_report); mapping = read(source_map)
    nets, layers = sorted(set(nets)), sorted(set(layers))
    if not nets or not layers or not set(layers) <= {'In1.Cu', 'In4.Cu'}:
        raise ValueError('Explicit adjacent native reference scope required')
    if full['board_sha256'] != sha(board_path) or full['source_map_sha256'] != sha(source_map):
        raise ValueError('Exact native board/source-map/full-report binding required')
    if full['exact_source_pad_inventory_checked'] != len(mapping['pads']):
        raise ValueError('Complete SOURCE pad inventory required')
    selected = eligible(full, nets, layers)
    return dict(type='literal_source_anchored_piece_eligibility', schema_version=1,
        passed=True, scope_only=True, whole_board_reference_qualification=False,
        whole_return_net_qualification=False, manufacturing_ready=False,
        board_sha256=sha(board_path), selected_return_nets=nets,
        selected_reference_layers=layers,
        full_plane_review=dict(path=str(full_report), sha256=sha(full_report),
                               passed=full['passed']),
        source_map=dict(path=str(source_map), sha256=sha(source_map)),
        eligible_filled_components=selected,
        complete_unanchored_components=copy.deepcopy(full['unanchored_components']),
        scope='Routes must fit entirely in actual SOURCE-anchored native pieces; other pieces remain failed.')


def verify_receipt(receipt, board_path, rows):
    proof = read(receipt); full = proof['full_plane_review']; mapping = proof['source_map']
    for item in (full, mapping):
        if sha(item['path']) != item['sha256']:
            raise ValueError('Frozen complete native evidence changed')
    expected = qualify(full['path'], mapping['path'], board_path,
                       proof['selected_return_nets'], proof['selected_reference_layers'])
    if proof != expected:
        raise ValueError('Eligibility receipt changed or promotes unanchored copper')
    for row in rows.values():
        if row['return_net'] not in proof['selected_return_nets'] or not set(
                row['reference_layers'].values()) <= set(proof['selected_reference_layers']):
            raise ValueError('Route leaves exact selected native side/domain scope')
    return proof


class SourceAnchoredPiecesCheck(NativeCollectedAnnulusCheck):
    def __init__(self, board, rows, mapping):
        dependencies()
        super().__init__(board, rows)
        self.full_native_report = validate(board, mapping)
        self.selected_keys = {(r['net'], board.GetLayerID(r['reference_layer']), r['filled_piece'])
                              for r in self.full_native_report['filled_components'] if r['passed']}
        for row in self.full_native_report['filled_components']:
            if row['passed']: anchor_check(row)
        nets = {r['return_net'] for r in rows.values()}
        layers = {board.GetLayerID(l) for r in rows.values() for l in r['reference_layers'].values()}
        self.native_fills = collect_native_reference_fills(board, nets, layers)
        self.eligible_piece_audit = []

    def reference(self, net, layer):
        key = net, layer
        if key not in self.fills:
            native = self.native_fills.get(key, pcbnew.SHAPE_POLY_SET())
            union = pcbnew.SHAPE_POLY_SET()
            for index, piece in enumerate(split_polygons(native)):
                if (net, layer, index) in self.selected_keys:
                    # Only actual filled polygons, with their holes intact.
                    union.BooleanAdd(piece)
                    self.eligible_piece_audit.append(dict(net=net,
                        reference_layer=self.board.GetLayerName(layer),
                        filled_piece=index, native_area_mm2=piece.Area()/1e12))
            union.Simplify()
            self.fills[key] = union
            self.zone_clearance[key] = max((z.GetLocalClearance() for z in self.board.Zones()
                if not z.GetIsRuleArea() and z.GetNetname() == net and z.HasFilledPolysForLayer(layer)), default=0)
        if not self.fills[key].OutlineCount():
            raise ValueError('No physically SOURCE-anchored native reference piece')
        return self.fills[key]
