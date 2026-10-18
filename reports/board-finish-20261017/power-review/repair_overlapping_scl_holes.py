"""Freeze a bounded two-hole -> one-hole SCL repair using saved actual evidence.

No PCB or historical evidence is rewritten. The exact packet retires one via
and adds a short F.Cu tie wholly inside the original two via copper disks.
Every original external same-net contact of the retired barrel is independently
required to touch the retained all-six-layer barrel, on its actual layer.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import re
from datetime import datetime, timezone
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / 'overlapping-scl-holes-r1'
R299 = ROOT / 'reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299'
HELPER = ROOT / 'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py'
DROP = '67c69f6a-075b-465b-96c4-89a8aff35b02'
KEEP = '8f6b8734-8176-4fbf-b83d-1da358cb6d7e'
NEW = 'f9bc120e-b043-5fb7-afaf-e59f25364585'
NET = '/motherboard_acc_control{slash}AO_I2C_SCL_HOST'
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def poly(nested):
    return unary_union([Polygon(p[0], p[1:]) for p in nested])

def disk(at, r):
    return Point(at).buffer(r, quad_segs=256)

def main():
    assert not OUT.exists(), 'Do not overwrite prior attempts'
    OUT.mkdir()
    paths = [R299/'native-full/actual-full-refill-geometry.json', R299/'native-full/actual-full-refill-via-flashes.json', R299/'native-full/partitions.json', R299/'native-full/receipt.json', R299/'filled-copy/board.kicad_pcb', R299/'copy/board.kicad_pcb', R299/'drc.json', HELPER, Path(__file__)]
    inputs = {str(p): sha(p) for p in paths}
    assert inputs[str(R299/'copy/board.kicad_pcb')] == '7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'
    assert inputs[str(R299/'filled-copy/board.kicad_pcb')] == '6d7719335455a1941c28de1ebd750e862915d483049dd90226e054bd559e1632'
    geometry = json.loads(paths[0].read_text())
    flashes = json.loads(paths[1].read_text())['vias']
    parts = json.loads(paths[2].read_text())['nets'][NET]
    vias = {v['uuid']: v for v in geometry['vias']}
    old, kept = vias[DROP], vias[KEEP]
    assert old['net'] == kept['net'] == NET
    assert old['w'] == kept['w'] == .6 and old['drill'] == kept['drill'] == .3
    assert old['locked'] and kept['locked']
    assert flashes[DROP] == flashes[KEEP] == LAYERS
    assert not any(z.get('net') == NET for z in geometry['zones']), 'Unexpected same-net filled zone requires new proof'
    distance = math.dist(old['at'], kept['at'])
    assert distance < .3  # Existing drill disks overlap.
    # Conservative finite contact proof retains the old (now removed) hole cut
    # in every old conductor. Actual hole removal can add copper to these cuts.
    holes = unary_union([disk(v['at'],v['drill']/2) for v in geometry['vias'] if math.dist(v['at'], old['at']) < 2])
    old_ring = disk(old['at'], .3).difference(holes)
    kept_ring = disk(kept['at'], .3).difference(holes)
    assert old_ring.intersection(kept_ring).area > .001
    contacts = []
    for layer in LAYERS:
        entities = []
        for t in geometry['tracks']:
            if t['net'] == NET and t['layer'] == layer:
                shape = LineString([t['s'], t['e']]).buffer(t['w']/2, quad_segs=256).difference(holes)
                entities.append((t['uuid'], 'track', shape))
        for p in geometry['pads']:
            if p['net'] == NET and layer in p['layers']:
                entities.append((f"{p['ref']}.{p['num']}", 'pad', poly(p['poly']).difference(holes)))
        for v in geometry['vias']:
            if v['net'] == NET and v['uuid'] not in (DROP, KEEP) and layer in flashes[v['uuid']]:
                entities.append((v['uuid'], 'via', disk(v['at'],v['w']/2).difference(holes)))
        for uid, kind, shape in entities:
            old_area = shape.intersection(old_ring).area
            if old_area > 1e-10:
                kept_area = shape.intersection(kept_ring).area
                assert kept_area > 1e-8, ('Would lose external finite layer contact', uid, layer)
                contacts.append({'entity': uid, 'kind': kind, 'layer': layer, 'old_contact_mm2': old_area, 'retained_barrel_contact_mm2': kept_area})
    assert {r['entity'] for r in contacts} == {'7068a896-83ce-4b01-8eca-95af65ef02bc','e927c058-612a-4a9c-ae5a-de20b6598e17','24696ad4-e6dc-4256-b46b-ed009f2d1df3'}
    assert {(r['layer'],r['kind']) for r in contacts} == {('F.Cu','track'),('B.Cu','track')}
    # Exact triangle-inequality certificate: every point of the .2 tie lies
    # within d/2+.1 of at least one old via center, below the original .3 radius.
    containment_upper_radius = distance/2 + .1
    assert containment_upper_radius < .3
    stub = LineString([kept['at'],old['at']]).buffer(.1, quad_segs=256)
    assert stub.difference(unary_union([disk(old['at'],.3),disk(kept['at'],.3)])).is_empty

    spec = importlib.util.spec_from_file_location('frozen_pcbtext', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    packets = []
    for stem in ('copy','filled-copy'):
        board = R299/stem/'board.kicad_pcb'
        _, chunks, _ = helper.split(board.read_bytes())
        byid = {helper.chunk_uuid(c): c for c in chunks if helper.chunk_uuid(c)}
        dropped = byid[DROP]
        retained = byid[KEEP]
        assert helper.chunk_kind(dropped) == helper.chunk_kind(retained) == 'via'
        (OUT/f'{stem}-{DROP}.exact-retirement-chunk').write_bytes(dropped)
        (OUT/f'{stem}-{KEEP}.retained-unchanged-chunk').write_bytes(retained)
        packets.append({'parent': str(board), 'parent_sha256': inputs[str(board)], 'retire_uuid': DROP, 'retire_exact_chunk_sha256': hashlib.sha256(dropped).hexdigest(), 'keep_uuid': KEEP, 'keep_exact_chunk_sha256': hashlib.sha256(retained).hexdigest()})
    # Keep native serialized integer geometry at 1 nm; no coordinate rounding.
    new = ('\t(segment\n\t\t(start 344.65 71.05)\n\t\t(end 344.85 70.95)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "'+NET+'")\n\t\t(uuid "'+NEW+'")\n\t)\n').encode()
    assert not any(v.get('uuid') == NEW for v in geometry['tracks'] + geometry['vias'])
    (OUT/f'{NEW}.add-track-chunk').write_bytes(new)
    drc = json.loads((R299/'drc.json').read_text())
    warning = [v for v in drc['violations'] if v['type']=='hole_to_hole' and {i['uuid'] for i in v['items']}=={DROP,KEEP}]
    assert len(warning)==1
    receipt = {
        'utc': datetime.now(timezone.utc).isoformat(),
        'verdict': 'PASS_BOUNDED_FINITE_ALL_LAYER_CONTACT_REPAIR_NATIVE_AFTER_PENDING',
        'input_sha256': inputs,
        'physical_problem': {'warning': warning[0], 'center_distance_mm': distance, 'drill_diameter_mm': .3, 'negative_edge_gap_mm': distance-.3},
        'retire_original_via': DROP, 'retained_original_via': KEEP,
        'retained_actual_native_flashes': flashes[KEEP],
        'all_external_old_finite_layer_contacts': contacts,
        'no_same_net_filled_zone_or_additional_pad_or_via_contact_omitted': True,
        'all_external_contacts_remain_directly_on_retained_native_barrel': True,
        'original_full_native_named_pad_groups': parts,
        'all_original_named_pad_relationships_preserved_by_local_graph_substitution': True,
        'added_stub': {'uuid': NEW, 'layer': 'F.Cu', 'width_mm': .2, 'length_mm': distance, 'file_sha256': hashlib.sha256(new).hexdigest()},
        'new_stub_outer_Cu_inside_original_two_via_disks': {'exact_triangle_bound_mm': containment_upper_radius, 'old_disk_radius_mm': .3, 'new_outer_reference_intrusion': False, 'ordinary_foreign_clearance_is_no_worse_outside_retired_own_hole': True},
        'only_planned_Cu_loss': 'Retired signal annular wings; every actual external layer contact has positive retained-barrel contact. No ground/reference Cu removed.',
        'native_packets': packets,
        'new_holes': 0, 'old_holes_retired': 1,
        'no_PCB_written': True, 'source_changes': 0, 'adopted': False,
        'full_native_after_refill_DRC_partitions_masks_references': 'REQUIRED_OPEN',
        'SI_and_physical_assembly_qualification': 'OPEN',
        'manufacturing_ready': False,
    }
    assert all(sha(Path(p))==h for p,h in inputs.items())
    (OUT/'repair-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'verdict':receipt['verdict'],'retire':DROP,'retain':KEEP,'external_contacts':len(contacts),'native_after':'OPEN'}))

if __name__=='__main__':
    main()
