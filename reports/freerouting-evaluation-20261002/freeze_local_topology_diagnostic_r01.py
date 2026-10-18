"""Freeze completed read-only topology diagnostics; no router or board writes."""
from pathlib import Path
import json, sys
ROOT=Path.cwd()
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01')]
import hardware_route_selected_additive_r02 as e
from shapely import wkt
from shapely.geometry import Polygon
from shapely.ops import nearest_points
R=ROOT/'reports/freerouting-evaluation-20261002'
D=R/'ROOT103-local-F-configuration-space-r02'
OUT=R/'ROOT103-local-topology-handoff-r01'
OUT.mkdir(exist_ok=False)
review=e.read(D/'review.json')
rows=[]
for row in review['all_endpoint_rows']:
    p=D/(row['net'].rsplit('/',1)[-1]+'-geometry.json')
    raw=e.read(p)
    free=wkt.loads(raw['conservative_F_free_space_WKT'])
    pieces=[free] if isinstance(free,Polygon) else list(free.geoms)
    source_ids=row['endpoints'][0]['free_components']
    target_ids=row['endpoints'][1]['free_components']
    pairs=[]
    for a in source_ids:
        for b in target_ids:
            left,right=nearest_points(pieces[a],pieces[b])
            pairs.append(dict(source_component=a,receiving_component=b,source_bounds_mm=[v/1e6 for v in pieces[a].bounds],receiving_bounds_mm=[v/1e6 for v in pieces[b].bounds],source_area_mm2=pieces[a].area/1e12,receiving_area_mm2=pieces[b].area/1e12,closest_component_distance_mm=left.distance(right)/1e6,closest_boundary_points_mm=[[left.x/1e6,left.y/1e6],[right.x/1e6,right.y/1e6]],boundary_proximity_not_a_physical_route_or_cut_proof=True))
    rows.append(dict(net=row['net'],endpoints=row['endpoints'],DSN_only_common_endpoint_components=row['DSN_only_common_endpoint_components'],DSN_plus_native_foreign_metal_common_endpoint_components=row['common_endpoint_components'],component_details=pairs,geometry_file=str(p.relative_to(ROOT)),geometry_sha256=e.sha(p)))
failure=R/'ROOT103-local-F-configuration-space-r01'/'execution-failure.json'
e.write(failure,dict(passed=False,script=str((R/'inspect_local_F_configuration_space_r01.py').relative_to(ROOT)),script_sha256=e.sha(R/'inspect_local_F_configuration_space_r01.py'),exception_type='AttributeError',exception_message="'BOARD_ITEM_CONTAINER' object has no attribute 'GetReference'",failed_operation='p.GetParent().GetReference()',no_completed_diagnostic=True,no_source_or_board_writes=True,successor='ROOT103-local-F-configuration-space-r02/review.json'))
paths=[D/'review.json',R/'inspect_local_F_configuration_space_r02.py',R/'inspect_local_F_configuration_space_r01.py',failure,R/'ROOT103-visual-local-native-import-r01'/'no-improvement-rejection.json',R/'ROOT103-visual-local-diagnostic-actual-router-r07'/'routing-result.json']
receipt=dict(diagnostic_completed=True,route_accepted=False,copper_adopted=False,no_source_or_board_writes=True,no_router_trial_started=True,copy_baseline_board_sha256=review['source_board_sha256'],copy_selected_DSN_sha256=review['selected_DSN_sha256'],inputs=review['inputs'],evidence={str(p.relative_to(ROOT)):e.sha(p) for p in paths},rows=rows,interpretation='F endpoint centers and straight outward escapes are clear. Exported polygon/reference masks alone retain a common configuration-space component. Including retained native foreign pad/track/via obstacles separates the endpoints in this conservative local F diagnostic. This supports native metal obstruction, but does not prove physical impossibility or diagnose a specific Freerouting failure code.',limits=['Only F.Cu in native x300..330/y120..150 mm is analyzed.','No complete width-compliant F route, other-layer route or signal transfer is accepted.','Native obstacles use 1 um outward polygon approximation; via span treatment can overblock unflashed annuli.','No return-reference, plane-antipad, clearance, Source, signal-via or protected-copper guard is relaxed.','Actual SES has zero approved new networks; native import rejection is retained.','The next board comes from the user Argus attempt; no further router trial or integration before reconciliation.'],authoritative_current='Source26 ROOT104 / CAD30; copy-only trial remains exact ROOT103')
e.write(OUT/'receipt.json',receipt)
(OUT/'README.md').write_text('''# Bounded routing topology handoff

This is a read-only diagnostic of the exact ROOT103 copy used for the completed local Freerouting evaluation. No copper was accepted or adopted. The current adopted board remains Source26 ROOT104 / CAD30.

For both OBS8_INVERTED and OBS9_INVERTED, the actual Source and receiving F-pad centers are clear. Exported polygon/reference masks alone leave both endpoints in one connected configuration-space component. Retained foreign native pads, traces and vias separate them when the 0.20 mm trace and 0.15 mm clearance are represented conservatively.

This supports a native-copper obstruction explanation. It is not a physical impossibility proof: transformed native shapes use 1 um outward approximation, and through-via layer spans can conservatively overblock unflashed annuli. No complete route or precise router failure cause is established. The actual Freerouting machine result reports two incomplete connections and no new networks; strict native import rejects the empty session improvement. Those results are retained separately.

The frozen receipt records exact board/DSN hashes, literal diagnostic operands, component membership, closest component boundaries, and the failed first diagnostic's SWIG parent-proxy lookup. The successor resolves Source pad ownership through the actual footprint inventory. No board, schematic, Source, frozen tool or accepted route was changed.

Further router trials and copper integration are held while the user uses Argus on the current native handoff. A returned candidate must be reconciled against that exact handoff and recheck protected Cu, Source clusters, uncapped connectivity, native DRC, literal references/annuli, registration, power geometry and retained circuits before any adoption.
''',encoding='utf-8')
print(json.dumps(dict(receipt=str((OUT/'receipt.json').relative_to(ROOT)),sha256=e.sha(OUT/'receipt.json'),rows=rows),indent=2))
