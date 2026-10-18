"""Independent native placement review; never writes a published PCB."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pcbnew as K

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'tools'))
from hardware_build_assembly import parse, dump, children, child, value

SOURCE = ROOT/'hardware/board_review/revisions/20260930-12/motion-card-route-candidate.kicad_pcb'
REVIEW = HERE/'native-review/courtyard-review.kicad_pcb'
SOURCED = {
    'TPS62901_RPJ9': ROOT/'hardware/motion_card/CNC_MC_Power.pretty/TPS62901_RPJ9.kicad_mod',
    'XGL4020': ROOT/'hardware/motion_card/CNC_MC_Power.pretty/XGL4020.kicad_mod',
    'LTC2962_UD16': ROOT/'hardware/motion_card/CNC_MC_Power.pretty/LTC2962_UD16.kicad_mod',
    'TPS3851_DRB8': ROOT/'hardware/motion_card/CNC_IS1.pretty/TPS3851_DRB8.kicad_mod',
}


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def mm(v): return round(K.ToMM(v), 6)
def xy(p): return [mm(p.x), mm(p.y)]


def physical(b):
    return {'footprints': sorted((f.GetReference(), f.GetFPIDAsString(),
                xy(f.GetPosition()), f.GetOrientationDegrees()) for f in b.GetFootprints()),
            'pads': sorted((f.GetReference(), p.GetNumber(), xy(p.GetPosition()),
                xy(p.GetSize()), p.GetNetname(), p.GetOrientationDegrees(), p.GetShape())
                for f in b.GetFootprints() for p in f.Pads()),
            'copper': sorted((type(t).__name__, xy(t.GetStart()), xy(t.GetEnd()),
                mm(t.GetWidth(K.F_Cu) if isinstance(t,K.PCB_VIA) else t.GetWidth()),
                t.GetNetname(), t.GetLayerName()) for t in b.GetTracks())}


def bbox(poly):
    box = poly.BBox(); pos, size = box.GetPosition(), box.GetSize()
    return [mm(pos.x), mm(pos.y), mm(pos.x+size.x), mm(pos.y+size.y)]


def suggested_shift(a, b):
    # Moving footprint B with this conservative full-bbox separation avoids
    # this one pair. It is not a collision-free reroute or placement approval.
    options = [('x', a[0]-b[2]-0.05), ('x', a[2]-b[0]+0.05),
               ('y', a[1]-b[3]-0.05), ('y', a[3]-b[1]+0.05)]
    axis, delta = min(options, key=lambda p: abs(p[1]))
    return {'axis': axis, 'delta_mm': round(delta, 6),
            'scope': 'Separates this pair bounding boxes by 0.05 mm only; check all other pairs and reroute before use'}


def main():
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    inputs = {p.relative_to(ROOT).as_posix(): sha(p) for p in [SOURCE, *SOURCED.values()]}
    before = parse(SOURCE.read_text(encoding='utf-8'))
    board_tree = parse(SOURCE.read_text(encoding='utf-8'))
    updated = []
    for footprint in children(board_tree, 'footprint'):
        name = value(footprint[1]).split(':')[-1]
        if name not in SOURCED:
            continue
        ref = value(next(p for p in children(footprint, 'property') if value(p[1]) == 'Reference')[2])
        if any(value(child(g, 'layer')[1]) == 'F.CrtYd' for g in children(footprint, 'fp_rect')):
            raise ValueError('Frozen input already has a courtyard: '+ref)
        source_tree = parse(SOURCED[name].read_text(encoding='utf-8'))
        rect = next(g for g in children(source_tree, 'fp_rect') if value(child(g, 'layer')[1]) == 'F.CrtYd')
        footprint.append(rect)
        updated.append(ref)
    if len(updated) != 9:
        raise ValueError('Expected nine courtyard-only edits, got '+repr(updated))
    restored = parse(dump(board_tree))
    for footprint in children(restored, 'footprint'):
        for item in list(footprint):
            if (isinstance(item, list) and item and item[0] == 'fp_rect' and
                    child(item, 'layer') is not None and value(child(item, 'layer')[1]) == 'F.CrtYd' and
                    value(footprint[1]).split(':')[-1] in SOURCED):
                footprint.remove(item)
    if restored != before:
        raise ValueError('Review copy changed something besides the nine F.CrtYd rectangles')
    REVIEW.write_text(dump(board_tree)+'\n', encoding='utf-8')
    project = json.loads((ROOT/'reports/board-completion-20260930/mc-integrated-r03/strict-rules-review/board/motion-card-route-candidate.kicad_pro').read_text(encoding='utf-8'))
    project['meta']['filename'] = REVIEW.with_suffix('.kicad_pro').name
    REVIEW.with_suffix('.kicad_pro').write_text(json.dumps(project, indent=2)+'\n', encoding='utf-8')
    shutil.copyfile(SOURCE.parent/'fp-lib-table', REVIEW.parent/'fp-lib-table')
    for directory in (ROOT/'hardware/motion_card').glob('*.pretty'):
        shutil.copytree(directory, REVIEW.parent/directory.name, dirs_exist_ok=True)
    old_native, new_native = K.LoadBoard(str(SOURCE)), K.LoadBoard(str(REVIEW))
    if physical(old_native) != physical(new_native):
        raise ValueError('Native pad, footprint or copper changed')
    footprints = {f.GetReference(): f for f in new_native.GetFootprints()}
    polys = {}
    for ref, f in footprints.items():
        f.BuildCourtyardCaches()
        polygon = f.GetCourtyard(K.F_Cu)
        if polygon.OutlineCount():
            polys[ref] = K.SHAPE_POLY_SET(polygon)
    overlaps = []; pairs = set()
    for ref in updated:
        a = polys[ref]
        for other, b in polys.items():
            pair = tuple(sorted([ref, other]))
            if ref == other or pair in pairs:
                continue
            pairs.add(pair)
            intersection = K.SHAPE_POLY_SET(a)
            intersection.BooleanIntersection(b)
            if intersection.Area() > 0:
                ba, bb = bbox(a), bbox(b)
                overlaps.append({'new_courtyard_ref': ref, 'other_ref': other,
                    'intersection_area_mm2': round(intersection.Area()/1e12, 6),
                    'new_courtyard_bounds_mm': ba, 'other_courtyard_bounds_mm': bb,
                    'other_footprint_position_mm': xy(footprints[other].GetPosition()),
                    'conservative_other_shift_candidate': suggested_shift(ba, bb)})
    for p,h in inputs.items():
        if sha(ROOT/p) != h:
            raise ValueError('Input changed during review: '+p)
    result = {'schema_version':1, 'input_sha256': inputs,
        'review_board_sha256':sha(REVIEW), 'source_board_unchanged':True,
        'only_added_nine_courtyard_rectangles':True,
        'native_footprint_positions_pad_geometry_nets_and_copper_unchanged':True,
        'physical_footprints':len(footprints), 'physical_pads':sum(len(list(f.Pads())) for f in footprints.values()),
        'copper_items':len(list(new_native.GetTracks())),
        'new_courtyard_refs':sorted(updated), 'native_front_courtyard_count':len(polys),
        'overlap_pairs':sorted(overlaps, key=lambda row:(row['new_courtyard_ref'],row['other_ref'])),
        'manufacturing_ready':False,
        'scope':'Native geometry review of published revision 12 with nine sourced courtyards only. No published board edit; no stencil, thermal, assembly, timing, SI or physical qualification.'}
    (HERE/'native-placement-review.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['physical_footprints','physical_pads','copper_items','new_courtyard_refs','native_front_courtyard_count','overlap_pairs']}))


if __name__ == '__main__': main()
