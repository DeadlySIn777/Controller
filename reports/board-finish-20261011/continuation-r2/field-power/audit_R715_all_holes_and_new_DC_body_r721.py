"""Supplement R719 with all original pad holes and the new DC ground body.

No native mask, physical sheet or current rating is inferred from this check.
Actual foreign fill is hard; the sparse nominee has no fill withdrawals.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
p = psutil.Process(); p.cpu_affinity(list(range(16, 28))); p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys, json, pickle, hashlib, time, collections
from pathlib import Path
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
H = Path(__file__).resolve().parent; ROOT = H.parent
for directory in (ROOT, ROOT / 'sbc-power', ROOT / 'coupled-recovery'):
    sys.path.insert(0, str(directory))
import contact_layout as L
import ordinary_routes as O
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import R157_native_selected_actual_conversion_r673 as N
OUT = H / 'R715-all-native-pad-holes-foreign-fill-and-new-DC-body-supplement-r721'
P = H / 'R157-high-current-FBG-actual-source-parallel-stitch-nomination-r715'
R719 = H / 'R715-FBG-parallel-stitch-actual-baseline-source-reference-independent-r719'
M = ROOT / 'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
NET = '/motherboard_do/FIELD_B_0V'; RAW = '/motherboard_do{slash}FIELD_B_0V'
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(path, value): path.write_text(json.dumps(value, indent=1, allow_nan=False) + '\n', encoding='utf-8')
def info(shape):
    return {'EMPTY': shape.is_empty, 'geom_type': shape.geom_type, 'area_mm2': shape.area,
            'length_mm': shape.length, 'bounds_mm': None if shape.is_empty else list(shape.bounds),
            'WKB_SHA256': hashlib.sha256(shape.wkb).hexdigest()}
def main():
    assert not OUT.exists(); OUT.mkdir(); start = time.monotonic()
    assert sha(P / 'receipt.json') == '156f6e97f1628baa9f8d39c67a4e953d7b5c5b1ddf345a1b5f8ee68846c1adf6'
    assert sha(R719 / 'receipt.json') == '55abb18b9fad6affedaf2c16f3299296bac619553086b97fd0032df17a13f62b'
    packet = P / 'only-one-new-parallel-FBG-barrel-and-B-source-stub-NOMINEE.pkl'
    assert sha(packet) == 'de776f9dc5f95bc937d88e90d89039c8337641f9f4be5dac52284fddafe811c0'
    item, = pickle.loads(packet.read_bytes()); via = item['via']; track, = item['tracks']
    N.assert_R157_actual_before(); assert sha(M) == 'ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
    g, h, b, q, c = pickle.loads(M.read_bytes())
    axis = Point(via['x'], via['y']); path = LineString([track['a'], track['b']])
    newdrill = axis.buffer(via['drill']/2, quad_segs=128)
    rawbody = path.buffer(track['w']/2, quad_segs=128)
    holes, tree = K.hole_context(h)
    pad_hole_rows = []; stub_hole_rows = []
    # The containing rectangular envelope is a conservative bound for every
    # serialized round/oval/native pad-hole shape, not an inscribed chord gap.
    for pad in h['pads']:
        for hole_index, hole in enumerate(L.poly(pad.get('hole') or [])):
            gap = axis.distance(hole.envelope) - via['drill']/2
            row = {'UUID': pad['uuid'], 'ref': pad['ref'], 'pin': str(pad['num']),
                   'NPTH': bool(pad['npth']), 'raw_net': pad['net'], 'hole_index': hole_index,
                   'hole_WKB_SHA256': hashlib.sha256(hole.wkb).hexdigest(),
                   'conservative_new_hole_to_original_pad_hole_gap_mm': gap,
                   'required_mm': .275, 'PASS': gap >= .275}
            pad_hole_rows.append(row)
            if pad['net'] == RAW and not pad['npth']:
                continue
            edgegap = path.distance(hole.envelope) - track['w']/2
            stub_hole_rows.append({**row, 'conservative_B_stub_to_foreign_or_NPTH_pad_hole_gap_mm': edgegap,
                                   'PASS': edgegap >= .275})
    observed = json.loads((N.R157 / 'actual-full-refill-via-flashes.json').read_bytes())['vias']
    for old in h['vias']:
        if old['net'] == RAW:
            continue
        gap = path.distance(Point(old['x'], old['y'])) - track['w']/2 - old['drill']/2
        stub_hole_rows.append({'UUID': old['uuid'], 'kind': 'foreign_ordinary_via_hole', 'raw_net': old['net'],
                               'true_B_stub_to_foreign_hole_gap_mm': gap, 'required_mm': .275, 'PASS': gap >= .275})
    native = json.loads((N.R157 / 'actual-full-refill-geometry.json').read_bytes())
    foreign_fill_rows = []
    own_domain = h['domains_normalized'][NET]
    for zone in native['zones']:
        if zone['net'] == RAW:
            continue
        domain = h['domains_normalized'][L.norm(zone['net'])]
        needed = max(.15 if domain == own_domain else .6, zone['clearance_mm']) + .025
        for layer, records in zone['fills'].items():
            for index, fill in enumerate(L.poly(O.polys(records))):
                via_gap = axis.distance(fill) - via['d']/2
                stub_gap = path.distance(fill) - track['w']/2 if layer == 'B.Cu' else None
                foreign_fill_rows.append({'UUID': zone['uuid'], 'layer': layer, 'index': index, 'raw_net': zone['net'],
                    'fill_WKB_SHA256': hashlib.sha256(fill.wkb).hexdigest(), 'required_mm': needed,
                    'true_via_to_actual_foreign_fill_gap_mm': via_gap,
                    'true_B_stub_to_actual_foreign_fill_gap_mm': stub_gap,
                    'PASS': via_gap >= needed and (stub_gap is None or stub_gap >= needed)})
    cache = R719 / 'prospective-one-stitch-three-ground-all-drilled-groups.pkl'
    assert sha(cache) == 'bfcd728db792979d06164989ee1f5c9a984421ed1e3b62b734e640144176e13d'
    groups = pickle.loads(cache.read_bytes()); root = K.root(groups[NET], 'J11005', '2')
    oldhole = next(v for v in h['vias'] if v['uuid'] == '7a9206b1-d64b-4ebf-9424-6c4d6d434176')
    physical = rawbody.difference(unary_union([holes[int(i)] for i in tree.query(rawbody, predicate='intersects')] + [newdrill]))
    rooted_newbody = unary_union([r['shape'] for r in root if r['kind']=='track' and r['uuid']==track['uuid'] and r['layer']=='B.Cu'])
    body_missing = physical.difference(rooted_newbody); body_excess = rooted_newbody.difference(physical)
    actual_refs = K.source_refs(root)
    raw_ref_gap = rawbody.difference(actual_refs['B.Cu'])
    physical_ref_gap = physical.difference(actual_refs['B.Cu'])
    for name, shape in [('new-B-stub-drilled-physical-body', physical), ('new-B-stub-source-component-body', rooted_newbody),
                        ('new-B-stub-raw-In4-reference-gap', raw_ref_gap), ('new-B-stub-drilled-In4-reference-gap', physical_ref_gap),
                        ('new-B-stub-source-body-missing', body_missing), ('new-B-stub-source-body-excess', body_excess)]:
        (OUT/(name+'.wkb')).write_bytes(shape.wkb)
    old_ann = Point(oldhole['x'], oldhole['y']).buffer(oldhole['d']/2, quad_segs=128).difference(Point(oldhole['x'], oldhole['y']).buffer(oldhole['drill']/2, quad_segs=128))
    old_B_contacts = unary_union([r['shape'] for r in root if r['kind']=='via' and r['uuid']==oldhole['uuid'] and r['layer']=='B.Cu'])
    ann_contact = physical.intersection(old_ann).intersection(old_B_contacts)
    body = {'raw_full_body': info(rawbody), 'all_drill_subtracted_physical_body': info(physical),
            'exact_physical_body_missing_from_J5_source_component': info(body_missing),
            'source_component_body_excess': info(body_excess), 'actual_existing_B_source_annular_attachment': info(ann_contact),
            'raw_full_body_actual_In4_fill_reference_gap': info(raw_ref_gap),
            'drill_subtracted_body_actual_In4_fill_reference_gap': info(physical_ref_gap),
            'classification': 'DC same-net ground conductor; old routed-reference preservation remains absolute; no automatic fast-signal shadow PASS',
            'complete_signed_return_current_drop_loop_barrel_thermal_and_native': 'OPEN'}
    put(OUT/'all-original-PTH-NPTH-pad-hole-audit.json', pad_hole_rows)
    put(OUT/'B-stub-all-foreign-and-NPTH-hole-audit.json', stub_hole_rows)
    put(OUT/'all-actual-native-foreign-fill-hard-audit.json', foreign_fill_rows)
    put(OUT/'new-DC-B-stub-physical-source-and-raw-reference-scope.json', body)
    failed = any(not r['PASS'] for r in pad_hole_rows+stub_hole_rows+foreign_fill_rows) or not body_missing.is_empty or not body_excess.is_empty or ann_contact.is_empty
    put(OUT/'receipt.json', {'status': 'R715_SUPPLEMENT_ALL_HOLES_FOREIGN_FILL_AND_DRILLED_DC_SOURCE_BODY_PASS_NATIVE_CURRENT_OPEN' if not failed else 'R715_SUPPLEMENT_REPAIR_REQUIRED',
        'R715_receipt_SHA256': sha(P/'receipt.json'), 'R719_receipt_SHA256': sha(R719/'receipt.json'),
        'R719_groups_SHA256': sha(cache), 'sparse_packet_SHA256': sha(packet),
        'all_original_pad_holes_checked': len(pad_hole_rows), 'all_foreign_or_NPTH_stub_holes_checked': len(stub_hole_rows),
        'all_actual_foreign_fill_pieces_checked': len(foreign_fill_rows),
        'all_hole_or_actual_foreign_fill_guard_error_count': sum(not r['PASS'] for r in pad_hole_rows+stub_hole_rows+foreign_fill_rows),
        'new_drilled_DC_source_body': body, 'unchanged_foreign_fills_no_antipads': True,
        'original_actual_masks_unchanged_new_via_masks_prospective': True,
        'R715_true_Cu_native_rule_and_exact_later_peer_scope_retained': True,
        'source_current_simplex_sharing_native_actual_contact_rating_loop_thermal': 'OPEN',
        'native_jobs': 0, 'adopted': False, 'elapsed_seconds': time.monotonic()-start})
    print('R721_COMPLETE', sha(OUT/'receipt.json'), 'FAIL', failed, 'rawReferenceGap', raw_ref_gap.area, 'physicalReferenceGap', physical_ref_gap.area, flush=True)
if __name__=='__main__': main()
