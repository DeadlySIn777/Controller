"""Bind a completed full independent audit to analytic circular transition geometry.

No refill/geometry change/reference healing is performed. A round ordinary via
defines a convex circular own-transition disk. Polygon vertices inside that
exact disk imply every linear edge and polygon interior is inside it too.
This removes inscribed-polygon chord artifacts without expanding any radius.
"""
import hashlib,json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
from shapely import wkb
from shapely.geometry import Polygon,MultiPolygon,GeometryCollection
C,G,N=A.C,A.G,A.N
OUT=HERE/'ao1-reference-coupled-r18-independent-analytic-transition-r5.json'

def vertices(shape):
    if shape.is_empty:return []
    if isinstance(shape,Polygon):return list(shape.exterior.coords)+[p for ring in shape.interiors for p in ring.coords]
    if isinstance(shape,(MultiPolygon,GeometryCollection)):return [p for g in shape.geoms for p in vertices(g)]
    raise ValueError('Unexpected gap geometry '+shape.geom_type)

def main():
    started=time.monotonic()
    if OUT.exists():raise ValueError('Fresh analytic transition audit required')
    audit_path=HERE/'ao1-reference-coupled-r18-independent-mon-r4.json';receipt=json.loads(A.read(audit_path))
    constructor_path=HERE/'ao1-reference-coupled-r18.json';constructor=json.loads(A.read(constructor_path))
    if Path(receipt['constructor_receipt']).resolve()!=constructor_path.resolve():raise ValueError('Full independent constructor binding differs')
    for key in ('clearance_errors','pad_relationship_losses','surviving_contact_losses','prospective_fill_contact_errors','unchanged_reference_losses','paired_return_errors'):
        if receipt[key]:raise ValueError('Full independent non-reference gate failed '+key)
    if receipt['independent_preserved_source_MON_piece']['previously_covered_retained_body_lost_mm2']>1e-9:raise ValueError('Retained source reference lost')
    # A new report cannot repair or silently supersede a changed frozen helper.
    for name,pin in receipt['read_files_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=pin:raise ValueError('Frozen full-audit input changed '+name)
    if receipt['source_sha256']!=A.SOURCE_SHA or constructor['source_sha256']!=A.SOURCE_SHA:raise ValueError('Source board identity differs')
    native_raw=A.read(A.NATIVE/'geometry.json');native=json.loads(native_raw);flash=json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))
    native_vias={r['uuid']:r for r in native['vias']};raw=A.read(G.SOURCE);identity=N.SourceNets(raw)
    if C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Exact source board changed')
    parsed={u:G.parse(u,ch.encode(),{}) for u,ch in constructor['exact_new_chunks'].items()}
    signal={z['net']:z for z in parsed.values() if z['kind']=='via' and z['net'] in (A.S.norm('/motherboard_analog_output/AO1_VREF'),A.S.norm('/motherboard_analog_output/AO1_DAC_SDI'))}
    refs={r['uuid']:r for r in receipt['full_new_signal_reference']};expected={r['uuid'] for r in receipt['reference_errors']};gaps=receipt['exact_reference_gap_classification']
    if {r['uuid'] for r in gaps}!=expected:raise ValueError('Exact gap WKB ledger differs from full audit')
    rows=[];open_rows=[]
    for row in gaps:
        path=Path(row['exact_gap_WKB_path']);data=A.read(path)
        if C.sha(data)!=row['exact_gap_WKB_sha256']:raise ValueError('Exact gap changed')
        shape=wkb.loads(data);pts=vertices(shape);ref=refs[row['uuid']];via=signal.get(row['net'])
        if not via or ref['own_transition_uuid']!=via['uuid']:raise ValueError('Actual own native transition identity differs')
        radius=via['d']/2+ref['exact_native_local_zone_clearance_mm']+.025
        if abs(radius-ref['own_void_radius_mm'])>1e-12:raise ValueError('Transition radius changed')
        maximum=max(math.dist(p[:2],via['at']) for p in pts);own=maximum<=radius
        stale=[]
        for old in row['withdrawn_native_barrel_geometry']:
            uid=old['withdrawn_uuid'];v=native_vias[uid]
            if uid not in constructor['removed_owned_items'] or v['at']!=old['exact_source_position_mm'] or v['w']!=old['exact_source_diameter_mm'] or row['reference_plane'] not in flash['vias'][uid]:raise ValueError('Actual withdrawn source annulus identity differs')
            old_radius=v['w']/2+ref['exact_native_local_zone_clearance_mm']+.025
            distance=max(math.dist(p[:2],v['at']) for p in pts)
            stale.append({'native_source_uuid':uid,'native_at_mm':v['at'],'actual_source_flash_layer':row['reference_plane'],'diameter_mm':v['w'],'exact_native_local_clearance_mm':ref['exact_native_local_zone_clearance_mm'],'unchanged_radius_mm':old_radius,'maximum_gap_vertex_radius_mm':distance,'all_gap_vertices_inside_exact_analytic_disk':distance<=old_radius})
        cache=any(r['all_gap_vertices_inside_exact_analytic_disk'] for r in stale)
        state='WITHIN_ACTUAL_OWN_TRANSITION_ANALYTIC_DISK' if own else 'WITHDRAWN_SDI_CACHE_REFERENCE_OPEN' if cache else 'UNEXPLAINED_NONCACHE_REFERENCE_OPEN'
        output={'uuid':row['uuid'],'net':row['net'],'layer':row['layer'],'exact_gap_WKB_path':str(path),'exact_gap_WKB_SHA256':C.sha(data),'uncovered_polygon_mm2':shape.area,'bounds_mm':list(shape.bounds),'classification':state,'own_native_round_via_uuid':via['uuid'],'own_at_mm':via['at'],'own_diameter_mm':via['d'],'own_unchanged_transition_radius_mm':radius,'maximum_gap_vertex_radius_from_own_mm':maximum,'own_radius_expansion_mm':0,'all_gap_vertices_inside_own_exact_analytic_disk':own,'convex_disk_edge_interior_proof':True,'withdrawn_native_clearance_disks':stale,'reference_healing_credit':False}
        rows.append(output)
        if not own:open_rows.append(output)
    only_cache=bool(open_rows) and all(r['classification']=='WITHDRAWN_SDI_CACHE_REFERENCE_OPEN' for r in open_rows)
    verdict='INDEPENDENT_PHYSICAL_CONTACT_NEIGHBOUR_PASS_ONLY_WITHDRAWN_SDI_CACHE_REFERENCE_OPEN' if only_cache else 'ANALYTIC_TRANSITION_CLASSIFICATION_INCOMPLETE'
    report={'verdict':verdict,'constructor_receipt':str(constructor_path),'constructor_SHA256':C.sha(constructor_path.read_bytes()),'full_independent_receipt':str(audit_path),'full_independent_SHA256':C.sha(audit_path.read_bytes()),'source_SHA256':A.SOURCE_SHA,'actual_native_geometry_SHA256':C.sha(native_raw),'exact_frozen_nonreference_gates_PASS':True,'retained_source_MON_body':receipt['independent_preserved_source_MON_piece'],'analytic_round_via_transition_rows':rows,'remaining_reference_rows':open_rows,'stale_fill_healing_credit':False,'reference_PASS':False,'native_refill_export_required':True,'native_all6_new_annuli':'OPEN','read_files_sha256':A.READS,'board_emitted':False,'native_jobs':0,'gpu_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started}
    OUT.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(OUT),'verdict':verdict,'actual_own_transition_rows':len(rows)-len(open_rows),'remaining_cache_rows':len(open_rows),'elapsed_seconds':report['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
