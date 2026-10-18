"""Literal original native fill comparison and local landing attribution.

The full-before/selected-after foreign cache states are kept distinct. This
diagnoses raw differences without repairing arrays or granting acceptance.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
process = psutil.Process()
process.cpu_affinity(list(range(16, 28)))
process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys, json, hashlib, time, collections
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
H = Path(__file__).resolve().parent; ROOT = H.parent
for directory in ('sbc-power', 'coupled-recovery'):
    sys.path.insert(0, str(ROOT / directory))
import ordinary_routes as O
import contact_layout as L
BEFORE = ROOT / 'R155-known-reference-native-diagnostic-r157/measure/actual-full-refill-geometry.json'
AFTER = H / 'R157-minimal-local-three-ground-landings-selected-native-r667/selected-ground-fill/geometry.json'
API = H / 'R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665/native-exact-local-zone-chunk-rows.json'
OUT = H / 'R667-original-native-fill-array-and-locality-attribution-r707'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def put(path, value):
    path.write_text(json.dumps(value, indent=1, allow_nan=False) + '\n', encoding='utf-8')

def arrayhash(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def info(shape):
    return {'EMPTY': shape.is_empty, 'type': shape.geom_type, 'area_mm2': shape.area,
            'length_mm': shape.length, 'bounds_mm': None if shape.is_empty else list(shape.bounds),
            'WKB_SHA256': hashlib.sha256(shape.wkb).hexdigest()}

def main():
    assert not OUT.exists(); OUT.mkdir(); started = time.monotonic()
    assert sha(BEFORE) == '421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b'
    before = json.loads(BEFORE.read_bytes()); after = json.loads(AFTER.read_bytes())
    api = json.loads(API.read_bytes()); assert len(api) == 23
    landing_by_layer = collections.defaultdict(list)
    for row in api:
        landing_by_layer[row['layer']].append(Polygon([(x / 1e6, y / 1e6) for x, y in row['rings_IU'][0]]))
    # Broad diagnostic locality windows only. These are NOT source support,
    # authorization, clearance waivers or proof of an exactly local CPP effect.
    windows = {layer: unary_union(shapes).buffer(.625001) for layer, shapes in landing_by_layer.items()}
    bz = {z['uuid']: z for z in before['zones']}; az = {z['uuid']: z for z in after['zones']}
    assert len(bz) == len(before['zones']) and len(az) == len(after['zones'])
    assert set(bz) <= set(az)
    original_changed, unchanged, source_selected, unselected_blank, remote_changes = [], [], [], [], []
    ground_raws = {row['raw_net'] for row in api}
    assert {L.norm(raw) for raw in ground_raws} == {'/LOGIC_GND', '/motherboard_motors/FIELD_GND', '/motherboard_do/FIELD_B_0V'}
    for uid, old in bz.items():
        new = az[uid]
        assert old['net'] == new['net']
        for layer in sorted(set(old['fills']) | set(new['fills'])):
            a = old['fills'].get(layer, []); b = new['fills'].get(layer, [])
            row = {'original_zone_UUID': uid, 'raw_net': old['net'], 'layer': layer,
                   'before_array_SHA256': arrayhash(a), 'after_array_SHA256': arrayhash(b),
                   'native_polygon_arrays_literal_identical': a == b,
                   'before_fill_record_count': len(a), 'after_fill_record_count': len(b),
                   'selected_ground_net': old['net'] in ground_raws}
            if a == b:
                unchanged.append(row); continue
            original_changed.append(row)
            oldshape = L.poly(O.polys(a)); newshape = L.poly(O.polys(b))
            oldshape = unary_union(oldshape); newshape = unary_union(newshape)
            lost = oldshape.difference(newshape); gained = newshape.difference(oldshape)
            window = windows.get(layer)
            outside_lost = lost if window is None else lost.difference(window)
            outside_gained = gained if window is None else gained.difference(window)
            row.update({'literal_before_minus_after': info(lost), 'literal_after_minus_before': info(gained),
                        'raw_loss_outside_broad_landing_windows': info(outside_lost),
                        'raw_gain_outside_broad_landing_windows': info(outside_gained),
                        'both_zero_area_and_positive_area_witnesses_preserved': True})
            for name, shape in [('lost', lost), ('gained', gained), ('outside-lost', outside_lost), ('outside-gained', outside_gained)]:
                if not shape.is_empty:
                    path = OUT / (uid + '-' + layer.replace('.', '-') + '-' + name + '.wkb')
                    path.write_bytes(shape.wkb)
                    row[name + '_exact_WKB_file'] = str(path.resolve())
            if old['net'] in ground_raws:
                source_selected.append(row)
            if a and not b and old['net'] not in ground_raws:
                unselected_blank.append(row)
            if not outside_lost.is_empty or not outside_gained.is_empty:
                remote_changes.append(row)
            put(OUT / 'changed-original-zone-layer-arrays-checkpoint.json', original_changed)
            print('R707 original', uid, layer, 'selected', old['net'] in ground_raws, 'outside', not outside_lost.is_empty or not outside_gained.is_empty, flush=True)
    put(OUT / 'all-original-zone-layer-array-changes.json', original_changed)
    put(OUT / 'all-unchanged-original-zone-layer-arrays.json', unchanged)
    put(OUT / 'receipt.json', {'status': 'LITERAL_NATIVE_FILL_STATE_AND_LOCALITY_ATTRIBUTION_NO_REPAIR_OR_ACCEPTANCE',
        'input_SHA256': {'before_FULL_R157': sha(BEFORE), 'after_SELECTED_R667': sha(AFTER), '23_landing_intended_arrays': sha(API)},
        'original_zone_count': len(bz), 'after_zone_count': len(az), 'new_zone_UUIDs': sorted(set(az) - set(bz)),
        'changed_original_zone_layer_array_count': len(original_changed), 'unchanged_original_zone_layer_array_count': len(unchanged),
        'changed_selected_ground_original_zone_layer_array_count': len(source_selected),
        'unselected_foreign_full_before_nonempty_selected_after_blank_count': len(unselected_blank),
        'nonempty_change_outside_broad_23_landing_locality_windows_count': len(remote_changes),
        'diagnostic_locality_window_margin_mm_NOT_geometry_authorization': .625001,
        'full_before_and_selected_after_are_different_foreign_fill_states_NO_apples_to_apples_full_board_acceptance': True,
        'all_R669_raw_reference_source_fill_contact_flash_failures_and_zero_area_witnesses_remain_frozen': True,
        'possible_next_gate': 'A fully filled candidate with all foreign zones and pinned source/rules may be needed; no substitute source arrays or manual filled_polygon changes.',
        'native_jobs': 0, 'native_arrays_or_flags_or_source_rules_mutated': False, 'adopted': False,
        'elapsed_seconds': time.monotonic() - started})
    print('R707_COMPLETE', sha(OUT / 'receipt.json'), 'nonlocal', len(remote_changes), flush=True)

if __name__ == '__main__':
    main()
